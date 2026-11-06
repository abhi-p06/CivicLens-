import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token
from app.core.demo_store import demo_store
from app.models.issue import Issue, IssueCategory, PriorityLevel, IssueStatus

client = TestClient(app)

def test_hierarchy_tree_unauthenticated_public():
    """Verify unauthenticated access returns complete tree across BMC (Mumbai) and NMMC (Navi Mumbai)."""
    res = client.get("/api/v1/hierarchy/tree")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 2
    auth_codes = [a["code"] for a in data]
    assert "BMC" in auth_codes
    assert "NMMC" in auth_codes

    for a in data:
        assert "name" in a
        assert a["level"] == "authority"
        for z in a.get("children", []):
            assert "name" in z
            assert z["level"] == "zone"
            for w in z.get("children", []):
                assert "name" in w
                assert w["level"] == "ward"
                for sw in w.get("children", []):
                    assert "name" in sw
                    assert sw["level"] == "sub_ward"

def test_hierarchy_tree_admin_role():
    """Verify Admin user gets complete tree with BMC (24 wards) and NMMC (8 wards)."""
    token = create_access_token(
        user_id="ADMIN-SYS-01",
        role="admin",
        email="admin@civilens.org",
        name="Municipal Operations Administrator"
    )
    res = client.get("/api/v1/hierarchy/tree", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 2

    bmc = next(a for a in data if a["code"] == "BMC")
    nmmc = next(a for a in data if a["code"] == "NMMC")

    # BMC has 7 zones and 24 administrative wards
    assert len(bmc["children"]) == 7
    bmc_wards = []
    for z in bmc["children"]:
        bmc_wards.extend(z["children"])
    assert len(bmc_wards) == 24

    # NMMC has 2 zones and 8 administrative ward offices
    assert len(nmmc["children"]) == 2
    nmmc_wards = []
    for z in nmmc["children"]:
        nmmc_wards.extend(z["children"])
    assert len(nmmc_wards) == 8

def test_hierarchy_tree_officer_mumbai_sees_both_authorities():
    """
    Verify Municipal Officer assigned to BMC N-Ward gets the EXACT SAME complete tree
    as Admin, displaying both BMC (24 wards) and Navi Mumbai NMMC (8 wards).
    """
    token = create_access_token(
        user_id="INSP-MUMBAI-01",
        role="inspector",
        email="inspector@civilens.org",
        name="Inspector Abhinay"
    )
    res = client.get("/api/v1/hierarchy/tree", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()

    # Must contain BOTH authorities (Mumbai BMC and Navi Mumbai NMMC)
    assert len(data) == 2
    auth_codes = [a["code"] for a in data]
    assert "BMC" in auth_codes
    assert "NMMC" in auth_codes

    bmc = next(a for a in data if a["code"] == "BMC")
    nmmc = next(a for a in data if a["code"] == "NMMC")

    bmc_wards = [w for z in bmc["children"] for w in z["children"]]
    assert len(bmc_wards) == 24

    nmmc_wards = [w for z in nmmc["children"] for w in z["children"]]
    assert len(nmmc_wards) == 8

def test_hierarchy_tree_officer_nmmc_sees_both_authorities():
    """
    Verify Municipal Officer assigned to NMMC Belapur gets the EXACT SAME complete tree
    as Admin, displaying both BMC (24 wards) and Navi Mumbai NMMC (8 wards).
    """
    token = create_access_token(
        user_id="INSP-NMMC-01",
        role="inspector",
        email="inspector.nmmc@civilens.org",
        name="Officer Deshmukh"
    )
    res = client.get("/api/v1/hierarchy/tree", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()

    assert len(data) == 2
    auth_codes = [a["code"] for a in data]
    assert "BMC" in auth_codes
    assert "NMMC" in auth_codes

def test_hierarchy_tree_citizen_forbidden():
    """Verify Citizen role is forbidden (HTTP 403) from accessing administrative hierarchy."""
    token = create_access_token(
        user_id="CITIZEN-DEMO-01",
        role="citizen",
        email="citizen@civilens.org",
        name="Citizen User"
    )
    res = client.get("/api/v1/hierarchy/tree", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403
    assert "Citizens are not authorized" in res.json()["detail"]

def test_hierarchy_tree_filter_by_ward():
    """Verify filtering by ward returns only the specified ward and prunes empty branches."""
    res = client.get("/api/v1/hierarchy/tree?ward=N-Ward")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["code"] == "BMC"
    assert len(data[0]["children"]) == 1
    assert len(data[0]["children"][0]["children"]) == 1
    assert data[0]["children"][0]["children"][0]["code"] == "N-Ward"

def test_officer_jurisdiction_me_endpoint():
    """Verify GET /api/v1/hierarchy/jurisdiction/me returns assigned operational scope."""
    mumbai_token = create_access_token(
        user_id="INSP-MUMBAI-01",
        role="inspector",
        email="inspector@civilens.org",
        name="Inspector Abhinay"
    )
    res_mumbai = client.get("/api/v1/hierarchy/jurisdiction/me", headers={"Authorization": f"Bearer {mumbai_token}"})
    assert res_mumbai.status_code == 200
    oj_mumbai = res_mumbai.json()
    assert oj_mumbai["authority_id"] == "AUTH-BMC"
    assert oj_mumbai["ward_code"] == "N-Ward"

    nmmc_token = create_access_token(
        user_id="INSP-NMMC-01",
        role="inspector",
        email="inspector.nmmc@civilens.org",
        name="Officer Deshmukh"
    )
    res_nmmc = client.get("/api/v1/hierarchy/jurisdiction/me", headers={"Authorization": f"Bearer {nmmc_token}"})
    assert res_nmmc.status_code == 200
    oj_nmmc = res_nmmc.json()
    assert oj_nmmc["authority_id"] == "AUTH-NMMC"
    assert oj_nmmc["ward_code"] == "NMMC-Belapur"

def test_backend_rbac_officer_cannot_mutate_unauthorized_jurisdictions():
    """
    Verify backend RBAC strictly blocks municipal officers from performing operations
    outside their authorized geographical jurisdiction.
    """
    mumbai_token = create_access_token(
        user_id="INSP-MUMBAI-01",
        role="inspector",
        email="inspector@civilens.org",
        name="Inspector Abhinay"
    )
    nmmc_token = create_access_token(
        user_id="INSP-NMMC-01",
        role="inspector",
        email="inspector.nmmc@civilens.org",
        name="Officer Deshmukh"
    )

    # 1. Inspector cannot create sub-wards (Admin only)
    res_sw = client.post(
        "/api/v1/hierarchy/sub-wards",
        json={"ward_id": "WARD-BMC-N", "code": "N-99", "name": "Illegal Subward"},
        headers={"Authorization": f"Bearer {mumbai_token}"}
    )
    assert res_sw.status_code == 403

    # 2. Inspector cannot create field teams (Admin only)
    res_tm = client.post(
        "/api/v1/admin/teams",
        json={"name": "Illegal Team", "department": "Road Infrastructure Maintenance"},
        headers={"Authorization": f"Bearer {mumbai_token}"}
    )
    assert res_tm.status_code == 403

    # 3. Inspector cannot assign supervisors (Admin only)
    res_sup = client.post(
        "/api/v1/hierarchy/supervisors/assign",
        json={"user_id": "INSP-MUMBAI-01", "ward_id": "WARD-BMC-N"},
        headers={"Authorization": f"Bearer {mumbai_token}"}
    )
    assert res_sup.status_code == 403

    # 4. Find issues in BMC and NMMC to test cross-jurisdiction operations
    all_issues = demo_store.list_issues()
    nmmc_issue = next((i for i in all_issues if getattr(i, "authority_code", "") == "NMMC" or "NMMC" in (i.ward or "")), None)
    bmc_n_issue = next((i for i in all_issues if i.ward == "N-Ward" or (i.ward_id or "").endswith("-N")), None)

    if nmmc_issue and bmc_n_issue:
        # BMC Inspector attempting to assign a task on NMMC issue -> must be 403 Forbidden
        res_assign = client.post(
            f"/api/v1/issues/{nmmc_issue.issueId}/assign",
            json={"department": "Road Infrastructure Maintenance", "team_name": "Team Alpha", "instructions": "Unauthorized assignment"},
            headers={"Authorization": f"Bearer {mumbai_token}"}
        )
        assert res_assign.status_code == 403
        assert "outside your authorized" in res_assign.json()["detail"].lower()

        # NMMC Inspector attempting to assign a task on BMC N-Ward issue -> must be 403 Forbidden
        res_assign_nmmc = client.post(
            f"/api/v1/issues/{bmc_n_issue.issueId}/assign",
            json={"department": "Road Infrastructure Maintenance", "team_name": "Team Alpha", "instructions": "Unauthorized assignment"},
            headers={"Authorization": f"Bearer {nmmc_token}"}
        )
        assert res_assign_nmmc.status_code == 403
        assert "outside your authorized" in res_assign_nmmc.json()["detail"].lower()

        # BMC Inspector attempting to correct jurisdiction by moving complaint to NMMC -> must be 403 Forbidden
        res_transfer = client.patch(
            f"/api/v1/issues/{bmc_n_issue.issueId}/jurisdiction",
            json={"ward_code": "NMMC-Belapur", "reason": "Illegal cross-authority move"},
            headers={"Authorization": f"Bearer {mumbai_token}"}
        )
        assert res_transfer.status_code == 403
        assert "cannot transfer complaints across municipal authorities" in res_transfer.json()["detail"].lower()

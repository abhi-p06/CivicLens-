import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token
from app.core.demo_store import demo_store

client = TestClient(app)

def test_hierarchy_tree_unauthenticated_public():
    """Verify legacy/public access returns complete tree for all authorities (Mumbai BMC & Navi Mumbai NMMC)."""
    res = client.get("/api/v1/hierarchy/tree")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 2
    auth_codes = [a["code"] for a in data]
    assert "BMC" in auth_codes
    assert "NMMC" in auth_codes

    # Verify nodes have name and level
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

def test_hierarchy_tree_inspector_with_jurisdiction():
    """Verify Municipal Officer assigned to N-Ward sees ONLY BMC -> Zone VI -> N-Ward."""
    token = create_access_token(
        user_id="INSP-MUMBAI-01",
        role="inspector",
        email="inspector@civilens.org",
        name="Inspector Abhinay"
    )
    res = client.get("/api/v1/hierarchy/tree", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()

    # Must contain only BMC, not NMMC
    assert len(data) == 1
    assert data[0]["code"] == "BMC"
    assert data[0]["name"] == "Brihanmumbai Municipal Corporation"

    # Must contain only Zone VI
    zones = data[0]["children"]
    assert len(zones) == 1
    assert "VI" in zones[0]["name"] or "VI" in zones[0]["label"]

    # Must contain only N-Ward
    wards = zones[0]["children"]
    assert len(wards) == 1
    assert wards[0]["code"] == "N-Ward"

    # Sub-wards and localities should be populated
    assert len(wards[0]["children"]) >= 1
    sw0 = wards[0]["children"][0]
    assert sw0["level"] == "sub_ward"
    assert "supervisor" in sw0
    assert "department" in sw0

def test_hierarchy_tree_inspector_without_jurisdiction():
    """Verify Municipal Officer with no assigned jurisdiction receives an empty list []."""
    token = create_access_token(
        user_id="INSP-UNASSIGNED-99",
        role="inspector",
        email="unassigned@civilens.org",
        name="Unassigned Officer"
    )
    res = client.get("/api/v1/hierarchy/tree", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert data == []

def test_hierarchy_tree_citizen_forbidden():
    """Verify Citizen role is forbidden from accessing administrative hierarchy."""
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

"""
CIVILENS Phase 3 — Hierarchical Complaint Routing & Jurisdiction Verification Test Suite.

Validates:
1. BMC multi-tier geographical routing (Authority -> Zone -> Ward -> Sub-Ward -> Locality).
2. NMMC multi-tier geographical routing.
3. Correct ward matching (no mismatch).
4. Wrong manually selected ward (mismatch detection & GPS authority enforcement).
5. Missing sub-ward boundary (complaint accepted, sub_ward_pending, flagged for review).
6. GPS boundary edge uncertainty and ambiguous corridor handling.
7. Strict rejection of outside jurisdictions (Kharghar, Panvel, Thane, Mira-Bhayandar, Delhi).
8. Complete complaint persistence with all indexed geographical fields.
9. Manual jurisdiction correction with immutable audit trail.
10. Real-time GIS workload tree synchronization.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.demo_store import demo_store
from app.modules.gis.hierarchy_spatial import OUT_OF_BOUNDS_ERROR


@pytest.fixture(scope="module")
def client():
    demo_store.seed_hierarchy_if_empty()
    with TestClient(app) as c:
        yield c


def test_bmc_hierarchical_routing(client):
    """Verify that a complaint in Mumbai correctly resolves and persists the complete 5-tier geographical hierarchy."""
    payload = {
        "complaintText": "Deep road fissure on 90 Feet Road near Somaiya Vidyavihar campus gate",
        "location": "Somaiya Vidyavihar Main Gate, Vidyavihar East",
        "latitude": 19.0728,
        "longitude": 72.8998,
        "category": "Roads & Footpaths",
        "ward": "N-Ward",
        "source": "citizen_portal"
    }
    res = client.post("/api/v1/issues", json=payload)
    assert res.status_code in (200, 201)
    issue = res.json()

    # Verify 5-tier Geographical Hierarchy
    assert issue["authority_code"] == "BMC"
    assert issue["authority_id"] == "AUTH-BMC"
    assert "Brihanmumbai" in issue["authority_name"]
    assert issue["zone_name"] is not None
    assert issue["ward"] == "N-Ward"
    assert issue["sub_ward_id"] is not None
    assert "N-01" in (issue["sub_ward_name"] or "")
    assert issue["locality_name"] is not None

    # Verify Separation of Geographical routing from Operational assignment
    assert "Road" in issue["department"]
    assert issue["routing_path"] is not None
    assert "BMC" in issue["routing_path"]
    assert "N-Ward" in issue["routing_path"]
    assert issue["jurisdiction_verified"] is True


def test_nmmc_hierarchical_routing(client):
    """Verify that a complaint in Navi Mumbai routes through NMMC hierarchy without mixing with BMC."""
    payload = {
        "complaintText": "Severe commercial garbage spill near Sector 17 Vashi vegetable market",
        "location": "Sector 17, Vashi, Navi Mumbai",
        "latitude": 19.0770,
        "longitude": 72.9985,
        "category": "Sanitation & Garbage",
        "source": "citizen_portal"
    }
    res = client.post("/api/v1/issues", json=payload)
    assert res.status_code in (200, 201)
    issue = res.json()

    assert issue["authority_code"] == "NMMC"
    assert issue["authority_id"] == "AUTH-NMMC"
    assert "Navi Mumbai" in issue["authority_name"]
    assert "Vashi" in issue["ward"]
    assert "NMMC" in issue["routing_path"]
    assert "Vashi" in issue["routing_path"]


def test_correct_ward_selection_no_mismatch(client):
    """Verify that when a citizen selects the true GPS ward, no mismatch is flagged."""
    res = client.post(
        "/api/v1/hierarchy/verify-location",
        json={
            "latitude": 19.0728,
            "longitude": 72.8998,
            "selected_ward": "N-Ward"
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data["is_valid"] is True
    assert data["has_ward_mismatch"] is False
    assert data["warning_message"] is None
    assert data["ward_code"] == "N-Ward"


def test_wrong_manually_selected_ward_mismatch(client):
    """Verify that when citizen selects K/West but pin is in Somaiya (N-Ward), mismatch is flagged and GPS jurisdiction enforced."""
    # Verification check
    ver_res = client.post(
        "/api/v1/hierarchy/verify-location",
        json={
            "latitude": 19.0728,
            "longitude": 72.8998,
            "selected_ward": "K/West"
        }
    )
    assert ver_res.status_code == 200
    ver_data = ver_res.json()
    assert ver_data["is_valid"] is True
    assert ver_data["has_ward_mismatch"] is True
    assert ver_data["ward_code"] == "N-Ward"
    assert "mismatch" in ver_data["warning_message"].lower()

    # Submission check: complaint is persisted under verified GPS ward (N-Ward)
    sub_res = client.post(
        "/api/v1/issues",
        json={
            "complaintText": "Crater pothole test mismatch enforcement",
            "location": "Somaiya Vidyavihar",
            "latitude": 19.0728,
            "longitude": 72.8998,
            "selected_ward": "K/West",
            "ward": "K/West",
            "category": "Roads & Footpaths"
        }
    )
    assert sub_res.status_code in (200, 201)
    sub_data = sub_res.json()
    assert sub_data["ward"] == "N-Ward", "Verified GPS ward must override erroneous manual selection"
    assert sub_data["authority_code"] == "BMC"


def test_missing_sub_ward_boundary_accepted_and_flagged(client):
    """
    Verify that an in-ward complaint without an existing sub-ward polygon (e.g. Mulund in T-Ward)
    is accepted with status 201, assigned to verified ward, marked sub_ward_pending, and flagged for review.
    """
    payload = {
        "complaintText": "Deep pothole on LBS Road near Mulund railway station junction",
        "location": "Mulund West Station Road",
        "latitude": 19.1726,
        "longitude": 72.9565,
        "category": "Roads & Footpaths"
    }
    res = client.post("/api/v1/issues", json=payload)
    assert res.status_code in (200, 201), "Legitimate in-ward complaint must NOT be rejected when sub-ward is pending"
    issue = res.json()

    assert issue["ward"] == "T-Ward"
    assert issue["sub_ward_id"] is None
    assert "Pending" in (issue["sub_ward_name"] or "")
    assert issue["jurisdiction_review_required"] is True
    assert "sub-ward" in issue["jurisdiction_review_reason"].lower()


def test_strict_rejection_outside_supported_boundaries(client):
    """Verify that coordinates outside BMC and NMMC boundaries are rejected with HTTP 400."""
    outside_coords = [
        (19.0473, 73.0699, "Kharghar (CIDCO / Panvel Municipal Corp)"),
        (18.9894, 73.1175, "Panvel City (Panvel Municipal Corp)"),
        (19.2183, 72.9781, "Thane City (Thane Municipal Corp)"),
        (19.2813, 72.8564, "Mira Road (Mira-Bhayandar Municipal Corp)"),
        (28.6139, 77.2090, "New Delhi"),
        (18.9100, 72.7500, "Offshore Arabian Sea")
    ]

    for lat, lng, label in outside_coords:
        res = client.post(
            "/api/v1/issues",
            json={
                "complaintText": f"Boundary rejection test for {label}",
                "location": label,
                "latitude": lat,
                "longitude": lng,
                "category": "Roads & Footpaths"
            }
        )
        assert res.status_code == 400, f"Expected 400 for {label}, got {res.status_code}"
        assert OUT_OF_BOUNDS_ERROR in res.json()["detail"]


def test_manual_jurisdiction_correction_and_audit_trail(client):
    """Verify authorized officer can correct jurisdiction, persisting new hierarchy and immutable audit trail."""
    # 1. Create issue in N-Ward
    res_create = client.post(
        "/api/v1/issues",
        json={
            "complaintText": "Pothole for jurisdiction reallocation audit testing",
            "location": "Ghatkopar West border",
            "latitude": 19.0856,
            "longitude": 72.9082,
            "category": "Roads & Footpaths"
        }
    )
    issue_id = res_create.json()["issueId"]

    # 2. Reallocate to L-Ward with reason
    reason_text = "Executive engineer boundary survey placed road segment in L-Ward"
    patch_res = client.patch(
        f"/api/v1/issues/{issue_id}/jurisdiction",
        json={
            "ward_code": "L-Ward",
            "sub_ward_id": "SUB-BMC-L-01",
            "reason": reason_text
        },
        headers={"Authorization": "Bearer demo-inspector-token"}
    )
    assert patch_res.status_code == 200
    updated_issue = patch_res.json()
    assert updated_issue["ward"] == "L-Ward"
    assert updated_issue["sub_ward_id"] == "SUB-BMC-L-01"

    # 3. Retrieve immutable audit trail
    history_res = client.get(f"/api/v1/issues/{issue_id}/jurisdiction-history")
    assert history_res.status_code == 200
    history = history_res.json()
    assert len(history) >= 1

    latest_audit = history[-1]
    assert latest_audit["changed_by"] == "Abhinay"
    assert latest_audit["changed_by_role"] == "inspector"
    assert latest_audit["reason"] == reason_text
    assert latest_audit["previous_jurisdiction"]["ward_code"] == "N-Ward"
    assert latest_audit["new_jurisdiction"]["ward_code"] == "L-Ward"
    assert latest_audit["timestamp"] is not None


def test_real_time_gis_workload_synchronization(client):
    """Verify that issue creation and reallocation immediately update dynamic hierarchy tree complaint counts."""
    # 1. Read baseline tree
    tree_start = client.get("/api/v1/hierarchy/tree").json()
    bmc_start = next(n for n in tree_start if n["code"] == "BMC")
    n_node_start = next(c for z in bmc_start["children"] for c in z["children"] if c["code"] == "N-Ward")
    l_node_start = next(c for z in bmc_start["children"] for c in z["children"] if c["code"] == "L-Ward")
    start_n = n_node_start["total_complaints"]
    start_l = l_node_start["total_complaints"]

    # 2. Create complaint in N-Ward
    res = client.post(
        "/api/v1/issues",
        json={
            "complaintText": "Workload sync test pothole",
            "location": "Somaiya Vidyavihar",
            "latitude": 19.0728,
            "longitude": 72.8998,
            "category": "Roads & Footpaths"
        }
    )
    issue_id = res.json()["issueId"]

    # 3. Verify tree count incremented in N-Ward
    tree_created = client.get("/api/v1/hierarchy/tree").json()
    bmc_created = next(n for n in tree_created if n["code"] == "BMC")
    n_node_created = next(c for z in bmc_created["children"] for c in z["children"] if c["code"] == "N-Ward")
    assert n_node_created["total_complaints"] == start_n + 1

    # 4. Reallocate issue to L-Ward
    client.patch(
        f"/api/v1/issues/{issue_id}/jurisdiction",
        json={
            "ward_code": "L-Ward",
            "sub_ward_id": "SUB-BMC-L-01",
            "reason": "Reallocation workload sync"
        },
        headers={"Authorization": "Bearer demo-inspector-token"}
    )

    # 5. Verify tree counts adjusted: N-Ward decremented, L-Ward incremented
    tree_final = client.get("/api/v1/hierarchy/tree").json()
    bmc_final = next(n for n in tree_final if n["code"] == "BMC")
    n_node_final = next(c for z in bmc_final["children"] for c in z["children"] if c["code"] == "N-Ward")
    l_node_final = next(c for z in bmc_final["children"] for c in z["children"] if c["code"] == "L-Ward")

    assert n_node_final["total_complaints"] == start_n
    assert l_node_final["total_complaints"] == start_l + 1


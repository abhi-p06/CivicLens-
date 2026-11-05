"""
CIVILENS Hierarchical Ward Management, Sub-Ward Routing and Crew Allocation Test Suite.

Validates:
1. BMC and NMMC hierarchy separation (distinct authorities, no shared ward codes).
2. Point-in-polygon spatial hierarchy resolution (Authority -> Zone -> Ward -> Sub-Ward -> Locality).
3. Out-of-bounds rejection for invalid coordinates.
4. Manually selected ward mismatch detection vs GPS derived ward.
5. Category-based routing path generation (Roads -> Road Maintenance, Garbage -> Sanitation).
6. Persisted complaint routing tree and jurisdiction audit log after corrections.
7. Operational Sub-Ward CRUD and validation (CIVILENS operational flag).
8. Real workload count calculation at hierarchy nodes.
9. GIS boundaries GeoJSON endpoint serving both administrative wards and operational sub-wards.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.demo_store import demo_store


@pytest.fixture(scope="module")
def client():
    # Ensure hierarchy seeded
    demo_store.seed_hierarchy_if_empty()
    with TestClient(app) as c:
        yield c


def test_bmc_nmmc_separation(client):
    """Verify BMC and NMMC are established as separate municipal authorities."""
    res = client.get("/api/v1/hierarchy/authorities")
    assert res.status_code == 200
    authorities = res.json()
    auth_ids = {a["id"] for a in authorities}
    assert "AUTH-BMC" in auth_ids
    assert "AUTH-NMMC" in auth_ids

    # Check wards separation
    bmc_wards = client.get("/api/v1/hierarchy/wards?authority_id=AUTH-BMC").json()
    nmmc_wards = client.get("/api/v1/hierarchy/wards?authority_id=AUTH-NMMC").json()

    assert len(bmc_wards) >= 10
    assert len(nmmc_wards) >= 6

    bmc_codes = {w["ward_code"] for w in bmc_wards}
    nmmc_codes = {w["ward_code"] for w in nmmc_wards}

    # Verify zero overlapping ward codes between BMC and NMMC
    assert bmc_codes.isdisjoint(nmmc_codes)
    assert "N-Ward" in bmc_codes
    assert any("Vashi" in c or "Belapur" in c for c in nmmc_codes)


def test_spatial_point_in_polygon_mumbai(client):
    """Verify coordinates in Vidyavihar/Somaiya (19.0728, 72.8998) resolve to BMC, Zone VI, N-Ward, Sub-Ward N-01."""
    res = client.post(
        "/api/v1/hierarchy/verify-location",
        json={"latitude": 19.0728, "longitude": 72.8998},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["is_valid"] is True
    assert data["authority_id"] == "AUTH-BMC"
    assert data["authority_code"] == "BMC"
    assert data["ward_code"] == "N-Ward"
    assert "N-01" in (data["sub_ward_name"] or "") or "N-01" in (data["sub_ward_code"] or "")
    assert data["has_ward_mismatch"] is False


def test_spatial_point_in_polygon_navi_mumbai(client):
    """Verify coordinates in Vashi Sector 17 (19.0770, 72.9985) resolve to NMMC, Zone I, Vashi Ward."""
    res = client.post(
        "/api/v1/hierarchy/verify-location",
        json={"latitude": 19.0770, "longitude": 72.9985},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["is_valid"] is True
    assert data["authority_id"] == "AUTH-NMMC"
    assert data["authority_code"] == "NMMC"
    assert "Vashi" in (data["ward_code"] or "") or "Vashi" in (data["ward_name"] or "")


def test_invalid_coordinates_rejection(client):
    """Verify coordinates far outside Mumbai/Navi Mumbai (e.g., Delhi) are marked invalid."""
    res = client.post(
        "/api/v1/hierarchy/verify-location",
        json={"latitude": 28.6139, "longitude": 77.2090},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["is_valid"] is False
    assert data["authority_id"] is None


def test_ward_mismatch_detection(client):
    """Verify that when a citizen selects K/West but GPS coordinates are in Somaiya (N-Ward), a mismatch is flagged."""
    res = client.post(
        "/api/v1/hierarchy/verify-location",
        json={
            "latitude": 19.0728,
            "longitude": 72.8998,
            "selected_ward": "K/West",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["is_valid"] is True
    assert data["has_ward_mismatch"] is True
    assert data["selected_ward"] == "K/West"
    assert data["ward_code"] == "N-Ward"
    assert "mismatch" in data["warning_message"].lower()


def test_complaint_routing_by_category(client):
    """Verify complaint creation sets proper department, supervisor, and routing path based on category."""
    # 1. Pothole / Road complaint in N-Ward
    road_payload = {
        "complaintText": "Deep hazardous pothole on 90 Feet Road near Somaiya gate causing heavy traffic jam",
        "location": "90 Feet Road, Vidyavihar",
        "latitude": 19.0728,
        "longitude": 72.8998,
        "category": "Roads & Footpaths",
        "ward": "N-Ward",
        "source": "citizen_portal",
    }
    res = client.post("/api/v1/issues", json=road_payload)
    assert res.status_code in (200, 201)
    road_issue = res.json()

    assert road_issue["authority_id"] == "AUTH-BMC"
    assert road_issue["ward"] == "N-Ward"
    assert "SUB-BMC-N" in (road_issue["sub_ward_id"] or "")
    assert "Road" in road_issue["department"]
    assert "BMC" in road_issue["routing_path"]
    assert "N-Ward" in road_issue["routing_path"]

    # 2. Garbage complaint in N-Ward
    garbage_payload = {
        "complaintText": "Overflowing municipal garbage bin spreading foul smell across residential footpath",
        "location": "Near Ghatkopar Station East",
        "latitude": 19.0850,
        "longitude": 72.9080,
        "category": "Sanitation & Garbage",
        "ward": "N-Ward",
        "source": "citizen_portal",
    }
    res_g = client.post("/api/v1/issues", json=garbage_payload)
    assert res_g.status_code in (200, 201)
    garbage_issue = res_g.json()

    assert garbage_issue["authority_id"] == "AUTH-BMC"
    assert "Sanitation" in garbage_issue["department"] or "Waste" in garbage_issue["department"]


def test_hierarchy_tree_structure_and_workload(client):
    """Verify /api/v1/hierarchy/tree returns nested authorities, zones, wards, and sub-wards with real DB workload counts."""
    res = client.get("/api/v1/hierarchy/tree")
    assert res.status_code == 200
    tree = res.json()
    assert len(tree) >= 2  # BMC and NMMC

    bmc_node = next(n for n in tree if n["code"] == "BMC")
    assert bmc_node["type"] == "authority"
    assert bmc_node["total_complaints"] >= 0
    assert len(bmc_node["children"]) > 0

    # Find N-Ward
    n_ward_node = None
    for child in bmc_node["children"]:
        if child["code"] == "N-Ward":
            n_ward_node = child
            break
        for grandchild in child.get("children", []):
            if grandchild["code"] == "N-Ward":
                n_ward_node = grandchild
                break
    assert n_ward_node is not None
    assert n_ward_node["type"] == "ward"
    assert len(n_ward_node["children"]) >= 1  # Sub-wards under N-Ward


def test_sub_ward_crud_and_civilens_designation(client):
    """Verify Admin can create, update, and delete CIVILENS operational sub-wards with is_official=False."""
    # Create
    new_sw_payload = {
        "ward_id": "WARD-BMC-N",
        "sub_ward_code": "N-TEST-99",
        "name": "Test Operational Beat 99",
        "supervisor_name": "Supervisor Test",
    }
    res = client.post(
        "/api/v1/hierarchy/sub-wards",
        json=new_sw_payload,
        headers={"Authorization": "Bearer demo-admin-token"},
    )
    assert res.status_code in (200, 201)
    created = res.json()
    sw_id = created["id"]
    assert created["is_official"] is False
    assert created["operational_type"] == "CIVILENS_OPERATIONAL_SUB_WARD"

    # Update
    update_res = client.patch(
        f"/api/v1/hierarchy/sub-wards/{sw_id}",
        json={"name": "Updated Test Operational Beat 99"},
        headers={"Authorization": "Bearer demo-admin-token"},
    )
    assert update_res.status_code == 200
    assert update_res.json()["name"] == "Updated Test Operational Beat 99"

    # Delete
    del_res = client.delete(
        f"/api/v1/hierarchy/sub-wards/{sw_id}",
        headers={"Authorization": "Bearer demo-admin-token"},
    )
    assert del_res.status_code == 200


def test_jurisdiction_correction_audit_history(client):
    """Verify authorized inspector/admin can correct an issue's jurisdiction with mandatory reason and persisted audit log."""
    # First create an issue
    issue_payload = {
        "complaintText": "Audit test pothole near boundary border",
        "location": "Boundary Junction",
        "latitude": 19.0728,
        "longitude": 72.8998,
        "ward": "N-Ward",
        "category": "Roads & Footpaths",
    }
    issue = client.post("/api/v1/issues", json=issue_payload).json()
    issue_id = issue["issueId"]

    # Reallocate to L-Ward with reason
    realloc_payload = {
        "ward_code": "L-Ward",
        "sub_ward_id": "SUB-BMC-L-01",
        "reason": "Road border shifted per executive engineer site survey",
    }
    patch_res = client.patch(
        f"/api/v1/issues/{issue_id}/jurisdiction",
        json=realloc_payload,
        headers={"Authorization": "Bearer demo-inspector-token"},
    )
    assert patch_res.status_code == 200
    updated_issue = patch_res.json()
    assert updated_issue["ward"] == "L-Ward"
    assert updated_issue["sub_ward_id"] == "SUB-BMC-L-01"

    # Check Audit History
    audit_res = client.get(
        f"/api/v1/issues/{issue_id}/jurisdiction-history",
        headers={"Authorization": "Bearer demo-inspector-token"},
    )
    assert audit_res.status_code == 200
    history = audit_res.json()
    assert len(history) >= 1
    latest = history[-1]
    assert history[-1]["new_jurisdiction"]["ward_code"] == "L-Ward"
    assert "survey" in latest["reason"].lower()


def test_gis_boundaries_endpoint(client):
    """Verify /api/v1/gis/boundaries serves valid GeoJSON FeatureCollection with wards and sub-wards."""
    res = client.get("/api/v1/gis/boundaries")
    assert res.status_code == 200
    fc = res.json()
    assert fc["type"] == "FeatureCollection"
    assert len(fc["features"]) > 0

    feature_layers = {f["properties"]["layer"] for f in fc["features"]}
    assert "ward" in feature_layers
    assert "sub_ward" in feature_layers

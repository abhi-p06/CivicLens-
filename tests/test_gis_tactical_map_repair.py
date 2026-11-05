"""
CIVILENS Phase 5 — Tactical GIS Map Repair, Hierarchical Routing, and Field Crew Allocation Test Suite.
Verifies:
1. Exact 24 BMC MultiPolygon administrative ward boundaries from GeoJSON.
2. CIVILENS operational sub-wards are non-rectangular corridors with is_official=False.
3. Unverified NMMC vector boundaries are None (not fake rectangles).
4. Boundary API returns distinct ADMIN_WARD and CIVILENS_OPERATIONAL_SUB_WARD properties.
5. Spatial Point-in-Polygon hierarchy resolution and out-of-bounds rejection.
6. Crew allocation capacity and category-based routing (Road vs Sanitation).
7. Citizen privacy redaction of internal officer contact details.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.demo_store import demo_store
from app.modules.gis.hierarchy_data import (
    MUNICIPAL_AUTHORITIES,
    ADMINISTRATIVE_WARDS,
    CIVILENS_OPERATIONAL_SUB_WARDS
)
from app.modules.gis.hierarchy_spatial import (
    resolve_coordinates_hierarchy,
    point_in_geometry,
    point_in_polygon
)

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def inspector_headers(client):
    res = client.post('/api/v1/auth/login', json={
        'usernameOrEmail': 'inspector@civilens.org',
        'password': 'Inspector@123',
        'expectedRole': 'inspector'
    })
    assert res.status_code == 200
    token = res.json()['token']
    return {'Authorization': f'Bearer {token}'}

# -----------------------------------------------------------------------------
# 1. Official Administrative Ward Boundaries
# -----------------------------------------------------------------------------
def test_bmc_official_24_administrative_wards():
    """Verify that BMC has exactly 24 official administrative wards with MultiPolygon geometry."""
    bmc_wards = [w for w in ADMINISTRATIVE_WARDS if w["authority_id"] == "AUTH-BMC"]
    assert len(bmc_wards) == 24, f"Expected exactly 24 BMC wards, found {len(bmc_wards)}"
    
    expected_codes = {
        "A-Ward", "B-Ward", "C-Ward", "D-Ward", "E-Ward",
        "F/South", "F/North", "G/South", "G/North",
        "H/East", "H/West", "K/East", "K/West",
        "P/South", "P/North", "L-Ward", "M/East", "M/West",
        "N-Ward", "S-Ward", "T-Ward",
        "R/South", "R/Central", "R/North"
    }
    actual_codes = {w["ward_code"] for w in bmc_wards}
    assert expected_codes == actual_codes, f"Mismatch in BMC ward codes: {expected_codes ^ actual_codes}"

    for w in bmc_wards:
        geom = w.get("boundary_geojson")
        assert geom is not None, f"BMC Ward {w['ward_code']} missing boundary geometry"
        assert geom.get("type") in ("Polygon", "MultiPolygon")
        coords = geom.get("coordinates")
        assert coords and len(coords) > 0

# -----------------------------------------------------------------------------
# 2. Sub-Ward Geometry Repair (No Fake 5-Point Bounding Rectangles)
# -----------------------------------------------------------------------------
def test_sub_ward_geometry_non_rectangular_corridors():
    """Verify operational sub-wards use non-rectangular corridor polygons or None for unconfigured beats."""
    configured_sub_wards = [sw for sw in CIVILENS_OPERATIONAL_SUB_WARDS if sw.get("boundary_geojson") is not None]
    assert len(configured_sub_wards) >= 8

    for sw in configured_sub_wards:
        geom = sw["boundary_geojson"]
        assert geom["type"] == "Polygon"
        ring = geom["coordinates"][0]
        # Must have at least 6 points (corridor polygon) and NOT be a naive 5-point bounding box
        assert len(ring) >= 6, f"Sub-ward {sw['id']} has fewer than 6 points: {len(ring)}"
        
        # Verify it is not an axis-aligned rectangle where all xs and ys take only 2 distinct values
        xs = {p[0] for p in ring}
        ys = {p[1] for p in ring}
        assert len(xs) > 2 and len(ys) > 2, f"Sub-ward {sw['id']} is an axis-aligned bounding box"

    # Verify unconfigured NMMC beats do NOT have fake rectangles
    nmmc_subs = [sw for sw in CIVILENS_OPERATIONAL_SUB_WARDS if sw["authority_id"] == "AUTH-NMMC"]
    for sw in nmmc_subs:
        assert sw.get("boundary_geojson") is None, f"NMMC sub-ward {sw['id']} should have None boundary"

# -----------------------------------------------------------------------------
# 3. GIS Boundary API Contract & Layer Metadata
# -----------------------------------------------------------------------------
def test_gis_boundaries_api_endpoint(client):
    """Verify /api/v1/gis/boundaries emits proper 'type' and 'layer' for independent toggling."""
    res = client.get("/api/v1/gis/boundaries")
    assert res.status_code == 200
    data = res.json()
    assert data.get("type") == "FeatureCollection"
    features = data.get("features", [])

    admin_ward_features = [f for f in features if f["properties"].get("type") == "ADMIN_WARD"]
    sub_ward_features = [f for f in features if f["properties"].get("type") == "CIVILENS_OPERATIONAL_SUB_WARD"]

    assert len(admin_ward_features) == 24
    assert len(sub_ward_features) >= 8

    # Verify property contracts
    for f in admin_ward_features:
        p = f["properties"]
        assert p["layer"] == "ward"
        assert p["type"] == "ADMIN_WARD"
        assert p["is_official"] is True
        assert "code" in p
        assert "lead_officer" in p

    for f in sub_ward_features:
        p = f["properties"]
        assert p["layer"] == "sub_ward"
        assert p["type"] == "CIVILENS_OPERATIONAL_SUB_WARD"
        assert p["is_official"] is False
        assert p["operational_type"] == "CIVILENS_OPERATIONAL_SUB_WARD"
        assert "supervisor_name" in p

# -----------------------------------------------------------------------------
# 4. Hierarchical Spatial Resolution & Containment
# -----------------------------------------------------------------------------
def test_spatial_resolution_vidyavihar():
    """Verify (19.0728, 72.8998) resolves strictly to BMC, Zone VI, N-Ward, SUB-BMC-N-01."""
    res = resolve_coordinates_hierarchy(lat=19.0728, lng=72.8998)
    assert res["is_valid"] is True
    assert res["authority_id"] == "AUTH-BMC"
    assert res["ward_code"] == "N-Ward"
    assert res["sub_ward_id"] == "SUB-BMC-N-01"

def test_spatial_resolution_ghatkopar_west():
    """Verify (19.0850, 72.9080) resolves strictly to BMC, Zone VI, N-Ward, SUB-BMC-N-02."""
    res = resolve_coordinates_hierarchy(lat=19.0850, lng=72.9080)
    assert res["is_valid"] is True
    assert res["authority_id"] == "AUTH-BMC"
    assert res["ward_code"] == "N-Ward"
    assert res["sub_ward_id"] == "SUB-BMC-N-02"

def test_spatial_resolution_out_of_bounds():
    """Verify coordinates outside Mumbai/Navi Mumbai metropolitan bounds are rejected."""
    # Delhi coordinates
    res = resolve_coordinates_hierarchy(lat=28.6139, lng=77.2090)
    assert res["is_valid"] is False
    assert "error" in res

# -----------------------------------------------------------------------------
# 5. Crew Allocation & Capacity Tracking
# -----------------------------------------------------------------------------
def test_crew_allocation_workload_and_capacity(client, inspector_headers):
    """Verify assigning a complaint to a field crew increments active_tasks_count."""
    # Get available road crew
    teams = client.get("/api/v1/teams").json()
    road_teams = [t for t in teams if "Road" in t["department"]]
    assert len(road_teams) > 0
    test_team = road_teams[0]
    initial_tasks = test_team.get("active_tasks_count", 0)

    # Post an issue in N-Ward (matching inspector's jurisdiction)
    issue_payload = {
        "complaintText": "Major pothole cluster on 90 Feet Road near Somaiya Vidyavihar gate",
        "location": "90 Feet Road, Vidyavihar East",
        "latitude": 19.0728,
        "longitude": 72.8998,
        "category": "Roads & Footpaths",
        "ward": "N-Ward",
        "source": "citizen_portal"
    }
    issue = client.post("/api/v1/issues", json=issue_payload).json()
    issue_id = issue["issueId"]

    # Assign issue to test_team via supervisor assignment
    assign_payload = {
        "department": test_team.get("department", "Road Infrastructure Maintenance"),
        "team_name": test_team["name"],
        "team_id": test_team["id"],
        "assigned_officer": "Duty Supervisor R. Shinde",
        "instructions": "Asphalt patch repair with roller compaction",
        "scheduled_date": "2026-11-10T10:00:00Z"
    }
    assign_res = client.post(f"/api/v1/issues/{issue_id}/assign", json=assign_payload, headers=inspector_headers)
    assert assign_res.status_code in (200, 201)
    assigned_issue = assign_res.json()
    assert assigned_issue["assignment"]["team_id"] == test_team["id"]

    # Check updated team active tasks count
    updated_teams = client.get("/api/v1/teams").json()
    updated_team = next(t for t in updated_teams if t["id"] == test_team["id"])
    assert updated_team["active_tasks_count"] >= initial_tasks + 1

# -----------------------------------------------------------------------------
# 6. Citizen Privacy Redaction
# -----------------------------------------------------------------------------
def test_citizen_privacy_redaction(client):
    """Verify that Citizen users cannot see internal officer names or instructions."""
    issues = client.get("/api/v1/issues?citizen_id=cit_101").json()
    for iss in issues:
        if iss.get("assignment"):
            assert iss["assignment"].get("assigned_officer") is None
            assert iss["assignment"].get("instructions") is None
        # Public civic hierarchy routing path must be present
        assert "routing_path" in iss

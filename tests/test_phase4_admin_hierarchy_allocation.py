"""
CIVILENS Phase 4 — Admin Ward Hierarchy & Allocation Test Suite.

Validates:
1. City & Authority tree structure (Mumbai -> BMC -> Zones -> 24 Wards, Navi Mumbai -> NMMC -> Zones -> 8 Ward Offices).
2. Direct vs. aggregate workload metric separation.
3. Admin operational sub-ward CRUD lifecycle (enforcing is_official=false).
4. Sub-ward GeoJSON polygon boundary ingestion and spatial routing.
5. Department and team/crew allocation (multiple crews per sub-ward, road & sanitation departments).
6. Supervisor assignment to operational jurisdictions.
7. Strict role permission gates (Admin authorized; Inspector/Citizen forbidden from hierarchy mutations).
8. Query filtering of field teams by ward and sub_ward_id.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.demo_store import demo_store


@pytest.fixture(scope="module")
def client():
    demo_store.seed_hierarchy_if_empty()
    demo_store.seed_default_teams_and_wards_if_empty()
    with TestClient(app) as c:
        yield c


ADMIN_HEADERS = {"Authorization": "Bearer demo-admin-token"}
INSPECTOR_HEADERS = {"Authorization": "Bearer demo-inspector-token"}
CITIZEN_HEADERS = {"Authorization": "Bearer demo-citizen-token"}


def test_city_and_authority_tree_hierarchy(client):
    """Verify backend returns complete multi-tier tree for BMC (24 wards) and NMMC (8 ward offices)."""
    res = client.get("/api/v1/hierarchy/tree")
    assert res.status_code == 200
    tree = res.json()
    assert len(tree) >= 2, "Must contain at least BMC and NMMC authorities"

    bmc = next((n for n in tree if n["code"] == "BMC"), None)
    nmmc = next((n for n in tree if n["code"] == "NMMC"), None)

    assert bmc is not None, "BMC authority must be present"
    assert nmmc is not None, "NMMC authority must be present"

    # BMC: 7 Zones
    assert len(bmc["children"]) == 7, "BMC must have 7 administrative zones"
    total_bmc_wards = sum(len(z["children"]) for z in bmc["children"])
    assert total_bmc_wards == 24, f"BMC must have exactly 24 administrative wards, got {total_bmc_wards}"

    # NMMC: 2 Zones, 8 Ward Offices
    assert len(nmmc["children"]) == 2, "NMMC must have 2 administrative zones"
    total_nmmc_wards = sum(len(z["children"]) for z in nmmc["children"])
    assert total_nmmc_wards == 8, f"NMMC must have 8 administrative ward offices, got {total_nmmc_wards}"


def test_direct_vs_aggregate_workload_distinction(client):
    """Verify that direct complaints are explicitly distinguished from aggregate sub-area totals."""
    res = client.get("/api/v1/hierarchy/tree")
    assert res.status_code == 200
    tree = res.json()

    bmc = next(n for n in tree if n["code"] == "BMC")
    # Find a ward node
    first_zone = bmc["children"][0]
    ward_node = first_zone["children"][0]

    assert "total_complaints" in ward_node
    assert "direct_complaints" in ward_node
    assert "unassigned_complaints" in ward_node
    assert "assigned_complaints" in ward_node
    assert "in_progress_tasks" in ward_node
    assert "completed_complaints" in ward_node

    # Direct complaints must be <= total_complaints
    assert ward_node["direct_complaints"] <= ward_node["total_complaints"]


def test_admin_sub_ward_crud_lifecycle(client):
    """Verify Admin can create, update, and deactivate operational sub-wards with non-statutory flag."""
    # 1. Create sub-ward under N-Ward
    create_payload = {
        "ward_id": "WARD-BMC-N",
        "sub_ward_code": "N-TEST-99",
        "name": "Phase 4 Innovation Test Beat",
        "supervisor_name": "Supervisor A. Patil",
        "assigned_department": "Road Infrastructure Maintenance",
        "is_active": True
    }
    create_res = client.post("/api/v1/hierarchy/sub-wards", json=create_payload, headers=ADMIN_HEADERS)
    assert create_res.status_code == 201, f"Expected 201 Created, got {create_res.status_code}: {create_res.text}"
    created_sub = create_res.json()

    assert created_sub["id"].startswith("SUB-")
    assert created_sub["sub_ward_code"] == "N-TEST-99"
    assert created_sub["name"] == "Phase 4 Innovation Test Beat"
    assert created_sub["is_official"] is False, "Operational sub-wards must strictly enforce is_official=false"
    assert created_sub["operational_type"] == "CIVILENS_OPERATIONAL_SUB_WARD"
    sub_id = created_sub["id"]

    # 2. Update sub-ward
    update_res = client.patch(
        f"/api/v1/hierarchy/sub-wards/{sub_id}",
        json={
            "name": "Phase 4 Innovation Test Beat (Updated)",
            "supervisor_name": "Inspector S. Shinde"
        },
        headers=ADMIN_HEADERS
    )
    assert update_res.status_code == 200
    updated_sub = update_res.json()
    assert updated_sub["name"] == "Phase 4 Innovation Test Beat (Updated)"
    assert updated_sub["supervisor_name"] == "Inspector S. Shinde"

    # 3. Deactivate sub-ward
    del_res = client.delete(f"/api/v1/hierarchy/sub-wards/{sub_id}", headers=ADMIN_HEADERS)
    assert del_res.status_code == 200
    assert "deactivated" in del_res.json()["message"].lower()


def test_sub_ward_geojson_boundary_ingestion_and_containment(client):
    """Verify sub-ward creation with validated GeoJSON Polygon and point containment."""
    # Polygon around a test corridor in Somaiya area [lng, lat]
    test_polygon = {
        "type": "Polygon",
        "coordinates": [
            [
                [72.8980, 19.0710],
                [72.9050, 19.0710],
                [72.9050, 19.0760],
                [72.8980, 19.0760],
                [72.8980, 19.0710]
            ]
        ]
    }

    create_payload = {
        "ward_id": "WARD-BMC-N",
        "sub_ward_code": "N-GEO-01",
        "name": "Somaiya Spatial Test Zone",
        "supervisor_name": "Spatial Engineer S. Kulkarni",
        "assigned_department": "Road Infrastructure Maintenance",
        "boundary_geojson": test_polygon,
        "is_active": True
    }
    create_res = client.post("/api/v1/hierarchy/sub-wards", json=create_payload, headers=ADMIN_HEADERS)
    assert create_res.status_code == 201
    created_sub = create_res.json()
    sub_id = created_sub["id"]

    # Spatial verification: point inside the polygon (19.0735, 72.9010)
    ver_res = client.post(
        "/api/v1/hierarchy/verify-location",
        json={"latitude": 19.0735, "longitude": 72.9010}
    )
    assert ver_res.status_code == 200
    ver_data = ver_res.json()
    assert ver_data["is_valid"] is True
    assert ver_data["ward_code"] == "N-Ward"
    # Should match our newly created sub-ward or existing N-01
    assert ver_data["sub_ward_id"] is not None

    # Cleanup test sub-ward
    client.delete(f"/api/v1/hierarchy/sub-wards/{sub_id}", headers=ADMIN_HEADERS)


def test_department_and_team_crew_allocation(client):
    """Verify Admin can create and assign multiple crews across Road and Sanitation departments to a sub-ward."""
    # 1. Create a sub-ward
    sw_res = client.post(
        "/api/v1/hierarchy/sub-wards",
        json={
            "ward_id": "WARD-BMC-N",
            "sub_ward_code": "N-CREW-TEST",
            "name": "Crew Allocation Test Sub-Ward",
            "supervisor_name": "Supervisor R. Deshmukh",
            "assigned_department": "Road Infrastructure Maintenance"
        },
        headers=ADMIN_HEADERS
    )
    assert sw_res.status_code == 201
    sw_id = sw_res.json()["id"]

    # 2. Create Road Crew assigned to this sub-ward
    road_team_res = client.post(
        "/api/v1/admin/teams",
        json={
            "name": "Alpha Asphalt Rapid Patchers",
            "department": "Road Infrastructure Maintenance",
            "category": "Roads & Footpaths",
            "capacity": 8,
            "ward": "N-Ward",
            "sub_ward_id": sw_id,
            "contact_lead": "Crew Chief M. Pawar",
            "status": "AVAILABLE"
        },
        headers=ADMIN_HEADERS
    )
    assert road_team_res.status_code == 200
    road_team = road_team_res.json()
    assert road_team["sub_ward_id"] == sw_id
    assert road_team["capacity"] == 8

    # 3. Create Sanitation Crew assigned to this same sub-ward (Multiple crews per area)
    swm_team_res = client.post(
        "/api/v1/admin/teams",
        json={
            "name": "Beta Sanitation Rapid Sweepers",
            "department": "Solid Waste Management & Sanitation",
            "category": "Sanitation & Garbage",
            "capacity": 6,
            "ward": "N-Ward",
            "sub_ward_id": sw_id,
            "contact_lead": "Foreman D. Shinde",
            "status": "AVAILABLE"
        },
        headers=ADMIN_HEADERS
    )
    assert swm_team_res.status_code == 200
    swm_team = swm_team_res.json()
    assert swm_team["sub_ward_id"] == sw_id

    # 4. Verify teams query by sub_ward_id
    teams_query_res = client.get(f"/api/v1/teams?sub_ward_id={sw_id}")
    assert teams_query_res.status_code == 200
    assigned_teams = teams_query_res.json()
    team_names = [t["name"] for t in assigned_teams]
    assert "Alpha Asphalt Rapid Patchers" in team_names
    assert "Beta Sanitation Rapid Sweepers" in team_names
    assert len(assigned_teams) >= 2, "Sub-ward must have multiple allocated crews"

    # Cleanup
    client.delete(f"/api/v1/admin/teams/{road_team['id']}", headers=ADMIN_HEADERS)
    client.delete(f"/api/v1/admin/teams/{swm_team['id']}", headers=ADMIN_HEADERS)
    client.delete(f"/api/v1/hierarchy/sub-wards/{sw_id}", headers=ADMIN_HEADERS)


def test_supervisor_assignment_to_sub_ward(client):
    """Verify Admin can assign supervisor to a sub-ward."""
    assign_res = client.post(
        "/api/v1/hierarchy/supervisors/assign",
        json={
            "user_id": "officer_n_ward",
            "ward_code": "N-Ward",
            "ward_id": "WARD-BMC-N",
            "sub_ward_id": "SUB-BMC-N-01",
            "jurisdiction_level": "SUB_WARD_SUPERVISOR",
            "role_title": "Senior Operations Supervisor"
        },
        headers=ADMIN_HEADERS
    )
    assert assign_res.status_code == 200
    data = assign_res.json()
    assert "user_id" in data or data.get("success") is True


def test_role_permissions_enforcement(client):
    """Verify non-admin roles (Inspector and Citizen) are strictly forbidden from modifying hierarchy."""
    sample_sub_payload = {
        "ward_id": "WARD-BMC-N",
        "sub_ward_code": "FORBIDDEN-01",
        "name": "Unauthorized Sub-Ward Attempt"
    }

    # 1. Inspector attempting sub-ward creation -> 403 Forbidden
    insp_create = client.post("/api/v1/hierarchy/sub-wards", json=sample_sub_payload, headers=INSPECTOR_HEADERS)
    assert insp_create.status_code == 403, f"Expected 403 for Inspector, got {insp_create.status_code}"

    # 2. Citizen attempting sub-ward creation -> 403 Forbidden
    cit_create = client.post("/api/v1/hierarchy/sub-wards", json=sample_sub_payload, headers=CITIZEN_HEADERS)
    assert cit_create.status_code == 403, f"Expected 403 for Citizen, got {cit_create.status_code}"

    # 3. Citizen attempting team creation -> 403 Forbidden
    cit_team = client.post(
        "/api/v1/admin/teams",
        json={"name": "Fake Citizen Crew", "department": "Roads"},
        headers=CITIZEN_HEADERS
    )
    assert cit_team.status_code == 403, f"Expected 403 for Citizen, got {cit_team.status_code}"

    # 4. Unauthenticated request -> 401 Unauthorized
    anon_res = client.post("/api/v1/hierarchy/sub-wards", json=sample_sub_payload)
    assert anon_res.status_code == 401

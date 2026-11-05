import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.demo_store import demo_store
from app.models.issue import Issue, IssueStatus

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

@pytest.fixture
def admin_headers(client):
    res = client.post('/api/v1/auth/login', json={
        'usernameOrEmail': 'admin@civilens.org',
        'password': 'Admin@123',
        'expectedRole': 'admin'
    })
    assert res.status_code == 200
    token = res.json()['token']
    return {'Authorization': f'Bearer {token}'}

@pytest.fixture
def citizen_headers(client):
    res = client.post('/api/v1/auth/login', json={
        'usernameOrEmail': 'citizen@civilens.org',
        'password': 'Citizen@123',
        'expectedRole': 'citizen'
    })
    assert res.status_code == 200
    token = res.json()['token']
    return {'Authorization': f'Bearer {token}'}


def test_inspector_jurisdiction_and_boundary_restrictions(client, inspector_headers, admin_headers):
    """
    Ensure inspector is constrained to authorized jurisdiction (N-Ward)
    and receives HTTP 403 Forbidden when trying to access or mutate out-of-scope complaints.
    """
    # 1. Fetch inspector's own assigned jurisdiction
    res_me = client.get('/api/v1/hierarchy/jurisdiction/me', headers=inspector_headers)
    assert res_me.status_code == 200
    jurisdiction = res_me.json()
    assert jurisdiction["ward_code"] == "N-Ward"
    assert jurisdiction["authority_id"] == "AUTH-BMC"

    # 2. Get list of issues as inspector - all returned issues must belong to N-Ward
    res_issues = client.get('/api/v1/issues', headers=inspector_headers)
    assert res_issues.status_code == 200
    issues = res_issues.json()
    assert len(issues) > 0
    for issue in issues:
        assert issue.get("ward") == "N-Ward", f"Inspector received issue from unauthorized ward: {issue.get('ward')}"

    # 3. Create or find an issue explicitly in a foreign ward (e.g. L-Ward or Belapur)
    all_admin_issues = client.get('/api/v1/issues', headers=admin_headers).json()
    foreign_issue = next((i for i in all_admin_issues if i.get("ward") and i.get("ward") != "N-Ward"), None)
    if not foreign_issue:
        # Create a test issue in L-Ward
        new_res = client.post('/api/v1/issues', json={
            "complaintText": "Major pothole on Kurla Andheri Road near station",
            "category": "Roads & Footpaths",
            "location": "Kurla West, L-Ward",
            "latitude": 19.0726,
            "longitude": 72.8845,
            "ward": "L-Ward"
        }, headers=admin_headers)
        assert new_res.status_code in (200, 201)
        foreign_issue = new_res.json()

    foreign_id = foreign_issue["issueId"]

    # 4. Attempt GET /api/v1/issues/{id} for foreign issue as Inspector -> 403 Forbidden
    res_foreign_get = client.get(f'/api/v1/issues/{foreign_id}', headers=inspector_headers)
    assert res_foreign_get.status_code == 403
    assert "jurisdiction" in res_foreign_get.json()["detail"].lower()

    # 5. Attempt POST /api/v1/issues/{id}/assign for foreign issue as Inspector -> 403 Forbidden
    res_foreign_assign = client.post(f'/api/v1/issues/{foreign_id}/assign', json={
        "department": "Road Infrastructure Maintenance",
        "team_name": "BMC L-Ward Pothole Squad",
        "team_id": "TEAM-BMC-L-01",
        "instructions": "Attempting unauthorized cross-ward dispatch"
    }, headers=inspector_headers)
    assert res_foreign_assign.status_code == 403

    # 6. Admin can access the foreign issue without restriction
    res_admin_get = client.get(f'/api/v1/issues/{foreign_id}', headers=admin_headers)
    assert res_admin_get.status_code == 200


def test_category_based_crew_filtering(client, inspector_headers):
    """
    Ensure teams endpoint filters operational field crews accurately by category and department.
    """
    # 1. Query Road Maintenance crews
    res_roads = client.get('/api/v1/teams?category=Roads%20%26%20Footpaths', headers=inspector_headers)
    assert res_roads.status_code == 200
    road_teams = res_roads.json()
    assert len(road_teams) >= 1
    for t in road_teams:
        assert t["category"] == "Roads & Footpaths"
        assert "Road" in t["department"] or "Infrastructure" in t["department"]

    # 2. Query Sanitation & Waste crews
    res_san = client.get('/api/v1/teams?category=Sanitation%20%26%20Garbage', headers=inspector_headers)
    assert res_san.status_code == 200
    san_teams = res_san.json()
    assert len(san_teams) >= 1
    for t in san_teams:
        assert t["category"] == "Sanitation & Garbage"
        assert "Waste" in t["department"] or "Sanitation" in t["department"]


def test_crew_availability_and_capacity_tracking(client, admin_headers):
    """
    Verify that crew active task counts and availability status dynamically reflect assignments.
    """
    # Fetch team list
    res = client.get('/api/v1/teams', headers=admin_headers)
    assert res.status_code == 200
    teams = res.json()
    assert len(teams) > 0
    target_team = teams[0]
    team_id = target_team["id"]

    initial_tasks = target_team.get("active_tasks_count", 0)

    # Ingest a new complaint
    new_res = client.post('/api/v1/issues', json={
        "complaintText": "Test pothole for crew capacity tracking",
        "category": "Roads & Footpaths",
        "location": "Ghatkopar East",
        "latitude": 19.0856,
        "longitude": 72.9082,
        "ward": "N-Ward"
    }, headers=admin_headers)
    assert new_res.status_code in (200, 201)
    issue_id = new_res.json()["issueId"]

    # Assign issue to the team
    assign_res = client.post(f'/api/v1/issues/{issue_id}/assign', json={
        "department": target_team["department"],
        "team_name": target_team["name"],
        "team_id": team_id,
        "assigned_officer": "Supervisor Sharma",
        "instructions": "Execute pothole patch test"
    }, headers=admin_headers)
    assert assign_res.status_code == 200

    # Fetch updated team info
    updated_teams = client.get('/api/v1/teams', headers=admin_headers).json()
    updated_team = next(t for t in updated_teams if t["id"] == team_id)
    assert updated_team["active_tasks_count"] == initial_tasks + 1

    # Complete the task
    comp_res = client.post(f'/api/v1/issues/{issue_id}/complete', json={
        "completion_note": "Repairs verified complete to municipal standard",
        "closure_reason": "Work executed to municipal standard",
        "completion_photo_url": "https://example.com/repair.jpg"
    }, headers=admin_headers)
    assert comp_res.status_code == 200

    # Verify task count decremented back
    final_teams = client.get('/api/v1/teams', headers=admin_headers).json()
    final_team = next(t for t in final_teams if t["id"] == team_id)
    assert final_team["active_tasks_count"] == initial_tasks


def test_full_assignment_lifecycle_and_8_tier_routing(client, admin_headers):
    """
    Test complete operational workflow:
    1. Ingestion -> 8-tier routing created with fallbacks
    2. Geographic verification via POST /api/v1/issues/{id}/verify-jurisdiction
    3. Supervisor review & Crew assignment -> updates supervisor and crew in path
    4. Scheduling work
    5. Action in progress
    6. Completion
    7. Audit timeline reflects all steps sequentially
    """
    # 1. Ingestion of issue with unconfigured sub-ward/supervisor shows Pending Allocation fallback
    unconf_res = client.post('/api/v1/issues', json={
        "complaintText": "Streetlight failure on isolated stretch",
        "category": "Street Lighting",
        "location": "Remote bypass road",
        "latitude": 19.1200,
        "longitude": 72.8400,
        "ward": "K/East"
    }, headers=admin_headers)
    assert unconf_res.status_code in (200, 201)
    unconf_issue = unconf_res.json()
    assert "Pending Allocation" in (unconf_issue.get("routing_path") or "")

    # Ingestion of operational issue
    ingest_res = client.post('/api/v1/issues', json={
        "complaintText": "Severe crater pothole on LBS Marg near Ghatkopar Metro Station",
        "category": "Roads & Footpaths",
        "location": "LBS Marg, Ghatkopar West",
        "latitude": 19.0865,
        "longitude": 72.9080,
        "ward": "N-Ward"
    }, headers=admin_headers)
    assert ingest_res.status_code in (200, 201)
    issue = ingest_res.json()
    issue_id = issue["issueId"]

    assert issue.get("authority_code") in ("BMC", "AUTH-BMC")
    assert issue.get("ward") == "N-Ward"
    # Ensure 8 tiers are formatted in the routing path
    assert len(issue.get("routing_path", "").split("→")) == 8

    # 2. Geographic Jurisdiction Verification
    verify_res = client.post(f'/api/v1/issues/{issue_id}/verify-jurisdiction', json={
        "notes": "Verified coordinates lie within BMC Zone IV N-Ward operational jurisdiction"
    }, headers=admin_headers)
    assert verify_res.status_code == 200
    v_data = verify_res.json()
    assert v_data["jurisdiction_review_required"] is False
    assert any(e["event_type"] == "GEOGRAPHIC_VERIFIED" for e in v_data.get("timeline", []))

    # 3. Supervisor Assignment
    assign_res = client.post(f'/api/v1/issues/{issue_id}/assign', json={
        "department": "Road Infrastructure Maintenance",
        "team_name": "BMC N-Ward Pothole Rapid Action Team",
        "team_id": "TEAM-BMC-N-01",
        "assigned_officer": "Asst. Engineer R. Deshmukh",
        "instructions": "Deploy cold-mix asphalt patch unit immediately"
    }, headers=admin_headers)
    assert assign_res.status_code == 200
    assigned_issue = assign_res.json()
    assert assigned_issue["status"] == "ASSIGNED"
    assert assigned_issue["supervisor_name"] == "Asst. Engineer R. Deshmukh"
    assert assigned_issue["assignment"]["team_name"] == "BMC N-Ward Pothole Rapid Action Team"
    # Ensure routing path updated with supervisor and crew
    assert "Asst. Engineer R. Deshmukh" in assigned_issue["routing_path"]
    assert "BMC N-Ward Pothole Rapid Action Team" in assigned_issue["routing_path"]

    # 4. Schedule Work
    sched_res = client.post(f'/api/v1/issues/{issue_id}/schedule', json={
        "scheduled_date": "2026-11-10",
        "schedule_type": "WORK",
        "instructions": "Night shift deployment scheduled to minimize traffic impact"
    }, headers=admin_headers)
    assert sched_res.status_code == 200
    assert sched_res.json()["status"] == "SCHEDULED"

    # 5. Start Action In Progress
    act_res = client.post(f'/api/v1/issues/{issue_id}/action', json={
        "action_type": "WORK_STARTED",
        "notes": "Crew arrived on-site, milling damaged pavement section"
    }, headers=admin_headers)
    assert act_res.status_code == 200
    assert act_res.json()["status"] in ("IN_PROGRESS", "ACTION IN PROGRESS", "SCHEDULED")

    # 6. Complete Work
    comp_res = client.post(f'/api/v1/issues/{issue_id}/complete', json={
        "completion_note": "Patch applied, roller compacted, and lane reopened",
        "closure_reason": "Work executed to municipal standard",
        "completion_photo_url": "https://civilens.gov.in/evidence/ghatkopar_fixed.jpg"
    }, headers=admin_headers)
    assert comp_res.status_code == 200
    final_issue = comp_res.json()
    assert final_issue["status"] in ("RESOLVED", "VERIFICATION")

    # 7. Verify Timeline Integrity
    timeline = final_issue.get("timeline", [])
    event_types = [e.get("event_type") for e in timeline]
    assert "GEOGRAPHIC_VERIFIED" in event_types
    assert "TEAM_ASSIGNED" in event_types
    assert "WORK_SCHEDULED" in event_types
    assert "WORK_COMPLETED" in event_types


def test_citizen_data_sanitization_and_privacy(client, citizen_headers, admin_headers):
    """
    Ensure citizen queries NEVER expose internal officer contact details,
    supervisor phone/email, or sensitive internal maintenance notes.
    """
    # 1. Ingest an issue as citizen
    res = client.post('/api/v1/issues', json={
        "complaintText": "Garbage pile accumulating beside Pant Nagar market gate",
        "category": "Sanitation & Garbage",
        "location": "Pant Nagar, Ghatkopar East",
        "latitude": 19.0798,
        "longitude": 72.9150,
        "ward": "N-Ward"
    }, headers=citizen_headers)
    assert res.status_code in (200, 201)
    issue_id = res.json()["issueId"]

    # 2. Admin assigns the task with internal confidential instructions
    client.post(f'/api/v1/issues/{issue_id}/assign', json={
        "department": "Solid Waste Management & Sanitation",
        "team_name": "BMC N-Ward Sanitation & Litter Response Crew",
        "team_id": "TEAM-BMC-N-02",
        "assigned_officer": "Supervisor K. Patil",
        "instructions": "INTERNAL CONFIDENTIAL: Contractor fine will apply if delayed past 4 PM"
    }, headers=admin_headers)

    # 3. Citizen fetches their issues via GET /api/v1/issues/my
    my_res = client.get('/api/v1/issues/my', headers=citizen_headers)
    assert my_res.status_code == 200
    my_issues = my_res.json()
    target = next((i for i in my_issues if i["issueId"] == issue_id), None)
    assert target is not None

    # Verify sensitive data redacted for citizen
    assert target.get("supervisor_name") is None, "Citizen received supervisor_name"
    assert target.get("supervisor_id") is None, "Citizen received supervisor_id"
    if target.get("assignment"):
        assert target["assignment"].get("assigned_officer") is None, "Citizen received assigned_officer"
        assert target["assignment"].get("instructions") is None, "Citizen received internal instructions"

    # Verify public civic hierarchy fields ARE preserved
    assert target.get("authority_code") in ("BMC", "AUTH-BMC")
    assert target.get("ward") == "N-Ward"
    assert target.get("department") is not None

    # 4. Citizen directly fetches GET /api/v1/issues/{id}
    detail_res = client.get(f'/api/v1/issues/{issue_id}', headers=citizen_headers)
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail.get("supervisor_name") is None
    if detail.get("assignment"):
        assert detail["assignment"].get("assigned_officer") is None
        assert detail["assignment"].get("instructions") is None

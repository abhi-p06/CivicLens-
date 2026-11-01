import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.demo_store import demo_store
from app.models.issue import IssueStatus

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

def test_operations_kpis(client, inspector_headers):
    res = client.get('/api/v1/operations/kpis', headers=inspector_headers)
    assert res.status_code == 200
    data = res.json()
    assert "unassigned_complaints" in data
    assert "high_priority_complaints" in data
    assert "work_in_progress" in data
    assert "resolved_this_month" in data
    assert "category_workload" in data
    assert "ward_distribution" in data

def test_list_teams(client, inspector_headers):
    res = client.get('/api/v1/teams', headers=inspector_headers)
    assert res.status_code == 200
    teams = res.json()
    assert len(teams) >= 6
    assert any(t["category"] == "Roads & Footpaths" for t in teams)
    assert any(t["category"] == "Sanitation & Garbage" for t in teams)

def test_task_assignment_and_rescheduling(client, inspector_headers):
    issues = client.get('/api/v1/issues', headers=inspector_headers).json()
    target_id = issues[0]['issueId']

    # Assign task
    assign_payload = {
        'department': 'Road Infrastructure Maintenance',
        'team_name': 'Quick Patch Asphalt Squad (Ward N)',
        'team_id': 'TEAM-ROAD-01',
        'assigned_officer': 'Abhinay',
        'priority': 'CRITICAL',
        'scheduled_date': '2026-11-04',
        'instructions': 'Seal pavement crater and tamp with asphalt roller.'
    }
    assign_res = client.post(f'/api/v1/issues/{target_id}/assign', headers=inspector_headers, json=assign_payload)
    assert assign_res.status_code == 200
    updated = assign_res.json()
    assert updated['status'] == IssueStatus.SCHEDULED.value
    assert updated['assignment']['team_name'] == 'Quick Patch Asphalt Squad (Ward N)'
    assert any(e['event_type'] == 'TEAM_ASSIGNED' for e in updated['timeline'])

    # Reschedule
    sched_res = client.post(f'/api/v1/issues/{target_id}/schedule', headers=inspector_headers, json={
        'scheduled_date': '2026-11-07',
        'schedule_type': 'WORK',
        'instructions': 'Rescheduled due to heavy monsoon rain.'
    })
    assert sched_res.status_code == 200
    sched_updated = sched_res.json()
    assert sched_updated['assignment']['scheduled_date'] == '2026-11-07'
    assert any(e['event_type'] == 'WORK_SCHEDULED' for e in sched_updated['timeline'])

def test_issue_specific_road_actions(client, inspector_headers):
    issues = client.get('/api/v1/issues', headers=inspector_headers).json()
    road_issue = next((i for i in issues if "Road" in i['category']), issues[0])
    target_id = road_issue['issueId']

    # Record Temporary Safety Measures
    meas_res = client.post(f'/api/v1/issues/{target_id}/action', headers=inspector_headers, json={
        'action_type': 'RECORD_TEMPORARY_MEASURES',
        'measures': ['Barricades placed', 'Warning cones installed', 'Cold-mix temporary fill'],
        'notes': 'Temporary safety perimeter placed on high-traffic lane.'
    })
    assert meas_res.status_code == 200
    meas_data = meas_res.json()
    assert 'temporary_measures' in meas_data
    assert len(meas_data['temporary_measures']['measures']) == 3
    assert any(e['event_type'] == 'TEMPORARY_MEASURES_TAKEN' for e in meas_data['timeline'])

    # Track Repair Progress
    prog_res = client.post(f'/api/v1/issues/{target_id}/action', headers=inspector_headers, json={
        'action_type': 'PROGRESS_UPDATE',
        'stage': 'Asphalt Laying & Compaction',
        'notes': 'Sub-base cured, asphalt mix compacted to road grade.'
    })
    assert prog_res.status_code == 200
    prog_data = prog_res.json()
    assert prog_data['status'] == IssueStatus.ACTION_IN_PROGRESS.value

def test_issue_specific_sanitation_actions(client, inspector_headers):
    issues = client.get('/api/v1/issues', headers=inspector_headers).json()
    waste_issue = next((i for i in issues if "Sanitation" in i['category'] or "Garbage" in i['category']), issues[-1])
    target_id = waste_issue['issueId']

    # Schedule repeat collection
    repeat_res = client.post(f'/api/v1/issues/{target_id}/action', headers=inspector_headers, json={
        'action_type': 'SCHEDULE_REPEAT_COLLECTION',
        'frequency': 'Bi-Weekly',
        'scheduled_date': '2026-11-08',
        'notes': 'High-density commercial market requires recurring collection.'
    })
    assert repeat_res.status_code == 200
    repeat_data = repeat_res.json()
    assert repeat_data['repeat_collection']['is_scheduled'] is True
    assert repeat_data['repeat_collection']['frequency'] == 'Bi-Weekly'
    assert any(e['event_type'] == 'REPEAT_COLLECTION_SCHEDULED' for e in repeat_data['timeline'])

def test_task_completion_and_reopen_workflow(client, inspector_headers):
    issues = client.get('/api/v1/issues', headers=inspector_headers).json()
    target_id = issues[1]['issueId']

    # Completion without note should fail
    bad_res = client.post(f'/api/v1/issues/{target_id}/complete', headers=inspector_headers, json={
        'completion_note': '   ',
        'closure_reason': 'Done'
    })
    assert bad_res.status_code == 400

    # Completion with note and evidence should succeed
    comp_res = client.post(f'/api/v1/issues/{target_id}/complete', headers=inspector_headers, json={
        'completion_note': 'Full cold-mix asphalt overlay applied, leveled, and reopened for traffic.',
        'closure_reason': 'Pothole restoration complete',
        'completion_photo_url': '/data/test_samples/repair_pothole_after_repaired.jpg'
    })
    assert comp_res.status_code == 200
    comp_data = comp_res.json()
    assert comp_data['status'] == IssueStatus.RESOLVED.value
    assert comp_data['completion_details']['closure_reason'] == 'Pothole restoration complete'

    # Reopen
    reopen_res = client.post(f'/api/v1/issues/{target_id}/reopen', headers=inspector_headers, json={
        'reason': 'Pavement settlement observed after rain',
        'note': 'Second coat required.'
    })
    assert reopen_res.status_code == 200
    reopen_data = reopen_res.json()
    assert reopen_data['status'] == IssueStatus.REOPENED.value
    assert any(e['event_type'] == 'REOPENED' for e in reopen_data['timeline'])

def test_citizen_feedback_workflow(client, citizen_headers, inspector_headers):
    issues = client.get('/api/v1/issues', headers=inspector_headers).json()
    target_id = issues[2]['issueId']

    # Citizen confirms resolution
    feed_res = client.post(f'/api/v1/issues/{target_id}/feedback', headers=citizen_headers, json={
        'feedback': 'CONFIRMED_RESOLVED',
        'note': 'Verified in person. Road surface is completely smooth.'
    })
    assert feed_res.status_code == 200
    feed_data = feed_res.json()
    assert feed_data['citizen_feedback']['status'] == 'CONFIRMED_RESOLVED'
    assert any(e['event_type'] == 'CITIZEN_CONFIRMED' for e in feed_data['timeline'])

def test_admin_configuration_permissions(client, citizen_headers, inspector_headers, admin_headers):
    # Citizen cannot manage teams
    c_res = client.post('/api/v1/admin/teams', headers=citizen_headers, json={'name': 'Rogue Team'})
    assert c_res.status_code == 403

    # Officer cannot manage teams
    o_res = client.post('/api/v1/admin/teams', headers=inspector_headers, json={'name': 'Rogue Team'})
    assert o_res.status_code == 403

    # Admin creates new team
    a_res = client.post('/api/v1/admin/teams', headers=admin_headers, json={
        'name': 'Bandra West Quick Litter Patrol',
        'department': 'Solid Waste Management',
        'category': 'Sanitation & Garbage',
        'ward': 'H/West',
        'status': 'AVAILABLE'
    })
    assert a_res.status_code == 200
    created_team = a_res.json()
    team_id = created_team['id']

    # Admin updates team availability
    patch_res = client.patch(f'/api/v1/admin/teams/{team_id}', headers=admin_headers, json={'status': 'BUSY'})
    assert patch_res.status_code == 200
    assert patch_res.json()['status'] == 'BUSY'

    # Admin updates ward configuration
    ward_res = client.patch('/api/v1/admin/wards/N-Ward', headers=admin_headers, json={
        'lead_officer': 'Abhinay',
        'active_teams': ['TEAM-ROAD-01', team_id]
    })
    assert ward_res.status_code == 200
    assert ward_res.json()['lead_officer'] == 'Abhinay'
    assert team_id in ward_res.json()['active_teams']


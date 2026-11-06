import time
import os
import sys
import subprocess
import requests

BASE_URL = "http://localhost:8000/api/v1"

def run_persistence_test():
    print("\n==================================================================")
    print("CIVILENS HIERARCHY RESTART PERSISTENCE AUDIT")
    print("==================================================================")

    # 1. Obtain Admin Token
    login_res = requests.post(
        f"{BASE_URL}/auth/login",
        json={"usernameOrEmail": "admin@civilens.org", "password": "Admin@123"}
    )
    assert login_res.status_code == 200, f"Admin login failed: {login_res.text}"
    token = login_res.json()["token"]
    admin_headers = {"Authorization": f"Bearer {token}"}
    print("✓ Successfully authenticated as Admin.")

    # 2. Load hierarchy before restart
    tree_res = requests.get(f"{BASE_URL}/hierarchy/tree", headers=admin_headers)
    assert tree_res.status_code == 200
    tree_data = tree_res.json()
    assert len(tree_data) == 2, f"Expected 2 authorities, got {len(tree_data)}"
    print(f"✓ Hierarchy loaded: {[a['code'] for a in tree_data]}")

    # 3. Create a disposable test operational sub-ward
    test_sub_code = "SW-PERSIST-99"
    test_sub_name = "Audited Persistence Test Beat 99"
    create_sw_payload = {
        "ward_id": "WARD-BMC-N",
        "sub_ward_code": test_sub_code,
        "name": test_sub_name,
        "supervisor_name": "Audited Supervisor Lead",
        "boundary_geojson": {
            "type": "Polygon",
            "coordinates": [[[72.90, 19.08], [72.91, 19.08], [72.91, 19.09], [72.90, 19.09], [72.90, 19.08]]]
        }
    }
    sw_res = requests.post(f"{BASE_URL}/hierarchy/sub-wards", json=create_sw_payload, headers=admin_headers)
    assert sw_res.status_code == 201, f"Failed creating subward: {sw_res.text}"
    created_sub = sw_res.json()
    test_sub_id = created_sub["id"]
    print(f"✓ Created disposable operational sub-ward: {test_sub_id} ({test_sub_code})")

    # 4. Assign a supervisor to this sub-ward
    sup_payload = {
        "user_id": "INSP-MUMBAI-01",
        "ward_code": "N-Ward",
        "sub_ward_id": test_sub_id,
        "jurisdiction_level": "SUB_WARD_SUPERVISOR"
    }
    sup_res = requests.post(f"{BASE_URL}/hierarchy/supervisors/assign", json=sup_payload, headers=admin_headers)
    assert sup_res.status_code == 200, f"Failed assigning supervisor: {sup_res.text}"
    print(f"✓ Assigned supervisor INSP-MUMBAI-01 to sub-ward {test_sub_id}")

    # 5. Create a disposable field crew assigned to this sub-ward
    team_payload = {
        "name": "Audit Test Alpha Crew 99",
        "department": "Road Infrastructure Maintenance",
        "category": "Roads & Footpaths",
        "capacity": 8,
        "ward": "N-Ward",
        "sub_ward_id": test_sub_id,
        "authority_id": "AUTH-BMC",
        "contact_lead": "Audited Supervisor Lead"
    }
    team_res = requests.post(f"{BASE_URL}/admin/teams", json=team_payload, headers=admin_headers)
    assert team_res.status_code == 200, f"Failed creating field team: {team_res.text}"
    created_team = team_res.json()
    test_team_id = created_team["id"]
    print(f"✓ Created field crew: {test_team_id} ({team_payload['name']}) assigned to {test_sub_id}")

    # 6. Verify pre-restart state in hierarchy tree
    tree_pre = requests.get(f"{BASE_URL}/hierarchy/tree", headers=admin_headers).json()
    bmc_pre = next(a for a in tree_pre if a["code"] == "BMC")
    n_ward_pre = next(w for z in bmc_pre["children"] for w in z["children"] if w["code"] == "N-Ward")
    sub_pre = next((s for s in n_ward_pre["children"] if s["id"] == test_sub_id), None)
    assert sub_pre is not None, "Test sub-ward not found in pre-restart hierarchy tree!"
    assert sub_pre["supervisor_name"] == "Abhinay", f"Expected supervisor Abhinay, got {sub_pre['supervisor_name']}"
    assert any(t["id"] == test_team_id for t in sub_pre.get("assigned_teams", [])), "Test crew not found in pre-restart subward!"
    print(f"✓ Pre-restart verification passed: Sub-ward, supervisor, and crew present in tree.")

    return test_sub_id, test_team_id

if __name__ == "__main__":
    test_sub_id, test_team_id = run_persistence_test()
    print(f"\nPhase 1 Complete. Target IDs for restart verification: sub={test_sub_id}, team={test_team_id}")

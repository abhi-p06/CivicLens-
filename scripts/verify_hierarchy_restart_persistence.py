import requests
import json
import sys

BASE_URL = "http://localhost:8000/api/v1"

def run_post_restart_audit(target_sub_id="SUB-B6430F43", target_team_id="TEAM-948C32"):
    print("\n" + "="*70)
    print("CIVILENS POST-RESTART HIERARCHY PERSISTENCE & AUTHORIZATION AUDIT")
    print("="*70)

    # -------------------------------------------------------------------------
    # 1. Admin Authentication & Hierarchy Tree Verification
    # -------------------------------------------------------------------------
    print("\n--- [STEP 1] Admin Authentication & Tree Structure Verification ---")
    admin_login = requests.post(
        f"{BASE_URL}/auth/login",
        json={"usernameOrEmail": "admin@civilens.org", "password": "Admin@123"}
    )
    assert admin_login.status_code == 200, f"Admin login failed: {admin_login.text}"
    admin_token = admin_login.json()["token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    print("✓ Successfully authenticated as Admin (ADMIN-SYS-01).")

    tree_res = requests.get(f"{BASE_URL}/hierarchy/tree", headers=admin_headers)
    assert tree_res.status_code == 200, f"Hierarchy tree request failed: {tree_res.text}"
    tree = tree_res.json()
    assert len(tree) == 2, f"Expected 2 authorities, got {len(tree)}"

    bmc = next((a for a in tree if a["code"] == "BMC"), None)
    nmmc = next((a for a in tree if a["code"] == "NMMC"), None)
    assert bmc is not None, "BMC authority missing in tree!"
    assert nmmc is not None, "NMMC authority missing in tree!"

    # Verify BMC wards: 7 zones, 24 administrative wards
    bmc_wards = [w for z in bmc["children"] for w in z["children"]]
    assert len(bmc["children"]) == 7, f"Expected 7 BMC zones, got {len(bmc['children'])}"
    assert len(bmc_wards) == 24, f"Expected 24 BMC wards, got {len(bmc_wards)}"
    print(f"✓ BMC Verified: 7 Administrative Zones, 24 Administrative Wards.")

    # Verify NMMC wards: 2 zones, 8 administrative ward offices
    nmmc_wards = [w for z in nmmc["children"] for w in z["children"]]
    assert len(nmmc["children"]) == 2, f"Expected 2 NMMC zones, got {len(nmmc['children'])}"
    assert len(nmmc_wards) == 8, f"Expected 8 NMMC ward offices, got {len(nmmc_wards)}"
    print(f"✓ NMMC Verified: 2 Administrative Zones, 8 Administrative Ward Offices.")

    # -------------------------------------------------------------------------
    # 2. Verify Post-Restart Persistence of Test Records
    # -------------------------------------------------------------------------
    print(f"\n--- [STEP 2] Verifying Post-Restart Persistence of {target_sub_id} & {target_team_id} ---")
    n_ward = next((w for z in bmc["children"] for w in z["children"] if w["code"] == "N-Ward"), None)
    assert n_ward is not None, "N-Ward not found in BMC!"

    persisted_sub = next((s for s in n_ward["children"] if s["id"] == target_sub_id), None)
    assert persisted_sub is not None, f"Disposable sub-ward {target_sub_id} NOT found after server restart!"
    print(f"✓ Operational Sub-Ward {target_sub_id} successfully persisted across full restart.")
    print(f"   - Name: {persisted_sub['name']}")
    print(f"   - Code: {persisted_sub['code']}")

    # Check supervisor assignment persisted
    assert persisted_sub["supervisor_name"] == "Abhinay", (
        f"Supervisor assignment failed to persist! Expected 'Abhinay', got '{persisted_sub['supervisor_name']}'"
    )
    print(f"✓ Supervisor Assignment persisted: '{persisted_sub['supervisor_name']}' (INSP-MUMBAI-01).")

    # Check field crew assignment persisted
    assigned_team_ids = [t["id"] for t in persisted_sub.get("assigned_teams", [])]
    assert target_team_id in assigned_team_ids, (
        f"Field crew {target_team_id} failed to persist in sub-ward teams list! Found: {assigned_team_ids}"
    )
    assigned_team = next(t for t in persisted_sub["assigned_teams"] if t["id"] == target_team_id)
    print(f"✓ Field Crew Assignment persisted: {assigned_team['id']} ('{assigned_team['name']}', capacity: {assigned_team['capacity']}).")

    # -------------------------------------------------------------------------
    # 3. Direct Backend Role-Based Authorization Audit
    # -------------------------------------------------------------------------
    print("\n--- [STEP 3] Role-Based Authorization Audit Across All 3 Roles ---")

    # Municipal Officer Login
    officer_login = requests.post(
        f"{BASE_URL}/auth/login",
        json={"usernameOrEmail": "inspector@civilens.org", "password": "Inspector@123"}
    )
    assert officer_login.status_code == 200
    officer_token = officer_login.json()["token"]
    officer_headers = {"Authorization": f"Bearer {officer_token}"}
    print("✓ Successfully authenticated as Municipal Officer (INSP-MUMBAI-01).")

    # Citizen Login
    citizen_login = requests.post(
        f"{BASE_URL}/auth/login",
        json={"usernameOrEmail": "citizen@civilens.org", "password": "Citizen@123"}
    )
    assert citizen_login.status_code == 200
    citizen_token = citizen_login.json()["token"]
    citizen_headers = {"Authorization": f"Bearer {citizen_token}"}
    print("✓ Successfully authenticated as Citizen (CITIZEN-001).")

    # A) Citizen Authorization Constraints
    print("\n  [Citizen RBAC Gate Checks]")
    # 1. Citizen forbidden from hierarchy tree
    res_cit_tree = requests.get(f"{BASE_URL}/hierarchy/tree", headers=citizen_headers)
    assert res_cit_tree.status_code == 403, f"Citizen expected 403 on tree, got {res_cit_tree.status_code}"
    print("  ✓ Citizen GET /hierarchy/tree -> HTTP 403 Forbidden (Enforced).")

    # 2. Citizen forbidden from sub-ward creation
    res_cit_sw = requests.post(
        f"{BASE_URL}/hierarchy/sub-wards",
        json={"ward_id": "WARD-BMC-N", "sub_ward_code": "SW-CIT-FAIL", "name": "Citizen Illegal Subward"},
        headers=citizen_headers
    )
    assert res_cit_sw.status_code == 403, f"Citizen expected 403 on sub-ward create, got {res_cit_sw.status_code}"
    print("  ✓ Citizen POST /hierarchy/sub-wards -> HTTP 403 Forbidden (Enforced).")

    # 3. Citizen forbidden from team creation
    res_cit_team = requests.post(
        f"{BASE_URL}/admin/teams",
        json={"name": "Citizen Crew", "department": "Road Infrastructure Maintenance"},
        headers=citizen_headers
    )
    assert res_cit_team.status_code == 403, f"Citizen expected 403 on team create, got {res_cit_team.status_code}"
    print("  ✓ Citizen POST /admin/teams -> HTTP 403 Forbidden (Enforced).")

    # 4. Citizen forbidden from supervisor assignment
    res_cit_sup = requests.post(
        f"{BASE_URL}/hierarchy/supervisors/assign",
        json={"user_id": "INSP-MUMBAI-01", "ward_code": "N-Ward"},
        headers=citizen_headers
    )
    assert res_cit_sup.status_code == 403, f"Citizen expected 403 on supervisor assign, got {res_cit_sup.status_code}"
    print("  ✓ Citizen POST /hierarchy/supervisors/assign -> HTTP 403 Forbidden (Enforced).")

    # B) Municipal Officer Authorization Constraints
    print("\n  [Municipal Officer RBAC Gate Checks]")
    # 1. Officer can view tree (both authorities)
    res_off_tree = requests.get(f"{BASE_URL}/hierarchy/tree", headers=officer_headers)
    assert res_off_tree.status_code == 200, f"Officer expected 200 on tree, got {res_off_tree.status_code}"
    off_tree = res_off_tree.json()
    assert len(off_tree) == 2, "Officer tree must contain both BMC and NMMC"
    print("  ✓ Officer GET /hierarchy/tree -> HTTP 200 (Both BMC and NMMC visible).")

    # 2. Officer cannot create sub-wards
    res_off_sw = requests.post(
        f"{BASE_URL}/hierarchy/sub-wards",
        json={"ward_id": "WARD-BMC-N", "sub_ward_code": "SW-OFF-FAIL", "name": "Officer Illegal Subward"},
        headers=officer_headers
    )
    assert res_off_sw.status_code == 403, f"Officer expected 403 on sub-ward create, got {res_off_sw.status_code}"
    print("  ✓ Officer POST /hierarchy/sub-wards -> HTTP 403 Forbidden (Admin only).")

    # 3. Officer cannot create field teams
    res_off_team = requests.post(
        f"{BASE_URL}/admin/teams",
        json={"name": "Officer Crew", "department": "Road Infrastructure Maintenance"},
        headers=officer_headers
    )
    assert res_off_team.status_code == 403, f"Officer expected 403 on team create, got {res_off_team.status_code}"
    print("  ✓ Officer POST /admin/teams -> HTTP 403 Forbidden (Admin only).")

    # 4. Officer cannot assign supervisors
    res_off_sup = requests.post(
        f"{BASE_URL}/hierarchy/supervisors/assign",
        json={"user_id": "INSP-MUMBAI-01", "ward_code": "N-Ward"},
        headers=officer_headers
    )
    assert res_off_sup.status_code == 403, f"Officer expected 403 on supervisor assign, got {res_off_sup.status_code}"
    print("  ✓ Officer POST /hierarchy/supervisors/assign -> HTTP 403 Forbidden (Admin only).")

    # 5. Officer cross-authority operations check
    # Fetch issues to test cross-jurisdiction assignment
    issues_res = requests.get(f"{BASE_URL}/issues", headers=admin_headers)
    assert issues_res.status_code == 200
    all_issues = issues_res.json()
    nmmc_issue = next((i for i in all_issues if getattr(i, "authority_code", "") == "NMMC" or "NMMC" in (i.get("ward") or "")), None)
    bmc_issue = next((i for i in all_issues if i.get("ward") == "N-Ward" or (i.get("ward_id") or "").endswith("-N")), None)

    if nmmc_issue and bmc_issue:
        # BMC Officer attempting to assign team to NMMC issue -> 403 Forbidden
        assign_fail = requests.post(
            f"{BASE_URL}/issues/{nmmc_issue['issueId']}/assign",
            json={"department": "Road Infrastructure Maintenance", "team_name": "Alpha", "instructions": "Unauthorized"},
            headers=officer_headers
        )
        assert assign_fail.status_code == 403, f"Expected 403 for cross-authority assign, got {assign_fail.status_code}"
        print(f"  ✓ BMC Officer assigning NMMC issue {nmmc_issue['issueId']} -> HTTP 403 Forbidden (Enforced).")

        # BMC Officer attempting cross-authority transfer -> 403 Forbidden
        transfer_fail = requests.patch(
            f"{BASE_URL}/issues/{bmc_issue['issueId']}/jurisdiction",
            json={"ward_code": "NMMC-Belapur", "reason": "Unauthorized cross-authority move"},
            headers=officer_headers
        )
        assert transfer_fail.status_code == 403, f"Expected 403 for cross-authority transfer, got {transfer_fail.status_code}"
        print(f"  ✓ BMC Officer transferring BMC issue to NMMC -> HTTP 403 Forbidden (Enforced).")

    # -------------------------------------------------------------------------
    # 4. Clean up disposable test records
    # -------------------------------------------------------------------------
    print("\n--- [STEP 4] Clean up disposable audit records ---")
    del_team = requests.delete(f"{BASE_URL}/admin/teams/{target_team_id}", headers=admin_headers)
    assert del_team.status_code == 200, f"Failed deleting test team {target_team_id}: {del_team.text}"
    print(f"✓ Deleted disposable test team: {target_team_id}")

    del_sw = requests.delete(f"{BASE_URL}/hierarchy/sub-wards/{target_sub_id}", headers=admin_headers)
    assert del_sw.status_code == 200, f"Failed deactivating test sub-ward {target_sub_id}: {del_sw.text}"
    print(f"✓ Deactivated disposable test sub-ward: {target_sub_id}")

    # Verify removal in hierarchy tree
    tree_after = requests.get(f"{BASE_URL}/hierarchy/tree", headers=admin_headers).json()
    bmc_after = next(a for a in tree_after if a["code"] == "BMC")
    n_ward_after = next(w for z in bmc_after["children"] for w in z["children"] if w["code"] == "N-Ward")
    sub_after = next((s for s in n_ward_after["children"] if s["id"] == target_sub_id), None)
    assert sub_after is None, f"Sub-ward {target_sub_id} still present in tree after deactivation!"
    print(f"✓ Verified cleanup: Disposable test sub-ward no longer appears in active hierarchy tree.")

    print("\n" + "="*70)
    print("ALL RESTART PERSISTENCE AND AUTHORIZATION AUDIT CHECKS PASSED")
    print("="*70)

if __name__ == "__main__":
    run_post_restart_audit()


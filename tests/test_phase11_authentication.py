import time
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings
from app.core.security import create_access_token, UserRole, AuthenticatedUser

client = TestClient(app)

# =============================================================================
# PHASE 11: Comprehensive Role-Based Authentication & Security Tests (13 Scenarios)
# =============================================================================

def test_1_valid_citizen_login():
    """1. Valid citizen login succeeds and yields verified citizen token."""
    res = client.post("/api/v1/auth/login", json={
        "usernameOrEmail": "citizen",
        "password": "Citizen@123",
        "expectedRole": "citizen"
    })
    assert res.status_code == 200, res.text
    data = res.json()
    assert "token" in data
    assert data["tokenType"] == "Bearer"
    assert data["user"]["role"] == "citizen"
    assert data["user"]["email"] == "citizen@civilens.org"

    # Verify session via /auth/me
    token = data["token"]
    res_me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res_me.status_code == 200
    assert res_me.json()["role"] == "citizen"


def test_2_valid_inspector_login():
    """2. Valid municipal officer/inspector login succeeds."""
    res = client.post("/api/v1/auth/login", json={
        "usernameOrEmail": "inspector@civilens.org",
        "password": "Inspector@123",
        "expectedRole": "inspector"
    })
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["user"]["role"] == "inspector"
    assert data["user"]["username"] == "inspector"

    # Verify session via /auth/me
    token = data["token"]
    res_me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res_me.status_code == 200
    assert res_me.json()["role"] == "inspector"


def test_3_valid_administrator_login():
    """3. Valid administrator login succeeds with administrative privileges."""
    res = client.post("/api/v1/auth/login", json={
        "usernameOrEmail": "admin",
        "password": "Admin@123",
        "expectedRole": "admin"
    })
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["user"]["role"] == "admin"
    assert data["user"]["email"] == "admin@civilens.org"

    # Verify session via /auth/me
    token = data["token"]
    res_me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res_me.status_code == 200
    assert res_me.json()["role"] == "admin"


def test_4_incorrect_password_rejected():
    """4. Incorrect password is rejected with HTTP 401."""
    res = client.post("/api/v1/auth/login", json={
        "usernameOrEmail": "citizen",
        "password": "WrongPassword999!",
        "expectedRole": "citizen"
    })
    assert res.status_code == 401
    assert "invalid" in res.json()["detail"].lower()


def test_5_unknown_account_rejected():
    """5. Unknown account is rejected with HTTP 401."""
    res = client.post("/api/v1/auth/login", json={
        "usernameOrEmail": "nonexistent_user_12345@civilens.org",
        "password": "SomePassword@123",
        "expectedRole": "citizen"
    })
    assert res.status_code == 401
    assert "invalid" in res.json()["detail"].lower()


def test_6_citizen_attempting_inspector_status_changes_forbidden():
    """6. Citizen attempting inspector-only status change is rejected with HTTP 403."""
    login_res = client.post("/api/v1/auth/login", json={
        "usernameOrEmail": "citizen",
        "password": "Citizen@123"
    })
    token = login_res.json()["token"]
    citizen_headers = {"Authorization": f"Bearer {token}"}

    res = client.patch(
        "/api/v1/issues/CIVIC-2026-001/status",
        headers=citizen_headers,
        json={"status": "Action in Progress"}
    )
    assert res.status_code == 403
    assert "forbidden" in res.json()["detail"].lower()
    assert "inspector" in res.json()["detail"].lower()


def test_7_inspector_attempting_administrator_routing_changes_forbidden():
    """7. Inspector attempting administrator routing changes is rejected with HTTP 403."""
    login_res = client.post("/api/v1/auth/login", json={
        "usernameOrEmail": "inspector",
        "password": "Inspector@123"
    })
    token = login_res.json()["token"]
    inspector_headers = {"Authorization": f"Bearer {token}"}

    res = client.post(
        "/api/v1/routing/config",
        headers=inspector_headers,
        json={
            "category": "Roads & Footpaths",
            "department": "Unauthorized Agency",
            "code": "UNAUTH",
            "actions": {"CRITICAL": ["Unauthorized update", 1]}
        }
    )
    assert res.status_code == 403
    assert "forbidden" in res.json()["detail"].lower()
    assert "admin" in res.json()["detail"].lower()


def test_8_citizen_attempting_administrator_operations_forbidden():
    """8. Citizen attempting administrator operations (demo reset, routing) is rejected with HTTP 403."""
    login_res = client.post("/api/v1/auth/login", json={
        "usernameOrEmail": "citizen",
        "password": "Citizen@123"
    })
    token = login_res.json()["token"]
    citizen_headers = {"Authorization": f"Bearer {token}"}

    # 1. Reset demo
    res_reset = client.post("/api/v1/demo/reset", headers=citizen_headers)
    assert res_reset.status_code == 403
    assert "admin" in res_reset.json()["detail"].lower()

    # 2. Routing config
    res_routing = client.post(
        "/api/v1/routing/config",
        headers=citizen_headers,
        json={
            "category": "Sanitation & Garbage",
            "department": "Unauthorized Corps",
            "code": "UC",
            "actions": {"HIGH": ["Unallowed action", 24]}
        }
    )
    assert res_routing.status_code == 403

    # 3. User administration
    res_users = client.get("/api/v1/admin/users", headers=citizen_headers)
    assert res_users.status_code == 403


def test_9_expired_or_invalid_tokens_rejected():
    """9. Expired or forged/corrupted tokens produce HTTP 401."""
    # 1. Corrupted signature
    res_corrupt = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer not-a-valid-token-payload"})
    assert res_corrupt.status_code == 401

    # 2. Expired token (expires_in_seconds = -10)
    expired_token = create_access_token(
        user_id="EXPIRED-USER-01",
        role=UserRole.CITIZEN,
        name="Expired User",
        expires_in_seconds=-10
    )
    res_expired = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert res_expired.status_code == 401
    assert "authentication required" in res_expired.json()["detail"].lower() or "invalid" in res_expired.json()["detail"].lower()


def test_10_forged_role_values_in_client_requests_rejected():
    """10. Forged role values: Public registration cannot create non-citizen roles."""
    # Attempt to self-register as admin
    res_forge_admin = client.post("/api/v1/auth/register", json={
        "username": "hacker_admin",
        "email": "hacker_admin@civilens.org",
        "name": "Malicious Admin Wannabe",
        "password": "HackerPassword@123",
        "role": "admin"
    })
    assert res_forge_admin.status_code == 403
    assert "restricted to citizen" in res_forge_admin.json()["detail"].lower()

    # Attempt to self-register as inspector
    res_forge_insp = client.post("/api/v1/auth/register", json={
        "username": "hacker_insp",
        "email": "hacker_insp@civilens.org",
        "name": "Malicious Inspector Wannabe",
        "password": "HackerPassword@123",
        "role": "inspector"
    })
    assert res_forge_insp.status_code == 403
    assert "restricted to citizen" in res_forge_insp.json()["detail"].lower()


def test_11_citizen_complaint_ownership_and_data_isolation():
    """11. Citizen complaint ownership and data isolation: citizens only see their owned complaints."""
    # Register two distinct citizens
    res_u1 = client.post("/api/v1/auth/register", json={
        "username": "citizen_priya",
        "email": "priya@example.com",
        "name": "Priya Sharma",
        "password": "Password@123"
    })
    assert res_u1.status_code == 200, res_u1.text
    token_u1 = res_u1.json()["token"]
    u1_id = res_u1.json()["user"]["userId"]

    res_u2 = client.post("/api/v1/auth/register", json={
        "username": "citizen_rahul",
        "email": "rahul@example.com",
        "name": "Rahul Verma",
        "password": "Password@123"
    })
    assert res_u2.status_code == 200, res_u2.text
    token_u2 = res_u2.json()["token"]
    u2_id = res_u2.json()["user"]["userId"]

    # Priya submits a pothole complaint
    res_submit_priya = client.post(
        "/api/v1/issues",
        headers={"Authorization": f"Bearer {token_u1}"},
        json={
            "complaintText": "Deep road crater in Kurla near junction",
            "location": "Kurla West",
            "source": "citizen_portal"
        }
    )
    assert res_submit_priya.status_code == 201
    priya_issue_id = res_submit_priya.json()["issueId"]

    # Rahul submits a garbage complaint
    res_submit_rahul = client.post(
        "/api/v1/issues",
        headers={"Authorization": f"Bearer {token_u2}"},
        json={
            "complaintText": "Overflowing waste bin outside Vidyavihar station",
            "location": "Vidyavihar East",
            "source": "citizen_portal"
        }
    )
    assert res_submit_rahul.status_code == 201
    rahul_issue_id = res_submit_rahul.json()["issueId"]

    # Priya queries /issues/my -> sees her issue, NOT Rahul's
    res_priya_my = client.get("/api/v1/issues/my", headers={"Authorization": f"Bearer {token_u1}"})
    assert res_priya_my.status_code == 200
    priya_issues = res_priya_my.json()
    priya_ids = [i["issueId"] for i in priya_issues]
    assert priya_issue_id in priya_ids
    assert rahul_issue_id not in priya_ids

    # Rahul queries /issues/my -> sees his issue, NOT Priya's
    res_rahul_my = client.get("/api/v1/issues/my", headers={"Authorization": f"Bearer {token_u2}"})
    assert res_rahul_my.status_code == 200
    rahul_issues = res_rahul_my.json()
    rahul_ids = [i["issueId"] for i in rahul_issues]
    assert rahul_issue_id in rahul_ids
    assert priya_issue_id not in rahul_ids


def test_12_development_credentials_rejected_in_production():
    """12. Development credentials strictly rejected in production environment."""
    with patch.object(settings, "allow_dev_tokens", False):
        res = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer demo-inspector-token"})
        assert res.status_code == 401

        res_admin = client.post("/api/v1/demo/reset", headers={"Authorization": "Bearer demo-admin-token"})
        assert res_admin.status_code == 401

    with patch.object(settings, "env", "production"):
        res = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer demo-inspector-token"})
        assert res.status_code == 401


def test_13_logout_and_session_lifecycle():
    """13. Logout endpoint returns success and invalidates client session."""
    login_res = client.post("/api/v1/auth/login", json={
        "usernameOrEmail": "citizen",
        "password": "Citizen@123"
    })
    token = login_res.json()["token"]

    res_logout = client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert res_logout.status_code == 200
    assert res_logout.json()["status"] == "success"

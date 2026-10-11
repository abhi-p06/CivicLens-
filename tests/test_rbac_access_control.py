import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings
from app.core.security import UserRole, DEV_TOKENS

client = TestClient(app)

# Helper headers
CITIZEN_HEADERS = {}  # Public unauthenticated
INSPECTOR_HEADERS = {"Authorization": "Bearer demo-inspector-token"}
ADMIN_HEADERS = {"Authorization": "Bearer demo-admin-token"}
INVALID_HEADERS = {"Authorization": "Bearer invalid-tampered-token-999"}

def test_citizen_public_endpoints_accessible():
    """Verify that Citizen public endpoints remain freely accessible without authentication."""
    # 1. Health
    res_health = client.get("/api/v1/health", headers=CITIZEN_HEADERS)
    assert res_health.status_code == 200

    # 2. View issues
    res_issues = client.get("/api/v1/issues", headers=CITIZEN_HEADERS)
    assert res_issues.status_code == 200

    # 3. View GIS GeoJSON
    res_gis = client.get("/api/v1/gis/geojson", headers=CITIZEN_HEADERS)
    assert res_gis.status_code == 200

    # 4. View hotspots
    res_hotspots = client.get("/api/v1/hotspots", headers=CITIZEN_HEADERS)
    assert res_hotspots.status_code == 200

    # 5. Stateless complaint analysis
    res_analyze = client.post(
        "/api/v1/analyze",
        headers=CITIZEN_HEADERS,
        json={"complaintText": "Deep crater on road near station"}
    )
    assert res_analyze.status_code == 200

    # 6. Citizen complaint submission
    res_submit = client.post(
        "/api/v1/issues",
        headers=CITIZEN_HEADERS,
        json={
            "complaintText": "Citizen submitted pothole on central road",
            "location": "Vidyavihar",
            "source": "citizen_portal"
        }
    )
    assert res_submit.status_code == 201


def test_unauthenticated_requests_to_protected_endpoints_rejected_with_401():
    """Verify that unauthenticated callers are rejected with HTTP 401 on protected endpoints."""
    # 1. Status update
    res_status = client.patch(
        "/api/v1/issues/CIVIC-2026-001/status",
        headers=CITIZEN_HEADERS,
        json={"status": "Action in Progress"}
    )
    assert res_status.status_code == 401
    assert "authentication required" in res_status.json()["detail"].lower()

    # 2. Resolution verification
    res_verify = client.post(
        "/api/v1/issues/CIVIC-2026-001/verify",
        headers=CITIZEN_HEADERS,
        json={"resolutionImageUrl": "data/test_samples/repair_pothole_after_repaired.jpg"}
    )
    assert res_verify.status_code == 401
    assert "authentication required" in res_verify.json()["detail"].lower()

    # 3. Routing configuration
    res_routing = client.post(
        "/api/v1/routing/config",
        headers=CITIZEN_HEADERS,
        json={"category": "Roads & Footpaths", "department": "Test Dept", "code": "TD-01", "actions": {}}
    )
    assert res_routing.status_code == 401
    assert "authentication required" in res_routing.json()["detail"].lower()

    # 4. Demo reset
    res_reset = client.post("/api/v1/demo/reset", headers=CITIZEN_HEADERS)
    assert res_reset.status_code == 401
    assert "authentication required" in res_reset.json()["detail"].lower()


def test_invalid_or_malformed_tokens_rejected_with_401():
    """Verify that tampered or unknown Bearer tokens produce HTTP 401."""
    res = client.patch(
        "/api/v1/issues/CIVIC-2026-001/status",
        headers=INVALID_HEADERS,
        json={"status": "Action in Progress"}
    )
    assert res.status_code == 401
    assert "invalid or expired" in res.json()["detail"].lower()


def test_inspector_role_permissions_and_boundaries():
    """Verify that Inspector role can update status and verify resolution, but CANNOT perform admin actions."""
    # 1. Inspector CAN update status
    res_status = client.patch(
        "/api/v1/issues/CIVIC-2026-001/status",
        headers=INSPECTOR_HEADERS,
        json={"status": "Action in Progress", "note": "Field crew dispatched"}
    )
    assert res_status.status_code == 200
    assert res_status.json()["status"] == "ACTION IN PROGRESS"

    # 2. Inspector CAN verify resolution
    res_verify = client.post(
        "/api/v1/issues/CIVIC-2026-001/verify",
        headers=INSPECTOR_HEADERS,
        json={
            "resolutionImageUrl": "data/test_samples/repair_pothole_after_repaired.jpg",
            "notes": "Verified by inspector"
        }
    )
    assert res_verify.status_code == 200

    # 3. Inspector CANNOT modify routing rules (HTTP 403 Forbidden)
    res_routing = client.post(
        "/api/v1/routing/config",
        headers=INSPECTOR_HEADERS,
        json={
            "category": "Roads & Footpaths",
            "department": "Rogue Dept",
            "code": "ROGUE",
            "actions": {"CRITICAL": ["Unauthorized change", 1]}
        }
    )
    assert res_routing.status_code == 403
    assert "forbidden" in res_routing.json()["detail"].lower()
    assert "admin privileges" in res_routing.json()["detail"].lower()

    # 4. Inspector CANNOT trigger destructive demo reset (HTTP 403 Forbidden)
    res_reset = client.post("/api/v1/demo/reset", headers=INSPECTOR_HEADERS)
    assert res_reset.status_code == 403
    assert "forbidden" in res_reset.json()["detail"].lower()


def test_admin_role_full_permissions():
    """Verify that Admin role has full authority across status, verify, routing, and reset."""
    # 1. Admin status update
    res_status = client.patch(
        "/api/v1/issues/CIVIC-2026-001/status",
        headers=ADMIN_HEADERS,
        json={"status": "Prioritized", "note": "Administrator override"}
    )
    assert res_status.status_code == 200

    # 2. Admin routing config update
    res_routing = client.post(
        "/api/v1/routing/config",
        headers=ADMIN_HEADERS,
        json={
            "category": "Sanitation & Garbage",
            "department": "Clean City Admin Corps",
            "code": "CCAC-01",
            "actions": {"HIGH": ["Same-day clearance", 12]}
        }
    )
    assert res_routing.status_code == 200
    assert res_routing.json()["status"] == "success"

    # 3. Admin demo reset
    res_reset = client.post("/api/v1/demo/reset", headers=ADMIN_HEADERS)
    assert res_reset.status_code == 200
    assert "reset" in res_reset.json()["message"].lower()


def test_server_side_inspector_identity_prevents_client_spoofing():
    """Verify that server-validated identity overrides arbitrary client inspectorId payload field."""
    # Client sends fake spoofed inspectorId in JSON payload
    spoofed_client_payload = {
        "inspectorId": "SPOOFED_UNAUTHORIZED_HACKER_ID_999",
        "resolutionImageUrl": "data/test_samples/repair_pothole_after_repaired.jpg",
        "notes": "Quality audit by field staff"
    }

    res = client.post(
        "/api/v1/issues/CIVIC-2026-001/verify",
        headers=INSPECTOR_HEADERS,  # maps to INSP-MUMBAI-01
        json=spoofed_client_payload
    )
    assert res.status_code == 200
    issue_data = res.json()

    # Crucial security verification:
    # Server recorded authenticated inspector "INSP-MUMBAI-01", completely ignoring spoofed ID!
    recorded_evidence = issue_data["resolutionEvidence"]
    assert recorded_evidence["inspector_id"] == "INSP-MUMBAI-01"
    assert recorded_evidence["inspector_id"] != "SPOOFED_UNAUTHORIZED_HACKER_ID_999"


def test_x_api_key_header_support():
    """Verify that X-API-Key header functions equivalently to Authorization: Bearer."""
    res = client.patch(
        "/api/v1/issues/CIVIC-2026-001/status",
        headers={"X-API-Key": "demo-inspector-token"},
        json={"status": "Action in Progress"}
    )
    assert res.status_code == 200


def test_production_mode_rejects_dev_tokens():
    """Verify that when dev tokens are disabled in production, demo tokens are strictly rejected."""
    with patch.object(settings, "allow_dev_tokens", False):
        res = client.patch(
            "/api/v1/issues/CIVIC-2026-001/status",
            headers=INSPECTOR_HEADERS,
            json={"status": "Action in Progress"}
        )
        assert res.status_code == 401

        # But configured environment keys continue to work
        with patch.object(settings, "inspector_api_key", "super-secret-prod-key-xyz"):
            res_prod = client.patch(
                "/api/v1/issues/CIVIC-2026-001/status",
                headers={"Authorization": "Bearer super-secret-prod-key-xyz"},
                json={"status": "Action in Progress"}
            )
            assert res_prod.status_code == 200

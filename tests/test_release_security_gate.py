import os
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings
from app.core.security import authenticate_credentials, UserRole

client = TestClient(app)

CITIZEN_HEADERS = {}
INSPECTOR_HEADERS = {"Authorization": "Bearer demo-inspector-token"}
ADMIN_HEADERS = {"Authorization": "Bearer demo-admin-token"}
INVALID_HEADERS = {"Authorization": "Bearer fake-token-12345"}


def test_rbac_distinct_permissions():
    """Verify distinct permission boundaries for citizen, inspector, and admin."""
    # Citizen can view issues (public)
    res_list = client.get("/api/v1/issues")
    assert res_list.status_code == 200

    # Citizen CANNOT update status (requires inspector)
    res_c_status = client.patch(
        "/api/v1/issues/CIVIC-2026-001/status",
        headers=CITIZEN_HEADERS,
        json={"status": "Action in Progress"}
    )
    assert res_c_status.status_code == 401

    # Inspector CAN update status
    res_i_status = client.patch(
        "/api/v1/issues/CIVIC-2026-001/status",
        headers=INSPECTOR_HEADERS,
        json={"status": "Action in Progress", "note": "Assigned to road crew"}
    )
    assert res_i_status.status_code == 200

    # Inspector CANNOT update routing rules (requires admin, returns 403)
    res_i_route = client.post(
        "/api/v1/routing/config",
        headers=INSPECTOR_HEADERS,
        json={"category": "Roads & Footpaths", "department": "Unauthorized", "code": "UA", "actions": {}}
    )
    assert res_i_route.status_code == 403

    # Admin CAN update routing rules
    res_a_route = client.post(
        "/api/v1/routing/config",
        headers=ADMIN_HEADERS,
        json={
            "category": "Roads & Footpaths",
            "department": "Road Maintenance Division",
            "code": "RMD-01",
            "actions": {"CRITICAL": ["Dispatch emergency crew", 4]}
        }
    )
    assert res_a_route.status_code == 200


def test_server_identity_cannot_be_overridden_by_request_body():
    """Verify request-body identity fields cannot override server-authenticated identity."""
    spoofed_payload = {
        "inspectorId": "ATTACKER_SPOOFED_ID_9999",
        "actor": "ATTACKER_OVERRIDE",
        "resolutionImageUrl": "data/test_samples/repair_pothole_after_repaired.jpg",
        "notes": "Field resolution verified"
    }

    res = client.post(
        "/api/v1/issues/CIVIC-2026-001/verify",
        headers=INSPECTOR_HEADERS,  # maps server-side to INSP-MUMBAI-01
        json=spoofed_payload
    )
    assert res.status_code == 200
    issue_data = res.json()
    assert issue_data["resolutionEvidence"]["inspector_id"] == "INSP-MUMBAI-01"
    assert issue_data["resolutionEvidence"]["inspector_id"] != "ATTACKER_SPOOFED_ID_9999"


def test_production_mode_strictly_rejects_development_tokens():
    """Verify that in production mode (CIVILENS_ENV=production), dev tokens are unconditionally rejected."""
    with patch.object(settings, "env", "production"):
        # Even with allow_dev_tokens=True or civilens_demo_mode=True, production MUST reject dev tokens
        assert authenticate_credentials("Bearer demo-inspector-token") is None
        assert authenticate_credentials("Bearer demo-admin-token") is None

        res_insp = client.patch(
            "/api/v1/issues/CIVIC-2026-001/status",
            headers=INSPECTOR_HEADERS,
            json={"status": "Action in Progress"}
        )
        assert res_insp.status_code == 401

        res_admin = client.post(
            "/api/v1/demo/reset",
            headers=ADMIN_HEADERS
        )
        assert res_admin.status_code == 401


def test_production_environment_api_keys_work_in_production():
    """Verify configured environment API keys work properly when production mode is active."""
    with patch.object(settings, "env", "production"):
        with patch.object(settings, "inspector_api_key", "prod-secret-inspector-key-888"):
            user = authenticate_credentials("Bearer prod-secret-inspector-key-888")
            assert user is not None
            assert user.role == UserRole.INSPECTOR
            assert user.user_id == "INSP-ENV-01"


def test_cors_does_not_permit_wildcard_with_credentials():
    """Verify that wildcard CORS does not enable credentials."""
    from app.main import app
    from fastapi.middleware.cors import CORSMiddleware

    # Check the registered CORSMiddleware instance on app
    cors_mw = None
    for mw in app.user_middleware:
        if mw.cls == CORSMiddleware:
            cors_mw = mw
            break

    assert cors_mw is not None
    # If allowed_origins contains "*", allow_credentials MUST be False
    origins = cors_mw.kwargs.get("allow_origins", [])
    allow_credentials = cors_mw.kwargs.get("allow_credentials", False)
    if "*" in origins:
        assert allow_credentials is False, "Unsafe wildcard-plus-credentials detected in CORS configuration!"


def test_image_upload_security_sanitization():
    """Verify that image upload safely rejects path traversal and non-image payloads."""
    # 1. Path traversal attempt in upload
    traversal_bytes = b"Not an image at all"
    res = client.post(
        "/api/v1/upload",
        files={"file": ("../../etc/passwd", traversal_bytes, "image/jpeg")}
    )
    # Rejection: invalid image format / decompression error / bad request
    assert res.status_code in [400, 422]

    # 2. Path traversal in retrieval endpoint
    res_get = client.get("/api/v1/uploads/../../etc/passwd")
    assert res_get.status_code in [400, 404]

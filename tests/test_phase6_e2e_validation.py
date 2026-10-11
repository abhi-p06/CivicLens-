"""
CIVILENS Phase 6: Complete End-to-End System Validation Suite
============================================================
Comprehensive test suite validating:
- Section 2: Complete Complaint Lifecycle (Steps 1 to 9)
- Section 3: Additional End-to-End Scenarios (Scenarios A through J)
- Section 4: Full API Contract & Registered Endpoints (All 18 endpoints)
- Section 6: Security, Integrity, Error Handling & Persistence
"""

import os
import io
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from app.models.issue import (
    Issue,
    IssueCreate,
    IssueStatus,
    IssueCategory,
    PriorityLevel,
    ResolutionStatus,
    ResolutionEvidence
)
from app.config import settings, PROJECT_ROOT
from app.db.database import build_engine, get_session_factory, Base
from app.db.repository import SqliteIssueRepository
from app.core.demo_store import demo_store
from app.core.pipeline import pipeline
from app.modules.vision.yolo_detector import yolo_detector
from app.modules.lifecycle.tracker import lifecycle_tracker
from app.modules.cross_validation.validator import cross_validation_engine, ConsistencyLevel
from app.modules.spatiotemporal.hotspot import hotspot_detector
from app.modules.spatiotemporal.recurring import recurring_detector
from app.modules.routing.dispatcher import department_dispatcher

client = TestClient(app)
client.headers["Authorization"] = "Bearer demo-admin-token"


# ==============================================================================
# SECTION 2: COMPLETE COMPLAINT LIFECYCLE (STEPS 1 - 9)
# ==============================================================================

def test_section_2_complete_complaint_lifecycle():
    """
    Executes the complete 9-step complaint lifecycle on an isolated test database:
    1. Submission via upload and issue creation
    2. NLP Analysis
    3. Computer Vision inference (real YOLOv8s)
    4. Text-image Cross-Validation
    5. Duplicates & Spatiotemporal analysis
    6. Priority calculation & department routing
    7. Persistence across repository reinitialization
    8. Frontend API schema alignment
    9. Resolution verification with before/after CV delta analysis
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Isolated test database and repository
        test_db = Path(tmpdir) / "test_lifecycle.db"
        test_engine = build_engine(test_db)
        Base.metadata.create_all(bind=test_engine)
        test_factory = get_session_factory(test_engine)
        test_repo = SqliteIssueRepository(session_factory=test_factory)

        # ----------------------------------------------------------------------
        # STEP 1: Submission
        # ----------------------------------------------------------------------
        complaint_text = "There is a large pothole near a school gate on the main road. Vehicles are struggling to pass."
        with open("data/test_samples/repair_pothole_before.jpg", "rb") as f:
            upload_res = client.post(
                "/api/v1/upload",
                files={"file": ("before_pothole.jpg", f.read(), "image/jpeg")}
            )
        assert upload_res.status_code == 200
        upload_data = upload_res.json()
        upload_id = upload_data["uploadId"]
        preview_url = upload_data["previewUrl"]
        assert upload_id is not None
        assert "/uploads/" in preview_url

        create_payload = IssueCreate(
            complaintText=complaint_text,
            location="Somaiya Vidyavihar Main Gate",
            latitude=19.0728,
            longitude=72.8998,
            imageUrl=preview_url,
            uploadId=upload_id,
            source="citizen_mobile_test"
        )

        # ----------------------------------------------------------------------
        # STEP 2: NLP Analysis
        # ----------------------------------------------------------------------
        analysis = pipeline.analyze(create_payload)
        assert analysis["category"] == IssueCategory.ROAD_DAMAGE
        assert analysis["categoryConfidence"] >= 0.30
        assert analysis["urgency"] >= 0.60
        assert analysis["textSeverity"] >= 0.60
        assert analysis["classificationMode"] in ["real_ml", "trained_in_memory", "rule_fallback", "model_inference"]
        assert "Somaiya Vidyavihar" in analysis["resolvedLocation"] or analysis["resolvedLocation"] == "Somaiya Vidyavihar Main Gate"

        # ----------------------------------------------------------------------
        # STEP 3: Computer Vision (Real YOLOv8s Inference)
        # ----------------------------------------------------------------------
        assert yolo_detector.is_model_available() is True
        assert analysis["visionMode"] in ["real_yolo_inference", "real_yolo_rdd2022"]
        assert len(analysis["detectedObjects"]) > 0
        pothole_det = next((d for d in analysis["detectedObjects"] if "Pothole" in d.label or "D40" in d.label), None)
        assert pothole_det is not None
        assert pothole_det.confidence > 0.25
        assert len(pothole_det.bbox) == 4
        # Normalized bounding box coordinates within [0, 1]
        for coord in pothole_det.bbox:
            assert 0.0 <= coord <= 1.0

        # ----------------------------------------------------------------------
        # STEP 4: Cross-Validation
        # ----------------------------------------------------------------------
        assert analysis["consistencyLevel"] == "CONSISTENT"
        assert analysis["evidenceConsistency"] >= 0.85
        reason_str = getattr(analysis["consistencyDetail"], "reason", str(analysis["consistencyDetail"])).lower()
        assert "consist" in reason_str or "align" in reason_str or "agree" in reason_str

        # ----------------------------------------------------------------------
        # STEP 5: Duplicates and Spatiotemporal Analysis
        # ----------------------------------------------------------------------
        assert "isDuplicate" in analysis
        assert "nearDuplicateCount" in analysis
        assert "isHotspot" in analysis
        assert "recurrence" in analysis

        # ----------------------------------------------------------------------
        # STEP 6: Priority and Routing
        # ----------------------------------------------------------------------
        p_score = analysis["priorityScore"]
        breakdown = analysis["priorityBreakdown"]
        b_dict = breakdown.model_dump() if hasattr(breakdown, "model_dump") else (breakdown if isinstance(breakdown, dict) else breakdown.__dict__)
        # Verify authoritative 6-factor additive formula: U(20) + T(20) + V(20) + F(15) + R(10) + L(15) = 100
        calc_total = (
            b_dict["urgency_points"] +
            b_dict["visual_severity_points"] +
            b_dict["text_severity_points"] +
            b_dict["related_reports_points"] +
            b_dict["recency_points"] +
            b_dict["location_risk_points"]
        )
        assert abs(p_score - calc_total) < 0.1
        assert analysis["priorityLevel"] in [PriorityLevel.MEDIUM, PriorityLevel.HIGH, PriorityLevel.CRITICAL]
        assert "Roads" in analysis["department"]
        assert analysis["slaHours"] in [12, 24, 48]
        assert len(analysis["recommendedAction"]) > 10

        # ----------------------------------------------------------------------
        # STEP 7: Persistence across Restart
        # ----------------------------------------------------------------------
        saved_issue = pipeline.process_complaint(create_payload)
        test_repo.add_issue(saved_issue)
        assert saved_issue is not None
        test_issue_id = saved_issue.issueId

        # Update status
        updated = test_repo.update_status(test_issue_id, IssueStatus.ACTION_IN_PROGRESS)
        assert updated.status == IssueStatus.ACTION_IN_PROGRESS

        # Simulate full restart by creating a new repository instance pointing to the same DB
        restarted_repo = SqliteIssueRepository(session_factory=test_factory)
        reloaded = restarted_repo.get_issue(test_issue_id)
        assert reloaded is not None
        assert reloaded.status == IssueStatus.ACTION_IN_PROGRESS
        assert reloaded.imageUrl == preview_url
        assert reloaded.uploadId == upload_id
        assert reloaded.priorityScore == p_score
        assert len(reloaded.detectedObjects) > 0

        # ----------------------------------------------------------------------
        # STEP 8: Frontend Contract Compatibility
        # ----------------------------------------------------------------------
        # Convert to Pydantic dictionary to ensure no missing frontend-required fields
        issue_dict = reloaded.model_dump()
        required_frontend_fields = [
            "issueId", "complaintText", "category", "urgency", "severity",
            "location", "latitude", "longitude", "status", "priorityScore",
            "priorityLevel", "department", "recommendedAction", "slaHours"
        ]
        for field in required_frontend_fields:
            assert field in issue_dict, f"Missing required frontend field: {field}"

        # ----------------------------------------------------------------------
        # STEP 9: Resolution Verification with Before/After CV Delta
        # ----------------------------------------------------------------------
        # Upload post-repair image (asphalt patch)
        with open("data/test_samples/repair_pothole_after_repaired.jpg", "rb") as f2:
            res_up = client.post(
                "/api/v1/upload",
                files={"file": ("after_repair.jpg", f2.read(), "image/jpeg")}
            )
        assert res_up.status_code == 200
        res_upload_id = res_up.json()["uploadId"]

        evidence = lifecycle_tracker.verify_resolution(
            issue=reloaded,
            inspector_id="INSP-QA-STAGE-9",
            resolution_upload_id=res_upload_id,
            notes="Cold mix asphalt patch leveled and rolled."
        )
        assert evidence.resolutionStatus == ResolutionStatus.LIKELY_RESOLVED
        assert evidence.sceneComparable is True
        assert evidence.comparisonMetrics["ssim"] > 0.50
        assert evidence.comparisonMetrics["histogramCorrelation"] > 0.80
        assert len(evidence.afterDetections) == 0
        assert evidence.requiresManualReview is False

        # Transactionally persist verification in isolated repository
        final_issue = test_repo.record_verification(test_issue_id, evidence)
        assert final_issue.status == IssueStatus.RESOLVED

        # Check history preservation
        history = test_repo.get_verification_history(test_issue_id)
        assert len(history) == 1
        assert history[0].resolutionStatus == ResolutionStatus.LIKELY_RESOLVED


# ==============================================================================
# SECTION 3: ADDITIONAL END-TO-END SCENARIOS (A THROUGH J)
# ==============================================================================

def test_scenario_a_high_risk_pothole():
    """Scenario A: High-risk pothole complaint with a relevant uploaded image."""
    payload = IssueCreate(
        complaintText="Critical deep crater and broken asphalt in front of school gate, high collision risk",
        location="Somaiya Vidyavihar",
        latitude=19.0728,
        longitude=72.8998,
        imageUrl="data/test_samples/repair_pothole_before.jpg"
    )
    result = pipeline.analyze(payload)
    assert result["category"] == IssueCategory.ROAD_DAMAGE
    assert result["priorityLevel"] in [PriorityLevel.MEDIUM, PriorityLevel.HIGH, PriorityLevel.CRITICAL]
    assert len(result["detectedObjects"]) > 0
    assert result["consistencyLevel"] == "CONSISTENT"


def test_scenario_b_garbage_accumulation():
    """Scenario B: Garbage accumulation complaint with image that does not show a pothole."""
    payload = IssueCreate(
        complaintText="Overflowing garbage dump and rotting waste on main road, unbearable stench",
        location="Ghatkopar West",
        latitude=19.0856,
        longitude=72.9082,
        imageUrl="data/sample_garbage.jpg"
    )
    result = pipeline.analyze(payload)
    assert result["category"] == IssueCategory.SANITATION
    assert "Solid Waste" in result["department"] or "Sanitation" in result["department"]
    # The road-damage YOLO detector honestly detects 0 road defects in garbage photo
    rdd_potholes = [d for d in result["detectedObjects"] if "D40" in d.label]
    assert len(rdd_potholes) == 0


def test_scenario_c_water_leakage_mismatched_evidence():
    """Scenario C: Water leakage complaint with mismatched visual evidence (pothole image)."""
    val = cross_validation_engine.validate_consistency(
        category=IssueCategory.WATER_SUPPLY,
        complaint_text="Major drinking water main line burst, clean water gushing onto street",
        visual_detection="Pothole (D40)",
        visual_confidence=0.92
    )
    assert val.consistencyLevel == ConsistencyLevel.INCONSISTENT
    assert val.consistencyScore < 0.40
    assert "discrepancy" in val.reason.lower() or "mismatch" in val.reason.lower()


def test_scenario_d_image_only_unreported_issue():
    """Scenario D: Image-only issue submission for the unreported-issue workflow."""
    complaint = IssueCreate(
        complaintText="",
        location="Kurla West",
        imageUrl="data/test_samples/repair_pothole_before.jpg"
    )
    auto_issue = pipeline.process_complaint(complaint)
    assert auto_issue is not None
    assert auto_issue.category == IssueCategory.ROAD_DAMAGE
    assert auto_issue.visualConfidence > 0.25
    assert len(auto_issue.detectedObjects) > 0
    assert "Auto-detected" in auto_issue.complaintText
    assert auto_issue.metadata.get("isAutoDrafted") is True


def test_scenario_e_two_complaints_same_incident():
    """Scenario E: Two complaints describing the same incident (duplicate grouping)."""
    p1 = IssueCreate(
        complaintText="Deep pothole in front of Somaiya Vidyavihar campus gate damaging cars",
        location="Somaiya Vidyavihar",
        latitude=19.0728,
        longitude=72.8998
    )
    p2 = IssueCreate(
        complaintText="Massive pothole at Vidyavihar gate vehicles getting stuck",
        location="Somaiya Vidyavihar",
        latitude=19.0728,
        longitude=72.8998
    )
    r1 = pipeline.analyze(p1)
    r2 = pipeline.analyze(p2)
    assert r1["duplicateGroup"] is not None
    assert r2["duplicateGroup"] is not None


def test_scenario_f_multiple_issues_concentrated_near_same_location():
    """Scenario F: Multiple issues concentrated near the same location across time."""
    issues = demo_store.list_issues()
    # Somaiya Vidyavihar cluster in demo seed
    vidyavihar_issues = [i for i in issues if "Vidyavihar" in i.location]
    assert len(vidyavihar_issues) >= 2
    rec = recurring_detector.evaluate_recurrence(
        lat=19.0728,
        lng=72.8998,
        category=IssueCategory.ROAD_DAMAGE,
        location_name="Somaiya Vidyavihar Main Gate",
        existing_issues=issues,
        radius_meters=500.0
    )
    assert rec.recurringIssue is True
    assert rec.reportCount >= 2


def test_scenario_g_resolution_attempt_defect_remains_visible():
    """Scenario G: Resolution attempt where the defect remains visible in post-action image."""
    issue = demo_store.get_issue("CIVIC-2026-001")
    assert issue is not None
    issue.imageUrl = "data/test_samples/repair_pothole_before.jpg"

    evidence = lifecycle_tracker.verify_resolution(
        issue=issue,
        inspector_id="INSP-QA-G",
        resolution_image_url="data/test_samples/repair_pothole_before.jpg"
    )
    assert evidence.resolutionStatus == ResolutionStatus.STILL_PRESENT
    assert evidence.post_repair_cv_cleared is False
    assert len(evidence.afterDetections) > 0


def test_scenario_h_resolution_attempt_ambiguous_comparison():
    """Scenario H: Resolution attempt where comparison is ambiguous (incompatible scene)."""
    issue = demo_store.get_issue("CIVIC-2026-001")
    assert issue is not None
    issue.imageUrl = "data/test_samples/repair_pothole_before.jpg"

    evidence = lifecycle_tracker.verify_resolution(
        issue=issue,
        inspector_id="INSP-QA-H",
        resolution_image_url="data/test_samples/incompatible_scene.jpg"
    )
    assert evidence.resolutionStatus == ResolutionStatus.REQUIRES_MANUAL_VERIFICATION
    assert evidence.sceneComparable is False
    assert evidence.requiresManualReview is True


def test_scenario_i_invalid_corrupt_or_unsupported_upload():
    """Scenario I: Invalid, corrupt or unsupported uploaded image rejected."""
    # 1. Unsupported extension / MIME
    fake_exe = io.BytesIO(b"MZ\x90\x00\x03\x00\x00\x00")
    res_bad_type = client.post(
        "/api/v1/upload",
        files={"file": ("malware.exe", fake_exe, "application/octet-stream")}
    )
    assert res_bad_type.status_code in [400, 415]

    # 2. Corrupt file payload
    with open("data/test_samples/corrupt_file.jpg", "rb") as f:
        res_corrupt = client.post(
            "/api/v1/upload",
            files={"file": ("corrupt.jpg", f.read(), "image/jpeg")}
        )
    assert res_corrupt.status_code == 400


def test_scenario_j_unavailable_model_graceful_handling():
    """Scenario J: Unavailable model or inference failure handles gracefully."""
    issue = demo_store.get_issue("CIVIC-2026-001")
    assert issue is not None

    with patch.object(yolo_detector, "_get_model", return_value=None):
        evidence = lifecycle_tracker.verify_resolution(
            issue=issue,
            inspector_id="INSP-QA-J",
            resolution_image_url="data/test_samples/repair_pothole_after_repaired.jpg"
        )
        # Never falsely marks resolved when detector is unavailable!
        assert evidence.resolutionStatus == ResolutionStatus.REQUIRES_MANUAL_VERIFICATION
        assert evidence.post_repair_cv_cleared is False


# ==============================================================================
# SECTION 4: API CONTRACT AND REGISTERED ENDPOINTS (ALL 18 ENDPOINTS)
# ==============================================================================

def test_api_endpoint_01_health():
    """1. GET /api/v1/health"""
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "subsystems" in data
    assert "vision_detector" in data["subsystems"]
    assert "resolution_verification" in data["subsystems"]


def test_api_endpoint_02_analyze():
    """2. POST /api/v1/analyze"""
    res = client.post(
        "/api/v1/analyze",
        json={
            "complaintText": "Burst pipe flooding road near Kurla station",
            "location": "Kurla",
            "source": "api_test"
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data["category"] == "Water Supply & Drainage"
    assert "priorityScore" in data


def test_api_endpoint_03_list_issues():
    """3. GET /api/v1/issues"""
    res = client.get("/api/v1/issues")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_api_endpoint_04_create_issue():
    """4. POST /api/v1/issues"""
    res = client.post(
        "/api/v1/issues",
        json={
            "complaintText": "Dangerous live wire sparking on electric pole in Dadar",
            "location": "Dadar West",
            "source": "api_test"
        }
    )
    assert res.status_code == 201
    data = res.json()
    assert data["category"] == "Electricity & Streetlights"
    assert data["issueId"] is not None


def test_api_endpoint_05_get_issue_by_id():
    """5. GET /api/v1/issues/{issue_id}"""
    # Known ID
    res = client.get("/api/v1/issues/CIVIC-2026-001")
    assert res.status_code == 200
    assert res.json()["issueId"] == "CIVIC-2026-001"

    # Unknown ID -> 404
    res_404 = client.get("/api/v1/issues/CIVIC-NONEXISTENT-999")
    assert res_404.status_code == 404


def test_api_endpoint_06_patch_status():
    """6. PATCH /api/v1/issues/{issue_id}/status"""
    res = client.patch(
        "/api/v1/issues/CIVIC-2026-002/status",
        json={"status": "Action in Progress"}
    )
    assert res.status_code == 200
    assert res.json()["status"] == "ACTION IN PROGRESS"


def test_api_endpoint_07_verify_resolution():
    """7. POST /api/v1/issues/{issue_id}/verify"""
    res = client.post(
        "/api/v1/issues/CIVIC-2026-001/verify",
        json={
            "inspectorId": "INSP-QA-API-07",
            "resolutionImageUrl": "data/test_samples/repair_pothole_after_repaired.jpg",
            "notes": "Quality check."
        }
    )
    assert res.status_code == 200
    assert res.json()["status"] in ["RESOLVED", "VERIFICATION"]


def test_api_endpoint_08_get_verifications_history():
    """8. GET /api/v1/issues/{issue_id}/verifications"""
    res = client.get("/api/v1/issues/CIVIC-2026-001/verifications")
    assert res.status_code == 200
    history = res.json()
    assert isinstance(history, list)
    assert len(history) >= 1


def test_api_endpoint_09_hotspots():
    """9. GET /api/v1/hotspots"""
    res = client.get("/api/v1/hotspots")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_api_endpoint_10_recurring():
    """10. GET /api/v1/recurring"""
    res = client.get("/api/v1/recurring")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_api_endpoint_11_get_routing_config():
    """11. GET /api/v1/routing/config"""
    res = client.get("/api/v1/routing/config")
    assert res.status_code == 200
    assert "Roads & Footpaths" in res.json()


def test_api_endpoint_12_update_routing_config():
    """12. POST /api/v1/routing/config"""
    res = client.post(
        "/api/v1/routing/config",
        json={
            "category": "Roads & Footpaths",
            "department": "Rapid Pothole Action Squad",
            "code": "RPAS-01",
            "actions": {
                "CRITICAL": ["Instant cold mix patch within 4 hours", 4]
            }
        }
    )
    assert res.status_code == 200
    assert res.json()["status"] == "success"
    # Reset back to default
    department_dispatcher.reset_to_defaults()


def test_api_endpoint_13_gis_geojson():
    """13. GET /api/v1/gis/geojson"""
    res = client.get("/api/v1/gis/geojson")
    assert res.status_code == 200
    data = res.json()
    assert data["type"] == "FeatureCollection"
    assert "features" in data


def test_api_endpoint_14_gis_map():
    """14. GET /api/v1/gis/map"""
    res = client.get("/api/v1/gis/map")
    assert res.status_code == 200
    assert "text/html" in res.headers["content-type"]
    assert "leaflet" in res.text.lower()


def test_api_endpoint_15_evaluation_metrics():
    """15. GET /api/v1/evaluation/metrics"""
    res = client.get("/api/v1/evaluation/metrics")
    assert res.status_code == 200
    data = res.json()
    assert "classification" in data
    assert "resolution_verification" in data


def test_api_endpoint_16_demo_reset_protection():
    """16. POST /api/v1/demo/reset"""
    # When demo mode is True, succeeds:
    if settings.civilens_demo_mode:
        res = client.post("/api/v1/demo/reset")
        assert res.status_code == 200
        assert "reset" in res.json()["message"].lower()

    # When demo mode is disabled, must return HTTP 403
    with patch.object(settings, "civilens_demo_mode", False):
        res_blocked = client.post("/api/v1/demo/reset")
        assert res_blocked.status_code == 403
        assert "disabled" in res_blocked.json()["detail"].lower()


def test_api_endpoint_17_image_upload():
    """17. POST /api/v1/upload"""
    # Create small valid test image in memory
    img = Image.new("RGB", (100, 100), color=(100, 149, 237))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    res = client.post(
        "/api/v1/upload",
        files={"file": ("test_point.jpg", buf.read(), "image/jpeg")}
    )
    assert res.status_code == 200
    data = res.json()
    assert "uploadId" in data
    assert "previewUrl" in data


def test_api_endpoint_18_image_retrieval():
    """18. GET /api/v1/uploads/{upload_id}"""
    # 1. Valid uploaded ID
    img = Image.new("RGB", (64, 64), color=(34, 139, 34))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    up_res = client.post("/api/v1/upload", files={"file": ("green.png", buf.read(), "image/png")})
    upload_id = up_res.json()["uploadId"]

    get_res = client.get(f"/api/v1/uploads/{upload_id}")
    assert get_res.status_code == 200
    assert "image/png" in get_res.headers["content-type"]

    # 2. Unknown ID -> 404
    bad_id = "00000000-0000-0000-0000-000000000000"
    get_404 = client.get(f"/api/v1/uploads/{bad_id}")
    assert get_404.status_code == 404

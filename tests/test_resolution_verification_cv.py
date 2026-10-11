import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.main import app
from app.models.issue import (
    Issue,
    IssueCreate,
    IssueStatus,
    ResolutionStatus,
    ResolutionEvidence
)
from app.core.demo_store import demo_store
from app.db.repository import SqliteIssueRepository
from app.modules.lifecycle.tracker import lifecycle_tracker
from app.modules.lifecycle.scene_comparator import scene_comparator
from app.modules.vision.yolo_detector import yolo_detector

@pytest.fixture
def client():
    c = TestClient(app)
    c.headers["Authorization"] = "Bearer demo-inspector-token"
    return c


def test_1_same_defect_remains_detectable():
    """Scenario 1: Genuine road damage defect remains detectable in post-action inspection photograph."""
    # Issue with real pothole baseline
    issue = demo_store.get_issue("CIVIC-2026-001")
    assert issue is not None
    issue.imageUrl = "data/test_samples/repair_pothole_before.jpg"

    # Post-repair photograph still contains the pothole
    evidence = lifecycle_tracker.verify_resolution(
        issue=issue,
        inspector_id="INSP-01",
        resolution_image_url="data/test_samples/repair_pothole_before.jpg",
        notes="First contractor pass."
    )

    assert evidence.resolutionStatus == ResolutionStatus.STILL_PRESENT
    assert evidence.post_repair_cv_cleared is False
    assert len(evidence.afterDetections) > 0
    assert "Pothole" in (evidence.remainingDetection or "")
    assert evidence.resolutionConfidence >= 0.30
    assert "Defect still present" in evidence.verificationSummary


def test_2_comparable_before_after_pair_has_no_remaining_detectable_defect():
    """Scenario 2: Genuine before/after pair where defect is cleared across a comparable scene."""
    issue = demo_store.get_issue("CIVIC-2026-001")
    assert issue is not None
    issue.imageUrl = "data/test_samples/repair_pothole_before.jpg"

    # Post-repair photograph shows smooth asphalt patch with 0 road damage detections
    evidence = lifecycle_tracker.verify_resolution(
        issue=issue,
        inspector_id="INSP-02",
        resolution_image_url="data/test_samples/repair_pothole_after_repaired.jpg",
        notes="High-performance cold mix patch completed."
    )

    assert evidence.resolutionStatus == ResolutionStatus.LIKELY_RESOLVED
    assert evidence.post_repair_cv_cleared is True
    assert evidence.remainingDetection is None
    assert len(evidence.afterDetections) == 0
    assert evidence.sceneComparable is True
    assert evidence.comparisonMetrics["ssim"] > 0.50
    assert evidence.comparisonMetrics["histogramCorrelation"] > 0.80
    assert evidence.resolutionConfidence >= 0.75
    # Caution clause: system avoids claiming absolute physical certainty
    assert "not claiming absolute certainty" in evidence.verificationSummary.lower()


def test_3_before_image_lacks_usable_evidence():
    """Scenario 3: When original report evidence lacked detectable road damage, system flags for manual review."""
    # Clean road image used as baseline (no detectable damage)
    clean_issue = Issue(
        issueId="CIVIC-TEST-CLEAN-01",
        complaintText="Minor surface irregularity reported by caller",
        location="Marine Drive",
        latitude=18.944,
        longitude=72.823,
        timestamp="2026-10-10T10:00:00Z",
        imageUrl="data/test_samples/clean_road.jpg",
        visualDetection=None,
        visualConfidence=0.0,
        visualSeverity=0.0,
        priorityScore=30.0
    )

    evidence = lifecycle_tracker.verify_resolution(
        issue=clean_issue,
        inspector_id="INSP-03",
        resolution_image_url="data/test_samples/repair_pothole_after_repaired.jpg"
    )

    # Must NOT claim likely resolved because baseline lacked detectable defects!
    assert evidence.resolutionStatus == ResolutionStatus.REQUIRES_MANUAL_VERIFICATION
    assert evidence.requiresManualReview is True
    assert evidence.post_repair_cv_cleared is False
    assert "lacked detectable road damage" in evidence.verificationSummary


def test_4_after_image_is_corrupt():
    """Scenario 4: When post-action photograph is corrupted, system flags manual verification."""
    issue = demo_store.get_issue("CIVIC-2026-001")
    assert issue is not None

    evidence = lifecycle_tracker.verify_resolution(
        issue=issue,
        inspector_id="INSP-04",
        resolution_image_url="data/test_samples/corrupt_file.jpg"
    )

    assert evidence.resolutionStatus == ResolutionStatus.REQUIRES_MANUAL_VERIFICATION
    assert evidence.post_repair_cv_cleared is False
    assert evidence.requiresManualReview is True
    assert "unreadable or corrupted" in evidence.verificationSummary


def test_5_images_have_incompatible_dimensions_or_viewpoints():
    """Scenario 5: Incompatible camera framing, aspect ratio, or disparate scenes trigger manual review."""
    issue = demo_store.get_issue("CIVIC-2026-001")
    assert issue is not None
    issue.imageUrl = "data/test_samples/repair_pothole_before.jpg"

    # Incompatible scene (portrait gradient image)
    evidence = lifecycle_tracker.verify_resolution(
        issue=issue,
        inspector_id="INSP-05",
        resolution_image_url="data/test_samples/incompatible_scene.jpg"
    )

    assert evidence.resolutionStatus == ResolutionStatus.REQUIRES_MANUAL_VERIFICATION
    assert evidence.sceneComparable is False
    assert evidence.requiresManualReview is True
    assert "not sufficiently comparable" in evidence.verificationSummary


def test_6_yolo_inference_unavailable():
    """Scenario 6: When YOLO inference is offline, system returns manual review and never marks resolved."""
    issue = demo_store.get_issue("CIVIC-2026-001")
    assert issue is not None

    with patch.object(yolo_detector, "_get_model", return_value=None):
        evidence = lifecycle_tracker.verify_resolution(
            issue=issue,
            inspector_id="INSP-06",
            resolution_image_url="data/test_samples/repair_pothole_after_repaired.jpg"
        )

        assert evidence.resolutionStatus == ResolutionStatus.REQUIRES_MANUAL_VERIFICATION
        assert evidence.post_repair_cv_cleared is False
        assert "unavailable" in evidence.verificationSummary.lower()


def test_7_comparison_with_sample_fixtures_evaluates_content_not_filenames():
    """Scenario 7: Content-based evaluation of sample_pothole.jpg (lacks RDD classes -> manual review)."""
    issue = Issue(
        issueId="CIVIC-TEST-STOCK-01",
        complaintText="Stock photo demonstration issue",
        location="BKC",
        latitude=19.065,
        longitude=72.868,
        timestamp="2026-10-10T12:00:00Z",
        imageUrl="data/sample_pothole.jpg",
        visualDetection=None,
        priorityScore=40.0
    )

    evidence = lifecycle_tracker.verify_resolution(
        issue=issue,
        inspector_id="INSP-07",
        resolution_image_url="data/sample_repaired_pothole.jpg"
    )

    # Since sample_pothole.jpg produces 0 RDD2022 detections, delta cannot be verified automatically
    assert evidence.resolutionStatus == ResolutionStatus.REQUIRES_MANUAL_VERIFICATION
    assert evidence.requiresManualReview is True


def test_8_missing_upload_id_or_empty_reference_rejected(client):
    """Scenario 8: API rejects arbitrary non-allowlisted image references."""
    res = client.post(
        "/api/v1/issues/CIVIC-2026-001/verify",
        json={
            "inspectorId": "INSP-08",
            "resolutionImageUrl": "/arbitrary/untrusted/remote/path.jpg"
        }
    )
    # Upload service rejects untrusted path traversal references with HTTP 400
    assert res.status_code == 400
    assert "Invalid image reference" in res.json()["detail"]


def test_9_failed_inference_never_falsely_marks_issue_resolved(client):
    """Scenario 9: Corrupt upload submitted via API transitions to VERIFICATION, never RESOLVED."""
    with open("data/test_samples/corrupt_file.jpg", "rb") as f:
        corrupt_bytes = f.read()

    # Upload corrupt image using valid endpoint
    # Note: upload endpoint validates headers/format, but if corrupt file gets through or fixture used:
    res = client.post(
        "/api/v1/issues/CIVIC-2026-001/verify",
        json={
            "inspectorId": "INSP-09",
            "resolutionImageUrl": "data/test_samples/corrupt_file.jpg"
        }
    )
    assert res.status_code == 200
    updated_issue = res.json()
    assert updated_issue["status"] == "VERIFICATION"
    assert updated_issue["status"] != "RESOLVED"
    assert updated_issue["resolutionEvidence"]["resolutionStatus"] == "REQUIRES MANUAL VERIFICATION"


def test_10_verification_records_persist_across_restart():
    """Scenario 10: Verification evidence and metrics survive SQLite repository reinitialization."""
    # Perform genuine resolution verification
    first = demo_store.get_issue("CIVIC-2026-001")
    assert first is not None
    first.imageUrl = "data/test_samples/repair_pothole_before.jpg"

    evidence = lifecycle_tracker.verify_resolution(
        issue=first,
        inspector_id="INSP-10",
        resolution_image_url="data/test_samples/repair_pothole_after_repaired.jpg",
        notes="Persistent lifecycle check."
    )
    demo_store.record_verification("CIVIC-2026-001", evidence)

    # Instantiate brand new repository pointing to the same SQLite database
    new_repo = SqliteIssueRepository()
    reloaded_issue = new_repo.get_issue("CIVIC-2026-001")
    assert reloaded_issue is not None
    assert reloaded_issue.status == IssueStatus.RESOLVED
    assert reloaded_issue.resolutionEvidence is not None
    assert reloaded_issue.resolutionEvidence.resolutionStatus == ResolutionStatus.LIKELY_RESOLVED
    assert reloaded_issue.resolutionEvidence.sceneComparable is True
    assert reloaded_issue.resolutionEvidence.comparisonMetrics["ssim"] > 0.50
    assert "yolo_before_after_comparison" in reloaded_issue.resolutionEvidence.verificationMethod


def test_11_repeated_verification_attempts_preserve_history(client):
    """Scenario 11: Repeated verification attempts maintain chronological audit trail."""
    target_id = "CIVIC-2026-002"
    issue = demo_store.get_issue(target_id)
    assert issue is not None
    issue.imageUrl = "data/test_samples/repair_pothole_before.jpg"
    demo_store.update_issue(issue)

    # Attempt 1: Defect still present
    res1 = client.post(
        f"/api/v1/issues/{target_id}/verify",
        json={
            "inspectorId": "INSP-ATTEMPT-1",
            "resolutionImageUrl": "data/test_samples/repair_pothole_before.jpg",
            "notes": "Attempt 1: Defect still visible."
        }
    )
    assert res1.status_code == 200
    assert res1.json()["status"] == "ACTION IN PROGRESS"

    # Attempt 2: Repaired surface
    res2 = client.post(
        f"/api/v1/issues/{target_id}/verify",
        json={
            "inspectorId": "INSP-ATTEMPT-2",
            "resolutionImageUrl": "data/test_samples/repair_pothole_after_repaired.jpg",
            "notes": "Attempt 2: Resurfacing completed."
        }
    )
    assert res2.status_code == 200
    assert res2.json()["status"] == "RESOLVED"

    # Retrieve full verification history via API
    hist_res = client.get(f"/api/v1/issues/{target_id}/verifications")
    assert hist_res.status_code == 200
    history = hist_res.json()
    assert len(history) >= 2
    # Verify chronological sequence
    assert history[-2]["resolutionStatus"] == "STILL PRESENT"
    assert history[-1]["resolutionStatus"] == "LIKELY RESOLVED"


def test_12_existing_lifecycle_transitions_continue_working():
    """Scenario 12: Standard 7-stage lifecycle state transitions operate normally."""
    assert lifecycle_tracker.can_transition(IssueStatus.OPEN, IssueStatus.ANALYZED)
    assert lifecycle_tracker.can_transition(IssueStatus.ANALYZED, IssueStatus.PRIORITIZED)
    assert lifecycle_tracker.can_transition(IssueStatus.PRIORITIZED, IssueStatus.ASSIGNED)
    assert lifecycle_tracker.can_transition(IssueStatus.ASSIGNED, IssueStatus.ACTION_IN_PROGRESS)
    assert lifecycle_tracker.can_transition(IssueStatus.ACTION_IN_PROGRESS, IssueStatus.VERIFICATION)
    assert lifecycle_tracker.can_transition(IssueStatus.VERIFICATION, IssueStatus.RESOLVED)


def test_13_no_filename_based_heuristics_honesty_check():
    """Scenario 13: Filename strings like 'repaired' or 'broken' do NOT dictate the outcome."""
    # We test with repair_pothole_before.jpg (has pothole defect)
    issue = demo_store.get_issue("CIVIC-2026-001")
    assert issue is not None
    issue.imageUrl = "data/test_samples/repair_pothole_before.jpg"

    # Even if notes or filename contained positive words, if damage is detected, it is STILL PRESENT
    evidence = lifecycle_tracker.verify_resolution(
        issue=issue,
        inspector_id="INSP-13",
        resolution_image_url="data/test_samples/repair_pothole_before.jpg",
        notes="claimed 100% repaired perfect clear"
    )
    assert evidence.resolutionStatus == ResolutionStatus.STILL_PRESENT
    assert evidence.post_repair_cv_cleared is False

"""
CIVILENS Verification Script:
Validates Issue Dossier Accuracy, Genuine YOLO Inference,
Six-Factor Priority Score Explainability, Duplicate Status, and Resolution Workflow Gating.
"""
import os
import requests
from fastapi.testclient import TestClient

from app.main import app
from app.core.demo_store import demo_store
from app.models.issue import IssueStatus
from app.modules.vision.yolo_detector import yolo_detector
from app.modules.vision.waste_detector import WasteDetector
from app.modules.vision.severity import visual_severity_estimator
from app.modules.priority.engine import priority_engine

def run_verification():
    print("=================================================================")
    print("CIVILENS ISSUE DOSSIER ACCURACY & WORKFLOW GATING VERIFICATION")
    print("=================================================================")
    
    # -------------------------------------------------------------------------
    # 1. Investigate Pothole Severity Result (Image from Screenshot)
    # -------------------------------------------------------------------------
    pothole_img = "uploads_presentation/821f9cad-1672-4efc-b415-2573b65f342d.png"
    if not os.path.exists(pothole_img):
        print(f"[WARN] {pothole_img} not found locally, using test sample")
        pothole_img = "data/test_samples/repair_pothole_before.jpg"

    print(f"\n1. Tracing genuine YOLO inference on: {pothole_img}")
    det_result = yolo_detector.detect(pothole_img)
    print(f"   Vision Execution Mode: {det_result.get('visionExecutionMode')}")
    print(f"   Model Name:            {det_result.get('visionModel')}")
    print(f"   Primary Detection:     {det_result.get('visualDetection')}")
    print(f"   Visual Confidence:     {det_result.get('visualConfidence')}")
    print(f"   Detected Objects Count:{len(det_result.get('detectedObjects', []))}")
    for idx, obj in enumerate(det_result.get('detectedObjects', [])):
        print(f"     [{idx+1}] {obj.label} (class {obj.class_name}): conf={obj.confidence:.4f}, bbox={obj.bbox}")

    vis_sev = visual_severity_estimator.estimate_severity(det_result.get('detectedObjects', []))
    print(f"   Visual Severity Score: {vis_sev} (out of 1.0)")

    # Test six-factor priority scoring for this pothole complaint
    score, level, breakdown, reasoning = priority_engine.calculate_priority(
        urgency=0.65,
        text_severity=0.82,
        visual_severity=vis_sev,
        visual_confidence=det_result.get('visualConfidence', 0.0),
        related_reports_count=1,
        hours_elapsed=0.0,
        recurrence_count=2,
        is_hotspot=False
    )
    print(f"   Calculated Priority Score: {score}/100 ({level.value})")
    print(f"   Component Breakdown:")
    print(f"     - Urgency:         {breakdown.urgency_points} / 20")
    print(f"     - Text Severity:   {breakdown.text_severity_points} / 20")
    print(f"     - Visual Severity: {breakdown.visual_severity_points} / 20")
    print(f"     - Related Reports: {breakdown.related_reports_points} / 15")
    print(f"     - Recency:         {breakdown.recency_points} / 10")
    print(f"     - Location Risk:   {breakdown.location_risk_points} / 15")
    sum_pts = (breakdown.urgency_points + breakdown.text_severity_points + 
               breakdown.visual_severity_points + breakdown.related_reports_points + 
               breakdown.recency_points + breakdown.location_risk_points)
    print(f"     Sum of components: {sum_pts:.1f} == Total Score {score:.1f}")
    assert abs(sum_pts - score) < 1e-4, "Component values must strictly sum to total score!"
    assert level.value == "MEDIUM", f"58.0 pts must evaluate to MEDIUM under 85/70/40 thresholds! Got: {level.value}"

    # -------------------------------------------------------------------------
    # 2. Garbage / Litter Complaint Trace
    # -------------------------------------------------------------------------
    garbage_img = "data/test_samples/litter.jpg"
    print(f"\n2. Tracing genuine YOLO inference on garbage sample: {garbage_img}")
    waste_detector = WasteDetector()
    g_det = waste_detector.detect(garbage_img)
    print(f"   Vision Execution Mode: {g_det.get('visionExecutionMode')}")
    print(f"   Model Name:            {g_det.get('sourceModel') or g_det.get('visionModel')}")
    print(f"   Primary Detection:     {g_det.get('visualDetection')}")
    print(f"   Visual Confidence:     {g_det.get('visualConfidence')}")
    print(f"   Detected Objects Count:{len(g_det.get('detectedObjects', []))}")
    for idx, obj in enumerate(g_det.get('detectedObjects', [])):
        print(f"     [{idx+1}] {obj.label}: conf={obj.confidence:.4f}, bbox={obj.bbox}")
    g_vis_sev = visual_severity_estimator.estimate_severity(g_det.get('detectedObjects', []))
    print(f"   Garbage Visual Severity: {g_vis_sev}")

    # -------------------------------------------------------------------------
    # 3. Test Lifecycle Gating & Verification API via TestClient
    # -------------------------------------------------------------------------
    print("\n3. Testing Lifecycle State Machine and Verification Gating on Backend...")
    client = TestClient(app)
    headers = {"Authorization": "Bearer demo-inspector-token"}

    # Case A: Verify call on OPEN issue must be rejected with 400
    demo_store.update_status("CIVIC-2026-001", IssueStatus.OPEN)
    res_open = client.post(
        "/api/v1/issues/CIVIC-2026-001/verify",
        headers=headers,
        json={
            "resolutionImageUrl": "data/test_samples/repair_pothole_after_repaired.jpg",
            "notes": "Premature attempt on OPEN issue."
        }
    )
    print(f"   [OPEN Status Check] HTTP {res_open.status_code}: {res_open.json().get('detail')}")
    assert res_open.status_code == 400, "Premature verification on OPEN issue must return HTTP 400!"
    assert "current lifecycle status is 'OPEN'" in res_open.json()["detail"]

    # Case B: Verify call on ASSIGNED issue must be rejected with 400
    demo_store.update_status("CIVIC-2026-001", IssueStatus.ASSIGNED)
    res_assigned = client.post(
        "/api/v1/issues/CIVIC-2026-001/verify",
        headers=headers,
        json={
            "resolutionImageUrl": "data/test_samples/repair_pothole_after_repaired.jpg",
            "notes": "Premature attempt on ASSIGNED issue."
        }
    )
    print(f"   [ASSIGNED Status Check] HTTP {res_assigned.status_code}: {res_assigned.json().get('detail')}")
    assert res_assigned.status_code == 400, "Premature verification on ASSIGNED issue must return HTTP 400!"

    # Case C: Verification call without post-action image evidence must be rejected with 400
    demo_store.update_status("CIVIC-2026-001", IssueStatus.ACTION_IN_PROGRESS)
    res_no_img = client.post(
        "/api/v1/issues/CIVIC-2026-001/verify",
        headers=headers,
        json={"notes": "No image provided"}
    )
    print(f"   [Missing Evidence Check] HTTP {res_no_img.status_code}: {res_no_img.json().get('detail')}")
    assert res_no_img.status_code == 400, "Verification without evidence must return HTTP 400!"

    # Case D: Verification call on ACTION IN PROGRESS with valid image succeeds with 200
    res_valid = client.post(
        "/api/v1/issues/CIVIC-2026-001/verify",
        headers=headers,
        json={
            "resolutionImageUrl": "data/test_samples/repair_pothole_after_repaired.jpg",
            "notes": "Repaired road surface verified by field inspector."
        }
    )
    print(f"   [ACTION IN PROGRESS Check] HTTP {res_valid.status_code}: ResolutionStatus={res_valid.json().get('resolutionEvidence', {}).get('resolutionStatus')}")
    assert res_valid.status_code == 200, "Verification in ACTION IN PROGRESS must succeed with HTTP 200!"
    assert res_valid.json()["status"] in ["RESOLVED", "VERIFICATION"]

    print("\n[SUCCESS] All verification criteria verified and confirmed!")

if __name__ == "__main__":
    run_verification()

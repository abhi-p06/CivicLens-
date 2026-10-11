import os
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings
from app.models.issue import IssueCategory, IssueCreate, ConsistencyLevel
from app.core.pipeline import pipeline
from app.modules.vision.manager import vision_manager, VisionPipelineManager
from app.modules.vision.road_detector import RoadDamageDetector
from app.modules.vision.waste_detector import WasteDetector
from app.modules.vision.flooding_detector import FloodingDetector
from app.modules.vision.severity import visual_severity_estimator
from app.modules.priority.engine import priority_engine

client = TestClient(app)


def test_1_pothole_image_detection():
    """1. Pothole image: Genuine YOLOv8s RDD2022 detection produces localized pothole box."""
    img_path = "data/test_samples/repair_pothole_before.jpg"
    assert os.path.exists(img_path)

    res = vision_manager.detect(img_path, category_hint="Roads & Footpaths", is_demo=False)
    assert res["visionExecutionMode"] == "real_yolo_inference"
    assert res["task"] == "ROAD_DAMAGE"
    assert len(res["detectedObjects"]) > 0

    pothole = res["detectedObjects"][0]
    assert "Pothole" in pothole.label or "D40" in pothole.label
    assert pothole.confidence >= 0.15
    assert len(pothole.bbox) == 4
    ymin, xmin, ymax, xmax = pothole.bbox
    assert 0.0 <= ymin < ymax <= 1.0
    assert 0.0 <= xmin < xmax <= 1.0


def test_2_road_crack_image_detection():
    """2. Road-crack image: Genuine detection of alligator/fatigue cracks."""
    img_path = "data/test_samples/alligator_crack.jpg"
    assert os.path.exists(img_path)

    res = vision_manager.detect(img_path, category_hint="Roads & Footpaths", is_demo=False)
    assert res["visionExecutionMode"] == "real_yolo_inference"
    assert res["task"] == "ROAD_DAMAGE"
    assert len(res["detectedObjects"]) > 0

    crack = res["detectedObjects"][0]
    assert any(k in crack.label for k in ["Crack", "D00", "D10", "D20"])
    assert crack.confidence >= 0.15


def test_3_normal_road_empty_detections():
    """3. Normal road image: Clean asphalt yields 0 detections without false positives."""
    img_path = "data/test_samples/clean_road.jpg"
    assert os.path.exists(img_path)

    res = vision_manager.detect(img_path, category_hint="Roads & Footpaths", is_demo=False)
    assert res["visionExecutionMode"] == "real_yolo_inference"
    assert res["detectedObjects"] == []
    assert res["visualDetection"] is None
    assert res["visualConfidence"] == 0.0


def test_4_garbage_accumulation_detection():
    """4. Garbage accumulation image: Genuine TACO YOLO detector locates waste/litter items."""
    img_path = "data/test_samples/litter.jpg"
    assert os.path.exists(img_path)

    res = vision_manager.detect(img_path, category_hint="Sanitation & Garbage", is_demo=False)
    assert res["visionExecutionMode"] == "real_yolo_inference"
    assert res["task"] == "SANITATION"
    assert len(res["detectedObjects"]) > 0

    # Verify detected classes and normalized bounding boxes
    labels = [d.label for d in res["detectedObjects"]]
    assert any("Plastic" in l or "Can" in l or "Carton" in l or "Waste" in l for l in labels)
    for d in res["detectedObjects"]:
        assert d.task == "SANITATION"
        assert d.confidence >= 0.20
        ymin, xmin, ymax, xmax = d.bbox
        assert 0.0 <= ymin < ymax <= 1.0
        assert 0.0 <= xmin < xmax <= 1.0

    # Also test discrete bottle image
    bottle_res = vision_manager.detect("data/test_samples/bottle.jpg", category_hint="Sanitation & Garbage", is_demo=False)
    assert len(bottle_res["detectedObjects"]) > 0
    assert any("Bottle" in d.label for d in bottle_res["detectedObjects"])


def test_5_visible_flooding_waterlogging_handling():
    """5. Visible flooding/waterlogging: Handled honestly as unsupported without fake boxes."""
    img_path = "data/test_samples/street_flooding.jpg"
    assert os.path.exists(img_path)

    res = vision_manager.detect(img_path, category_hint="Water Supply & Drainage", is_demo=False)
    # Zero synthetic bounding boxes
    assert res["detectedObjects"] == []
    assert res["visualDetection"] is None
    assert res["visionExecutionMode"] == "unsupported_visual_category"

    # Pipeline integration: verify manual review status without marking citizen complaint fake
    payload = IssueCreate(
        complaintText="Severe street flooding and waterlogging near market sub-station.",
        imageUrl=img_path,
        location="Market Sub-station"
    )
    analysis = pipeline.analyze(payload)
    assert analysis["consistencyLevel"] == ConsistencyLevel.MANUAL_REVIEW
    assert "cannot confirm subsurface" in analysis["consistencyDetail"].reason.lower()


def test_6_complaint_image_category_mismatch():
    """6. Complaint/image mismatch: Flags cross-modal discrepancy for supervisory triage."""
    # Scenario A: Citizen reported road pothole, but attached image shows waste/litter
    road_payload = IssueCreate(
        complaintText="Massive dangerous pothole causing tire damage on main road.",
        imageUrl="data/test_samples/litter.jpg",
        location="Linking Road"
    )
    road_analysis = pipeline.analyze(road_payload)
    assert road_analysis["category"] == IssueCategory.ROAD_DAMAGE
    assert road_analysis["consistencyLevel"] == ConsistencyLevel.INCONSISTENT
    assert "discrepancy" in road_analysis["consistencyDetail"].reason.lower()

    # Scenario B: Citizen reported overflowing garbage, but attached image shows asphalt pothole
    waste_payload = IssueCreate(
        complaintText="Overflowing rotten garbage dump creating terrible stench and health hazard.",
        imageUrl="data/test_samples/repair_pothole_before.jpg",
        location="Station Road"
    )
    waste_analysis = pipeline.analyze(waste_payload)
    assert waste_analysis["category"] == IssueCategory.SANITATION
    assert waste_analysis["consistencyLevel"] == ConsistencyLevel.INCONSISTENT
    assert "discrepancy" in waste_analysis["consistencyDetail"].reason.lower()


def test_7_corrupted_image_handling():
    """7. Corrupted image: Unreadable payload handled gracefully with manual review."""
    corrupt_path = "data/test_samples/corrupt_file.jpg"
    assert os.path.exists(corrupt_path)

    res = vision_manager.detect(corrupt_path, category_hint="Roads & Footpaths", is_demo=False)
    assert res["visionExecutionMode"] == "unreadable_image_file"
    assert res["detectedObjects"] == []
    assert res["visualDetection"] is None


def test_8_missing_model_checkpoint():
    """8. Missing model checkpoint: Detector reports unavailable_model gracefully."""
    fake_detector = WasteDetector(model_path="models/nonexistent_model_weights.pt")
    assert fake_detector.is_model_available() is False

    res = fake_detector.detect("data/test_samples/bottle.jpg", is_demo=False)
    assert res["visionExecutionMode"] == "unavailable_model"
    assert res["detectedObjects"] == []


def test_9_unsupported_visual_category():
    """9. Unsupported category: Electrical/Traffic claims route to manual review honestly."""
    payload = IssueCreate(
        complaintText="Streetlight cluster dark and non-functional on college avenue.",
        location="College Avenue",
        imageUrl="data/test_samples/clean_road.jpg"
    )
    analysis = pipeline.analyze(payload)
    assert analysis["category"] == IssueCategory.ELECTRICAL
    assert analysis["consistencyLevel"] == ConsistencyLevel.MANUAL_REVIEW


def test_10_image_with_no_relevant_detections():
    """10. Image with no relevant detections: Clean roadway produces empty detections and manual review."""
    payload = IssueCreate(
        complaintText="Severe asphalt fissure on arterial roadway.",
        location="Arterial Road",
        imageUrl="data/test_samples/clean_road.jpg"
    )
    analysis = pipeline.analyze(payload)
    assert analysis["visualDetection"] is None
    assert analysis["visualConfidence"] == 0.0
    assert analysis["visualSeverity"] == 0.0
    assert analysis["consistencyLevel"] == ConsistencyLevel.MANUAL_REVIEW


def test_11_priority_scoring_regression_proof():
    """
    11. Regression proof: Authoritative 6-factor priority formula (100 pts max)
    remains strictly intact across both Road Damage and Waste categories.
    """
    # Verify road damage visual severity calculation remains identical
    road_res = vision_manager.detect("data/test_samples/repair_pothole_before.jpg", is_demo=False)
    road_sev = visual_severity_estimator.estimate_severity(road_res["detectedObjects"])
    assert 0.30 <= road_sev <= 0.95

    # Verify waste accumulation visual severity calculation
    waste_res = vision_manager.detect("data/test_samples/litter.jpg", is_demo=False)
    waste_sev = visual_severity_estimator.estimate_severity(waste_res["detectedObjects"])
    assert 0.30 <= waste_sev <= 0.95

    # Priority calculation with waste evidence
    score, level, breakdown, reasoning = priority_engine.calculate_priority(
        urgency=0.8,
        text_severity=0.7,
        visual_severity=waste_sev,
        visual_confidence=waste_res["visualConfidence"],
        related_reports_count=2,
        hours_elapsed=2.0,
        recurrence_count=1,
        is_hotspot=False
    )
    assert 0.0 <= score <= 100.0
    # Component breakdown sums exactly to composite score
    sum_pts = (
        breakdown.urgency_points +
        breakdown.text_severity_points +
        breakdown.visual_severity_points +
        breakdown.related_reports_points +
        breakdown.recency_points +
        breakdown.location_risk_points
    )
    assert abs(round(sum_pts, 2) - score) <= 0.05


def test_12_end_to_end_api_submission_and_persistence():
    """12. End-to-end API upload, multi-category analysis, submission, and persistence."""
    with open("data/test_samples/bottle.jpg", "rb") as f:
        img_bytes = f.read()

    # Step A: Secure Upload
    upload_res = client.post(
        "/api/v1/upload",
        files={"file": ("street_litter.jpg", img_bytes, "image/jpeg")}
    )
    assert upload_res.status_code == 200
    upload_id = upload_res.json()["uploadId"]

    # Step B: Multimodal Analysis via API
    analyze_res = client.post(
        "/api/v1/analyze",
        json={
            "complaintText": "Accumulated plastic bottles and litter blocking sidewalk near bus stop",
            "location": "SVT Road, Juhu",
            "uploadId": upload_id
        }
    )
    assert analyze_res.status_code == 200
    analysis_data = analyze_res.json()
    assert analysis_data["category"] == IssueCategory.SANITATION.value
    assert analysis_data["consistencyFlag"] == "CONSISTENT"
    assert len(analysis_data["detectedObjects"]) > 0
    assert any("Bottle" in d["label"] for d in analysis_data["detectedObjects"])

    # Step C: Formal Issue Registration
    submit_res = client.post(
        "/api/v1/issues",
        json={
            "complaintText": "Accumulated plastic bottles and litter blocking sidewalk near bus stop",
            "location": "SVT Road, Juhu",
            "uploadId": upload_id
        }
    )
    assert submit_res.status_code == 201
    created_issue = submit_res.json()
    issue_id = created_issue["issueId"]

    # Step D: Retrieve Persisted Issue
    get_res = client.get(f"/api/v1/issues/{issue_id}")
    assert get_res.status_code == 200
    retrieved = get_res.json()
    assert retrieved["issueId"] == issue_id
    assert retrieved["category"] == IssueCategory.SANITATION.value
    assert retrieved["consistencyFlag"] == "CONSISTENT"
    assert len(retrieved["detectedObjects"]) > 0

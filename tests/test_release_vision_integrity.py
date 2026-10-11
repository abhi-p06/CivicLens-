import os
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings
from app.models.issue import IssueCategory, IssueCreate, ConsistencyLevel, PriorityLevel
from app.core.pipeline import pipeline
from app.modules.vision.manager import vision_manager, VisionPipelineManager
from app.modules.vision.road_detector import RoadDamageDetector
from app.modules.vision.waste_detector import WasteDetector
from app.modules.vision.flooding_detector import FloodingDetector
from app.modules.priority.engine import priority_engine

client = TestClient(app)


def test_edge_case_1_pothole_image_under_roads_category():
    """Edge Case 1: A pothole image submitted under a roads category."""
    img_path = "data/test_samples/repair_pothole_before.jpg"
    assert os.path.exists(img_path)

    payload = IssueCreate(
        complaintText="Critical crater-like pothole breaking wheel rims and causing traffic jams on Linking Road.",
        imageUrl=img_path,
        location="Linking Road, Bandra West"
    )

    analysis = pipeline.analyze(payload)
    assert analysis["category"] == IssueCategory.ROAD_DAMAGE
    assert analysis["visionMode"] == "real_yolo_inference"
    assert analysis["visionTask"] == "ROAD_DAMAGE"
    assert analysis["visualDetection"] is not None
    assert analysis["visualConfidence"] > 0.0
    assert len(analysis["detectedObjects"]) > 0
    assert any("Pothole" in getattr(d, "label", "") or "D40" in getattr(d, "label", "") for d in analysis["detectedObjects"])

    # Visual severity points modulated by confidence
    assert analysis["visualSeverity"] > 0.0
    assert analysis["consistencyLevel"] == ConsistencyLevel.CONSISTENT
    assert analysis["evidenceConsistency"] >= 0.90
    assert analysis["priorityScore"] > 0.0


def test_edge_case_2_litter_image_under_sanitation_category():
    """Edge Case 2: A litter image submitted under sanitation."""
    img_path = "data/test_samples/litter.jpg"
    assert os.path.exists(img_path)

    payload = IssueCreate(
        complaintText="Severe municipal garbage dump with discarded plastic bags, cups, and food cartons decaying on footpath.",
        imageUrl=img_path,
        location="Hill Road, Bandra"
    )

    analysis = pipeline.analyze(payload)
    assert analysis["category"] == IssueCategory.SANITATION
    assert analysis["visionMode"] == "real_yolo_inference"
    assert analysis["visionTask"] == "SANITATION"
    assert analysis["visualDetection"] is not None
    assert analysis["visualConfidence"] > 0.0
    assert len(analysis["detectedObjects"]) > 0
    assert any(any(k in getattr(d, "label", "") for k in ["Plastic", "Can", "Carton", "Cup", "Waste"]) for d in analysis["detectedObjects"])

    assert analysis["visualSeverity"] > 0.0
    assert analysis["consistencyLevel"] == ConsistencyLevel.CONSISTENT
    assert analysis["evidenceConsistency"] >= 0.90


def test_edge_case_3_flooding_waterlogging_unsupported_manual_review():
    """
    Edge Case 3: A flooding/waterlogging report with an image.
    Must remain explicitly unsupported without fabricating synthetic bounding boxes.
    """
    img_path = "data/test_samples/street_flooding.jpg"
    assert os.path.exists(img_path)

    payload = IssueCreate(
        complaintText="Massive stormwater drain rupture causing knee-deep waterlogging across low-lying transit corridor.",
        imageUrl=img_path,
        location="Hindmata Flyover Underpass"
    )

    analysis = pipeline.analyze(payload)
    assert analysis["category"] == IssueCategory.WATER_SUPPLY

    # Must produce ZERO fabricated boxes
    assert analysis["detectedObjects"] == []
    assert analysis["visualDetection"] is None
    assert analysis["visualConfidence"] == 0.0
    assert analysis["visualSeverity"] == 0.0
    assert analysis["visionMode"] == "unsupported_visual_category"

    # Must route to manual supervisory review without marking complaint fake
    assert analysis["consistencyLevel"] == ConsistencyLevel.MANUAL_REVIEW
    assert "inspection pending" in analysis["consistencyDetail"].reason.lower()

    # Text urgency and text severity must still function and produce legitimate priority points
    assert analysis["urgency"] >= 0.30
    assert analysis["textSeverity"] >= 0.50
    assert analysis["priorityScore"] >= 35.0  # Medium or higher based on urgent text alone


def test_edge_case_4_zero_detections_image():
    """
    Edge Case 4: An image that produces zero detections (e.g. clean road asphalt).
    Zero detections must not automatically prove complaint is fake or area is free of defects.
    """
    img_path = "data/test_samples/clean_road.jpg"
    assert os.path.exists(img_path)

    payload = IssueCreate(
        complaintText="Reported structural asphalt fissure near intersection curb.",
        imageUrl=img_path,
        location="Nehru Road, Kurla"
    )

    analysis = pipeline.analyze(payload)
    assert analysis["detectedObjects"] == []
    assert analysis["visualDetection"] is None
    assert analysis["visualConfidence"] == 0.0
    assert analysis["visualSeverity"] == 0.0

    # Never labeled 'fake'; routed for standard field verification
    assert analysis["consistencyLevel"] == ConsistencyLevel.MANUAL_REVIEW
    assert "field verification" in analysis["consistencyDetail"].reason.lower()

    # Priority score calculated purely from non-visual factors (0 visual severity points)
    score, level, breakdown, reasoning = priority_engine.calculate_priority(
        urgency=analysis["urgency"],
        text_severity=analysis["textSeverity"],
        visual_severity=analysis["visualSeverity"],
        visual_confidence=analysis["visualConfidence"],
        related_reports_count=0,
        hours_elapsed=1.0,
        recurrence_count=1,
        is_hotspot=False
    )
    assert breakdown.visual_severity_points == 0.0
    assert score > 0.0


def test_edge_case_5_missing_corrupt_unsupported_image_evidence():
    """
    Edge Case 5: Missing, corrupted or unsupported image evidence.
    Must not generate artificial visual severity points; text factors must continue operating.
    """
    # 5a: Missing image evidence
    payload_no_img = IssueCreate(
        complaintText="Dangerous open manhole posing grave pedestrian risk at night.",
        imageUrl=None,
        location="Station Plaza"
    )
    analysis_no_img = pipeline.analyze(payload_no_img)
    assert analysis_no_img["visualSeverity"] == 0.0
    assert analysis_no_img["visualDetection"] is None
    assert analysis_no_img["consistencyLevel"] == ConsistencyLevel.MANUAL_REVIEW
    assert analysis_no_img["urgency"] > 0.70  # Text urgency active
    assert analysis_no_img["priorityScore"] > 35.0

    # 5b: Corrupted image file
    corrupt_path = "data/test_samples/corrupt_file.jpg"
    assert os.path.exists(corrupt_path)
    res_corrupt = vision_manager.detect(corrupt_path, category_hint="Roads & Footpaths")
    assert res_corrupt["visionExecutionMode"] == "unreadable_image_file"
    assert res_corrupt["detectedObjects"] == []
    assert res_corrupt["visualDetection"] is None

    # 5c: Unsupported visual category (e.g. Electrical / Streetlights)
    payload_elec = IssueCreate(
        complaintText="Streetlight pole feeder box sparking intermittently.",
        imageUrl="data/test_samples/clean_road.jpg",
        location="MG Road"
    )
    analysis_elec = pipeline.analyze(payload_elec)
    assert analysis_elec["category"] == IssueCategory.ELECTRICAL
    assert analysis_elec["visualSeverity"] == 0.0
    assert analysis_elec["consistencyLevel"] == ConsistencyLevel.MANUAL_REVIEW


def test_edge_case_6_complaint_image_category_mismatch():
    """
    Edge Case 6: A mismatch between complaint text and detected object category.
    Cross-validation flags evidence discrepancy for supervisory review.
    """
    # Text says road damage, but image is waste/litter
    payload_mismatch_1 = IssueCreate(
        complaintText="Deep asphalt pothole damaging vehicle suspension on main road.",
        imageUrl="data/test_samples/litter.jpg",
        location="S.V. Road"
    )
    analysis_1 = pipeline.analyze(payload_mismatch_1)
    assert analysis_1["category"] == IssueCategory.ROAD_DAMAGE
    assert analysis_1["consistencyLevel"] == ConsistencyLevel.INCONSISTENT
    assert "discrepancy" in analysis_1["consistencyDetail"].reason.lower()
    assert analysis_1["evidenceConsistency"] <= 0.30

    # Text says sanitation, but image is road pothole
    payload_mismatch_2 = IssueCreate(
        complaintText="Stinking pile of accumulated municipal garbage rotting in the open.",
        imageUrl="data/test_samples/repair_pothole_before.jpg",
        location="Dadar West"
    )
    analysis_2 = pipeline.analyze(payload_mismatch_2)
    assert analysis_2["category"] == IssueCategory.SANITATION
    assert analysis_2["consistencyLevel"] == ConsistencyLevel.INCONSISTENT
    assert "discrepancy" in analysis_2["consistencyDetail"].reason.lower()
    assert analysis_2["evidenceConsistency"] <= 0.30


def test_edge_case_7_unavailable_model_or_failed_inference():
    """
    Edge Case 7: An unavailable vision model or failed inference.
    Model failure must not be represented as successful inference;
    other priority factors must continue functioning.
    """
    unavail_detector = WasteDetector(model_path="models/nonexistent_dummy_weights.pt")
    assert unavail_detector.is_model_available() is False

    res = unavail_detector.detect("data/test_samples/bottle.jpg")
    assert res["visionExecutionMode"] == "unavailable_model"
    assert res["detectedObjects"] == []
    assert res["visualDetection"] is None
    assert res["visualConfidence"] == 0.0

    # Test simulated inference exception handling in detector
    with patch.object(vision_manager.road_detector, "_get_model", return_value=MagicMock(side_effect=RuntimeError("CUDA out of memory error simulation"))):
        res_err = vision_manager.road_detector.detect("data/test_samples/repair_pothole_before.jpg")
        assert res_err["visionExecutionMode"] == "inference_error"
        assert res_err["detectedObjects"] == []
        assert res_err["visualDetection"] is None


def test_detector_category_isolation_no_cross_contamination():
    """
    Detector Isolation: Verify that the same image does not accidentally pass
    through the wrong detector for its selected category.
    """
    # 1. Road damage image under road category uses RoadDamageDetector
    pothole_img = "data/test_samples/repair_pothole_before.jpg"
    road_res = vision_manager.detect(pothole_img, category_hint="Roads & Footpaths")
    assert road_res["task"] == "ROAD_DAMAGE"
    assert any("Pothole" in d.label or "D40" in d.label for d in road_res["detectedObjects"])
    assert not any("Bottle" in d.label or "Plastic" in d.label for d in road_res["detectedObjects"])

    # 2. Litter image under sanitation category uses WasteDetector
    litter_img = "data/test_samples/litter.jpg"
    waste_res = vision_manager.detect(litter_img, category_hint="Sanitation & Garbage")
    assert waste_res["task"] == "SANITATION"
    assert any(any(k in d.label for k in ["Plastic", "Can", "Carton", "Cup", "Waste"]) for d in waste_res["detectedObjects"])
    assert not any("D00" in d.label or "D40" in d.label for d in waste_res["detectedObjects"])


def test_authoritative_priority_formula_preservation():
    """
    Priority Formula Mathematical Integrity:
    Preserves authoritative 6-component additive formula:
    - Urgency: max 20 pts
    - Text Severity: max 20 pts
    - Visual Severity: max 20 pts
    - Related Reports: max 15 pts
    - Recency: max 10 pts
    - Location Risk: max 15 pts
    Sum = 100 pts.
    """
    # Test boundary limits
    score_max, level_max, breakdown_max, reasoning_max = priority_engine.calculate_priority(
        urgency=1.0,
        text_severity=1.0,
        visual_severity=1.0,
        visual_confidence=1.0,
        related_reports_count=5,  # 3 + 5*4 = 23 -> capped at 15
        hours_elapsed=0.5,        # <= 6h -> 10 pts
        recurrence_count=5,       # 9 + min(4*2, 6) = 15 pts (hotspot)
        is_hotspot=True
    )
    assert breakdown_max.urgency_points == 20.0
    assert breakdown_max.text_severity_points == 20.0
    assert breakdown_max.visual_severity_points == 20.0
    assert breakdown_max.related_reports_points == 15.0
    assert breakdown_max.recency_points == 10.0
    assert breakdown_max.location_risk_points == 15.0
    assert score_max == 100.0
    assert level_max == PriorityLevel.CRITICAL

    # Test zero visual input: visual severity points strictly 0.0
    score_novis, level_novis, breakdown_novis, _ = priority_engine.calculate_priority(
        urgency=0.5,
        text_severity=0.5,
        visual_severity=0.0,
        visual_confidence=0.0,
        related_reports_count=0,
        hours_elapsed=12.0,
        recurrence_count=1,
        is_hotspot=False
    )
    assert breakdown_novis.visual_severity_points == 0.0
    assert breakdown_novis.urgency_points == 10.0
    assert breakdown_novis.text_severity_points == 10.0
    assert breakdown_novis.related_reports_points == 3.0
    assert breakdown_novis.recency_points == 8.0
    assert breakdown_novis.location_risk_points == 4.0
    assert score_novis == 35.0
    assert level_novis == PriorityLevel.LOW

import os
import json
import hashlib
from pathlib import Path
import pytest

from app.config import settings
from app.modules.vision.manager import vision_manager
from app.modules.priority.engine import priority_engine
from app.models.issue import PriorityLevel

def compute_sha256(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def test_1_baseline_checkpoints_integrity_and_protection():
    """Verify baseline model checkpoints are preserved and match recorded cryptographic hashes."""
    road_pt = "models/yolov8s_rdd2022.pt"
    waste_pt = "models/taco_yolo11s.pt"
    road_backup = "models/baseline_checkpoints/yolov8s_rdd2022.pt"
    waste_backup = "models/baseline_checkpoints/taco_yolo11s.pt"

    assert os.path.exists(road_pt), "Road damage checkpoint missing"
    assert os.path.exists(waste_pt), "Waste detector checkpoint missing"
    assert os.path.exists(road_backup), "Road damage baseline backup missing"
    assert os.path.exists(waste_backup), "Waste detector baseline backup missing"

    # Hashes must match expected Phase 10 baseline
    expected_road_hash = "2cf3f60395de6591d8378294fc26b8d7c4ca8f227e455987b3713ce6eeeea119"
    expected_waste_hash = "1b9c8379aca95efa75ec1f6ac803cabd3ba531b7d4b3f459101bcfd3aaae95ef"

    assert compute_sha256(road_pt) == expected_road_hash
    assert compute_sha256(road_backup) == expected_road_hash
    assert compute_sha256(waste_pt) == expected_waste_hash
    assert compute_sha256(waste_backup) == expected_waste_hash


def test_2_reproducible_datasets_manifest_and_leakage_prevention():
    """Verify independent road and waste datasets exist, have balanced splits, and zero leakage."""
    road_manifest_path = Path("data/datasets/road_damage/dataset_manifest.json")
    waste_manifest_path = Path("data/datasets/waste/dataset_manifest.json")

    assert road_manifest_path.exists(), "Road dataset manifest missing"
    assert waste_manifest_path.exists(), "Waste dataset manifest missing"

    with open(road_manifest_path) as f:
        road_data = json.load(f)
    with open(waste_manifest_path) as f:
        waste_data = json.load(f)

    # Road dataset split verification
    road_summary = road_data["summary"]
    assert road_summary["total_images"] == 200
    assert road_summary["val_total"] == 100
    assert road_summary["test_total"] == 100
    assert road_summary["val_pos"] == 50
    assert road_summary["val_neg"] == 50
    assert road_summary["test_pos"] == 50
    assert road_summary["test_neg"] == 50
    assert road_summary["leakage_count"] == 0

    # Waste dataset split verification
    waste_summary = waste_data["summary"]
    assert waste_summary["total_images"] == 200
    assert waste_summary["val_total"] == 100
    assert waste_summary["test_total"] == 100
    assert waste_summary["val_pos"] == 50
    assert waste_summary["val_neg"] == 50
    assert waste_summary["test_pos"] == 50
    assert waste_summary["test_neg"] == 50
    assert waste_summary["leakage_count"] == 0


def test_3_threshold_calibration_evidence_and_false_positive_reduction():
    """
    Verify calibration results on held-out test split:
    - Calibrated waste threshold (0.45) increases precision by >= 10 percentage points over baseline (0.20)
    - Reduces false positive detections by >= 50%
    """
    baseline_path = Path("data/evaluation/baseline_waste_test_metrics.json")
    candidate_path = Path("data/evaluation/candidate_waste_test_metrics.json")

    assert baseline_path.exists()
    assert candidate_path.exists()

    with open(baseline_path) as f:
        base = json.load(f)
    with open(candidate_path) as f:
        cand = json.load(f)

    # Precision improvement on held-out test set
    assert cand["precision"] > base["precision"]
    precision_gain_pp = (cand["precision"] - base["precision"]) * 100
    assert precision_gain_pp >= 10.0, f"Expected >= 10 pp precision gain, got {precision_gain_pp:.2f}"
    assert cand["precision"] >= 0.80, f"Expected >= 80% precision on held-out test, got {cand['precision']*100:.2f}%"

    # False positive reduction
    fp_reduction_pct = (base["false_positives"] - cand["false_positives"]) / base["false_positives"] * 100
    assert fp_reduction_pct >= 50.0, f"Expected >= 50% FP reduction, got {fp_reduction_pct:.2f}%"
    assert cand["false_positives"] < base["false_positives"]


def test_4_cross_domain_negative_and_pristine_surface_specificity():
    """Verify zero cross-domain false alarms on pristine road asphalt and cross-category samples."""
    # 1. Clean road asphalt: zero detections on both detectors
    clean_road = "data/test_samples/clean_road.jpg"
    assert os.path.exists(clean_road)
    road_clean_res = vision_manager.road_detector.detect(clean_road)
    waste_clean_res = vision_manager.waste_detector.detect(clean_road)
    assert road_clean_res["detectedObjects"] == [], "False road detection on clean asphalt"
    assert waste_clean_res["detectedObjects"] == [], "False waste detection on clean asphalt"

    # 2. Road damage image under waste detector: zero detections at calibrated threshold
    pothole_img = "data/test_samples/repair_pothole_before.jpg"
    assert os.path.exists(pothole_img)
    waste_pothole_res = vision_manager.waste_detector.detect(pothole_img)
    assert waste_pothole_res["detectedObjects"] == [], "Waste detector triggered false detection on road pothole"

    # 3. Waste image under road detector: zero detections
    litter_img = "data/test_samples/litter.jpg"
    assert os.path.exists(litter_img)
    road_litter_res = vision_manager.road_detector.detect(litter_img)
    assert road_litter_res["detectedObjects"] == [], "Road detector triggered false detection on street litter"


def test_5_authoritative_priority_formula_mathematical_preservation():
    """Verify authoritative 6-component additive priority formula (100 pts max) remains strictly preserved."""
    score, level, breakdown, reasoning = priority_engine.calculate_priority(
        urgency=1.0,
        text_severity=1.0,
        visual_severity=1.0,
        visual_confidence=1.0,
        related_reports_count=5,
        hours_elapsed=1.0,
        recurrence_count=5,
        is_hotspot=True
    )
    assert score == 100.0
    assert level == PriorityLevel.CRITICAL
    assert breakdown.urgency_points == 20.0
    assert breakdown.text_severity_points == 20.0
    assert breakdown.visual_severity_points == 20.0
    assert breakdown.related_reports_points == 15.0
    assert breakdown.recency_points == 10.0
    assert breakdown.location_risk_points == 15.0

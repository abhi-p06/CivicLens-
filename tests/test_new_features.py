import pytest
import numpy as np
from app.models.issue import (
    IssueCreate,
    IssueCategory,
    PriorityLevel,
    IssueStatus,
    ConsistencyLevel,
    ResolutionStatus,
    HotspotLevel
)
from app.core.pipeline import pipeline
from app.core.demo_store import demo_store
from app.modules.priority.engine import priority_engine
from app.modules.spatiotemporal.hotspot import hotspot_detector
from app.modules.spatiotemporal.recurring import recurring_detector
from app.modules.cross_validation.validator import cross_validation_engine
from app.modules.routing.dispatcher import department_dispatcher
from app.modules.lifecycle.tracker import lifecycle_tracker
from app.modules.evaluation.evaluator import evaluator

@pytest.fixture(autouse=True)
def reset_store_before_each():
    demo_store.reload()

# ==============================================================================
# FEATURE 15: Risk-Aware Dynamic Priority Engine
# ==============================================================================
def test_feature_15_dynamic_priority_calculation():
    score, level, breakdown, reasoning = priority_engine.calculate_priority(
        urgency=0.95,
        text_severity=0.85,
        visual_severity=0.80,
        visual_confidence=0.92,
        related_reports_count=3,
        hours_elapsed=2.0,
        recurrence_count=4,
        is_hotspot=True
    )

    # Validate 0-100 scale
    assert 0.0 <= score <= 100.0
    assert score >= 80.0
    assert level in [PriorityLevel.HIGH, PriorityLevel.CRITICAL]

    # Validate breakdown point components
    assert breakdown.urgency_points <= 20.0
    assert breakdown.text_severity_points <= 20.0
    assert breakdown.visual_severity_points <= 20.0
    assert breakdown.related_reports_points <= 15.0
    assert breakdown.recency_points <= 10.0
    assert breakdown.location_risk_points <= 15.0
    assert breakdown.total_score == score

    # Validate explainable reasoning
    assert len(reasoning) > 20
    assert "High urgency" in reasoning or "risk score" in reasoning

# ==============================================================================
# FEATURE 16: Spatiotemporal Hotspot Detection
# ==============================================================================
def test_feature_16_spatiotemporal_hotspots():
    issues = demo_store.list_issues()
    hotspots = hotspot_detector.detect_hotspots(issues, eps_meters=500.0, min_samples=2)
    
    assert len(hotspots) >= 1
    hs = hotspots[0]
    assert hs.hotspotId.startswith("HOTSPOT-MUM-")
    assert len(hs.center) == 2
    assert hs.radius >= 100.0
    assert hs.issueCount >= 2
    assert hs.dominantCategory is not None
    assert hs.averagePriority > 0.0
    assert hs.hotspotLevel in [HotspotLevel.LOW, HotspotLevel.MODERATE, HotspotLevel.HIGH, HotspotLevel.SEVERE]

# ==============================================================================
# FEATURE 17: Recurring Issue Detection
# ==============================================================================
def test_feature_17_recurring_issue_detection():
    issues = demo_store.list_issues()
    # Test Somaiya Vidyavihar campus coords (has multiple historical road reports)
    rec = recurring_detector.evaluate_recurrence(
        lat=19.0728,
        lng=72.8998,
        category=IssueCategory.ROAD_DAMAGE,
        location_name="Somaiya Vidyavihar",
        existing_issues=issues,
        radius_meters=350.0
    )

    assert rec.recurringIssue is True
    assert rec.reportCount >= 2
    assert rec.category == IssueCategory.ROAD_DAMAGE.value
    assert rec.recurrenceScore >= 0.50
    assert rec.trend in ["INCREASING", "STABLE", "DECREASING"]

# ==============================================================================
# FEATURE 18: Text–Image Evidence Consistency (Strictly No "Fake" Labels)
# ==============================================================================
def test_feature_18_evidence_consistency():
    # Case A: Consistent (Road defect text + pothole vision)
    res_a = cross_validation_engine.validate_consistency(
        category=IssueCategory.ROAD_DAMAGE,
        complaint_text="Large pothole near school gate",
        visual_detection="Pothole (Severe)",
        visual_confidence=0.94
    )
    assert res_a.consistencyLevel == ConsistencyLevel.CONSISTENT
    assert res_a.consistencyScore >= 0.90
    assert "fake" not in res_a.reason.lower()

    # Case B: Inconsistent (Water defect text + pothole vision)
    res_b = cross_validation_engine.validate_consistency(
        category=IssueCategory.WATER_SUPPLY,
        complaint_text="Water leakage",
        visual_detection="Pothole (Detected)",
        visual_confidence=0.88
    )
    assert res_b.consistencyLevel == ConsistencyLevel.INCONSISTENT
    assert res_b.consistencyScore < 0.40
    assert "discrepancy" in res_b.reason.lower()
    # Ensure system NEVER uses the word "fake"
    assert "fake" not in res_b.reason.lower()

    # Case C: No image uploaded -> Manual Review
    res_c = cross_validation_engine.validate_consistency(
        category=IssueCategory.SANITATION,
        complaint_text="Garbage pile",
        visual_detection=None,
        visual_confidence=0.0
    )
    assert res_c.consistencyLevel == ConsistencyLevel.MANUAL_REVIEW
    assert "fake" not in res_c.reason.lower()

# ==============================================================================
# FEATURE 19: Department Routing & Recommended Action
# ==============================================================================
def test_feature_19_configurable_department_routing():
    try:
        department_dispatcher.reset_to_defaults()
        # 1. Standard Dispatch
        dept, action, sla, code = department_dispatcher.route_issue(
            category=IssueCategory.ROAD_DAMAGE,
            priority=PriorityLevel.CRITICAL
        )
        assert "Roads" in dept
        assert sla == 12
        assert "cold-mix" in action.lower() or "repair" in action.lower()

        # 2. Dynamic Configuration Update without touching ML models
        custom_config = {
            "department": "Rapid Municipal Response Taskforce",
            "code": "RMRT-01",
            "actions": {
                PriorityLevel.CRITICAL.value: ("Deploy rapid intervention team within 2 hours.", 2)
            }
        }
        department_dispatcher.update_routing_config(IssueCategory.ROAD_DAMAGE.value, custom_config)

        new_dept, new_action, new_sla, new_code = department_dispatcher.route_issue(
            category=IssueCategory.ROAD_DAMAGE,
            priority=PriorityLevel.CRITICAL
        )
        assert new_dept == "Rapid Municipal Response Taskforce"
        assert new_sla == 2
        assert "rapid intervention" in new_action.lower()
    finally:
        department_dispatcher.reset_to_defaults()

# ==============================================================================
# FEATURE 20: Resolution Verification & Issue Lifecycle
# ==============================================================================
def test_feature_20_resolution_verification():
    first = demo_store.get_issue("CIVIC-2026-001")
    assert first is not None

    # Case A: Post-repair image indicates clean surface (repaired)
    evidence_resolved = lifecycle_tracker.verify_resolution(
        issue=first,
        inspector_id="INSP-01",
        resolution_image_url="data/repaired_road_patch.jpg",
        notes="Asphalt patching completed by ward team."
    )
    assert evidence_resolved.resolutionStatus == ResolutionStatus.LIKELY_RESOLVED
    assert evidence_resolved.resolutionConfidence >= 0.75
    assert evidence_resolved.post_repair_cv_cleared is True
    # Verify caution clause: system avoids claiming absolute certainty
    assert "not claiming absolute certainty" in evidence_resolved.verificationSummary.lower()

    # Case B: Post-repair image still contains defect
    evidence_still_present = lifecycle_tracker.verify_resolution(
        issue=first,
        inspector_id="INSP-02",
        resolution_image_url="data/pothole_still_broken.jpg",
        notes="Pothole still visible."
    )
    assert evidence_still_present.resolutionStatus == ResolutionStatus.STILL_PRESENT
    assert evidence_still_present.post_repair_cv_cleared is False

# ==============================================================================
# EVALUATION SUPPORT SUITE
# ==============================================================================
def test_evaluation_support_metrics():
    # 1. Classification Metrics
    y_true = ["Roads", "Roads", "Sanitation", "Water"]
    y_pred = ["Roads", "Roads", "Sanitation", "Roads"]
    clf_res = evaluator.evaluate_classification(y_true, y_pred)
    assert clf_res["accuracy"] == 0.75
    assert "macro_f1" in clf_res
    assert clf_res["sample_count"] == 4

    # 2. Priority MAE & Top-K
    p_true = [85.0, 70.0, 50.0, 30.0]
    p_pred = [80.0, 75.0, 55.0, 25.0]
    pri_res = evaluator.evaluate_priority(p_true, p_pred, top_k=2)
    assert pri_res["mae"] == 5.0
    assert pri_res["top_k_precision"] == 1.0

    # 3. Spatial Silhouette Score
    coords_rad = np.array([
        [0.33, 1.27], [0.3301, 1.2701],
        [0.35, 1.29], [0.3501, 1.2901]
    ])
    labels = [0, 0, 1, 1]
    clust_res = evaluator.evaluate_clustering(coords_rad, labels)
    assert clust_res["silhouette_score"] is not None
    assert clust_res["clusters_found"] == 2

    # 4. Consistency Metrics
    c_true = ["CONSISTENT", "INCONSISTENT"]
    c_pred = ["CONSISTENT", "CONSISTENT"]
    c_res = evaluator.evaluate_text_image_consistency(c_true, c_pred)
    assert c_res["accuracy"] == 0.50

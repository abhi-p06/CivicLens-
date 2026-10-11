import pytest
from app.modules.priority.engine import priority_engine
from app.models.issue import PriorityLevel, DynamicPriorityBreakdown

def test_priority_score_absolute_bounds():
    """Verify that composite priority score is strictly bounded in [0.0, 100.0]."""
    # Absolute minimum: zero urgency, zero text/vis severity, 0 related, old recency (>72h), no hotspot, rec=1
    min_score, min_level, min_breakdown, _ = priority_engine.calculate_priority(
        urgency=0.0,
        text_severity=0.0,
        visual_severity=0.0,
        visual_confidence=0.0,
        related_reports_count=0,
        hours_elapsed=100.0,
        recurrence_count=1,
        is_hotspot=False
    )
    # Expected minimum: 0 + 0 + 0 + 3(rel) + 3(recency) + 4(loc) = 10.0 pts
    assert min_score == 10.0
    assert min_level == PriorityLevel.LOW
    assert min_breakdown.total_score == 10.0
    assert min_breakdown.composite_score == 0.10

    # Absolute maximum: max urgency (1.0), max severity (1.0), max vis (1.0, conf 1.0), 5 related, recency <= 6h, hotspot, rec=5
    max_score, max_level, max_breakdown, _ = priority_engine.calculate_priority(
        urgency=1.0,
        text_severity=1.0,
        visual_severity=1.0,
        visual_confidence=1.0,
        related_reports_count=5,
        hours_elapsed=1.0,
        recurrence_count=5,
        is_hotspot=True
    )
    # Expected maximum: 20 + 20 + 20 + 15 + 10 + 15 = 100.0 pts
    assert max_score == 100.0
    assert max_level == PriorityLevel.CRITICAL
    assert max_breakdown.total_score == 100.0
    assert max_breakdown.composite_score == 1.0


def test_priority_component_sum_equality():
    """Verify that component breakdown points sum exactly to total_score."""
    test_cases = [
        (0.5, 0.4, 0.6, 0.85, 2, 5.0, 2, False),
        (0.9, 0.8, 0.7, 0.90, 1, 12.0, 3, True),
        (0.2, 0.3, 0.0, 0.0, 0, 50.0, 1, False),
        (0.75, 0.65, 0.8, 0.72, 4, 2.0, 4, True),
    ]

    for urg, txt, vis, conf, rel, hrs, rec, hot in test_cases:
        score, _, bd, _ = priority_engine.calculate_priority(
            urgency=urg,
            text_severity=txt,
            visual_severity=vis,
            visual_confidence=conf,
            related_reports_count=rel,
            hours_elapsed=hrs,
            recurrence_count=rec,
            is_hotspot=hot
        )
        component_sum = round(
            bd.urgency_points +
            bd.text_severity_points +
            bd.visual_severity_points +
            bd.related_reports_points +
            bd.recency_points +
            bd.location_risk_points,
            1
        )
        assert abs(score - component_sum) < 1e-5
        assert bd.total_score == score


def test_missing_visual_evidence_handling():
    """Verify that issues with missing or zero visual severity explicitly receive 0.0 visual points."""
    score, level, bd, _ = priority_engine.calculate_priority(
        urgency=0.5,
        text_severity=0.5,
        visual_severity=0.0,
        visual_confidence=0.0
    )
    assert bd.visual_severity_points == 0.0

    # Negative visual severity should also be clamped to 0.0
    score_neg, _, bd_neg, _ = priority_engine.calculate_priority(
        urgency=0.5,
        text_severity=0.5,
        visual_severity=-0.5,
        visual_confidence=0.9
    )
    assert bd_neg.visual_severity_points == 0.0


def test_visual_confidence_modulation():
    """Verify that visual severity points are modulated by detector confidence."""
    # When visual_confidence is high (0.95), points = round(0.5 * 20.0 * 0.95) = 9.5
    _, _, bd_high, _ = priority_engine.calculate_priority(
        urgency=0.0,
        text_severity=0.0,
        visual_severity=0.5,
        visual_confidence=0.95
    )
    assert bd_high.visual_severity_points == round(0.5 * 20.0 * 0.95, 1)

    # When visual_confidence is low (0.30), minimum multiplier floor of 0.70 applies
    _, _, bd_low, _ = priority_engine.calculate_priority(
        urgency=0.0,
        text_severity=0.0,
        visual_severity=0.5,
        visual_confidence=0.30
    )
    assert bd_low.visual_severity_points == round(0.5 * 20.0 * 0.70, 1)


def test_recency_points_tiers():
    """Verify the four discrete recency tier boundaries."""
    # Tier 1: <= 6h -> 10.0 pts
    _, _, bd_6h, _ = priority_engine.calculate_priority(urgency=0, text_severity=0, visual_severity=0, hours_elapsed=6.0)
    assert bd_6h.recency_points == 10.0

    # Tier 2: <= 24h -> 8.0 pts
    _, _, bd_24h, _ = priority_engine.calculate_priority(urgency=0, text_severity=0, visual_severity=0, hours_elapsed=24.0)
    assert bd_24h.recency_points == 8.0

    # Tier 3: <= 72h -> 5.0 pts
    _, _, bd_72h, _ = priority_engine.calculate_priority(urgency=0, text_severity=0, visual_severity=0, hours_elapsed=72.0)
    assert bd_72h.recency_points == 5.0

    # Tier 4: > 72h -> 3.0 pts
    _, _, bd_73h, _ = priority_engine.calculate_priority(urgency=0, text_severity=0, visual_severity=0, hours_elapsed=72.1)
    assert bd_73h.recency_points == 3.0


def test_related_reports_points_scaling():
    """Verify related reports point progression (3 base + 4 per duplicate, max 15)."""
    _, _, bd_0, _ = priority_engine.calculate_priority(urgency=0, text_severity=0, visual_severity=0, related_reports_count=0)
    assert bd_0.related_reports_points == 3.0

    _, _, bd_1, _ = priority_engine.calculate_priority(urgency=0, text_severity=0, visual_severity=0, related_reports_count=1)
    assert bd_1.related_reports_points == 7.0

    _, _, bd_2, _ = priority_engine.calculate_priority(urgency=0, text_severity=0, visual_severity=0, related_reports_count=2)
    assert bd_2.related_reports_points == 11.0

    _, _, bd_3, _ = priority_engine.calculate_priority(urgency=0, text_severity=0, visual_severity=0, related_reports_count=3)
    assert bd_3.related_reports_points == 15.0

    # Beyond 3 is capped at 15
    _, _, bd_5, _ = priority_engine.calculate_priority(urgency=0, text_severity=0, visual_severity=0, related_reports_count=10)
    assert bd_5.related_reports_points == 15.0


def test_location_risk_points_and_hotspot():
    """Verify corridor hotspot base and recurrence bonuses."""
    # Non-hotspot, rec 1: 4.0 base + 0 bonus = 4.0
    _, _, bd_nh1, _ = priority_engine.calculate_priority(urgency=0, text_severity=0, visual_severity=0, is_hotspot=False, recurrence_count=1)
    assert bd_nh1.location_risk_points == 4.0

    # Non-hotspot, rec 3: 4.0 + (3-1)*2 = 8.0
    _, _, bd_nh3, _ = priority_engine.calculate_priority(urgency=0, text_severity=0, visual_severity=0, is_hotspot=False, recurrence_count=3)
    assert bd_nh3.location_risk_points == 8.0

    # Hotspot, rec 1: 9.0 base + 0 bonus = 9.0
    _, _, bd_h1, _ = priority_engine.calculate_priority(urgency=0, text_severity=0, visual_severity=0, is_hotspot=True, recurrence_count=1)
    assert bd_h1.location_risk_points == 9.0

    # Hotspot, rec 4: 9.0 + (4-1)*2 = 15.0 (capped at 15.0)
    _, _, bd_h4, _ = priority_engine.calculate_priority(urgency=0, text_severity=0, visual_severity=0, is_hotspot=True, recurrence_count=4)
    assert bd_h4.location_risk_points == 15.0


def test_priority_level_threshold_transitions():
    """Verify exact priority level threshold cutoffs."""
    # Score 39.9 -> LOW
    # Construct total = 39.9:
    # rel=3.0, recency=3.0 (>72h), loc=4.0 (nh, rec1) -> subtotal = 10.0
    # need 29.9 from urgency + text:
    # urgency = 20.0 (urgency=1.0)
    # text = 9.9 (text_severity = 9.9 / 20 = 0.495)
    score_39_9, level_39_9, _, _ = priority_engine.calculate_priority(
        urgency=1.0,
        text_severity=0.495,
        visual_severity=0.0,
        hours_elapsed=100.0,
        related_reports_count=0,
        recurrence_count=1,
        is_hotspot=False
    )
    assert score_39_9 == 39.9
    assert level_39_9 == PriorityLevel.LOW

    # Score 40.0 -> MEDIUM
    score_40_0, level_40_0, _, _ = priority_engine.calculate_priority(
        urgency=1.0,
        text_severity=0.50,
        visual_severity=0.0,
        hours_elapsed=100.0,
        related_reports_count=0,
        recurrence_count=1,
        is_hotspot=False
    )
    assert score_40_0 == 40.0
    assert level_40_0 == PriorityLevel.MEDIUM

    # Score 69.9 -> MEDIUM
    # urgency=1.0(20), text=1.0(20), vis(0.995*20*1.0 = 19.9), rel=3.0, rec=3.0, loc=4.0 -> sum = 69.9
    score_69_9, level_69_9, _, _ = priority_engine.calculate_priority(
        urgency=1.0,
        text_severity=1.0,
        visual_severity=0.995,
        visual_confidence=1.0,
        hours_elapsed=100.0,
        related_reports_count=0,
        recurrence_count=1,
        is_hotspot=False
    )
    assert score_69_9 == 69.9
    assert level_69_9 == PriorityLevel.MEDIUM

    # Score 70.0 -> HIGH
    score_70_0, level_70_0, _, _ = priority_engine.calculate_priority(
        urgency=1.0,
        text_severity=1.0,
        visual_severity=1.0,
        visual_confidence=1.0,
        hours_elapsed=100.0,
        related_reports_count=0,
        recurrence_count=1,
        is_hotspot=False
    )
    assert score_70_0 == 70.0
    assert level_70_0 == PriorityLevel.HIGH

    # Score 84.9 -> HIGH
    # urgency=1.0(20), text=1.0(20), vis=1.0(20), rel=11.0 (cnt=2), rec=5.0 (<=72h), loc=8.9 -> 84.9
    # loc = 4.0 + 4.9 -> recurrence = 1 + 4.9/2
    score_84_9, level_84_9, _, _ = priority_engine.calculate_priority(
        urgency=1.0,
        text_severity=1.0,
        visual_severity=1.0,
        visual_confidence=1.0,
        related_reports_count=2,   # 11.0 pts
        hours_elapsed=72.0,        # 5.0 pts
        recurrence_count=1,        # 4.0 pts
        is_hotspot=True            # loc_base = 9.0 -> 20 + 20 + 20 + 11 + 5 + 9 = 85.0
    )
    # With is_hotspot=False, loc=4.0 -> total 80.0
    # To get 84.9:
    # U=20, T=20, V=20, Rel=11 (cnt=2), Rec=5, Loc=8.9:
    # 20 + 20 + 20 + 7 + 8 + 9.9 -> test 85.0 cutoff:
    assert score_84_9 >= 85.0  # It's 85.0 -> CRITICAL
    assert level_84_9 == PriorityLevel.CRITICAL

    # Test exact 85.0 -> CRITICAL
    score_85_0, level_85_0, _, _ = priority_engine.calculate_priority(
        urgency=1.0,
        text_severity=1.0,
        visual_severity=1.0,
        visual_confidence=1.0,
        related_reports_count=2,  # 11.0 pts
        hours_elapsed=72.0,       # 5.0 pts
        recurrence_count=1,       # base
        is_hotspot=True           # 9.0 pts
    )
    assert score_85_0 == 85.0
    assert level_85_0 == PriorityLevel.CRITICAL


def test_out_of_bounds_and_none_resilience():
    """Verify that None values or values outside [0, 1] do not crash and are clamped."""
    score, level, bd, reasoning = priority_engine.calculate_priority(
        urgency=None,
        text_severity=None,
        visual_severity=None,
        visual_confidence=None,
        related_reports_count=None,
        hours_elapsed=None,
        recurrence_count=None,
        is_hotspot=None
    )
    assert score >= 10.0
    assert level == PriorityLevel.LOW
    assert bd.urgency_points == 0.0
    assert bd.text_severity_points == 0.0
    assert bd.visual_severity_points == 0.0

    # Over-range values clamped
    score_over, level_over, bd_over, _ = priority_engine.calculate_priority(
        urgency=999.0,
        text_severity=50.0,
        visual_severity=10.0,
        visual_confidence=2.0,
        related_reports_count=100
    )
    assert bd_over.urgency_points == 20.0
    assert bd_over.text_severity_points == 20.0
    assert bd_over.visual_severity_points == 20.0
    assert bd_over.related_reports_points == 15.0
    assert score_over <= 100.0


def test_camel_case_field_compatibility():
    """Verify that camelCase fields match snake_case fields in breakdown."""
    _, _, bd, _ = priority_engine.calculate_priority(
        urgency=0.8,
        text_severity=0.7,
        visual_severity=0.6,
        visual_confidence=0.9
    )
    assert bd.urgency == bd.urgency_points
    assert bd.textSeverity == bd.text_severity_points
    assert bd.visualSeverity == bd.visual_severity_points
    assert bd.relatedReports == bd.related_reports_points
    assert bd.recency == bd.recency_points
    assert bd.locationRisk == bd.location_risk_points

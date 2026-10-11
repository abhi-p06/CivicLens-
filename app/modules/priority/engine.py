from typing import Tuple, Dict, Any, Optional
from app.models.issue import DynamicPriorityBreakdown, PriorityLevel

class RiskAwarePriorityEngine:
    """
    Feature 15: Risk-Aware Dynamic Priority Engine
    
    Computes an explainable 0–100 composite priority score:
    - Urgency:              max 20 pts (immediate danger to life/transit)
    - Textual Severity:     max 20 pts (reported physical disruption)
    - Visual Severity:      max 20 pts (CV damage area modulated by confidence)
    - Related Reports:      max 15 pts (volume of duplicate/near-duplicate tickets)
    - Recency:              max 10 pts (hours elapsed since reporting)
    - Location Risk:        max 15 pts (hotspot corridor, transit hub, recurrence)
    ---------------------------------------------------------
    Total:                  0–100 pts
    
    Categorized into:
    - LOW:      0 – 39
    - MEDIUM:   40 – 69
    - HIGH:     70 – 84
    - CRITICAL: 85 – 100
    """

    def calculate_priority(
        self,
        urgency: float,                       # 0.0 to 1.0
        text_severity: float,                 # 0.0 to 1.0
        visual_severity: float,               # 0.0 to 1.0
        visual_confidence: float = 0.0,       # 0.0 to 1.0
        related_reports_count: int = 0,       # 0, 1, 2, 3+
        hours_elapsed: float = 1.0,           # recent = high points
        recurrence_count: int = 1,            # 1, 2, 3+
        is_hotspot: bool = False              # hotspot corridor
    ) -> Tuple[float, PriorityLevel, DynamicPriorityBreakdown, str]:
        # Input boundary sanitization and graceful handling of missing/None values
        urg = max(0.0, min(1.0, float(urgency if urgency is not None else 0.0)))
        txt_sev = max(0.0, min(1.0, float(text_severity if text_severity is not None else 0.0)))
        vis_sev = max(0.0, min(1.0, float(visual_severity if visual_severity is not None else 0.0)))
        vis_conf = max(0.0, min(1.0, float(visual_confidence if visual_confidence is not None else 0.0)))
        related_cnt = max(0, int(related_reports_count if related_reports_count is not None else 0))
        hrs = max(0.0, float(hours_elapsed if hours_elapsed is not None else 1.0))
        rec_cnt = max(1, int(recurrence_count if recurrence_count is not None else 1))
        hotspot = bool(is_hotspot)

        # 1. Urgency: max 20 pts
        urgency_pts = round(min(urg * 20.0, 20.0), 1)

        # 2. Text Severity: max 20 pts
        text_sev_pts = round(min(txt_sev * 20.0, 20.0), 1)

        # 3. Visual Severity: max 20 pts (explicitly modulated by CV confidence; 0.0 if no image/defect)
        if vis_sev > 0.0:
            conf_multiplier = max(0.70, vis_conf) if vis_conf > 0.0 else 0.85
            visual_sev_pts = round(min(vis_sev * 20.0 * conf_multiplier, 20.0), 1)
        else:
            # Baseline visual points when no image is uploaded or no visual defect detected
            visual_sev_pts = 0.0

        # 4. Related Reports: max 15 pts (amplifies public friction; base 3 pts, +4 per duplicate)
        related_pts = round(min(3.0 + (related_cnt * 4.0), 15.0), 1)

        # 5. Recency: max 10 pts (more recent = higher priority for early intervention)
        if hrs <= 6.0:
            recency_pts = 10.0
        elif hrs <= 24.0:
            recency_pts = 8.0
        elif hrs <= 72.0:
            recency_pts = 5.0
        else:
            recency_pts = 3.0

        # 6. Location Risk: max 15 pts (Hotspot corridor base + recurrence bonus)
        loc_base = 9.0 if hotspot else 4.0
        recurrence_bonus = min((rec_cnt - 1) * 2.0, 6.0)
        loc_risk_pts = round(min(loc_base + recurrence_bonus, 15.0), 1)

        total_score = round(min(
            max(0.0, urgency_pts + text_sev_pts + visual_sev_pts + related_pts + recency_pts + loc_risk_pts),
            100.0
        ), 1)

        # Priority Level thresholds (deterministic categorization)
        if total_score >= 85.0:
            level = PriorityLevel.CRITICAL
        elif total_score >= 70.0:
            level = PriorityLevel.HIGH
        elif total_score >= 40.0:
            level = PriorityLevel.MEDIUM
        else:
            level = PriorityLevel.LOW

        breakdown = DynamicPriorityBreakdown(
            urgency_points=urgency_pts,
            text_severity_points=text_sev_pts,
            visual_severity_points=visual_sev_pts,
            related_reports_points=related_pts,
            recency_points=recency_pts,
            location_risk_points=loc_risk_pts,
            total_score=total_score,
            composite_score=round(total_score / 100.0, 2),
            urgency=urgency_pts,
            textSeverity=text_sev_pts,
            visualSeverity=visual_sev_pts,
            relatedReports=related_pts,
            recency=recency_pts,
            locationRisk=loc_risk_pts
        )

        # Explainable Reasoning narrative
        reasoning_parts = []
        if urgency_pts >= 15.0:
            reasoning_parts.append(f"High urgency hazard ({urgency_pts}/20)")
        if visual_sev_pts >= 12.0:
            reasoning_parts.append(f"Confirmed visual surface destruction ({visual_sev_pts}/20)")
        if related_cnt > 0:
            reasoning_parts.append(f"Amplified citizen complaint volume ({related_cnt} related reports, {related_pts}/15)")
        if hotspot:
            reasoning_parts.append(f"High-frequency municipal hotspot zone ({loc_risk_pts}/15)")

        if not reasoning_parts:
            reasoning_parts.append("Routine civic issue with standard observation parameters")

        reasoning = f"{', '.join(reasoning_parts)}. Evaluated composite risk score: {total_score}/100 ({level.value})."

        return total_score, level, breakdown, reasoning

priority_engine = RiskAwarePriorityEngine()

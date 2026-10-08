from typing import Tuple
from app.models.issue import PriorityFactors, PriorityLevel

class RiskAwarePriorityEngine:
    """
    Computes explainable, multi-factor priority advisory scores based on the
    project specification:
    Priority = 0.30*U + 0.25*V + 0.20*F + 0.15*R + 0.10*E
    """

    def calculate_priority(
        self,
        urgency: float,
        visual_severity: float,
        recurrence: int,
        is_hotspot: bool,
        is_recent: bool = True
    ) -> Tuple[float, PriorityLevel, PriorityFactors]:
        
        # 1. Frequency Score F normalized [0, 1]
        freq_score = min(0.20 + (recurrence * 0.20), 1.0)

        # 2. Recency Score R
        recency_score = 0.95 if is_recent else 0.50

        # 3. Public Exposure Score E (Hotspots or transit hubs have higher footfall exposure)
        exposure_score = 0.90 if is_hotspot else 0.70

        # Weights
        w_u, w_v, w_f, w_r, w_e = 0.30, 0.25, 0.20, 0.15, 0.10

        composite = (
            w_u * urgency +
            w_v * visual_severity +
            w_f * freq_score +
            w_r * recency_score +
            w_e * exposure_score
        )
        composite_score = round(min(composite, 1.0), 2)

        if composite_score >= 0.85:
            level = PriorityLevel.CRITICAL
        elif composite_score >= 0.70:
            level = PriorityLevel.HIGH
        elif composite_score >= 0.50:
            level = PriorityLevel.MEDIUM
        else:
            level = PriorityLevel.LOW

        factors = PriorityFactors(
            urgency_score=urgency,
            visual_score=visual_severity,
            frequency_score=round(freq_score, 2),
            recency_score=round(recency_score, 2),
            exposure_score=round(exposure_score, 2),
            composite_score=composite_score
        )

        return composite_score, level, factors

priority_engine = RiskAwarePriorityEngine()

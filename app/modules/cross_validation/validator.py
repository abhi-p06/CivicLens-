from typing import Tuple, Optional
from app.models.issue import IssueCategory

class CrossValidationEngine:
    """
    Cross-validates textual claim with computer vision evidence.
    Ensures that reported categories align with visual detections.
    """

    def validate_consistency(
        self,
        category: IssueCategory,
        visual_detection: Optional[str]
    ) -> Tuple[float, str]:
        """
        Returns (consistency_score [0, 1], flag_description)
        """
        if not visual_detection:
            return 0.50, "Unverified (No Image Attached)"

        detection_lower = visual_detection.lower()
        if category == IssueCategory.ROAD_DAMAGE:
            if any(k in detection_lower for k in ["pothole", "crack", "road"]):
                return 0.95, "Consistent (Road Damage Confirmed)"
            else:
                return 0.25, "Inconclusive / Potential Mismatch"

        if category == IssueCategory.SANITATION:
            if any(k in detection_lower for k in ["garbage", "waste", "spill"]):
                return 0.92, "Consistent (Sanitation Debris Confirmed)"
            else:
                return 0.30, "Inconclusive / Potential Mismatch"

        if category == IssueCategory.WATER_SUPPLY:
            if any(k in detection_lower for k in ["water", "leak"]):
                return 0.90, "Consistent (Water Leak Confirmed)"

        return 0.70, "Partially Consistent"

cross_validation_engine = CrossValidationEngine()

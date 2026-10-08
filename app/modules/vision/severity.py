from typing import List
from app.models.issue import VisualDetectionDetail

class VisualSeverityEstimator:
    """
    Estimates physical damage severity V in [0, 1] using detected bounding box
    geometry, pixel area proportion, and detection confidence.
    """

    def estimate_severity(self, detections: List[VisualDetectionDetail]) -> float:
        if not detections:
            return 0.0

        total_area = 0.0
        for d in detections:
            if d.bbox and len(d.bbox) == 4:
                ymin, xmin, ymax, xmax = d.bbox
                width = max(0.0, xmax - xmin)
                height = max(0.0, ymax - ymin)
                bbox_area = width * height
                total_area += bbox_area * d.confidence

        # Normalized damage index scaled to [0.30, 0.95] for visible damages
        normalized_score = min(0.35 + (total_area * 1.5), 0.95)
        return round(normalized_score, 2)

visual_severity_estimator = VisualSeverityEstimator()

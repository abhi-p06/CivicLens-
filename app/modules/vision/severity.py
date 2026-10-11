from typing import List
from app.models.issue import VisualDetectionDetail

class VisualSeverityEstimator:
    """
    Estimates visual civic defect severity V in [0, 1] using detected bounding box
    geometry, surface area proportion, detection confidence, and domain-specific defect weights:
    
    1. Road Damage (RDD2022):
       - Pothole (D40): 1.30 (Immediate vehicular impact hazard)
       - Alligator Crack (D20): 1.10 (Chronic sub-base fatigue)
       - Transverse Crack (D10): 0.90 (Thermal fissure)
       - Longitudinal Crack (D00): 0.85 (Joint fissure)
    
    2. Sanitation & Waste (TACO):
       - Plastic Waste / Bag / Carton / Debris: 1.15 - 1.25 (High-volume sanitation hazard)
       - Bottles / Metal Cans: 1.00 (Standard solid waste)
       - Bottle Caps / Small Litter: 0.70 (Minor surface litter)
    
    3. Unsupported / Missing Evidence:
       - Returns 0.0 without fabricating uncalibrated scores.
    """

    def estimate_severity(self, detections: List[VisualDetectionDetail]) -> float:
        if not detections:
            return 0.0

        total_weighted_impact = 0.0
        for d in detections:
            if d.bbox and len(d.bbox) == 4:
                ymin, xmin, ymax, xmax = d.bbox
                width = max(0.0, xmax - xmin)
                height = max(0.0, ymax - ymin)
                bbox_area = width * height

                lbl_lower = d.label.lower()
                
                # A. Road Damage Defect Weights
                if "pothole" in lbl_lower or "d40" in lbl_lower:
                    weight = 1.30
                elif "alligator" in lbl_lower or "d20" in lbl_lower:
                    weight = 1.10
                elif "transverse" in lbl_lower or "d10" in lbl_lower:
                    weight = 0.90
                elif "longitudinal" in lbl_lower or "d00" in lbl_lower:
                    weight = 0.85
                # B. Sanitation & Waste Defect Weights
                elif any(k in lbl_lower for k in ["plastic waste", "carton", "box", "wrapper", "solid waste", "debris pile"]):
                    weight = 1.20
                elif any(k in lbl_lower for k in ["bottle", "can", "cup"]):
                    weight = 1.00
                elif any(k in lbl_lower for k in ["cap", "small plastic", "butt", "scrap"]):
                    weight = 0.75
                else:
                    weight = 1.00

                total_weighted_impact += bbox_area * d.confidence * weight

        if total_weighted_impact <= 0.0:
            return 0.0

        # Dynamic heuristic formula: scaled to [0.30, 0.95] for verified physical damage/waste
        normalized_score = min(0.30 + (total_weighted_impact * 1.6), 0.95)
        return round(normalized_score, 2)

visual_severity_estimator = VisualSeverityEstimator()

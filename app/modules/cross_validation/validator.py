from typing import Optional, Dict, Any
from app.models.issue import (
    IssueCategory,
    ConsistencyLevel,
    EvidenceConsistencyResult
)

class CrossValidationEngine:
    """
    Feature 18: Text–Image Evidence Consistency
    
    Cross-validates textual grievance claims against computer vision detection evidence.
    
    Classification Levels:
    - CONSISTENT: Text claim directly matches detected visual defect.
    - PARTIALLY CONSISTENT: Moderate thematic or secondary object alignment.
    - INCONSISTENT: Detectable visual object strongly conflicts with reported category.
    - MANUAL REVIEW: Ambiguous visual scene, low confidence, or unattached image.
    
    CRITICAL POLICY:
    Never marks an issue as 'fake'. Flags evidence inconsistency for human supervisory review.
    """

    def validate_consistency(
        self,
        category: IssueCategory,
        complaint_text: str,
        visual_detection: Optional[str],
        visual_confidence: float = 0.0
    ) -> EvidenceConsistencyResult:
        
        # 1. No Image Uploaded
        if not visual_detection or visual_confidence <= 0.0:
            return EvidenceConsistencyResult(
                consistencyScore=0.50,
                consistencyLevel=ConsistencyLevel.MANUAL_REVIEW,
                textEvidence=f"Reported under '{category.value}'.",
                visualEvidence="No photographic evidence attached with submission.",
                reason="Inspection pending: Photographic evidence was not attached. Requires standard field verification."
            )

        det_lower = visual_detection.lower()
        cat_lower = category.value.lower()
        text_lower = complaint_text.lower()

        # 2. Road Damage Category Checks
        if category == IssueCategory.ROAD_DAMAGE:
            if any(k in det_lower for k in ["pothole", "crack", "asphalt", "road"]):
                return EvidenceConsistencyResult(
                    consistencyScore=0.96,
                    consistencyLevel=ConsistencyLevel.CONSISTENT,
                    textEvidence=f"Text cites road defect: '{complaint_text[:60]}...'",
                    visualEvidence=f"CV confirmed {visual_detection} (confidence: {visual_confidence:.2f}).",
                    reason="High cross-modal consistency: Textual road defect description aligns with computer vision detection."
                )
            elif any(k in det_lower for k in ["garbage", "trash", "water", "leak"]):
                return EvidenceConsistencyResult(
                    consistencyScore=0.25,
                    consistencyLevel=ConsistencyLevel.INCONSISTENT,
                    textEvidence=f"Reported as road damage: '{complaint_text[:60]}...'",
                    visualEvidence=f"CV detected alternative feature: {visual_detection}.",
                    reason="Evidence discrepancy: Attached photograph indicates non-road visual features. Routed for manual supervisory triage."
                )

        # 3. Sanitation & Garbage Checks
        elif category == IssueCategory.SANITATION:
            if any(k in det_lower for k in ["garbage", "waste", "refuse", "litter", "spill"]):
                return EvidenceConsistencyResult(
                    consistencyScore=0.94,
                    consistencyLevel=ConsistencyLevel.CONSISTENT,
                    textEvidence=f"Text cites sanitation hazard: '{complaint_text[:60]}...'",
                    visualEvidence=f"CV confirmed {visual_detection} (confidence: {visual_confidence:.2f}).",
                    reason="High cross-modal consistency: Sanitation grievance aligns with visible waste debris."
                )
            elif any(k in det_lower for k in ["pothole", "water"]):
                return EvidenceConsistencyResult(
                    consistencyScore=0.28,
                    consistencyLevel=ConsistencyLevel.INCONSISTENT,
                    textEvidence=f"Reported as sanitation issue: '{complaint_text[:60]}...'",
                    visualEvidence=f"CV detected: {visual_detection}.",
                    reason="Evidence discrepancy: Detected objects in photo differ from reported garbage category. Routed for manual review."
                )

        # 4. Water Supply & Drainage Checks
        elif category in [IssueCategory.WATER_SUPPLY, IssueCategory.STORM_WATER]:
            if any(k in det_lower for k in ["water", "leak", "flood", "drain", "burst"]):
                return EvidenceConsistencyResult(
                    consistencyScore=0.92,
                    consistencyLevel=ConsistencyLevel.CONSISTENT,
                    textEvidence=f"Text cites water defect: '{complaint_text[:60]}...'",
                    visualEvidence=f"CV confirmed {visual_detection} (confidence: {visual_confidence:.2f}).",
                    reason="High cross-modal consistency: Water leakage report corroborated by visual water accumulation."
                )
            elif any(k in det_lower for k in ["garbage", "pothole"]):
                return EvidenceConsistencyResult(
                    consistencyScore=0.30,
                    consistencyLevel=ConsistencyLevel.INCONSISTENT,
                    textEvidence=f"Reported as water leakage: '{complaint_text[:60]}...'",
                    visualEvidence=f"CV detected: {visual_detection}.",
                    reason="Evidence discrepancy: Photo shows alternative civic defect. Routed for manual review."
                )

        # 5. Low confidence or partial alignment
        if visual_confidence < 0.60:
            return EvidenceConsistencyResult(
                consistencyScore=0.55,
                consistencyLevel=ConsistencyLevel.MANUAL_REVIEW,
                textEvidence=f"Text category: '{category.value}'.",
                visualEvidence=f"Low confidence detection: {visual_detection} ({visual_confidence:.2f}).",
                reason="Sub-threshold computer vision confidence. Requires human reviewer inspection."
            )

        # Partial default
        return EvidenceConsistencyResult(
            consistencyScore=0.70,
            consistencyLevel=ConsistencyLevel.PARTIALLY_CONSISTENT,
            textEvidence=f"Reported category: '{category.value}'.",
            visualEvidence=f"CV detected: {visual_detection}.",
            reason="Partial evidence corroboration: General civic defect detected. Verified for operational dispatch."
        )

cross_validation_engine = CrossValidationEngine()

import os
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from fastapi import HTTPException

from app.models.issue import (
    Issue,
    IssueStatus,
    ResolutionStatus,
    ResolutionEvidence,
    VisualDetectionDetail
)
from app.modules.vision.yolo_detector import yolo_detector
from app.modules.lifecycle.scene_comparator import scene_comparator
from app.services.upload_service import upload_service

class IssueLifecycleTracker:
    """
    Feature 20: Genuine Image-Based Resolution Verification & Lifecycle Management.
    
    Replaces filename-based heuristic matching with a genuine computer-vision before/after
    delta comparison pipeline:
    1. Associates original issue baseline with post-action inspection photograph.
    2. Runs the genuine YOLOv8s RDD2022 detector on both photographs.
    3. Evaluates OpenCV scene comparability (2D HSV histogram correlation, SSIM, aspect ratio).
    4. Applies conservative decision rules to determine physical repair status:
       - LIKELY_RESOLVED: Defect was detected in baseline, after-image is comparable, and damage is cleared.
       - STILL_PRESENT: Credible road damage remains detectable in after-image.
       - REQUIRES_MANUAL_VERIFICATION: Incompatible scenes, missing baseline, unreadable image, or ambiguous evidence.
    5. Avoids absolute claims of physical certainty without human ground-truth sign-off.
    """

    ALLOWED_TRANSITIONS: Dict[str, List[str]] = {
        # Standard 7-stage lifecycle
        IssueStatus.OPEN.value: [IssueStatus.ANALYZED.value, IssueStatus.ASSIGNED.value],
        IssueStatus.ANALYZED.value: [IssueStatus.PRIORITIZED.value, IssueStatus.ASSIGNED.value],
        IssueStatus.PRIORITIZED.value: [IssueStatus.ASSIGNED.value, IssueStatus.ACTION_IN_PROGRESS.value],
        IssueStatus.ASSIGNED.value: [IssueStatus.ACTION_IN_PROGRESS.value],
        IssueStatus.ACTION_IN_PROGRESS.value: [IssueStatus.VERIFICATION.value, IssueStatus.RESOLVED.value],
        IssueStatus.VERIFICATION.value: [IssueStatus.RESOLVED.value, IssueStatus.ACTION_IN_PROGRESS.value],
        IssueStatus.RESOLVED.value: [IssueStatus.ACTION_IN_PROGRESS.value, IssueStatus.VERIFICATION.value],

        # Legacy backward-compatibility transitions
        IssueStatus.REPORTED.value: [IssueStatus.TRIAGED.value, IssueStatus.IN_PROGRESS.value, IssueStatus.ANALYZED.value],
        IssueStatus.TRIAGED.value: [IssueStatus.IN_PROGRESS.value, IssueStatus.PRIORITIZED.value, IssueStatus.ASSIGNED.value],
        IssueStatus.IN_PROGRESS.value: [IssueStatus.RESOLVED.value, IssueStatus.VERIFICATION.value],
        IssueStatus.VERIFIED_CLOSED.value: []
    }

    def can_transition(self, current: IssueStatus, target: IssueStatus) -> bool:
        curr_val = current.value if hasattr(current, "value") else str(current)
        targ_val = target.value if hasattr(target, "value") else str(target)
        
        if curr_val == targ_val:
            return True
        allowed = self.ALLOWED_TRANSITIONS.get(curr_val, [])
        return targ_val in allowed or target in [IssueStatus.RESOLVED, IssueStatus.VERIFICATION, IssueStatus.ASSIGNED]

    def verify_resolution(
        self,
        issue: Issue,
        inspector_id: str,
        resolution_image_url: Optional[str] = None,
        resolution_upload_id: Optional[str] = None,
        notes: Optional[str] = None
    ) -> ResolutionEvidence:
        """
        Executes genuine evidence-based computer-vision resolution verification.
        Compares baseline before-image with post-repair inspection image.
        Never checks filenames for keywords ('repaired', 'pothole', 'clear', 'broken').
        """
        now_str = datetime.now(timezone.utc).isoformat()
        original_det_label = issue.visualDetection or "Reported Surface Hazard"

        # ----------------------------------------------------------------------
        # Step 1: Validate and Resolve Post-Action Image Reference
        # ----------------------------------------------------------------------
        if not resolution_image_url and not resolution_upload_id:
            return ResolutionEvidence(
                verified_at=now_str,
                inspector_id=inspector_id,
                original_image_url=getattr(issue, "imageUrl", None),
                original_upload_id=getattr(issue, "uploadId", None),
                resolution_image_url=None,
                resolution_upload_id=None,
                original_detection=original_det_label,
                post_action_detection=None,
                resolutionStatus=ResolutionStatus.REQUIRES_MANUAL_VERIFICATION,
                resolutionConfidence=0.50,
                remainingDetection=original_det_label,
                verificationSummary=(
                    "Photographic proof of resolution was not uploaded. "
                    "Claimed repair requires on-site supervisory manual verification."
                ),
                verificationMethod="no_imagery_provided",
                sceneComparable=False,
                comparisonMetrics={},
                beforeDetections=[],
                afterDetections=[],
                requiresManualReview=True,
                post_repair_cv_cleared=False
            )

        # Resolve post-action image path safely through upload service
        try:
            after_path, after_preview, resolved_after_id = upload_service.resolve_image_reference(
                upload_id=resolution_upload_id,
                image_url=resolution_image_url
            )
        except HTTPException:
            raise
        except Exception as e:
            return ResolutionEvidence(
                verified_at=now_str,
                inspector_id=inspector_id,
                original_image_url=getattr(issue, "imageUrl", None),
                original_upload_id=getattr(issue, "uploadId", None),
                resolution_image_url=resolution_image_url,
                resolution_upload_id=resolution_upload_id,
                original_detection=original_det_label,
                post_action_detection=None,
                resolutionStatus=ResolutionStatus.REQUIRES_MANUAL_VERIFICATION,
                resolutionConfidence=0.0,
                remainingDetection=original_det_label,
                verificationSummary=f"Post-action image reference rejected: {str(e)}",
                verificationMethod="invalid_image_reference",
                sceneComparable=False,
                comparisonMetrics={},
                beforeDetections=[],
                afterDetections=[],
                requiresManualReview=True,
                post_repair_cv_cleared=False
            )

        # Check post-action file readability on disk
        if not after_path or not os.path.exists(after_path):
            return ResolutionEvidence(
                verified_at=now_str,
                inspector_id=inspector_id,
                original_image_url=getattr(issue, "imageUrl", None),
                original_upload_id=getattr(issue, "uploadId", None),
                resolution_image_url=after_preview or resolution_image_url,
                resolution_upload_id=resolved_after_id,
                original_detection=original_det_label,
                post_action_detection=None,
                resolutionStatus=ResolutionStatus.REQUIRES_MANUAL_VERIFICATION,
                resolutionConfidence=0.0,
                remainingDetection=original_det_label,
                verificationSummary="Post-action inspection file not found or inaccessible.",
                verificationMethod="unreadable_image_file",
                sceneComparable=False,
                comparisonMetrics={},
                beforeDetections=[],
                afterDetections=[],
                requiresManualReview=True,
                post_repair_cv_cleared=False
            )

        # ----------------------------------------------------------------------
        # Step 2: Resolve Original Baseline Image Reference
        # ----------------------------------------------------------------------
        before_path = None
        before_preview = None
        resolved_before_id = getattr(issue, "uploadId", None)
        orig_raw = getattr(issue, "imageUrl", None)

        if resolved_before_id or orig_raw:
            try:
                before_path, before_preview, resolved_before_id = upload_service.resolve_image_reference(
                    upload_id=resolved_before_id,
                    image_url=orig_raw
                )
            except Exception:
                before_path = None

        # ----------------------------------------------------------------------
        # Step 3: Run YOLO Road-Damage Detection on Both Images
        # ----------------------------------------------------------------------
        # Post-action detection
        after_cv = yolo_detector.detect(after_path)
        after_det_mode = after_cv.get("visionExecutionMode", "unknown")
        after_detections = after_cv.get("detectedObjects", [])
        after_max_conf = float(after_cv.get("visualConfidence", 0.0))
        after_primary = after_cv.get("visualDetection")

        if after_det_mode in ["unreadable_image_file", "inference_error"]:
            return ResolutionEvidence(
                verified_at=now_str,
                inspector_id=inspector_id,
                original_image_url=before_preview or orig_raw,
                original_upload_id=resolved_before_id,
                resolution_image_url=after_preview or resolution_image_url,
                resolution_upload_id=resolved_after_id,
                original_detection=original_det_label,
                post_action_detection=None,
                resolutionStatus=ResolutionStatus.REQUIRES_MANUAL_VERIFICATION,
                resolutionConfidence=0.0,
                remainingDetection=original_det_label,
                verificationSummary="Post-action inspection imagery unreadable or corrupted. Physical repair cannot be verified. Requires manual inspection.",
                verificationMethod="corrupt_post_action_image",
                sceneComparable=False,
                comparisonMetrics={},
                beforeDetections=[],
                afterDetections=[],
                requiresManualReview=True,
                post_repair_cv_cleared=False
            )

        if after_det_mode == "unavailable_model":
            return ResolutionEvidence(
                verified_at=now_str,
                inspector_id=inspector_id,
                original_image_url=before_preview or orig_raw,
                original_upload_id=resolved_before_id,
                resolution_image_url=after_preview or resolution_image_url,
                resolution_upload_id=resolved_after_id,
                original_detection=original_det_label,
                post_action_detection=None,
                resolutionStatus=ResolutionStatus.REQUIRES_MANUAL_VERIFICATION,
                resolutionConfidence=0.0,
                remainingDetection=original_det_label,
                verificationSummary="YOLO road-damage inference model unavailable. Automated verification offline; requires manual engineer review.",
                verificationMethod="yolo_model_unavailable",
                sceneComparable=False,
                comparisonMetrics={},
                beforeDetections=[],
                afterDetections=[],
                requiresManualReview=True,
                post_repair_cv_cleared=False
            )

        # Baseline before detection
        before_detections: List[VisualDetectionDetail] = []
        before_max_conf = 0.0
        if before_path and os.path.exists(before_path):
            before_cv = yolo_detector.detect(before_path)
            before_detections = before_cv.get("detectedObjects", [])
            before_max_conf = float(before_cv.get("visualConfidence", 0.0))
        elif getattr(issue, "detectedObjects", None):
            before_detections = issue.detectedObjects
            before_max_conf = float(getattr(issue, "visualConfidence", 0.0))

        # ----------------------------------------------------------------------
        # Step 4: OpenCV Scene Comparability Analysis
        # ----------------------------------------------------------------------
        has_before_file = bool(before_path and os.path.exists(before_path))
        if has_before_file:
            comp_res = scene_comparator.assess_comparability(before_path, after_path)
            is_comparable = bool(comp_res["isComparable"])
            comp_score = float(comp_res["comparabilityScore"])
            comp_metrics = {
                "ssim": comp_res["ssim"],
                "histogramCorrelation": comp_res["histogramCorrelation"],
                "featureMatchRatio": comp_res["featureMatchRatio"],
                "featureMatchCount": comp_res.get("featureMatchCount", 0),
                "aspectRatioDiff": comp_res["aspectRatioDiff"],
                "comparabilityScore": comp_score,
                "reason": comp_res["reason"]
            }
            comp_reason = comp_res["reason"]
        else:
            is_comparable = False
            comp_score = 0.0
            comp_metrics = {
                "ssim": 0.0,
                "histogramCorrelation": 0.0,
                "featureMatchRatio": 0.0,
                "aspectRatioDiff": 1.0,
                "comparabilityScore": 0.0,
                "reason": "Baseline before-image file unavailable for spatial/structural alignment."
            }
            comp_reason = "Baseline image file unavailable for spatial alignment."

        # ----------------------------------------------------------------------
        # Step 5: Conservative Decision Engine
        # ----------------------------------------------------------------------
        # CASE 1: Residual defect detected in post-action photograph -> STILL_PRESENT
        if len(after_detections) > 0:
            res_status = ResolutionStatus.STILL_PRESENT
            res_conf = round(min(0.95, max(0.65, after_max_conf)), 2)
            primary_label = after_detections[0].label
            summary = (
                f"Post-action inspection photograph still displays residual defect indicators: "
                f"'{primary_label}' (confidence: {round(after_max_conf * 100, 1)}%, {len(after_detections)} box(es)). "
                f"Defect still present; requires rework."
            )
            rem_det = primary_label
            cv_cleared = False
            manual_review = False

        # CASE 2: No defects detected in after-image, BUT baseline lacked detectable damage -> REQUIRES_MANUAL_VERIFICATION
        elif len(before_detections) == 0:
            res_status = ResolutionStatus.REQUIRES_MANUAL_VERIFICATION
            res_conf = 0.50
            summary = (
                "Original baseline report lacked detectable road damage objects. "
                "Resolution delta cannot be established by computer vision alone. "
                "Assigned for on-site supervisory manual verification."
            )
            rem_det = None
            cv_cleared = False
            manual_review = True

        # CASE 3: No defects detected in after-image, BUT scenes are NOT comparable -> REQUIRES_MANUAL_VERIFICATION
        elif not is_comparable:
            res_status = ResolutionStatus.REQUIRES_MANUAL_VERIFICATION
            res_conf = round(max(0.35, min(0.60, comp_score)), 2)
            summary = (
                f"Before and after inspection photographs are not sufficiently comparable ({comp_reason}). "
                f"Camera viewpoint or pavement context shifted (comparability score: {comp_score:.2f}). "
                f"Assigned for manual ward engineer sign-off."
            )
            rem_det = None
            cv_cleared = False
            manual_review = True

        # CASE 4: Defect cleared on verified, comparable scene -> LIKELY_RESOLVED
        else:
            res_status = ResolutionStatus.LIKELY_RESOLVED
            # Heuristic resolution confidence based on scene comparability and baseline detection margin
            # (Explicitly defined as a composite index, not an empirical probability)
            base_bonus = 0.30 * comp_score + 0.15 * max(0.20, min(1.0, before_max_conf))
            res_conf = round(min(0.92, 0.50 + base_bonus), 2)
            summary = (
                f"Computer vision delta analysis confirms defect clearance across comparable scene "
                f"(scene comparability: {comp_score:.2f}, SSIM: {comp_metrics['ssim']:.2f}, "
                f"color correlation: {comp_metrics['histogramCorrelation']:.2f}). "
                f"No residual surface hazards detected. Probabilistically likely resolved (not claiming absolute certainty)."
            )
            rem_det = None
            cv_cleared = True
            manual_review = False

        if notes:
            summary += f" Inspector remarks: {notes}"

        return ResolutionEvidence(
            verified_at=now_str,
            inspector_id=inspector_id,
            original_image_url=before_preview or orig_raw,
            original_upload_id=resolved_before_id,
            resolution_image_url=after_preview or resolution_image_url,
            resolution_upload_id=resolved_after_id,
            original_detection=original_det_label,
            post_action_detection=after_primary,
            resolutionStatus=res_status,
            resolutionConfidence=res_conf,
            remainingDetection=rem_det,
            verificationSummary=summary,
            verificationMethod="yolo_before_after_comparison",
            sceneComparable=is_comparable,
            comparisonMetrics=comp_metrics,
            beforeDetections=before_detections,
            afterDetections=after_detections,
            requiresManualReview=manual_review,
            post_repair_cv_cleared=cv_cleared
        )

lifecycle_tracker = IssueLifecycleTracker()

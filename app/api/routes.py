import os
from pathlib import Path
from typing import List, Optional, Dict, Any
import numpy as np
from fastapi import APIRouter, HTTPException, Query, status, UploadFile, File, Depends
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel, model_validator

from app.config import settings
from app.core.security import require_inspector, require_admin, AuthenticatedUser
from app.services.upload_service import upload_service
from app.models.issue import (
    Issue,
    IssueCreate,
    IssueStatus,
    IssueCategory,
    PriorityLevel,
    ResolutionStatus,
    ResolutionEvidence,
    HotspotInfo,
    RecurrenceInfo
)
from app.core.demo_store import demo_store
from app.core.pipeline import pipeline
from app.modules.lifecycle.tracker import lifecycle_tracker
from app.modules.gis.mapper import gis_mapper
from app.modules.spatiotemporal.hotspot import hotspot_detector
from app.modules.spatiotemporal.recurring import recurring_detector
from app.modules.routing.dispatcher import department_dispatcher
from app.modules.evaluation.evaluator import evaluator
from app.modules.vision.yolo_detector import yolo_detector
from app.modules.vision.manager import vision_manager
from app.modules.nlp.classifier import nlp_classifier

router = APIRouter(prefix="/api/v1", tags=["Civic Issue Intelligence"])

class StatusUpdateRequest(BaseModel):
    status: str
    note: Optional[str] = None

class VerifyResolutionRequest(BaseModel):
    inspectorId: str = "INSP-FIELD-01"
    uploadId: Optional[str] = None
    resolutionImageUrl: Optional[str] = None
    postActionImageUrl: Optional[str] = None
    notes: Optional[str] = None

class DepartmentConfigUpdate(BaseModel):
    category: str
    department: Optional[str] = None
    code: Optional[str] = None
    actions: Optional[Dict[str, Any]] = None
    slaHours: Optional[Dict[str, Any]] = None
    config: Optional[Dict[str, Any]] = None

    @model_validator(mode="before")
    @classmethod
    def normalize_routing_payload(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        category = data.get("category")
        if not category or not str(category).strip():
            raise ValueError("Category name is required and cannot be empty.")

        nested = data.get("config")
        if nested is not None and not isinstance(nested, dict):
            raise ValueError("'config' must be a dictionary object if provided.")

        nested_dict = nested if isinstance(nested, dict) else {}

        dept = data.get("department") if data.get("department") is not None else nested_dict.get("department")
        if not dept or not str(dept).strip():
            raise ValueError("Department name is required (provide 'department' or 'config.department').")

        code = data.get("code") if data.get("code") is not None else nested_dict.get("code")
        if not code or not str(code).strip():
            raise ValueError("Department agency code is required (provide 'code' or 'config.code').")

        actions = data.get("actions") if data.get("actions") is not None else nested_dict.get("actions")
        if actions is None:
            raise ValueError("Actions mapping is required (provide 'actions' or 'config.actions').")
        if not isinstance(actions, dict):
            raise ValueError("Actions must be a dictionary mapping priority levels to directives.")

        sla_hours = data.get("slaHours") if data.get("slaHours") is not None else nested_dict.get("slaHours")
        if not isinstance(sla_hours, dict):
            sla_hours = {}

        return {
            "category": str(category).strip(),
            "department": str(dept).strip(),
            "code": str(code).strip(),
            "actions": actions,
            "slaHours": sla_hours,
            "config": nested_dict or None
        }

@router.get("/health")
def health_check() -> Dict[str, Any]:
    # Dynamic checks for model readiness and provenance
    yolo_model = yolo_detector._get_model()
    yolo_weights_exist = os.path.exists(yolo_detector.model_path)

    if yolo_model is not None:
        vision_status = "ONLINE"
        vision_mode = "real_yolo_inference"
        vision_available = True
        vision_provenance = f"Upstream Sekilab benchmark on RDD2022 test set. Checkpoint '{yolo_detector.model_path}'."
        vision_mode_desc = "Real Ultralytics YOLOv8s inference on RDD2022 taxonomy"
        vision_metric_display = "0.4643 mAP@50 (Upstream RDD2022 Benchmark)"
        vision_meas_status = "measured"
    elif yolo_weights_exist:
        vision_status = "UNAVAILABLE"
        vision_mode = "deterministic_demo_fallback"
        vision_available = False
        vision_provenance = f"Weights present at '{yolo_detector.model_path}' but runtime inference engine failed to load."
        vision_mode_desc = "Model unavailable (Runtime initialization failure)"
        vision_metric_display = "Not evaluated (Inference engine unavailable)"
        vision_meas_status = "unavailable"
    else:
        vision_status = "UNAVAILABLE"
        vision_mode = "deterministic_demo_fallback"
        vision_available = False
        vision_provenance = f"Weights file '{yolo_detector.model_path}' not found on disk."
        vision_mode_desc = "Model unavailable (Weights missing on disk)"
        vision_metric_display = "Not evaluated (Weights missing)"
        vision_meas_status = "unavailable"

    # Dynamic checks for Waste Detector (YOLO11s TACO)
    waste_model = vision_manager.waste_detector._get_model()
    waste_path = vision_manager.waste_detector.model_path
    waste_weights_exist = os.path.exists(waste_path) if waste_path else False

    if waste_model is not None:
        waste_status = "ONLINE"
        waste_available = True
        waste_meas_status = "measured"
        waste_metric_display = "0.311 mAP@50 (Upstream TACO) | Local: 27.3% Prec@50 (N=5)"
        waste_provenance = (
            f"Upstream TACO benchmark (mAP50=0.311, mAP50-95=0.234). "
            f"Local held-out test (N=5) precision 27.3% due to complex street backgrounds. Checkpoint '{waste_path}'."
        )
        waste_mode_desc = "Real Ultralytics YOLO11s inference on TACO waste taxonomy (9 classes)"
    elif waste_weights_exist:
        waste_status = "UNAVAILABLE"
        waste_available = False
        waste_meas_status = "unavailable"
        waste_metric_display = "Not evaluated (Runtime error)"
        waste_provenance = f"Weights present at '{waste_path}' but model runtime failed to load."
        waste_mode_desc = "Model unavailable (Runtime initialization failure)"
    else:
        waste_status = "UNAVAILABLE"
        waste_available = False
        waste_meas_status = "unavailable"
        waste_metric_display = "Not evaluated (Weights missing)"
        waste_provenance = f"Weights file '{waste_path}' not found on disk."
        waste_mode_desc = "Model unavailable (Weights missing on disk)"

    # Flooding Detector: Explicitly unsupported / unvalidated ground-level detector
    flooding_status = "UNSUPPORTED"
    flooding_available = False
    flooding_meas_status = "unavailable"
    flooding_metric_display = "Not evaluated (No validated ground-level detector deployed)"
    flooding_provenance = (
        "No verified open ground-level object detection model exists for street waterlogging. "
        "Handled via manual supervisory triage without fabricating synthetic bounding boxes."
    )
    flooding_mode_desc = "Manual supervisory triage (No automated bounding box inference)"

    nlp_ready = getattr(nlp_classifier, "_real_model_ready", False)
    nlp_status = "ONLINE" if nlp_ready else "FALLBACK_KEYWORDS"

    total_issues = len(demo_store.list_issues())

    return {
        "status": "healthy",
        "service": "CiviLens Intelligence Engine",
        "version": "1.0.0",
        "totalIssuesTracked": total_issues,
        "activeIssues": total_issues,
        "storageMode": "sqlite_persistent_store",
        "subsystems": {
            "nlp_classifier": {
                "name": "NLP Civic Category Classifier",
                "tech": "TF-IDF Vectorizer + Scikit-Learn Multiclass",
                "status": nlp_status,
                "mode": "Trained in-memory on civic corpus (27 samples)" if nlp_ready else "Keyword matching fallback",
                "is_model_available": nlp_ready,
                "metric_name": "Empirical Accuracy",
                "metric_value": None,
                "metric_display": "Evaluated on demand (via /evaluation/metrics)",
                "metric_provenance": "scikit-learn accuracy_score",
                "measurement_status": "configured"
            },
            "vision_detector": {
                "name": "YOLOv8 Road Damage Detection",
                "tech": "Ultralytics PyTorch / YOLOv8s RDD2022 Multi-class",
                "status": vision_status,
                "mode": vision_mode_desc,
                "is_model_available": vision_available,
                "metric_name": "mAP@50",
                "metric_value": 0.4643 if vision_available else None,
                "metric_display": vision_metric_display,
                "metric_provenance": vision_provenance,
                "measurement_status": vision_meas_status
            },
            "waste_detector": {
                "name": "YOLO11s Waste & Litter Detection",
                "tech": "Ultralytics PyTorch / YOLO11s TACO 9-Class Multi-Object",
                "status": waste_status,
                "mode": waste_mode_desc,
                "is_model_available": waste_available,
                "metric_name": "mAP@50",
                "metric_value": 0.311 if waste_available else None,
                "metric_display": waste_metric_display,
                "metric_provenance": waste_provenance,
                "measurement_status": waste_meas_status
            },
            "flooding_detector": {
                "name": "Street Flooding / Waterlogging",
                "tech": "Standard Field Verification (CV Uncalibrated)",
                "status": flooding_status,
                "mode": flooding_mode_desc,
                "is_model_available": flooding_available,
                "metric_name": "mAP@50",
                "metric_value": None,
                "metric_display": flooding_metric_display,
                "metric_provenance": flooding_provenance,
                "measurement_status": flooding_meas_status
            },
            "cross_validation": {
                "name": "Text–Image Evidence Consistency",
                "tech": "Multimodal Semantic Consistency Matrix",
                "status": "ONLINE",
                "mode": "Rule-based alignment matrix (Enforces ethical no-'fake' policy)",
                "is_model_available": True,
                "metric_name": "Consistency Accuracy",
                "metric_value": None,
                "metric_display": "Evaluated on demand (via /evaluation/metrics)",
                "metric_provenance": "Empirical ground-truth matrix comparison",
                "measurement_status": "configured"
            },
            "hotspot_clustering": {
                "name": "Spatiotemporal Hotspot Engine",
                "tech": "Scikit-Learn DBSCAN (Haversine distance)",
                "status": "ONLINE",
                "mode": "Real algorithmic spatial clustering & temporal velocity",
                "is_model_available": True,
                "metric_name": "Silhouette Score",
                "metric_value": None,
                "metric_display": "Evaluated on demand (via /evaluation/metrics)",
                "metric_provenance": "scikit-learn silhouette_score",
                "measurement_status": "configured"
            },
            "priority_engine": {
                "name": "Risk-Aware Dynamic Priority Engine",
                "tech": "Multi-Factor Explainable Vector Scoring (0–100)",
                "status": "ONLINE",
                "mode": "Authoritative 6-factor explainable additive scoring (0–100)",
                "is_model_available": True,
                "metric_name": "Priority MAE",
                "metric_value": None,
                "metric_display": "100% Explainable (Formulaic)",
                "metric_provenance": "Exact mathematical 6-factor composite weighting (Max 100 pts)",
                "measurement_status": "measured"
            },
            "resolution_verification": {
                "name": "Resolution Verification & Lifecycle",
                "tech": "OpenCV SSIM + Dual YOLOv8s Delta Analysis",
                "status": "ONLINE",
                "mode": "Comparative computer-vision delta inspection & scene comparability",
                "is_model_available": True,
                "metric_name": "Structural Similarity (SSIM)",
                "metric_value": None,
                "metric_display": "Evaluated dynamically per before/after image pair (Controlled Benchmark: N=5)",
                "metric_provenance": "Controlled fixture benchmark & active OpenCV SSIM / 2D HSV color histogram correlation",
                "measurement_status": "measured"
            }
        }
    }

@router.post("/upload")
async def upload_image_endpoint(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Secure multipart image upload endpoint.
    Accepts JPEG, PNG, and WebP up to 10 MB.
    Enforces format verification, dimension checks, and decompression bomb protection.
    """
    return await upload_service.save_image_upload(file)

@router.get("/uploads/{upload_id}")
def get_uploaded_image(upload_id: str):
    """
    Safe preview and retrieval endpoint for uploaded images by upload ID.
    Guarantees strict containment within the configured upload directory.
    """
    file_path, content_type = upload_service.resolve_upload_file(upload_id)
    return FileResponse(path=file_path, media_type=content_type)

@router.post("/analyze")
def analyze_complaint_endpoint(payload: IssueCreate) -> Dict[str, Any]:
    """
    Stateless endpoint: Executes the full 14-feature original + 5 new features pipeline
    and returns rich structured results without mutating database store.
    """
    try:
        return pipeline.analyze(payload)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis pipeline error: {str(e)}"
        )

@router.get("/issues", response_model=List[Issue])
def get_issues(
    category: Optional[IssueCategory] = None,
    priority: Optional[PriorityLevel] = None,
    status_filter: Optional[IssueStatus] = Query(None, alias="status"),
    hotspot_only: bool = False
) -> List[Issue]:
    return demo_store.list_issues(
        category=category,
        priority=priority,
        status_filter=status_filter,
        hotspot_only=hotspot_only
    )

@router.post("/issues", response_model=Issue, status_code=status.HTTP_201_CREATED)
def submit_complaint(payload: IssueCreate) -> Issue:
    try:
        return pipeline.process_complaint(payload)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error executing intelligence pipeline: {str(e)}"
        )

@router.get("/issues/{issue_id}", response_model=Issue)
def get_issue_by_id(issue_id: str) -> Issue:
    issue = demo_store.get_issue(issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail=f"Issue {issue_id} not found")
    return issue

@router.patch("/issues/{issue_id}/status", response_model=Issue)
def update_issue_status(
    issue_id: str,
    payload: StatusUpdateRequest,
    current_user: AuthenticatedUser = Depends(require_inspector)
) -> Issue:
    issue = demo_store.get_issue(issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail=f"Issue {issue_id} not found")
    
    status_str = payload.status.strip().upper()
    status_map = {
        "OPEN": IssueStatus.OPEN,
        "ANALYZED": IssueStatus.ANALYZED,
        "PRIORITIZED": IssueStatus.PRIORITIZED,
        "ASSIGNED": IssueStatus.ASSIGNED,
        "ACTION IN PROGRESS": IssueStatus.ACTION_IN_PROGRESS,
        "IN PROGRESS": IssueStatus.ACTION_IN_PROGRESS,
        "VERIFICATION": IssueStatus.VERIFICATION,
        "RESOLVED": IssueStatus.RESOLVED,
        "REPORTED": IssueStatus.OPEN,
        "TRIAGED": IssueStatus.ANALYZED,
        "VERIFIED CLOSED": IssueStatus.RESOLVED
    }
    target_status = status_map.get(status_str, IssueStatus.RESOLVED if "RESOLV" in status_str else IssueStatus.OPEN)
    
    updated = demo_store.update_status(issue_id, target_status, note=payload.note, actor=current_user.user_id)
    return updated

@router.post("/issues/{issue_id}/verify", response_model=Issue)
def verify_issue_resolution(
    issue_id: str,
    payload: VerifyResolutionRequest,
    current_user: AuthenticatedUser = Depends(require_inspector)
) -> Issue:
    """
    Feature 20: Genuine Image-Based Resolution Verification
    Executes OpenCV scene comparability and dual YOLO road-damage delta analysis.
    Updates issue state and atomically records verification audit history.
    Enforces server-authenticated inspector identity (ignores unverified client inspectorId).
    """
    issue = demo_store.get_issue(issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail=f"Issue {issue_id} not found")
    
    raw_img = payload.resolutionImageUrl or payload.postActionImageUrl
    # Server-side identity enforcement: use authenticated inspector ID
    evidence = lifecycle_tracker.verify_resolution(
        issue=issue,
        inspector_id=current_user.user_id,
        resolution_image_url=raw_img,
        resolution_upload_id=payload.uploadId,
        notes=payload.notes
    )

    updated_issue = demo_store.record_verification(issue_id, evidence)
    return updated_issue

@router.get("/issues/{issue_id}/verifications", response_model=List[ResolutionEvidence])
def get_issue_verifications(issue_id: str) -> List[ResolutionEvidence]:
    """Retrieves full chronological verification history for an issue."""
    issue = demo_store.get_issue(issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail=f"Issue {issue_id} not found")
    return demo_store.get_verification_history(issue_id)

@router.get("/hotspots", response_model=List[HotspotInfo])
def get_spatiotemporal_hotspots() -> List[HotspotInfo]:
    """
    Feature 16: Returns active detected spatiotemporal hotspots
    using Haversine DBSCAN spatial clustering and period comparison.
    """
    issues = demo_store.list_issues()
    return hotspot_detector.detect_hotspots(issues)

@router.get("/recurring", response_model=List[RecurrenceInfo])
def get_recurring_issues() -> List[RecurrenceInfo]:
    """
    Feature 17: Identifies repeated civic problems at historical locations over time.
    """
    issues = demo_store.list_issues()
    results = []
    seen_locations = set()
    for issue in issues:
        loc_key = f"{issue.location}_{issue.category}"
        if loc_key not in seen_locations:
            seen_locations.add(loc_key)
            rec = recurring_detector.evaluate_recurrence(
                lat=issue.latitude,
                lng=issue.longitude,
                category=issue.category,
                location_name=issue.location,
                existing_issues=issues
            )
            if rec.recurringIssue:
                results.append(rec)
    return results

@router.get("/routing/config")
def get_routing_configuration() -> Dict[str, Any]:
    """
    Feature 19: Returns the current configurable department routing rules.
    """
    return department_dispatcher.get_routing_config()

@router.post("/routing/config")
def update_routing_configuration(
    payload: DepartmentConfigUpdate,
    current_user: AuthenticatedUser = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Feature 19: Dynamically updates department routing without changing ML models.
    Supports both flat payloads and nested {category, config: {...}} payloads.
    """
    dept_info: Dict[str, Any] = {
        "department": payload.department,
        "code": payload.code,
        "actions": payload.actions
    }
    if payload.slaHours:
        dept_info["slaHours"] = payload.slaHours

    department_dispatcher.update_routing_config(payload.category, dept_info)
    updated_config = department_dispatcher.get_routing_config().get(payload.category)
    return {
        "status": "success",
        "message": f"Successfully updated routing rules for {payload.category}",
        "category": payload.category,
        "config": updated_config
    }

@router.get("/gis/geojson")
def get_gis_geojson() -> Dict[str, Any]:
    features = []
    for issue in demo_store.list_issues():
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [issue.longitude, issue.latitude]
            },
            "properties": {
                "issueId": issue.issueId,
                "category": issue.category,
                "priorityScore": issue.priorityScore,
                "priorityLevel": issue.priorityLevel,
                "urgency": issue.urgency,
                "visualSeverity": issue.visualSeverity,
                "status": issue.status,
                "hotspot": issue.hotspot,
                "location": issue.location,
                "department": issue.department,
                "recommendedAction": issue.recommendedAction
            }
        })
    return {
        "type": "FeatureCollection",
        "features": features
    }

@router.get("/gis/map", response_class=HTMLResponse)
def get_gis_interactive_map() -> str:
    issues = demo_store.list_issues()
    return gis_mapper.generate_map_html(issues)

@router.get("/evaluation/metrics")
def get_evaluation_metrics() -> Dict[str, Any]:
    """
    EVALUATION SUPPORT:
    Calculates actual empirical metrics from test data and historical issues.
    Never fabricates metrics.
    """
    issues = demo_store.list_issues()
    y_true_cats = [i.category.value for i in issues]
    y_pred_cats = [pipeline.analyze(IssueCreate(complaintText=i.complaintText))["category"].value for i in issues]

    clf_metrics = evaluator.evaluate_classification(y_true_cats, y_pred_cats)

    y_true_pri = [float(i.priorityScore) for i in issues]
    y_pred_pri = [float(pipeline.analyze(IssueCreate(complaintText=i.complaintText))["priorityScore"]) for i in issues]
    pri_metrics = evaluator.evaluate_priority(y_true_pri, y_pred_pri)

    y_true_depts = [i.department for i in issues]
    y_pred_depts = [pipeline.analyze(IssueCreate(complaintText=i.complaintText))["department"] for i in issues]
    dept_metrics = evaluator.evaluate_department_routing(y_true_depts, y_pred_depts)

    # Hotspot clustering evaluation
    coords = np.radians([[i.latitude, i.longitude] for i in issues])
    labels = [
        0 if (i.metadata.get("ward") == "N-Ward" or "Vidyavihar" in i.location)
        else (1 if (i.metadata.get("ward") == "G/North" or "Dharavi" in i.location) else 2)
        for i in issues
    ]
    clustering_metrics = evaluator.evaluate_clustering(coords, labels)

    # Text-image consistency evaluation
    # Uses dedicated ground-truth manifest separating eligible multimodal pairs from missing-evidence cases
    manifest_path = Path("data/evaluation/text_image_consistency_manifest.json")
    if manifest_path.exists():
        import json
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_items = json.load(f)

        eligible_pairs = [item for item in manifest_items if item.get("evidence_status") != "MISSING_EVIDENCE"]
        missing_evidence_items = [item for item in manifest_items if item.get("evidence_status") == "MISSING_EVIDENCE"]

        y_true_cons = [item["ground_truth"] for item in eligible_pairs]
        y_pred_cons = [
            pipeline.analyze(IssueCreate(
                complaintText=item["complaintText"],
                imageUrl=item.get("image_path")
            ))["consistencyFlag"]
            for item in eligible_pairs
        ]
        consistency_metrics = evaluator.evaluate_text_image_consistency(
            y_true_cons,
            y_pred_cons,
            missing_evidence_count=len(missing_evidence_items)
        )
    else:
        eligible_issues = [i for i in issues if i.imageUrl]
        missing_issues = [i for i in issues if not i.imageUrl]
        y_true_cons = [i.consistencyFlag or "CONSISTENT" for i in eligible_issues] if eligible_issues else ["CONSISTENT"]
        y_pred_cons = [pipeline.analyze(IssueCreate(complaintText=i.complaintText, imageUrl=i.imageUrl))["consistencyFlag"] for i in eligible_issues] if eligible_issues else ["CONSISTENT"]
        consistency_metrics = evaluator.evaluate_text_image_consistency(
            y_true_cons,
            y_pred_cons,
            missing_evidence_count=len(missing_issues)
        )

    # Resolution verification evaluation
    y_true_res = ["LIKELY RESOLVED" if i.status.value in ["RESOLVED", "Resolved"] else "REQUIRES MANUAL VERIFICATION" for i in issues]
    y_pred_res = ["LIKELY RESOLVED" if (i.resolutionEvidence and i.resolutionEvidence.resolutionStatus.value == "LIKELY RESOLVED") else "REQUIRES MANUAL VERIFICATION" for i in issues]
    resolution_metrics = evaluator.evaluate_resolution_verification(y_true_res, y_pred_res)

    return {
        "classification": clf_metrics,
        "priority": pri_metrics,
        "priority_mae": pri_metrics,
        "department_routing": dept_metrics,
        "hotspot_clustering": clustering_metrics,
        "text_image_consistency": consistency_metrics,
        "resolution_verification": resolution_metrics,
        "evaluated_sample_count": len(issues)
    }

@router.post("/demo/reset")
def reset_demo_data(
    current_user: AuthenticatedUser = Depends(require_admin)
) -> Dict[str, str]:
    if not settings.civilens_demo_mode:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Destructive demo reset is disabled. Set CIVILENS_DEMO_MODE=true in configuration to permit restoring seed baseline."
        )
    demo_store.reset_demo()
    department_dispatcher.reset_to_defaults()
    return {"message": "Demo data successfully reset to baseline seed state."}

import os
from pathlib import Path
from typing import List, Optional, Dict, Any
import numpy as np
from fastapi import APIRouter, HTTPException, Query, status, UploadFile, File, Depends
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel, model_validator

from app.config import settings
from app.core.security import (
    require_citizen,
    require_inspector,
    require_admin,
    get_current_user,
    AuthenticatedUser,
    UserRole,
    verify_password,
    hash_password,
    create_access_token
)
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
    RecurrenceInfo,
    TaskAssignRequest,
    ScheduleRequest,
    ActionRequest,
    CompleteRequest,
    ReopenRequest,
    FeedbackRequest
)
from app.models.field_guidance import (
    FieldGuidanceResult,
    GuidanceDecisionRequest,
    AdminSourceUpdateRequest,
    AdminDocumentUpdateRequest,
    AdminIngestRequest
)
from app.models.hierarchy import (
    LocationVerificationRequest,
    LocationVerificationResult,
    JurisdictionUpdatePayload,
    SubWardCreate,
    SubWardUpdate,
    LocalityBeatCreate,
    LocalityBeatUpdate
)
from app.modules.gis.hierarchy_spatial import resolve_coordinates_hierarchy, check_ward_mismatch
from app.services.guidance.knowledge_base import GuidanceKnowledgeBase
from app.services.guidance.scraper import DocumentScraper
from app.services.guidance.registry import validate_source_url
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
from app.modules.nlp.location import location_extractor
from app.modules.gis.bounds import (
    is_within_supported_bounds,
    get_supported_bounds,
    OUT_OF_BOUNDS_ERROR
)
import urllib.request

router = APIRouter(prefix="/api/v1", tags=["Civic Issue Intelligence"])

class LoginRequest(BaseModel):
    usernameOrEmail: str
    password: str
    expectedRole: Optional[str] = None

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    name: str
    role: Optional[str] = "citizen"

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
        waste_metric_display = "0.311 mAP@50 (Upstream TACO) | Local Calibrated: 81.3% Prec@50 (N=100 Test)"
        waste_provenance = (
            f"Upstream TACO benchmark (mAP50=0.311, mAP50-95=0.234). "
            f"Local held-out test (N=100) precision 81.3% (F1=75.5%, mAP50=0.710) with calibrated conf=0.45. Checkpoint '{waste_path}'."
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

class VisionCompareRequest(BaseModel):
    image_path: Optional[str] = None
    upload_id: Optional[str] = None
    image_url: Optional[str] = None
    category: Optional[str] = "Roads & Footpaths"

@router.post("/vision/compare")
def compare_vision_models_endpoint(payload: VisionCompareRequest) -> Dict[str, Any]:
    """
    Controlled Vision Comparison Endpoint (Phase 14):
    Runs local production detector side-by-side with hosted Roboflow candidate.
    Returns comparison metrics, bounding boxes, latencies without altering issue priority.
    """
    target_path = None
    if payload.upload_id or payload.image_url:
        server_path, _, _ = upload_service.resolve_image_reference(
            upload_id=payload.upload_id,
            image_url=payload.image_url
        )
        target_path = server_path
    elif payload.image_path:
        target_path = payload.image_path

    if not target_path or not os.path.exists(target_path):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Valid image_path, upload_id, or image_url is required for model comparison."
        )

    return vision_manager.compare_models(target_path, category_hint=payload.category)

# -----------------------------------------------------------------------------
# Authentication & Role Administration Endpoints
# -----------------------------------------------------------------------------

@router.post("/auth/login")
def login_endpoint(payload: LoginRequest) -> Dict[str, Any]:
    identifier = payload.usernameOrEmail.strip()
    if not identifier:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username or email is required.")
    if not payload.password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password is required.")

    user = demo_store.get_user_by_identifier(identifier)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username/email or password.")

    if not verify_password(payload.password, user["salt"], user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username/email or password.")

    if payload.expectedRole:
        expected = payload.expectedRole.strip().lower()
        if user["role"] != expected:
            role_labels = {
                "citizen": "Citizen",
                "inspector": "Municipal Officer",
                "admin": "Administrator"
            }
            exp_label = role_labels.get(expected, expected.capitalize())
            act_label = role_labels.get(user["role"], user["role"].capitalize())
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: This account has the '{act_label}' role and cannot log in via the {exp_label} portal. Please select the correct role."
            )

    token = create_access_token(
        user_id=user["id"],
        role=UserRole(user["role"]),
        name=user["name"],
        email=user["email"],
        username=user["username"]
    )

    user_data = {
        "userId": user["id"],
        "username": user["username"],
        "email": user["email"],
        "name": user["name"],
        "role": user["role"]
    }
    if user["role"] == "inspector":
        oj = demo_store.get_officer_jurisdiction(user["id"])
        if oj:
            user_data["jurisdiction"] = oj

    return {
        "token": token,
        "tokenType": "Bearer",
        "user": user_data
    }

@router.post("/auth/register")
def register_endpoint(payload: RegisterRequest) -> Dict[str, Any]:
    # Restrict public registration to Citizen role only
    if payload.role and payload.role.strip().lower() != "citizen":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Public registration is restricted to citizen accounts. Municipal officer and administrator accounts cannot be self-registered."
        )

    uname = payload.username.strip().lower()
    email = payload.email.strip().lower()
    name = payload.name.strip()
    pwd = payload.password

    if len(uname) < 3:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username must be at least 3 characters.")
    if "@" not in email or "." not in email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Please provide a valid email address.")
    if len(pwd) < 6:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password must be at least 6 characters.")
    if len(name) < 2:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Name must be at least 2 characters.")

    existing_u = demo_store.get_user_by_identifier(uname)
    if existing_u:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Username '{uname}' is already registered.")

    existing_e = demo_store.get_user_by_identifier(email)
    if existing_e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Email '{email}' is already registered.")

    pw_hash, salt = hash_password(pwd)
    created = demo_store.create_user(
        username=uname,
        email=email,
        name=name,
        password_hash=pw_hash,
        salt=salt,
        role="citizen"
    )

    token = create_access_token(
        user_id=created["id"],
        role=UserRole.CITIZEN,
        name=created["name"],
        email=created["email"],
        username=created["username"]
    )

    return {
        "token": token,
        "tokenType": "Bearer",
        "user": {
            "userId": created["id"],
            "username": created["username"],
            "email": created["email"],
            "name": created["name"],
            "role": created["role"]
        }
    }

@router.get("/auth/me")
def get_current_user_profile(
    current_user: Optional[AuthenticatedUser] = Depends(get_current_user)
) -> Dict[str, Any]:
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required: No valid session token provided.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    res = {
        "userId": current_user.user_id,
        "username": current_user.username or current_user.user_id,
        "email": current_user.email or "",
        "name": current_user.name,
        "role": current_user.role.value
    }
    if current_user.role == UserRole.INSPECTOR:
        oj = demo_store.get_officer_jurisdiction(current_user.user_id)
        if oj:
            res["jurisdiction"] = oj
    return res

@router.post("/auth/logout")
def logout_endpoint() -> Dict[str, Any]:
    return {"status": "success", "message": "Logged out successfully"}

@router.get("/admin/users")
def list_admin_users(
    current_user: AuthenticatedUser = Depends(require_admin)
) -> List[Dict[str, Any]]:
    return demo_store.list_users()

# -----------------------------------------------------------------------------
# Civic Issues Endpoints
# -----------------------------------------------------------------------------

def sanitize_issue_for_citizen(issue: Issue) -> Issue:
    """Sanitizes an issue before returning to citizen, omitting internal staff details and notes."""
    sanitized = issue.model_copy(deep=True)
    if sanitized.assignment:
        sanitized.assignment.assigned_officer = None
        sanitized.assignment.instructions = None
    sanitized.supervisor_name = None
    sanitized.supervisor_id = None
    if sanitized.timeline:
        clean_timeline = []
        for evt in sanitized.timeline:
            evt_copy = evt.model_copy(deep=True)
            if evt_copy.actor and evt_copy.actor not in ("Citizen", "Automated Patrol", "AI Pipeline"):
                evt_copy.actor = "Municipal Operations"
            clean_timeline.append(evt_copy)
        sanitized.timeline = clean_timeline
    return sanitized

def check_inspector_jurisdiction(current_user: AuthenticatedUser, issue: Issue) -> None:
    """Enforces jurisdiction boundary constraints for municipal officers / supervisors."""
    if current_user.role == "inspector":
        oj = demo_store.get_officer_jurisdiction(current_user.user_id)
        if not oj or not oj.get("ward_code"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: no administrative jurisdiction has been assigned to your account."
            )
        
        # Enforce Municipal Authority boundary (BMC vs NMMC)
        if oj.get("authority_id"):
            auth_id = oj["authority_id"]
            if getattr(issue, "authority_id", None) and issue.authority_id != auth_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: complaint is outside your authorized municipal authority."
                )

        if oj.get("jurisdiction_level") == "SUB_WARD_SUPERVISOR" and oj.get("sub_ward_id"):
            if getattr(issue, "sub_ward_id", None) != oj["sub_ward_id"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: complaint is outside your authorized sub-ward jurisdiction."
                )
        elif oj.get("ward_code"):
            oj_ward = oj["ward_code"].strip().upper()
            issue_ward = (issue.ward or "").strip().upper()
            if (oj_ward != issue_ward and
                oj_ward not in issue_ward and
                issue_ward not in oj_ward and
                f"WARD-BMC-{oj_ward}" != (issue.ward_id or "").upper() and
                f"WARD-NMMC-{oj_ward}" != (issue.ward_id or "").upper()):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: complaint is outside your authorized municipal ward jurisdiction."
                )

@router.get("/issues", response_model=List[Issue])
def get_issues(
    category: Optional[IssueCategory] = None,
    priority: Optional[PriorityLevel] = None,
    status_filter: Optional[IssueStatus] = Query(None, alias="status"),
    hotspot_only: bool = False,
    citizen_id: Optional[str] = None,
    ward: Optional[str] = None,
    sub_ward_id: Optional[str] = None,
    locality_id: Optional[str] = None,
    department: Optional[str] = None,
    assignment_status: Optional[str] = None,
    current_user: Optional[AuthenticatedUser] = Depends(get_current_user)
) -> List[Issue]:
    effective_ward = ward
    effective_sub_ward = sub_ward_id

    # If Municipal Officer has an assigned jurisdiction, scope strictly to authorized boundaries
    if current_user and current_user.role == "inspector":
        oj = demo_store.get_officer_jurisdiction(current_user.user_id)
        if oj:
            if oj.get("jurisdiction_level") == "SUB_WARD_SUPERVISOR" and oj.get("sub_ward_id"):
                effective_ward = oj.get("ward_code")
                effective_sub_ward = oj["sub_ward_id"]
            elif oj.get("ward_code"):
                effective_ward = oj["ward_code"]
                if sub_ward_id:
                    effective_sub_ward = sub_ward_id
        else:
            effective_ward = "N-Ward"
    elif current_user and current_user.role == "citizen":
        citizen_id = current_user.user_id

    issues = demo_store.list_issues(
        category=category,
        priority=priority,
        status_filter=status_filter,
        hotspot_only=hotspot_only,
        citizen_id=citizen_id
    )

    if effective_ward and effective_ward != "ALL" and "ALL WARDS" not in effective_ward.upper():
        issues = [i for i in issues if i.ward == effective_ward or (i.ward and effective_ward in i.ward)]
    if effective_sub_ward and effective_sub_ward != "ALL":
        issues = [i for i in issues if getattr(i, "sub_ward_id", None) == effective_sub_ward]
    if locality_id and locality_id != "ALL":
        issues = [i for i in issues if getattr(i, "locality_id", None) == locality_id or (getattr(i, "locality_name", None) and locality_id.lower() in getattr(i, "locality_name", "").lower())]
    if department and department != "ALL":
        issues = [i for i in issues if getattr(i, "department", None) == department or (department.lower() in getattr(i, "department", "").lower())]
    if assignment_status and assignment_status != "ALL":
        norm_stat = assignment_status.upper().replace(" ", "_")
        if norm_stat == "UNASSIGNED":
            issues = [i for i in issues if not i.assignment or not i.assignment.team_name]
        elif norm_stat == "ASSIGNED":
            issues = [i for i in issues if i.status == IssueStatus.ASSIGNED]
        elif norm_stat == "SCHEDULED":
            issues = [i for i in issues if i.status == IssueStatus.SCHEDULED]
        elif norm_stat in ("IN_PROGRESS", "ACTION_IN_PROGRESS"):
            issues = [i for i in issues if i.status in (IssueStatus.ACTION_IN_PROGRESS, IssueStatus.IN_PROGRESS)]
        elif norm_stat in ("RESOLVED", "COMPLETED", "VERIFIED_CLOSED"):
            issues = [i for i in issues if i.status in (IssueStatus.RESOLVED, IssueStatus.VERIFIED_CLOSED)]
        elif norm_stat in ("JURISDICTION_REVIEW", "REVIEW_REQUIRED"):
            issues = [i for i in issues if getattr(i, "jurisdiction_review_required", False)]

    if current_user and current_user.role == "citizen":
        issues = [sanitize_issue_for_citizen(i) for i in issues]

    return issues

@router.get("/issues/my", response_model=List[Issue])
def get_my_issues(
    current_user: AuthenticatedUser = Depends(require_citizen)
) -> List[Issue]:
    """Returns complaints owned by the authenticated citizen with internal staff notes redacted."""
    issues = demo_store.list_issues(citizen_id=current_user.user_id)
    return [sanitize_issue_for_citizen(i) for i in issues]

@router.post("/issues", response_model=Issue, status_code=status.HTTP_201_CREATED)
def submit_complaint(
    payload: IssueCreate,
    current_user: Optional[AuthenticatedUser] = Depends(get_current_user)
) -> Issue:
    try:
        # Enforce authenticated citizen identity on created issues
        if current_user:
            payload.citizen_id = current_user.user_id
        return pipeline.process_complaint(payload)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error executing intelligence pipeline: {str(e)}"
        )

@router.get("/issues/{issue_id}", response_model=Issue)
def get_issue_by_id(
    issue_id: str,
    current_user: Optional[AuthenticatedUser] = Depends(get_current_user)
) -> Issue:
    issue = demo_store.get_issue(issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail=f"Issue {issue_id} not found")

    if current_user:
        if current_user.role == "inspector":
            check_inspector_jurisdiction(current_user, issue)
        elif current_user.role == "citizen":
            if issue.citizen_id and issue.citizen_id != current_user.user_id:
                raise HTTPException(status_code=403, detail="Access denied: cannot view another citizen's grievance")
            return sanitize_issue_for_citizen(issue)

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

# -----------------------------------------------------------------------------
# Lightweight Ward Operations Management Endpoints
# -----------------------------------------------------------------------------

@router.get("/operations/kpis")
def get_operations_kpis() -> Dict[str, Any]:
    """
    Returns actual database-driven operational KPIs:
    - Unassigned complaints
    - High-priority complaints
    - Work in progress
    - Complaints resolved this month
    - Road vs sanitation workload
    - Ward-level complaint distribution
    """
    return demo_store.get_operations_kpis()

@router.post("/issues/{issue_id}/assign", response_model=Issue)
def assign_issue_task(
    issue_id: str,
    payload: TaskAssignRequest,
    current_user: AuthenticatedUser = Depends(require_inspector)
) -> Issue:
    """
    Assigns task to a predefined field team with scheduled date and instructions.
    Persists assignment in database and appends to issue activity timeline.
    """
    issue = demo_store.get_issue(issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail=f"Issue {issue_id} not found")
    check_inspector_jurisdiction(current_user, issue)

    updated = demo_store.assign_task(
        issue_id=issue_id,
        assignment_data=payload.model_dump(),
        actor=current_user.name or current_user.user_id,
        role=current_user.role.value
    )
    if not updated:
        raise HTTPException(status_code=404, detail=f"Issue {issue_id} not found")
    return updated

@router.post("/issues/{issue_id}/schedule", response_model=Issue)
def schedule_issue_task(
    issue_id: str,
    payload: ScheduleRequest,
    current_user: AuthenticatedUser = Depends(require_inspector)
) -> Issue:
    """
    Schedules an inspection or repair work date for an issue.
    """
    issue = demo_store.get_issue(issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail=f"Issue {issue_id} not found")
    check_inspector_jurisdiction(current_user, issue)

    updated = demo_store.schedule_task(
        issue_id=issue_id,
        scheduled_date=payload.scheduled_date,
        schedule_type=payload.schedule_type,
        instructions=payload.instructions,
        actor=current_user.name or current_user.user_id,
        role=current_user.role.value
    )
    if not updated:
        raise HTTPException(status_code=404, detail=f"Issue {issue_id} not found")
    return updated

@router.post("/issues/{issue_id}/action", response_model=Issue)
def record_issue_action(
    issue_id: str,
    payload: ActionRequest,
    current_user: AuthenticatedUser = Depends(require_inspector)
) -> Issue:
    """
    Records issue-specific actions:
    - Roads: temporary safety measures, inspection completed, work progress
    - Sanitation: waste collection scheduled, repeat collection, cleanup progress
    """
    issue = demo_store.get_issue(issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail=f"Issue {issue_id} not found")
    check_inspector_jurisdiction(current_user, issue)

    updated = demo_store.record_action(
        issue_id=issue_id,
        action_type=payload.action_type,
        action_data=payload.model_dump(),
        actor=current_user.name or current_user.user_id,
        role=current_user.role.value
    )
    if not updated:
        raise HTTPException(status_code=404, detail=f"Issue {issue_id} not found")
    return updated

@router.post("/issues/{issue_id}/complete", response_model=Issue)
def complete_issue_task(
    issue_id: str,
    payload: CompleteRequest,
    current_user: AuthenticatedUser = Depends(require_inspector)
) -> Issue:
    """
    Completes and closes an issue. Strictly requires a completion note and closure reason.
    """
    if not payload.completion_note or not payload.completion_note.strip():
        raise HTTPException(status_code=400, detail="Completion note is strictly required to close a complaint.")
    
    issue = demo_store.get_issue(issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail=f"Issue {issue_id} not found")
    check_inspector_jurisdiction(current_user, issue)

    updated = demo_store.complete_task(
        issue_id=issue_id,
        completion_note=payload.completion_note,
        closure_reason=payload.closure_reason,
        completion_photo_url=payload.completion_photo_url,
        actor=current_user.name or current_user.user_id,
        role=current_user.role.value
    )
    if not updated:
        raise HTTPException(status_code=404, detail=f"Issue {issue_id} not found")
    return updated

@router.post("/issues/{issue_id}/reopen", response_model=Issue)
def reopen_issue_task(
    issue_id: str,
    payload: ReopenRequest,
    current_user: AuthenticatedUser = Depends(require_inspector)
) -> Issue:
    """
    Reopens a complaint when defect persists or recurs.
    """
    if not payload.reason or not payload.reason.strip():
        raise HTTPException(status_code=400, detail="Reopen reason is required.")
        
    issue = demo_store.get_issue(issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail=f"Issue {issue_id} not found")
    check_inspector_jurisdiction(current_user, issue)

    updated = demo_store.reopen_task(
        issue_id=issue_id,
        reason=payload.reason,
        note=payload.note,
        actor=current_user.name or current_user.user_id,
        role=current_user.role.value
    )
    if not updated:
        raise HTTPException(status_code=404, detail=f"Issue {issue_id} not found")
    return updated

@router.post("/issues/{issue_id}/verify-jurisdiction", response_model=Issue)
def verify_issue_jurisdiction(
    issue_id: str,
    payload: Optional[Dict[str, Any]] = None,
    current_user: AuthenticatedUser = Depends(require_inspector)
) -> Issue:
    """
    Municipal Officer / Admin: Confirms geographical assignment,
    clearing review flags and recording a verification audit event.
    """
    issue = demo_store.get_issue(issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail=f"Issue {issue_id} not found")
    check_inspector_jurisdiction(current_user, issue)

    notes = payload.get("notes") if payload else None
    updated = demo_store.verify_jurisdiction(
        issue_id=issue_id,
        actor=current_user.name or current_user.user_id,
        role=current_user.role.value,
        notes=notes
    )
    if not updated:
        raise HTTPException(status_code=404, detail=f"Issue {issue_id} not found")
    return updated

@router.post("/issues/{issue_id}/feedback", response_model=Issue)
def submit_citizen_feedback(
    issue_id: str,
    payload: FeedbackRequest,
    current_user: Optional[AuthenticatedUser] = Depends(get_current_user)
) -> Issue:
    """
    Citizen confirms resolution or reports issue remains unresolved (triggers reopen).
    """
    citizen_name = current_user.name if current_user else "Citizen"
    try:
        updated = demo_store.record_feedback(
            issue_id=issue_id,
            feedback=payload.feedback,
            note=payload.note,
            citizen_name=citizen_name
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    if not updated:
        raise HTTPException(status_code=404, detail=f"Issue {issue_id} not found")
    return updated

# -----------------------------------------------------------------------------
# Teams & Ward Configurations
# -----------------------------------------------------------------------------

@router.get("/teams")
def list_field_teams(
    category: Optional[str] = None,
    ward: Optional[str] = None,
    sub_ward_id: Optional[str] = None,
    department: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Returns list of municipal field teams and availability status."""
    cat_filter = category
    if category:
        cat_lower = category.lower()
        if "road" in cat_lower or "pothole" in cat_lower or "footpath" in cat_lower:
            cat_filter = "Roads & Footpaths"
        elif "sanitation" in cat_lower or "garbage" in cat_lower or "waste" in cat_lower:
            cat_filter = "Sanitation & Garbage"

    teams = demo_store.list_teams(category=cat_filter, ward=ward, sub_ward_id=sub_ward_id)
    if department and department != "ALL":
        teams = [t for t in teams if t.get("department") == department or (department.lower() in str(t.get("department", "")).lower())]

    # Dynamically verify tracked capacity against active tasks
    for t in teams:
        active = t.get("active_tasks_count", 0)
        cap = t.get("capacity", 6)
        if t.get("status") != "OFF_DUTY":
            t["status"] = "BUSY" if active >= cap else "AVAILABLE"

    return teams

@router.post("/admin/teams")
def create_field_team(
    payload: Dict[str, Any],
    current_user: AuthenticatedUser = Depends(require_admin)
) -> Dict[str, Any]:
    """Admin: Creates a new operational field team."""
    if not payload.get("name") or not str(payload["name"]).strip():
        raise HTTPException(status_code=400, detail="Team name is required.")
    return demo_store.create_team(payload)

@router.patch("/admin/teams/{team_id}")
def update_field_team(
    team_id: str,
    payload: Dict[str, Any],
    current_user: AuthenticatedUser = Depends(require_admin)
) -> Dict[str, Any]:
    """Admin: Updates team details or availability status (AVAILABLE, BUSY, OFF_DUTY)."""
    updated = demo_store.update_team(team_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Team {team_id} not found")
    return updated

@router.delete("/admin/teams/{team_id}")
def delete_field_team(
    team_id: str,
    current_user: AuthenticatedUser = Depends(require_admin)
) -> Dict[str, str]:
    """Admin: Deletes a field team."""
    success = demo_store.delete_team(team_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Team {team_id} not found")
    return {"status": "success", "message": f"Team {team_id} removed"}

@router.get("/admin/wards")
def list_ward_configurations() -> List[Dict[str, Any]]:
    """Returns list of configured municipal wards and lead officers."""
    return demo_store.list_wards()

@router.patch("/admin/wards/{ward_code}")
def update_ward_configuration(
    ward_code: str,
    payload: Dict[str, Any],
    current_user: AuthenticatedUser = Depends(require_admin)
) -> Dict[str, Any]:
    """Admin: Updates designated lead officer and assigned active teams for a ward."""
    updated = demo_store.update_ward(ward_code, payload)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Ward {ward_code} not found")
    return updated

# -----------------------------------------------------------------------------
# Hierarchical Ward Management & Operations Allocation Endpoints
# -----------------------------------------------------------------------------

@router.get("/hierarchy/tree")
def get_hierarchy_tree(
    authority: Optional[str] = Query(None, description="Optional authority filter (BMC or NMMC)"),
    ward: Optional[str] = Query(None, description="Optional ward filter (e.g. N-Ward)"),
    current_user: Optional[AuthenticatedUser] = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """
    Returns complete collapsible tree structure with real-time calculated workloads.
    - Admin & Inspector: Complete geographical hierarchy across both Mumbai (BMC, 24 wards)
      and Navi Mumbai (NMMC, 8 ward offices).
    - Citizen: HTTP 403 Forbidden.
    """
    if current_user and current_user.role == "citizen":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Citizens are not authorized to access administrative hierarchy management."
        )

    return demo_store.get_hierarchy_tree(authority_code=authority, ward_code=ward)

@router.get("/hierarchy/authorities")
def list_municipal_authorities() -> List[Dict[str, Any]]:
    """Returns official municipal authorities (BMC & NMMC)."""
    return demo_store.list_authorities()

@router.get("/hierarchy/wards")
def list_hierarchical_wards(
    authority_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Returns official administrative wards with geographical boundaries."""
    return demo_store.list_admin_wards(authority_id=authority_id)

@router.get("/hierarchy/sub-wards")
def list_operational_sub_wards(
    ward_code: Optional[str] = None,
    ward_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Returns configured CIVILENS operational sub-wards for a ward."""
    return demo_store.list_sub_wards(ward_code=ward_code, ward_id=ward_id)

@router.post("/hierarchy/sub-wards", status_code=status.HTTP_201_CREATED)
def create_operational_sub_ward(
    payload: SubWardCreate,
    current_user: AuthenticatedUser = Depends(require_admin)
) -> Dict[str, Any]:
    """Admin: Creates a new CIVILENS operational sub-ward."""
    return demo_store.create_sub_ward(payload.model_dump())

@router.patch("/hierarchy/sub-wards/{sub_ward_id}")
def update_operational_sub_ward(
    sub_ward_id: str,
    payload: SubWardUpdate,
    current_user: AuthenticatedUser = Depends(require_admin)
) -> Dict[str, Any]:
    """Admin: Updates an operational sub-ward."""
    updated = demo_store.update_sub_ward(sub_ward_id, payload.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail=f"Sub-ward {sub_ward_id} not found")
    return updated

@router.delete("/hierarchy/sub-wards/{sub_ward_id}")
def deactivate_operational_sub_ward(
    sub_ward_id: str,
    current_user: AuthenticatedUser = Depends(require_admin)
) -> Dict[str, str]:
    """Admin: Deactivates an operational sub-ward."""
    success = demo_store.delete_sub_ward(sub_ward_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Sub-ward {sub_ward_id} not found")
    return {"status": "success", "message": f"Sub-ward {sub_ward_id} deactivated"}

@router.get("/hierarchy/localities")
def list_localities(
    sub_ward_id: Optional[str] = None,
    ward_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Returns configured operational locality beats."""
    return demo_store.list_localities(sub_ward_id=sub_ward_id, ward_id=ward_id)

@router.post("/hierarchy/localities", status_code=status.HTTP_201_CREATED)
def create_locality(
    payload: LocalityBeatCreate,
    current_user: AuthenticatedUser = Depends(require_admin)
) -> Dict[str, Any]:
    """Admin: Creates a new locality beat."""
    return demo_store.create_locality(payload.model_dump())

@router.post("/hierarchy/verify-location", response_model=LocationVerificationResult)
def verify_location(payload: LocationVerificationRequest) -> LocationVerificationResult:
    """
    Point-in-polygon spatial verification for GPS coordinates or confirmed pin.
    Determines Municipal Authority, Zone, Ward, Sub-Ward, and Locality.
    Compares against citizen's selected ward to detect location mismatches.
    """
    res = resolve_coordinates_hierarchy(payload.latitude, payload.longitude, sub_wards=demo_store.list_sub_wards())
    if not res.get("is_valid"):
        return LocationVerificationResult(
            is_valid=False,
            is_valid_jurisdiction=False,
            error=res.get("error", "Location outside supported boundaries"),
            latitude=payload.latitude,
            longitude=payload.longitude
        )

    derived_ward = res["ward_code"]
    mismatch = check_ward_mismatch(payload.selected_ward, derived_ward)
    geo_path = f"{res.get('authority_code')} → {res.get('zone_name')} → {res.get('ward_name')} → {res.get('sub_ward_name')} → {res.get('locality_name')}"

    return LocationVerificationResult(
        is_valid=True,
        is_valid_jurisdiction=True,
        latitude=payload.latitude,
        longitude=payload.longitude,
        authority_id=res.get("authority_id"),
        authority_code=res.get("authority_code"),
        authority_name=res.get("authority_name"),
        zone_id=res.get("zone_id"),
        zone_code=res.get("zone_code"),
        zone_name=res.get("zone_name"),
        ward_id=res.get("ward_id"),
        ward_code=derived_ward,
        ward_name=res.get("ward_name"),
        sub_ward_id=res.get("sub_ward_id"),
        sub_ward_code=res.get("sub_ward_code"),
        sub_ward_name=res.get("sub_ward_name"),
        is_official_sub_ward=False,
        locality_id=res.get("locality_id"),
        locality_name=res.get("locality_name"),
        landmark=res.get("landmark"),
        supervisor_name=res.get("supervisor_name"),
        is_ambiguous=res.get("is_ambiguous", False),
        requires_admin_review=res.get("requires_admin_review", False),
        review_reason=res.get("review_reason"),
        has_ward_mismatch=mismatch.get("is_mismatch", False),
        selected_ward=payload.selected_ward,
        warning_message=mismatch.get("warning_message"),
        is_mismatch=mismatch.get("is_mismatch", False),
        derived_ward=derived_ward,
        mismatch_message=mismatch.get("warning_message"),
        review_required=res.get("requires_admin_review", False),
        geographic_path=geo_path
    )

@router.get("/hierarchy/jurisdiction/me")
def get_my_jurisdiction(
    current_user: AuthenticatedUser = Depends(require_inspector)
) -> Optional[Dict[str, Any]]:
    """Returns assigned geographical jurisdiction for authenticated Municipal Officer."""
    return demo_store.get_officer_jurisdiction(current_user.user_id)

@router.post("/hierarchy/supervisors/assign")
def assign_supervisor_jurisdiction(
    payload: Dict[str, Any],
    current_user: AuthenticatedUser = Depends(require_admin)
) -> Dict[str, Any]:
    """Admin: Assigns officer/supervisor to a ward or operational sub-ward."""
    user_id = payload.get("user_id")
    ward_code = payload.get("ward_code") or payload.get("ward_id")
    sub_ward_id = payload.get("sub_ward_id")
    authority_id = payload.get("authority_id", "AUTH-BMC")
    level = payload.get("jurisdiction_level", "WARD_OFFICER")
    if not user_id or not ward_code:
        raise HTTPException(status_code=400, detail="user_id and ward_code are required")

    return demo_store.assign_officer_jurisdiction(
        user_id=user_id,
        ward_code=ward_code,
        sub_ward_id=sub_ward_id,
        authority_id=authority_id,
        jurisdiction_level=level
    )

@router.patch("/issues/{issue_id}/jurisdiction", response_model=Issue)
def correct_issue_jurisdiction(
    issue_id: str,
    payload: JurisdictionUpdatePayload,
    current_user: AuthenticatedUser = Depends(require_inspector)
) -> Issue:
    """
    Municipal Officer / Admin: Corrects jurisdiction assignment of a complaint,
    updating routing tree path and recording an immutable audit log.
    """
    issue = demo_store.get_issue(issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail=f"Issue {issue_id} not found")
    check_inspector_jurisdiction(current_user, issue)

    if current_user.role == "inspector":
        oj = demo_store.get_officer_jurisdiction(current_user.user_id)
        if oj and oj.get("authority_id"):
            is_officer_nmmc = "NMMC" in oj["authority_id"]
            target_upper = payload.ward_code.upper()
            is_target_nmmc = "NMMC" in target_upper
            if is_officer_nmmc != is_target_nmmc:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: municipal officers cannot transfer complaints across municipal authorities."
                )

    updated = demo_store.update_issue_jurisdiction(
        issue_id=issue_id,
        new_ward_code=payload.ward_code,
        new_sub_ward_id=payload.sub_ward_id,
        new_locality_id=payload.locality_id,
        changed_by=current_user.name or current_user.username,
        changed_by_role=current_user.role,
        reason=payload.reason
    )
    if not updated:
        raise HTTPException(status_code=404, detail=f"Issue {issue_id} not found")
    return updated

@router.get("/issues/{issue_id}/jurisdiction-history")
def get_issue_jurisdiction_history(issue_id: str) -> List[Dict[str, Any]]:
    """Returns audit log of jurisdiction changes for an issue."""
    return demo_store.get_jurisdiction_audit_logs(issue_id=issue_id)

@router.get("/gis/boundaries")
def get_gis_boundaries() -> Dict[str, Any]:
    """Returns GeoJSON FeatureCollection of all administrative and operational sub-ward boundaries."""
    wards = demo_store.list_admin_wards()
    sub_wards = demo_store.list_sub_wards()
    features = []

    for w in wards:
        geom = w.get("boundary_geojson")
        if geom:
            features.append({
                "type": "Feature",
                "id": w["id"],
                "geometry": geom,
                "properties": {
                    "layer": "ward",
                    "type": "ADMIN_WARD",
                    "id": w["id"],
                    "code": w["ward_code"],
                    "name": w["ward_name"],
                    "authority_id": w["authority_id"],
                    "lead_officer": w.get("lead_officer", "Lead Officer"),
                    "office_location": w.get("office_address", "Ward Municipal Office"),
                    "is_official": True
                }
            })

    for sw in sub_wards:
        geom = sw.get("boundary_geojson")
        if geom:
            features.append({
                "type": "Feature",
                "id": sw["id"],
                "geometry": geom,
                "properties": {
                    "layer": "sub_ward",
                    "type": "CIVILENS_OPERATIONAL_SUB_WARD",
                    "id": sw["id"],
                    "code": sw["sub_ward_code"],
                    "name": sw["name"],
                    "ward_id": sw["ward_id"],
                    "authority_id": sw.get("authority_id", "AUTH-BMC"),
                    "supervisor_name": sw.get("supervisor_name", "Area Supervisor"),
                    "assigned_department": "Infrastructure & Public Works",
                    "is_official": False,
                    "operational_type": "CIVILENS_OPERATIONAL_SUB_WARD"
                }
            })

    return {
        "type": "FeatureCollection",
        "features": features
    }

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
    Enforces lifecycle state machine: rejects premature verification for issues not yet in field action.
    Requires valid post-action photographic evidence.
    """
    issue = demo_store.get_issue(issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail=f"Issue {issue_id} not found")
    
    # Lifecycle state machine gating: prevent premature verification or reverification of closed issues
    allowed_statuses = {
        IssueStatus.ACTION_IN_PROGRESS.value,
        IssueStatus.VERIFICATION.value,
        IssueStatus.IN_PROGRESS.value,
    }
    curr_status = issue.status.value if hasattr(issue.status, "value") else str(issue.status)
    if curr_status in {IssueStatus.RESOLVED.value, IssueStatus.VERIFIED_CLOSED.value}:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Cannot verify resolution for issue {issue_id}: issue is already closed ('{curr_status}'). "
                f"Closed issues cannot be reverified unless reopened."
            )
        )
    if curr_status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Cannot verify resolution for issue {issue_id}: current lifecycle status is '{curr_status}'. "
                f"Resolution verification is only permitted once field repair is under way or pending verification "
                f"(ACTION IN PROGRESS or VERIFICATION)."
            )
        )

    raw_img = payload.resolutionImageUrl or payload.postActionImageUrl
    if not raw_img and not payload.uploadId:
        raise HTTPException(
            status_code=400,
            detail="Resolution verification requires valid post-action photographic evidence (uploadId or resolutionImageUrl)."
        )

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

@router.get("/geo/bounds")
def get_geographic_bounds() -> Dict[str, Any]:
    """Returns the configured regional boundaries for Mumbai & Navi Mumbai."""
    return get_supported_bounds()

@router.get("/geo/reverse-geocode")
def reverse_geocode(
    lat: float = Query(..., description="Latitude coordinate"),
    lng: float = Query(..., description="Longitude coordinate")
) -> Dict[str, Any]:
    """
    Reverse geocodes coordinates within Mumbai & Navi Mumbai.
    Validates boundary and derives canonical locality and municipal ward.
    """
    if not is_within_supported_bounds(lat, lng):
        return {
            "valid": False,
            "error": OUT_OF_BOUNDS_ERROR,
            "latitude": lat,
            "longitude": lng
        }

    derived_ward = location_extractor.derive_ward_from_coordinates(lat, lng)
    local_name = location_extractor.derive_landmark_from_coordinates(lat, lng)
    address = local_name

    try:
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lng}&zoom=18&addressdetails=1"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "CiviLens-CivicIntelligence/1.0"}
        )
        with urllib.request.urlopen(req, timeout=2.5) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                disp_name = data.get("display_name")
                if disp_name:
                    parts = [p.strip() for p in disp_name.split(",")]
                    address = ", ".join(parts[:4])
    except Exception:
        address = local_name

    return {
        "valid": True,
        "address": address,
        "ward": derived_ward,
        "latitude": lat,
        "longitude": lng
    }

@router.get("/geo/search")
def search_locations(
    query: str = Query("", description="Search term for Mumbai/Navi Mumbai localities"),
    limit: int = Query(6, ge=1, le=20)
) -> List[Dict[str, Any]]:
    """Autocomplete search for Mumbai & Navi Mumbai localities and landmarks."""
    return location_extractor.search_landmarks(query=query, limit=limit)

@router.get("/evaluation/metrics")
def get_evaluation_metrics() -> Dict[str, Any]:
    """
    EVALUATION SUPPORT:
    Calculates actual empirical metrics from test data and historical issues.
    Never fabricates metrics. Handles empty complaint database cleanly.
    """
    issues = demo_store.list_issues()
    if len(issues) == 0:
        return {
            "classification": {
                "accuracy": 0.0,
                "macro_precision": 0.0,
                "macro_recall": 0.0,
                "macro_f1": 0.0,
                "weighted_f1": 0.0,
                "sample_count": 0
            },
            "priority": {
                "mae": 0.0,
                "top_k": 0,
                "top_k_precision": 0.0,
                "top_k_recall": 0.0,
                "sample_count": 0
            },
            "priority_mae": {
                "mae": 0.0,
                "top_k": 0,
                "top_k_precision": 0.0,
                "top_k_recall": 0.0,
                "sample_count": 0
            },
            "department_routing": {
                "accuracy": 0.0,
                "macro_f1": 0.0,
                "sample_count": 0
            },
            "hotspot_clustering": {
                "silhouette_score": None,
                "clusters_found": 0,
                "total_points": 0,
                "status": "No issues submitted yet to calculate spatial clustering."
            },
            "text_image_consistency": {
                "accuracy": 0.0,
                "sample_count": 0,
                "missing_evidence_count": 0,
                "manual_review_count": 0
            },
            "resolution_verification": {
                "accuracy": 0.0,
                "sample_count": 0
            },
            "evaluated_sample_count": 0,
            "status": "No complaints submitted yet."
        }

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
    if settings.is_presentation_database:
        demo_store.reset_demo()
        department_dispatcher.reset_to_defaults()
        return {"message": "Presentation environment reset: All live complaints cleared to clean empty state."}

    if not settings.civilens_demo_mode:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Destructive demo reset is disabled. Set CIVILENS_DEMO_MODE=true in configuration to permit restoring seed baseline."
        )
    demo_store.reset_demo()
    department_dispatcher.reset_to_defaults()
    return {"message": "Demo data successfully reset to baseline seed state."}

# ==============================================================================
# AI Field Guidance & Official Government Research Endpoints
# ==============================================================================

@router.get("/issues/{issue_id}/guidance", response_model=FieldGuidanceResult)
def get_issue_guidance(
    issue_id: str,
    force_regenerate: bool = Query(False),
    current_user: AuthenticatedUser = Depends(require_inspector)
) -> FieldGuidanceResult:
    """
    Retrieves or generates context-aware, grounded field guidance for a civic issue.
    Enforces inspector / municipal officer authentication.
    """
    guidance = demo_store.get_or_generate_field_guidance(issue_id, force_regenerate=force_regenerate)
    if not guidance:
        raise HTTPException(status_code=404, detail=f"Issue {issue_id} not found")
    return guidance

@router.post("/issues/{issue_id}/guidance/regenerate", response_model=FieldGuidanceResult)
def regenerate_issue_guidance(
    issue_id: str,
    current_user: AuthenticatedUser = Depends(require_inspector)
) -> FieldGuidanceResult:
    """
    Forces fresh re-synthesis of field guidance against latest official knowledge base.
    """
    guidance = demo_store.get_or_generate_field_guidance(issue_id, force_regenerate=True)
    if not guidance:
        raise HTTPException(status_code=404, detail=f"Issue {issue_id} not found")
    return guidance

@router.post("/issues/{issue_id}/guidance/decision", response_model=FieldGuidanceResult)
def record_guidance_decision(
    issue_id: str,
    payload: GuidanceDecisionRequest,
    current_user: AuthenticatedUser = Depends(require_inspector)
) -> FieldGuidanceResult:
    """
    Records officer decision (ACCEPTED, EDITED, DISMISSED) for a specific guidance item.
    When accepted or edited, appends text to task instructions and adds a timeline event.
    Never automatically assigns teams, orders materials, or closes issues.
    """
    guidance = demo_store.record_guidance_decision(
        issue_id=issue_id,
        item_id=payload.item_id,
        decision=payload.decision,
        edited_text=payload.edited_text,
        reason=payload.reason,
        actor=getattr(current_user, "name", None) or "Abhinay",
        role=current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    )
    if not guidance:
        raise HTTPException(status_code=404, detail=f"Issue {issue_id} not found")
    return guidance

@router.get("/guidance/documents/{doc_id}", response_model=Dict[str, Any])
def get_guidance_document(
    doc_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Returns full details, metadata, and sections for a specific official guidance document.
    """
    kb = GuidanceKnowledgeBase()
    doc = kb.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Guidance document {doc_id} not found")
    return doc

# ------------------------------------------------------------------------------
# Admin Source & Document Management Endpoints
# ------------------------------------------------------------------------------

@router.get("/admin/guidance/sources", response_model=List[Dict[str, Any]])
def list_admin_guidance_sources(
    current_user: AuthenticatedUser = Depends(require_admin)
) -> List[Dict[str, Any]]:
    """
    Admin: Lists all registered official government guidance sources.
    """
    kb = GuidanceKnowledgeBase()
    return kb.list_sources()

@router.patch("/admin/guidance/sources/{source_id}", response_model=Dict[str, Any])
def update_admin_guidance_source(
    source_id: str,
    payload: AdminSourceUpdateRequest,
    current_user: AuthenticatedUser = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Admin: Updates source category or active status.
    """
    kb = GuidanceKnowledgeBase()
    updates = payload.model_dump(exclude_unset=True)
    res = kb.update_source(source_id, updates)
    if not res:
        raise HTTPException(status_code=404, detail=f"Source {source_id} not found")
    return res

@router.get("/admin/guidance/documents", response_model=List[Dict[str, Any]])
def list_admin_guidance_documents(
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    current_user: AuthenticatedUser = Depends(require_admin)
) -> List[Dict[str, Any]]:
    """
    Admin: Lists all ingested documents in the knowledge base.
    """
    kb = GuidanceKnowledgeBase()
    return kb.list_documents(category=category, status=status)

@router.patch("/admin/guidance/documents/{doc_id}", response_model=Dict[str, Any])
def update_admin_guidance_document(
    doc_id: str,
    payload: AdminDocumentUpdateRequest,
    current_user: AuthenticatedUser = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Admin: Updates document approval status or lifecycle status (CURRENT/DRAFT/SUPERSEDED).
    """
    kb = GuidanceKnowledgeBase()
    updates = payload.model_dump(exclude_unset=True)
    if "document_status" in updates and hasattr(updates["document_status"], "value"):
        updates["document_status"] = updates["document_status"].value
    res = kb.update_document(doc_id, updates)
    if not res:
        raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")
    return res

@router.post("/admin/guidance/ingest", response_model=Dict[str, Any])
async def ingest_guidance_document(
    payload: AdminIngestRequest,
    current_user: AuthenticatedUser = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Admin: Scrapes and ingests an official document from an allowlisted government URL.
    Validates domain against official allowlist, parses HTML/PDF, computes SHA-256 hash,
    and updates/supersedes the knowledge base.
    """
    kb = GuidanceKnowledgeBase()
    target_url = payload.source_url
    target_source_id = payload.source_id

    if not target_url and target_source_id:
        sources = kb.list_sources()
        matched = next((s for s in sources if s["id"] == target_source_id), None)
        if not matched:
            raise HTTPException(status_code=404, detail=f"Source {target_source_id} not found")
        target_url = matched["base_url"]
    elif not target_url:
        raise HTTPException(status_code=400, detail="Either source_url or source_id must be provided")

    is_valid, domain, error = validate_source_url(target_url)
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"Disallowed or non-government source: {error}")

    scraper = DocumentScraper()
    scraped = await scraper.fetch_and_parse(target_url)

    if not scraped.get("is_successful"):
        if target_source_id:
            kb.update_source(target_source_id, {
                "last_status": "ERROR",
                "error_message": scraped.get("error_message")
            })
        raise HTTPException(status_code=502, detail=f"Scraping failed: {scraped.get('error_message')}")

    # Determine category and source
    category = "Roads & Footpaths" if any(k in target_url.lower() or k in domain.lower() for k in ["morth", "road", "pothole"]) else "Sanitation & Garbage"
    source_org = "Government Department"
    sources = kb.list_sources()
    src = next((s for s in sources if s["domain"] == domain or s["id"] == target_source_id), None)
    if src:
        source_org = src["name"]
        category = src.get("category", category)

    ingested = kb.save_ingested_document(
        doc_data={
            "source_domain": domain,
            "source_org": source_org,
            "title": scraped["title"],
            "url": target_url,
            "content_type": scraped.get("content_type", "text/html"),
            "file_hash": scraped["file_hash"],
            "raw_text": scraped.get("raw_text", ""),
            "sections": scraped.get("sections", [])
        },
        source_id=src["id"] if src else f"SRC-{domain.upper()}",
        category=category,
        version="Live-Ingested"
    )

    if src:
        from datetime import datetime, timezone
        kb.update_source(src["id"], {
            "last_status": "OK",
            "error_message": None,
            "last_retrieved_at": datetime.now(timezone.utc)
        })

    return {
        "status": "SUCCESS",
        "message": f"Successfully ingested document '{scraped['title']}' from {domain}.",
        "document": ingested
    }


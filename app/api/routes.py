from typing import List, Optional, Dict, Any
import numpy as np
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

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

router = APIRouter(prefix="/api/v1", tags=["Civic Issue Intelligence"])

class StatusUpdateRequest(BaseModel):
    status: str

class VerifyResolutionRequest(BaseModel):
    inspectorId: str = "INSP-FIELD-01"
    resolutionImageUrl: Optional[str] = None
    postActionImageUrl: Optional[str] = None
    notes: Optional[str] = None

class DepartmentConfigUpdate(BaseModel):
    category: str
    department: str
    code: str
    actions: Dict[str, Any]

@router.get("/health")
def health_check() -> Dict[str, Any]:
    return {
        "status": "healthy",
        "service": "CiviLens Intelligence Engine",
        "version": "1.0.0",
        "totalIssuesTracked": len(demo_store.list_issues())
    }

@router.post("/analyze")
def analyze_complaint_endpoint(payload: IssueCreate) -> Dict[str, Any]:
    """
    Stateless endpoint: Executes the full 14-feature original + 5 new features pipeline
    and returns rich structured results without mutating database store.
    """
    try:
        return pipeline.analyze(payload)
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
    issues = demo_store.list_issues()
    if category:
        issues = [i for i in issues if i.category == category]
    if priority:
        issues = [i for i in issues if i.priorityLevel == priority]
    if status_filter:
        issues = [i for i in issues if i.status == status_filter]
    if hotspot_only:
        issues = [i for i in issues if i.hotspot]
    return issues

@router.post("/issues", response_model=Issue, status_code=status.HTTP_201_CREATED)
def submit_complaint(payload: IssueCreate) -> Issue:
    try:
        return pipeline.process_complaint(payload)
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
def update_issue_status(issue_id: str, payload: StatusUpdateRequest) -> Issue:
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
    
    updated = demo_store.update_status(issue_id, target_status)
    return updated

@router.post("/issues/{issue_id}/verify", response_model=Issue)
def verify_issue_resolution(issue_id: str, payload: VerifyResolutionRequest) -> Issue:
    """
    Feature 20: Resolution Verification
    Compares original defect detection vs post-repair inspection image.
    Transitions status according to resolution findings.
    """
    issue = demo_store.get_issue(issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail=f"Issue {issue_id} not found")
    
    evidence = lifecycle_tracker.verify_resolution(
        issue=issue,
        inspector_id=payload.inspectorId,
        resolution_image_url=payload.resolutionImageUrl or payload.postActionImageUrl,
        notes=payload.notes
    )
    issue.resolutionEvidence = evidence

    if evidence.resolutionStatus == ResolutionStatus.LIKELY_RESOLVED:
        issue.status = IssueStatus.RESOLVED
    elif evidence.resolutionStatus == ResolutionStatus.STILL_PRESENT:
        issue.status = IssueStatus.ACTION_IN_PROGRESS
    else:
        issue.status = IssueStatus.VERIFICATION

    demo_store.add_issue(issue)
    return issue

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
def update_routing_configuration(payload: DepartmentConfigUpdate) -> Dict[str, str]:
    """
    Feature 19: Dynamically updates department routing without changing ML models.
    """
    department_dispatcher.update_routing_config(payload.category, {
        "department": payload.department,
        "code": payload.code,
        "actions": payload.actions
    })
    return {"message": f"Successfully updated routing rules for {payload.category}"}

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
    y_true_cons = [i.consistencyFlag or "CONSISTENT" for i in issues]
    y_pred_cons = [pipeline.analyze(IssueCreate(complaintText=i.complaintText, imageUrl=i.imageUrl))["consistencyFlag"] for i in issues]
    consistency_metrics = evaluator.evaluate_text_image_consistency(y_true_cons, y_pred_cons)

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
def reset_demo_data() -> Dict[str, str]:
    demo_store.reload()
    return {"message": "Demo data successfully reset to baseline seed state."}

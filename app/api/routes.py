from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from app.models.issue import (
    Issue,
    IssueCreate,
    IssueStatus,
    IssueCategory,
    PriorityLevel,
    ResolutionEvidence
)
from app.core.demo_store import demo_store
from app.core.pipeline import pipeline
from app.modules.lifecycle.tracker import lifecycle_tracker
from app.modules.gis.mapper import gis_mapper

router = APIRouter(prefix="/api/v1", tags=["Civic Issue Intelligence"])

class StatusUpdateRequest(BaseModel):
    status: IssueStatus

class VerifyResolutionRequest(BaseModel):
    inspectorId: str
    resolutionImageUrl: Optional[str] = None
    notes: Optional[str] = None

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
    Stateless endpoint: Executes the full 14-feature analysis pipeline
    and returns rich structured results without writing to persistent store.
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
    
    if not lifecycle_tracker.can_transition(issue.status, payload.status):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid transition from {issue.status} to {payload.status}"
        )
    
    updated = demo_store.update_status(issue_id, payload.status)
    return updated

@router.post("/issues/{issue_id}/verify", response_model=Issue)
def verify_issue_resolution(issue_id: str, payload: VerifyResolutionRequest) -> Issue:
    issue = demo_store.get_issue(issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail=f"Issue {issue_id} not found")
    
    evidence = lifecycle_tracker.verify_resolution(
        issue=issue,
        inspector_id=payload.inspectorId,
        resolution_image_url=payload.resolutionImageUrl,
        notes=payload.notes
    )
    issue.resolutionEvidence = evidence
    issue.status = IssueStatus.VERIFIED_CLOSED
    demo_store.add_issue(issue)
    return issue

@router.get("/gis/geojson")
def get_gis_geojson() -> Dict[str, Any]:
    """
    Returns standard GeoJSON FeatureCollection for direct Leaflet/MapLibre GIS mapping.
    """
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
    """
    Renders and serves an interactive Folium map visualization.
    """
    issues = demo_store.list_issues()
    return gis_mapper.generate_map_html(issues)

@router.post("/demo/reset")
def reset_demo_data() -> Dict[str, str]:
    demo_store.reload()
    return {"message": "Demo data successfully reset to baseline seed state."}

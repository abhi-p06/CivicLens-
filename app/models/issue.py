from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class IssueCategory(str, Enum):
    ROAD_DAMAGE = "Roads & Footpaths"
    SANITATION = "Sanitation & Garbage"
    WATER_SUPPLY = "Water Supply & Drainage"
    ELECTRICAL = "Electricity & Streetlights"
    TRAFFIC_SAFETY = "Traffic & Public Safety"
    UNSPECIFIED = "General Civic Issue"

class PriorityLevel(str, Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"

class IssueStatus(str, Enum):
    REPORTED = "Reported"
    TRIAGED = "Triaged"
    IN_PROGRESS = "In Progress"
    RESOLVED = "Resolved"
    VERIFIED_CLOSED = "Verified Closed"
    REOPENED = "Reopened"

class PriorityFactors(BaseModel):
    urgency_weight: float = 0.30
    visual_weight: float = 0.25
    frequency_weight: float = 0.20
    recency_weight: float = 0.15
    exposure_weight: float = 0.10
    
    urgency_score: float = Field(0.0, ge=0.0, le=1.0)
    visual_score: float = Field(0.0, ge=0.0, le=1.0)
    frequency_score: float = Field(0.0, ge=0.0, le=1.0)
    recency_score: float = Field(0.0, ge=0.0, le=1.0)
    exposure_score: float = Field(0.0, ge=0.0, le=1.0)
    composite_score: float = Field(0.0, ge=0.0, le=1.0)

class VisualDetectionDetail(BaseModel):
    label: str
    confidence: float
    bbox: Optional[List[float]] = None  # [ymin, xmin, ymax, xmax] normalized

class IssueCreate(BaseModel):
    complaintText: str = Field(..., description="Citizen complaint text")
    location: Optional[str] = Field(None, description="Landmark or locality name")
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    imageUrl: Optional[str] = None
    source: str = "citizen_portal"

class ResolutionEvidence(BaseModel):
    verified_at: Optional[str] = None
    inspector_id: Optional[str] = None
    resolution_image_url: Optional[str] = None
    inspection_notes: Optional[str] = None
    post_repair_cv_cleared: bool = False

class Issue(BaseModel):
    issueId: str
    complaintText: str
    category: IssueCategory = IssueCategory.UNSPECIFIED
    urgency: float = Field(0.0, ge=0.0, le=1.0, description="Text-derived urgency score")
    severity: float = Field(0.0, ge=0.0, le=1.0, description="Overall severity index")
    location: str
    latitude: float
    longitude: float
    timestamp: str
    
    # Deduplication & Grouping
    duplicateGroup: Optional[str] = None
    isDuplicate: bool = False
    nearDuplicateCount: int = 0
    
    # Computer Vision Details
    visualDetection: Optional[str] = None
    visualConfidence: float = 0.0
    visualSeverity: float = Field(0.0, ge=0.0, le=1.0)
    detectedObjects: List[VisualDetectionDetail] = []
    
    # Cross-Modal Cross-Validation
    evidenceConsistency: float = Field(0.0, ge=0.0, le=1.0, description="Text-Image consistency alignment")
    consistencyFlag: str = "Unverified"  # "Consistent", "Contradictory", "No Image"
    
    # Spatiotemporal Intelligence
    recurrence: int = Field(1, description="Times reported in this 200m zone in past 90 days")
    hotspot: bool = Field(False, description="Flagged as part of high-density spatial cluster")
    hotspotClusterId: Optional[str] = None
    
    # Priority Advisory
    priorityScore: float = Field(0.0, ge=0.0, le=1.0)
    priorityLevel: PriorityLevel = PriorityLevel.LOW
    priorityBreakdown: Optional[PriorityFactors] = None
    
    # Governance & Routing
    department: str = "Municipal Administration"
    recommendedAction: str = "Inspect and triage"
    slaHours: int = 72
    
    # Lifecycle Tracking
    status: IssueStatus = IssueStatus.REPORTED
    resolutionEvidence: Optional[ResolutionEvidence] = None
    
    metadata: Dict[str, Any] = {}

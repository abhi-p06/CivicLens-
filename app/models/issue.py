from enum import Enum
from typing import Optional, List, Dict, Any, Tuple
from pydantic import BaseModel, Field
from datetime import datetime

class IssueCategory(str, Enum):
    ROAD_DAMAGE = "Roads & Footpaths"
    SANITATION = "Sanitation & Garbage"
    WATER_SUPPLY = "Water Supply & Drainage"
    ELECTRICAL = "Electricity & Streetlights"
    TRAFFIC_SAFETY = "Traffic & Public Safety"
    STORM_WATER = "Storm Water & Drainage"
    UNSPECIFIED = "General Civic Issue"

class PriorityLevel(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class IssueStatus(str, Enum):
    # Standard 7-stage lifecycle
    OPEN = "OPEN"
    ANALYZED = "ANALYZED"
    PRIORITIZED = "PRIORITIZED"
    ASSIGNED = "ASSIGNED"
    ACTION_IN_PROGRESS = "ACTION IN PROGRESS"
    VERIFICATION = "VERIFICATION"
    RESOLVED = "RESOLVED"
    
    # Backwards compatibility aliases
    REPORTED = "Reported"
    TRIAGED = "Triaged"
    IN_PROGRESS = "In Progress"
    VERIFIED_CLOSED = "Verified Closed"
    REOPENED = "Reopened"

class ConsistencyLevel(str, Enum):
    CONSISTENT = "CONSISTENT"
    PARTIALLY_CONSISTENT = "PARTIALLY CONSISTENT"
    INCONSISTENT = "INCONSISTENT"
    MANUAL_REVIEW = "MANUAL REVIEW"

class ResolutionStatus(str, Enum):
    LIKELY_RESOLVED = "LIKELY RESOLVED"
    STILL_PRESENT = "STILL PRESENT"
    REQUIRES_MANUAL_VERIFICATION = "REQUIRES MANUAL VERIFICATION"

class HotspotLevel(str, Enum):
    SEVERE = "SEVERE"
    HIGH = "HIGH"
    MODERATE = "MODERATE"
    LOW = "LOW"

class RecurrenceTrend(str, Enum):
    INCREASING = "INCREASING"
    STABLE = "STABLE"
    DECREASING = "DECREASING"

class DynamicPriorityBreakdown(BaseModel):
    """
    Authoritative 6-Component Explainable Additive Scoring Model (Total: 0–100 pts):
    1. Urgency:              Max 20 pts (Immediate danger to life, safety, or transit)
    2. Textual Severity:     Max 20 pts (Physical disruption magnitude from complaint text)
    3. Visual Severity:      Max 20 pts (CV damage area modulated by detector confidence)
    4. Related Reports:      Max 15 pts (Public friction amplification from near-duplicates)
    5. Recency:              Max 10 pts (Hours elapsed since report submission)
    6. Location Risk:        Max 15 pts (Corridor vulnerability, municipal hotspot, recurrence)
    -------------------------------------------------------------------------------------
    Total Score:             0–100 pts = U + T + V + F + R + L

    Note on Legacy Weights:
    The legacy `*_weight` fields below (0.30, 0.25, 0.20, 0.15, 0.10) reflect an early
    5-factor prototype. They are deprecated and retained solely for backward compatibility.
    The active and authoritative scoring logic implemented across CiviLens is the 6-factor additive model.
    """
    urgency_points: float = Field(..., description="Max 20 pts: Based on immediate hazard cues")
    text_severity_points: float = Field(..., description="Max 20 pts: Physical disruption magnitude")
    visual_severity_points: float = Field(..., description="Max 20 pts: CV surface damage proportion")
    related_reports_points: float = Field(..., description="Max 15 pts: Duplicate/near-duplicate report volume")
    recency_points: float = Field(..., description="Max 10 pts: Hours elapsed since report")
    location_risk_points: float = Field(..., description="Max 15 pts: Corridor vulnerability/hotspot status")
    total_score: float = Field(..., description="Total 0-100 composite score")

    # CamelCase aliases matching frontend TypeScript PriorityBreakdown interface
    urgency: Optional[float] = Field(None, description="CamelCase alias for urgency_points")
    textSeverity: Optional[float] = Field(None, description="CamelCase alias for text_severity_points")
    visualSeverity: Optional[float] = Field(None, description="CamelCase alias for visual_severity_points")
    relatedReports: Optional[float] = Field(None, description="CamelCase alias for related_reports_points")
    recency: Optional[float] = Field(None, description="CamelCase alias for recency_points")
    locationRisk: Optional[float] = Field(None, description="CamelCase alias for location_risk_points")
    
    # Deprecated legacy sub-factor weights for backward compatibility
    urgency_weight: float = 0.30
    visual_weight: float = 0.25
    frequency_weight: float = 0.20
    recency_weight: float = 0.15
    exposure_weight: float = 0.10
    composite_score: float = Field(0.0, description="Normalized 0.0-1.0 score (total_score / 100.0)")

class VisualDetectionDetail(BaseModel):
    label: str
    confidence: float
    bbox: Optional[List[float]] = None  # [ymin, xmin, ymax, xmax] normalized
    task: Optional[str] = None
    class_id: Optional[int] = None
    class_name: Optional[str] = None
    source_model: Optional[str] = None
    execution_mode: Optional[str] = None

class IssueCreate(BaseModel):
    complaintText: str = Field(..., description="Citizen complaint text")
    location: Optional[str] = Field(None, description="Landmark or locality name")
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    imageUrl: Optional[str] = None
    uploadId: Optional[str] = None
    source: str = "citizen_portal"
    citizen_id: Optional[str] = None

class ResolutionEvidence(BaseModel):
    verified_at: Optional[str] = None
    inspector_id: Optional[str] = None
    original_image_url: Optional[str] = None
    original_upload_id: Optional[str] = None
    resolution_image_url: Optional[str] = None
    resolution_upload_id: Optional[str] = None
    original_detection: Optional[str] = None
    post_action_detection: Optional[str] = None
    resolutionStatus: ResolutionStatus = ResolutionStatus.REQUIRES_MANUAL_VERIFICATION
    resolutionConfidence: float = 0.0
    remainingDetection: Optional[str] = None
    verificationSummary: str = ""
    verificationMethod: str = "yolo_before_after_comparison"
    sceneComparable: bool = False
    comparisonMetrics: Dict[str, Any] = Field(default_factory=dict)
    beforeDetections: List[VisualDetectionDetail] = Field(default_factory=list)
    afterDetections: List[VisualDetectionDetail] = Field(default_factory=list)
    requiresManualReview: bool = False
    post_repair_cv_cleared: bool = False

class HotspotInfo(BaseModel):
    hotspotId: str
    center: List[float]  # [lat, lng]
    radius: float  # in meters
    issueCount: int
    dominantCategory: str
    averagePriority: float
    growthRate: float
    hotspotLevel: HotspotLevel
    densityPerKm2: float = 0.0

class RecurrenceInfo(BaseModel):
    recurringIssue: bool = False
    location: str
    category: str
    reportCount: int = 1
    firstReported: str
    lastReported: str
    recurrenceScore: float = 0.0  # 0.0 to 1.0
    trend: RecurrenceTrend = RecurrenceTrend.STABLE

class EvidenceConsistencyResult(BaseModel):
    consistencyScore: float = 0.50  # 0.0 to 1.0
    consistencyLevel: ConsistencyLevel = ConsistencyLevel.MANUAL_REVIEW
    textEvidence: str
    visualEvidence: str
    reason: str

class Issue(BaseModel):
    issueId: str
    complaintText: str
    category: IssueCategory = IssueCategory.UNSPECIFIED
    urgency: float = Field(0.0, ge=0.0, le=1.0, description="Text-derived urgency score")
    severity: float = Field(0.0, ge=0.0, le=1.0, description="Overall severity index")
    location: str
    latitude: float
    longitude: float
    ward: Optional[str] = "N-Ward"
    timestamp: str
    imageUrl: Optional[str] = None
    uploadId: Optional[str] = None
    citizen_id: Optional[str] = None
    
    # Deduplication & Grouping (Features 5, 6)
    duplicateGroup: Optional[str] = None
    isDuplicate: bool = False
    nearDuplicateCount: int = 0
    
    # Computer Vision Details (Features 8, 9)
    visualDetection: Optional[str] = None
    visualConfidence: float = 0.0
    visualSeverity: float = Field(0.0, ge=0.0, le=1.0)
    detectedObjects: List[VisualDetectionDetail] = []
    visionModel: Optional[str] = None
    visionTask: Optional[str] = None
    visionMode: Optional[str] = None
    
    # Text-Image Evidence Consistency (Feature 18)
    evidenceConsistency: float = Field(0.0, ge=0.0, le=1.0)
    consistencyLevel: ConsistencyLevel = ConsistencyLevel.MANUAL_REVIEW
    consistencyFlag: str = "Unverified"
    consistencyDetail: Optional[EvidenceConsistencyResult] = None
    
    # Spatiotemporal Intelligence & Hotspots (Features 7, 16)
    recurrence: int = Field(1, description="Times reported in corridor")
    hotspot: bool = Field(False, description="Flagged as high-density hotspot")
    hotspotClusterId: Optional[str] = None
    hotspotDetail: Optional[HotspotInfo] = None
    
    # Recurring Issue Detection (Feature 17)
    recurringDetail: Optional[RecurrenceInfo] = None
    
    # Risk-Aware Dynamic Priority (Feature 15: 0-100 explainable score)
    priorityScore: float = Field(..., description="0-100 explainable priority score")
    priorityLevel: PriorityLevel = PriorityLevel.LOW
    priorityBreakdown: Optional[DynamicPriorityBreakdown] = None
    priorityReasoning: str = ""
    
    # Department Routing & Recommended Action (Feature 19)
    department: str = "Municipal Administration"
    recommendedAction: str = "Inspect and triage"
    slaHours: int = 72
    
    # Issue Lifecycle & Resolution Verification (Feature 20)
    status: IssueStatus = IssueStatus.OPEN
    resolutionEvidence: Optional[ResolutionEvidence] = None
    resolutionHistory: List[ResolutionEvidence] = Field(default_factory=list)
    statusHistory: List[Dict[str, Any]] = Field(default_factory=list)
    
    metadata: Dict[str, Any] = {}

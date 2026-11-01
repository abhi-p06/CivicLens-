from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class DocumentStatus(str, Enum):
    CURRENT = "CURRENT"
    DRAFT = "DRAFT"
    SUPERSEDED = "SUPERSEDED"
    UNVERIFIED = "UNVERIFIED"

class RecommendationType(str, Enum):
    PRECAUTION = "PRECAUTION"
    ACTION = "ACTION"
    CHECKLIST = "CHECKLIST"

class OfficerDecisionType(str, Enum):
    ACCEPTED = "ACCEPTED"
    EDITED = "EDITED"
    DISMISSED = "DISMISSED"
    PENDING = "PENDING"

class GuidanceCitation(BaseModel):
    doc_id: str
    doc_title: str
    source_org: str
    url: str
    section: str
    page_number: Optional[int] = None
    document_version: Optional[str] = None
    document_status: DocumentStatus = DocumentStatus.CURRENT
    is_statutory_requirement: bool = True

class GuidanceActionItem(BaseModel):
    id: str
    item_type: RecommendationType
    title: str
    description: str
    steps: List[str] = Field(default_factory=list)
    equipment: List[str] = Field(default_factory=list)
    handling_precautions: List[str] = Field(default_factory=list)
    citation: GuidanceCitation
    is_requirement: bool = False
    officer_decision: OfficerDecisionType = OfficerDecisionType.PENDING
    edited_text: Optional[str] = None
    decision_reason: Optional[str] = None
    decided_by: Optional[str] = None
    decided_at: Optional[str] = None

class ConflictingSourceTopic(BaseModel):
    topic: str
    source_a: str
    position_a: str
    source_b: str
    position_b: str
    recommended_reconciliation: str

class FieldGuidanceResult(BaseModel):
    guidance_id: str
    issue_id: str
    category: str
    generated_at: str
    situation_summary: str
    recommendation_rationale: str
    immediate_precautions: List[GuidanceActionItem] = Field(default_factory=list)
    recommended_field_actions: List[GuidanceActionItem] = Field(default_factory=list)
    equipment_and_resources: List[str] = Field(default_factory=list)
    handling_precautions: List[str] = Field(default_factory=list)
    completion_checklist: List[Dict[str, Any]] = Field(default_factory=list)
    retrieved_references: List[GuidanceCitation] = Field(default_factory=list)
    disagreements: List[ConflictingSourceTopic] = Field(default_factory=list)
    is_hazardous_escalation: bool = False
    escalation_notice: Optional[str] = None
    has_insufficient_sources: bool = False
    fallback_message: Optional[str] = None
    engineering_disclaimer: Optional[str] = None

class GuidanceDecisionRequest(BaseModel):
    item_id: str
    decision: OfficerDecisionType
    edited_text: Optional[str] = None
    reason: Optional[str] = None

class GuidanceSource(BaseModel):
    id: str
    name: str
    domain: str
    base_url: str
    category: str
    is_active: bool = True
    is_allowlisted: bool = True
    last_retrieved_at: Optional[str] = None
    last_status: str = "NEVER_RUN"
    error_message: Optional[str] = None

class GuidanceDocument(BaseModel):
    id: str
    source_id: str
    source_domain: str
    source_org: str
    title: str
    url: str
    publication_date: str
    document_version: str
    document_status: DocumentStatus
    applicable_category: str
    content_type: str = "text/html"
    file_hash: str
    summary: str
    sections_json: str = "[]"
    is_approved: bool = True
    last_retrieved_at: Optional[str] = None

class AdminSourceUpdateRequest(BaseModel):
    is_active: Optional[bool] = None
    category: Optional[str] = None

class AdminDocumentUpdateRequest(BaseModel):
    document_status: Optional[DocumentStatus] = None
    is_approved: Optional[bool] = None

class AdminIngestRequest(BaseModel):
    source_url: Optional[str] = None
    source_id: Optional[str] = None
    force_refresh: bool = False


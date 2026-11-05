from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import (
    String,
    Float,
    Integer,
    Boolean,
    Text,
    DateTime,
    Index
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base

class IssueRecord(Base):
    """
    Persistent SQLite storage representation for civic issues.
    Combines indexed query columns for fast relational filtering
    with a complete JSON payload ensuring 100% fidelity with Pydantic Issue models.
    """
    __tablename__ = "issues"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    complaint_text: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    urgency: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    severity: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    location: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    longitude: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    ward: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    timestamp: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    
    # Deduplication & Grouping
    duplicate_group: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    is_duplicate: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    near_duplicate_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    # Computer Vision Details
    visual_detection: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    visual_confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    visual_severity: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    
    # Text-Image Consistency
    evidence_consistency: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    consistency_level: Mapped[str] = mapped_column(String(64), nullable=False, default="MANUAL REVIEW")
    consistency_flag: Mapped[str] = mapped_column(String(64), nullable=False, default="Unverified")
    
    # Spatiotemporal
    recurrence: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_hotspot: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    hotspot_cluster_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    
    # Priority
    priority_score: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    priority_level: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    
    # Department & SLA
    department: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    recommended_action: Mapped[str] = mapped_column(Text, nullable=False, default="Inspect and triage")
    sla_hours: Mapped[int] = mapped_column(Integer, nullable=False, default=72)
    
    # Hierarchical Ward & Operations Management
    authority_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    authority_code: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, index=True)
    authority_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    zone_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    zone_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    ward_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    sub_ward_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    sub_ward_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    locality_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    locality_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    supervisor_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    routing_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    jurisdiction_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    jurisdiction_review_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    jurisdiction_review_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Ownership & Status
    citizen_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    
    # Complete, loss-free Pydantic payload serialization
    data_json: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Audit timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        Index("ix_issues_category_priority", "category", "priority_score"),
        Index("ix_issues_status_priority", "status", "priority_score"),
        Index("ix_issues_lat_lng", "latitude", "longitude"),
    )


class RoutingConfigRecord(Base):
    """
    Persistent storage for municipal department routing and SLA rules.
    Ensures agency routing customizations survive server restarts.
    """
    __tablename__ = "routing_configs"

    category: Mapped[str] = mapped_column(String(64), primary_key=True)
    department: Mapped[str] = mapped_column(String(128), nullable=False)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    config_json: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )


class UploadRecord(Base):
    """
    Persistent metadata storage for verified and stored image uploads.
    Prevents direct filesystem path exposure to clients while tracking
    provenance, MIME type, size, and issue association.
    """
    __tablename__ = "uploads"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(64), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    original_filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    issue_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )


class VerificationHistoryRecord(Base):
    """
    Persistent audit trail of computer vision verification attempts.
    Preserves historical inspection outcomes across repeated checks.
    """
    __tablename__ = "verification_history"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    issue_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    inspector_id: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    verification_method: Mapped[str] = mapped_column(String(128), nullable=False)
    scene_comparable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    resolution_upload_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    data_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )


class UserRecord(Base):
    """
    Persistent storage for authenticated CIVILENS accounts:
    - Citizen
    - Municipal Officer / Field Inspector
    - Administrator
    Stores per-user salt and PBKDF2-HMAC-SHA256 password hash.
    """
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    salt: Mapped[str] = mapped_column(String(64), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )


class TeamRecord(Base):
    """
    Persistent storage for municipal field teams (Roads & Sanitation).
    """
    __tablename__ = "operational_teams"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    department: Mapped[str] = mapped_column(String(128), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="AVAILABLE")
    ward: Mapped[str] = mapped_column(String(64), nullable=False, default="ALL")
    sub_ward_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    authority_id: Mapped[str] = mapped_column(String(64), nullable=False, default="AUTH-BMC")
    supervisor_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=6)
    contact_lead: Mapped[str] = mapped_column(String(128), nullable=False, default="Duty Supervisor")
    active_tasks_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )


class WardConfigRecord(Base):
    """
    Persistent storage for municipal ward operational configurations.
    """
    __tablename__ = "ward_configs"

    ward_code: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    ward_name: Mapped[str] = mapped_column(String(128), nullable=False)
    lead_officer: Mapped[str] = mapped_column(String(128), nullable=False, default="Abhinay")
    active_teams: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )


class MunicipalAuthorityRecord(Base):
    """
    Persistent storage for separate municipal authorities (e.g. BMC and NMMC).
    """
    __tablename__ = "authorities"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    short_name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    city: Mapped[str] = mapped_column(String(64), nullable=False)
    headquarters: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    boundary_geojson: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )


class AdminZoneRecord(Base):
    """
    Persistent storage for official administrative zones under a municipal authority.
    """
    __tablename__ = "admin_zones"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    authority_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    zonal_officer: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    boundary_geojson: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )


class AdminWardRecord(Base):
    """
    Persistent storage for official administrative wards / ward offices.
    """
    __tablename__ = "admin_wards"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    authority_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    zone_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    ward_code: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    ward_name: Mapped[str] = mapped_column(String(128), nullable=False)
    office_address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    lead_officer: Mapped[str] = mapped_column(String(128), nullable=False, default="Abhinay")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    boundary_geojson: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )


class SubWardRecord(Base):
    """
    Persistent storage for CIVILENS operational sub-wards / service beats.
    Clearly flagged with is_official=False to prevent false labeling.
    """
    __tablename__ = "sub_wards"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    ward_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    authority_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    sub_ward_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    is_official: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    operational_type: Mapped[str] = mapped_column(String(64), nullable=False, default="CIVILENS_OPERATIONAL_SUB_WARD")
    supervisor_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    supervisor_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    default_road_team_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    default_swm_team_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    boundary_geojson: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )


class LocalityBeatRecord(Base):
    """
    Persistent storage for micro-localities, service beats, and landmark road corridors.
    """
    __tablename__ = "localities"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    sub_ward_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    ward_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    authority_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    landmark: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    radius_meters: Mapped[float] = mapped_column(Float, default=500.0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )


class OfficerJurisdictionRecord(Base):
    """
    Scoped jurisdiction assignment linking municipal officers and supervisors
    to specific authorities, administrative wards, or operational sub-wards.
    """
    __tablename__ = "officer_jurisdictions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    authority_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    ward_code: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    sub_ward_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    jurisdiction_level: Mapped[str] = mapped_column(String(64), nullable=False, default="WARD_OFFICER")
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )


class JurisdictionAuditLogRecord(Base):
    """
    Complete audit trail of jurisdiction corrections and routing changes.
    Tracks previous vs new jurisdiction, changing actor, timestamp, and mandatory reason.
    """
    __tablename__ = "jurisdiction_audit_logs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    issue_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    previous_jurisdiction_json: Mapped[str] = mapped_column(Text, nullable=False)
    new_jurisdiction_json: Mapped[str] = mapped_column(Text, nullable=False)
    changed_by: Mapped[str] = mapped_column(String(128), nullable=False)
    changed_by_role: Mapped[str] = mapped_column(String(32), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )


class GuidanceSourceRecord(Base):
    """
    Controlled allowlist registry of trusted government research sources.
    """
    __tablename__ = "guidance_sources"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    domain: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    base_url: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False, default="ALL")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_allowlisted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_retrieved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_status: Mapped[str] = mapped_column(String(32), nullable=False, default="NEVER_RUN")
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )


class GuidanceDocumentRecord(Base):
    """
    Persistent indexed knowledge base of official government specifications,
    manuals, and circulars for grounding AI field recommendations.
    """
    __tablename__ = "guidance_documents"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    source_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_domain: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    source_org: Mapped[str] = mapped_column(String(128), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    url: Mapped[str] = mapped_column(String(512), nullable=False)
    publication_date: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    document_version: Mapped[str] = mapped_column(String(64), nullable=False, default="Current")
    document_status: Mapped[str] = mapped_column(String(32), nullable=False, default="CURRENT", index=True)
    applicable_category: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    content_type: Mapped[str] = mapped_column(String(64), nullable=False, default="text/html")
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    sections_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    is_approved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    last_retrieved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        Index("ix_guidance_cat_status", "applicable_category", "document_status", "is_approved"),
    )




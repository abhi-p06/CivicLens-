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



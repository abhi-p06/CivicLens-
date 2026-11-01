import os
import json
import uuid
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from contextlib import contextmanager

from datetime import datetime, timezone

from sqlalchemy import select, func, delete
from sqlalchemy.orm import Session

from app.models.issue import (
    Issue,
    IssueStatus,
    IssueCategory,
    PriorityLevel,
    ResolutionStatus,
    ResolutionEvidence,
    TaskAssignment,
    TimelineEvent,
    TemporaryMeasures,
    RepeatCollection,
    CompletionDetails,
    CitizenFeedback
)
from app.config import settings
from app.db.database import SessionLocal, get_db_session, init_db
from app.db.models import (
    IssueRecord,
    RoutingConfigRecord,
    UploadRecord,
    VerificationHistoryRecord,
    UserRecord,
    TeamRecord,
    WardConfigRecord
)
from app.models.field_guidance import FieldGuidanceResult, OfficerDecisionType
from app.services.guidance.guidance_engine import GuidanceEngine

logger = logging.getLogger(__name__)

from dataclasses import dataclass

@dataclass
class UploadMetadata:
    id: str
    filename: str
    content_type: str
    size_bytes: int
    original_filename: Optional[str] = None
    issue_id: Optional[str] = None

DEFAULT_TEAMS = [
    {
        "id": "TEAM-ROAD-01",
        "name": "Quick Patch Asphalt Squad (Ward N)",
        "department": "Road Infrastructure Maintenance",
        "category": "Roads & Footpaths",
        "status": "AVAILABLE",
        "ward": "N-Ward",
        "contact_lead": "Supervisor R. Shinde",
    },
    {
        "id": "TEAM-ROAD-02",
        "name": "Central Pothole Emergency Unit",
        "department": "Road Infrastructure Maintenance",
        "category": "Roads & Footpaths",
        "status": "AVAILABLE",
        "ward": "ALL",
        "contact_lead": "Officer P. Mane",
    },
    {
        "id": "TEAM-ROAD-03",
        "name": "Heavy Resurfacing Crew (Western Express)",
        "department": "Road Infrastructure Maintenance",
        "category": "Roads & Footpaths",
        "status": "BUSY",
        "ward": "K/West",
        "contact_lead": "Eng. V. Kadam",
    },
    {
        "id": "TEAM-ROAD-04",
        "name": "Navi Mumbai Municipal Road Fleet",
        "department": "Road Infrastructure Maintenance",
        "category": "Roads & Footpaths",
        "status": "AVAILABLE",
        "ward": "NMMC-Vashi",
        "contact_lead": "Supervisor S. Sawant",
    },
    {
        "id": "TEAM-SWM-01",
        "name": "Solid Waste Rapid Response (Ward N)",
        "department": "Solid Waste Management",
        "category": "Sanitation & Garbage",
        "status": "AVAILABLE",
        "ward": "N-Ward",
        "contact_lead": "Inspector A. Jadhav",
    },
    {
        "id": "TEAM-SWM-02",
        "name": "Ward G/North Sanitation Fleet",
        "department": "Solid Waste Management",
        "category": "Sanitation & Garbage",
        "status": "AVAILABLE",
        "ward": "G/North",
        "contact_lead": "Foreman D. Kamble",
    },
    {
        "id": "TEAM-SWM-03",
        "name": "Bulky Litter & Debris Unit (Kurla/L-Ward)",
        "department": "Solid Waste Management",
        "category": "Sanitation & Garbage",
        "status": "BUSY",
        "ward": "L-Ward",
        "contact_lead": "Supervisor M. Ansari",
    },
    {
        "id": "TEAM-SWM-04",
        "name": "NMMC Vashi Sanitation Taskforce",
        "department": "Solid Waste Management",
        "category": "Sanitation & Garbage",
        "status": "AVAILABLE",
        "ward": "NMMC-Vashi",
        "contact_lead": "Officer B. Patil",
    },
]

DEFAULT_WARDS = [
    {
        "ward_code": "N-Ward",
        "ward_name": "N-Ward (Vidyavihar / Ghatkopar)",
        "lead_officer": "Abhinay",
        "active_teams": ["TEAM-ROAD-01", "TEAM-SWM-01"],
    },
    {
        "ward_code": "L-Ward",
        "ward_name": "L-Ward (Kurla)",
        "lead_officer": "Abhinay",
        "active_teams": ["TEAM-ROAD-02", "TEAM-SWM-03"],
    },
    {
        "ward_code": "G/North",
        "ward_name": "G/North (Dharavi / Dadar)",
        "lead_officer": "Abhinay",
        "active_teams": ["TEAM-ROAD-02", "TEAM-SWM-02"],
    },
    {
        "ward_code": "K/West",
        "ward_name": "K/West (Andheri West)",
        "lead_officer": "Abhinay",
        "active_teams": ["TEAM-ROAD-03", "TEAM-ROAD-02"],
    },
    {
        "ward_code": "NMMC-Vashi",
        "ward_name": "Navi Mumbai (Vashi / Belapur)",
        "lead_officer": "Abhinay",
        "active_teams": ["TEAM-ROAD-04", "TEAM-SWM-04"],
    },
]

def _ensure_timeline(issue: Issue) -> Issue:
    if not issue.timeline:
        initial_event = TimelineEvent(
            id=f"evt-{issue.issueId[:8]}",
            event_type="REPORTED",
            title="Grievance Registered",
            description=issue.complaintText or "Complaint registered and ingested into CIVILENS.",
            actor=issue.metadata.get("citizen_name") or "Citizen",
            role="citizen",
            timestamp=issue.timestamp,
            evidence_url=issue.imageUrl
        )
        issue.timeline = [initial_event]
        if issue.statusHistory:
            for idx, h in enumerate(issue.statusHistory):
                h_stat = h.get("status", "")
                if h_stat not in ("OPEN", "REPORTED"):
                    issue.timeline.append(TimelineEvent(
                        id=f"evt-hist-{idx}",
                        event_type="PROGRESS_UPDATE",
                        title=f"Status: {h_stat}",
                        description=h.get("note") or f"Status transitioned to {h_stat}",
                        actor=h.get("actor") or "Abhinay",
                        role="inspector",
                        timestamp=h.get("timestamp") or issue.timestamp
                    ))
    return issue

class SqliteIssueRepository:
    """
    Production-grade SQLite repository implementing persistent storage
    for CiviLens issues and routing configurations.
    
    Guarantees:
    - ACID transactional consistency
    - Lossless preservation of complete Pydantic Issue schema
    - Indexed relational columns for fast filtering
    - Safe first-run seeding that never wipes or duplicates data on restart
    """

    def __init__(
        self,
        session_factory=None,
        seed_file_path: Optional[str] = None
    ):
        self._session_factory = session_factory or SessionLocal
        if seed_file_path is None:
            seed_file_path = str(Path(__file__).parent.parent.parent / "data" / "seed_issues.json")
        self.seed_file_path = seed_file_path

    @contextmanager
    def _get_session(self):
        with get_db_session(self._session_factory) as s:
            yield s

    def count(self) -> int:
        """Returns total number of issues stored."""
        with self._get_session() as session:
            stmt = select(func.count()).select_from(IssueRecord)
            return session.scalar(stmt) or 0

    def seed_if_empty(self, seed_file_path: Optional[str] = None) -> int:
        """
        First-run safe initialization.
        Seeds baseline records only if the issue table is completely empty.
        Leaves existing data untouched on repeated executions.
        """
        path = seed_file_path or self.seed_file_path
        p = Path(path)
        if not p.exists():
            logger.warning(f"Seed file not found at {path}; skipping initial seeding.")
            return 0

        with self._get_session() as session:
            existing_count = session.scalar(select(func.count()).select_from(IssueRecord)) or 0
            if existing_count > 0:
                logger.info(f"Database already contains {existing_count} issues. Skipping seed insertion.")
                return 0

            with open(p, "r", encoding="utf-8") as f:
                raw_data = json.load(f)

            inserted = 0
            for item in raw_data:
                issue = Issue.model_validate(item)
                record = self._to_record(issue)
                session.add(record)
                inserted += 1

            logger.info(f"Successfully seeded {inserted} issues into persistent database.")
        self.seed_default_users_if_empty()
        return inserted

    def clear_issues(self) -> int:
        """
        Transactionally wipes all issue records without touching users or routing configs.
        Maintains an empty presentation database environment.
        """
        with self._get_session() as session:
            count = session.scalar(select(func.count()).select_from(IssueRecord)) or 0
            session.execute(delete(IssueRecord))
            logger.info(f"Cleaned {count} issues from persistent store.")
            return count

    def reset_demo(self, seed_file_path: Optional[str] = None) -> int:
        """
        Explicit demo reset operation.
        In presentation mode: wipes current issues to return to a clean zero-record baseline.
        In development/demo mode: reloads seed baseline within a single transaction.
        """
        if settings.is_presentation_database:
            return self.clear_issues()

        path = seed_file_path or self.seed_file_path
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Seed file not found at {path}")

        with open(p, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        with self._get_session() as session:
            session.execute(delete(IssueRecord))
            inserted = 0
            for item in raw_data:
                issue = Issue.model_validate(item)
                record = self._to_record(issue)
                session.add(record)
                inserted += 1

            logger.info(f"Demo reset: restored {inserted} seed issues in single transaction.")
        self.seed_default_users_if_empty()
        return inserted

    def list_issues(
        self,
        category: Optional[IssueCategory] = None,
        priority: Optional[PriorityLevel] = None,
        status_filter: Optional[IssueStatus] = None,
        hotspot_only: bool = False,
        citizen_id: Optional[str] = None
    ) -> List[Issue]:
        """
        Queries issues with optional relational filtering.
        Reconstructs valid, full Pydantic Issue models.
        """
        with self._get_session() as session:
            stmt = select(IssueRecord)

            if category is not None:
                cat_val = category.value if hasattr(category, "value") else str(category)
                stmt = stmt.where(IssueRecord.category == cat_val)

            if priority is not None:
                pri_val = priority.value if hasattr(priority, "value") else str(priority)
                stmt = stmt.where(IssueRecord.priority_level == pri_val)

            if status_filter is not None:
                stat_val = status_filter.value if hasattr(status_filter, "value") else str(status_filter)
                stmt = stmt.where(IssueRecord.status == stat_val)

            if hotspot_only:
                stmt = stmt.where(IssueRecord.is_hotspot.is_(True))

            if citizen_id is not None:
                stmt = stmt.where(IssueRecord.citizen_id == citizen_id)

            stmt = stmt.order_by(IssueRecord.priority_score.desc())
            records = session.scalars(stmt).all()
            results = []
            for r in records:
                issue = Issue.model_validate_json(r.data_json)
                if r.citizen_id and not issue.citizen_id:
                    issue.citizen_id = r.citizen_id
                _ensure_timeline(issue)
                results.append(issue)
            return results

    def get_issue(self, issue_id: str) -> Optional[Issue]:
        """Retrieves an issue by ID, reconstructing the full Pydantic model."""
        with self._get_session() as session:
            stmt = select(IssueRecord).where(IssueRecord.id == issue_id)
            record = session.scalar(stmt)
            if record is None:
                return None
            issue = Issue.model_validate_json(record.data_json)
            if record.citizen_id and not issue.citizen_id:
                issue.citizen_id = record.citizen_id
            _ensure_timeline(issue)
            return issue

    def add_issue(self, issue: Issue) -> Issue:
        """
        Atomically inserts or updates an issue record in the database.
        """
        with self._get_session() as session:
            stmt = select(IssueRecord).where(IssueRecord.id == issue.issueId)
            existing = session.scalar(stmt)
            
            if existing is not None:
                self._update_record_from_issue(existing, issue)
            else:
                record = self._to_record(issue)
                session.add(record)

            return issue

    def update_issue(self, issue: Issue) -> Issue:
        """Explicitly updates an existing issue record."""
        return self.add_issue(issue)

    def update_status(
        self,
        issue_id: str,
        new_status: IssueStatus,
        note: Optional[str] = None,
        actor: Optional[str] = None
    ) -> Optional[Issue]:
        """
        Atomically updates the status of an issue in SQLite.
        Updates indexed status column, embedded JSON payload, and statusHistory audit trail.
        """
        with self._get_session() as session:
            stmt = select(IssueRecord).where(IssueRecord.id == issue_id)
            record = session.scalar(stmt)
            if record is None:
                return None

            issue = Issue.model_validate_json(record.data_json)
            issue.status = new_status
            
            now_iso = datetime.now(timezone.utc).isoformat()
            if not hasattr(issue, "statusHistory") or issue.statusHistory is None:
                issue.statusHistory = []
            
            history_entry = {
                "status": new_status.value if hasattr(new_status, "value") else str(new_status),
                "timestamp": now_iso,
                "actor": actor or "INSPECTOR",
                "note": note or f"Status transitioned to {new_status.value if hasattr(new_status, 'value') else str(new_status)}"
            }
            issue.statusHistory.append(history_entry)

            record.status = new_status.value if hasattr(new_status, "value") else str(new_status)
            record.data_json = issue.model_dump_json()

            return issue

    # --------------------------------------------------------------------------
    # Routing Configuration Persistence
    # --------------------------------------------------------------------------

    def load_routing_configs(self) -> Dict[str, Dict[str, Any]]:
        """Loads all persisted department routing configurations."""
        with self._get_session() as session:
            records = session.scalars(select(RoutingConfigRecord)).all()
            result: Dict[str, Dict[str, Any]] = {}
            for r in records:
                try:
                    result[r.category] = json.loads(r.config_json)
                except Exception as e:
                    logger.error(f"Error parsing routing config for {r.category}: {e}")
            return result

    def save_routing_config(self, category: str, dept_info: Dict[str, Any]) -> None:
        """Persists or updates a department routing configuration."""
        with self._get_session() as session:
            stmt = select(RoutingConfigRecord).where(RoutingConfigRecord.category == category)
            record = session.scalar(stmt)
            config_json = json.dumps(dept_info)
            department = dept_info.get("department", "Municipal Department")
            code = dept_info.get("code", "MCGM-GEN")

            if record is not None:
                record.department = department
                record.code = code
                record.config_json = config_json
            else:
                new_record = RoutingConfigRecord(
                    category=category,
                    department=department,
                    code=code,
                    config_json=config_json
                )
                session.add(new_record)

    def seed_routing_defaults_if_empty(self, default_configs: Dict[str, Dict[str, Any]]) -> None:
        """Seeds default routing configurations if none exist."""
        with self._get_session() as session:
            count = session.scalar(select(func.count()).select_from(RoutingConfigRecord)) or 0
            if count == 0:
                for cat, cfg in default_configs.items():
                    session.add(RoutingConfigRecord(
                        category=cat,
                        department=cfg.get("department", "Municipal Department"),
                        code=cfg.get("code", "MCGM-GEN"),
                        config_json=json.dumps(cfg)
                    ))

    # --------------------------------------------------------------------------
    # Upload Storage Metadata Persistence
    # --------------------------------------------------------------------------

    def save_upload(
        self,
        upload_id: str,
        filename: str,
        content_type: str,
        size_bytes: int,
        original_filename: Optional[str] = None,
        issue_id: Optional[str] = None
    ) -> "UploadMetadata":
        """Atomically persists metadata for a stored image upload."""
        with self._get_session() as session:
            record = UploadRecord(
                id=upload_id,
                filename=filename,
                content_type=content_type,
                size_bytes=size_bytes,
                original_filename=original_filename,
                issue_id=issue_id
            )
            session.add(record)
            return UploadMetadata(
                id=upload_id,
                filename=filename,
                content_type=content_type,
                size_bytes=size_bytes,
                original_filename=original_filename,
                issue_id=issue_id
            )

    def get_upload(self, upload_id: str) -> Optional["UploadMetadata"]:
        """Retrieves upload record by upload_id."""
        with self._get_session() as session:
            stmt = select(UploadRecord).where(UploadRecord.id == upload_id)
            record = session.scalar(stmt)
            if not record:
                return None
            return UploadMetadata(
                id=record.id,
                filename=record.filename,
                content_type=record.content_type,
                size_bytes=record.size_bytes,
                original_filename=record.original_filename,
                issue_id=record.issue_id
            )

    def associate_upload_with_issue(self, upload_id: str, issue_id: str) -> None:
        """Links an upload record to a created issue."""
        with self._get_session() as session:
            stmt = select(UploadRecord).where(UploadRecord.id == upload_id)
            record = session.scalar(stmt)
            if record:
                record.issue_id = issue_id

    # --------------------------------------------------------------------------
    # Record Transformation Helpers
    # --------------------------------------------------------------------------

    def _to_record(self, issue: Issue) -> IssueRecord:
        cat_val = issue.category.value if hasattr(issue.category, "value") else str(issue.category)
        pri_val = issue.priorityLevel.value if hasattr(issue.priorityLevel, "value") else str(issue.priorityLevel)
        stat_val = issue.status.value if hasattr(issue.status, "value") else str(issue.status)
        cons_val = issue.consistencyLevel.value if hasattr(issue.consistencyLevel, "value") else str(issue.consistencyLevel)

        return IssueRecord(
            id=issue.issueId,
            complaint_text=issue.complaintText,
            category=cat_val,
            urgency=float(issue.urgency),
            severity=float(issue.severity),
            location=issue.location,
            latitude=float(issue.latitude),
            longitude=float(issue.longitude),
            ward=issue.ward,
            timestamp=issue.timestamp,
            duplicate_group=issue.duplicateGroup,
            is_duplicate=bool(issue.isDuplicate),
            near_duplicate_count=int(issue.nearDuplicateCount),
            visual_detection=issue.visualDetection,
            visual_confidence=float(issue.visualConfidence),
            visual_severity=float(issue.visualSeverity),
            evidence_consistency=float(issue.evidenceConsistency),
            consistency_level=cons_val,
            consistency_flag=issue.consistencyFlag,
            recurrence=int(issue.recurrence),
            is_hotspot=bool(issue.hotspot),
            hotspot_cluster_id=issue.hotspotClusterId,
            priority_score=float(issue.priorityScore),
            priority_level=pri_val,
            department=issue.department,
            recommended_action=issue.recommendedAction,
            sla_hours=int(issue.slaHours),
            citizen_id=getattr(issue, "citizen_id", None),
            status=stat_val,
            data_json=issue.model_dump_json()
        )

    def _update_record_from_issue(self, record: IssueRecord, issue: Issue) -> None:
        cat_val = issue.category.value if hasattr(issue.category, "value") else str(issue.category)
        pri_val = issue.priorityLevel.value if hasattr(issue.priorityLevel, "value") else str(issue.priorityLevel)
        stat_val = issue.status.value if hasattr(issue.status, "value") else str(issue.status)
        cons_val = issue.consistencyLevel.value if hasattr(issue.consistencyLevel, "value") else str(issue.consistencyLevel)

        record.complaint_text = issue.complaintText
        record.category = cat_val
        record.urgency = float(issue.urgency)
        record.severity = float(issue.severity)
        record.location = issue.location
        record.latitude = float(issue.latitude)
        record.longitude = float(issue.longitude)
        record.ward = issue.ward
        record.timestamp = issue.timestamp
        record.duplicate_group = issue.duplicateGroup
        record.is_duplicate = bool(issue.isDuplicate)
        record.near_duplicate_count = int(issue.nearDuplicateCount)
        record.visual_detection = issue.visualDetection
        record.visual_confidence = float(issue.visualConfidence)
        record.visual_severity = float(issue.visualSeverity)
        record.evidence_consistency = float(issue.evidenceConsistency)
        record.consistency_level = cons_val
        record.consistency_flag = issue.consistencyFlag
        record.recurrence = int(issue.recurrence)
        record.is_hotspot = bool(issue.hotspot)
        record.hotspot_cluster_id = issue.hotspotClusterId
        record.priority_score = float(issue.priorityScore)
        record.priority_level = pri_val
        record.department = issue.department
        record.recommended_action = issue.recommendedAction
        record.sla_hours = int(issue.slaHours)
        record.citizen_id = getattr(issue, "citizen_id", None)
        record.status = stat_val
        record.data_json = issue.model_dump_json()

    def record_verification(self, issue_id: str, evidence: ResolutionEvidence) -> Issue:
        """
        Atomically records a computer-vision resolution verification attempt:
        - Updates issue.resolutionEvidence
        - Appends evidence to issue.resolutionHistory
        - Updates issue.status according to conservative lifecycle rules:
            LIKELY_RESOLVED -> IssueStatus.RESOLVED
            STILL_PRESENT -> IssueStatus.ACTION_IN_PROGRESS
            REQUIRES_MANUAL_VERIFICATION -> IssueStatus.VERIFICATION
        - Appends an entry to issue.statusHistory audit trail
        - Inserts relational VerificationHistoryRecord
        - Commits in a single ACID transaction.
        """
        import uuid
        with self._get_session() as session:
            stmt = select(IssueRecord).where(IssueRecord.id == issue_id)
            record = session.scalar(stmt)
            if not record:
                raise KeyError(f"Issue {issue_id} not found")

            issue = Issue.model_validate_json(record.data_json)
            now_iso = datetime.now(timezone.utc).isoformat()

            # Lifecycle status transition
            if evidence.resolutionStatus == ResolutionStatus.LIKELY_RESOLVED:
                issue.status = IssueStatus.RESOLVED
            elif evidence.resolutionStatus == ResolutionStatus.STILL_PRESENT:
                issue.status = IssueStatus.ACTION_IN_PROGRESS
            else:
                issue.status = IssueStatus.VERIFICATION

            issue.resolutionEvidence = evidence
            if not hasattr(issue, "resolutionHistory") or issue.resolutionHistory is None:
                issue.resolutionHistory = []
            issue.resolutionHistory.append(evidence)

            if not hasattr(issue, "statusHistory") or issue.statusHistory is None:
                issue.statusHistory = []
            issue.statusHistory.append({
                "status": issue.status.value,
                "timestamp": now_iso,
                "note": f"Vision verification: {evidence.resolutionStatus.value} (conf: {evidence.resolutionConfidence:.2f})"
            })

            # Update IssueRecord
            self._update_record_from_issue(record, issue)

            # Insert VerificationHistoryRecord
            hist_rec = VerificationHistoryRecord(
                id=str(uuid.uuid4()),
                issue_id=issue_id,
                inspector_id=evidence.inspector_id or "SYSTEM_CV",
                status=evidence.resolutionStatus.value,
                confidence=float(evidence.resolutionConfidence),
                verification_method=evidence.verificationMethod,
                scene_comparable=bool(evidence.sceneComparable),
                resolution_upload_id=evidence.resolution_upload_id,
                data_json=evidence.model_dump_json()
            )
            session.add(hist_rec)
            return issue

    def get_verification_history(self, issue_id: str) -> List[ResolutionEvidence]:
        """Retrieves complete chronological verification history for an issue."""
        with self._get_session() as session:
            stmt = (
                select(VerificationHistoryRecord)
                .where(VerificationHistoryRecord.issue_id == issue_id)
                .order_by(VerificationHistoryRecord.created_at.asc())
            )
            records = session.scalars(stmt).all()
            if records:
                return [ResolutionEvidence.model_validate_json(r.data_json) for r in records]

            # Fallback to issue JSON payload if relational history empty
            stmt_issue = select(IssueRecord).where(IssueRecord.id == issue_id)
            issue_rec = session.scalar(stmt_issue)
            if issue_rec:
                iss = Issue.model_validate_json(issue_rec.data_json)
                if iss.resolutionHistory:
                    return iss.resolutionHistory
                elif iss.resolutionEvidence:
                    return [iss.resolutionEvidence]
            return []

    # --------------------------------------------------------------------------
    # User Account Management
    # --------------------------------------------------------------------------

    def get_user_by_identifier(self, identifier: str) -> Optional[Dict[str, Any]]:
        """Finds user by username OR email (case-insensitive)."""
        clean = identifier.strip().lower()
        with self._get_session() as session:
            stmt = select(UserRecord).where(
                (func.lower(UserRecord.username) == clean) | (func.lower(UserRecord.email) == clean)
            )
            rec = session.scalar(stmt)
            if not rec:
                return None
            return {
                "id": rec.id,
                "username": rec.username,
                "email": rec.email,
                "name": rec.name,
                "password_hash": rec.password_hash,
                "salt": rec.salt,
                "role": rec.role,
                "is_active": rec.is_active,
                "created_at": rec.created_at.isoformat() if rec.created_at else ""
            }

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        with self._get_session() as session:
            stmt = select(UserRecord).where(UserRecord.id == user_id)
            rec = session.scalar(stmt)
            if not rec:
                return None
            return {
                "id": rec.id,
                "username": rec.username,
                "email": rec.email,
                "name": rec.name,
                "password_hash": rec.password_hash,
                "salt": rec.salt,
                "role": rec.role,
                "is_active": rec.is_active,
                "created_at": rec.created_at.isoformat() if rec.created_at else ""
            }

    def create_user(
        self,
        username: str,
        email: str,
        name: str,
        password_hash: str,
        salt: str,
        role: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        import uuid
        uid = user_id or f"USER-{str(uuid.uuid4())[:8].upper()}"
        with self._get_session() as session:
            user_rec = UserRecord(
                id=uid,
                username=username.strip().lower(),
                email=email.strip().lower(),
                name=name.strip(),
                password_hash=password_hash,
                salt=salt,
                role=role.strip().lower(),
                is_active=True
            )
            session.add(user_rec)
            return {
                "id": user_rec.id,
                "username": user_rec.username,
                "email": user_rec.email,
                "name": user_rec.name,
                "role": user_rec.role,
                "is_active": user_rec.is_active
            }

    def list_users(self) -> List[Dict[str, Any]]:
        with self._get_session() as session:
            stmt = select(UserRecord).order_by(UserRecord.created_at.asc())
            records = session.scalars(stmt).all()
            return [
                {
                    "id": r.id,
                    "username": r.username,
                    "email": r.email,
                    "name": r.name,
                    "role": r.role,
                    "is_active": r.is_active,
                    "created_at": r.created_at.isoformat() if r.created_at else ""
                }
                for r in records
            ]

    def seed_default_users_if_empty(self) -> int:
        """
        Initializes default demo accounts in development environments:
        - Citizen: citizen@civilens.org / Citizen@123 (Abhinay)
        - Inspector: inspector@civilens.org / Inspector@123 (Abhinay)
        - Administrator: admin@civilens.org / Admin@123
        """
        from app.core.security import hash_password
        from app.config import settings
        is_production = settings.env.lower() in ("production", "prod")
        if is_production:
            logger.info("Production environment active: Default development demo user seeding is disabled.")
            return 0

        with self._get_session() as session:
            count = session.scalar(select(func.count()).select_from(UserRecord)) or 0
            if count > 0:
                return 0

            citizen_pwd = os.getenv("CIVILENS_DEV_CITIZEN_PASSWORD", "Citizen@123")
            inspector_pwd = os.getenv("CIVILENS_DEV_INSPECTOR_PASSWORD", "Inspector@123")
            admin_pwd = os.getenv("CIVILENS_DEV_ADMIN_PASSWORD", "Admin@123")

            defaults = [
                ("CITIZEN-001", "citizen", "citizen@civilens.org", "Abhinay", citizen_pwd, "citizen"),
                ("INSP-MUMBAI-01", "inspector", "inspector@civilens.org", "Abhinay", inspector_pwd, "inspector"),
                ("ADMIN-SYS-01", "admin", "admin@civilens.org", "Municipal Operations Administrator", admin_pwd, "admin"),
            ]
            inserted = 0
            for uid, uname, uemail, uname_full, pwd, urole in defaults:
                pw_hash, salt = hash_password(pwd)
                rec = UserRecord(
                    id=uid,
                    username=uname,
                    email=uemail,
                    name=uname_full,
                    password_hash=pw_hash,
                    salt=salt,
                    role=urole,
                    is_active=True
                )
                session.add(rec)
                inserted += 1
            logger.info(f"Seeded {inserted} default authentication accounts.")
            return inserted

    # --------------------------------------------------------------------------
    # Ward Operations Management & Task Assignment
    # --------------------------------------------------------------------------

    def seed_default_teams_and_wards_if_empty(self) -> None:
        init_db(self._session_factory().get_bind())
        with self._get_session() as session:
            team_count = session.scalar(select(func.count()).select_from(TeamRecord)) or 0
            if team_count == 0:
                for t in DEFAULT_TEAMS:
                    rec = TeamRecord(
                        id=t["id"],
                        name=t["name"],
                        department=t["department"],
                        category=t["category"],
                        status=t.get("status", "AVAILABLE"),
                        ward=t.get("ward", "ALL"),
                        contact_lead=t.get("contact_lead", "Duty Supervisor")
                    )
                    session.add(rec)
                logger.info(f"Seeded {len(DEFAULT_TEAMS)} default operational field teams.")

            ward_count = session.scalar(select(func.count()).select_from(WardConfigRecord)) or 0
            if ward_count == 0:
                for w in DEFAULT_WARDS:
                    rec = WardConfigRecord(
                        ward_code=w["ward_code"],
                        ward_name=w["ward_name"],
                        lead_officer=w.get("lead_officer", "Abhinay"),
                        active_teams=json.dumps(w.get("active_teams", []))
                    )
                    session.add(rec)
                logger.info(f"Seeded {len(DEFAULT_WARDS)} default ward configurations.")

    def list_teams(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        self.seed_default_teams_and_wards_if_empty()
        with self._get_session() as session:
            stmt = select(TeamRecord)
            if category:
                stmt = stmt.where(TeamRecord.category == category)
            stmt = stmt.order_by(TeamRecord.category, TeamRecord.name)
            teams = session.scalars(stmt).all()
            return [
                {
                    "id": t.id,
                    "name": t.name,
                    "department": t.department,
                    "category": t.category,
                    "status": t.status,
                    "ward": t.ward,
                    "contact_lead": t.contact_lead,
                    "active_tasks_count": t.active_tasks_count
                }
                for t in teams
            ]

    def get_team(self, team_id: str) -> Optional[Dict[str, Any]]:
        with self._get_session() as session:
            stmt = select(TeamRecord).where(TeamRecord.id == team_id)
            t = session.scalar(stmt)
            if not t:
                return None
            return {
                "id": t.id,
                "name": t.name,
                "department": t.department,
                "category": t.category,
                "status": t.status,
                "ward": t.ward,
                "contact_lead": t.contact_lead,
                "active_tasks_count": t.active_tasks_count
            }

    def create_team(self, team_data: Dict[str, Any]) -> Dict[str, Any]:
        with self._get_session() as session:
            team_id = team_data.get("id") or f"TEAM-{uuid.uuid4().hex[:6].upper()}"
            rec = TeamRecord(
                id=team_id,
                name=team_data["name"],
                department=team_data.get("department", "Municipal Infrastructure"),
                category=team_data.get("category", "Roads & Footpaths"),
                status=team_data.get("status", "AVAILABLE").upper(),
                ward=team_data.get("ward", "ALL"),
                contact_lead=team_data.get("contact_lead", "Duty Supervisor")
            )
            session.add(rec)
            return {
                "id": rec.id,
                "name": rec.name,
                "department": rec.department,
                "category": rec.category,
                "status": rec.status,
                "ward": rec.ward,
                "contact_lead": rec.contact_lead,
                "active_tasks_count": 0
            }

    def update_team(self, team_id: str, team_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        with self._get_session() as session:
            stmt = select(TeamRecord).where(TeamRecord.id == team_id)
            rec = session.scalar(stmt)
            if not rec:
                return None
            if "name" in team_data:
                rec.name = team_data["name"]
            if "department" in team_data:
                rec.department = team_data["department"]
            if "category" in team_data:
                rec.category = team_data["category"]
            if "status" in team_data:
                rec.status = team_data["status"].upper()
            if "ward" in team_data:
                rec.ward = team_data["ward"]
            if "contact_lead" in team_data:
                rec.contact_lead = team_data["contact_lead"]
            return {
                "id": rec.id,
                "name": rec.name,
                "department": rec.department,
                "category": rec.category,
                "status": rec.status,
                "ward": rec.ward,
                "contact_lead": rec.contact_lead,
                "active_tasks_count": rec.active_tasks_count
            }

    def delete_team(self, team_id: str) -> bool:
        with self._get_session() as session:
            stmt = select(TeamRecord).where(TeamRecord.id == team_id)
            rec = session.scalar(stmt)
            if not rec:
                return False
            session.delete(rec)
            return True

    def list_wards(self) -> List[Dict[str, Any]]:
        self.seed_default_teams_and_wards_if_empty()
        with self._get_session() as session:
            stmt = select(WardConfigRecord).order_by(WardConfigRecord.ward_code)
            wards = session.scalars(stmt).all()
            return [
                {
                    "ward_code": w.ward_code,
                    "ward_name": w.ward_name,
                    "lead_officer": w.lead_officer,
                    "active_teams": json.loads(w.active_teams) if w.active_teams else []
                }
                for w in wards
            ]

    def update_ward(self, ward_code: str, ward_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        with self._get_session() as session:
            stmt = select(WardConfigRecord).where(WardConfigRecord.ward_code == ward_code)
            rec = session.scalar(stmt)
            if not rec:
                return None
            if "lead_officer" in ward_data:
                rec.lead_officer = ward_data["lead_officer"]
            if "active_teams" in ward_data:
                teams = ward_data["active_teams"]
                rec.active_teams = json.dumps(teams) if isinstance(teams, list) else str(teams)
            return {
                "ward_code": rec.ward_code,
                "ward_name": rec.ward_name,
                "lead_officer": rec.lead_officer,
                "active_teams": json.loads(rec.active_teams) if rec.active_teams else []
            }

    def assign_task(
        self,
        issue_id: str,
        assignment_data: Dict[str, Any],
        actor: str = "Abhinay",
        role: str = "inspector"
    ) -> Optional[Issue]:
        with self._get_session() as session:
            stmt = select(IssueRecord).where(IssueRecord.id == issue_id)
            record = session.scalar(stmt)
            if record is None:
                return None

            issue = Issue.model_validate_json(record.data_json)
            _ensure_timeline(issue)

            now_iso = datetime.now(timezone.utc).isoformat()
            sched_date = assignment_data.get("scheduled_date")
            team_name = assignment_data.get("team_name") or "Municipal Operations Crew"
            dept = assignment_data.get("department") or issue.department
            pri = assignment_data.get("priority") or (issue.priorityLevel.value if hasattr(issue.priorityLevel, "value") else str(issue.priorityLevel))
            instructions = assignment_data.get("instructions")
            assigned_off = assignment_data.get("assigned_officer") or actor

            assignment = TaskAssignment(
                department=dept,
                team_name=team_name,
                team_id=assignment_data.get("team_id"),
                assigned_officer=assigned_off,
                priority=pri,
                scheduled_date=sched_date,
                instructions=instructions,
                assigned_at=now_iso,
                assigned_by=actor
            )
            issue.assignment = assignment
            issue.department = dept

            new_status = IssueStatus.SCHEDULED if sched_date else IssueStatus.ASSIGNED
            issue.status = new_status

            desc = f"Task assigned to {team_name} by {actor} ({role}). Department: {dept}."
            if sched_date:
                desc += f" Scheduled Work Date: {sched_date}."
            if instructions:
                desc += f" Instructions: {instructions}."

            event = TimelineEvent(
                id=f"evt-asgn-{now_iso[-6:]}",
                event_type="TEAM_ASSIGNED",
                title=f"Task Assigned: {team_name}",
                description=desc,
                actor=actor,
                role=role,
                timestamp=now_iso,
                metadata={"team_id": assignment.team_id, "scheduled_date": sched_date}
            )
            issue.timeline.append(event)
            issue.statusHistory.append({
                "status": new_status.value,
                "timestamp": now_iso,
                "actor": actor,
                "note": desc
            })

            record.status = new_status.value
            record.department = dept
            record.data_json = issue.model_dump_json()
            return issue

    def schedule_task(
        self,
        issue_id: str,
        scheduled_date: str,
        schedule_type: str = "WORK",
        instructions: Optional[str] = None,
        actor: str = "Abhinay",
        role: str = "inspector"
    ) -> Optional[Issue]:
        with self._get_session() as session:
            stmt = select(IssueRecord).where(IssueRecord.id == issue_id)
            record = session.scalar(stmt)
            if record is None:
                return None

            issue = Issue.model_validate_json(record.data_json)
            _ensure_timeline(issue)

            now_iso = datetime.now(timezone.utc).isoformat()
            if issue.assignment:
                issue.assignment.scheduled_date = scheduled_date
                if instructions:
                    issue.assignment.instructions = instructions
            else:
                issue.assignment = TaskAssignment(
                    department=issue.department,
                    team_name="Municipal Operations Team",
                    assigned_officer=actor,
                    scheduled_date=scheduled_date,
                    instructions=instructions,
                    assigned_at=now_iso,
                    assigned_by=actor
                )

            issue.status = IssueStatus.SCHEDULED
            event_type = "WORK_SCHEDULED" if schedule_type.upper() == "WORK" else "INSPECTION_SCHEDULED"
            title = f"{schedule_type.capitalize()} Scheduled for {scheduled_date}"
            desc = instructions or f"{schedule_type.capitalize()} scheduled for {scheduled_date} by {actor}."

            event = TimelineEvent(
                id=f"evt-sched-{now_iso[-6:]}",
                event_type=event_type,
                title=title,
                description=desc,
                actor=actor,
                role=role,
                timestamp=now_iso,
                metadata={"scheduled_date": scheduled_date, "schedule_type": schedule_type}
            )
            issue.timeline.append(event)
            issue.statusHistory.append({
                "status": IssueStatus.SCHEDULED.value,
                "timestamp": now_iso,
                "actor": actor,
                "note": title
            })

            record.status = IssueStatus.SCHEDULED.value
            record.data_json = issue.model_dump_json()
            return issue

    def record_action(
        self,
        issue_id: str,
        action_type: str,
        action_data: Dict[str, Any],
        actor: str = "Abhinay",
        role: str = "inspector"
    ) -> Optional[Issue]:
        with self._get_session() as session:
            stmt = select(IssueRecord).where(IssueRecord.id == issue_id)
            record = session.scalar(stmt)
            if record is None:
                return None

            issue = Issue.model_validate_json(record.data_json)
            _ensure_timeline(issue)

            now_iso = datetime.now(timezone.utc).isoformat()
            act_upper = action_type.upper()

            if act_upper == "RECORD_TEMPORARY_MEASURES":
                measures = action_data.get("measures", [])
                notes = action_data.get("notes", "")
                issue.temporary_measures = TemporaryMeasures(
                    measures=measures,
                    notes=notes,
                    recorded_at=now_iso,
                    recorded_by=actor
                )
                measures_str = ", ".join(measures) if measures else "Safety perimeter established"
                title = "Temporary Safety Measures Implemented"
                desc = f"Safety measures deployed: {measures_str}."
                if notes:
                    desc += f" Notes: {notes}."
                evt = TimelineEvent(
                    id=f"evt-act-{now_iso[-6:]}",
                    event_type="TEMPORARY_MEASURES_TAKEN",
                    title=title,
                    description=desc,
                    actor=actor,
                    role=role,
                    timestamp=now_iso,
                    metadata={"measures": measures}
                )
                issue.timeline.append(evt)
                if issue.status not in (IssueStatus.RESOLVED, IssueStatus.VERIFIED_CLOSED):
                    issue.status = IssueStatus.ACTION_IN_PROGRESS
                    record.status = IssueStatus.ACTION_IN_PROGRESS.value

            elif act_upper == "INSPECTION_COMPLETED":
                notes = action_data.get("notes") or "On-site road inspection completed."
                photo_url = action_data.get("photo_url")
                title = "On-Site Inspection Completed"
                evt = TimelineEvent(
                    id=f"evt-act-{now_iso[-6:]}",
                    event_type="INSPECTION_COMPLETED",
                    title=title,
                    description=notes,
                    actor=actor,
                    role=role,
                    timestamp=now_iso,
                    evidence_url=photo_url
                )
                issue.timeline.append(evt)
                issue.status = IssueStatus.ACTION_IN_PROGRESS
                record.status = IssueStatus.ACTION_IN_PROGRESS.value

            elif act_upper in ("WORK_STARTED", "PROGRESS_UPDATE", "CLEANUP_PROGRESS"):
                stage = action_data.get("stage") or "Field operations active"
                notes = action_data.get("notes", "")
                desc = f"Stage: {stage}."
                if notes:
                    desc += f" Notes: {notes}."
                title = f"Progress Update: {stage}"
                evt = TimelineEvent(
                    id=f"evt-act-{now_iso[-6:]}",
                    event_type="PROGRESS_UPDATE",
                    title=title,
                    description=desc,
                    actor=actor,
                    role=role,
                    timestamp=now_iso,
                    metadata={"stage": stage}
                )
                issue.timeline.append(evt)
                issue.status = IssueStatus.ACTION_IN_PROGRESS
                record.status = IssueStatus.ACTION_IN_PROGRESS.value

            elif act_upper == "SCHEDULE_WASTE_COLLECTION":
                sched_date = action_data.get("scheduled_date") or now_iso[:10]
                notes = action_data.get("notes") or "Waste collection dispatch scheduled."
                title = f"Waste Collection Scheduled for {sched_date}"
                if issue.assignment:
                    issue.assignment.scheduled_date = sched_date
                evt = TimelineEvent(
                    id=f"evt-act-{now_iso[-6:]}",
                    event_type="WORK_SCHEDULED",
                    title=title,
                    description=notes,
                    actor=actor,
                    role=role,
                    timestamp=now_iso,
                    metadata={"scheduled_date": sched_date}
                )
                issue.timeline.append(evt)
                issue.status = IssueStatus.SCHEDULED
                record.status = IssueStatus.SCHEDULED.value

            elif act_upper == "SCHEDULE_REPEAT_COLLECTION":
                freq = action_data.get("frequency") or "Weekly"
                next_date = action_data.get("scheduled_date")
                notes = action_data.get("notes", "")
                issue.repeat_collection = RepeatCollection(
                    is_scheduled=True,
                    frequency=freq,
                    next_collection_date=next_date,
                    instructions=notes,
                    scheduled_at=now_iso,
                    scheduled_by=actor
                )
                title = f"Repeat Collection Configured ({freq})"
                desc = f"Sanitation repeat schedule activated ({freq}). Next collection: {next_date or 'Next cycle'}."
                if notes:
                    desc += f" Notes: {notes}."
                evt = TimelineEvent(
                    id=f"evt-act-{now_iso[-6:]}",
                    event_type="REPEAT_COLLECTION_SCHEDULED",
                    title=title,
                    description=desc,
                    actor=actor,
                    role=role,
                    timestamp=now_iso,
                    metadata={"frequency": freq, "next_date": next_date}
                )
                issue.timeline.append(evt)

            record.data_json = issue.model_dump_json()
            return issue

    def complete_task(
        self,
        issue_id: str,
        completion_note: str,
        closure_reason: str = "Work executed to municipal standard",
        completion_photo_url: Optional[str] = None,
        actor: str = "Abhinay",
        role: str = "inspector"
    ) -> Optional[Issue]:
        if not completion_note or not completion_note.strip():
            raise ValueError("A completion note is strictly required before closing the complaint.")

        with self._get_session() as session:
            stmt = select(IssueRecord).where(IssueRecord.id == issue_id)
            record = session.scalar(stmt)
            if record is None:
                return None

            issue = Issue.model_validate_json(record.data_json)
            _ensure_timeline(issue)

            now_iso = datetime.now(timezone.utc).isoformat()
            issue.completion_details = CompletionDetails(
                completed_at=now_iso,
                completed_by=actor,
                completion_note=completion_note.strip(),
                completion_photo_url=completion_photo_url,
                closure_reason=closure_reason
            )
            issue.status = IssueStatus.RESOLVED

            desc = f"Closure Reason: {closure_reason}. Note: {completion_note.strip()}"
            evt = TimelineEvent(
                id=f"evt-comp-{now_iso[-6:]}",
                event_type="WORK_COMPLETED",
                title="Complaint Completed & Resolved",
                description=desc,
                actor=actor,
                role=role,
                timestamp=now_iso,
                evidence_url=completion_photo_url,
                metadata={"closure_reason": closure_reason}
            )
            issue.timeline.append(evt)
            issue.statusHistory.append({
                "status": IssueStatus.RESOLVED.value,
                "timestamp": now_iso,
                "actor": actor,
                "note": desc
            })

            record.status = IssueStatus.RESOLVED.value
            record.data_json = issue.model_dump_json()
            return issue

    def reopen_task(
        self,
        issue_id: str,
        reason: str,
        note: Optional[str] = None,
        actor: str = "Abhinay",
        role: str = "inspector"
    ) -> Optional[Issue]:
        if not reason or not reason.strip():
            raise ValueError("Reopen reason is required.")

        with self._get_session() as session:
            stmt = select(IssueRecord).where(IssueRecord.id == issue_id)
            record = session.scalar(stmt)
            if record is None:
                return None

            issue = Issue.model_validate_json(record.data_json)
            _ensure_timeline(issue)

            now_iso = datetime.now(timezone.utc).isoformat()
            issue.status = IssueStatus.REOPENED

            desc = f"Complaint reopened by {actor} ({role}). Reason: {reason.strip()}."
            if note:
                desc += f" Notes: {note.strip()}."

            evt = TimelineEvent(
                id=f"evt-reopen-{now_iso[-6:]}",
                event_type="REOPENED",
                title=f"Complaint Reopened ({reason.strip()})",
                description=desc,
                actor=actor,
                role=role,
                timestamp=now_iso,
                metadata={"reason": reason}
            )
            issue.timeline.append(evt)
            issue.statusHistory.append({
                "status": IssueStatus.REOPENED.value,
                "timestamp": now_iso,
                "actor": actor,
                "note": desc
            })

            record.status = IssueStatus.REOPENED.value
            record.data_json = issue.model_dump_json()
            return issue

    def record_feedback(
        self,
        issue_id: str,
        feedback: str,
        note: Optional[str] = None,
        citizen_name: str = "Abhinay"
    ) -> Optional[Issue]:
        feed_upper = feedback.strip().upper()
        if feed_upper not in ("CONFIRMED_RESOLVED", "REOPEN_REQUESTED"):
            raise ValueError("Feedback must be either 'CONFIRMED_RESOLVED' or 'REOPEN_REQUESTED'.")

        with self._get_session() as session:
            stmt = select(IssueRecord).where(IssueRecord.id == issue_id)
            record = session.scalar(stmt)
            if record is None:
                return None

            issue = Issue.model_validate_json(record.data_json)
            _ensure_timeline(issue)

            now_iso = datetime.now(timezone.utc).isoformat()
            issue.citizen_feedback = CitizenFeedback(
                status=feed_upper,
                note=note.strip() if note else None,
                submitted_at=now_iso,
                citizen_name=citizen_name
            )

            if feed_upper == "CONFIRMED_RESOLVED":
                desc = note.strip() if note else f"Citizen {citizen_name} confirmed the issue has been resolved to satisfaction."
                evt = TimelineEvent(
                    id=f"evt-feed-{now_iso[-6:]}",
                    event_type="CITIZEN_CONFIRMED",
                    title="Citizen Confirmed Resolution",
                    description=desc,
                    actor=citizen_name,
                    role="citizen",
                    timestamp=now_iso
                )
                issue.timeline.append(evt)
            else:
                issue.status = IssueStatus.REOPENED
                record.status = IssueStatus.REOPENED.value
                desc = note.strip() if note else f"Citizen {citizen_name} reported that the issue remains unresolved."
                evt = TimelineEvent(
                    id=f"evt-feed-{now_iso[-6:]}",
                    event_type="CITIZEN_REOPEN_REQUESTED",
                    title="Citizen Reopen Request: Issue Unresolved",
                    description=desc,
                    actor=citizen_name,
                    role="citizen",
                    timestamp=now_iso
                )
                issue.timeline.append(evt)
                issue.statusHistory.append({
                    "status": IssueStatus.REOPENED.value,
                    "timestamp": now_iso,
                    "actor": citizen_name,
                    "note": f"Citizen feedback: {desc}"
                })

            record.data_json = issue.model_dump_json()
            return issue

    def get_operations_kpis(self) -> Dict[str, Any]:
        with self._get_session() as session:
            records = session.scalars(select(IssueRecord)).all()
            now = datetime.now(timezone.utc)
            current_year = now.year
            current_month = now.month

            unassigned = 0
            high_priority = 0
            work_in_progress = 0
            resolved_this_month = 0
            roads_count = 0
            sanitation_count = 0
            ward_counts: Dict[str, int] = {
                "N-Ward": 0,
                "L-Ward": 0,
                "G/North": 0,
                "K/West": 0,
                "NMMC-Vashi": 0
            }

            for r in records:
                try:
                    issue = Issue.model_validate_json(r.data_json)
                except Exception:
                    continue

                # Category workload
                cat_str = str(r.category)
                if "Road" in cat_str or "Footpath" in cat_str:
                    roads_count += 1
                elif "Sanitation" in cat_str or "Garbage" in cat_str or "Waste" in cat_str:
                    sanitation_count += 1

                # Ward distribution
                w = r.ward or "N-Ward"
                ward_counts[w] = ward_counts.get(w, 0) + 1

                # High priority (CRITICAL, HIGH, or priority_score >= 65)
                if r.priority_level in ("CRITICAL", "HIGH") or r.priority_score >= 65:
                    high_priority += 1

                # Unassigned complaints (no assignment team and not yet resolved)
                has_assignment = bool(issue.assignment and issue.assignment.team_name)
                is_resolved = r.status in ("RESOLVED", "VERIFIED_CLOSED", "Verified Closed")
                if not has_assignment and not is_resolved:
                    unassigned += 1

                # Work in progress
                if r.status in ("ACTION IN PROGRESS", "In Progress", "ASSIGNED", "SCHEDULED", "AWAITING CONFIRMATION", "VERIFICATION"):
                    work_in_progress += 1

                # Complaints resolved this month
                if is_resolved:
                    try:
                        dt = datetime.fromisoformat(r.timestamp.replace("Z", "+00:00"))
                        if dt.year == current_year and dt.month == current_month:
                            resolved_this_month += 1
                        else:
                            resolved_this_month += 1
                    except Exception:
                        resolved_this_month += 1

            return {
                "unassigned_complaints": unassigned,
                "high_priority_complaints": high_priority,
                "work_in_progress": work_in_progress,
                "resolved_this_month": resolved_this_month,
                "category_workload": {
                    "roads": roads_count,
                    "sanitation": sanitation_count,
                    "total": roads_count + sanitation_count
                },
                "ward_distribution": ward_counts,
                "total_complaints": len(records)
            }

    # --------------------------------------------------------------------------
    # AI Field Guidance & Decision Lifecycle
    # --------------------------------------------------------------------------

    def get_or_generate_field_guidance(
        self,
        issue_id: str,
        force_regenerate: bool = False
    ) -> Optional[FieldGuidanceResult]:
        issue = self.get_issue(issue_id)
        if not issue:
            return None

        engine = GuidanceEngine()
        guidance = engine.generate_guidance(issue, force_regenerate=force_regenerate)
        if not issue.metadata:
            issue.metadata = {}
        issue.metadata["field_guidance"] = guidance.model_dump()
        self.update_issue(issue)
        return guidance

    def record_guidance_decision(
        self,
        issue_id: str,
        item_id: str,
        decision: OfficerDecisionType,
        edited_text: Optional[str] = None,
        reason: Optional[str] = None,
        actor: str = "Abhinay",
        role: str = "inspector"
    ) -> Optional[FieldGuidanceResult]:
        issue = self.get_issue(issue_id)
        if not issue:
            return None

        _ensure_timeline(issue)

        if not issue.metadata or "field_guidance" not in issue.metadata:
            engine = GuidanceEngine()
            guidance = engine.generate_guidance(issue, force_regenerate=True)
        else:
            try:
                guidance = FieldGuidanceResult.model_validate(issue.metadata["field_guidance"])
            except Exception:
                engine = GuidanceEngine()
                guidance = engine.generate_guidance(issue, force_regenerate=True)

        target_item = None
        for item in guidance.immediate_precautions + guidance.recommended_field_actions:
            if item.id == item_id:
                target_item = item
                break

        if not target_item:
            logger.warning(f"Guidance item {item_id} not found in issue {issue_id}")
            return guidance

        now_iso = datetime.now(timezone.utc).isoformat()
        target_item.officer_decision = decision
        target_item.decided_by = actor
        target_item.decided_at = now_iso

        if decision == OfficerDecisionType.EDITED:
            target_item.edited_text = edited_text
        elif decision == OfficerDecisionType.DISMISSED:
            target_item.decision_reason = reason

        # Process adoption: append instruction and log timeline event
        if decision in (OfficerDecisionType.ACCEPTED, OfficerDecisionType.EDITED):
            inst_text = (
                target_item.edited_text
                if decision == OfficerDecisionType.EDITED and target_item.edited_text
                else f"{target_item.title}: {target_item.description}"
            )
            bullet = f"• [Adopted Guidance]: {inst_text}"

            if issue.assignment:
                if issue.assignment.instructions:
                    issue.assignment.instructions += f"\n{bullet}"
                else:
                    issue.assignment.instructions = bullet
            else:
                # Do NOT automatically assign teams or change status to ASSIGNED/CLOSED
                # Store instructions in assignment with empty team_name so it remains unassigned
                issue.assignment = TaskAssignment(
                    department=issue.department,
                    team_name="",
                    assigned_officer=actor,
                    instructions=bullet,
                    assigned_at=now_iso,
                    assigned_by=actor
                )

            ev_id = f"evt-guide-{uuid.uuid4().hex[:6]}"
            evt = TimelineEvent(
                id=ev_id,
                event_type="FIELD_GUIDANCE_ACCEPTED",
                title=f"Field Guidance Adopted: {target_item.title}",
                description=f"{actor} adopted statutory field guidance item '{target_item.title}' referencing {target_item.citation.doc_title} ({target_item.citation.section}).",
                actor=actor,
                role=role,
                timestamp=now_iso,
                metadata={
                    "guidance_item_id": item_id,
                    "citation_doc": target_item.citation.doc_id,
                    "citation_section": target_item.citation.section,
                    "decision": decision.value if hasattr(decision, "value") else str(decision)
                }
            )
            issue.timeline.append(evt)

        elif decision == OfficerDecisionType.DISMISSED:
            ev_id = f"evt-guide-{uuid.uuid4().hex[:6]}"
            evt = TimelineEvent(
                id=ev_id,
                event_type="FIELD_GUIDANCE_DISMISSED",
                title=f"Field Guidance Dismissed: {target_item.title}",
                description=f"{actor} dismissed guidance item '{target_item.title}'. Reason: {reason or 'Not applicable to current site conditions'}.",
                actor=actor,
                role=role,
                timestamp=now_iso,
                metadata={
                    "guidance_item_id": item_id,
                    "reason": reason
                }
            )
            issue.timeline.append(evt)

        if not issue.metadata:
            issue.metadata = {}
        issue.metadata["field_guidance"] = guidance.model_dump()
        self.update_issue(issue)
        return guidance




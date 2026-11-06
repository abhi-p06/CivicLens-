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
    WardConfigRecord,
    MunicipalAuthorityRecord,
    AdminZoneRecord,
    AdminWardRecord,
    SubWardRecord,
    LocalityBeatRecord,
    OfficerJurisdictionRecord,
    JurisdictionAuditLogRecord
)
from app.modules.gis.hierarchy_data import (
    MUNICIPAL_AUTHORITIES,
    ADMINISTRATIVE_ZONES,
    ADMINISTRATIVE_WARDS,
    CIVILENS_OPERATIONAL_SUB_WARDS,
    LOCALITY_BEATS
)
from app.modules.gis.hierarchy_spatial import resolve_coordinates_hierarchy, check_ward_mismatch
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
        "sub_ward_id": "SW-BMC-N-01",
        "authority_id": "AUTH-BMC",
        "supervisor_name": "Supervisor R. Shinde",
        "capacity": 6,
        "contact_lead": "Supervisor R. Shinde",
    },
    {
        "id": "TEAM-ROAD-02",
        "name": "Central Pothole Emergency Unit",
        "department": "Road Infrastructure Maintenance",
        "category": "Roads & Footpaths",
        "status": "AVAILABLE",
        "ward": "ALL",
        "sub_ward_id": None,
        "authority_id": "AUTH-BMC",
        "supervisor_name": "Officer P. Mane",
        "capacity": 10,
        "contact_lead": "Officer P. Mane",
    },
    {
        "id": "TEAM-ROAD-03",
        "name": "Heavy Resurfacing Crew (Western Express)",
        "department": "Road Infrastructure Maintenance",
        "category": "Roads & Footpaths",
        "status": "BUSY",
        "ward": "K/West",
        "sub_ward_id": "SW-BMC-KW-01",
        "authority_id": "AUTH-BMC",
        "supervisor_name": "Eng. V. Kadam",
        "capacity": 8,
        "contact_lead": "Eng. V. Kadam",
    },
    {
        "id": "TEAM-ROAD-04",
        "name": "Navi Mumbai Municipal Road Fleet",
        "department": "Road Infrastructure Maintenance",
        "category": "Roads & Footpaths",
        "status": "AVAILABLE",
        "ward": "NMMC-Vashi",
        "sub_ward_id": "SW-NMMC-V-01",
        "authority_id": "AUTH-NMMC",
        "supervisor_name": "Supervisor S. Sawant",
        "capacity": 6,
        "contact_lead": "Supervisor S. Sawant",
    },
    {
        "id": "TEAM-SWM-01",
        "name": "Solid Waste Rapid Response (Ward N)",
        "department": "Solid Waste Management",
        "category": "Sanitation & Garbage",
        "status": "AVAILABLE",
        "ward": "N-Ward",
        "sub_ward_id": "SW-BMC-N-01",
        "authority_id": "AUTH-BMC",
        "supervisor_name": "Inspector A. Jadhav",
        "capacity": 6,
        "contact_lead": "Inspector A. Jadhav",
    },
    {
        "id": "TEAM-SWM-02",
        "name": "Ward G/North Sanitation Fleet",
        "department": "Solid Waste Management",
        "category": "Sanitation & Garbage",
        "status": "AVAILABLE",
        "ward": "G/North",
        "sub_ward_id": "SW-BMC-GN-01",
        "authority_id": "AUTH-BMC",
        "supervisor_name": "Foreman D. Kamble",
        "capacity": 6,
        "contact_lead": "Foreman D. Kamble",
    },
    {
        "id": "TEAM-SWM-03",
        "name": "Bulky Litter & Debris Unit (Kurla/L-Ward)",
        "department": "Solid Waste Management",
        "category": "Sanitation & Garbage",
        "status": "BUSY",
        "ward": "L-Ward",
        "sub_ward_id": "SW-BMC-L-01",
        "authority_id": "AUTH-BMC",
        "supervisor_name": "Supervisor M. Ansari",
        "capacity": 6,
        "contact_lead": "Supervisor M. Ansari",
    },
    {
        "id": "TEAM-SWM-04",
        "name": "NMMC Vashi Sanitation Taskforce",
        "department": "Solid Waste Management",
        "category": "Sanitation & Garbage",
        "status": "AVAILABLE",
        "ward": "NMMC-Vashi",
        "sub_ward_id": "SW-NMMC-V-01",
        "authority_id": "AUTH-NMMC",
        "supervisor_name": "Officer B. Patil",
        "capacity": 6,
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

def build_hierarchical_routing_path(
    authority_name: Optional[str] = None,
    zone_name: Optional[str] = None,
    ward_name: Optional[str] = None,
    sub_ward_name: Optional[str] = None,
    locality_name: Optional[str] = None,
    department: Optional[str] = None,
    supervisor_name: Optional[str] = None,
    crew_name: Optional[str] = None,
) -> str:
    auth = authority_name or "Pending Allocation"
    if auth != "Pending Allocation":
        if "Brihanmumbai" in auth and "BMC" not in auth:
            auth = f"{auth} (BMC)"
        elif "Navi Mumbai" in auth and "NMMC" not in auth:
            auth = f"{auth} (NMMC)"
    zone = zone_name or "Pending Allocation"
    ward = ward_name or "Pending Allocation"
    sub_ward = sub_ward_name if (sub_ward_name and "PENDING" not in str(sub_ward_name).upper()) else "Pending Allocation"
    loc = locality_name or "Pending Allocation"
    dept = department or "Pending Allocation"
    sup = supervisor_name or "Pending Allocation"
    crew = crew_name or "Pending Allocation"
    return f"{auth} → {zone} → {ward} → {sub_ward} → {loc} → {dept} → {sup} → {crew}"

def _ensure_hierarchy(issue: Issue) -> Issue:
    if not getattr(issue, "sub_ward_id", None) or not getattr(issue, "routing_path", None):
        res = resolve_coordinates_hierarchy(issue.latitude, issue.longitude)
        if res.get("is_valid"):
            issue.authority_id = res.get("authority_id", "AUTH-BMC")
            issue.authority_code = res.get("authority_code", "BMC")
            issue.authority_name = res.get("authority_name", "Brihanmumbai Municipal Corporation")
            issue.zone_id = res.get("zone_id")
            issue.zone_name = res.get("zone_name")
            issue.ward_id = res.get("ward_id")
            if not issue.ward or issue.ward in ("None", "ALL", "HQ-Ward"):
                issue.ward = res.get("ward_code", "N-Ward")
            issue.sub_ward_id = res.get("sub_ward_id")
            issue.sub_ward_name = res.get("sub_ward_name")
            issue.locality_id = res.get("locality_id")
            issue.locality_name = res.get("locality_name")
            if not getattr(issue, "supervisor_name", None):
                issue.supervisor_name = res.get("supervisor_name")
            if not getattr(issue, "routing_path", None):
                dept_name = issue.department or ("Road Infrastructure Maintenance" if "Road" in str(issue.category) else "Solid Waste Management")
                crew_name = issue.assignment.team_name if (issue.assignment and issue.assignment.team_name) else None
                issue.routing_path = build_hierarchical_routing_path(
                    authority_name=issue.authority_name or issue.authority_code,
                    zone_name=issue.zone_name,
                    ward_name=issue.ward,
                    sub_ward_name=issue.sub_ward_name,
                    locality_name=issue.locality_name or issue.location,
                    department=dept_name,
                    supervisor_name=issue.supervisor_name,
                    crew_name=crew_name,
                )
    return issue

def _ensure_timeline(issue: Issue) -> Issue:
    _ensure_hierarchy(issue)
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
            authority_id=getattr(issue, "authority_id", "AUTH-BMC"),
            authority_code=getattr(issue, "authority_code", "BMC"),
            authority_name=getattr(issue, "authority_name", "Brihanmumbai Municipal Corporation"),
            zone_id=getattr(issue, "zone_id", None),
            zone_name=getattr(issue, "zone_name", None),
            ward_id=getattr(issue, "ward_id", None),
            sub_ward_id=getattr(issue, "sub_ward_id", None),
            sub_ward_name=getattr(issue, "sub_ward_name", None),
            locality_id=getattr(issue, "locality_id", None),
            locality_name=getattr(issue, "locality_name", None),
            supervisor_name=getattr(issue, "supervisor_name", None),
            routing_path=getattr(issue, "routing_path", None),
            jurisdiction_verified=bool(getattr(issue, "jurisdiction_verified", True)),
            jurisdiction_review_required=bool(getattr(issue, "jurisdiction_review_required", False)),
            jurisdiction_review_reason=getattr(issue, "jurisdiction_review_reason", None),
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
        record.authority_id = getattr(issue, "authority_id", record.authority_id)
        record.authority_code = getattr(issue, "authority_code", record.authority_code)
        record.authority_name = getattr(issue, "authority_name", record.authority_name)
        record.zone_id = getattr(issue, "zone_id", record.zone_id)
        record.zone_name = getattr(issue, "zone_name", record.zone_name)
        record.ward_id = getattr(issue, "ward_id", record.ward_id)
        record.sub_ward_id = getattr(issue, "sub_ward_id", record.sub_ward_id)
        record.sub_ward_name = getattr(issue, "sub_ward_name", record.sub_ward_name)
        record.locality_id = getattr(issue, "locality_id", record.locality_id)
        record.locality_name = getattr(issue, "locality_name", record.locality_name)
        record.supervisor_name = getattr(issue, "supervisor_name", record.supervisor_name)
        record.routing_path = getattr(issue, "routing_path", record.routing_path)
        record.jurisdiction_verified = bool(getattr(issue, "jurisdiction_verified", True))
        record.jurisdiction_review_required = bool(getattr(issue, "jurisdiction_review_required", False))
        record.jurisdiction_review_reason = getattr(issue, "jurisdiction_review_reason", record.jurisdiction_review_reason)
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
            citizen_pwd = os.getenv("CIVILENS_DEV_CITIZEN_PASSWORD", "Citizen@123")
            inspector_pwd = os.getenv("CIVILENS_DEV_INSPECTOR_PASSWORD", "Inspector@123")
            admin_pwd = os.getenv("CIVILENS_DEV_ADMIN_PASSWORD", "Admin@123")

            defaults = [
                ("CITIZEN-001", "citizen", "citizen@civilens.org", "Abhinay", citizen_pwd, "citizen"),
                ("INSP-MUMBAI-01", "inspector", "inspector@civilens.org", "Abhinay", inspector_pwd, "inspector"),
                ("INSP-NMMC-01", "inspector_nmmc", "inspector.nmmc@civilens.org", "Officer Deshmukh", inspector_pwd, "inspector"),
                ("ADMIN-SYS-01", "admin", "admin@civilens.org", "Municipal Operations Administrator", admin_pwd, "admin"),
            ]
            inserted = 0
            for uid, uname, uemail, uname_full, pwd, urole in defaults:
                rec = session.get(UserRecord, uid)
                if not rec:
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
            if inserted > 0:
                session.commit()
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
                        sub_ward_id=t.get("sub_ward_id"),
                        authority_id=t.get("authority_id", "AUTH-BMC"),
                        supervisor_name=t.get("supervisor_name") or t.get("contact_lead"),
                        capacity=t.get("capacity", 6),
                        contact_lead=t.get("contact_lead", "Duty Supervisor"),
                        active_tasks_count=t.get("active_tasks_count", 0)
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

        self.seed_hierarchy_if_empty()

    def list_teams(
        self,
        category: Optional[str] = None,
        ward: Optional[str] = None,
        sub_ward_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        self.seed_default_teams_and_wards_if_empty()
        with self._get_session() as session:
            stmt = select(TeamRecord)
            if category:
                stmt = stmt.where(TeamRecord.category == category)
            if ward:
                stmt = stmt.where((TeamRecord.ward == ward) | (TeamRecord.ward == "ALL"))
            if sub_ward_id:
                stmt = stmt.where(TeamRecord.sub_ward_id == sub_ward_id)
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
                    "sub_ward_id": t.sub_ward_id,
                    "authority_id": t.authority_id,
                    "supervisor_name": t.supervisor_name,
                    "capacity": t.capacity,
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
                "sub_ward_id": t.sub_ward_id,
                "authority_id": t.authority_id,
                "supervisor_name": t.supervisor_name,
                "capacity": t.capacity,
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
                sub_ward_id=team_data.get("sub_ward_id"),
                authority_id=team_data.get("authority_id", "AUTH-BMC"),
                supervisor_name=team_data.get("supervisor_name"),
                capacity=int(team_data.get("capacity", 6)),
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
                "sub_ward_id": rec.sub_ward_id,
                "authority_id": rec.authority_id,
                "supervisor_name": rec.supervisor_name,
                "capacity": rec.capacity,
                "contact_lead": rec.contact_lead,
                "active_tasks_count": 0
            }

    def update_team(self, team_id: str, team_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        with self._get_session() as session:
            stmt = select(TeamRecord).where(TeamRecord.id == team_id)
            rec = session.scalar(stmt)
            if not rec:
                return None
            if "name" in team_data and team_data["name"] is not None:
                rec.name = team_data["name"]
            if "department" in team_data and team_data["department"] is not None:
                rec.department = team_data["department"]
            if "category" in team_data and team_data["category"] is not None:
                rec.category = team_data["category"]
            if "status" in team_data and team_data["status"] is not None:
                rec.status = str(team_data["status"]).upper()
            if "ward" in team_data and team_data["ward"] is not None:
                rec.ward = team_data["ward"]
            if "sub_ward_id" in team_data:
                rec.sub_ward_id = team_data["sub_ward_id"]
            if "authority_id" in team_data and team_data["authority_id"] is not None:
                rec.authority_id = team_data["authority_id"]
            if "supervisor_name" in team_data:
                rec.supervisor_name = team_data["supervisor_name"]
            if "capacity" in team_data and team_data["capacity"] is not None:
                rec.capacity = int(team_data["capacity"])
            if "contact_lead" in team_data and team_data["contact_lead"] is not None:
                rec.contact_lead = team_data["contact_lead"]
            return {
                "id": rec.id,
                "name": rec.name,
                "department": rec.department,
                "category": rec.category,
                "status": rec.status,
                "ward": rec.ward,
                "sub_ward_id": rec.sub_ward_id,
                "authority_id": rec.authority_id,
                "supervisor_name": rec.supervisor_name,
                "capacity": rec.capacity,
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
                adm_ward = session.scalar(select(AdminWardRecord).where((AdminWardRecord.ward_code == ward_code) | (AdminWardRecord.id == ward_code)))
                if adm_ward:
                    adm_ward.lead_officer = ward_data["lead_officer"]
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

            # Track field team task allocation and availability
            old_team_id = issue.assignment.team_id if (issue.assignment and issue.assignment.team_id) else None
            new_team_id = assignment_data.get("team_id")
            if old_team_id and old_team_id != new_team_id:
                old_team = session.scalar(select(TeamRecord).where(TeamRecord.id == old_team_id))
                if old_team:
                    old_team.active_tasks_count = max(0, old_team.active_tasks_count - 1)
                    if old_team.active_tasks_count < old_team.capacity and old_team.status == "BUSY":
                        old_team.status = "AVAILABLE"

            if new_team_id:
                new_team = session.scalar(select(TeamRecord).where(TeamRecord.id == new_team_id))
                if new_team:
                    new_team.active_tasks_count += 1
                    if new_team.active_tasks_count >= new_team.capacity:
                        new_team.status = "BUSY"

            assignment = TaskAssignment(
                department=dept,
                team_name=team_name,
                team_id=new_team_id,
                assigned_officer=assigned_off,
                priority=pri,
                scheduled_date=sched_date,
                instructions=instructions,
                assigned_at=now_iso,
                assigned_by=actor
            )
            issue.assignment = assignment
            issue.department = dept
            issue.supervisor_name = assigned_off

            # Rebuild authoritative 8-tier routing path
            issue.routing_path = build_hierarchical_routing_path(
                authority_name=issue.authority_name or issue.authority_code,
                zone_name=issue.zone_name,
                ward_name=issue.ward,
                sub_ward_name=issue.sub_ward_name,
                locality_name=issue.locality_name or issue.location,
                department=dept,
                supervisor_name=assigned_off,
                crew_name=team_name
            )

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
            record.supervisor_name = assigned_off
            record.routing_path = issue.routing_path
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

            # Release field team capacity upon completion
            if issue.assignment and issue.assignment.team_id:
                team_rec = session.scalar(select(TeamRecord).where(TeamRecord.id == issue.assignment.team_id))
                if team_rec:
                    team_rec.active_tasks_count = max(0, team_rec.active_tasks_count - 1)
                    if team_rec.active_tasks_count < team_rec.capacity and team_rec.status == "BUSY":
                        team_rec.status = "AVAILABLE"

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

            # Re-engage field team capacity upon reopening
            if issue.assignment and issue.assignment.team_id:
                team_rec = session.scalar(select(TeamRecord).where(TeamRecord.id == issue.assignment.team_id))
                if team_rec:
                    team_rec.active_tasks_count += 1
                    if team_rec.active_tasks_count >= team_rec.capacity:
                        team_rec.status = "BUSY"

            record.status = IssueStatus.REOPENED.value
            record.data_json = issue.model_dump_json()
            return issue

    def verify_jurisdiction(
        self,
        issue_id: str,
        actor: str = "Abhinay",
        role: str = "inspector",
        notes: Optional[str] = None
    ) -> Optional[Issue]:
        """
        Confirms geographical jurisdiction assignment,
        marking the complaint verified and recording a verification audit event.
        """
        with self._get_session() as session:
            stmt = select(IssueRecord).where(IssueRecord.id == issue_id)
            record = session.scalar(stmt)
            if record is None:
                return None

            issue = Issue.model_validate_json(record.data_json)
            _ensure_timeline(issue)

            now_iso = datetime.now(timezone.utc).isoformat()
            issue.jurisdiction_verified = True
            issue.jurisdiction_review_required = False
            issue.jurisdiction_review_reason = None

            desc = f"Geographical jurisdiction verified and confirmed by {actor} ({role})."
            if notes:
                desc += f" Field Note: {notes}."

            event = TimelineEvent(
                id=f"evt-geo-{now_iso[-6:]}",
                event_type="GEOGRAPHIC_VERIFIED",
                title="Geographical Assignment Verified",
                description=desc,
                actor=actor,
                role=role,
                timestamp=now_iso,
                metadata={
                    "authority": issue.authority_name or issue.authority_code,
                    "ward": issue.ward,
                    "sub_ward": issue.sub_ward_name,
                    "locality": issue.locality_name,
                    "notes": notes
                }
            )
            issue.timeline.append(event)
            record.jurisdiction_verified = True
            record.jurisdiction_review_required = False
            record.jurisdiction_review_reason = None
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

    # --------------------------------------------------------------------------
    # Hierarchical Ward Management, Sub-Ward Routing & Crew Allocation
    # --------------------------------------------------------------------------

    def seed_hierarchy_if_empty(self) -> None:
        init_db(self._session_factory().get_bind())
        with self._get_session() as session:
            auth_count = session.scalar(select(func.count()).select_from(MunicipalAuthorityRecord)) or 0
            if auth_count < len(MUNICIPAL_AUTHORITIES):
                for a in MUNICIPAL_AUTHORITIES:
                    rec = session.get(MunicipalAuthorityRecord, a["id"])
                    if not rec:
                        rec = MunicipalAuthorityRecord(
                            id=a["id"],
                            code=a["code"],
                            name=a["name"],
                            short_name=a.get("short_name"),
                            city=a["city"],
                            headquarters=a.get("headquarters"),
                            is_active=a.get("is_active", True),
                            boundary_geojson=json.dumps(a.get("boundary_geojson")) if a.get("boundary_geojson") else None
                        )
                        session.add(rec)
                    else:
                        rec.boundary_geojson = json.dumps(a.get("boundary_geojson")) if a.get("boundary_geojson") else None
                logger.info(f"Seeded/Updated {len(MUNICIPAL_AUTHORITIES)} municipal authorities (BMC & NMMC).")

            zone_count = session.scalar(select(func.count()).select_from(AdminZoneRecord)) or 0
            if zone_count < len(ADMINISTRATIVE_ZONES):
                for z in ADMINISTRATIVE_ZONES:
                    rec = session.get(AdminZoneRecord, z["id"])
                    if not rec:
                        rec = AdminZoneRecord(
                            id=z["id"],
                            authority_id=z["authority_id"],
                            code=z["code"],
                            name=z["name"],
                            zonal_officer=z.get("zonal_officer"),
                            is_active=z.get("is_active", True),
                            boundary_geojson=json.dumps(z.get("boundary_geojson")) if z.get("boundary_geojson") else None
                        )
                        session.add(rec)
                    else:
                        rec.boundary_geojson = json.dumps(z.get("boundary_geojson")) if z.get("boundary_geojson") else None
                logger.info(f"Seeded/Updated {len(ADMINISTRATIVE_ZONES)} administrative zones.")

            ward_count = session.scalar(select(func.count()).select_from(AdminWardRecord)) or 0
            if ward_count < len(ADMINISTRATIVE_WARDS):
                for w in ADMINISTRATIVE_WARDS:
                    stmt = select(AdminWardRecord).where(
                        (AdminWardRecord.ward_code == w["ward_code"]) | (AdminWardRecord.id == w["id"])
                    )
                    rec = session.scalar(stmt)
                    if not rec:
                        rec = AdminWardRecord(
                            id=w["id"],
                            authority_id=w["authority_id"],
                            zone_id=w.get("zone_id"),
                            ward_code=w["ward_code"],
                            ward_name=w["ward_name"],
                            office_address=w.get("office_address"),
                            lead_officer=w.get("lead_officer", "Abhinay"),
                            is_active=w.get("is_active", True),
                            boundary_geojson=json.dumps(w.get("boundary_geojson")) if w.get("boundary_geojson") else None
                        )
                        session.add(rec)
                    else:
                        rec.boundary_geojson = json.dumps(w.get("boundary_geojson")) if w.get("boundary_geojson") else None
                        rec.ward_name = w["ward_name"]
                        if w.get("office_address"):
                            rec.office_address = w["office_address"]
                session.commit()
                logger.info(f"Seeded/Updated {len(ADMINISTRATIVE_WARDS)} administrative wards.")

            for s in CIVILENS_OPERATIONAL_SUB_WARDS:
                rec = session.get(SubWardRecord, s["id"])
                if not rec:
                    rec = SubWardRecord(
                        id=s["id"],
                        ward_id=s["ward_id"],
                        authority_id=s["authority_id"],
                        sub_ward_code=s["sub_ward_code"],
                        name=s["name"],
                        is_official=False,
                        operational_type="CIVILENS_OPERATIONAL_SUB_WARD",
                        supervisor_name=s.get("supervisor_name", "Area Supervisor"),
                        default_road_team_id=s.get("default_road_team_id"),
                        default_swm_team_id=s.get("default_swm_team_id"),
                        is_active=s.get("is_active", True),
                        boundary_geojson=json.dumps(s.get("boundary_geojson")) if s.get("boundary_geojson") else None
                    )
                    session.add(rec)
                else:
                    # Preserve user modifications across server restarts
                    if not rec.boundary_geojson and s.get("boundary_geojson"):
                        rec.boundary_geojson = json.dumps(s.get("boundary_geojson"))
                    if not rec.supervisor_name and s.get("supervisor_name"):
                        rec.supervisor_name = s["supervisor_name"]
            session.commit()
            logger.info(f"Seeded/Synchronized {len(CIVILENS_OPERATIONAL_SUB_WARDS)} CIVILENS operational sub-wards.")

            loc_count = session.scalar(select(func.count()).select_from(LocalityBeatRecord)) or 0
            if loc_count == 0:
                for l in LOCALITY_BEATS:
                    rec = LocalityBeatRecord(
                        id=l["id"],
                        sub_ward_id=l["sub_ward_id"],
                        ward_id=l["ward_id"],
                        authority_id=l.get("authority_id", "AUTH-BMC"),
                        name=l["name"],
                        landmark=l.get("landmark"),
                        latitude=l["latitude"],
                        longitude=l["longitude"],
                        radius_meters=l.get("radius_meters", 500.0),
                        is_active=l.get("is_active", True)
                    )
                    session.add(rec)
                logger.info(f"Seeded {len(LOCALITY_BEATS)} operational locality beats.")

            # Assign default officer jurisdictions
            oj_bmc = session.scalar(select(OfficerJurisdictionRecord).where(OfficerJurisdictionRecord.user_id == "INSP-MUMBAI-01"))
            if not oj_bmc:
                oj = OfficerJurisdictionRecord(
                    id="OJ-INSP-01",
                    user_id="INSP-MUMBAI-01",
                    authority_id="AUTH-BMC",
                    ward_code="N-Ward",
                    sub_ward_id="SUB-BMC-N-01",
                    jurisdiction_level="WARD_OFFICER"
                )
                session.add(oj)

            oj_nmmc = session.scalar(select(OfficerJurisdictionRecord).where(OfficerJurisdictionRecord.user_id == "INSP-NMMC-01"))
            if not oj_nmmc:
                oj_n = OfficerJurisdictionRecord(
                    id="OJ-INSP-NMMC-01",
                    user_id="INSP-NMMC-01",
                    authority_id="AUTH-NMMC",
                    ward_code="NMMC-Belapur",
                    sub_ward_id="SUB-NMMC-B-01",
                    jurisdiction_level="WARD_OFFICER"
                )
                session.add(oj_n)

            # Update teams with authority_id and default sub_ward_id if missing
            team_recs = session.scalars(select(TeamRecord)).all()
            for tr in team_recs:
                if not tr.authority_id:
                    tr.authority_id = "AUTH-NMMC" if "NMMC" in (tr.ward or "") else "AUTH-BMC"
                if not tr.sub_ward_id:
                    if tr.ward == "N-Ward":
                        tr.sub_ward_id = "SUB-BMC-N-01"
                    elif tr.ward == "L-Ward":
                        tr.sub_ward_id = "SUB-BMC-L-01"
                    elif tr.ward == "G/North":
                        tr.sub_ward_id = "SUB-BMC-GN-01"
                    elif tr.ward == "K/West":
                        tr.sub_ward_id = "SUB-BMC-HW-01"
                    elif "Vashi" in (tr.ward or ""):
                        tr.sub_ward_id = "SUB-NMMC-V-01"

    def list_authorities(self) -> List[Dict[str, Any]]:
        self.seed_hierarchy_if_empty()
        with self._get_session() as session:
            stmt = select(MunicipalAuthorityRecord).where(MunicipalAuthorityRecord.is_active.is_(True)).order_by(MunicipalAuthorityRecord.name)
            records = session.scalars(stmt).all()
            return [
                {
                    "id": r.id,
                    "code": r.code,
                    "name": r.name,
                    "short_name": r.short_name,
                    "city": r.city,
                    "headquarters": r.headquarters,
                    "boundary_geojson": json.loads(r.boundary_geojson) if r.boundary_geojson else None
                }
                for r in records
            ]

    def list_admin_wards(self, authority_id: Optional[str] = None) -> List[Dict[str, Any]]:
        self.seed_hierarchy_if_empty()
        with self._get_session() as session:
            stmt = select(AdminWardRecord).where(AdminWardRecord.is_active.is_(True))
            if authority_id:
                stmt = stmt.where(AdminWardRecord.authority_id == authority_id)
            stmt = stmt.order_by(AdminWardRecord.ward_code)
            records = session.scalars(stmt).all()
            return [
                {
                    "id": r.id,
                    "authority_id": r.authority_id,
                    "zone_id": r.zone_id,
                    "ward_code": r.ward_code,
                    "ward_name": r.ward_name,
                    "office_address": r.office_address,
                    "lead_officer": r.lead_officer,
                    "boundary_geojson": json.loads(r.boundary_geojson) if r.boundary_geojson else None
                }
                for r in records
            ]

    def list_sub_wards(self, ward_code: Optional[str] = None, ward_id: Optional[str] = None) -> List[Dict[str, Any]]:
        self.seed_hierarchy_if_empty()
        with self._get_session() as session:
            stmt = select(SubWardRecord).where(SubWardRecord.is_active.is_(True))
            if ward_id:
                stmt = stmt.where(SubWardRecord.ward_id == ward_id)
            elif ward_code:
                # Find ward_id from ward_code
                w = session.scalar(select(AdminWardRecord).where(AdminWardRecord.ward_code == ward_code))
                if w:
                    stmt = stmt.where(SubWardRecord.ward_id == w.id)
            stmt = stmt.order_by(SubWardRecord.sub_ward_code)
            records = session.scalars(stmt).all()
            return [
                {
                    "id": r.id,
                    "ward_id": r.ward_id,
                    "authority_id": r.authority_id,
                    "sub_ward_code": r.sub_ward_code,
                    "name": r.name,
                    "is_official": r.is_official,
                    "operational_type": r.operational_type,
                    "supervisor_name": r.supervisor_name,
                    "default_road_team_id": r.default_road_team_id,
                    "default_swm_team_id": r.default_swm_team_id,
                    "boundary_geojson": json.loads(r.boundary_geojson) if r.boundary_geojson else None
                }
                for r in records
            ]

    def get_sub_ward(self, sub_ward_id: str) -> Optional[Dict[str, Any]]:
        self.seed_hierarchy_if_empty()
        with self._get_session() as session:
            rec = session.scalar(select(SubWardRecord).where(SubWardRecord.id == sub_ward_id))
            if not rec:
                return None
            return {
                "id": rec.id,
                "ward_id": rec.ward_id,
                "authority_id": rec.authority_id,
                "sub_ward_code": rec.sub_ward_code,
                "name": rec.name,
                "is_official": rec.is_official,
                "operational_type": rec.operational_type,
                "supervisor_name": rec.supervisor_name,
                "default_road_team_id": rec.default_road_team_id,
                "default_swm_team_id": rec.default_swm_team_id,
                "is_active": rec.is_active,
                "boundary_geojson": json.loads(rec.boundary_geojson) if rec.boundary_geojson else None
            }

    def create_sub_ward(self, sub_ward_data: Dict[str, Any]) -> Dict[str, Any]:
        self.seed_hierarchy_if_empty()
        with self._get_session() as session:
            ward_id = sub_ward_data.get("ward_id")
            ward_rec = session.scalar(select(AdminWardRecord).where(AdminWardRecord.id == ward_id))
            authority_id = ward_rec.authority_id if ward_rec else "AUTH-BMC"

            sub_id = sub_ward_data.get("id") or f"SUB-{uuid.uuid4().hex[:8].upper()}"
            sub_code = sub_ward_data.get("sub_ward_code") or f"SW-{uuid.uuid4().hex[:4].upper()}"
            name = sub_ward_data.get("name") or f"CIVILENS Operational Sub-Ward {sub_code}"

            rec = SubWardRecord(
                id=sub_id,
                ward_id=ward_id,
                authority_id=authority_id,
                sub_ward_code=sub_code,
                name=name,
                is_official=False,  # Enforce non-official flag
                operational_type="CIVILENS_OPERATIONAL_SUB_WARD",
                supervisor_name=sub_ward_data.get("supervisor_name", "Area Supervisor"),
                default_road_team_id=sub_ward_data.get("default_road_team_id"),
                default_swm_team_id=sub_ward_data.get("default_swm_team_id"),
                is_active=True,
                boundary_geojson=json.dumps(sub_ward_data.get("boundary_geojson")) if sub_ward_data.get("boundary_geojson") else None
            )
            session.add(rec)
            return {
                "id": rec.id,
                "ward_id": rec.ward_id,
                "authority_id": rec.authority_id,
                "sub_ward_code": rec.sub_ward_code,
                "name": rec.name,
                "is_official": False,
                "operational_type": rec.operational_type,
                "supervisor_name": rec.supervisor_name,
                "default_road_team_id": rec.default_road_team_id,
                "default_swm_team_id": rec.default_swm_team_id,
                "is_active": True,
                "boundary_geojson": sub_ward_data.get("boundary_geojson")
            }

    def update_sub_ward(self, sub_ward_id: str, sub_ward_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        self.seed_hierarchy_if_empty()
        with self._get_session() as session:
            rec = session.scalar(select(SubWardRecord).where(SubWardRecord.id == sub_ward_id))
            if not rec:
                return None
            if "sub_ward_code" in sub_ward_data and sub_ward_data["sub_ward_code"] is not None:
                rec.sub_ward_code = sub_ward_data["sub_ward_code"]
            if "name" in sub_ward_data and sub_ward_data["name"] is not None:
                rec.name = sub_ward_data["name"]
            if "supervisor_name" in sub_ward_data and sub_ward_data["supervisor_name"] is not None:
                rec.supervisor_name = sub_ward_data["supervisor_name"]
            if "default_road_team_id" in sub_ward_data:
                rec.default_road_team_id = sub_ward_data["default_road_team_id"]
            if "default_swm_team_id" in sub_ward_data:
                rec.default_swm_team_id = sub_ward_data["default_swm_team_id"]
            if "is_active" in sub_ward_data and sub_ward_data["is_active"] is not None:
                rec.is_active = sub_ward_data["is_active"]
            if "boundary_geojson" in sub_ward_data and sub_ward_data["boundary_geojson"] is not None:
                rec.boundary_geojson = json.dumps(sub_ward_data["boundary_geojson"])

            return {
                "id": rec.id,
                "ward_id": rec.ward_id,
                "authority_id": rec.authority_id,
                "sub_ward_code": rec.sub_ward_code,
                "name": rec.name,
                "is_official": rec.is_official,
                "operational_type": rec.operational_type,
                "supervisor_name": rec.supervisor_name,
                "default_road_team_id": rec.default_road_team_id,
                "default_swm_team_id": rec.default_swm_team_id,
                "is_active": rec.is_active,
                "boundary_geojson": json.loads(rec.boundary_geojson) if rec.boundary_geojson else None
            }

    def delete_sub_ward(self, sub_ward_id: str) -> bool:
        self.seed_hierarchy_if_empty()
        with self._get_session() as session:
            rec = session.scalar(select(SubWardRecord).where(SubWardRecord.id == sub_ward_id))
            if not rec:
                return False
            rec.is_active = False
            return True

    def list_localities(self, sub_ward_id: Optional[str] = None, ward_id: Optional[str] = None) -> List[Dict[str, Any]]:
        self.seed_hierarchy_if_empty()
        with self._get_session() as session:
            stmt = select(LocalityBeatRecord).where(LocalityBeatRecord.is_active.is_(True))
            if sub_ward_id:
                stmt = stmt.where(LocalityBeatRecord.sub_ward_id == sub_ward_id)
            if ward_id:
                stmt = stmt.where(LocalityBeatRecord.ward_id == ward_id)
            stmt = stmt.order_by(LocalityBeatRecord.name)
            records = session.scalars(stmt).all()
            return [
                {
                    "id": r.id,
                    "sub_ward_id": r.sub_ward_id,
                    "ward_id": r.ward_id,
                    "authority_id": r.authority_id,
                    "name": r.name,
                    "landmark": r.landmark,
                    "latitude": r.latitude,
                    "longitude": r.longitude,
                    "radius_meters": r.radius_meters,
                    "is_active": r.is_active
                }
                for r in records
            ]

    def create_locality(self, locality_data: Dict[str, Any]) -> Dict[str, Any]:
        self.seed_hierarchy_if_empty()
        with self._get_session() as session:
            sub_id = locality_data.get("sub_ward_id")
            sub_rec = session.scalar(select(SubWardRecord).where(SubWardRecord.id == sub_id))
            ward_id = sub_rec.ward_id if sub_rec else "WARD-BMC-N"
            authority_id = sub_rec.authority_id if sub_rec else "AUTH-BMC"

            loc_id = locality_data.get("id") or f"LOC-{uuid.uuid4().hex[:8].upper()}"
            rec = LocalityBeatRecord(
                id=loc_id,
                sub_ward_id=sub_id,
                ward_id=ward_id,
                authority_id=authority_id,
                name=locality_data["name"],
                landmark=locality_data.get("landmark"),
                latitude=float(locality_data["latitude"]),
                longitude=float(locality_data["longitude"]),
                radius_meters=float(locality_data.get("radius_meters", 500.0)),
                is_active=True
            )
            session.add(rec)
            return {
                "id": rec.id,
                "sub_ward_id": rec.sub_ward_id,
                "ward_id": rec.ward_id,
                "authority_id": rec.authority_id,
                "name": rec.name,
                "landmark": rec.landmark,
                "latitude": rec.latitude,
                "longitude": rec.longitude,
                "radius_meters": rec.radius_meters,
                "is_active": True
            }

    def get_officer_jurisdiction(self, user_id: str) -> Optional[Dict[str, Any]]:
        self.seed_hierarchy_if_empty()
        with self._get_session() as session:
            stmt = select(OfficerJurisdictionRecord).where(OfficerJurisdictionRecord.user_id == user_id)
            rec = session.scalar(stmt)
            if not rec:
                return None
            return {
                "id": rec.id,
                "user_id": rec.user_id,
                "authority_id": rec.authority_id,
                "ward_code": rec.ward_code,
                "sub_ward_id": rec.sub_ward_id,
                "jurisdiction_level": rec.jurisdiction_level
            }

    def assign_officer_jurisdiction(
        self,
        user_id: str,
        ward_code: str,
        sub_ward_id: Optional[str] = None,
        authority_id: str = "AUTH-BMC",
        jurisdiction_level: str = "WARD_OFFICER"
    ) -> Dict[str, Any]:
        self.seed_hierarchy_if_empty()
        with self._get_session() as session:
            stmt = select(OfficerJurisdictionRecord).where(OfficerJurisdictionRecord.user_id == user_id)
            rec = session.scalar(stmt)
            if not rec:
                rec = OfficerJurisdictionRecord(
                    id=f"OJ-{uuid.uuid4().hex[:6].upper()}",
                    user_id=user_id,
                    authority_id=authority_id,
                    ward_code=ward_code,
                    sub_ward_id=sub_ward_id,
                    jurisdiction_level=jurisdiction_level
                )
                session.add(rec)
            else:
                rec.authority_id = authority_id
                rec.ward_code = ward_code
                rec.sub_ward_id = sub_ward_id
                rec.jurisdiction_level = jurisdiction_level

            # Synchronize supervisor and lead officer fields on linked hierarchy records
            user_rec = session.get(UserRecord, user_id)
            if sub_ward_id:
                sw = session.get(SubWardRecord, sub_ward_id)
                if sw:
                    sw.supervisor_id = user_id
                    if user_rec:
                        sw.supervisor_name = user_rec.name
            if ward_code:
                w = session.scalar(select(AdminWardRecord).where((AdminWardRecord.ward_code == ward_code) | (AdminWardRecord.id == ward_code)))
                if w and user_rec:
                    w.lead_officer = user_rec.name

            return {
                "id": rec.id,
                "user_id": rec.user_id,
                "authority_id": rec.authority_id,
                "ward_code": rec.ward_code,
                "sub_ward_id": rec.sub_ward_id,
                "jurisdiction_level": rec.jurisdiction_level
            }

    def update_issue_jurisdiction(
        self,
        issue_id: str,
        new_ward_code: str,
        new_sub_ward_id: Optional[str] = None,
        new_locality_id: Optional[str] = None,
        changed_by: str = "Abhinay",
        changed_by_role: str = "inspector",
        reason: str = "Municipal jurisdiction correction"
    ) -> Optional[Issue]:
        """
        Allows authorized municipal officers and admins to correct the administrative assignment
        of a complaint, persisting the change in the database and recording an immutable audit log.
        """
        self.seed_hierarchy_if_empty()
        with self._get_session() as session:
            rec = session.scalar(select(IssueRecord).where(IssueRecord.id == issue_id))
            if not rec:
                return None

            issue = Issue.model_validate_json(rec.data_json)
            _ensure_timeline(issue)

            # 1. Capture previous jurisdiction snapshot
            prev_jurisdiction = {
                "authority_id": issue.authority_id,
                "authority_code": issue.authority_code,
                "ward_code": issue.ward,
                "ward_id": issue.ward_id,
                "sub_ward_id": issue.sub_ward_id,
                "sub_ward_name": issue.sub_ward_name,
                "locality_id": issue.locality_id,
                "locality_name": issue.locality_name,
                "routing_path": issue.routing_path
            }

            # 2. Look up new administrative entities
            ward_rec = session.scalar(select(AdminWardRecord).where(AdminWardRecord.ward_code == new_ward_code))
            if not ward_rec:
                # Try finding by ward_id or partial
                ward_rec = session.scalar(select(AdminWardRecord).where(AdminWardRecord.id == new_ward_code))

            auth_id = ward_rec.authority_id if ward_rec else ("AUTH-NMMC" if "NMMC" in new_ward_code else "AUTH-BMC")
            auth_rec = session.scalar(select(MunicipalAuthorityRecord).where(MunicipalAuthorityRecord.id == auth_id))
            auth_code = auth_rec.code if auth_rec else ("NMMC" if "NMMC" in new_ward_code else "BMC")
            auth_name = auth_rec.name if auth_rec else "Brihanmumbai Municipal Corporation"

            # Resolve sub-ward
            sub_rec = None
            if new_sub_ward_id:
                sub_rec = session.scalar(select(SubWardRecord).where(SubWardRecord.id == new_sub_ward_id))
            if not sub_rec and ward_rec:
                # Pick first active sub-ward
                sub_rec = session.scalar(select(SubWardRecord).where(SubWardRecord.ward_id == ward_rec.id))

            sub_name = sub_rec.name if sub_rec else f"Operational Service Area ({new_ward_code})"
            sub_id = sub_rec.id if sub_rec else None
            supervisor = sub_rec.supervisor_name if sub_rec else "Area Supervisor"

            # Resolve locality
            loc_rec = None
            if new_locality_id:
                loc_rec = session.scalar(select(LocalityBeatRecord).where(LocalityBeatRecord.id == new_locality_id))
            elif sub_rec:
                loc_rec = session.scalar(select(LocalityBeatRecord).where(LocalityBeatRecord.sub_ward_id == sub_rec.id))

            loc_name = loc_rec.name if loc_rec else issue.location
            loc_id = loc_rec.id if loc_rec else None

            # 3. Construct new routing path
            dept_name = issue.department or ("Road Infrastructure Maintenance" if "Road" in str(issue.category) else "Solid Waste Management")
            crew_name = issue.assignment.team_name if (issue.assignment and issue.assignment.team_name) else None
            zone_rec = session.scalar(select(AdminZoneRecord).where(AdminZoneRecord.id == ward_rec.zone_id)) if (ward_rec and ward_rec.zone_id) else None
            zone_label = zone_rec.name if zone_rec else "Pending Allocation"
            new_routing_path = build_hierarchical_routing_path(
                authority_name=auth_name,
                zone_name=zone_label,
                ward_name=new_ward_code,
                sub_ward_name=sub_name,
                locality_name=loc_name,
                department=dept_name,
                supervisor_name=supervisor,
                crew_name=crew_name
            )

            new_jurisdiction = {
                "authority_id": auth_id,
                "authority_code": auth_code,
                "authority_name": auth_name,
                "ward_code": new_ward_code,
                "ward_id": ward_rec.id if ward_rec else None,
                "sub_ward_id": sub_id,
                "sub_ward_name": sub_name,
                "locality_id": loc_id,
                "locality_name": loc_name,
                "routing_path": new_routing_path
            }

            now_iso = datetime.now(timezone.utc).isoformat()

            # 4. Record audit log
            audit_log = JurisdictionAuditLogRecord(
                id=f"AUDIT-JUR-{uuid.uuid4().hex[:8].upper()}",
                issue_id=issue_id,
                previous_jurisdiction_json=json.dumps(prev_jurisdiction),
                new_jurisdiction_json=json.dumps(new_jurisdiction),
                changed_by=changed_by,
                changed_by_role=changed_by_role,
                reason=reason,
                timestamp=datetime.now(timezone.utc)
            )
            session.add(audit_log)

            # 5. Append event to issue timeline
            evt = TimelineEvent(
                id=f"evt-jur-{uuid.uuid4().hex[:6]}",
                event_type="JURISDICTION_CORRECTED",
                title=f"Jurisdiction Corrected: {new_ward_code}",
                description=f"{changed_by} ({changed_by_role}) reallocated complaint from {prev_jurisdiction.get('ward_code')} to {new_ward_code}. Reason: {reason}",
                actor=changed_by,
                role=changed_by_role,
                timestamp=now_iso,
                metadata={
                    "previous_jurisdiction": prev_jurisdiction,
                    "new_jurisdiction": new_jurisdiction,
                    "reason": reason
                }
            )
            issue.timeline.append(evt)

            # 6. Update issue fields
            issue.ward = new_ward_code
            issue.authority_id = auth_id
            issue.authority_code = auth_code
            issue.authority_name = auth_name
            issue.ward_id = ward_rec.id if ward_rec else None
            issue.sub_ward_id = sub_id
            issue.sub_ward_name = sub_name
            issue.locality_id = loc_id
            issue.locality_name = loc_name
            issue.routing_path = new_routing_path
            issue.jurisdiction_review_required = False
            issue.jurisdiction_verified = True
            issue.jurisdiction_review_reason = None
            if not hasattr(issue, "jurisdiction_history") or issue.jurisdiction_history is None:
                issue.jurisdiction_history = []
            issue.jurisdiction_history.append({
                "previous": prev_jurisdiction,
                "new": new_jurisdiction,
                "changed_by": changed_by,
                "changed_by_role": changed_by_role,
                "reason": reason,
                "timestamp": now_iso
            })

            self._update_record_from_issue(rec, issue)
            return issue

    def get_jurisdiction_audit_logs(self, issue_id: Optional[str] = None) -> List[Dict[str, Any]]:
        self.seed_hierarchy_if_empty()
        with self._get_session() as session:
            stmt = select(JurisdictionAuditLogRecord)
            if issue_id:
                stmt = stmt.where(JurisdictionAuditLogRecord.issue_id == issue_id)
            stmt = stmt.order_by(JurisdictionAuditLogRecord.timestamp.desc())
            records = session.scalars(stmt).all()
            return [
                {
                    "id": r.id,
                    "issue_id": r.issue_id,
                    "previous_jurisdiction": json.loads(r.previous_jurisdiction_json),
                    "new_jurisdiction": json.loads(r.new_jurisdiction_json),
                    "changed_by": r.changed_by,
                    "changed_by_role": r.changed_by_role,
                    "reason": r.reason,
                    "timestamp": r.timestamp.isoformat()
                }
                for r in records
            ]

    def get_hierarchy_tree(
        self,
        authority_code: Optional[str] = None,
        ward_code: Optional[str] = None,
        sub_ward_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Builds complete hierarchical geographical tree (Authority -> Zone -> Ward -> Sub-Ward -> Locality)
        with real-time aggregated workload metrics computed directly from SQLite records.
        """
        self.seed_hierarchy_if_empty()
        with self._get_session() as session:
            # Query all base data
            authorities = session.scalars(select(MunicipalAuthorityRecord).where(MunicipalAuthorityRecord.is_active.is_(True))).all()
            zones = session.scalars(select(AdminZoneRecord).where(AdminZoneRecord.is_active.is_(True))).all()
            wards = session.scalars(select(AdminWardRecord).where(AdminWardRecord.is_active.is_(True))).all()
            sub_wards = session.scalars(select(SubWardRecord).where(SubWardRecord.is_active.is_(True))).all()
            localities = session.scalars(select(LocalityBeatRecord).where(LocalityBeatRecord.is_active.is_(True))).all()
            teams = session.scalars(select(TeamRecord)).all()
            issues = session.scalars(select(IssueRecord)).all()

            # Map teams by ward and sub_ward
            teams_by_ward: Dict[str, List[str]] = {}
            teams_by_sub_ward: Dict[str, List[str]] = {}
            team_objs_by_ward: Dict[str, List[Dict[str, Any]]] = {}
            team_objs_by_sub_ward: Dict[str, List[Dict[str, Any]]] = {}
            for t in teams:
                td = {
                    "id": t.id,
                    "name": t.name,
                    "department": t.department,
                    "category": t.category,
                    "status": t.status,
                    "ward": t.ward,
                    "sub_ward_id": t.sub_ward_id,
                    "capacity": t.capacity,
                    "supervisor_name": t.supervisor_name,
                    "contact_lead": t.contact_lead,
                    "active_tasks_count": t.active_tasks_count
                }
                w = t.ward
                if w:
                    teams_by_ward.setdefault(w, []).append(t.name)
                    team_objs_by_ward.setdefault(w, []).append(td)
                sw = t.sub_ward_id
                if sw:
                    teams_by_sub_ward.setdefault(sw, []).append(t.name)
                    team_objs_by_sub_ward.setdefault(sw, []).append(td)

            # Map issues by sub_ward_id and ward
            issues_by_sub_ward: Dict[str, List[IssueRecord]] = {}
            issues_by_ward: Dict[str, List[IssueRecord]] = {}
            for iss in issues:
                w = iss.ward
                if w:
                    issues_by_ward.setdefault(w, []).append(iss)
                sw = iss.sub_ward_id
                if sw:
                    issues_by_sub_ward.setdefault(sw, []).append(iss)

            def calc_metrics(iss_list: List[IssueRecord], direct_count: int = 0) -> Dict[str, int]:
                total = len(iss_list)
                unassigned = 0
                assigned = 0
                in_progress = 0
                completed = 0
                for i in iss_list:
                    st = (i.status or "").upper()
                    if st in ("RESOLVED", "VERIFIED CLOSED"):
                        completed += 1
                    elif st in ("ACTION IN PROGRESS", "IN_PROGRESS", "IN PROGRESS"):
                        in_progress += 1
                    elif st in ("ASSIGNED", "SCHEDULED"):
                        assigned += 1
                    else:
                        # Check assignment in data_json
                        try:
                            d = json.loads(i.data_json)
                            if d.get("assignment") and d["assignment"].get("team_name"):
                                assigned += 1
                            else:
                                unassigned += 1
                        except Exception:
                            unassigned += 1
                return {
                    "total_complaints": total,
                    "direct_complaints": direct_count,
                    "unassigned_complaints": unassigned,
                    "assigned_complaints": assigned,
                    "in_progress_tasks": in_progress,
                    "completed_complaints": completed
                }

            # Build tree
            tree = []
            for auth in authorities:
                if authority_code and auth.code.upper() != authority_code.upper():
                    continue

                auth_node = {
                    "id": auth.id,
                    "label": f"{auth.name} ({auth.code})",
                    "name": auth.name,
                    "code": auth.code,
                    "type": "authority",
                    "level": "authority",
                    "is_official": True,
                    "is_active": auth.is_active,
                    "boundary_geojson": json.loads(auth.boundary_geojson) if auth.boundary_geojson else None,
                    "children": [],
                    "assigned_crews": [],
                    "assigned_crews_count": 0,
                    "assigned_teams": []
                }

                auth_zones = [z for z in zones if z.authority_id == auth.id]
                auth_issues: List[IssueRecord] = []

                for zone in auth_zones:
                    zone_node = {
                        "id": zone.id,
                        "label": zone.name,
                        "name": zone.name,
                        "code": zone.code,
                        "type": "zone",
                        "level": "zone",
                        "parent_id": auth.id,
                        "is_official": True,
                        "is_active": zone.is_active,
                        "lead_officer": zone.zonal_officer,
                        "boundary_geojson": json.loads(zone.boundary_geojson) if zone.boundary_geojson else None,
                        "children": [],
                        "assigned_crews": [],
                        "assigned_crews_count": 0,
                        "assigned_teams": []
                    }

                    zone_wards = [w for w in wards if w.zone_id == zone.id or (not w.zone_id and w.authority_id == auth.id)]
                    zone_issues: List[IssueRecord] = []

                    for w in zone_wards:
                        if ward_code:
                            wc_clean = ward_code.strip().upper()
                            matches_ward = (
                                w.ward_code.upper() == wc_clean or
                                w.ward_name.upper() == wc_clean or
                                w.id.upper() == wc_clean or
                                w.id.upper() == f"WARD-{wc_clean}" or
                                w.id.upper() == f"WARD-BMC-{wc_clean}" or
                                (len(wc_clean) >= 3 and wc_clean in w.ward_name.upper()) or
                                (len(wc_clean) >= 3 and wc_clean in w.ward_code.upper())
                            )
                            if not matches_ward:
                                continue

                        ward_teams = teams_by_ward.get(w.ward_code, []) + teams_by_ward.get(w.id, [])
                        ward_team_objs = team_objs_by_ward.get(w.ward_code, []) + team_objs_by_ward.get(w.id, [])
                        w_issues = issues_by_ward.get(w.ward_code, [])

                        ward_node = {
                            "id": w.id,
                            "label": w.ward_name,
                            "name": w.ward_name,
                            "code": w.ward_code,
                            "type": "ward",
                            "level": "ward",
                            "parent_id": zone.id,
                            "is_official": True,
                            "is_active": w.is_active,
                            "lead_officer": w.lead_officer,
                            "office_address": w.office_address,
                            "boundary_geojson": json.loads(w.boundary_geojson) if w.boundary_geojson else None,
                            "assigned_crews": ward_teams,
                            "assigned_crews_count": len(ward_teams),
                            "assigned_teams": ward_team_objs,
                            "children": []
                        }

                        w_subs = [s for s in sub_wards if s.ward_id == w.id]
                        w_sub_issues: List[IssueRecord] = []

                        for sw in w_subs:
                            if sub_ward_id and sw.id != sub_ward_id and sw.sub_ward_code != sub_ward_id:
                                continue

                            sw_teams = teams_by_sub_ward.get(sw.id, [])
                            sw_team_objs = team_objs_by_sub_ward.get(sw.id, [])
                            sw_issues = issues_by_sub_ward.get(sw.id, [])
                            w_sub_issues.extend(sw_issues)

                            sub_node = {
                                "id": sw.id,
                                "label": sw.name,
                                "name": sw.name,
                                "code": sw.sub_ward_code,
                                "type": "sub_ward",
                                "level": "sub_ward",
                                "parent_id": w.id,
                                "is_official": sw.is_official,
                                "operational_type": sw.operational_type,
                                "is_active": sw.is_active,
                                "supervisor_name": sw.supervisor_name,
                                "supervisor": sw.supervisor_name,
                                "department": getattr(sw, "assigned_department", None) or "Solid Waste & Infrastructure",
                                "assigned_crews": sw_teams,
                                "assigned_crews_count": len(sw_teams),
                                "assigned_teams": sw_team_objs,
                                "boundary_geojson": json.loads(sw.boundary_geojson) if sw.boundary_geojson else None,
                                "children": []
                            }

                            sw_locs = [l for l in localities if l.sub_ward_id == sw.id]
                            for loc in sw_locs:
                                loc_issues = [i for i in sw_issues if i.locality_id == loc.id or (i.location and loc.name.lower() in i.location.lower())]
                                loc_node = {
                                    "id": loc.id,
                                    "label": loc.name,
                                    "name": loc.name,
                                    "code": f"BEAT-{loc.name[:4].upper()}",
                                    "type": "locality",
                                    "level": "locality",
                                    "parent_id": sw.id,
                                    "is_official": False,
                                    "is_active": loc.is_active,
                                    "landmark": loc.landmark,
                                    "latitude": loc.latitude,
                                    "longitude": loc.longitude,
                                    "radius_meters": loc.radius_meters,
                                    "assigned_crews": [],
                                    "assigned_crews_count": 0,
                                    "assigned_teams": [],
                                    "children": []
                                }
                                loc_metrics = calc_metrics(loc_issues, direct_count=len(loc_issues))
                                loc_node.update(loc_metrics)
                                sub_node["children"].append(loc_node)

                            direct_sw_count = len([i for i in sw_issues if not i.locality_id or str(i.locality_id) in ("None", "")])
                            sub_metrics = calc_metrics(sw_issues, direct_count=direct_sw_count)
                            sub_node.update(sub_metrics)
                            ward_node["children"].append(sub_node)

                        if sub_ward_id and len(ward_node["children"]) == 0:
                            continue

                        # All issues belonging to ward
                        direct_w_count = len([i for i in w_issues if not i.sub_ward_id or str(i.sub_ward_id) in ("None", "", "SUB-WARD-PENDING")])
                        all_ward_issues = list({i.id: i for i in (w_issues + w_sub_issues)}.values())
                        ward_metrics = calc_metrics(all_ward_issues, direct_count=direct_w_count)
                        ward_node.update(ward_metrics)
                        zone_node["children"].append(ward_node)
                        zone_issues.extend(all_ward_issues)

                    # Prune empty zones if ward_code or sub_ward_id filtering is active
                    if (ward_code or sub_ward_id) and len(zone_node["children"]) == 0:
                        continue

                    all_zone_issues = list({i.id: i for i in zone_issues}.values())
                    zone_metrics = calc_metrics(all_zone_issues, direct_count=0)
                    zone_node.update(zone_metrics)
                    auth_node["children"].append(zone_node)
                    auth_issues.extend(all_zone_issues)

                # Prune empty authorities if ward_code or sub_ward_id filtering is active
                if (ward_code or sub_ward_id) and len(auth_node["children"]) == 0:
                    continue

                all_auth_issues = list({i.id: i for i in auth_issues}.values())
                auth_metrics = calc_metrics(all_auth_issues, direct_count=0)
                auth_node.update(auth_metrics)
                tree.append(auth_node)

            return tree





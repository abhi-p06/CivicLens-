import os
import json
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
    ResolutionEvidence
)
from app.db.database import SessionLocal, get_db_session, init_db
from app.db.models import (
    IssueRecord,
    RoutingConfigRecord,
    UploadRecord,
    VerificationHistoryRecord,
    UserRecord
)

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

    def reset_demo(self, seed_file_path: Optional[str] = None) -> int:
        """
        Explicit demo reset operation.
        Wipes current issues and reloads seed baseline within a single transaction.
        Must only be invoked when CIVILENS_DEMO_MODE is active.
        """
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
        - Citizen: citizen@civilens.org / Citizen@123
        - Inspector: inspector@civilens.org / Inspector@123
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
                ("CITIZEN-001", "citizen", "citizen@civilens.org", "Suresh Patil (Citizen)", citizen_pwd, "citizen"),
                ("INSP-MUMBAI-01", "inspector", "inspector@civilens.org", "Ward Field Inspector", inspector_pwd, "inspector"),
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


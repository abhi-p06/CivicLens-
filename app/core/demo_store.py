from pathlib import Path
from typing import List, Optional, Dict, Any
from app.models.issue import (
    Issue,
    IssueStatus,
    IssueCategory,
    PriorityLevel
)
from app.models.field_guidance import FieldGuidanceResult, OfficerDecisionType
from app.db.database import init_db
from app.db.repository import SqliteIssueRepository

class DemoDataStore:
    """
    SQLite-backed repository preserving existing API contracts and method signatures.
    Replaces volatile in-memory dictionary with ACID persistent SQLite storage.
    Ensures zero data loss across FastAPI server restarts while retaining 100%
    compatibility with existing services, pipelines, and test suites.
    """
    def __init__(
        self,
        seed_file_path: Optional[str] = None,
        repository: Optional[SqliteIssueRepository] = None
    ):
        init_db()
        self.repository = repository or SqliteIssueRepository(seed_file_path=seed_file_path)
        self.seed_file_path = self.repository.seed_file_path

    @property
    def _issues(self) -> Dict[str, Issue]:
        """Backward-compatibility read accessor. Authoritative data is in SQLite."""
        return {issue.issueId: issue for issue in self.repository.list_issues()}

    def seed_if_empty(self) -> int:
        """First-run initialization: populates seed records only when database is empty."""
        return self.repository.seed_if_empty(self.seed_file_path)

    def reload(self) -> int:
        """Restores demo seed baseline in SQLite transactionally."""
        return self.repository.reset_demo(self.seed_file_path)

    def reset_demo(self) -> int:
        """Transactionally wipes and restores seed baseline (or wipes in presentation mode)."""
        return self.repository.reset_demo(self.seed_file_path)

    def clear_issues(self) -> int:
        """Clears all issue records."""
        return self.repository.clear_issues()

    def list_issues(
        self,
        category: Optional[IssueCategory] = None,
        priority: Optional[PriorityLevel] = None,
        status_filter: Optional[IssueStatus] = None,
        hotspot_only: bool = False,
        citizen_id: Optional[str] = None
    ) -> List[Issue]:
        return self.repository.list_issues(
            category=category,
            priority=priority,
            status_filter=status_filter,
            hotspot_only=hotspot_only,
            citizen_id=citizen_id
        )

    def get_issue(self, issue_id: str) -> Optional[Issue]:
        return self.repository.get_issue(issue_id)

    def add_issue(self, issue: Issue) -> Issue:
        return self.repository.add_issue(issue)

    def update_issue(self, issue: Issue) -> Issue:
        return self.repository.update_issue(issue)

    def update_status(
        self,
        issue_id: str,
        new_status: IssueStatus,
        note: Optional[str] = None,
        actor: Optional[str] = None
    ) -> Optional[Issue]:
        return self.repository.update_status(issue_id, new_status, note=note, actor=actor)

    def record_verification(self, issue_id: str, evidence: Any) -> Issue:
        return self.repository.record_verification(issue_id, evidence)

    def get_verification_history(self, issue_id: str) -> List[Any]:
        return self.repository.get_verification_history(issue_id)

    # Forward user management methods
    def get_user_by_identifier(self, identifier: str) -> Optional[Dict[str, Any]]:
        return self.repository.get_user_by_identifier(identifier)

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        return self.repository.get_user_by_id(user_id)

    def create_user(self, username: str, email: str, name: str, password_hash: str, salt: str, role: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        return self.repository.create_user(username, email, name, password_hash, salt, role, user_id=user_id)

    def list_users(self) -> List[Dict[str, Any]]:
        return self.repository.list_users()

    def seed_default_users_if_empty(self) -> int:
        return self.repository.seed_default_users_if_empty()

    # Forward Ward Operations Management methods
    def seed_default_teams_and_wards_if_empty(self) -> None:
        return self.repository.seed_default_teams_and_wards_if_empty()

    def list_teams(
        self,
        category: Optional[str] = None,
        ward: Optional[str] = None,
        sub_ward_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        return self.repository.list_teams(category=category, ward=ward, sub_ward_id=sub_ward_id)

    def get_team(self, team_id: str) -> Optional[Dict[str, Any]]:
        return self.repository.get_team(team_id)

    def create_team(self, team_data: Dict[str, Any]) -> Dict[str, Any]:
        return self.repository.create_team(team_data)

    def update_team(self, team_id: str, team_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return self.repository.update_team(team_id, team_data)

    def delete_team(self, team_id: str) -> bool:
        return self.repository.delete_team(team_id)

    def list_wards(self) -> List[Dict[str, Any]]:
        return self.repository.list_wards()

    def update_ward(self, ward_code: str, ward_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return self.repository.update_ward(ward_code, ward_data)

    def assign_task(self, issue_id: str, assignment_data: Dict[str, Any], actor: str = "Abhinay", role: str = "inspector") -> Optional[Issue]:
        return self.repository.assign_task(issue_id, assignment_data, actor=actor, role=role)

    def schedule_task(self, issue_id: str, scheduled_date: str, schedule_type: str = "WORK", instructions: Optional[str] = None, actor: str = "Abhinay", role: str = "inspector") -> Optional[Issue]:
        return self.repository.schedule_task(issue_id, scheduled_date, schedule_type=schedule_type, instructions=instructions, actor=actor, role=role)

    def record_action(self, issue_id: str, action_type: str, action_data: Dict[str, Any], actor: str = "Abhinay", role: str = "inspector") -> Optional[Issue]:
        return self.repository.record_action(issue_id, action_type, action_data, actor=actor, role=role)

    def complete_task(self, issue_id: str, completion_note: str, closure_reason: str = "Work executed to municipal standard", completion_photo_url: Optional[str] = None, actor: str = "Abhinay", role: str = "inspector") -> Optional[Issue]:
        return self.repository.complete_task(issue_id, completion_note, closure_reason=closure_reason, completion_photo_url=completion_photo_url, actor=actor, role=role)

    def reopen_task(self, issue_id: str, reason: str, note: Optional[str] = None, actor: str = "Abhinay", role: str = "inspector") -> Optional[Issue]:
        return self.repository.reopen_task(issue_id, reason, note=note, actor=actor, role=role)

    def record_feedback(self, issue_id: str, feedback: str, note: Optional[str] = None, citizen_name: str = "Abhinay") -> Optional[Issue]:
        return self.repository.record_feedback(issue_id, feedback, note=note, citizen_name=citizen_name)

    def get_operations_kpis(self) -> Dict[str, Any]:
        return self.repository.get_operations_kpis()

    def get_or_generate_field_guidance(self, issue_id: str, force_regenerate: bool = False) -> Optional[FieldGuidanceResult]:
        return self.repository.get_or_generate_field_guidance(issue_id, force_regenerate=force_regenerate)

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
        return self.repository.record_guidance_decision(
            issue_id=issue_id,
            item_id=item_id,
            decision=decision,
            edited_text=edited_text,
            reason=reason,
            actor=actor,
            role=role
        )

    # Hierarchical Ward Management Forwarding Methods
    def seed_hierarchy_if_empty(self) -> None:
        return self.repository.seed_hierarchy_if_empty()

    def get_hierarchy_tree(
        self,
        authority_code: Optional[str] = None,
        ward_code: Optional[str] = None,
        sub_ward_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        return self.repository.get_hierarchy_tree(
            authority_code=authority_code,
            ward_code=ward_code,
            sub_ward_id=sub_ward_id
        )

    def list_authorities(self) -> List[Dict[str, Any]]:
        return self.repository.list_authorities()

    def list_admin_wards(self, authority_id: Optional[str] = None) -> List[Dict[str, Any]]:
        return self.repository.list_admin_wards(authority_id=authority_id)

    def list_sub_wards(self, ward_code: Optional[str] = None, ward_id: Optional[str] = None) -> List[Dict[str, Any]]:
        return self.repository.list_sub_wards(ward_code=ward_code, ward_id=ward_id)

    def get_sub_ward(self, sub_ward_id: str) -> Optional[Dict[str, Any]]:
        return self.repository.get_sub_ward(sub_ward_id)

    def create_sub_ward(self, sub_ward_data: Dict[str, Any]) -> Dict[str, Any]:
        return self.repository.create_sub_ward(sub_ward_data)

    def update_sub_ward(self, sub_ward_id: str, sub_ward_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return self.repository.update_sub_ward(sub_ward_id, sub_ward_data)

    def delete_sub_ward(self, sub_ward_id: str) -> bool:
        return self.repository.delete_sub_ward(sub_ward_id)

    def list_localities(self, sub_ward_id: Optional[str] = None, ward_id: Optional[str] = None) -> List[Dict[str, Any]]:
        return self.repository.list_localities(sub_ward_id=sub_ward_id, ward_id=ward_id)

    def create_locality(self, locality_data: Dict[str, Any]) -> Dict[str, Any]:
        return self.repository.create_locality(locality_data)

    def get_officer_jurisdiction(self, user_id: str) -> Optional[Dict[str, Any]]:
        return self.repository.get_officer_jurisdiction(user_id)

    def assign_officer_jurisdiction(
        self,
        user_id: str,
        ward_code: str,
        sub_ward_id: Optional[str] = None,
        authority_id: str = "AUTH-BMC",
        jurisdiction_level: str = "WARD_OFFICER"
    ) -> Dict[str, Any]:
        return self.repository.assign_officer_jurisdiction(
            user_id=user_id,
            ward_code=ward_code,
            sub_ward_id=sub_ward_id,
            authority_id=authority_id,
            jurisdiction_level=jurisdiction_level
        )

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
        return self.repository.update_issue_jurisdiction(
            issue_id=issue_id,
            new_ward_code=new_ward_code,
            new_sub_ward_id=new_sub_ward_id,
            new_locality_id=new_locality_id,
            changed_by=changed_by,
            changed_by_role=changed_by_role,
            reason=reason
        )

    def get_jurisdiction_audit_logs(self, issue_id: Optional[str] = None) -> List[Dict[str, Any]]:
        return self.repository.get_jurisdiction_audit_logs(issue_id=issue_id)

    def verify_jurisdiction(
        self,
        issue_id: str,
        actor: str = "Abhinay",
        role: str = "inspector",
        notes: Optional[str] = None
    ) -> Optional[Issue]:
        return self.repository.verify_jurisdiction(
            issue_id=issue_id,
            actor=actor,
            role=role,
            notes=notes
        )

# Global singleton instance
demo_store = DemoDataStore()

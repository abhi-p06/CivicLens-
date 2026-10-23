from pathlib import Path
from typing import List, Optional, Dict, Any
from app.models.issue import (
    Issue,
    IssueStatus,
    IssueCategory,
    PriorityLevel
)
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
        """Transactionally wipes and restores seed baseline."""
        return self.repository.reset_demo(self.seed_file_path)

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

# Global singleton instance
demo_store = DemoDataStore()

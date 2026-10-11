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
        hotspot_only: bool = False
    ) -> List[Issue]:
        return self.repository.list_issues(
            category=category,
            priority=priority,
            status_filter=status_filter,
            hotspot_only=hotspot_only
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

# Global singleton instance
demo_store = DemoDataStore()

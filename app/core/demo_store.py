import json
from pathlib import Path
from typing import List, Optional, Dict
from app.models.issue import Issue, IssueCreate, IssueStatus

class DemoDataStore:
    """
    Centralized, deterministic single source of truth for demo fallback data.
    Ensures tests and frontend demonstrations never rely on scattered hardcoded mocks.
    """
    def __init__(self, seed_file_path: Optional[str] = None):
        if seed_file_path is None:
            seed_file_path = str(Path(__file__).parent.parent.parent / "data" / "seed_issues.json")
        self.seed_file_path = seed_file_path
        self._issues: Dict[str, Issue] = {}
        self.reload()

    def reload(self):
        self._issues.clear()
        p = Path(self.seed_file_path)
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
                for item in raw_data:
                    issue = Issue(**item)
                    self._issues[issue.issueId] = issue

    def list_issues(self) -> List[Issue]:
        return list(self._issues.values())

    def get_issue(self, issue_id: str) -> Optional[Issue]:
        return self._issues.get(issue_id)

    def add_issue(self, issue: Issue) -> Issue:
        self._issues[issue.issueId] = issue
        return issue

    def update_status(self, issue_id: str, new_status: IssueStatus) -> Optional[Issue]:
        issue = self.get_issue(issue_id)
        if issue:
            issue.status = new_status
            self._issues[issue_id] = issue
        return issue

# Global singleton instance
demo_store = DemoDataStore()

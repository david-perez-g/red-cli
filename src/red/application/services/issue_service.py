"""Issue-related use cases."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Iterator, List, Optional

from ...domain.models import Issue
from ...domain.utils import parse_ids
from ...infrastructure.redmine.client import RedmineClient
from .auth_service import AuthService


@dataclass
class IssueService:
    _auth_service: AuthService

    def list_for_current_user(self, limit: Optional[int] = None) -> List[Issue]:
        client = RedmineClient(self._auth_service.require_session())
        issues = [Issue.from_api_data(raw) for raw in client.list_issues(assigned_to_id="me", limit=limit)]
        return issues

    def list_by_project(self, project_identifier: str, limit: Optional[int] = None) -> List[Issue]:
        client = RedmineClient(self._auth_service.require_session())
        issues = [Issue.from_api_data(raw) for raw in client.list_issues(project_id=project_identifier, limit=limit)]
        return issues

    def list_by_ids(self, specs: Iterable[str], limit: Optional[int] = None) -> List[Issue]:
        client = RedmineClient(self._auth_service.require_session())
        results: List[Issue] = []
        for issue_id in parse_ids(list(specs)):
            try:
                raw = client.get_issue(issue_id)
                if raw:
                    results.append(Issue.from_api_data(raw))
            except Exception:  # noqa: BLE001
                # Silently skip issues that can't be fetched
                pass
            if limit is not None and len(results) >= limit:
                break
        return results

    def parse_issue_ids(self, specs: Iterable[str]) -> Iterator[int]:
        return parse_ids(list(specs))

    def get_logged_hours(self, issue_id: int) -> float:
        """Get total logged hours for an issue."""
        client = RedmineClient(self._auth_service.require_session())
        time_entries = client.list_time_entries(issue_id=issue_id)
        return sum(entry["hours"] for entry in time_entries)

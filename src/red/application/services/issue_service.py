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
        issues = [Issue.from_api_data(raw) for raw in client.list_issues(assigned_to_id="me")]
        return issues[:limit] if limit is not None else issues

    def list_by_ids(self, specs: Iterable[str], limit: Optional[int] = None) -> List[Issue]:
        client = RedmineClient(self._auth_service.require_session())
        results: List[Issue] = []
        for issue_id in parse_ids(list(specs)):
            raw = client.get_issue(issue_id)
            if raw:
                results.append(Issue.from_api_data(raw))
            if limit is not None and len(results) >= limit:
                break
        return results

    def parse_issue_ids(self, specs: Iterable[str]) -> Iterator[int]:
        return parse_ids(list(specs))

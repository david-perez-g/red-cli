"""Issue-related use cases."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Iterator, List, Optional, Sequence

from ...domain.models import Issue, UserSession
from ...domain.utils import parse_ids
from ...infrastructure.redmine.client import RedmineClient
from .auth_service import AuthService


@dataclass
class IssueService:
    _auth_service: AuthService

    def list_for_current_user(self, *, limit: Optional[int] = None, offset: Optional[int] = None, status: Optional[str] = None) -> List[Issue]:
        client = RedmineClient(self._auth_service.require_session())
        filters = {"assigned_to_id": "me"}
        if status:
            filters["status_id"] = status
        if limit is not None:
            filters["limit"] = limit
        if offset is not None:
            filters["offset"] = offset
        issues = [
            Issue.from_api_data(raw)
            for raw in client.list_issues(**filters)
        ]
        return issues

    def list_by_project(
        self,
        project_identifier: str,
        *,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        status: Optional[str] = None,
    ) -> List[Issue]:
        client = RedmineClient(self._auth_service.require_session())
        filters = {"project_id": project_identifier}
        if status:
            filters["status_id"] = status
        if limit is not None:
            filters["limit"] = limit
        if offset is not None:
            filters["offset"] = offset
        issues = [
            Issue.from_api_data(raw)
            for raw in client.list_issues(**filters)
        ]
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
        totals = self.get_logged_hours_bulk([issue_id])
        return totals.get(issue_id, 0.0)

    def create_issue(
        self,
        *,
        project: str,
        subject: str,
        description: Optional[str] = None,
        tracker: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[str] = None,
        due_date: Optional[str] = None,
        assignee: Optional[str] = None,
    ) -> Issue:
        """Create a new issue in the given project."""

        client = RedmineClient(self._auth_service.require_session())
        resolved_project = client.resolve_project(project)

        payload: Dict[str, Any] = {
            "project_id": resolved_project,
            "subject": subject,
        }
        if description:
            payload["description"] = description
        if tracker:
            payload["tracker_id"] = client.resolve_tracker(tracker)
        if status:
            payload["status_id"] = client.resolve_status(status)
        if start_date:
            payload["start_date"] = start_date
        if due_date:
            payload["due_date"] = due_date
        if assignee:
            payload["assigned_to_id"] = client.resolve_assignee(assignee)

        created = client.create_issue(payload)
        if not created:
            raise RuntimeError("Issue creation failed: empty response")
        return Issue.from_api_data(created)

    def get_logged_hours_bulk(
        self,
        issue_ids: Sequence[int],
        *,
        batch_size: int = 10,
        max_workers: int = 5,
    ) -> Dict[int, float]:
        session = self._auth_service.require_session()
        unique_issue_ids: List[int] = list(dict.fromkeys(issue_ids))
        if not unique_issue_ids:
            return {}

        results: Dict[int, float] = {}
        batch_size = max(batch_size, 1)

        for start in range(0, len(unique_issue_ids), batch_size):
            batch = unique_issue_ids[start : start + batch_size]
            max_pool_size = min(max_workers, len(batch)) or 1

            with ThreadPoolExecutor(max_workers=max_pool_size) as executor:
                futures = {
                    executor.submit(self._fetch_logged_hours_for_issue, session, issue_id): issue_id
                    for issue_id in batch
                }
                for future in as_completed(futures):
                    issue_id = futures[future]
                    try:
                        results[issue_id] = future.result()
                    except Exception:  # noqa: BLE001
                        results[issue_id] = 0.0

        return results

    @staticmethod
    def _fetch_logged_hours_for_issue(session: UserSession, issue_id: int) -> float:
        client = RedmineClient(session)
        time_entries = client.list_time_entries(issue_id=str(issue_id))
        total = 0.0
        for entry in time_entries:
            hours = entry.get("hours")
            if hours is not None:
                total += float(hours)
        return total

"""Overview reporting service."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Dict, Iterable, Optional, Tuple

from ...application.dto.overview import (
    IssueSummary,
    OverviewPayload,
    OverviewStats,
    TimeEntrySummary,
)
from ...domain.models import Issue, TimeEntry
from ...infrastructure.redmine.client import RedmineClient
from .auth_service import AuthService

DateRange = Tuple[Optional[date], Optional[date]]


@dataclass
class OverviewService:
    _auth_service: AuthService

    def personal_overview(self, date_range: Optional[DateRange] = None) -> OverviewPayload:
        session = self._auth_service.require_session()
        client = RedmineClient(session)

        if date_range:
            from_date = date_range[0].strftime("%Y-%m-%d") if date_range[0] else None
            to_date = date_range[1].strftime("%Y-%m-%d") if date_range[1] else None
        else:
            from_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            to_date = None

        issues = [Issue.from_api_data(raw) for raw in client.list_issues(assigned_to_id="me")]
        time_entries = [
            TimeEntry.from_api_data(raw)
            for raw in client.list_time_entries(user_id=session.user_id, from_date=from_date, to_date=to_date)
        ]

        stats = _build_personal_stats(issues, time_entries, date_range)
        issue_summaries = [_to_issue_summary(i) for i in issues[:5]]
        time_summaries = [_to_time_entry_summary(entry) for entry in time_entries[:5]]
        return OverviewPayload(stats=stats, issues=issue_summaries, time_entries=time_summaries, date_range=date_range)

    def project_overview(self, project_identifier: str, date_range: Optional[DateRange] = None) -> OverviewPayload:
        session = self._auth_service.require_session()
        client = RedmineClient(session)

        issues = [Issue.from_api_data(raw) for raw in client.list_issues()]
        target = project_identifier.lower()
        filtered = [
            issue
            for issue in issues
            if issue.project.lower() == target
            or (issue.project_identifier or "").lower() == target
            or issue.project.replace(" ", "-").lower() == target
        ]

        stats = _build_project_stats(filtered, [])
        return OverviewPayload(
            stats=stats,
            issues=[_to_issue_summary(issue) for issue in filtered[:5]],
            time_entries=[],
            date_range=date_range,
        )


def _build_personal_stats(issues: Iterable[Issue], time_entries: Iterable[TimeEntry], date_range: Optional[DateRange]) -> OverviewStats:
    issues = list(issues)
    time_entries = list(time_entries)

    status_counts: Dict[str, int] = defaultdict(int)
    tracker_counts: Dict[str, int] = defaultdict(int)
    project_counts: Dict[str, int] = defaultdict(int)

    for issue in issues:
        status_counts[issue.status] += 1
        tracker_counts[issue.tracker] += 1
        project_counts[issue.project] += 1

    total_hours = sum(entry.hours for entry in time_entries)

    if date_range and date_range[0]:
        start_dt = datetime.combine(date_range[0], datetime.min.time())
        period_hours = sum(entry.hours for entry in time_entries if entry.spent_on >= start_dt)
        recent_issues = [issue for issue in issues if issue.updated_on >= start_dt]
    else:
        window_start = datetime.now() - timedelta(days=7)
        period_hours = sum(entry.hours for entry in time_entries if entry.spent_on >= window_start)
        recent_issues = [issue for issue in issues if issue.updated_on >= window_start]

    open_issues = sum(status_counts.get(name, 0) for name in ("New", "Open", "Assigned"))

    return OverviewStats(
        total_issues=len(issues),
        open_issues=open_issues,
        total_hours=total_hours,
        this_period_hours=period_hours,
        recent_issues=len(recent_issues),
        status_counts=dict(status_counts),
        tracker_counts=dict(tracker_counts),
        project_counts=dict(project_counts),
        extra={},
    )


def _build_project_stats(issues: Iterable[Issue], time_entries: Iterable[TimeEntry]) -> OverviewStats:
    issues = list(issues)
    time_entries = list(time_entries)

    status_counts: Dict[str, int] = defaultdict(int)
    tracker_counts: Dict[str, int] = defaultdict(int)

    for issue in issues:
        status_counts[issue.status] += 1
        tracker_counts[issue.tracker] += 1

    contributors = {entry.user for entry in time_entries}
    total_hours = sum(entry.hours for entry in time_entries)

    return OverviewStats(
        total_issues=len(issues),
        open_issues=0,
        total_hours=total_hours,
        this_period_hours=total_hours,
        recent_issues=len(issues),
        status_counts=dict(status_counts),
        tracker_counts=dict(tracker_counts),
        project_counts={},
        extra={"contributors_count": len(contributors)},
    )


def _to_issue_summary(issue: Issue) -> IssueSummary:
    return IssueSummary(
        id=issue.id,
        subject=issue.subject,
        status=issue.status,
        tracker=issue.tracker,
        project=issue.project,
        project_identifier=issue.project_identifier,
        updated_on=issue.updated_on,
        raw={},
    )


def _to_time_entry_summary(entry: TimeEntry) -> TimeEntrySummary:
    return TimeEntrySummary(
        id=entry.id,
        issue_id=entry.issue_id,
        hours=entry.hours,
        spent_on=entry.spent_on,
        user=entry.user,
        comments=entry.comments,
        raw={},
    )

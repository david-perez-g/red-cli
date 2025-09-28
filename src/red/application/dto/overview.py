"""Transfer objects for overview use cases."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class IssueSummary:
    id: int
    subject: str
    status: str
    tracker: str
    project: str
    project_identifier: Optional[str]
    updated_on: datetime
    raw: dict


@dataclass(frozen=True)
class TimeEntrySummary:
    id: int
    issue_id: int
    hours: float
    spent_on: datetime
    user: str
    comments: str
    raw: dict


@dataclass(frozen=True)
class OverviewStats:
    total_issues: int
    open_issues: int
    total_hours: float
    this_period_hours: float
    recent_issues: int
    status_counts: Dict[str, int]
    tracker_counts: Dict[str, int]
    project_counts: Dict[str, int]
    extra: Dict[str, float | int]


@dataclass(frozen=True)
class OverviewPayload:
    stats: OverviewStats
    issues: List[IssueSummary]
    time_entries: List[TimeEntrySummary]
    date_range: Optional[Tuple[Optional[date], Optional[date]]]

"""Application container wiring for CLI entrypoints."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from ..application.services.auth_service import AuthService
from ..application.services.issue_service import IssueService
from ..application.services.overview_service import OverviewService
from ..infrastructure.config.repository import SessionRepository


@dataclass(frozen=True)
class AppContainer:
    auth: AuthService
    issues: IssueService
    overview: OverviewService


@lru_cache(maxsize=1)
def build_app_container() -> AppContainer:
    session_repo = SessionRepository()
    auth_service = AuthService(session_repo)
    overview_service = OverviewService(auth_service)
    issue_service = IssueService(auth_service)
    return AppContainer(auth=auth_service, issues=issue_service, overview=overview_service)

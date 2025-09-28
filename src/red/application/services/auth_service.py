"""Authentication workflows exposed to presentation layers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ...domain.exceptions import AuthError, AuthorizationRequiredError
from ...domain.models import UserSession
from ...infrastructure.auth.authenticator import RedmineAuthenticator
from ...infrastructure.config.repository import SessionRepository
from ...settings.env import resolve_server_url


@dataclass
class AuthService:
    _sessions: SessionRepository

    def login(self, server: str, *, username: Optional[str] = None, password: Optional[str] = None, token: Optional[str] = None) -> UserSession:
        server_url = resolve_server_url(server)
        authenticator = RedmineAuthenticator(server_url)
        if token:
            result = authenticator.authenticate_with_token(token)
        elif username and password:
            result = authenticator.authenticate_with_credentials(username, password)
        else:
            raise AuthError("Either token or (username and password) must be provided")
        self._sessions.save(result.session)
        return result.session

    def logout(self) -> None:
        self._sessions.clear()

    def current_session(self) -> Optional[UserSession]:
        return self._sessions.load()

    def require_session(self) -> UserSession:
        session = self._sessions.load()
        if not session:
            raise AuthorizationRequiredError("Not logged in. Use 'red login' to authenticate.")
        return session

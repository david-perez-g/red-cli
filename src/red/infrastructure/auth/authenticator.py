"""Redmine authentication helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from urllib.parse import urljoin

import requests

from ...domain.exceptions import AuthError
from ...domain.models import UserSession


@dataclass
class AuthenticationResult:
    session: UserSession


class RedmineAuthenticator:
    """Perform Redmine authentication workflows."""

    def __init__(self, server_url: str):
        self._server_url = server_url.rstrip("/")
        self._session = requests.Session()

    def authenticate_with_token(self, api_token: str) -> AuthenticationResult:
        self._session.headers.update(
            {
                "X-Redmine-API-Key": api_token,
                "Content-Type": "application/json",
            }
        )
        user_payload = self._get_current_user()
        if not user_payload:
            self._raise_for_current_user()
        session = UserSession(
            server_url=self._server_url,
            user_id=user_payload["id"],
            user_name=f"{user_payload['firstname']} {user_payload['lastname']}",
            api_token=api_token,
        )
        return AuthenticationResult(session=session)

    def authenticate_with_credentials(self, username: str, password: str) -> AuthenticationResult:
        auth_url = urljoin(self._server_url + "/", "users/current.json")
        response = requests.get(
            auth_url,
            auth=(username, password),
            headers={"Content-Type": "application/json"},
        )
        if response.status_code != 200:
            raise AuthError("Invalid credentials or server URL")
        user_payload = response.json()["user"]
        api_token = user_payload.get("api_key")
        if not api_token:
            raise AuthError("User does not have API access enabled")
        session = UserSession(
            server_url=self._server_url,
            user_id=user_payload["id"],
            user_name=f"{user_payload['firstname']} {user_payload['lastname']}",
            api_token=api_token,
        )
        return AuthenticationResult(session=session)

    def _get_current_user(self) -> Optional[dict]:
        try:
            url = urljoin(self._server_url + "/", "users/current.json")
            response = self._session.get(url)
            if response.status_code == 200:
                return response.json()["user"]
            return None
        except requests.RequestException:
            return None

    def _raise_for_current_user(self) -> None:
        try:
            url = urljoin(self._server_url + "/", "users/current.json")
            response = self._session.get(url)
        except requests.RequestException as exc:
            raise AuthError(f"Network error: {exc}") from exc

        if response.status_code == 401:
            raise AuthError("Invalid API token")
        if response.status_code == 403:
            raise AuthError("API access forbidden - check if API is enabled for your user")
        if response.status_code >= 400:
            raise AuthError(f"Server error: {response.status_code} - {response.text}")
        raise AuthError("Unexpected response from server")

"""Filesystem-backed configuration repository."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from ...domain.models import UserSession


class SessionRepository:
    """Persist and retrieve user session data."""

    def __init__(self, base_dir: Optional[Path] = None):
        self._config_dir = (base_dir or Path.home() / ".red").expanduser()
        self._session_file = self._config_dir / "session.json"
        self._config_dir.mkdir(parents=True, exist_ok=True)

    def save(self, session: UserSession) -> None:
        payload = session.to_dict()
        with self._session_file.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)

    def load(self) -> Optional[UserSession]:
        if not self._session_file.exists():
            return None
        try:
            with self._session_file.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except (json.JSONDecodeError, OSError):
            return None
        try:
            return UserSession.from_dict(payload)
        except TypeError:
            return None

    def clear(self) -> None:
        if self._session_file.exists():
            self._session_file.unlink()

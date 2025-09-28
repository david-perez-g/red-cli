# src/red/config.py
"""Configuration and session management for red CLI."""

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict


@dataclass
class UserSession:
    """User session data."""
    server_url: str
    user_id: int
    user_name: str
    api_token: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserSession':
        return cls(**data)


class Config:
    """Configuration manager for red CLI."""

    def __init__(self):
        self.config_dir = Path.home() / '.red'
        self.session_file = self.config_dir / 'session.json'
        self._ensure_config_dir()

    def _ensure_config_dir(self):
        """Ensure configuration directory exists."""
        self.config_dir.mkdir(exist_ok=True)

    def save_session(self, session: UserSession) -> None:
        """Save user session to disk."""
        with open(self.session_file, 'w') as f:
            json.dump(session.to_dict(), f, indent=2)

    def load_session(self) -> Optional[UserSession]:
        """Load user session from disk."""
        if not self.session_file.exists():
            return None

        try:
            with open(self.session_file, 'r') as f:
                data = json.load(f)
            return UserSession.from_dict(data)
        except (json.JSONDecodeError, KeyError):
            return None

    def clear_session(self) -> None:
        """Clear user session."""
        if self.session_file.exists():
            self.session_file.unlink()

    def is_logged_in(self) -> bool:
        """Check if user is logged in."""
        return self.load_session() is not None

    def get_session(self) -> Optional[UserSession]:
        """Get current session."""
        return self.load_session()


# Global config instance
config = Config()
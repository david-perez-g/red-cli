"""Environment helper utilities."""

from __future__ import annotations

from functools import lru_cache
from typing import Optional


@lru_cache
def resolve_server_url(raw_url: str) -> str:
    """Normalize user-provided Redmine server URLs."""
    url = (raw_url or "").strip()
    if not url:
        raise ValueError("Server URL cannot be empty")
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url.rstrip("/")


def get_environment_variable(name: str, default: Optional[str] = None) -> Optional[str]:
    from os import getenv

    return getenv(name, default)

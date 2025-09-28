"""Shared symbol palette with emoji/ASCII fallbacks."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Dict, Optional

import click


@dataclass(frozen=True)
class Symbol:
    """Represents a symbol with emoji and ASCII variants."""

    emoji: str
    ascii: str


def _resolve_stream(stream) -> click.utils.LazyFile:
    if stream is not None:
        return stream
    resolved = click.get_text_stream("stdout")
    if resolved is not None:
        return resolved
    return sys.stdout


def _should_use_emoji(stream) -> bool:
    """Return True when emojis should be used for the provided stream."""

    if os.environ.get("RED_FORCE_ASCII"):
        return False
    if os.environ.get("RED_FORCE_EMOJI"):
        return True

    resolved = _resolve_stream(stream)
    try:
        return resolved.isatty()
    except Exception:  # pragma: no cover - defensive guard
        return False


def use_emoji(stream=None) -> bool:
    """Public helper that mirrors the emoji decision logic."""

    return _should_use_emoji(stream)


class SymbolPalette:
    """Provides convenient access to application symbols."""

    def __init__(self, mapping: Dict[str, Symbol]):
        self._mapping = mapping

    def get(self, name: str, *, stream=None, default: Optional[str] = None) -> str:
        symbol = self._mapping.get(name)
        if symbol is None:
            if default is not None:
                return default
            raise KeyError(name)

        if _should_use_emoji(stream):
            return symbol.emoji
        return symbol.ascii

    def __getattr__(self, name: str) -> str:
        try:
            return self.get(name)
        except KeyError as exc:  # pragma: no cover - delegated to get
            raise AttributeError(name) from exc


SYMBOLS = SymbolPalette(
    {
        "search": Symbol("🔍", "[SEARCH]"),
        "list": Symbol("📋", "[LIST]"),
        "ellipsis": Symbol("…", "..."),
        "error": Symbol("❌", "[ERROR]"),
        "auth": Symbol("🔐", "[AUTH]"),
        "success": Symbol("✅", "[OK]"),
        "warning": Symbol("⚠", "[WARN]"),
        "info": Symbol("ℹ", "[INFO]"),
        "goodbye": Symbol("👋", "[BYE]"),
        "unknown": Symbol("❓", "[UNKNOWN]"),
        "person": Symbol("👤", "[USER]"),
        "summary": Symbol("📈", "[SUMMARY]"),
        "project": Symbol("🏢", "[PROJECT]"),
        "flame": Symbol("🔥", "[RECENT]"),
        "clock": Symbol("⏰", "[TIME]"),
        "chart": Symbol("📊", "[OVERVIEW]"),
        "tag": Symbol("🏷", "[TRACKER]"),
    }
)

__all__ = ["Symbol", "SymbolPalette", "SYMBOLS", "use_emoji"]

"""Spinner helper for CLI feedback."""

from __future__ import annotations

import threading
from typing import Iterable, List, Optional

import click


class Spinner:
    """Context manager that renders a spinner while a block executes."""

    def __init__(self, message: str = "Loading...", spinner_chars: Optional[Iterable[str]] = None):
        self._message = message
        self._chars: List[str] = list(spinner_chars or ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"])
        self._stop_event: Optional[threading.Event] = None
        self._thread: Optional[threading.Thread] = None

    def __enter__(self) -> "Spinner":
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._spin, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._stop_event:
            self._stop_event.set()
        if self._thread:
            self._thread.join()

    def _spin(self) -> None:
        import time

        i = 0
        assert self._stop_event is not None
        while not self._stop_event.is_set():
            frame = self._chars[i % len(self._chars)]
            click.echo(f"\r{frame} {self._message}", nl=False)
            time.sleep(0.1)
            i += 1
        line_length = len(self._chars[0]) + 1 + len(self._message)
        click.echo(f"\r{' ' * line_length}\r", nl=False)

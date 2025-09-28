"""Spinner helper for CLI feedback."""

from __future__ import annotations

import threading
from typing import Iterable, List, Optional

import click

from .symbols import use_emoji


class Spinner:
    """Context manager that renders a spinner while a block executes."""

    def __init__(
        self,
        message: str = "Loading...",
        spinner_chars: Optional[Iterable[str]] = None,
        stream=None,
    ):
        self._message = message
        self._stream = stream or click.get_text_stream("stdout")
        if self._stream is None:
            import sys

            self._stream = sys.stdout

        supports_emoji = use_emoji(self._stream)
        default_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"] if supports_emoji else ["-", "\\", "|", "/"]
        self._chars: List[str] = list(spinner_chars or default_chars)
        self._stop_event: Optional[threading.Event] = None
        self._thread: Optional[threading.Thread] = None
        self._interactive = False

    def __enter__(self) -> "Spinner":
        self._interactive = bool(getattr(self._stream, "isatty", lambda: False)())
        if self._interactive:
            self._stop_event = threading.Event()
            self._thread = threading.Thread(target=self._spin, daemon=True)
            self._thread.start()
        else:
            click.echo(self._message, file=self._stream)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if not self._interactive:
            return

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
            click.echo(f"\r{frame} {self._message}", nl=False, file=self._stream)
            time.sleep(0.1)
            i += 1
        line_length = len(self._chars[0]) + 1 + len(self._message)
        click.echo(f"\r{' ' * line_length}\r", nl=False, file=self._stream)

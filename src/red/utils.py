# src/red/utils.py
"""Utility functions for red CLI."""

import re
from typing import Iterator, List, Optional
from pathlib import Path
import csv
import json
import threading

RANGE_RE = re.compile(r"^(\d+)\.\.(\d+)$")


def expand_range_token(token: str) -> Iterator[int]:
    """Expand a range token like '1..10' into individual numbers."""
    token = token.strip()
    if not token:
        return
    m = RANGE_RE.match(token)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        step = 1 if a <= b else -1
        # range end inclusive
        for i in range(a, b + step, step):
            yield i
    else:
        yield int(token)


def parse_ids(specs: List[str]) -> Iterator[int]:
    """
    Parse ID specifications into individual IDs.

    Accept forms:
      - "1..10"
      - "1,3,5..8"
      - multiple args: "1..5" "7,9"
      - individual numbers: "1" "2" "3"
    Returns an iterator (doesn't build the entire list).
    """
    for spec in specs:
        for part in spec.split(","):
            part = part.strip()
            if not part:
                continue
            for n in expand_range_token(part):
                yield n


def read_csv_file(file_path: str) -> List[dict]:
    """Read CSV file and return list of dictionaries."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)


def write_csv_file(file_path: str, data: List[dict], fieldnames: List[str]) -> None:
    """Write data to CSV file."""
    path = Path(file_path)
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


def format_datetime(dt) -> str:
    """Format datetime for display."""
    if hasattr(dt, 'strftime'):
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    return str(dt)


def truncate_text(text: str, max_length: int = 50) -> str:
    """Truncate text to max_length with ellipsis."""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + '...'


def parse_date_range(date_range: str) -> tuple[str, str]:
    """Parse date range string like '2025-01-01..2025-01-31'."""
    if '..' not in date_range:
        raise ValueError("Date range must be in format 'start..end'")

    start, end = date_range.split('..', 1)
    return start.strip(), end.strip()


def validate_server_url(url: str) -> str:
    """Validate and normalize server URL."""
    url = url.strip()
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    return url.rstrip('/')


def status_name_to_id(status_name: str) -> Optional[int]:
    """Convert status name to ID (simplified mapping)."""
    # This would need to be expanded with actual Redmine status mappings
    status_map = {
        'new': 1,
        'in progress': 2,
        'resolved': 3,
        'feedback': 4,
        'closed': 5,
        'rejected': 6,
        'open': 'open',  # Special case
        'closed': 'closed'  # Special case
    }
    return status_map.get(status_name.lower())


def tracker_name_to_id(tracker_name: str) -> Optional[int]:
    """Convert tracker name to ID (simplified mapping)."""
    # This would need to be expanded with actual Redmine tracker mappings
    tracker_map = {
        'bug': 1,
        'feature': 2,
        'support': 3,
        'task': 4
    }
    return tracker_map.get(tracker_name.lower())


class Spinner:
    """Context manager for showing a spinning animation during operations."""
    
    def __init__(self, message: str = "Loading...", spinner_chars: List[str] = None):
        self.message = message
        self.spinner_chars = spinner_chars or ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        self.stop_event = None
        self.thread = None
    
    def __enter__(self):
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self._spin)
        self.thread.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_event.set()
        self.thread.join()
    
    def _spin(self):
        """Internal spinner animation function."""
        import click
        import time
        
        i = 0
        while not self.stop_event.is_set():
            click.echo(f'\r{self.spinner_chars[i % len(self.spinner_chars)]} {self.message}', nl=False)
            time.sleep(0.1)
            i += 1
        click.echo('\r', nl=False)  # Clear the spinner line

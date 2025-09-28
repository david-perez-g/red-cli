"""Domain utility helpers shared across services."""

from __future__ import annotations

import re
from typing import Iterator, List, Optional, Tuple

RANGE_RE = re.compile(r"^(\d+)\.\.(\d+)$")


def expand_range_token(token: str) -> Iterator[int]:
    token = token.strip()
    if not token:
        return
    match = RANGE_RE.match(token)
    if match:
        start, end = int(match.group(1)), int(match.group(2))
        step = 1 if start <= end else -1
        for value in range(start, end + step, step):
            yield value
    else:
        yield int(token)


def parse_ids(specs: List[str]) -> Iterator[int]:
    for spec in specs:
        for part in spec.split(","):
            part = part.strip()
            if not part:
                continue
            yield from expand_range_token(part)


def parse_date_range(range_spec: str) -> Tuple[str, str]:
    if ".." not in range_spec:
        raise ValueError("Date range must be in format 'start..end'")
    start, end = range_spec.split("..", 1)
    return start.strip(), end.strip()


def status_name_to_id(status_name: str) -> Optional[int]:
    mapping = {
        "new": 1,
        "in progress": 2,
        "resolved": 3,
        "feedback": 4,
        "closed": 5,
        "rejected": 6,
        "open": "open",
        "closed": "closed",
    }
    return mapping.get(status_name.lower()) if status_name else None


def tracker_name_to_id(tracker_name: str) -> Optional[int]:
    mapping = {
        "bug": 1,
        "feature": 2,
        "support": 3,
        "task": 4,
    }
    return mapping.get(tracker_name.lower()) if tracker_name else None

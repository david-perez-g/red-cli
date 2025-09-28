# src/red/models.py
"""Data models for red CLI."""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from datetime import datetime


@dataclass
class Issue:
    """Redmine issue model."""
    id: int
    subject: str
    description: Optional[str]
    status: str
    tracker: str
    priority: str
    author: str
    assigned_to: Optional[str]
    created_on: datetime
    updated_on: datetime
    done_ratio: int
    estimated_hours: Optional[float]

    @classmethod
    def from_api_data(cls, data: Dict[str, Any]) -> 'Issue':
        """Create Issue from Redmine API data."""
        return cls(
            id=data['id'],
            subject=data['subject'],
            description=data.get('description'),
            status=data['status']['name'],
            tracker=data['tracker']['name'],
            priority=data['priority']['name'],
            author=data['author']['name'],
            assigned_to=data.get('assigned_to', {}).get('name') if data.get('assigned_to') else None,
            created_on=datetime.fromisoformat(data['created_on'].replace('Z', '+00:00')),
            updated_on=datetime.fromisoformat(data['updated_on'].replace('Z', '+00:00')),
            done_ratio=data.get('done_ratio', 0),
            estimated_hours=data.get('estimated_hours')
        )


@dataclass
class TimeEntry:
    """Time entry model."""
    id: int
    issue_id: int
    hours: float
    comments: str
    spent_on: datetime
    user: str
    activity: str

    @classmethod
    def from_api_data(cls, data: Dict[str, Any]) -> 'TimeEntry':
        """Create TimeEntry from Redmine API data."""
        return cls(
            id=data['id'],
            issue_id=data['issue']['id'],
            hours=data['hours'],
            comments=data.get('comments', ''),
            spent_on=datetime.fromisoformat(data['spent_on']),
            user=data['user']['name'],
            activity=data['activity']['name']
        )


@dataclass
class Project:
    """Project model."""
    id: int
    name: str
    identifier: str
    description: Optional[str]

    @classmethod
    def from_api_data(cls, data: Dict[str, Any]) -> 'Project':
        """Create Project from Redmine API data."""
        return cls(
            id=data['id'],
            name=data['name'],
            identifier=data['identifier'],
            description=data.get('description')
        )
"""Domain models representing Redmine entities used by the CLI."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class UserSession:
    """Authenticated user session details."""

    server_url: str
    user_id: int
    user_name: str
    api_token: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserSession":
        return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "server_url": self.server_url,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "api_token": self.api_token,
        }


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
    project: str
    project_identifier: Optional[str]
    created_on: datetime
    updated_on: datetime
    done_ratio: int
    estimated_hours: Optional[float]

    @classmethod
    def from_api_data(cls, data: Dict[str, Any]) -> "Issue":
        return cls(
            id=data["id"],
            subject=data["subject"],
            description=data.get("description"),
            status=data["status"]["name"],
            tracker=data["tracker"]["name"],
            priority=data["priority"]["name"],
            author=data["author"]["name"],
            assigned_to=data.get("assigned_to", {}).get("name") if data.get("assigned_to") else None,
            project=data["project"]["name"],
            project_identifier=data["project"].get("identifier") if data.get("project") else None,
            created_on=datetime.fromisoformat(data["created_on"].replace("Z", "+00:00")).replace(tzinfo=None),
            updated_on=datetime.fromisoformat(data["updated_on"].replace("Z", "+00:00")).replace(tzinfo=None),
            done_ratio=data.get("done_ratio", 0),
            estimated_hours=data.get("estimated_hours"),
        )


@dataclass
class TimeEntry:
    """Redmine time entry model."""

    id: int
    issue_id: int
    hours: float
    comments: str
    spent_on: datetime
    user: str
    activity: str

    @classmethod
    def from_api_data(cls, data: Dict[str, Any]) -> "TimeEntry":
        return cls(
            id=data["id"],
            issue_id=data["issue"]["id"],
            hours=data["hours"],
            comments=data.get("comments", ""),
            spent_on=datetime.fromisoformat(data["spent_on"]),
            user=data["user"]["name"],
            activity=data["activity"]["name"],
        )


@dataclass
class Project:
    """Redmine project model."""

    id: int
    name: str
    identifier: str
    description: Optional[str]

    @classmethod
    def from_api_data(cls, data: Dict[str, Any]) -> "Project":
        return cls(
            id=data["id"],
            name=data["name"],
            identifier=data["identifier"],
            description=data.get("description"),
        )

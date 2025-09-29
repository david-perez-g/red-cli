"""HTTP client for the Redmine REST API."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import requests

from ...domain.exceptions import AuthorizationRequiredError
from ...domain.models import UserSession


class RedmineClient:
    """Thin wrapper around requests.Session aware of Redmine semantics."""

    def __init__(self, session: UserSession):
        if not session.api_token:
            raise AuthorizationRequiredError("Missing API token")
        self._session = requests.Session()
        self._session.headers.update(
            {
                "X-Redmine-API-Key": session.api_token,
                "Content-Type": "application/json",
            }
        )
        self._base_url = session.server_url.rstrip("/") + "/"

    def _request(self, method: str, endpoint: str, *, params: Optional[Dict[str, Any]] = None, json: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = urljoin(self._base_url, endpoint)
        response = self._session.request(method, url, params=params, json=json)
        if response.status_code == 401:
            raise AuthorizationRequiredError("Authentication failed")
        if response.status_code == 403:
            raise AuthorizationRequiredError("Access denied")
        if response.status_code >= 400:
            raise RuntimeError(f"API error: {response.status_code} - {response.text}")
        return response.json()

    def _resolve_project_id(self, project_name_or_identifier: str) -> str:
        """Resolve a project name or identifier to its ID."""
        projects = self.list_projects()
        for project in projects:
            name_matches = project.get("name") == project_name_or_identifier
            identifier_matches = project.get("identifier") == project_name_or_identifier
            if name_matches or identifier_matches:
                return str(project["id"])
        return project_name_or_identifier

    def list_projects(self) -> List[Dict[str, Any]]:
        payload = self._request("GET", "projects.json")
        return payload.get("projects", [])

    def list_issues(self, **filters: Any) -> List[Dict[str, Any]]:
        params: Dict[str, Any] = {}
        if "assigned_to_id" in filters:
            params["assigned_to_id"] = filters["assigned_to_id"]
        if "status_id" in filters:
            params["status_id"] = filters["status_id"]
        if "tracker_id" in filters:
            params["tracker_id"] = filters["tracker_id"]
        if "project_id" in filters:
            project_id = filters["project_id"]
            if isinstance(project_id, str) and not str(project_id).isdigit():
                project_id = self._resolve_project_id(project_id)
            params["project_id"] = project_id
        if "limit" in filters and filters["limit"] is not None:
            params["limit"] = filters["limit"]
        if "offset" in filters and filters["offset"] is not None:
            params["offset"] = filters["offset"]
        if "issue_ids" in filters:
            # For now return empty list; future work may iterate calls.
            return []
        payload = self._request("GET", "issues.json", params=params)
        return payload.get("issues", [])

    def get_issue(self, issue_id: int) -> Dict[str, Any]:
        payload = self._request("GET", f"issues/{issue_id}.json")
        return payload.get("issue", {})

    def create_issue(self, issue_data: Dict[str, Any]) -> Dict[str, Any]:
        payload = self._request("POST", "issues.json", json={"issue": issue_data})
        return payload.get("issue", {})

    def update_issue(self, issue_id: int, issue_data: Dict[str, Any]) -> None:
        self._request("PUT", f"issues/{issue_id}.json", json={"issue": issue_data})

    def list_time_entries(self, **filters: Any) -> List[Dict[str, Any]]:
        params: Dict[str, Any] = {}
        if "user_id" in filters:
            params["user_id"] = filters["user_id"]
        if "from_date" in filters:
            params["from"] = filters["from_date"]
        if "to_date" in filters:
            params["to"] = filters["to_date"]
        if "issue_id" in filters:
            params["issue_id"] = filters["issue_id"]
        payload = self._request("GET", "time_entries.json", params=params)
        return payload.get("time_entries", [])

    def log_time(self, issue_id: int, hours: float, comments: str = "") -> Dict[str, Any]:
        payload = self._request(
            "POST",
            "time_entries.json",
            json={"time_entry": {"issue_id": issue_id, "hours": hours, "comments": comments}},
        )
        return payload.get("time_entry", {})

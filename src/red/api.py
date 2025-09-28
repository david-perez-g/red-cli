# src/red/api.py
"""Redmine API client for red CLI."""

import requests
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin

from .auth import require_auth
from .config import UserSession


class RedmineAPI:
    """Redmine API client."""

    def __init__(self, session: UserSession):
        self.session = requests.Session()
        self.server_url = session.server_url
        self.session.headers.update({
            'X-Redmine-API-Key': session.api_token,
            'Content-Type': 'application/json'
        })

    def _get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make GET request to Redmine API."""
        url = urljoin(self.server_url + '/', endpoint)
        response = self.session.get(url, params=params)

        if response.status_code == 401:
            raise PermissionError("Authentication failed")
        elif response.status_code == 403:
            raise PermissionError("Access denied")
        elif response.status_code >= 400:
            raise RuntimeError(f"API error: {response.status_code} - {response.text}")

        return response.json()

    def _post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make POST request to Redmine API."""
        url = urljoin(self.server_url + '/', endpoint)
        response = self.session.post(url, json=data)

        if response.status_code == 401:
            raise PermissionError("Authentication failed")
        elif response.status_code == 403:
            raise PermissionError("Access denied")
        elif response.status_code >= 400:
            raise RuntimeError(f"API error: {response.status_code} - {response.text}")

        return response.json()

    def _put(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make PUT request to Redmine API."""
        url = urljoin(self.server_url + '/', endpoint)
        response = self.session.put(url, json=data)

        if response.status_code == 401:
            raise PermissionError("Authentication failed")
        elif response.status_code == 403:
            raise PermissionError("Access denied")
        elif response.status_code >= 400:
            raise RuntimeError(f"API error: {response.status_code} - {response.text}")

        return response.json()

    def get_issues(self, **filters) -> List[Dict[str, Any]]:
        """Get issues with optional filters."""
        params = {}

        # Build query parameters from filters
        if 'assigned_to_id' in filters:
            params['assigned_to_id'] = filters['assigned_to_id']
        if 'status_id' in filters:
            params['status_id'] = filters['status_id']
        if 'tracker_id' in filters:
            params['tracker_id'] = filters['tracker_id']
        if 'issue_ids' in filters:
            # For specific issue IDs, we might need multiple calls
            # For now, return empty list as placeholder
            return []

        response = self._get('issues.json', params=params)
        return response.get('issues', [])

    def get_issue(self, issue_id: int) -> Dict[str, Any]:
        """Get single issue by ID."""
        response = self._get(f'issues/{issue_id}.json')
        return response.get('issue', {})

    def create_issue(self, issue_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new issue."""
        data = {'issue': issue_data}
        response = self._post('issues.json', data)
        return response.get('issue', {})

    def update_issue(self, issue_id: int, issue_data: Dict[str, Any]) -> None:
        """Update an existing issue."""
        data = {'issue': issue_data}
        self._put(f'issues/{issue_id}.json', data)

    def get_time_entries(self, **filters) -> List[Dict[str, Any]]:
        """Get time entries with optional filters."""
        params = {}

        if 'user_id' in filters:
            params['user_id'] = filters['user_id']
        if 'from_date' in filters:
            params['from'] = filters['from_date']
        if 'to_date' in filters:
            params['to'] = filters['to_date']

        response = self._get('time_entries.json', params=params)
        return response.get('time_entries', [])

    def log_time(self, issue_id: int, hours: float, comments: str = "") -> Dict[str, Any]:
        """Log time for an issue."""
        data = {
            'time_entry': {
                'issue_id': issue_id,
                'hours': hours,
                'comments': comments
            }
        }
        response = self._post('time_entries.json', data)
        return response.get('time_entry', {})


def get_api_client() -> RedmineAPI:
    """Get authenticated API client."""
    session = require_auth()
    return RedmineAPI(session)
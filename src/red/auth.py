# src/red/auth.py
"""Authentication module for red CLI."""

import requests
from typing import Optional, Tuple
from urllib.parse import urljoin

from .config import config, UserSession


class AuthError(Exception):
    """Authentication error."""
    pass


class RedmineAuthenticator:
    """Handles Redmine authentication."""

    def __init__(self, server_url: str):
        self.server_url = server_url.rstrip('/')
        self.session = requests.Session()

    def authenticate_with_token(self, api_token: str) -> UserSession:
        """Authenticate using API token."""
        # Set up session with token
        self.session.headers.update({
            'X-Redmine-API-Key': api_token,
            'Content-Type': 'application/json'
        })

        # Test authentication by getting current user
        user_data = self._get_current_user()
        if not user_data:
            # Debug: try to get more info about the failure
            try:
                url = urljoin(self.server_url + '/', 'users/current.json')
                response = self.session.get(url)
                if response.status_code == 401:
                    raise AuthError("Invalid API token")
                elif response.status_code == 403:
                    raise AuthError("API access forbidden - check if API is enabled for your user")
                elif response.status_code >= 400:
                    raise AuthError(f"Server error: {response.status_code} - {response.text}")
                else:
                    raise AuthError("Unexpected response from server")
            except requests.RequestException as e:
                raise AuthError(f"Network error: {e}")

        return UserSession(
            server_url=self.server_url,
            user_id=user_data['id'],
            user_name=user_data['firstname'] + ' ' + user_data['lastname'],
            api_token=api_token
        )

    def authenticate_with_credentials(self, username: str, password: str) -> UserSession:
        """Authenticate using username and password."""
        # First, get API token using basic auth
        auth_url = urljoin(self.server_url + '/', 'users/current.json')

        response = requests.get(
            auth_url,
            auth=(username, password),
            headers={'Content-Type': 'application/json'}
        )

        if response.status_code != 200:
            raise AuthError("Invalid credentials or server URL")

        user_data = response.json()['user']

        # Extract API token from user data
        api_token = user_data.get('api_key')
        if not api_token:
            raise AuthError("User does not have API access enabled")

        return UserSession(
            server_url=self.server_url,
            user_id=user_data['id'],
            user_name=user_data['firstname'] + ' ' + user_data['lastname'],
            api_token=api_token
        )

    def _get_current_user(self) -> Optional[dict]:
        """Get current user information."""
        try:
            url = urljoin(self.server_url + '/', 'users/current.json')
            response = self.session.get(url)

            if response.status_code == 200:
                return response.json()['user']
            return None
        except requests.RequestException:
            return None


def login(server_url: str, token: Optional[str] = None, username: Optional[str] = None, password: Optional[str] = None) -> UserSession:
    """Login to Redmine and save session."""
    authenticator = RedmineAuthenticator(server_url)

    if token:
        session = authenticator.authenticate_with_token(token)
    elif username and password:
        session = authenticator.authenticate_with_credentials(username, password)
    else:
        raise AuthError("Either token or (username and password) must be provided")

    config.save_session(session)
    return session


def logout():
    """Logout and clear session."""
    config.clear_session()


def get_current_session() -> Optional[UserSession]:
    """Get current user session."""
    return config.get_session()


def require_auth() -> UserSession:
    """Require authentication and return session."""
    session = get_current_session()
    if not session:
        raise AuthError("Not logged in. Use 'red login' to authenticate.")
    return session
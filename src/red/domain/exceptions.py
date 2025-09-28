"""Domain-level exception definitions."""


class AuthError(Exception):
    """Raised when authentication or session state is invalid."""


class AuthorizationRequiredError(AuthError):
    """Raised when an operation requires an authenticated session."""

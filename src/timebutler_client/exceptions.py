"""Custom exceptions for the Timebutler client."""

__all__ = [
    "TimebutlerApiError",
    "TimebutlerAuthenticationError",
    "TimebutlerConflictError",
    "TimebutlerError",
    "TimebutlerMissingCredentialsError",
    "TimebutlerNotFoundError",
    "TimebutlerParseError",
    "TimebutlerPermissionError",
    "TimebutlerRateLimitError",
    "TimebutlerServerError",
    "TimebutlerValidationError",
]


class TimebutlerError(Exception):
    """Base exception for Timebutler client errors."""


class TimebutlerAuthenticationError(TimebutlerError):
    """Raised when API authentication fails (HTTP 401/403)."""


class TimebutlerRateLimitError(TimebutlerError):
    """Raised when rate limit is exceeded (HTTP 429)."""

    def __init__(self, retry_after: int | None = None) -> None:
        self.retry_after = retry_after
        message = f"Rate limit exceeded. Retry after {retry_after}s" if retry_after else "Rate limit exceeded"
        super().__init__(message)


class TimebutlerServerError(TimebutlerError):
    """Raised for 5xx server errors."""

    def __init__(self, status_code: int, message: str = "") -> None:
        self.status_code = status_code
        super().__init__(f"Server error {status_code}: {message}" if message else f"Server error {status_code}")


class TimebutlerParseError(TimebutlerError):
    """Raised when API response cannot be parsed."""


class TimebutlerApiError(TimebutlerError):
    """Base for v2 HTTP errors that carry the status code and (truncated) response body."""

    def __init__(self, status_code: int, response_text: str = "") -> None:
        self.status_code = status_code
        self.response_text = response_text
        super().__init__(f"HTTP {status_code}: {response_text}" if response_text else f"HTTP {status_code}")


class TimebutlerValidationError(TimebutlerApiError):
    """Raised when the API rejects the request as invalid (HTTP 400/422)."""


class TimebutlerNotFoundError(TimebutlerApiError):
    """Raised when the requested resource does not exist (HTTP 404)."""


class TimebutlerConflictError(TimebutlerApiError):
    """Raised on state conflicts (HTTP 409), e.g. month closed, clock already running, duplicate entry."""


class TimebutlerPermissionError(TimebutlerAuthenticationError):
    """Raised when the authenticated user is not allowed to perform the action (HTTP 403, v2 only)."""

    def __init__(self, status_code: int, response_text: str = "") -> None:
        self.status_code = status_code
        self.response_text = response_text
        super().__init__(
            f"Permission denied (HTTP {status_code}): {response_text}" if response_text else "Permission denied"
        )


class TimebutlerMissingCredentialsError(TimebutlerError):
    """Raised when a method needs a credential the client was not configured with."""

    def __init__(self, credential: str) -> None:
        self.credential = credential
        super().__init__(f"This method requires the client to be configured with '{credential}'")

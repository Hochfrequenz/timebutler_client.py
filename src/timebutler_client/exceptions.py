"""Custom exceptions for the Timebutler client."""

__all__ = [
    "TimebutlerError",
    "TimebutlerAuthenticationError",
    "TimebutlerRateLimitError",
    "TimebutlerServerError",
    "TimebutlerParseError",
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

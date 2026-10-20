"""Tests for the exception hierarchy."""

from timebutler_client import (
    TimebutlerAuthenticationError,
    TimebutlerConflictError,
    TimebutlerError,
    TimebutlerMissingCredentialsError,
    TimebutlerNotFoundError,
    TimebutlerPermissionError,
    TimebutlerValidationError,
)
from timebutler_client.exceptions import TimebutlerApiError


class TestExceptions:
    """Tests for the new v2 exceptions."""

    def test_api_errors_carry_status_and_text(self) -> None:
        for cls in (TimebutlerValidationError, TimebutlerNotFoundError, TimebutlerConflictError):
            error = cls(409, "locked")
            assert isinstance(error, TimebutlerApiError)
            assert isinstance(error, TimebutlerError)
            assert error.status_code == 409
            assert error.response_text == "locked"
            assert "409" in str(error)
            assert "locked" in str(error)

    def test_permission_error_is_authentication_error(self) -> None:
        error = TimebutlerPermissionError(403, "not allowed")
        assert isinstance(error, TimebutlerAuthenticationError)
        assert error.status_code == 403
        assert error.response_text == "not allowed"

    def test_missing_credentials_error_names_credential(self) -> None:
        error = TimebutlerMissingCredentialsError("personal_token")
        assert isinstance(error, TimebutlerError)
        assert error.credential == "personal_token"
        assert "personal_token" in str(error)

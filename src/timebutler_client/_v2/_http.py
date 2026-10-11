"""HTTP transport for the Timebutler API v2 (JSON, bearer auth)."""

import json as jsonlib
from collections.abc import Mapping
from typing import Any, TypeVar

import aiohttp
from pydantic import BaseModel, TypeAdapter, ValidationError

from timebutler_client.exceptions import (
    TimebutlerAuthenticationError,
    TimebutlerConflictError,
    TimebutlerMissingCredentialsError,
    TimebutlerNotFoundError,
    TimebutlerParseError,
    TimebutlerPermissionError,
    TimebutlerRateLimitError,
    TimebutlerServerError,
    TimebutlerValidationError,
)

V2_BASE_URL = "https://app.timebutler.com/api/v2"

M = TypeVar("M", bound=BaseModel)
_MAX_ERROR_TEXT = 200


def raise_for_v2_status(status: int, text: str, headers: Mapping[str, str]) -> None:
    """Map a non-2xx v2 response to the matching Timebutler exception."""
    if status < 400:
        return
    text = text[:_MAX_ERROR_TEXT]
    if status == 401:
        raise TimebutlerAuthenticationError(f"Invalid or expired token: {text}" if text else "Invalid or expired token")
    if status == 403:
        raise TimebutlerPermissionError(status, text)
    if status in (400, 422):
        raise TimebutlerValidationError(status, text)
    if status == 404:
        raise TimebutlerNotFoundError(status, text)
    if status == 409:
        raise TimebutlerConflictError(status, text)
    if status == 429:
        retry_after = headers.get("Retry-After", "")
        raise TimebutlerRateLimitError(int(retry_after) if retry_after.isdigit() else None)
    if status >= 500:
        raise TimebutlerServerError(status, text)
    raise TimebutlerValidationError(status, text)


def parse_model(model: type[M], data: Any) -> M:
    """Validate a JSON object into a v2 model."""
    try:
        return model.model_validate(data)
    except ValidationError as e:
        raise TimebutlerParseError(f"Failed to parse API response as {model.__name__}: {e}") from e


def parse_model_list(model: type[M], data: Any) -> list[M]:
    """Validate a JSON array into a list of v2 models."""
    try:
        return TypeAdapter(list[model]).validate_python(data)  # type: ignore[valid-type]
    except ValidationError as e:
        raise TimebutlerParseError(f"Failed to parse API response as list[{model.__name__}]: {e}") from e


def path_id(value: int | str) -> str:
    """Validate an ID for use in a URL path. v2 models carry IDs as strings, so both are accepted."""
    text = str(value)
    if not text.isdigit():
        raise ValueError(f"ID must be a non-negative integer, got {value!r}")
    return text


class V2Transport:
    """Holds v2 credentials and performs authenticated requests."""

    def __init__(
        self,
        base_url: str,
        timeout: float,
        access_token: str,
        refresh_token: str | None = None,
        client_id: str = "public",
        client_secret: str | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.client_id = client_id
        self.client_secret = client_secret

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, str | int] | None = None,
        json: Mapping[str, Any] | None = None,
    ) -> Any:
        """Perform an authenticated request; return parsed JSON or None for empty responses."""
        status, text, headers = await self._send(method, path, params=params, json=json)
        raise_for_v2_status(status, text, headers)
        if status == 204 or not text.strip():
            return None
        try:
            return jsonlib.loads(text)
        except ValueError as e:
            raise TimebutlerParseError(f"Response is not valid JSON: {text[:_MAX_ERROR_TEXT]}") from e

    async def _send(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, str | int] | None,
        json: Mapping[str, Any] | None,
    ) -> tuple[int, str, dict[str, str]]:
        headers = {"Authorization": f"Bearer {self.access_token}", "Accept": "application/json"}
        str_params = {key: str(value) for key, value in params.items()} if params else None
        timeout_config = aiohttp.ClientTimeout(total=self.timeout)
        async with aiohttp.ClientSession(timeout=timeout_config) as session:
            async with session.request(
                method, f"{self.base_url}{path}", headers=headers, params=str_params, json=json
            ) as response:
                return response.status, await response.text(), dict(response.headers)


class V2Mixin:
    """Base for all v2 area mixins. Mixed into TimebutlerClient."""

    _v2: V2Transport | None

    def _require_v2(self) -> V2Transport:
        if self._v2 is None:
            raise TimebutlerMissingCredentialsError("personal_token")
        return self._v2

    async def _v2_request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, str | int] | None = None,
        json: Mapping[str, Any] | None = None,
    ) -> Any:
        return await self._require_v2().request(method, path, params=params, json=json)

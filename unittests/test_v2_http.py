"""Tests for the v2 HTTP transport (headers, error mapping, parsing)."""

import pytest
from aioresponses import aioresponses

from timebutler_client import (
    TimebutlerAuthenticationError,
    TimebutlerConflictError,
    TimebutlerNotFoundError,
    TimebutlerParseError,
    TimebutlerPermissionError,
    TimebutlerRateLimitError,
    TimebutlerServerError,
    TimebutlerValidationError,
)
from timebutler_client._v2._http import parse_model, parse_model_list, path_id
from timebutler_client.models.v2 import ProjectDto
from unittests.v2_helpers import TOKEN, V2, make_client, only_request

# pylint: disable=protected-access


class TestV2Request:
    """V2Transport.request via V2Mixin._v2_request."""

    async def test_sends_bearer_and_accept_headers(self) -> None:
        with aioresponses() as mocked:
            mocked.get(f"{V2}/user/profile", status=200, payload={"id": "1"})
            result = await make_client()._v2_request("GET", "/user/profile")
            call = only_request(mocked)
        assert result == {"id": "1"}
        assert call.kwargs["headers"]["Authorization"] == f"Bearer {TOKEN}"
        assert call.kwargs["headers"]["Accept"] == "application/json"

    async def test_sends_json_body_and_params(self) -> None:
        with aioresponses() as mocked:
            mocked.post(f"{V2}/x?a=1", status=200, payload={})
            await make_client()._v2_request("POST", "/x", params={"a": 1}, json={"b": 2})
            call = only_request(mocked)
        assert call.kwargs["json"] == {"b": 2}
        assert call.kwargs["params"] == {"a": "1"}

    async def test_204_and_empty_body_return_none(self) -> None:
        with aioresponses() as mocked:
            mocked.post(f"{V2}/a", status=204)
            mocked.post(f"{V2}/b", status=200, body="")
            client = make_client()
            assert await client._v2_request("POST", "/a") is None
            assert await client._v2_request("POST", "/b") is None

    @pytest.mark.parametrize(
        ("status", "exc"),
        [
            (400, TimebutlerValidationError),
            (422, TimebutlerValidationError),
            (401, TimebutlerAuthenticationError),
            (403, TimebutlerPermissionError),
            (404, TimebutlerNotFoundError),
            (409, TimebutlerConflictError),
            (500, TimebutlerServerError),
            (502, TimebutlerServerError),
        ],
    )
    async def test_error_mapping(self, status: int, exc: type[Exception]) -> None:
        with aioresponses() as mocked:
            mocked.get(f"{V2}/x", status=status, body='{"message":"boom"}', content_type="application/json")
            with pytest.raises(exc) as excinfo:
                await make_client()._v2_request("GET", "/x")
        assert "boom" in str(excinfo.value)

    async def test_non_json_error_body(self) -> None:
        with aioresponses() as mocked:
            mocked.get(f"{V2}/x", status=502, body="<html>Bad Gateway</html>", content_type="text/html")
            with pytest.raises(TimebutlerServerError, match="Bad Gateway"):
                await make_client()._v2_request("GET", "/x")
            mocked.get(f"{V2}/y", status=400, body="plain text", content_type="text/plain")
            with pytest.raises(TimebutlerValidationError) as excinfo:
                await make_client()._v2_request("GET", "/y")
        assert excinfo.value.response_text == "plain text"

    async def test_error_text_truncated_to_200_chars(self) -> None:
        with aioresponses() as mocked:
            mocked.get(f"{V2}/x", status=409, body="x" * 500)
            with pytest.raises(TimebutlerConflictError) as excinfo:
                await make_client()._v2_request("GET", "/x")
        assert len(excinfo.value.response_text) == 200

    @pytest.mark.parametrize(
        ("header", "expected"), [("30", 30), ("Wed, 21 Oct 2026 07:28:00 GMT", None), (None, None)]
    )
    async def test_rate_limit_retry_after(self, header: str | None, expected: int | None) -> None:
        headers = {"Retry-After": header} if header else {}
        with aioresponses() as mocked:
            mocked.get(f"{V2}/x", status=429, headers=headers)
            with pytest.raises(TimebutlerRateLimitError) as excinfo:
                await make_client()._v2_request("GET", "/x")
        assert excinfo.value.retry_after == expected

    async def test_invalid_json_on_success_is_parse_error(self) -> None:
        with aioresponses() as mocked:
            mocked.get(f"{V2}/x", status=200, body="not json", content_type="application/json")
            with pytest.raises(TimebutlerParseError):
                await make_client()._v2_request("GET", "/x")


class TestParseHelpers:
    """parse_model / parse_model_list / path_id."""

    def test_parse_model_list(self) -> None:
        actual = parse_model_list(ProjectDto, [{"id": "5", "name": "A", "isFavorite": True}])
        assert actual == [ProjectDto.model_validate({"id": "5", "name": "A", "is_favorite": True})]
        assert actual[0].is_favorite is True

    def test_parse_model_rejects_wrong_shape(self) -> None:
        with pytest.raises(TimebutlerParseError):
            parse_model(ProjectDto, ["not", "an", "object"])
        with pytest.raises(TimebutlerParseError):
            parse_model_list(ProjectDto, {"id": "5"})

    @pytest.mark.parametrize("good", [42, "98765"])
    def test_path_id_accepts_int_and_digit_str(self, good: int | str) -> None:
        assert path_id(good) == str(good)

    @pytest.mark.parametrize("bad", ["", "abc", "1/2", -1])
    def test_path_id_rejects_non_digits(self, bad: int | str) -> None:
        with pytest.raises(ValueError):
            path_id(bad)

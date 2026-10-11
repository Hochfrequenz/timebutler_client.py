"""Tests for OAuth password login and token refresh."""

import asyncio
from typing import Any

import pytest
from aioresponses import aioresponses

from timebutler_client import TimebutlerAuthenticationError, TimebutlerClient
from unittests.v2_helpers import V2

# pylint: disable=protected-access

TOKEN_URL = f"{V2}/oauth2/token"
TOKENS = {"access_token": "at-1", "refresh_token": "rt-1", "token_type": "Bearer", "expires_in": 3600}
REFRESHED = {"access_token": "at-2", "refresh_token": "rt-2", "token_type": "Bearer", "expires_in": 3600}


def _form_calls(mocked: aioresponses) -> list[Any]:
    return [
        call.kwargs["data"]
        for (_method, url), calls in mocked.requests.items()
        if str(url) == TOKEN_URL
        for call in calls
    ]


class TestPasswordLogin:
    """TimebutlerClient.from_password"""

    async def test_password_grant(self) -> None:
        with aioresponses() as mocked:
            mocked.post(TOKEN_URL, status=200, payload=TOKENS)
            client = await TimebutlerClient.from_password("user@example.com", "s3cr3t")
            forms = _form_calls(mocked)
        assert forms == [
            {"grant_type": "password", "username": "user@example.com", "password": "s3cr3t", "client_id": "public"}
        ]
        transport = client._require_v2()
        assert (transport.access_token, transport.refresh_token) == ("at-1", "rt-1")

    async def test_client_secret_is_sent(self) -> None:
        with aioresponses() as mocked:
            mocked.post(TOKEN_URL, status=200, payload=TOKENS)
            await TimebutlerClient.from_password("u", "p", client_id="my-app", client_secret="shh")
            forms = _form_calls(mocked)
        assert forms[0]["client_id"] == "my-app"
        assert forms[0]["client_secret"] == "shh"

    async def test_mfa_required_raises(self) -> None:
        with aioresponses() as mocked:
            mocked.post(TOKEN_URL, status=200, payload={"mfa_required": True, "mfa_token": "m", "mfa_expires_in": 300})
            with pytest.raises(TimebutlerAuthenticationError, match="personal token"):
                await TimebutlerClient.from_password("u", "p")

    async def test_invalid_grant_raises(self) -> None:
        with aioresponses() as mocked:
            mocked.post(
                TOKEN_URL,
                status=400,
                payload={"error": "invalid_grant", "error_description": "Invalid username or password"},
            )
            with pytest.raises(TimebutlerAuthenticationError, match="Invalid username or password"):
                await TimebutlerClient.from_password("u", "wrong")


class TestRefresh:
    """Automatic refresh on 401."""

    async def _logged_in(self, mocked: aioresponses) -> TimebutlerClient:
        mocked.post(TOKEN_URL, status=200, payload=TOKENS)
        return await TimebutlerClient.from_password("u", "p")

    async def test_refreshes_once_and_retries(self) -> None:
        with aioresponses() as mocked:
            client = await self._logged_in(mocked)
            mocked.get(f"{V2}/user/profile", status=401)
            mocked.post(TOKEN_URL, status=200, payload=REFRESHED)
            mocked.get(f"{V2}/user/profile", status=200, payload={"id": "1"})
            result = await client._v2_request("GET", "/user/profile")
            forms = _form_calls(mocked)
        assert result == {"id": "1"}
        assert forms[1] == {"grant_type": "refresh_token", "refresh_token": "rt-1", "client_id": "public"}
        assert client._require_v2().refresh_token == "rt-2"

    async def test_second_401_raises(self) -> None:
        with aioresponses() as mocked:
            client = await self._logged_in(mocked)
            mocked.get(f"{V2}/user/profile", status=401)
            mocked.post(TOKEN_URL, status=200, payload=REFRESHED)
            mocked.get(f"{V2}/user/profile", status=401)
            with pytest.raises(TimebutlerAuthenticationError):
                await client._v2_request("GET", "/user/profile")

    async def test_personal_token_never_refreshes(self) -> None:
        client = TimebutlerClient(personal_token="tb_x")
        with aioresponses() as mocked:
            mocked.get(f"{V2}/user/profile", status=401)
            with pytest.raises(TimebutlerAuthenticationError):
                await client._v2_request("GET", "/user/profile")
            assert _form_calls(mocked) == []

    async def test_concurrent_401s_refresh_only_once(self) -> None:
        with aioresponses() as mocked:
            client = await self._logged_in(mocked)
            mocked.get(f"{V2}/user/profile", status=401)
            mocked.get(f"{V2}/user/profile", status=401)
            mocked.post(TOKEN_URL, status=200, payload=REFRESHED)
            mocked.get(f"{V2}/user/profile", status=200, payload={"id": "1"}, repeat=True)
            results = await asyncio.gather(
                client._v2_request("GET", "/user/profile"),
                client._v2_request("GET", "/user/profile"),
            )
            forms = _form_calls(mocked)
        assert list(results) == [{"id": "1"}, {"id": "1"}]
        assert [form["grant_type"] for form in forms] == ["password", "refresh_token"]

    async def test_failed_refresh_is_not_retried(self) -> None:
        with aioresponses() as mocked:
            client = await self._logged_in(mocked)
            for _ in range(3):
                mocked.get(f"{V2}/user/profile", status=401)
            mocked.post(TOKEN_URL, status=400, payload={"error": "invalid_grant"}, repeat=True)
            results = await asyncio.gather(
                *(client._v2_request("GET", "/user/profile") for _ in range(3)), return_exceptions=True
            )
            mocked.get(f"{V2}/user/profile", status=401)
            with pytest.raises(TimebutlerAuthenticationError):
                await client._v2_request("GET", "/user/profile")
            forms = _form_calls(mocked)
        assert all(isinstance(result, TimebutlerAuthenticationError) for result in results)
        assert [form["grant_type"] for form in forms] == ["password", "refresh_token"]

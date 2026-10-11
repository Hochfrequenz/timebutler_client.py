"""Shared helpers for API v2 tests."""

from aioresponses import aioresponses
from aioresponses.core import RequestCall

from timebutler_client import TimebutlerClient

V2 = "https://app.timebutler.com/api/v2"
TOKEN = "tb_test-token"


def make_client() -> TimebutlerClient:
    """Client configured with a personal token only."""
    return TimebutlerClient(personal_token=TOKEN)


def only_request(mocked: aioresponses) -> RequestCall:
    """Return the single request made against the mock; fail if there were more or none."""
    calls = [call for call_list in mocked.requests.values() for call in call_list]
    assert len(calls) == 1, f"expected exactly one request, got {len(calls)}"
    return calls[0]

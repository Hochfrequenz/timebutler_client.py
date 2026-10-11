"""
Read-only tests against the real Timebutler API v2.

Run with: TIMEBUTLER_PERSONAL_TOKEN=tb_... uv run --group tests pytest -m integration
"""

import os

import pytest

from timebutler_client import TimebutlerClient

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not os.environ.get("TIMEBUTLER_PERSONAL_TOKEN"), reason="TIMEBUTLER_PERSONAL_TOKEN not set"),
]


@pytest.fixture
def client() -> TimebutlerClient:
    return TimebutlerClient(personal_token=os.environ["TIMEBUTLER_PERSONAL_TOKEN"])


class TestReadOnly:
    """Smoke tests; never write."""

    async def test_profile(self, client: TimebutlerClient) -> None:
        assert await client.get_user_profile() is not None

    async def test_projects_and_categories(self, client: TimebutlerClient) -> None:
        await client.get_time_tracking_projects()
        await client.get_time_tracking_categories()

    async def test_my_time_entries(self, client: TimebutlerClient) -> None:
        await client.get_my_time_entries()

    async def test_time_clock_status(self, client: TimebutlerClient) -> None:
        await client.get_time_clock_status()

    async def test_absences(self, client: TimebutlerClient) -> None:
        await client.get_my_absence_requests()
        await client.get_absence_types()

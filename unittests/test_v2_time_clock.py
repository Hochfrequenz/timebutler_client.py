"""Tests for v2 time clock endpoints."""

from collections.abc import Awaitable, Callable

import pytest
from aioresponses import aioresponses

from timebutler_client import TimebutlerClient, TimebutlerConflictError
from timebutler_client.models.v2 import TimeClockStatusDto
from unittests.v2_helpers import V2, make_client, only_request

STATUS = {"status": "running", "startTimestamp": 1791536400000, "workTimeElapsedSeconds": 60}

ACTIONS: list[tuple[str, str, Callable[[TimebutlerClient], Awaitable[TimeClockStatusDto]]]] = [
    ("GET", "/time-clock/status", lambda c: c.get_time_clock_status()),
    ("POST", "/time-clock/start", lambda c: c.start_time_clock()),
    ("POST", "/time-clock/pause", lambda c: c.pause_time_clock()),
    ("POST", "/time-clock/resume", lambda c: c.resume_time_clock()),
    ("POST", "/time-clock/cancel", lambda c: c.cancel_time_clock()),
    ("POST", "/time-clock/business-trip-start", lambda c: c.start_business_trip()),
    ("POST", "/time-clock/business-trip-end", lambda c: c.end_business_trip()),
]


class TestTimeClock:
    """/time-clock/*"""

    @pytest.mark.parametrize(("method", "path", "action"), ACTIONS)
    async def test_status_actions(
        self, method: str, path: str, action: Callable[[TimebutlerClient], Awaitable[TimeClockStatusDto]]
    ) -> None:
        with aioresponses() as mocked:
            mocked.add(f"{V2}{path}", method=method, status=200, payload=STATUS)
            actual = await action(make_client())
            only_request(mocked)
        assert actual.status == "running"
        assert actual.start_timestamp == 1791536400000

    async def test_start_twice_conflict(self) -> None:
        with aioresponses() as mocked:
            mocked.post(f"{V2}/time-clock/start", status=409, body="already running")
            with pytest.raises(TimebutlerConflictError):
                await make_client().start_time_clock()

    async def test_stop_saved(self) -> None:
        with aioresponses() as mocked:
            mocked.post(
                f"{V2}/time-clock/stop", status=200, payload={"outcome": "saved", "id": "98765", "workedMinutes": 450}
            )
            actual = await make_client().stop_time_clock(project_id="5", remarks="done")
            call = only_request(mocked)
        assert actual is not None
        assert actual.outcome == "saved"
        assert actual.id == "98765"
        assert call.kwargs["json"] == {"projectId": 5, "remarks": "done"}

    async def test_stop_confirmation_then_apply(self) -> None:
        with aioresponses() as mocked:
            mocked.post(
                f"{V2}/time-clock/stop", status=200, payload={"outcome": "confirmationRequired", "breakRegulation": {}}
            )
            mocked.post(
                f"{V2}/time-clock/stop",
                status=200,
                payload={"outcome": "saved", "id": "1", "breakRegulationApplied": True},
            )
            client = make_client()
            first = await client.stop_time_clock()
            second = await client.stop_time_clock(break_regulation="apply")
            bodies = [c.kwargs["json"] for calls in mocked.requests.values() for c in calls]
        assert first is not None
        assert first.outcome == "confirmationRequired"
        assert second is not None
        assert second.break_regulation_applied is True
        assert bodies == [{}, {"breakRegulation": "apply"}]

    async def test_stop_waiting_discarded_returns_none(self) -> None:
        with aioresponses() as mocked:
            mocked.post(f"{V2}/time-clock/stop", status=204)
            assert await make_client().stop_time_clock() is None

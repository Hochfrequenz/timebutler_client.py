"""Tests for v2 time entry endpoints."""

from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from aioresponses import aioresponses

from timebutler_client import TimebutlerConflictError
from timebutler_client.models.v2 import ClockEntryResponse, DeleteResultResponse, TimeEntryDto
from unittests.v2_helpers import V2, make_client, only_request

BERLIN = ZoneInfo("Europe/Berlin")
CREATED = {"id": "98765", "workedMinutes": 450, "breakMinutes": 30}


class TestGetMyTimeEntries:
    """GET /time-entries/my"""

    async def test_no_params(self) -> None:
        payload = [{"id": "1", "date": "2026-10-09", "workedMinutes": 480, "status": "done"}]
        with aioresponses() as mocked:
            mocked.get(f"{V2}/time-entries/my", status=200, payload=payload)
            actual = await make_client().get_my_time_entries()
            call = only_request(mocked)
        assert actual == [TimeEntryDto.model_validate(payload[0])]
        assert not call.kwargs.get("params")

    async def test_all_filters(self) -> None:
        url = f"{V2}/time-entries/my?year=2026&month=10&projectId=5&categoryId=3&status=pending"
        with aioresponses() as mocked:
            mocked.get(url, status=200, payload=[])
            await make_client().get_my_time_entries(
                year=2026, month=10, project_id="5", category_id=3, status="pending"
            )
            call = only_request(mocked)
        assert call.kwargs["params"] == {
            "year": "2026",
            "month": "10",
            "projectId": "5",
            "categoryId": "3",
            "status": "pending",
        }

    @pytest.mark.parametrize(("year", "month"), [(2026, 0), (2026, 13), (1969, None), (2101, None), (None, 5)])
    async def test_invalid_year_month(self, year: int | None, month: int | None) -> None:
        with pytest.raises(ValueError):
            await make_client().get_my_time_entries(year=year, month=month)


class TestCreateTimeEntry:
    """POST /time-tracking/clock-entry"""

    async def test_body(self) -> None:
        start = datetime(2026, 10, 9, 9, 0, tzinfo=UTC)
        with aioresponses() as mocked:
            mocked.post(f"{V2}/time-tracking/clock-entry", status=200, payload=CREATED)
            actual = await make_client().create_time_entry(
                start,
                start + timedelta(hours=8),
                pause=timedelta(minutes=30),
                project_id="5",
                category_id=3,
                remarks="Review",
            )
            call = only_request(mocked)
        assert actual == ClockEntryResponse.model_validate(CREATED)
        assert call.kwargs["json"] == {
            "startTimestamp": 1791536400000,
            "endTimestamp": 1791565200000,
            "pauseSeconds": 1800,
            "projectId": 5,
            "categoryId": 3,
            "remarks": "Review",
        }

    async def test_minimal_body_omits_optionals(self) -> None:
        start = datetime(2026, 10, 9, 9, 0, tzinfo=UTC)
        with aioresponses() as mocked:
            mocked.post(f"{V2}/time-tracking/clock-entry", status=200, payload=CREATED)
            await make_client().create_time_entry(start, start + timedelta(hours=1))
            call = only_request(mocked)
        assert call.kwargs["json"] == {
            "startTimestamp": 1791536400000,
            "endTimestamp": 1791540000000,
            "pauseSeconds": 0,
        }

    async def test_berlin_dst_day(self) -> None:
        # 2026-10-25: clocks go back 03:00 CEST -> 02:00 CET; 01:00 CEST..05:00 CET is 5 real hours
        start = datetime(2026, 10, 25, 1, 0, tzinfo=BERLIN)
        end = datetime(2026, 10, 25, 5, 0, tzinfo=BERLIN)
        with aioresponses() as mocked:
            mocked.post(f"{V2}/time-tracking/clock-entry", status=200, payload=CREATED)
            await make_client().create_time_entry(start, end)
            body = only_request(mocked).kwargs["json"]
        assert body["endTimestamp"] - body["startTimestamp"] == 5 * 3600 * 1000
        assert body["startTimestamp"] == int(start.timestamp()) * 1000

    async def test_naive_datetime_rejected(self) -> None:
        with pytest.raises(ValueError, match="timezone"):
            await make_client().create_time_entry(datetime(2026, 10, 9, 9), datetime(2026, 10, 9, 17))

    async def test_end_not_after_start_rejected(self) -> None:
        start = datetime(2026, 10, 9, 9, 0, tzinfo=BERLIN)
        with pytest.raises(ValueError, match="after"):
            await make_client().create_time_entry(start, start)

    async def test_midnight_end_rejected(self) -> None:
        with pytest.raises(ValueError, match="same calendar day"):
            await make_client().create_time_entry(
                datetime(2026, 10, 9, 22, 0, tzinfo=BERLIN), datetime(2026, 10, 10, 0, 0, tzinfo=BERLIN)
            )

    async def test_negative_pause_rejected(self) -> None:
        start = datetime(2026, 10, 9, 9, 0, tzinfo=BERLIN)
        with pytest.raises(ValueError, match="pause"):
            await make_client().create_time_entry(start, start + timedelta(hours=1), pause=timedelta(minutes=-1))


class TestDeleteAndRequests:
    """delete, pending count, time entry requests, summaries"""

    async def test_delete_with_str_id_from_model(self) -> None:
        created = ClockEntryResponse.model_validate(CREATED)
        assert created.id is not None
        with aioresponses() as mocked:
            mocked.delete(f"{V2}/time-entries/98765", status=200, payload={"id": "98765", "result": "deleted"})
            actual = await make_client().delete_time_entry(created.id)
        assert actual == DeleteResultResponse.model_validate({"id": "98765", "result": "deleted"})

    async def test_delete_month_closed(self) -> None:
        with aioresponses() as mocked:
            mocked.delete(f"{V2}/time-entries/1", status=409, body="month closed")
            with pytest.raises(TimebutlerConflictError):
                await make_client().delete_time_entry(1)

    async def test_pending_count(self) -> None:
        with aioresponses() as mocked:
            mocked.get(f"{V2}/time-entries/pending-count", status=200, payload={})
            await make_client().get_time_entries_pending_count()
            assert only_request(mocked)

    async def test_time_entry_requests(self) -> None:
        with aioresponses() as mocked:
            mocked.get(f"{V2}/time-entry-requests", status=200, payload=[{"id": "7"}])
            mocked.post(f"{V2}/time-entry-requests/7/approve", status=200, payload={"id": "7"})
            mocked.post(f"{V2}/time-entry-requests/7/reject", status=200, payload={"id": "7"})
            client = make_client()
            requests = await client.get_time_entry_requests()
            assert requests[0].id is not None
            await client.approve_time_entry_request(requests[0].id)
            await client.reject_time_entry_request("7", reason="falsches Projekt")
            reject_calls = [
                c for (_m, u), calls in mocked.requests.items() if str(u).endswith("/reject") for c in calls
            ]
        assert requests[0].id == "7"
        assert reject_calls[0].kwargs["json"] == {"reason": "falsches Projekt"}

    async def test_reject_without_reason_sends_empty_object(self) -> None:
        with aioresponses() as mocked:
            mocked.post(f"{V2}/time-entry-requests/7/reject", status=200, payload={"id": "7"})
            await make_client().reject_time_entry_request(7)
            assert only_request(mocked).kwargs["json"] == {}

    async def test_summaries(self) -> None:
        summary_payload = {
            "commitmentMinutes": 480,
            "workedMinutes": 240,
            "remainingMinutes": 240,
            "percentDone": 50,
            "breakMinutes": 0,
        }
        with aioresponses() as mocked:
            mocked.get(f"{V2}/time-tracking/work-summary", status=200, payload=summary_payload)
            mocked.get(f"{V2}/time-tracking/time-off-summary", status=200, payload={})
            client = make_client()
            summary = await client.get_work_summary()
            await client.get_time_off_summary()
        assert summary.percent_done == 50

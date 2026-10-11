"""Tests for v2 absence endpoints."""

from datetime import date
from decimal import Decimal

import pytest
from aioresponses import aioresponses

from timebutler_client.models.v2 import AbsenceRequestDto, DeleteResultResponse
from unittests.v2_helpers import V2, make_client, only_request

REQUEST = {"id": "12345", "type": "URL", "startDate": "2026-12-21", "endDate": "2026-12-23", "status": "pending"}


class TestAbsenceRequests:
    """/absence-requests*"""

    @pytest.mark.parametrize(
        ("path", "method_name"), [("my", "get_my_absence_requests"), ("team", "get_team_absence_requests")]
    )
    async def test_lists(self, path: str, method_name: str) -> None:
        with aioresponses() as mocked:
            mocked.get(f"{V2}/absence-requests/{path}", status=200, payload=[REQUEST])
            actual = await getattr(make_client(), method_name)()
        assert actual == [AbsenceRequestDto.model_validate(REQUEST)]

    async def test_create_full_body(self) -> None:
        with aioresponses() as mocked:
            mocked.post(f"{V2}/absence-requests", status=200, payload=REQUEST)
            await make_client().create_absence_request(
                "UEB",
                date(2026, 12, 21),
                date(2026, 12, 21),
                half_day="morning",
                comments="Arzt",
                hours=Decimal("1.5"),
                substitute_employee_id=42,
            )
            body = only_request(mocked).kwargs["json"]
        assert body == {
            "absenceTypeId": "UEB",
            "startDate": "2026-12-21",
            "endDate": "2026-12-21",
            "halfDay": "morning",
            "comments": "Arzt",
            "hours": "1.5",
            "substituteEmployeeId": "42",
        }

    async def test_create_minimal_body(self) -> None:
        with aioresponses() as mocked:
            mocked.post(f"{V2}/absence-requests", status=200, payload=REQUEST)
            await make_client().create_absence_request("URL", date(2026, 12, 21), date(2026, 12, 23))
            body = only_request(mocked).kwargs["json"]
        assert body == {"absenceTypeId": "URL", "startDate": "2026-12-21", "endDate": "2026-12-23"}

    async def test_create_end_before_start_rejected(self) -> None:
        with pytest.raises(ValueError, match="end_date"):
            await make_client().create_absence_request("URL", date(2026, 12, 23), date(2026, 12, 21))

    async def test_create_invalid_hours_rejected(self) -> None:
        with pytest.raises(ValueError, match="hours"):
            await make_client().create_absence_request("UEB", date(2026, 12, 21), date(2026, 12, 21), hours="1,5")

    async def test_update_sends_only_given_fields(self) -> None:
        with aioresponses() as mocked:
            mocked.put(f"{V2}/absence-requests/12345", status=200, payload=REQUEST)
            await make_client().update_absence_request("12345", end_date=date(2026, 12, 24), half_day="")
            body = only_request(mocked).kwargs["json"]
        assert body == {"endDate": "2026-12-24", "halfDay": ""}

    async def test_delete_with_reason(self) -> None:
        with aioresponses() as mocked:
            mocked.delete(
                f"{V2}/absence-requests/12345", status=200, payload={"id": "12345", "result": "cancellation_requested"}
            )
            actual = await make_client().delete_absence_request(12345, reason="Plan geändert")
            body = only_request(mocked).kwargs["json"]
        assert actual == DeleteResultResponse.model_validate({"id": "12345", "result": "cancellation_requested"})
        assert body == {"reason": "Plan geändert"}

    async def test_approve_and_reject_with_model_id(self) -> None:
        request = AbsenceRequestDto.model_validate(REQUEST)
        assert request.id is not None
        with aioresponses() as mocked:
            mocked.post(f"{V2}/absence-requests/12345/approve", status=200, payload=REQUEST)
            mocked.post(f"{V2}/absence-requests/12345/reject", status=200, payload=REQUEST)
            client = make_client()
            await client.approve_absence_request(request.id)
            await client.reject_absence_request("12345", reason="Urlaubssperre")
            bodies = [c.kwargs.get("json") for calls in mocked.requests.values() for c in calls]
        assert bodies == [None, {"reason": "Urlaubssperre"}]

    async def test_pending_count_and_types(self) -> None:
        with aioresponses() as mocked:
            mocked.get(f"{V2}/absence-requests/pending-count", status=200, payload={})
            mocked.get(f"{V2}/absence-types", status=200, payload=[{}])
            client = make_client()
            await client.get_absence_requests_pending_count()
            assert len(await client.get_absence_types()) == 1


class TestCancellationRequests:
    """/cancellation-requests*"""

    async def test_all(self) -> None:
        with aioresponses() as mocked:
            mocked.get(f"{V2}/cancellation-requests", status=200, payload=[{}])
            mocked.get(f"{V2}/cancellation-requests/pending-count", status=200, payload={})
            mocked.post(f"{V2}/cancellation-requests/9/approve", status=200, payload={})
            mocked.post(f"{V2}/cancellation-requests/9/reject", status=200, payload={})
            client = make_client()
            assert len(await client.get_cancellation_requests()) == 1
            await client.get_cancellation_requests_pending_count()
            await client.approve_cancellation_request("9")
            await client.reject_cancellation_request(9)
            assert sum(len(calls) for calls in mocked.requests.values()) == 4

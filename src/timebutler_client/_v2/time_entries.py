"""Timebutler API v2: time entries, clock entries, time entry requests, summaries."""

from datetime import datetime, timedelta
from typing import Any

from timebutler_client._v2._http import V2Mixin, parse_model, parse_model_list, path_id
from timebutler_client.models.v2 import (
    ClockEntryResponse,
    DeleteResultResponse,
    TimeEntryDto,
    TimeEntryPendingCountResponse,
    TimeEntryRequestDto,
    TimeEntryStatus,
    TimeOffSummaryResponse,
    WorkSummaryResponse,
)


def _unix_ms(value: datetime) -> int:
    return int(value.timestamp()) * 1000 + value.microsecond // 1000


def _int_id(value: int | str) -> int:
    return int(path_id(value))


class TimeEntriesMixin(V2Mixin):
    """Time entries of the token owner and approval of others' entries."""

    async def get_my_time_entries(
        self,
        year: int | None = None,
        month: int | None = None,
        project_id: int | str | None = None,
        category_id: int | str | None = None,
        status: TimeEntryStatus | None = None,
    ) -> list[TimeEntryDto]:
        """
        Fetch the token owner's time entries, newest first.

        Without arguments: current month. `year` alone: whole year. `month` requires `year`.
        """
        if year is not None and not 1970 <= year <= 2100:
            raise ValueError(f"Year must be between 1970 and 2100, got {year}")
        if month is not None:
            if year is None:
                raise ValueError("month requires year")
            if not 1 <= month <= 12:
                raise ValueError(f"Month must be between 1 and 12, got {month}")
        params: dict[str, str | int] = {}
        if year is not None:
            params["year"] = year
        if month is not None:
            params["month"] = month
        if project_id is not None:
            params["projectId"] = path_id(project_id)
        if category_id is not None:
            params["categoryId"] = path_id(category_id)
        if status is not None:
            params["status"] = status
        data = await self._v2_request("GET", "/time-entries/my", params=params or None)
        return parse_model_list(TimeEntryDto, data)

    async def create_time_entry(
        self,
        start: datetime,
        end: datetime,
        pause: timedelta = timedelta(0),
        project_id: int | str | None = None,
        category_id: int | str | None = None,
        remarks: str | None = None,
    ) -> ClockEntryResponse:
        """
        Create a completed time entry for the token owner.

        `start`/`end` must be timezone-aware and on the same calendar day (in `start`'s timezone).
        Depending on company settings the entry is `pending` (needs approval) or `done`.
        There is no update endpoint in v2: to correct an entry, delete it and create a new one.
        """
        if start.tzinfo is None or end.tzinfo is None:
            raise ValueError("start and end must be timezone-aware datetimes")
        if end <= start:
            raise ValueError("end must be after start")
        if end.astimezone(start.tzinfo).date() != start.date():
            raise ValueError("start and end must be on the same calendar day")
        if pause < timedelta(0):
            raise ValueError("pause must not be negative")
        body: dict[str, Any] = {
            "startTimestamp": _unix_ms(start),
            "endTimestamp": _unix_ms(end),
            "pauseSeconds": int(pause.total_seconds()),
        }
        if project_id is not None:
            body["projectId"] = _int_id(project_id)
        if category_id is not None:
            body["categoryId"] = _int_id(category_id)
        if remarks is not None:
            body["remarks"] = remarks
        return parse_model(ClockEntryResponse, await self._v2_request("POST", "/time-tracking/clock-entry", json=body))

    async def delete_time_entry(self, entry_id: int | str) -> DeleteResultResponse:
        """
        Delete a time entry, or request its deletion (see `result`).

        Raises TimebutlerConflictError if the month is already closed.
        """
        data = await self._v2_request("DELETE", f"/time-entries/{path_id(entry_id)}")
        return parse_model(DeleteResultResponse, data)

    async def get_time_entries_pending_count(self) -> TimeEntryPendingCountResponse:
        """Number of time entries awaiting the token owner's approval."""
        return parse_model(TimeEntryPendingCountResponse, await self._v2_request("GET", "/time-entries/pending-count"))

    async def get_time_entry_requests(self) -> list[TimeEntryRequestDto]:
        """Pending time entry requests the token owner may approve."""
        return parse_model_list(TimeEntryRequestDto, await self._v2_request("GET", "/time-entry-requests"))

    async def approve_time_entry_request(self, request_id: int | str) -> TimeEntryRequestDto:
        """Approve a pending time entry request."""
        data = await self._v2_request("POST", f"/time-entry-requests/{path_id(request_id)}/approve")
        return parse_model(TimeEntryRequestDto, data)

    async def reject_time_entry_request(self, request_id: int | str, reason: str | None = None) -> TimeEntryRequestDto:
        """Reject a pending time entry request, optionally with a reason shown to the employee."""
        body = {"reason": reason} if reason is not None else {}
        data = await self._v2_request("POST", f"/time-entry-requests/{path_id(request_id)}/reject", json=body)
        return parse_model(TimeEntryRequestDto, data)

    async def get_work_summary(self) -> WorkSummaryResponse:
        """Today's work summary of the token owner (commitment, worked, remaining minutes)."""
        return parse_model(WorkSummaryResponse, await self._v2_request("GET", "/time-tracking/work-summary"))

    async def get_time_off_summary(self) -> TimeOffSummaryResponse:
        """Time-off summary of the token owner."""
        return parse_model(TimeOffSummaryResponse, await self._v2_request("GET", "/time-tracking/time-off-summary"))

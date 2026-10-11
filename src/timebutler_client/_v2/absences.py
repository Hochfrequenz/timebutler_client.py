"""Timebutler API v2: absence requests, absence types, cancellation requests."""

from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any, Literal

from timebutler_client._v2._http import V2Mixin, parse_model, parse_model_list, path_id
from timebutler_client.models.v2 import (
    AbsencePendingCountResponse,
    AbsenceRequestDto,
    AbsenceTypeDto,
    CancellationPendingCountResponse,
    CancellationRequestDto,
    DeleteResultResponse,
)


def _hours(value: Decimal | str) -> str:
    """The API expects hours as a string with '.' as decimal separator."""
    text = str(value).strip()
    try:
        is_valid = Decimal(text).is_finite()
    except InvalidOperation:
        is_valid = False
    if not is_valid:
        raise ValueError(f"hours must be a decimal number with '.' as separator, got {value!r}")
    return text


class AbsencesMixin(V2Mixin):
    """Absence requests of the token owner and approval of the team's requests."""

    async def get_my_absence_requests(self) -> list[AbsenceRequestDto]:
        """The token owner's own absence requests (all states)."""
        return parse_model_list(AbsenceRequestDto, await self._v2_request("GET", "/absence-requests/my"))

    async def get_team_absence_requests(self) -> list[AbsenceRequestDto]:
        """Absence requests of employees the token owner manages (admins: everyone), all states."""
        return parse_model_list(AbsenceRequestDto, await self._v2_request("GET", "/absence-requests/team"))

    async def get_absence_requests_pending_count(self) -> AbsencePendingCountResponse:
        """Pending request counts for the token owner's team."""
        data = await self._v2_request("GET", "/absence-requests/pending-count")
        return parse_model(AbsencePendingCountResponse, data)

    async def create_absence_request(
        self,
        absence_type_id: str,
        start_date: date,
        end_date: date,
        half_day: Literal["morning", "afternoon"] | None = None,
        comments: str | None = None,
        hours: Decimal | str | None = None,
        substitute_employee_id: int | str | None = None,
    ) -> AbsenceRequestDto:
        """
        Create an absence request for the token owner.

        `absence_type_id` is the 3-letter code from `get_absence_types()` (e.g. "URL").
        `hours` is required for overtime types ("UEB", "AUA"). For `half_day`, start and end must be equal.
        """
        if end_date < start_date:
            raise ValueError("end_date must not be before start_date")
        body: dict[str, Any] = {
            "absenceTypeId": absence_type_id,
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
        }
        if half_day is not None:
            body["halfDay"] = half_day
        if comments is not None:
            body["comments"] = comments
        if hours is not None:
            body["hours"] = _hours(hours)
        if substitute_employee_id is not None:
            body["substituteEmployeeId"] = path_id(substitute_employee_id)
        return parse_model(AbsenceRequestDto, await self._v2_request("POST", "/absence-requests", json=body))

    async def update_absence_request(
        self,
        request_id: int | str,
        *,
        absence_type_id: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        half_day: Literal["morning", "afternoon", ""] | None = None,
        comments: str | None = None,
        hours: Decimal | str | None = None,
        substitute_employee_id: int | str | None = None,
    ) -> AbsenceRequestDto:
        """
        Update an absence request. Only arguments that are not None are sent; the rest stay unchanged.

        `half_day=""` switches back to a full day, `comments=""` clears the comment,
        `substitute_employee_id="0"` removes the substitute.
        """
        body: dict[str, Any] = {}
        if absence_type_id is not None:
            body["absenceTypeId"] = absence_type_id
        if start_date is not None:
            body["startDate"] = start_date.isoformat()
        if end_date is not None:
            body["endDate"] = end_date.isoformat()
        if half_day is not None:
            body["halfDay"] = half_day
        if comments is not None:
            body["comments"] = comments
        if hours is not None:
            body["hours"] = _hours(hours)
        if substitute_employee_id is not None:
            body["substituteEmployeeId"] = path_id(substitute_employee_id)
        data = await self._v2_request("PUT", f"/absence-requests/{path_id(request_id)}", json=body)
        return parse_model(AbsenceRequestDto, data)

    async def delete_absence_request(self, request_id: int | str, reason: str | None = None) -> DeleteResultResponse:
        """Delete an absence request, or send a cancellation request if already approved (see `result`)."""
        body = {"reason": reason} if reason is not None else {}
        data = await self._v2_request("DELETE", f"/absence-requests/{path_id(request_id)}", json=body)
        return parse_model(DeleteResultResponse, data)

    async def approve_absence_request(self, request_id: int | str) -> AbsenceRequestDto:
        """Approve a pending absence request."""
        data = await self._v2_request("POST", f"/absence-requests/{path_id(request_id)}/approve")
        return parse_model(AbsenceRequestDto, data)

    async def reject_absence_request(self, request_id: int | str, reason: str | None = None) -> AbsenceRequestDto:
        """Reject a pending absence request, optionally with a reason shown to the employee."""
        body = {"reason": reason} if reason is not None else {}
        data = await self._v2_request("POST", f"/absence-requests/{path_id(request_id)}/reject", json=body)
        return parse_model(AbsenceRequestDto, data)

    async def get_absence_types(self) -> list[AbsenceTypeDto]:
        """Absence types (codes for `create_absence_request`)."""
        return parse_model_list(AbsenceTypeDto, await self._v2_request("GET", "/absence-types"))

    async def get_cancellation_requests(self) -> list[CancellationRequestDto]:
        """Open cancellation requests the token owner may decide on."""
        return parse_model_list(CancellationRequestDto, await self._v2_request("GET", "/cancellation-requests"))

    async def get_cancellation_requests_pending_count(self) -> CancellationPendingCountResponse:
        """Number of open cancellation requests."""
        data = await self._v2_request("GET", "/cancellation-requests/pending-count")
        return parse_model(CancellationPendingCountResponse, data)

    async def approve_cancellation_request(self, request_id: int | str) -> CancellationRequestDto:
        """Approve a cancellation request."""
        data = await self._v2_request("POST", f"/cancellation-requests/{path_id(request_id)}/approve")
        return parse_model(CancellationRequestDto, data)

    async def reject_cancellation_request(self, request_id: int | str) -> CancellationRequestDto:
        """Reject a cancellation request."""
        data = await self._v2_request("POST", f"/cancellation-requests/{path_id(request_id)}/reject")
        return parse_model(CancellationRequestDto, data)

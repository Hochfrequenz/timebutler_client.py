"""Timebutler API v2: time clock (stamp in/out) of the token owner."""

from typing import Any, Literal

from timebutler_client._v2._http import V2Mixin, parse_model, path_id
from timebutler_client.models.v2 import TimeClockStatusDto, TimeClockStopResponse


class TimeClockMixin(V2Mixin):
    """Virtual time clock. Conflicting actions (e.g. start while running) raise TimebutlerConflictError."""

    async def _clock(self, method: str, action: str) -> TimeClockStatusDto:
        return parse_model(TimeClockStatusDto, await self._v2_request(method, f"/time-clock/{action}"))

    async def get_time_clock_status(self) -> TimeClockStatusDto:
        """Current clock state (`idle`, `running`, `paused`, `waiting`) and elapsed times."""
        return await self._clock("GET", "status")

    async def start_time_clock(self) -> TimeClockStatusDto:
        """Start the clock. May enter `waiting` if a minimum start interval is configured."""
        return await self._clock("POST", "start")

    async def pause_time_clock(self) -> TimeClockStatusDto:
        """Pause the running clock."""
        return await self._clock("POST", "pause")

    async def resume_time_clock(self) -> TimeClockStatusDto:
        """Resume the paused clock."""
        return await self._clock("POST", "resume")

    async def cancel_time_clock(self) -> TimeClockStatusDto:
        """Discard the current session without saving."""
        return await self._clock("POST", "cancel")

    async def start_business_trip(self) -> TimeClockStatusDto:
        """Start a business trip within the current session."""
        return await self._clock("POST", "business-trip-start")

    async def end_business_trip(self) -> TimeClockStatusDto:
        """End the business trip within the current session."""
        return await self._clock("POST", "business-trip-end")

    async def stop_time_clock(
        self,
        project_id: int | str | None = None,
        category_id: int | str | None = None,
        remarks: str | None = None,
        break_regulation: Literal["apply", "ignore"] | None = None,
    ) -> TimeClockStopResponse | None:
        """
        Stop the clock and save the entry.

        If the session violates the break regulation and no decision was given, nothing is saved and
        `outcome == "confirmationRequired"`; call again with `break_regulation="apply"` (or `"ignore"`
        if `break_regulation.obligatory` is false). Returns None if the clock was `waiting` and was discarded.
        """
        body: dict[str, Any] = {}
        if project_id is not None:
            body["projectId"] = int(path_id(project_id))
        if category_id is not None:
            body["categoryId"] = int(path_id(category_id))
        if remarks is not None:
            body["remarks"] = remarks
        if break_regulation is not None:
            body["breakRegulation"] = break_regulation
        data = await self._v2_request("POST", "/time-clock/stop", json=body)
        return None if data is None else parse_model(TimeClockStopResponse, data)

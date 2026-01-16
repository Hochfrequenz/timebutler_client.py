"""Worktime entry model for Timebutler API."""

from datetime import datetime, time, timedelta
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, computed_field

from timebutler_client.models.absence import EmployeeNumber, EuropeanDate

__all__ = ["WorktimeEntry", "HHMMTime"]


def _parse_hhmm_time(value: str | time) -> time:
    """Parse HH:MM format strictly."""
    if isinstance(value, time):
        return value
    try:
        return datetime.strptime(value, "%H:%M").time()
    except ValueError as e:
        raise ValueError(f"Time must be in HH:MM format, got: {value!r}") from e


#: Annotated type for times in HH:MM format
HHMMTime = Annotated[time, BeforeValidator(_parse_hhmm_time)]


class WorktimeEntry(BaseModel):
    """
    Represents a worktime entry from Timebutler.

    Each entry records time spent by an employee, optionally linked
    to a project and/or service. Times are in 24-hour format.
    """

    model_config = ConfigDict(frozen=True)

    id: int = Field(description="Unique worktime entry identifier")
    user_id: int = Field(description="User ID of the employee")
    employee_number: EmployeeNumber = Field(description="Employee number with leading zeros, e.g. '00123'")
    date: EuropeanDate = Field(description="Date of the worktime entry")
    start_time: HHMMTime = Field(description="Start time in HH:MM format")
    end_time: HHMMTime = Field(description="End time in HH:MM format")
    working_time_seconds: int = Field(description="Working time in seconds (excludes pause)")
    pause_seconds: int = Field(default=0, description="Pause duration in seconds")
    state: str = Field(description="Entry state: Done, Requested, Accepted, Rejected, or In process")
    project_id: int = Field(default=0, description="Project ID, 0 if no project assigned")
    service_id: int = Field(default=0, description="Service ID, 0 if no service assigned")
    comments: str | None = Field(default=None, description="Optional comments")
    auto_stopped: bool = Field(default=False, description="Whether the entry was auto-stopped")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def duration(self) -> timedelta:
        """Working time as timedelta (excludes pause)."""
        return timedelta(seconds=self.working_time_seconds)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def pause(self) -> timedelta:
        """Pause duration as timedelta."""
        return timedelta(seconds=self.pause_seconds)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def has_project(self) -> bool:
        """True if a project is assigned."""
        return self.project_id != 0

    @computed_field  # type: ignore[prop-decorator]
    @property
    def has_service(self) -> bool:
        """True if a service is assigned."""
        return self.service_id != 0

    @computed_field  # type: ignore[prop-decorator]
    @property
    def employee_number_numeric(self) -> int:
        """Employee number without leading zeros."""
        return int(self.employee_number)

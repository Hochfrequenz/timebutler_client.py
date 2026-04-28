"""Workday schedule model for Timebutler API."""

from datetime import date, timedelta
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, computed_field

from timebutler_client.models.absence import EmployeeNumber, _parse_european_date
from timebutler_client.models.invalid_employee import InvalidEmployee

__all__ = ["WorkdaySchedule", "WorkdaysResult", "UNLIMITED_DATE"]

#: Sentinel for when Timebutler returns "unlimited" as a workday schedule start date.
#: "unlimited" means the schedule has been in effect since the very beginning — hence a
#: date in the distant past, not the future.
UNLIMITED_DATE = date(1900, 1, 1)


def _parse_workday_start_date(value: str | date) -> date:
    """Parse a workday schedule start date, mapping 'unlimited' to UNLIMITED_DATE."""
    if isinstance(value, str) and value.strip().lower() == "unlimited":
        return UNLIMITED_DATE
    return _parse_european_date(value)


#: Date type for workday schedule start dates; accepts 'unlimited' in addition to dd/mm/yyyy.
WorkdayStartDate = Annotated[date, BeforeValidator(_parse_workday_start_date)]


class WorkdaySchedule(BaseModel):
    """
    Represents a workday schedule entry for a user from Timebutler.

    A user may have multiple entries (e.g. when their schedule changes over time).
    Each entry is valid from valid_from onwards, until the next entry's valid_from.
    Working times are stored in minutes per weekday.
    """

    model_config = ConfigDict(frozen=True)

    # Critical fields - strictly validated
    user_id: int
    valid_from: WorkdayStartDate = Field(description="Date from which this schedule is valid (inclusive)")
    employee_number: EmployeeNumber = Field(description="Employee number with leading zeros, e.g. '00123'")

    # Good to have - relaxed validation with defaults
    monday_minutes: int = 0
    tuesday_minutes: int = 0
    wednesday_minutes: int = 0
    thursday_minutes: int = 0
    friday_minutes: int = 0
    saturday_minutes: int = 0
    sunday_minutes: int = 0
    holiday_set_id: int = 0

    @computed_field  # type: ignore[prop-decorator]
    @property
    def monday(self) -> timedelta:
        """Working time on Monday as timedelta."""
        return timedelta(minutes=self.monday_minutes)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def tuesday(self) -> timedelta:
        """Working time on Tuesday as timedelta."""
        return timedelta(minutes=self.tuesday_minutes)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def wednesday(self) -> timedelta:
        """Working time on Wednesday as timedelta."""
        return timedelta(minutes=self.wednesday_minutes)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def thursday(self) -> timedelta:
        """Working time on Thursday as timedelta."""
        return timedelta(minutes=self.thursday_minutes)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def friday(self) -> timedelta:
        """Working time on Friday as timedelta."""
        return timedelta(minutes=self.friday_minutes)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def saturday(self) -> timedelta:
        """Working time on Saturday as timedelta."""
        return timedelta(minutes=self.saturday_minutes)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def sunday(self) -> timedelta:
        """Working time on Sunday as timedelta."""
        return timedelta(minutes=self.sunday_minutes)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def weekly_minutes(self) -> int:
        """Total working time per week in minutes."""
        return (
            self.monday_minutes
            + self.tuesday_minutes
            + self.wednesday_minutes
            + self.thursday_minutes
            + self.friday_minutes
            + self.saturday_minutes
            + self.sunday_minutes
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def weekly_duration(self) -> timedelta:
        """Total working time per week as timedelta."""
        return timedelta(minutes=self.weekly_minutes)


class WorkdaysResult(BaseModel):
    """Return value of TimebutlerClient.get_workdays()."""

    model_config = ConfigDict(frozen=True)

    schedules: list[WorkdaySchedule]
    invalid_employees: list[InvalidEmployee]

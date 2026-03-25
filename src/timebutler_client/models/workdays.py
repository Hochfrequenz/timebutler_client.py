"""Workday schedule model for Timebutler API."""

from datetime import timedelta

from pydantic import BaseModel, ConfigDict, Field, computed_field

from timebutler_client.models.absence import EuropeanDate

__all__ = ["WorkdaySchedule"]


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
    valid_from: EuropeanDate = Field(description="Date from which this schedule is valid (inclusive)")

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

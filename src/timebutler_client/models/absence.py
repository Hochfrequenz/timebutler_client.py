"""Absence model for Timebutler API."""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, computed_field

__all__ = ["Absence", "EuropeanDate", "EmployeeNumber"]

_EMPLOYEE_NUMBER_PATTERN = r"^\d+$"

#: Annotated type for employee numbers (digits only, with leading zeros preserved)
EmployeeNumber = Annotated[str, Field(pattern=_EMPLOYEE_NUMBER_PATTERN)]


def _parse_european_date(value: str | date) -> date:
    """Parse dd/mm/yyyy format strictly. No lenient parsing."""
    if isinstance(value, date):
        return value
    try:
        return datetime.strptime(value, "%d/%m/%Y").date()
    except ValueError as e:
        raise ValueError(f"Date must be in dd/mm/yyyy format, got: {value!r}") from e


#: Annotated type for dates in European dd/mm/yyyy format
EuropeanDate = Annotated[date, BeforeValidator(_parse_european_date)]


class Absence(BaseModel):
    """
    Represents an absence entry from Timebutler.

    Date range is inclusive: an absence from 15/05/2026 to 15/05/2026
    represents a single day off (that day is included).
    """

    model_config = ConfigDict(frozen=True)

    # Critical fields - strictly validated
    id: int
    from_date: EuropeanDate = Field(description="Start date (inclusive)")
    to_date: EuropeanDate = Field(description="End date (inclusive)")
    # we chose the inclusive end not because it's a good choice, but because the API uses it
    employee_number: EmployeeNumber = Field(description="Employee number with leading zeros, e.g. '00123'")

    # Good to have - relaxed validation with defaults
    user_id: int = 0
    half_day: bool = False
    morning: bool = False
    absence_type: str = ""
    extra_vacation: bool = False
    state: str = ""
    substitute_state: str = ""
    workdays: Decimal = Decimal("0")
    hours: Decimal = Decimal("0")
    medical_certificate: str | None = None
    comments: str | None = None
    substitute_user_id: int = 0

    @computed_field  # type: ignore[prop-decorator]
    @property
    def to_date_exclusive(self) -> date:
        """End date (exclusive). The day after to_date, useful for date range calculations."""
        return self.to_date + timedelta(days=1)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def employee_number_numeric(self) -> int:
        """Employee number as integer, without leading zeros."""
        return int(self.employee_number)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def has_substitute(self) -> bool:
        """True if a substitute is assigned."""
        return self.substitute_user_id != 0

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_morning_half_day(self) -> bool:
        """True if this is a morning half-day."""
        return self.half_day and self.morning

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_afternoon_half_day(self) -> bool:
        """True if this is an afternoon half-day."""
        return self.half_day and not self.morning

    @computed_field  # type: ignore[prop-decorator]
    @property
    def has_comments(self) -> bool:
        """True if comments are present."""
        return bool(self.comments and self.comments.strip())

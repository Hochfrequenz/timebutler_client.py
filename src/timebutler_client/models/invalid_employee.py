"""Model for employee records that could not be parsed due to invalid data."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class InvalidEmployee(BaseModel):
    """
    An employee record from Timebutler whose employee_number could not be parsed.

    Returned alongside valid users so callers can surface the problem without
    crashing the entire sync.
    """

    model_config = ConfigDict(frozen=True)

    user_id: int | None
    first_name: str
    last_name: str
    raw_employee_number: str

    @property
    def display_name(self) -> str:
        """Full name as 'First Last'."""
        return f"{self.first_name} {self.last_name}".strip()

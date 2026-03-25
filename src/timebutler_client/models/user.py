"""User model for Timebutler API."""

from datetime import date, datetime
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, computed_field

from timebutler_client.models.absence import EmployeeNumber

__all__ = ["User"]


def _parse_optional_european_date(value: str | date | None) -> date | None:
    """Parse dd/mm/yyyy format, returning None for empty/missing values."""
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    if isinstance(value, date):
        return value
    try:
        return datetime.strptime(value, "%d/%m/%Y").date()
    except ValueError as e:
        raise ValueError(f"Date must be in dd/mm/yyyy format, got: {value!r}") from e


#: Annotated type for optional dates in European dd/mm/yyyy format (empty string → None)
OptionalEuropeanDate = Annotated[date | None, BeforeValidator(_parse_optional_european_date)]


def _parse_manager_user_ids(value: str | list) -> list[int]:
    """Parse a comma-separated string of user IDs into a list of ints."""
    if isinstance(value, list):
        return value
    if not value or not value.strip():
        return []
    return [int(uid.strip()) for uid in value.split(",") if uid.strip()]


#: Annotated type for a comma-separated list of user IDs
ManagerUserIds = Annotated[list[int], BeforeValidator(_parse_manager_user_ids)]


class User(BaseModel):
    """
    Represents a user from Timebutler.

    User type can be one of: Employee, Manager, Admin.
    """

    model_config = ConfigDict(frozen=True)

    # Critical fields - strictly validated
    user_id: int
    last_name: str
    first_name: str
    employee_number: EmployeeNumber = Field(description="Employee number with leading zeros, e.g. '00123'")

    # Good to have - relaxed validation with defaults
    email: str = ""
    phone: str = ""
    mobile_phone: str = ""
    cost_center: str = ""
    branch_office: str = ""
    department: str = ""
    user_type: str = ""
    language: str = ""
    manager_user_ids: ManagerUserIds = []
    account_locked: bool = False
    additional_information: str = ""
    date_of_entry: OptionalEuropeanDate = None
    date_of_separation: OptionalEuropeanDate = None
    date_of_birth: OptionalEuropeanDate = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def full_name(self) -> str:
        """Full name as 'First Last'."""
        return f"{self.first_name} {self.last_name}"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def employee_number_numeric(self) -> int:
        """Employee number as integer, without leading zeros."""
        return int(self.employee_number)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_active(self) -> bool:
        """True if the account is not locked."""
        return not self.account_locked

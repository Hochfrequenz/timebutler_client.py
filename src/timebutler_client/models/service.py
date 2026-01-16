"""Service model for Timebutler API."""

from pydantic import BaseModel, ConfigDict, Field, computed_field

from timebutler_client.models.absence import EuropeanDate

__all__ = ["Service"]


class Service(BaseModel):
    """
    Represents a service from Timebutler.

    Services are used to categorize worktime entries by type of work.
    """

    model_config = ConfigDict(frozen=True)

    id: int = Field(description="Unique service identifier")
    name: str = Field(description="Service name (free text, may contain whitespace)")
    state: str = Field(description="Service state: 'Active' or 'Inactive'")
    billable: bool = Field(default=False, description="Whether the service is billable")
    comments: str | None = Field(default=None, description="Optional comments")
    creation_date: EuropeanDate = Field(description="Date the service was created")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def name_stripped(self) -> str:
        """Service name with leading/trailing whitespace removed."""
        return self.name.strip()  # pylint: disable=no-member

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_active(self) -> bool:
        """True if service state is Active."""
        return self.state == "Active"

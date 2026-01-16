"""Project model for Timebutler API."""

from pydantic import BaseModel, ConfigDict, Field, computed_field

from timebutler_client.models.absence import EuropeanDate

__all__ = ["Project"]


class Project(BaseModel):
    """
    Represents a project from Timebutler.

    Projects are used to categorize worktime entries. The name field
    is free text set by users and may contain trailing whitespace.
    """

    model_config = ConfigDict(frozen=True)

    id: int = Field(description="Unique project identifier")
    name: str = Field(description="Project name (free text, may contain whitespace)")
    state: str = Field(description="Project state: 'Active' or 'Inactive'")
    budget_hours: int = Field(default=0, description="Budget in hours, 0 if not set")
    comments: str | None = Field(default=None, description="Optional comments")
    creation_date: EuropeanDate = Field(description="Date the project was created")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def name_stripped(self) -> str:
        """Project name with leading/trailing whitespace removed."""
        return self.name.strip()  # pylint: disable=no-member

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_active(self) -> bool:
        """True if project state is Active."""
        return self.state == "Active"

"""Base class for generated Timebutler API v2 models."""

from pydantic import BaseModel, ConfigDict


class V2BaseModel(BaseModel):
    """Frozen base model; fields are snake_case, JSON uses camelCase aliases."""

    model_config = ConfigDict(frozen=True, populate_by_name=True)

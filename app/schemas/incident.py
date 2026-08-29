from typing import Literal
from datetime import datetime
from pydantic import BaseModel, Field
from pydantic import BaseModel, ConfigDict, Field


class IncidentCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=5)
    service: str = Field(min_length=2, max_length=100)
    severity: Literal["low", "medium", "high", "critical"]


class IncidentUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=200)
    description: str | None = Field(default=None, min_length=5)
    service: str | None = Field(default=None, min_length=2, max_length=100)
    severity: Literal["low", "medium", "high", "critical"] | None = None
    status: str | None = None

class IncidentResponse(BaseModel):
    id: int
    title: str
    description: str
    service: str
    severity: Literal["low", "medium", "high", "critical"]
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
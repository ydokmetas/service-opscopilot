from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

IncidentSeverity = Literal["low", "medium", "high", "critical"]
IncidentStatus = Literal["triggered", "acknowledged", "resolved"]
IncidentDescription = Annotated[str, Field(min_length=5)]
IncidentTitle = Annotated[str, Field(min_length=3, max_length=200)]
IncidentService = Annotated[str, Field(min_length=2, max_length=100)]

class IncidentCreate(BaseModel):
    title: IncidentTitle
    description: IncidentDescription
    service: IncidentService
    severity: IncidentSeverity


class IncidentUpdate(BaseModel):
    title: IncidentTitle | None = None
    description: IncidentDescription | None = None
    service: IncidentService | None = None
    severity: IncidentSeverity | None = None
    status: IncidentStatus | None = None

class IncidentResponse(BaseModel):
    id: int
    title: IncidentTitle
    description: IncidentDescription
    service: IncidentService
    severity: IncidentSeverity
    status: IncidentStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

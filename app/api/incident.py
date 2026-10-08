from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.incident import (
    IncidentCreate,
    IncidentResponse,
    IncidentService,
    IncidentSeverity,
    IncidentStatus,
    IncidentUpdate,
)
from app.services import incident as incident_service

DbSession = Annotated[Session, Depends(get_db)]

router = APIRouter(prefix="/incidents", tags=["incidents"])

@router.get("", response_model=list[IncidentResponse])
def list_incidents(
    db: DbSession,
    service: Annotated[IncidentService | None, Query()] = None,
    severity: IncidentSeverity | None = None,
    status: Annotated[IncidentStatus | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    return incident_service.list_incidents(
        db=db,
        service=service,
        severity=severity,
        status=status,
        limit=limit,
        offset=offset,
    )


@router.get("/{incident_id}", response_model=IncidentResponse)
def get_incident(incident_id: int, db: DbSession,):
    incident = incident_service.get_incident(db, incident_id)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    return incident

@router.post("", status_code=status.HTTP_201_CREATED, response_model=IncidentResponse)
def create_incident(incident: IncidentCreate, db: DbSession,):
    data = incident.model_dump()
    return incident_service.create_incident(db, data)

@router.patch("/{incident_id}", response_model=IncidentResponse,)
def update_incident(incident_id: int, incident_update: IncidentUpdate, db: DbSession,):
    changes = incident_update.model_dump(
        exclude_unset=True,
        exclude_none=True,
    )
    incident = incident_service.update_incident(db, incident_id, changes)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    return incident
    
@router.delete("/{incident_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_incident(incident_id: int, db: DbSession,):
    deleted = incident_service.delete_incident(db, incident_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")


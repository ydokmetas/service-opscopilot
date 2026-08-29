from fastapi import APIRouter, Depends, HTTPException, Query

from app.schemas.incident import IncidentCreate, IncidentUpdate

from app.services import incident as incident_service

from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.schemas.incident import (
    IncidentCreate,
    IncidentResponse,
    IncidentUpdate,
)

from typing import Literal


router = APIRouter(prefix="/incidents", tags=["incidents"])

@router.get("", response_model=list[IncidentResponse])
def list_incidents(
    service: str | None = Query(
        default=None,
        min_length=2,
        max_length=100,
    ),
    severity: Literal[
        "low",
        "medium",
        "high",
        "critical",
    ] | None = None,
    status: str | None = Query(
        default=None,
        min_length=1,
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
    db: Session = Depends(get_db),
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
def get_incident(incident_id: int, db: Session = Depends(get_db),):
    incident = incident_service.get_incident(db, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident

@router.post("", status_code=201, response_model=IncidentResponse)
def create_incident(incident: IncidentCreate, db: Session = Depends(get_db),):
    data = incident.model_dump()
    return incident_service.create_incident(db, data)

@router.patch("/{incident_id}", response_model=IncidentResponse,)
def update_incident(incident_id: int, incident_update: IncidentUpdate, db: Session = Depends(get_db),):
    changes = incident_update.model_dump(
        exclude_unset=True,
        exclude_none=True,
    )
    incident = incident_service.update_incident(db, incident_id, changes)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident
    
@router.delete("/{incident_id}", status_code=204)
def delete_incident(incident_id: int, db: Session = Depends(get_db),):
    deleted = incident_service.delete_incident(db, incident_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Incident not found")


import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import Incident as IncidentModel


logger = logging.getLogger(__name__)

def list_incidents(
    db: Session,
    service: str | None = None,
    severity: str | None = None,
    status: str | None = None,
    limit: int = 20,
    offset: int = 0,
):
    statement = select(IncidentModel)

    if service is not None:
        statement = statement.where(
            IncidentModel.service == service
        )

    if severity is not None:
        statement = statement.where(
            IncidentModel.severity == severity
        )

    if status is not None:
        statement = statement.where(
            IncidentModel.status == status
        )

    statement = (
        statement
        .order_by(IncidentModel.id)
        .offset(offset)
        .limit(limit)
    )

    return list(db.scalars(statement).all())

def get_incident(db: Session, incident_id: int):
    return db.get(IncidentModel,incident_id)

def create_incident(db: Session, data: dict):
    incident = IncidentModel(
        **data,
        status="open",
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)

    logger.info(
        "incident_created incident_id=%s service=%s severity=%s",
        incident.id,
        incident.service,
        incident.severity,
    )

    return incident

def update_incident(db: Session,
                    incident_id: int, 
                    changes: dict):
    
    incident = db.get(IncidentModel,incident_id)

    if incident is None:
        logger.warning(
            "incident_update_target_not_found incident_id=%s",
            incident_id,
        )   
        return None

    for field, value in changes.items():
        setattr(incident,field,value)

    db.commit()
    db.refresh(incident)

    return incident


def delete_incident(db: Session, incident_id: int) -> bool:
    incident = db.get(IncidentModel,incident_id)

    if incident is None:
        logger.warning(
            "incident_delete_target_not_found incident_id=%s",
            incident_id,
        )
        return False

    db.delete(incident)
    db.commit()
    return True
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import Document as DocumentModel


def create_document(db: Session, data: dict):

    document = DocumentModel(**data)
    db.add(document)
    db.commit()
    db.refresh(document)
    return document

def list_documents(
    db: Session,
    title: str | None = None,
    document_type: str | None = None,
    limit: int = 20,
    offset: int = 0,
):
    statement = select(DocumentModel)

    if title is not None:
        statement = statement.where(DocumentModel.title == title)

    if document_type is not None:
        statement = statement.where(
            DocumentModel.document_type == document_type
        )

    statement = (
        statement
        .order_by(DocumentModel.id)
        .offset(offset)
        .limit(limit)
    )

    return list(db.scalars(statement).all())

def get_document(db: Session, document_id: int):
    return db.get(DocumentModel,document_id)

def delete_document(db: Session, document_id: int) -> bool:
    document = db.get(DocumentModel,document_id)

    if document is None:
        return False
    db.delete(document)
    db.commit()
    return True

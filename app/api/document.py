from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.document import DocumentCreate, DocumentResponse
from app.services import document as document_service

DbSession = Annotated[Session, Depends(get_db)]

router = APIRouter(
    prefix="/documents",
    tags=["documents"],
)

@router.post("",status_code=status.HTTP_201_CREATED, response_model=DocumentResponse)
def create_document(
    document: DocumentCreate,
    db: DbSession,
):
    data = document.model_dump()
    return document_service.create_document(db, data)

@router.get("", response_model=list[DocumentResponse])
def list_documents(
    db: DbSession,
    title: Annotated[str | None, Query(min_length=1, max_length=200)] = None,
    document_type: Annotated[str | None, Query(min_length=1, max_length=50)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    return document_service.list_documents(
        db=db,
        title=title,
        document_type=document_type,
        limit=limit,
        offset=offset,
    )

@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
)
def get_document(
    document_id: int,
    db: DbSession,
):
    document = document_service.get_document(db, document_id)

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    return document

@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: int,
    db: DbSession,
):
    deleted = document_service.delete_document(db, document_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

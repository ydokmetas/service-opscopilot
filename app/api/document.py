from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.document import DocumentCreate, DocumentResponse
from app.services import document as document_service

router = APIRouter(
    prefix="/documents",
    tags=["documents"],
)

@router.post("",status_code=201, response_model=DocumentResponse)
def create_document(
    document: DocumentCreate,
    db: Session = Depends(get_db),                
    ):
    data = document.model_dump()
    return document_service.create_document(db, data)

@router.get("", response_model=list[DocumentResponse])
def list_documents(
    title: str | None = Query(
        default=None,
        min_length=1,
        max_length=200,
    ),
    document_type: str | None = Query(
        default=None,
        min_length=1,
        max_length=50,
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
    db: Session = Depends(get_db),
):
    document = document_service.get_document(db, document_id)

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    return document

@router.delete("/{document_id}", status_code=204)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
):
    deleted = document_service.delete_document(db, document_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

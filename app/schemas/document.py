from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

class DocumentCreate(BaseModel):
    title: str = Field(min_length=1)
    document_type: str = Field(min_length=1)
    content: str = Field(min_length=1)

class DocumentResponse(DocumentCreate):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
    
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class NoteCreate(BaseModel):
    charity_id: str
    cycle_id: Optional[str] = None
    note_type: str = "general"
    content: str


class NoteUpdate(BaseModel):
    content: Optional[str] = None
    note_type: Optional[str] = None


class NoteResponse(BaseModel):
    id: str
    charity_id: str
    cycle_id: Optional[str] = None
    note_type: str
    content: str
    author_id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

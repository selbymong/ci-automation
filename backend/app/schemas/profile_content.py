from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ProfileContentCreate(BaseModel):
    charity_id: str
    section_type: str
    content: str = ""


class ProfileContentUpdate(BaseModel):
    content: str


class ProfileContentResponse(BaseModel):
    id: str
    charity_id: str
    section_type: str
    content: str
    version: int
    author_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class AssembledProfile(BaseModel):
    charity_id: str
    sections: dict[str, ProfileContentResponse]

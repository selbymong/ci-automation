from typing import Optional

from pydantic import BaseModel


class ContactCreate(BaseModel):
    charity_id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    notes: Optional[str] = None


class ContactUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    notes: Optional[str] = None


class ContactResponse(BaseModel):
    id: str
    charity_id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    notes: Optional[str] = None

    model_config = {"from_attributes": True}

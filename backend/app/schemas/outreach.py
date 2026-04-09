from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class OutreachCreate(BaseModel):
    evaluation_id: str
    charity_id: str


class OutreachUpdate(BaseModel):
    profile_sent_at: Optional[date] = None
    sent_to_email: Optional[str] = None
    email_saved: Optional[bool] = None
    read_receipt: Optional[bool] = None
    response_received: Optional[bool] = None
    response_received_at: Optional[date] = None
    call_scheduled: Optional[bool] = None
    call_scheduled_at: Optional[date] = None
    charity_adds_content: Optional[str] = None
    notes: Optional[str] = None


class OutreachResponse(BaseModel):
    id: str
    evaluation_id: str
    charity_id: str
    profile_sent_at: Optional[date] = None
    sent_to_email: Optional[str] = None
    email_saved: bool
    read_receipt: bool
    response_received: bool
    response_received_at: Optional[date] = None
    call_scheduled: bool
    call_scheduled_at: Optional[date] = None
    charity_adds_content: Optional[str] = None
    notes: Optional[str] = None
    analyst_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

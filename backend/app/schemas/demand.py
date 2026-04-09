from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CharityRequestCreate(BaseModel):
    requester_name: str
    requester_email: str
    requested_charity_name: str


class CharityRequestUpdate(BaseModel):
    status: Optional[str] = None
    matched_charity_id: Optional[str] = None
    disposition: Optional[str] = None
    notes: Optional[str] = None


class CharityRequestResponse(BaseModel):
    id: str
    requester_name: str
    requester_email: str
    requested_charity_name: str
    status: str
    matched_charity_id: Optional[str] = None
    disposition: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class DemandAggregateResponse(BaseModel):
    id: str
    charity_id: str
    vote_count: int
    disposition: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class DemandAggregateUpdate(BaseModel):
    disposition: Optional[str] = None

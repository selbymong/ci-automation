from datetime import date
from typing import Optional

from pydantic import BaseModel


class CRARequestCreate(BaseModel):
    charity_id: str
    years_requested: str
    requested_at: Optional[date] = None
    batch_id: Optional[str] = None


class CRARequestUpdate(BaseModel):
    status: Optional[str] = None
    received_at: Optional[date] = None


class CRARequestResponse(BaseModel):
    id: str
    charity_id: str
    years_requested: str
    status: str
    requested_at: Optional[date] = None
    received_at: Optional[date] = None
    batch_id: Optional[str] = None

    model_config = {"from_attributes": True}


class CRABatchCreate(BaseModel):
    charity_ids: list[str]
    years_requested: str
    batch_id: str
    requested_at: Optional[date] = None

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class CycleCreate(BaseModel):
    name: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    target_count: Optional[int] = None


class CycleUpdate(BaseModel):
    name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    target_count: Optional[int] = None


class CycleTransition(BaseModel):
    status: str


class CycleResponse(BaseModel):
    id: str
    name: str
    status: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    target_count: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

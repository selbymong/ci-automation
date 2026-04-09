from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class TrafficSnapshotCreate(BaseModel):
    charity_id: str
    period_start: date
    period_end: date
    page_views: int = 0
    active_users: int = 0
    avg_engagement_seconds: Optional[float] = None


class TrafficSnapshotResponse(BaseModel):
    id: str
    charity_id: str
    period_start: date
    period_end: date
    page_views: int
    active_users: int
    avg_engagement_seconds: Optional[float] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

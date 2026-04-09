from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class RatingCreate(BaseModel):
    charity_id: str
    cycle_id: Optional[str] = None
    admin_percent: Optional[float] = None
    fundraising_percent: Optional[float] = None
    overhead_percent: Optional[float] = None
    program_cost_coverage: Optional[float] = None
    srss_score: Optional[float] = None
    notes: Optional[str] = None


class RatingUpdate(BaseModel):
    admin_percent: Optional[float] = None
    fundraising_percent: Optional[float] = None
    overhead_percent: Optional[float] = None
    program_cost_coverage: Optional[float] = None
    srss_score: Optional[float] = None
    star_rating: Optional[int] = None
    impact_x: Optional[float] = None
    impact_y: Optional[float] = None
    impact_label: Optional[str] = None
    notes: Optional[str] = None


class RatingResponse(BaseModel):
    id: str
    charity_id: str
    cycle_id: Optional[str] = None
    star_rating: Optional[int] = None
    impact_x: Optional[float] = None
    impact_y: Optional[float] = None
    impact_label: Optional[str] = None
    admin_percent: Optional[float] = None
    fundraising_percent: Optional[float] = None
    overhead_percent: Optional[float] = None
    program_cost_coverage: Optional[float] = None
    srss_score: Optional[float] = None
    notes: Optional[str] = None
    analyst_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

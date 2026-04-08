from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PublishedEvaluation(BaseModel):
    charity_id: str
    business_number: str
    formal_name: str
    common_name: Optional[str] = None
    sector: Optional[str] = None
    star_rating: Optional[float] = None
    impact_rating_x: Optional[float] = None
    impact_rating_y: Optional[float] = None
    srss_grade: Optional[str] = None
    srss_score_pct: Optional[float] = None
    transparency_level: Optional[int] = None
    results_and_impact: Optional[str] = None
    financial_notes: Optional[str] = None
    published_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class DemandSignal(BaseModel):
    business_number: Optional[str] = None
    requested_name: str
    vote_count: int
    first_requested_at: Optional[datetime] = None
    last_requested_at: Optional[datetime] = None

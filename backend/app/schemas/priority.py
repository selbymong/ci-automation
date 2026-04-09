from typing import Optional

from pydantic import BaseModel


class PriorityCalculateRequest(BaseModel):
    page_views: Optional[int] = None
    years_since_eval: Optional[float] = None
    demand_votes: Optional[int] = None


class PriorityScoreResponse(BaseModel):
    id: str
    charity_id: str
    views_score: float
    staleness_score: float
    demand_score: float
    top100_bonus: float
    composite_score: float
    priority_rank: int
    page_views: Optional[int] = None
    years_since_eval: Optional[float] = None
    demand_votes: Optional[int] = None

    model_config = {"from_attributes": True}


class PriorityQueueItem(BaseModel):
    charity_id: str
    cra_number: str
    formal_name: str
    priority_rank: int
    composite_score: float

    model_config = {"from_attributes": True}

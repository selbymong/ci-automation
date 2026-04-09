from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class EvaluationCreate(BaseModel):
    charity_id: str
    cycle_id: str
    analyst_id: Optional[str] = None


class EvaluationTransition(BaseModel):
    to_stage: str
    note: Optional[str] = None


class EvaluationResponse(BaseModel):
    id: str
    charity_id: str
    cycle_id: str
    stage: str
    analyst_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class StageLogResponse(BaseModel):
    id: str
    evaluation_id: str
    from_stage: str
    to_stage: str
    actor_id: str
    note: Optional[str] = None
    transitioned_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class KanbanColumn(BaseModel):
    stage: str
    evaluations: list[EvaluationResponse]
    count: int

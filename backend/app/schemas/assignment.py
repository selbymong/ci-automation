from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AssignmentCreate(BaseModel):
    analyst_id: str
    charity_id: str
    cycle_id: str


class AssignmentBulkCreate(BaseModel):
    analyst_id: str
    charity_ids: list[str]
    cycle_id: str


class AssignmentReassign(BaseModel):
    new_analyst_id: str
    reason: Optional[str] = None


class AssignmentResponse(BaseModel):
    id: str
    analyst_id: str
    charity_id: str
    cycle_id: str
    assigned_at: Optional[datetime] = None
    reassigned_from_id: Optional[str] = None
    reassignment_reason: Optional[str] = None

    model_config = {"from_attributes": True}


class WorkloadItem(BaseModel):
    analyst_id: str
    analyst_name: str
    assignment_count: int

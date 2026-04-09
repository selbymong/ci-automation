from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AuthorizationCreate(BaseModel):
    evaluation_id: str
    step: str


class AuthorizationDecision(BaseModel):
    status: str  # "approved" or "rejected"
    comment: Optional[str] = None


class AuthorizationResponse(BaseModel):
    id: str
    evaluation_id: str
    step: str
    status: str
    reviewer_id: Optional[str] = None
    comment: Optional[str] = None
    decided_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

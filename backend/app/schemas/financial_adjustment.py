from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class FinancialAdjustmentCreate(BaseModel):
    charity_id: str
    analysis_id: Optional[str] = None
    adjustment_type: str
    description: str
    amount: Optional[float] = None
    field_affected: Optional[str] = None


class FinancialAdjustmentUpdate(BaseModel):
    adjustment_type: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[float] = None
    field_affected: Optional[str] = None


class FinancialAdjustmentResponse(BaseModel):
    id: str
    charity_id: str
    analysis_id: Optional[str] = None
    adjustment_type: str
    description: str
    amount: Optional[float] = None
    field_affected: Optional[str] = None
    analyst_id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

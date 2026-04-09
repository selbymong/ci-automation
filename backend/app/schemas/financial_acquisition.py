from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class FinancialAcquisitionCreate(BaseModel):
    charity_id: str
    cycle_id: str


class FinancialAcquisitionUpdate(BaseModel):
    status: Optional[str] = None
    afs_online_checked_at: Optional[date] = None
    afs_url: Optional[str] = None
    rfi_sent_at: Optional[date] = None
    rfi_2_sent_at: Optional[date] = None
    phone_followup_at: Optional[date] = None
    cra_request_at: Optional[date] = None
    received_at: Optional[date] = None
    financial_statement_url: Optional[str] = None
    notes: Optional[str] = None


class FinancialAcquisitionResponse(BaseModel):
    id: str
    charity_id: str
    cycle_id: str
    status: str
    afs_online_checked_at: Optional[date] = None
    afs_url: Optional[str] = None
    rfi_sent_at: Optional[date] = None
    rfi_2_sent_at: Optional[date] = None
    phone_followup_at: Optional[date] = None
    cra_request_at: Optional[date] = None
    received_at: Optional[date] = None
    financial_statement_url: Optional[str] = None
    notes: Optional[str] = None
    escalation_needed: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

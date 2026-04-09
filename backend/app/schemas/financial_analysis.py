from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class FinancialAnalysisCreate(BaseModel):
    charity_id: str
    cycle_id: Optional[str] = None
    fiscal_year_end: str
    year_number: int = 1

    # Revenue
    donations: Optional[float] = None
    government_funding: Optional[float] = None
    other_revenue: Optional[float] = None
    total_revenue: Optional[float] = None

    # Expenses
    program_costs: Optional[float] = None
    admin_costs: Optional[float] = None
    fundraising_costs: Optional[float] = None
    total_expenses: Optional[float] = None

    # Balance sheet
    total_assets: Optional[float] = None
    total_liabilities: Optional[float] = None
    net_assets: Optional[float] = None
    reserves: Optional[float] = None

    notes: Optional[str] = None


class FinancialAnalysisUpdate(BaseModel):
    fiscal_year_end: Optional[str] = None

    donations: Optional[float] = None
    government_funding: Optional[float] = None
    other_revenue: Optional[float] = None
    total_revenue: Optional[float] = None

    program_costs: Optional[float] = None
    admin_costs: Optional[float] = None
    fundraising_costs: Optional[float] = None
    total_expenses: Optional[float] = None

    total_assets: Optional[float] = None
    total_liabilities: Optional[float] = None
    net_assets: Optional[float] = None
    reserves: Optional[float] = None

    notes: Optional[str] = None


class FinancialAnalysisResponse(BaseModel):
    id: str
    charity_id: str
    cycle_id: Optional[str] = None
    fiscal_year_end: str
    year_number: int

    donations: Optional[float] = None
    government_funding: Optional[float] = None
    other_revenue: Optional[float] = None
    total_revenue: Optional[float] = None

    program_costs: Optional[float] = None
    admin_costs: Optional[float] = None
    fundraising_costs: Optional[float] = None
    total_expenses: Optional[float] = None

    total_assets: Optional[float] = None
    total_liabilities: Optional[float] = None
    net_assets: Optional[float] = None
    reserves: Optional[float] = None

    admin_percent: Optional[float] = None
    fundraising_percent: Optional[float] = None
    overhead_percent: Optional[float] = None
    program_cost_coverage: Optional[float] = None

    notes: Optional[str] = None
    analyst_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class FinancialSummary(BaseModel):
    charity_id: str
    years: list[FinancialAnalysisResponse]

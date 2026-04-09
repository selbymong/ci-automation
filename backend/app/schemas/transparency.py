from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class TransparencyConfigCreate(BaseModel):
    charity_id: str


class TransparencyConfigUpdate(BaseModel):
    show_donations: Optional[bool] = None
    show_government_funding: Optional[bool] = None
    show_other_revenue: Optional[bool] = None
    show_total_revenue: Optional[bool] = None
    show_program_costs: Optional[bool] = None
    show_admin_costs: Optional[bool] = None
    show_fundraising_costs: Optional[bool] = None
    show_total_expenses: Optional[bool] = None
    show_total_assets: Optional[bool] = None
    show_total_liabilities: Optional[bool] = None
    show_net_assets: Optional[bool] = None
    show_reserves: Optional[bool] = None
    show_admin_percent: Optional[bool] = None
    show_fundraising_percent: Optional[bool] = None
    show_overhead_percent: Optional[bool] = None
    show_program_cost_coverage: Optional[bool] = None
    show_compensation: Optional[bool] = None
    show_endowment: Optional[bool] = None
    show_capital_assets: Optional[bool] = None
    show_pension: Optional[bool] = None
    show_deferred_revenue: Optional[bool] = None
    show_foreign_activity: Optional[bool] = None
    show_gifts_to_other_charities: Optional[bool] = None
    show_political_expenditure: Optional[bool] = None
    show_staff_count: Optional[bool] = None
    show_volunteer_count: Optional[bool] = None
    show_board_compensation: Optional[bool] = None
    show_top10_compensation: Optional[bool] = None
    show_related_party: Optional[bool] = None
    show_professional_fundraiser: Optional[bool] = None


class TransparencyConfigResponse(BaseModel):
    id: str
    charity_id: str

    show_donations: bool
    show_government_funding: bool
    show_other_revenue: bool
    show_total_revenue: bool
    show_program_costs: bool
    show_admin_costs: bool
    show_fundraising_costs: bool
    show_total_expenses: bool
    show_total_assets: bool
    show_total_liabilities: bool
    show_net_assets: bool
    show_reserves: bool
    show_admin_percent: bool
    show_fundraising_percent: bool
    show_overhead_percent: bool
    show_program_cost_coverage: bool
    show_compensation: bool
    show_endowment: bool
    show_capital_assets: bool
    show_pension: bool
    show_deferred_revenue: bool
    show_foreign_activity: bool
    show_gifts_to_other_charities: bool
    show_political_expenditure: bool
    show_staff_count: bool
    show_volunteer_count: bool
    show_board_compensation: bool
    show_top10_compensation: bool
    show_related_party: bool
    show_professional_fundraiser: bool

    transparency_score: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

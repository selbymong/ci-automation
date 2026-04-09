import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TransparencyConfig(Base):
    __tablename__ = "transparency_config"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    charity_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("charity.id"), nullable=False, unique=True
    )

    # Display flags (REPORT_Show* booleans)
    show_donations: Mapped[bool] = mapped_column(Boolean, default=True)
    show_government_funding: Mapped[bool] = mapped_column(Boolean, default=True)
    show_other_revenue: Mapped[bool] = mapped_column(Boolean, default=True)
    show_total_revenue: Mapped[bool] = mapped_column(Boolean, default=True)
    show_program_costs: Mapped[bool] = mapped_column(Boolean, default=True)
    show_admin_costs: Mapped[bool] = mapped_column(Boolean, default=True)
    show_fundraising_costs: Mapped[bool] = mapped_column(Boolean, default=True)
    show_total_expenses: Mapped[bool] = mapped_column(Boolean, default=True)
    show_total_assets: Mapped[bool] = mapped_column(Boolean, default=True)
    show_total_liabilities: Mapped[bool] = mapped_column(Boolean, default=True)
    show_net_assets: Mapped[bool] = mapped_column(Boolean, default=True)
    show_reserves: Mapped[bool] = mapped_column(Boolean, default=True)
    show_admin_percent: Mapped[bool] = mapped_column(Boolean, default=True)
    show_fundraising_percent: Mapped[bool] = mapped_column(Boolean, default=True)
    show_overhead_percent: Mapped[bool] = mapped_column(Boolean, default=True)
    show_program_cost_coverage: Mapped[bool] = mapped_column(Boolean, default=True)
    show_compensation: Mapped[bool] = mapped_column(Boolean, default=False)
    show_endowment: Mapped[bool] = mapped_column(Boolean, default=False)
    show_capital_assets: Mapped[bool] = mapped_column(Boolean, default=False)
    show_pension: Mapped[bool] = mapped_column(Boolean, default=False)
    show_deferred_revenue: Mapped[bool] = mapped_column(Boolean, default=False)
    show_foreign_activity: Mapped[bool] = mapped_column(Boolean, default=False)
    show_gifts_to_other_charities: Mapped[bool] = mapped_column(Boolean, default=False)
    show_political_expenditure: Mapped[bool] = mapped_column(Boolean, default=False)
    show_staff_count: Mapped[bool] = mapped_column(Boolean, default=False)
    show_volunteer_count: Mapped[bool] = mapped_column(Boolean, default=False)
    show_board_compensation: Mapped[bool] = mapped_column(Boolean, default=False)
    show_top10_compensation: Mapped[bool] = mapped_column(Boolean, default=False)
    show_related_party: Mapped[bool] = mapped_column(Boolean, default=False)
    show_professional_fundraiser: Mapped[bool] = mapped_column(Boolean, default=False)

    # Derived transparency score (1-3)
    transparency_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


# All flag field names for iteration
TRANSPARENCY_FLAGS = [
    "show_donations", "show_government_funding", "show_other_revenue",
    "show_total_revenue", "show_program_costs", "show_admin_costs",
    "show_fundraising_costs", "show_total_expenses", "show_total_assets",
    "show_total_liabilities", "show_net_assets", "show_reserves",
    "show_admin_percent", "show_fundraising_percent", "show_overhead_percent",
    "show_program_cost_coverage", "show_compensation", "show_endowment",
    "show_capital_assets", "show_pension", "show_deferred_revenue",
    "show_foreign_activity", "show_gifts_to_other_charities",
    "show_political_expenditure", "show_staff_count", "show_volunteer_count",
    "show_board_compensation", "show_top10_compensation", "show_related_party",
    "show_professional_fundraiser",
]

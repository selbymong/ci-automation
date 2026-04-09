import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class FinancialAnalysis(Base):
    __tablename__ = "financial_analysis"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    charity_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("charity.id"), nullable=False
    )
    cycle_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("evaluation_cycle.id"), nullable=True
    )
    fiscal_year_end: Mapped[str] = mapped_column(String(10), nullable=False)

    # Revenue
    donations: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    government_funding: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    other_revenue: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_revenue: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Expenses
    program_costs: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    admin_costs: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    fundraising_costs: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_expenses: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Balance sheet
    total_assets: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_liabilities: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    net_assets: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    reserves: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Derived metrics (auto-calculated)
    admin_percent: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    fundraising_percent: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    overhead_percent: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    program_cost_coverage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Year comparison
    year_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    analyst_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("user.id"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

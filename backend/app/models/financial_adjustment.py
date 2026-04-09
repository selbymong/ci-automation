import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AdjustmentType(str, enum.Enum):
    deferred_contributions = "deferred_contributions"
    amortization = "amortization"
    consolidation = "consolidation"
    reclassification = "reclassification"
    other = "other"


class FinancialAdjustment(Base):
    __tablename__ = "financial_adjustment"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    charity_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("charity.id"), nullable=False
    )
    analysis_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("financial_analysis.id"), nullable=True
    )
    adjustment_type: Mapped[str] = mapped_column(String(30), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    field_affected: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    analyst_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("user.id"), nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

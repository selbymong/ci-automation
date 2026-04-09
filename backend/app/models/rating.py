import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class CharityRating(Base):
    __tablename__ = "charity_rating"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    charity_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("charity.id"), nullable=False
    )
    cycle_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("evaluation_cycle.id"), nullable=True
    )

    # Star rating (1-5)
    star_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Impact rating as X,Y coordinate
    impact_x: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    impact_y: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    impact_label: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Source metrics
    admin_percent: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    fundraising_percent: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    overhead_percent: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    program_cost_coverage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    srss_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    analyst_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("user.id"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

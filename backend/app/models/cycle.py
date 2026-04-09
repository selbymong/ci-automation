import enum
import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class CycleStatus(str, enum.Enum):
    planning = "planning"
    active = "active"
    review = "review"
    closed = "closed"


CYCLE_TRANSITIONS = {
    CycleStatus.planning: [CycleStatus.active],
    CycleStatus.active: [CycleStatus.review],
    CycleStatus.review: [CycleStatus.closed, CycleStatus.active],
    CycleStatus.closed: [],
}


class EvaluationCycle(Base):
    __tablename__ = "evaluation_cycle"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=CycleStatus.planning.value
    )
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    target_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

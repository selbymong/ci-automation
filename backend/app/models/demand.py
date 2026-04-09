import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class RequestStatus(str, enum.Enum):
    new = "new"
    matched = "matched"
    unmatched = "unmatched"


class DispositionType(str, enum.Enum):
    done = "done"
    to_do = "to_do"
    not_a_charity = "not_a_charity"
    too_small = "too_small"
    not_in_canada = "not_in_canada"


class CharityRequest(Base):
    """Public request for a charity evaluation."""
    __tablename__ = "charity_request"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    requester_name: Mapped[str] = mapped_column(String(200), nullable=False)
    requester_email: Mapped[str] = mapped_column(String(255), nullable=False)
    requested_charity_name: Mapped[str] = mapped_column(String(300), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=RequestStatus.new.value
    )
    matched_charity_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("charity.id"), nullable=True
    )
    disposition: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class DemandAggregate(Base):
    """Aggregated vote counts per charity."""
    __tablename__ = "demand_aggregate"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    charity_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("charity.id"), nullable=False, unique=True
    )
    vote_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    disposition: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

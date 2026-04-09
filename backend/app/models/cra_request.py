import enum
import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class CRARequestStatus(str, enum.Enum):
    pending = "pending"
    received = "received"
    not_available = "not_available"


class CRADataRequest(Base):
    __tablename__ = "cra_data_request"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    charity_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("charity.id"), nullable=False
    )
    years_requested: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=CRARequestStatus.pending.value
    )
    requested_at: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    received_at: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    batch_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

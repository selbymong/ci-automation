import enum
import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AcquisitionStatus(str, enum.Enum):
    not_started = "not_started"
    afs_checked = "afs_checked"
    rfi_sent = "rfi_sent"
    rfi_2_sent = "rfi_2_sent"
    phone_followup = "phone_followup"
    cra_requested = "cra_requested"
    received = "received"
    not_available = "not_available"


class FinancialAcquisition(Base):
    __tablename__ = "financial_acquisition"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    charity_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("charity.id"), nullable=False
    )
    cycle_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("evaluation_cycle.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=AcquisitionStatus.not_started.value
    )
    afs_online_checked_at: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    afs_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    rfi_sent_at: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    rfi_2_sent_at: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    phone_followup_at: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    cra_request_at: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    received_at: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    financial_statement_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

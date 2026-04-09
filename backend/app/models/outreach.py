import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class CharityOutreach(Base):
    __tablename__ = "charity_outreach"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    evaluation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("evaluation.id"), nullable=False
    )
    charity_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("charity.id"), nullable=False
    )

    # Send tracking
    profile_sent_at: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    sent_to_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    email_saved: Mapped[bool] = mapped_column(Boolean, default=False)

    # Response tracking
    read_receipt: Mapped[bool] = mapped_column(Boolean, default=False)
    response_received: Mapped[bool] = mapped_column(Boolean, default=False)
    response_received_at: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    call_scheduled: Mapped[bool] = mapped_column(Boolean, default=False)
    call_scheduled_at: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Charity response content
    charity_adds_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    analyst_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("user.id"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

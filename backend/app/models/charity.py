import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Charity(Base):
    __tablename__ = "charity"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    cra_number: Mapped[str] = mapped_column(String(15), unique=True, nullable=False)
    formal_name: Mapped[str] = mapped_column(String(500), nullable=False)
    common_name: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    sector: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    sub_sector: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    fiscal_year_end: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    province: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_top_100: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

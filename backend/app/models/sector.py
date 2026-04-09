import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SectorGroup(Base):
    __tablename__ = "sector_group"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    sectors: Mapped[list["Sector"]] = relationship(back_populates="group", lazy="selectin")


class Sector(Base):
    __tablename__ = "sector"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    group_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("sector_group.id"), nullable=True
    )
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    group: Mapped[SectorGroup | None] = relationship(back_populates="sectors", lazy="selectin")
    sub_sectors: Mapped[list["SubSector"]] = relationship(back_populates="sector", lazy="selectin")


class SubSector(Base):
    __tablename__ = "sub_sector"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    sector_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sector.id"), nullable=False
    )
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    sector: Mapped[Sector] = relationship(back_populates="sub_sectors", lazy="selectin")

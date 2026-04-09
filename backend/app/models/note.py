import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class NoteType(str, enum.Enum):
    general = "general"
    financial = "financial"
    followup = "followup"
    difficulty = "difficulty"


class EvaluationNote(Base):
    __tablename__ = "evaluation_note"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    charity_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("charity.id"), nullable=False
    )
    cycle_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("evaluation_cycle.id"), nullable=True
    )
    note_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default=NoteType.general.value
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    author_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("user.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

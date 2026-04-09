import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


# SRSS category definitions
SRSS_CATEGORIES = {
    "strategy": {"questions": list(range(1, 5)), "label": "Strategy"},          # Q1-Q4
    "activities": {"questions": list(range(5, 9)), "label": "Activities"},       # Q5-Q8
    "outputs": {"questions": list(range(9, 14)), "label": "Outputs"},            # Q9-Q13
    "outcomes": {"questions": list(range(14, 19)), "label": "Outcomes"},          # Q14-Q18
    "quality": {"questions": list(range(19, 23)), "label": "Quality"},            # Q19-Q22
    "learning": {"questions": list(range(23, 27)), "label": "Learning"},          # Q23-Q26
}

# Maximum scores per question (most are 0-8, varies by question)
QUESTION_MAX_SCORES = {i: 8 for i in range(1, 27)}

# Grade thresholds
GRADE_THRESHOLDS = [
    (90, "A+"), (80, "A"), (70, "B+"), (60, "B"),
    (50, "C"), (40, "D"), (0, "F"),
]


def percentage_to_grade(pct: float) -> str:
    for threshold, grade in GRADE_THRESHOLDS:
        if pct >= threshold:
            return grade
    return "F"


class SRSSScore(Base):
    __tablename__ = "srss_score"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    charity_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("charity.id"), nullable=False
    )
    cycle_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("evaluation_cycle.id"), nullable=True
    )
    year: Mapped[int] = mapped_column(Integer, nullable=False)

    # Individual question scores (Q1-Q26)
    q1: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    q2: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    q3: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    q4: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    q5: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    q6: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    q7: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    q8: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    q9: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    q10: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    q11: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    q12: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    q13: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    q14: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    q15: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    q16: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    q17: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    q18: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    q19: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    q20: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    q21: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    q22: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    q23: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    q24: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    q25: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    q26: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Category percentages (derived)
    strategy_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    activities_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    outputs_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    outcomes_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    quality_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    learning_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Total (derived)
    total_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    letter_grade: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)

    analyst_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("user.id"), nullable=True
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class SRSSHistorical(Base):
    """Stores historical SRSS scores by year for trend tracking."""
    __tablename__ = "srss_historical"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    charity_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("charity.id"), nullable=False
    )
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    total_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    letter_grade: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)

    strategy_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    activities_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    outputs_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    outcomes_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    quality_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    learning_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

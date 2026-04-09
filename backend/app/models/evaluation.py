import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class EvaluationStage(str, enum.Enum):
    prioritized = "prioritized"
    assigned = "assigned"
    financials_acquisition = "financials_acquisition"
    federal_corp_check = "federal_corp_check"
    cra_data_pull = "cra_data_pull"
    financial_analysis = "financial_analysis"
    srss_scoring = "srss_scoring"
    impact_scoring = "impact_scoring"
    review = "review"
    charity_outreach = "charity_outreach"
    charity_response = "charity_response"
    published = "published"


STAGE_ORDER = list(EvaluationStage)

# Forward-only transitions plus explicit rejection back to prior stage
VALID_TRANSITIONS: dict[EvaluationStage, list[EvaluationStage]] = {}
for i, stage in enumerate(STAGE_ORDER):
    forward = [STAGE_ORDER[i + 1]] if i + 1 < len(STAGE_ORDER) else []
    backward = [STAGE_ORDER[i - 1]] if i > 0 else []
    VALID_TRANSITIONS[stage] = forward + backward


class Evaluation(Base):
    __tablename__ = "evaluation"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    charity_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("charity.id"), nullable=False
    )
    cycle_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("evaluation_cycle.id"), nullable=False
    )
    stage: Mapped[str] = mapped_column(
        String(30), nullable=False, default=EvaluationStage.prioritized.value
    )
    analyst_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("user.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class EvaluationStageLog(Base):
    __tablename__ = "evaluation_stage_log"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    evaluation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("evaluation.id"), nullable=False
    )
    from_stage: Mapped[str] = mapped_column(String(30), nullable=False)
    to_stage: Mapped[str] = mapped_column(String(30), nullable=False)
    actor_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("user.id"), nullable=False
    )
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    transitioned_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

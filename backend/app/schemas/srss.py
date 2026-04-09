from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class SRSSScoreCreate(BaseModel):
    charity_id: str
    cycle_id: Optional[str] = None
    year: int

    q1: Optional[int] = None
    q2: Optional[int] = None
    q3: Optional[int] = None
    q4: Optional[int] = None
    q5: Optional[int] = None
    q6: Optional[int] = None
    q7: Optional[int] = None
    q8: Optional[int] = None
    q9: Optional[int] = None
    q10: Optional[int] = None
    q11: Optional[int] = None
    q12: Optional[int] = None
    q13: Optional[int] = None
    q14: Optional[int] = None
    q15: Optional[int] = None
    q16: Optional[int] = None
    q17: Optional[int] = None
    q18: Optional[int] = None
    q19: Optional[int] = None
    q20: Optional[int] = None
    q21: Optional[int] = None
    q22: Optional[int] = None
    q23: Optional[int] = None
    q24: Optional[int] = None
    q25: Optional[int] = None
    q26: Optional[int] = None

    notes: Optional[str] = None


class SRSSScoreUpdate(BaseModel):
    q1: Optional[int] = None
    q2: Optional[int] = None
    q3: Optional[int] = None
    q4: Optional[int] = None
    q5: Optional[int] = None
    q6: Optional[int] = None
    q7: Optional[int] = None
    q8: Optional[int] = None
    q9: Optional[int] = None
    q10: Optional[int] = None
    q11: Optional[int] = None
    q12: Optional[int] = None
    q13: Optional[int] = None
    q14: Optional[int] = None
    q15: Optional[int] = None
    q16: Optional[int] = None
    q17: Optional[int] = None
    q18: Optional[int] = None
    q19: Optional[int] = None
    q20: Optional[int] = None
    q21: Optional[int] = None
    q22: Optional[int] = None
    q23: Optional[int] = None
    q24: Optional[int] = None
    q25: Optional[int] = None
    q26: Optional[int] = None

    notes: Optional[str] = None


class SRSSScoreResponse(BaseModel):
    id: str
    charity_id: str
    cycle_id: Optional[str] = None
    year: int

    q1: Optional[int] = None
    q2: Optional[int] = None
    q3: Optional[int] = None
    q4: Optional[int] = None
    q5: Optional[int] = None
    q6: Optional[int] = None
    q7: Optional[int] = None
    q8: Optional[int] = None
    q9: Optional[int] = None
    q10: Optional[int] = None
    q11: Optional[int] = None
    q12: Optional[int] = None
    q13: Optional[int] = None
    q14: Optional[int] = None
    q15: Optional[int] = None
    q16: Optional[int] = None
    q17: Optional[int] = None
    q18: Optional[int] = None
    q19: Optional[int] = None
    q20: Optional[int] = None
    q21: Optional[int] = None
    q22: Optional[int] = None
    q23: Optional[int] = None
    q24: Optional[int] = None
    q25: Optional[int] = None
    q26: Optional[int] = None

    strategy_pct: Optional[float] = None
    activities_pct: Optional[float] = None
    outputs_pct: Optional[float] = None
    outcomes_pct: Optional[float] = None
    quality_pct: Optional[float] = None
    learning_pct: Optional[float] = None

    total_score: Optional[float] = None
    total_pct: Optional[float] = None
    letter_grade: Optional[str] = None

    analyst_id: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class SRSSHistoricalResponse(BaseModel):
    id: str
    charity_id: str
    year: int
    total_pct: Optional[float] = None
    letter_grade: Optional[str] = None
    strategy_pct: Optional[float] = None
    activities_pct: Optional[float] = None
    outputs_pct: Optional[float] = None
    outcomes_pct: Optional[float] = None
    quality_pct: Optional[float] = None
    learning_pct: Optional[float] = None

    model_config = {"from_attributes": True}


class SRSSHistoricalCreate(BaseModel):
    charity_id: str
    year: int
    total_pct: Optional[float] = None
    letter_grade: Optional[str] = None
    strategy_pct: Optional[float] = None
    activities_pct: Optional[float] = None
    outputs_pct: Optional[float] = None
    outcomes_pct: Optional[float] = None
    quality_pct: Optional[float] = None
    learning_pct: Optional[float] = None

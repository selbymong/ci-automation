from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.srss import (
    QUESTION_MAX_SCORES,
    SRSS_CATEGORIES,
    SRSSHistorical,
    SRSSScore,
    percentage_to_grade,
)
from app.models.user import User
from app.schemas.srss import (
    SRSSHistoricalCreate,
    SRSSHistoricalResponse,
    SRSSScoreCreate,
    SRSSScoreResponse,
    SRSSScoreUpdate,
)

router = APIRouter(prefix="/srss", tags=["srss"])


def _calculate_srss(score: SRSSScore) -> None:
    """Calculate category percentages, total, and grade from question scores."""
    total_raw = 0
    total_max = 0

    for cat_key, cat_info in SRSS_CATEGORIES.items():
        cat_raw = 0
        cat_max = 0
        for q_num in cat_info["questions"]:
            q_val = getattr(score, f"q{q_num}", None)
            if q_val is not None:
                cat_raw += q_val
                cat_max += QUESTION_MAX_SCORES[q_num]

        if cat_max > 0:
            pct = round(cat_raw / cat_max * 100, 2)
        else:
            pct = None

        setattr(score, f"{cat_key}_pct", pct)
        total_raw += cat_raw
        total_max += cat_max

    if total_max > 0:
        score.total_score = float(total_raw)
        score.total_pct = round(total_raw / total_max * 100, 2)
        score.letter_grade = percentage_to_grade(score.total_pct)
    else:
        score.total_score = None
        score.total_pct = None
        score.letter_grade = None


@router.post("/", response_model=SRSSScoreResponse, status_code=status.HTTP_201_CREATED)
async def create_srss_score(
    body: SRSSScoreCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> SRSSScore:
    score = SRSSScore(
        **body.model_dump(),
        analyst_id=current_user.id,
    )
    _calculate_srss(score)
    db.add(score)
    await db.commit()
    await db.refresh(score)
    return score


@router.get("/{score_id}", response_model=SRSSScoreResponse)
async def get_srss_score(
    score_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> SRSSScore:
    score = await db.get(SRSSScore, score_id)
    if not score:
        raise HTTPException(status_code=404, detail="SRSS score not found")
    return score


@router.put("/{score_id}", response_model=SRSSScoreResponse)
async def update_srss_score(
    score_id: str,
    body: SRSSScoreUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> SRSSScore:
    score = await db.get(SRSSScore, score_id)
    if not score:
        raise HTTPException(status_code=404, detail="SRSS score not found")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(score, key, value)
    _calculate_srss(score)
    await db.commit()
    await db.refresh(score)
    return score


@router.get("/charity/{charity_id}", response_model=list[SRSSScoreResponse])
async def list_srss_by_charity(
    charity_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> list[SRSSScore]:
    result = await db.execute(
        select(SRSSScore)
        .where(SRSSScore.charity_id == charity_id)
        .order_by(SRSSScore.year.desc())
    )
    return list(result.scalars().all())


# Historical SRSS endpoints (F031)

@router.post("/historical", response_model=SRSSHistoricalResponse, status_code=status.HTTP_201_CREATED)
async def create_historical(
    body: SRSSHistoricalCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> SRSSHistorical:
    record = SRSSHistorical(**body.model_dump())
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


@router.get("/historical/{charity_id}", response_model=list[SRSSHistoricalResponse])
async def list_historical(
    charity_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> list[SRSSHistorical]:
    result = await db.execute(
        select(SRSSHistorical)
        .where(SRSSHistorical.charity_id == charity_id)
        .order_by(SRSSHistorical.year)
    )
    return list(result.scalars().all())

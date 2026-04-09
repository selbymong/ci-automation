from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.charity import Charity
from app.models.priority import PriorityScore
from app.models.user import User
from app.schemas.priority import PriorityCalculateRequest, PriorityQueueItem, PriorityScoreResponse
from app.services.priority import calculate_priority

router = APIRouter(prefix="/priorities", tags=["priorities"])


@router.post("/{charity_id}/calculate", response_model=PriorityScoreResponse)
async def calculate_charity_priority(
    charity_id: str,
    body: PriorityCalculateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> PriorityScore:
    try:
        score = await calculate_priority(
            db, charity_id,
            page_views=body.page_views,
            years_since_eval=body.years_since_eval,
            demand_votes=body.demand_votes,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return score


@router.get("/{charity_id}", response_model=PriorityScoreResponse)
async def get_charity_priority(
    charity_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> PriorityScore:
    result = await db.execute(
        select(PriorityScore).where(PriorityScore.charity_id == charity_id)
    )
    score = result.scalar_one_or_none()
    if not score:
        raise HTTPException(status_code=404, detail="No priority score for this charity")
    return score


@router.get("/", response_model=list[PriorityQueueItem])
async def priority_queue(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
    limit: int = Query(50, ge=1, le=200),
) -> list[PriorityQueueItem]:
    result = await db.execute(
        select(
            PriorityScore.charity_id,
            Charity.cra_number,
            Charity.formal_name,
            PriorityScore.priority_rank,
            PriorityScore.composite_score,
        )
        .join(Charity, PriorityScore.charity_id == Charity.id)
        .where(Charity.deleted_at.is_(None))
        .order_by(PriorityScore.priority_rank, PriorityScore.composite_score.desc())
        .limit(limit)
    )
    rows = result.all()
    return [
        PriorityQueueItem(
            charity_id=r.charity_id,
            cra_number=r.cra_number,
            formal_name=r.formal_name,
            priority_rank=r.priority_rank,
            composite_score=r.composite_score,
        )
        for r in rows
    ]

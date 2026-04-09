"""F072: Data export API for Harness platform consumption.

Exposes published evaluations, incremental sync, and demand signals.
Authenticated via API key (X-API-Key header).
"""

import sys
from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.charity import Charity
from app.models.demand import DemandAggregate
from app.models.evaluation import Evaluation
from app.models.profile_content import ProfileContent
from app.models.rating import CharityRating
from app.models.srss import SRSSScore
from app.models.transparency import TransparencyConfig

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[3]))
from shared.api_contracts.evaluator_export import DemandSignal, PublishedEvaluation

router = APIRouter(prefix="/api/v1", tags=["export"])

EXPORT_API_KEY = "evaluator-export-key-dev"


async def verify_api_key(x_api_key: str = Header(...)):
    """Validate API key from request header."""
    expected = getattr(settings, "EXPORT_API_KEY", EXPORT_API_KEY)
    if x_api_key != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )


async def _build_evaluation(charity: Charity, eval: Evaluation, db: AsyncSession) -> PublishedEvaluation:
    """Assemble a PublishedEvaluation from related records."""
    # Rating
    result = await db.execute(
        select(CharityRating)
        .where(CharityRating.charity_id == charity.id)
        .order_by(CharityRating.created_at.desc())
        .limit(1)
    )
    rating = result.scalar_one_or_none()

    # SRSS
    result = await db.execute(
        select(SRSSScore)
        .where(SRSSScore.charity_id == charity.id)
        .order_by(SRSSScore.created_at.desc())
        .limit(1)
    )
    srss = result.scalar_one_or_none()

    # Transparency
    result = await db.execute(
        select(TransparencyConfig)
        .where(TransparencyConfig.charity_id == charity.id)
        .limit(1)
    )
    transparency = result.scalar_one_or_none()

    # Profile content: results_impact and financial_notes (latest versions)
    results_impact = None
    financial_notes = None
    result = await db.execute(
        select(ProfileContent)
        .where(
            ProfileContent.charity_id == charity.id,
            ProfileContent.section_type == "results_impact",
        )
        .order_by(ProfileContent.version.desc())
        .limit(1)
    )
    pc = result.scalar_one_or_none()
    if pc:
        results_impact = pc.content

    result = await db.execute(
        select(ProfileContent)
        .where(
            ProfileContent.charity_id == charity.id,
            ProfileContent.section_type == "financial_notes",
        )
        .order_by(ProfileContent.version.desc())
        .limit(1)
    )
    pc = result.scalar_one_or_none()
    if pc:
        financial_notes = pc.content

    return PublishedEvaluation(
        charity_id=charity.id,
        business_number=charity.cra_number,
        formal_name=charity.formal_name,
        common_name=charity.common_name,
        sector=charity.sector,
        star_rating=rating.star_rating if rating else None,
        impact_rating_x=rating.impact_x if rating else None,
        impact_rating_y=rating.impact_y if rating else None,
        srss_grade=srss.letter_grade if srss else None,
        srss_score_pct=srss.total_pct if srss else None,
        transparency_level=transparency.score if transparency else None,
        results_and_impact=results_impact,
        financial_notes=financial_notes,
        published_at=eval.updated_at,
        updated_at=eval.updated_at,
    )


@router.get(
    "/evaluations/published",
    response_model=list[PublishedEvaluation],
    dependencies=[Depends(verify_api_key)],
)
async def get_published_evaluations(
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    """Return all published evaluations for Harness consumption."""
    result = await db.execute(
        select(Evaluation)
        .where(Evaluation.stage == "published")
        .offset(skip)
        .limit(limit)
    )
    evaluations = list(result.scalars().all())

    published = []
    for eval in evaluations:
        charity = await db.get(Charity, eval.charity_id)
        if charity:
            published.append(await _build_evaluation(charity, eval, db))
    return published


@router.get(
    "/evaluations/updated-since",
    response_model=list[PublishedEvaluation],
    dependencies=[Depends(verify_api_key)],
)
async def get_updated_evaluations(
    since: datetime,
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(100, ge=1, le=500),
):
    """Return published evaluations updated after the given timestamp (incremental sync)."""
    result = await db.execute(
        select(Evaluation)
        .where(
            Evaluation.stage == "published",
            Evaluation.updated_at > since,
        )
        .order_by(Evaluation.updated_at)
        .limit(limit)
    )
    evaluations = list(result.scalars().all())

    published = []
    for eval in evaluations:
        charity = await db.get(Charity, eval.charity_id)
        if charity:
            published.append(await _build_evaluation(charity, eval, db))
    return published


@router.get(
    "/demand/signals",
    response_model=list[DemandSignal],
    dependencies=[Depends(verify_api_key)],
)
async def get_demand_signals(
    db: Annotated[AsyncSession, Depends(get_db)],
    min_votes: int = Query(1, ge=1),
    limit: int = Query(100, ge=1, le=1000),
):
    """Return aggregated donor demand signals for Harness."""
    result = await db.execute(
        select(DemandAggregate)
        .where(DemandAggregate.vote_count >= min_votes)
        .order_by(DemandAggregate.vote_count.desc())
        .limit(limit)
    )
    aggregates = list(result.scalars().all())

    signals = []
    for agg in aggregates:
        charity = await db.get(Charity, agg.charity_id)
        if not charity:
            continue
        signals.append(DemandSignal(
            business_number=charity.cra_number,
            requested_name=charity.formal_name,
            vote_count=agg.vote_count,
            first_requested_at=agg.created_at,
            last_requested_at=agg.updated_at,
        ))
    return signals

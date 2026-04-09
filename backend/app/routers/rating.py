from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.rating import CharityRating
from app.models.user import User
from app.schemas.rating import RatingCreate, RatingResponse, RatingUpdate

router = APIRouter(prefix="/ratings", tags=["ratings"])


def calculate_star_rating(
    overhead_pct: Optional[float],
    pcc: Optional[float],
    srss: Optional[float],
) -> Optional[int]:
    """Calculate star rating (1-5) from financial metrics.

    Algorithm:
    - Low overhead (<15%) + strong reserves (PCC > 1.0) + high SRSS (>80) = 5 stars
    - Scoring tiers based on overhead, reserves coverage, and SRSS
    """
    if overhead_pct is None and pcc is None and srss is None:
        return None

    score = 0.0
    components = 0

    if overhead_pct is not None:
        components += 1
        if overhead_pct < 15:
            score += 5.0
        elif overhead_pct < 25:
            score += 4.0
        elif overhead_pct < 35:
            score += 3.0
        elif overhead_pct < 50:
            score += 2.0
        else:
            score += 1.0

    if pcc is not None:
        components += 1
        if pcc >= 1.0:
            score += 5.0
        elif pcc >= 0.75:
            score += 4.0
        elif pcc >= 0.5:
            score += 3.0
        elif pcc >= 0.25:
            score += 2.0
        else:
            score += 1.0

    if srss is not None:
        components += 1
        if srss >= 80:
            score += 5.0
        elif srss >= 70:
            score += 4.0
        elif srss >= 60:
            score += 3.0
        elif srss >= 50:
            score += 2.0
        else:
            score += 1.0

    if components == 0:
        return None

    avg = score / components
    return max(1, min(5, round(avg)))


def calculate_impact_coordinates(
    overhead_pct: Optional[float],
    srss: Optional[float],
) -> tuple[Optional[float], Optional[float], Optional[str]]:
    """Calculate impact X,Y coordinates.

    X axis = financial efficiency (inverse of overhead)
    Y axis = results/impact (SRSS score normalized to 0-10)
    """
    x = None
    y = None
    label = None

    if overhead_pct is not None:
        x = round(max(0, min(10, (100 - overhead_pct) / 10)), 2)

    if srss is not None:
        y = round(max(0, min(10, srss / 10)), 2)

    if x is not None and y is not None:
        if x >= 7 and y >= 7:
            label = "High Impact, High Efficiency"
        elif x >= 7:
            label = "Low Impact, High Efficiency"
        elif y >= 7:
            label = "High Impact, Low Efficiency"
        else:
            label = "Low Impact, Low Efficiency"

    return x, y, label


@router.post("/", response_model=RatingResponse, status_code=status.HTTP_201_CREATED)
async def create_rating(
    body: RatingCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> CharityRating:
    rating = CharityRating(
        **body.model_dump(),
        analyst_id=current_user.id,
    )
    # Auto-calculate derived ratings
    rating.star_rating = calculate_star_rating(
        rating.overhead_percent, rating.program_cost_coverage, rating.srss_score
    )
    x, y, label = calculate_impact_coordinates(
        rating.overhead_percent, rating.srss_score
    )
    rating.impact_x = x
    rating.impact_y = y
    rating.impact_label = label

    db.add(rating)
    await db.commit()
    await db.refresh(rating)
    return rating


@router.get("/{rating_id}", response_model=RatingResponse)
async def get_rating(
    rating_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> CharityRating:
    rating = await db.get(CharityRating, rating_id)
    if not rating:
        raise HTTPException(status_code=404, detail="Rating not found")
    return rating


@router.put("/{rating_id}", response_model=RatingResponse)
async def update_rating(
    rating_id: str,
    body: RatingUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> CharityRating:
    rating = await db.get(CharityRating, rating_id)
    if not rating:
        raise HTTPException(status_code=404, detail="Rating not found")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(rating, key, value)
    # Recalculate if source metrics changed
    if any(k in body.model_dump(exclude_unset=True) for k in ("overhead_percent", "program_cost_coverage", "srss_score")):
        rating.star_rating = calculate_star_rating(
            rating.overhead_percent, rating.program_cost_coverage, rating.srss_score
        )
        x, y, label = calculate_impact_coordinates(
            rating.overhead_percent, rating.srss_score
        )
        rating.impact_x = x
        rating.impact_y = y
        rating.impact_label = label
    await db.commit()
    await db.refresh(rating)
    return rating


@router.get("/charity/{charity_id}", response_model=list[RatingResponse])
async def list_ratings(
    charity_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> list[CharityRating]:
    result = await db.execute(
        select(CharityRating)
        .where(CharityRating.charity_id == charity_id)
        .order_by(CharityRating.created_at.desc())
    )
    return list(result.scalars().all())

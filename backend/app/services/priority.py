"""Priority scoring engine.

Composite score from 4 components, each weighted 1-5:
  priority = (views_score * 0.3) + (staleness_score * 0.3) + (demand_score * 0.2) + (top100_bonus * 0.2)

Output is integer 1-5 (1 = highest priority).
"""
import math
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.charity import Charity
from app.models.priority import PriorityScore


def quintile_score(value: float, values: list[float]) -> float:
    """Return 1-5 score based on quintile ranking. 5 = top quintile."""
    if not values or value is None:
        return 1.0
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    rank = sum(1 for v in sorted_vals if v <= value)
    pct = rank / n
    if pct >= 0.8:
        return 5.0
    elif pct >= 0.6:
        return 4.0
    elif pct >= 0.4:
        return 3.0
    elif pct >= 0.2:
        return 2.0
    return 1.0


def staleness_score(years_since: Optional[float]) -> float:
    """Score 1-5 based on years since last evaluation. Capped at 5 years."""
    if years_since is None:
        return 5.0  # Never evaluated = highest staleness
    capped = min(years_since, 5.0)
    return max(1.0, capped)


def compute_composite(
    views: float, staleness: float, demand: float, top100: float
) -> float:
    return (views * 0.3) + (staleness * 0.3) + (demand * 0.2) + (top100 * 0.2)


def composite_to_rank(composite: float) -> int:
    """Convert composite score to priority rank 1-5 (1 = highest)."""
    if composite >= 4.0:
        return 1
    elif composite >= 3.0:
        return 2
    elif composite >= 2.0:
        return 3
    elif composite >= 1.0:
        return 4
    return 5


async def calculate_priority(
    db: AsyncSession,
    charity_id: str,
    page_views: Optional[int] = None,
    years_since_eval: Optional[float] = None,
    demand_votes: Optional[int] = None,
) -> PriorityScore:
    """Calculate and store priority score for a single charity."""
    charity = await db.get(Charity, charity_id)
    if not charity:
        raise ValueError(f"Charity {charity_id} not found")

    # For quintile ranking, we'd normally compare against all charities.
    # For single-charity calculation, use the raw values as scores.
    vs = quintile_score(float(page_views or 0), [float(page_views or 0)])
    ss = staleness_score(years_since_eval)
    ds = quintile_score(float(demand_votes or 0), [float(demand_votes or 0)])
    t100 = 5.0 if charity.is_top_100 else 0.0

    composite = compute_composite(vs, ss, ds, t100)
    rank = composite_to_rank(composite)

    # Upsert
    result = await db.execute(
        select(PriorityScore).where(PriorityScore.charity_id == charity_id)
    )
    score = result.scalar_one_or_none()
    if score is None:
        score = PriorityScore(charity_id=charity_id)
        db.add(score)

    score.views_score = vs
    score.staleness_score = ss
    score.demand_score = ds
    score.top100_bonus = t100
    score.composite_score = composite
    score.priority_rank = rank
    score.page_views = page_views
    score.years_since_eval = years_since_eval
    score.demand_votes = demand_votes

    await db.commit()
    await db.refresh(score)
    return score


async def batch_calculate_priorities(
    db: AsyncSession,
    view_data: dict[str, int],
    staleness_data: dict[str, float],
    demand_data: dict[str, int],
) -> int:
    """Recalculate priority scores for all active charities. Returns count processed."""
    result = await db.execute(
        select(Charity).where(Charity.deleted_at.is_(None))
    )
    charities = list(result.scalars().all())

    all_views = [float(view_data.get(c.id, 0)) for c in charities]
    all_demands = [float(demand_data.get(c.id, 0)) for c in charities]

    count = 0
    for charity in charities:
        views = view_data.get(charity.id, 0)
        years = staleness_data.get(charity.id)
        demand = demand_data.get(charity.id, 0)

        vs = quintile_score(float(views), all_views)
        ss = staleness_score(years)
        ds = quintile_score(float(demand), all_demands)
        t100 = 5.0 if charity.is_top_100 else 0.0

        composite = compute_composite(vs, ss, ds, t100)
        rank = composite_to_rank(composite)

        existing = await db.execute(
            select(PriorityScore).where(PriorityScore.charity_id == charity.id)
        )
        score = existing.scalar_one_or_none()
        if score is None:
            score = PriorityScore(charity_id=charity.id)
            db.add(score)

        score.views_score = vs
        score.staleness_score = ss
        score.demand_score = ds
        score.top100_bonus = t100
        score.composite_score = composite
        score.priority_rank = rank
        score.page_views = views
        score.years_since_eval = years
        score.demand_votes = demand
        count += 1

    await db.commit()
    return count

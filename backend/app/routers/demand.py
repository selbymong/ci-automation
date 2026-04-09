from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func as sa_func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.charity import Charity
from app.models.demand import CharityRequest, DemandAggregate, DispositionType
from app.models.user import User
from app.schemas.demand import (
    CharityRequestCreate,
    CharityRequestResponse,
    CharityRequestUpdate,
    DemandAggregateResponse,
    DemandAggregateUpdate,
)

router = APIRouter(prefix="/demand", tags=["demand"])


def _fuzzy_match_charity(name: str, charities: list) -> Optional[dict]:
    """Simple fuzzy match: case-insensitive substring check."""
    name_lower = name.lower()
    for c in charities:
        if name_lower in c["formal_name"].lower():
            return c
        if c.get("common_name") and name_lower in c["common_name"].lower():
            return c
    return None


@router.post("/requests", response_model=CharityRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_request(
    body: CharityRequestCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CharityRequest:
    """Public endpoint - no auth required."""
    # Fuzzy match against existing charities
    result = await db.execute(
        select(Charity).where(Charity.deleted_at.is_(None))
    )
    charities = result.scalars().all()
    charity_dicts = [{"id": c.id, "formal_name": c.formal_name, "common_name": c.common_name} for c in charities]
    match = _fuzzy_match_charity(body.requested_charity_name, charity_dicts)

    req = CharityRequest(
        requester_name=body.requester_name,
        requester_email=body.requester_email,
        requested_charity_name=body.requested_charity_name,
        status="matched" if match else "unmatched",
        matched_charity_id=match["id"] if match else None,
    )
    db.add(req)

    # Update aggregate if matched
    if match:
        agg_result = await db.execute(
            select(DemandAggregate).where(DemandAggregate.charity_id == match["id"])
        )
        agg = agg_result.scalar_one_or_none()
        if agg:
            agg.vote_count += 1
        else:
            agg = DemandAggregate(charity_id=match["id"], vote_count=1)
            db.add(agg)

    await db.commit()
    await db.refresh(req)
    return req


@router.get("/requests", response_model=list[CharityRequestResponse])
async def list_requests(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
    request_status: str = Query(None, alias="status"),
) -> list[CharityRequest]:
    query = select(CharityRequest).order_by(CharityRequest.created_at.desc())
    if request_status:
        query = query.where(CharityRequest.status == request_status)
    result = await db.execute(query)
    return list(result.scalars().all())


@router.put("/requests/{request_id}", response_model=CharityRequestResponse)
async def update_request(
    request_id: str,
    body: CharityRequestUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> CharityRequest:
    req = await db.get(CharityRequest, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if body.disposition and body.disposition not in [d.value for d in DispositionType]:
        raise HTTPException(status_code=400, detail=f"Invalid disposition: {body.disposition}")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(req, key, value)
    await db.commit()
    await db.refresh(req)
    return req


@router.get("/aggregates", response_model=list[DemandAggregateResponse])
async def list_aggregates(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> list[DemandAggregate]:
    result = await db.execute(
        select(DemandAggregate).order_by(DemandAggregate.vote_count.desc())
    )
    return list(result.scalars().all())


@router.put("/aggregates/{aggregate_id}", response_model=DemandAggregateResponse)
async def update_aggregate(
    aggregate_id: str,
    body: DemandAggregateUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> DemandAggregate:
    agg = await db.get(DemandAggregate, aggregate_id)
    if not agg:
        raise HTTPException(status_code=404, detail="Aggregate not found")
    if body.disposition and body.disposition not in [d.value for d in DispositionType]:
        raise HTTPException(status_code=400, detail=f"Invalid disposition: {body.disposition}")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(agg, key, value)
    await db.commit()
    await db.refresh(agg)
    return agg

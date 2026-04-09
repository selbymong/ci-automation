from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, require_role
from app.database import get_db
from app.models.cycle import CYCLE_TRANSITIONS, CycleStatus, EvaluationCycle
from app.models.user import User
from app.schemas.cycle import CycleCreate, CycleResponse, CycleTransition, CycleUpdate

router = APIRouter(prefix="/cycles", tags=["cycles"])


@router.post("/", response_model=CycleResponse, status_code=status.HTTP_201_CREATED)
async def create_cycle(
    body: CycleCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_role("admin"))],
) -> EvaluationCycle:
    existing = await db.execute(
        select(EvaluationCycle).where(EvaluationCycle.name == body.name)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Cycle name already exists")
    cycle = EvaluationCycle(**body.model_dump())
    db.add(cycle)
    await db.commit()
    await db.refresh(cycle)
    return cycle


@router.get("/", response_model=list[CycleResponse])
async def list_cycles(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> list[EvaluationCycle]:
    result = await db.execute(
        select(EvaluationCycle).order_by(EvaluationCycle.created_at.desc())
    )
    return list(result.scalars().all())


@router.get("/{cycle_id}", response_model=CycleResponse)
async def get_cycle(
    cycle_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> EvaluationCycle:
    cycle = await db.get(EvaluationCycle, cycle_id)
    if not cycle:
        raise HTTPException(status_code=404, detail="Cycle not found")
    return cycle


@router.put("/{cycle_id}", response_model=CycleResponse)
async def update_cycle(
    cycle_id: str,
    body: CycleUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_role("admin"))],
) -> EvaluationCycle:
    cycle = await db.get(EvaluationCycle, cycle_id)
    if not cycle:
        raise HTTPException(status_code=404, detail="Cycle not found")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(cycle, key, value)
    await db.commit()
    await db.refresh(cycle)
    return cycle


@router.post("/{cycle_id}/transition", response_model=CycleResponse)
async def transition_cycle(
    cycle_id: str,
    body: CycleTransition,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_role("admin"))],
) -> EvaluationCycle:
    cycle = await db.get(EvaluationCycle, cycle_id)
    if not cycle:
        raise HTTPException(status_code=404, detail="Cycle not found")

    try:
        new_status = CycleStatus(body.status)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status: {body.status}. Must be one of: {', '.join(s.value for s in CycleStatus)}",
        )

    current = CycleStatus(cycle.status)
    allowed = CYCLE_TRANSITIONS.get(current, [])
    if new_status not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot transition from '{current.value}' to '{new_status.value}'. Allowed: {', '.join(s.value for s in allowed) or 'none'}",
        )

    cycle.status = new_status.value
    await db.commit()
    await db.refresh(cycle)
    return cycle

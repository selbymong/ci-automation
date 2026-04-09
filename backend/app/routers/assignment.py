from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, require_role
from app.database import get_db
from app.models.assignment import EvaluationAssignment
from app.models.charity import Charity
from app.models.cycle import EvaluationCycle
from app.models.user import User
from app.schemas.assignment import (
    AssignmentBulkCreate,
    AssignmentCreate,
    AssignmentReassign,
    AssignmentResponse,
    WorkloadItem,
)

router = APIRouter(prefix="/assignments", tags=["assignments"])


@router.post("/", response_model=AssignmentResponse, status_code=status.HTTP_201_CREATED)
async def create_assignment(
    body: AssignmentCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_role("admin", "reviewer"))],
) -> EvaluationAssignment:
    # Validate references
    analyst = await db.get(User, body.analyst_id)
    if not analyst:
        raise HTTPException(status_code=404, detail="Analyst not found")
    charity = await db.get(Charity, body.charity_id)
    if not charity or charity.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Charity not found")
    cycle = await db.get(EvaluationCycle, body.cycle_id)
    if not cycle:
        raise HTTPException(status_code=404, detail="Cycle not found")

    # Check for existing assignment
    existing = await db.execute(
        select(EvaluationAssignment).where(
            EvaluationAssignment.charity_id == body.charity_id,
            EvaluationAssignment.cycle_id == body.cycle_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Charity already assigned in this cycle")

    assignment = EvaluationAssignment(
        analyst_id=body.analyst_id,
        charity_id=body.charity_id,
        cycle_id=body.cycle_id,
    )
    db.add(assignment)
    await db.commit()
    await db.refresh(assignment)
    return assignment


@router.post("/bulk", response_model=list[AssignmentResponse], status_code=status.HTTP_201_CREATED)
async def bulk_assign(
    body: AssignmentBulkCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_role("admin", "reviewer"))],
) -> list[EvaluationAssignment]:
    analyst = await db.get(User, body.analyst_id)
    if not analyst:
        raise HTTPException(status_code=404, detail="Analyst not found")
    cycle = await db.get(EvaluationCycle, body.cycle_id)
    if not cycle:
        raise HTTPException(status_code=404, detail="Cycle not found")

    created = []
    for charity_id in body.charity_ids:
        existing = await db.execute(
            select(EvaluationAssignment).where(
                EvaluationAssignment.charity_id == charity_id,
                EvaluationAssignment.cycle_id == body.cycle_id,
            )
        )
        if existing.scalar_one_or_none():
            continue
        assignment = EvaluationAssignment(
            analyst_id=body.analyst_id,
            charity_id=charity_id,
            cycle_id=body.cycle_id,
        )
        db.add(assignment)
        created.append(assignment)

    await db.commit()
    for a in created:
        await db.refresh(a)
    return created


@router.get("/cycle/{cycle_id}", response_model=list[AssignmentResponse])
async def list_assignments_by_cycle(
    cycle_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
    analyst_id: str = Query(None),
) -> list[EvaluationAssignment]:
    query = select(EvaluationAssignment).where(
        EvaluationAssignment.cycle_id == cycle_id
    )
    if analyst_id:
        query = query.where(EvaluationAssignment.analyst_id == analyst_id)
    result = await db.execute(query.order_by(EvaluationAssignment.assigned_at))
    return list(result.scalars().all())


@router.post("/{assignment_id}/reassign", response_model=AssignmentResponse)
async def reassign(
    assignment_id: str,
    body: AssignmentReassign,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_role("admin", "reviewer"))],
) -> EvaluationAssignment:
    assignment = await db.get(EvaluationAssignment, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    new_analyst = await db.get(User, body.new_analyst_id)
    if not new_analyst:
        raise HTTPException(status_code=404, detail="New analyst not found")

    assignment.reassigned_from_id = assignment.analyst_id
    assignment.reassignment_reason = body.reason
    assignment.analyst_id = body.new_analyst_id
    assignment.assigned_at = datetime.now(timezone.utc).replace(tzinfo=None)
    await db.commit()
    await db.refresh(assignment)
    return assignment


@router.get("/workload/{cycle_id}", response_model=list[WorkloadItem])
async def workload_balance(
    cycle_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> list[WorkloadItem]:
    result = await db.execute(
        select(
            EvaluationAssignment.analyst_id,
            User.full_name,
            func.count(EvaluationAssignment.id).label("cnt"),
        )
        .join(User, EvaluationAssignment.analyst_id == User.id)
        .where(EvaluationAssignment.cycle_id == cycle_id)
        .group_by(EvaluationAssignment.analyst_id, User.full_name)
        .order_by(func.count(EvaluationAssignment.id).desc())
    )
    return [
        WorkloadItem(analyst_id=r.analyst_id, analyst_name=r.full_name, assignment_count=r.cnt)
        for r in result.all()
    ]

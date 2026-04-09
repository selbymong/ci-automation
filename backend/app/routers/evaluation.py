from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.evaluation import (
    VALID_TRANSITIONS,
    Evaluation,
    EvaluationStage,
    EvaluationStageLog,
    STAGE_ORDER,
)
from app.models.user import User
from app.schemas.evaluation import (
    EvaluationCreate,
    EvaluationResponse,
    EvaluationTransition,
    KanbanColumn,
    StageLogResponse,
)

router = APIRouter(prefix="/evaluations", tags=["evaluations"])


@router.post("/", response_model=EvaluationResponse, status_code=status.HTTP_201_CREATED)
async def create_evaluation(
    body: EvaluationCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Evaluation:
    # Check for existing evaluation of same charity in same cycle
    existing = await db.execute(
        select(Evaluation).where(
            Evaluation.charity_id == body.charity_id,
            Evaluation.cycle_id == body.cycle_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Evaluation already exists for this charity in this cycle")

    evaluation = Evaluation(
        charity_id=body.charity_id,
        cycle_id=body.cycle_id,
        analyst_id=body.analyst_id,
    )
    db.add(evaluation)
    await db.commit()
    await db.refresh(evaluation)
    return evaluation


@router.get("/{evaluation_id}", response_model=EvaluationResponse)
async def get_evaluation(
    evaluation_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> Evaluation:
    evaluation = await db.get(Evaluation, evaluation_id)
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    return evaluation


@router.post("/{evaluation_id}/transition", response_model=EvaluationResponse)
async def transition_evaluation(
    evaluation_id: str,
    body: EvaluationTransition,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Evaluation:
    evaluation = await db.get(Evaluation, evaluation_id)
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    try:
        new_stage = EvaluationStage(body.to_stage)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid stage: {body.to_stage}",
        )

    current_stage = EvaluationStage(evaluation.stage)
    allowed = VALID_TRANSITIONS.get(current_stage, [])
    if new_stage not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot transition from '{current_stage.value}' to '{new_stage.value}'. Allowed: {', '.join(s.value for s in allowed) or 'none'}",
        )

    # Log the transition
    log = EvaluationStageLog(
        evaluation_id=evaluation.id,
        from_stage=current_stage.value,
        to_stage=new_stage.value,
        actor_id=current_user.id,
        note=body.note,
    )
    db.add(log)

    evaluation.stage = new_stage.value
    await db.commit()
    await db.refresh(evaluation)
    return evaluation


@router.get("/{evaluation_id}/history", response_model=list[StageLogResponse])
async def get_stage_history(
    evaluation_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> list[EvaluationStageLog]:
    result = await db.execute(
        select(EvaluationStageLog)
        .where(EvaluationStageLog.evaluation_id == evaluation_id)
        .order_by(EvaluationStageLog.transitioned_at)
    )
    return list(result.scalars().all())


@router.get("/cycle/{cycle_id}/kanban", response_model=list[KanbanColumn])
async def kanban_board(
    cycle_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> list[KanbanColumn]:
    result = await db.execute(
        select(Evaluation).where(Evaluation.cycle_id == cycle_id)
    )
    evaluations = list(result.scalars().all())

    columns = []
    for stage in STAGE_ORDER:
        stage_evals = [e for e in evaluations if e.stage == stage.value]
        columns.append(KanbanColumn(
            stage=stage.value,
            evaluations=stage_evals,
            count=len(stage_evals),
        ))
    return columns

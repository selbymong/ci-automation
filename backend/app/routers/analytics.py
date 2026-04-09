from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func as sa_func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, require_role
from app.database import get_db
from app.models.assignment import EvaluationAssignment
from app.models.evaluation import Evaluation, EvaluationStageLog
from app.models.user import User

router = APIRouter(prefix="/analytics", tags=["analytics"])


# F060: Analyst throughput dashboard

@router.get("/analyst-throughput")
async def analyst_throughput(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_role("reviewer", "admin"))],
    cycle_id: Optional[str] = Query(None),
) -> list[dict]:
    """Per-analyst metrics: assignments, stage transitions, completion counts."""
    # Get assignment counts per analyst
    assign_query = (
        select(
            EvaluationAssignment.analyst_id,
            sa_func.count(EvaluationAssignment.id).label("assignment_count"),
        )
        .group_by(EvaluationAssignment.analyst_id)
    )
    if cycle_id:
        assign_query = assign_query.where(EvaluationAssignment.cycle_id == cycle_id)
    assign_result = await db.execute(assign_query)
    assignments = {row.analyst_id: row.assignment_count for row in assign_result}

    # Get transition counts per actor (stages moved)
    trans_query = (
        select(
            EvaluationStageLog.actor_id,
            sa_func.count(EvaluationStageLog.id).label("transition_count"),
        )
        .group_by(EvaluationStageLog.actor_id)
    )
    trans_result = await db.execute(trans_query)
    transitions = {row.actor_id: row.transition_count for row in trans_result}

    # Combine
    all_analyst_ids = set(assignments.keys()) | set(transitions.keys())
    results = []
    for analyst_id in all_analyst_ids:
        results.append({
            "analyst_id": analyst_id,
            "assignment_count": assignments.get(analyst_id, 0),
            "transition_count": transitions.get(analyst_id, 0),
        })
    results.sort(key=lambda x: x["assignment_count"], reverse=True)
    return results


# F061: Cycle progress dashboard

@router.get("/cycle-progress/{cycle_id}")
async def cycle_progress(
    cycle_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> dict:
    """Cycle progress: stage distribution, completion count, total."""
    # Count evaluations per stage for this cycle
    stage_query = (
        select(
            Evaluation.stage,
            sa_func.count(Evaluation.id).label("count"),
        )
        .where(Evaluation.cycle_id == cycle_id)
        .group_by(Evaluation.stage)
    )
    result = await db.execute(stage_query)
    stage_distribution = {row.stage: row.count for row in result}

    total = sum(stage_distribution.values())
    published = stage_distribution.get("published", 0)

    return {
        "cycle_id": cycle_id,
        "total_evaluations": total,
        "completed": published,
        "stage_distribution": stage_distribution,
        "completion_percent": round(published / total * 100, 1) if total > 0 else 0,
    }


@router.get("/stage-durations/{cycle_id}")
async def stage_durations(
    cycle_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> list[dict]:
    """Average time per stage transition for a cycle."""
    # Get all evaluations for this cycle
    eval_result = await db.execute(
        select(Evaluation.id).where(Evaluation.cycle_id == cycle_id)
    )
    eval_ids = [row[0] for row in eval_result]
    if not eval_ids:
        return []

    # Get stage logs for those evaluations
    logs_result = await db.execute(
        select(EvaluationStageLog)
        .where(EvaluationStageLog.evaluation_id.in_(eval_ids))
        .order_by(EvaluationStageLog.evaluation_id, EvaluationStageLog.transitioned_at)
    )
    logs = list(logs_result.scalars().all())

    # Group by evaluation and calculate durations
    from collections import defaultdict
    durations_by_stage: dict[str, list[float]] = defaultdict(list)
    prev_log: dict[str, EvaluationStageLog] = {}

    for log in logs:
        if log.evaluation_id in prev_log:
            prev = prev_log[log.evaluation_id]
            delta = (log.transitioned_at - prev.transitioned_at).total_seconds() / 3600
            durations_by_stage[prev.to_stage].append(delta)
        prev_log[log.evaluation_id] = log

    results = []
    for stage, durations in durations_by_stage.items():
        results.append({
            "stage": stage,
            "avg_hours": round(sum(durations) / len(durations), 2) if durations else 0,
            "count": len(durations),
        })
    return results

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, require_role
from app.database import get_db
from app.models.authorization import (
    AuthorizationStatus,
    AuthorizationStep,
    EvaluationAuthorization,
)
from app.models.user import User
from app.schemas.authorization import (
    AuthorizationCreate,
    AuthorizationDecision,
    AuthorizationResponse,
)

router = APIRouter(prefix="/authorizations", tags=["authorizations"])


@router.post("/", response_model=AuthorizationResponse, status_code=status.HTTP_201_CREATED)
async def create_authorization(
    body: AuthorizationCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> EvaluationAuthorization:
    if body.step not in [s.value for s in AuthorizationStep]:
        raise HTTPException(status_code=400, detail=f"Invalid step: {body.step}")
    # Check for existing pending authorization for same evaluation + step
    existing = await db.execute(
        select(EvaluationAuthorization).where(
            EvaluationAuthorization.evaluation_id == body.evaluation_id,
            EvaluationAuthorization.step == body.step,
            EvaluationAuthorization.status == AuthorizationStatus.pending.value,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Pending authorization already exists for this step")
    auth = EvaluationAuthorization(
        evaluation_id=body.evaluation_id,
        step=body.step,
    )
    db.add(auth)
    await db.commit()
    await db.refresh(auth)
    return auth


@router.put("/{auth_id}/decide", response_model=AuthorizationResponse)
async def decide_authorization(
    auth_id: str,
    body: AuthorizationDecision,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role("reviewer", "admin"))],
) -> EvaluationAuthorization:
    auth = await db.get(EvaluationAuthorization, auth_id)
    if not auth:
        raise HTTPException(status_code=404, detail="Authorization not found")
    if auth.status != AuthorizationStatus.pending.value:
        raise HTTPException(status_code=400, detail="Authorization already decided")
    if body.status not in (AuthorizationStatus.approved.value, AuthorizationStatus.rejected.value):
        raise HTTPException(status_code=400, detail="Status must be 'approved' or 'rejected'")
    auth.status = body.status
    auth.reviewer_id = current_user.id
    auth.comment = body.comment
    auth.decided_at = datetime.now(timezone.utc).replace(tzinfo=None)
    await db.commit()
    await db.refresh(auth)
    return auth


@router.get("/evaluation/{evaluation_id}", response_model=list[AuthorizationResponse])
async def list_authorizations(
    evaluation_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> list[EvaluationAuthorization]:
    result = await db.execute(
        select(EvaluationAuthorization)
        .where(EvaluationAuthorization.evaluation_id == evaluation_id)
        .order_by(EvaluationAuthorization.created_at)
    )
    return list(result.scalars().all())


@router.get("/pending", response_model=list[AuthorizationResponse])
async def list_pending(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_role("reviewer", "admin"))],
    step: str = Query(None),
) -> list[EvaluationAuthorization]:
    query = select(EvaluationAuthorization).where(
        EvaluationAuthorization.status == AuthorizationStatus.pending.value
    ).order_by(EvaluationAuthorization.created_at)
    if step:
        query = query.where(EvaluationAuthorization.step == step)
    result = await db.execute(query)
    return list(result.scalars().all())

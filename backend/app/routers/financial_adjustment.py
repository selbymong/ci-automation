from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.financial_adjustment import AdjustmentType, FinancialAdjustment
from app.models.user import User
from app.schemas.financial_adjustment import (
    FinancialAdjustmentCreate,
    FinancialAdjustmentResponse,
    FinancialAdjustmentUpdate,
)

router = APIRouter(prefix="/financial-adjustments", tags=["financial-adjustments"])


@router.post("/", response_model=FinancialAdjustmentResponse, status_code=status.HTTP_201_CREATED)
async def create_adjustment(
    body: FinancialAdjustmentCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> FinancialAdjustment:
    if body.adjustment_type not in [t.value for t in AdjustmentType]:
        raise HTTPException(status_code=400, detail=f"Invalid adjustment type: {body.adjustment_type}")
    adj = FinancialAdjustment(
        **body.model_dump(),
        analyst_id=current_user.id,
    )
    db.add(adj)
    await db.commit()
    await db.refresh(adj)
    return adj


@router.get("/charity/{charity_id}", response_model=list[FinancialAdjustmentResponse])
async def list_adjustments(
    charity_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> list[FinancialAdjustment]:
    result = await db.execute(
        select(FinancialAdjustment)
        .where(FinancialAdjustment.charity_id == charity_id)
        .order_by(FinancialAdjustment.created_at.desc())
    )
    return list(result.scalars().all())


@router.put("/{adjustment_id}", response_model=FinancialAdjustmentResponse)
async def update_adjustment(
    adjustment_id: str,
    body: FinancialAdjustmentUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> FinancialAdjustment:
    adj = await db.get(FinancialAdjustment, adjustment_id)
    if not adj:
        raise HTTPException(status_code=404, detail="Adjustment not found")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(adj, key, value)
    await db.commit()
    await db.refresh(adj)
    return adj


@router.delete("/{adjustment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_adjustment(
    adjustment_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> None:
    adj = await db.get(FinancialAdjustment, adjustment_id)
    if not adj:
        raise HTTPException(status_code=404, detail="Adjustment not found")
    await db.delete(adj)
    await db.commit()

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.financial_analysis import FinancialAnalysis
from app.models.user import User
from app.schemas.financial_analysis import (
    FinancialAnalysisCreate,
    FinancialAnalysisResponse,
    FinancialAnalysisUpdate,
    FinancialSummary,
)

router = APIRouter(prefix="/financial-analyses", tags=["financial-analyses"])


def _calculate_derived(fa: FinancialAnalysis) -> None:
    """Auto-calculate derived metrics from raw financial data."""
    total_exp = fa.total_expenses
    if total_exp and total_exp > 0:
        fa.admin_percent = round((fa.admin_costs or 0) / total_exp * 100, 2)
        fa.fundraising_percent = round((fa.fundraising_costs or 0) / total_exp * 100, 2)
        fa.overhead_percent = round(fa.admin_percent + fa.fundraising_percent, 2)
    else:
        fa.admin_percent = None
        fa.fundraising_percent = None
        fa.overhead_percent = None

    program = fa.program_costs
    if program and program > 0 and fa.reserves is not None:
        fa.program_cost_coverage = round(fa.reserves / program, 2)
    else:
        fa.program_cost_coverage = None


@router.post("/", response_model=FinancialAnalysisResponse, status_code=status.HTTP_201_CREATED)
async def create_financial_analysis(
    body: FinancialAnalysisCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> FinancialAnalysis:
    fa = FinancialAnalysis(
        **body.model_dump(),
        analyst_id=current_user.id,
    )
    _calculate_derived(fa)
    db.add(fa)
    await db.commit()
    await db.refresh(fa)
    return fa


@router.get("/{analysis_id}", response_model=FinancialAnalysisResponse)
async def get_financial_analysis(
    analysis_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> FinancialAnalysis:
    fa = await db.get(FinancialAnalysis, analysis_id)
    if not fa:
        raise HTTPException(status_code=404, detail="Financial analysis not found")
    return fa


@router.put("/{analysis_id}", response_model=FinancialAnalysisResponse)
async def update_financial_analysis(
    analysis_id: str,
    body: FinancialAnalysisUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> FinancialAnalysis:
    fa = await db.get(FinancialAnalysis, analysis_id)
    if not fa:
        raise HTTPException(status_code=404, detail="Financial analysis not found")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(fa, key, value)
    _calculate_derived(fa)
    await db.commit()
    await db.refresh(fa)
    return fa


@router.get("/charity/{charity_id}", response_model=list[FinancialAnalysisResponse])
async def list_by_charity(
    charity_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
    cycle_id: Optional[str] = Query(None),
) -> list[FinancialAnalysis]:
    query = (
        select(FinancialAnalysis)
        .where(FinancialAnalysis.charity_id == charity_id)
        .order_by(FinancialAnalysis.year_number)
    )
    if cycle_id:
        query = query.where(FinancialAnalysis.cycle_id == cycle_id)
    result = await db.execute(query)
    return list(result.scalars().all())


@router.get("/charity/{charity_id}/summary", response_model=FinancialSummary)
async def financial_summary(
    charity_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> FinancialSummary:
    result = await db.execute(
        select(FinancialAnalysis)
        .where(FinancialAnalysis.charity_id == charity_id)
        .order_by(FinancialAnalysis.year_number)
    )
    years = list(result.scalars().all())
    return FinancialSummary(
        charity_id=charity_id,
        years=[FinancialAnalysisResponse.model_validate(y) for y in years],
    )

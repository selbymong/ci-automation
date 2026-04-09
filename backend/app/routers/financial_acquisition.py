from datetime import date, timedelta
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.financial_acquisition import AcquisitionStatus, FinancialAcquisition
from app.models.user import User
from app.schemas.financial_acquisition import (
    FinancialAcquisitionCreate,
    FinancialAcquisitionResponse,
    FinancialAcquisitionUpdate,
)

router = APIRouter(prefix="/financial-acquisitions", tags=["financial-acquisitions"])

ESCALATION_DAYS = 14


def _check_escalation(acq: FinancialAcquisition) -> Optional[str]:
    """Check if an escalation action is needed based on dates."""
    today = date.today()
    if acq.status == AcquisitionStatus.rfi_sent.value and acq.rfi_sent_at:
        if (today - acq.rfi_sent_at).days >= ESCALATION_DAYS and not acq.rfi_2_sent_at:
            return "Send 2nd RFI"
    if acq.status == AcquisitionStatus.rfi_2_sent.value and acq.rfi_2_sent_at:
        if (today - acq.rfi_2_sent_at).days >= ESCALATION_DAYS and not acq.phone_followup_at:
            return "Phone follow-up needed"
    if acq.status == AcquisitionStatus.phone_followup.value and acq.phone_followup_at:
        if (today - acq.phone_followup_at).days >= ESCALATION_DAYS and not acq.cra_request_at:
            return "Submit CRA request"
    return None


def _to_response(acq: FinancialAcquisition) -> FinancialAcquisitionResponse:
    resp = FinancialAcquisitionResponse.model_validate(acq)
    resp.escalation_needed = _check_escalation(acq)
    return resp


@router.post("/", response_model=FinancialAcquisitionResponse, status_code=status.HTTP_201_CREATED)
async def create_acquisition(
    body: FinancialAcquisitionCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> FinancialAcquisitionResponse:
    existing = await db.execute(
        select(FinancialAcquisition).where(
            FinancialAcquisition.charity_id == body.charity_id,
            FinancialAcquisition.cycle_id == body.cycle_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Acquisition tracker already exists for this charity/cycle")
    acq = FinancialAcquisition(charity_id=body.charity_id, cycle_id=body.cycle_id)
    db.add(acq)
    await db.commit()
    await db.refresh(acq)
    return _to_response(acq)


@router.get("/{acquisition_id}", response_model=FinancialAcquisitionResponse)
async def get_acquisition(
    acquisition_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> FinancialAcquisitionResponse:
    acq = await db.get(FinancialAcquisition, acquisition_id)
    if not acq:
        raise HTTPException(status_code=404, detail="Acquisition not found")
    return _to_response(acq)


@router.put("/{acquisition_id}", response_model=FinancialAcquisitionResponse)
async def update_acquisition(
    acquisition_id: str,
    body: FinancialAcquisitionUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> FinancialAcquisitionResponse:
    acq = await db.get(FinancialAcquisition, acquisition_id)
    if not acq:
        raise HTTPException(status_code=404, detail="Acquisition not found")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(acq, key, value)
    await db.commit()
    await db.refresh(acq)
    return _to_response(acq)


@router.get("/cycle/{cycle_id}", response_model=list[FinancialAcquisitionResponse])
async def list_acquisitions_by_cycle(
    cycle_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> list[FinancialAcquisitionResponse]:
    result = await db.execute(
        select(FinancialAcquisition).where(FinancialAcquisition.cycle_id == cycle_id)
    )
    return [_to_response(a) for a in result.scalars().all()]

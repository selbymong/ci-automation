from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.outreach import CharityOutreach
from app.models.user import User
from app.schemas.outreach import OutreachCreate, OutreachResponse, OutreachUpdate

router = APIRouter(prefix="/outreach", tags=["outreach"])


@router.post("/", response_model=OutreachResponse, status_code=status.HTTP_201_CREATED)
async def create_outreach(
    body: OutreachCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> CharityOutreach:
    outreach = CharityOutreach(
        evaluation_id=body.evaluation_id,
        charity_id=body.charity_id,
        analyst_id=current_user.id,
    )
    db.add(outreach)
    await db.commit()
    await db.refresh(outreach)
    return outreach


@router.get("/{outreach_id}", response_model=OutreachResponse)
async def get_outreach(
    outreach_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> CharityOutreach:
    outreach = await db.get(CharityOutreach, outreach_id)
    if not outreach:
        raise HTTPException(status_code=404, detail="Outreach not found")
    return outreach


@router.put("/{outreach_id}", response_model=OutreachResponse)
async def update_outreach(
    outreach_id: str,
    body: OutreachUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> CharityOutreach:
    outreach = await db.get(CharityOutreach, outreach_id)
    if not outreach:
        raise HTTPException(status_code=404, detail="Outreach not found")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(outreach, key, value)
    await db.commit()
    await db.refresh(outreach)
    return outreach


@router.get("/evaluation/{evaluation_id}", response_model=list[OutreachResponse])
async def list_by_evaluation(
    evaluation_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> list[CharityOutreach]:
    result = await db.execute(
        select(CharityOutreach)
        .where(CharityOutreach.evaluation_id == evaluation_id)
        .order_by(CharityOutreach.created_at.desc())
    )
    return list(result.scalars().all())

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, require_role
from app.database import get_db
from app.models.charity import Charity
from app.models.sector import Sector, SectorGroup, SubSector
from app.models.user import User
from app.schemas.sector import (
    CharitySectorAssign,
    SectorCreate,
    SectorGroupCreate,
    SectorGroupDetailResponse,
    SectorGroupResponse,
    SectorResponse,
    SubSectorCreate,
    SubSectorResponse,
)

router = APIRouter(prefix="/sectors", tags=["sectors"])


# ── Sector Groups ──

@router.post("/groups", response_model=SectorGroupResponse, status_code=status.HTTP_201_CREATED)
async def create_sector_group(
    body: SectorGroupCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_role("admin"))],
) -> SectorGroup:
    existing = await db.execute(select(SectorGroup).where(SectorGroup.name == body.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Sector group already exists")
    group = SectorGroup(name=body.name, description=body.description)
    db.add(group)
    await db.commit()
    await db.refresh(group)
    return group


@router.get("/groups", response_model=list[SectorGroupDetailResponse])
async def list_sector_groups(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> list[SectorGroup]:
    result = await db.execute(select(SectorGroup).order_by(SectorGroup.name))
    return list(result.scalars().all())


# ── Sectors ──

@router.post("/", response_model=SectorResponse, status_code=status.HTTP_201_CREATED)
async def create_sector(
    body: SectorCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_role("admin"))],
) -> Sector:
    existing = await db.execute(select(Sector).where(Sector.name == body.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Sector already exists")
    if body.group_id:
        group = await db.get(SectorGroup, body.group_id)
        if not group:
            raise HTTPException(status_code=404, detail="Sector group not found")
    sector = Sector(name=body.name, group_id=body.group_id, description=body.description)
    db.add(sector)
    await db.commit()
    await db.refresh(sector)
    return sector


@router.get("/", response_model=list[SectorResponse])
async def list_sectors(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> list[Sector]:
    result = await db.execute(select(Sector).order_by(Sector.name))
    return list(result.scalars().all())


# ── Sub-Sectors ──

@router.post("/sub-sectors", response_model=SubSectorResponse, status_code=status.HTTP_201_CREATED)
async def create_sub_sector(
    body: SubSectorCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_role("admin"))],
) -> SubSector:
    sector = await db.get(Sector, body.sector_id)
    if not sector:
        raise HTTPException(status_code=404, detail="Sector not found")
    sub = SubSector(name=body.name, sector_id=body.sector_id, description=body.description)
    db.add(sub)
    await db.commit()
    await db.refresh(sub)
    return sub


# ── Assign sector to charity ──

@router.put("/charities/{charity_id}/sector", response_model=dict)
async def assign_charity_sector(
    charity_id: str,
    body: CharitySectorAssign,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> dict:
    charity = await db.get(Charity, charity_id)
    if not charity or charity.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Charity not found")
    charity.sector = body.sector
    charity.sub_sector = body.sub_sector
    await db.commit()
    return {"charity_id": charity_id, "sector": body.sector, "sub_sector": body.sub_sector}

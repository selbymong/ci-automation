from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.traffic import TrafficSnapshot
from app.models.user import User
from app.schemas.traffic import TrafficSnapshotCreate, TrafficSnapshotResponse

router = APIRouter(prefix="/traffic", tags=["traffic"])


@router.post("/", response_model=TrafficSnapshotResponse, status_code=status.HTTP_201_CREATED)
async def create_snapshot(
    body: TrafficSnapshotCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> TrafficSnapshot:
    snapshot = TrafficSnapshot(**body.model_dump())
    db.add(snapshot)
    await db.commit()
    await db.refresh(snapshot)
    return snapshot


@router.post("/batch", response_model=list[TrafficSnapshotResponse], status_code=status.HTTP_201_CREATED)
async def create_batch(
    body: list[TrafficSnapshotCreate],
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> list[TrafficSnapshot]:
    snapshots = [TrafficSnapshot(**item.model_dump()) for item in body]
    db.add_all(snapshots)
    await db.commit()
    for s in snapshots:
        await db.refresh(s)
    return snapshots


@router.get("/charity/{charity_id}", response_model=list[TrafficSnapshotResponse])
async def list_snapshots(
    charity_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> list[TrafficSnapshot]:
    result = await db.execute(
        select(TrafficSnapshot)
        .where(TrafficSnapshot.charity_id == charity_id)
        .order_by(TrafficSnapshot.period_start.desc())
    )
    return list(result.scalars().all())

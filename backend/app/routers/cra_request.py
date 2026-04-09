from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.cra_request import CRADataRequest, CRARequestStatus
from app.models.user import User
from app.schemas.cra_request import CRABatchCreate, CRARequestCreate, CRARequestResponse, CRARequestUpdate

router = APIRouter(prefix="/cra-requests", tags=["cra-requests"])


@router.post("/", response_model=CRARequestResponse, status_code=status.HTTP_201_CREATED)
async def create_request(
    body: CRARequestCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> CRADataRequest:
    req = CRADataRequest(**body.model_dump())
    db.add(req)
    await db.commit()
    await db.refresh(req)
    return req


@router.post("/batch", response_model=list[CRARequestResponse], status_code=status.HTTP_201_CREATED)
async def create_batch(
    body: CRABatchCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> list[CRADataRequest]:
    created = []
    for charity_id in body.charity_ids:
        req = CRADataRequest(
            charity_id=charity_id,
            years_requested=body.years_requested,
            batch_id=body.batch_id,
            requested_at=body.requested_at,
        )
        db.add(req)
        created.append(req)
    await db.commit()
    for r in created:
        await db.refresh(r)
    return created


@router.get("/", response_model=list[CRARequestResponse])
async def list_requests(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
    status_filter: str = Query(None, alias="status"),
    batch_id: str = Query(None),
) -> list[CRADataRequest]:
    query = select(CRADataRequest).order_by(CRADataRequest.created_at.desc())
    if status_filter:
        query = query.where(CRADataRequest.status == status_filter)
    if batch_id:
        query = query.where(CRADataRequest.batch_id == batch_id)
    result = await db.execute(query)
    return list(result.scalars().all())


@router.put("/{request_id}", response_model=CRARequestResponse)
async def update_request(
    request_id: str,
    body: CRARequestUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> CRADataRequest:
    req = await db.get(CRADataRequest, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="CRA request not found")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(req, key, value)
    await db.commit()
    await db.refresh(req)
    return req

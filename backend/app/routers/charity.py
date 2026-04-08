from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.charity import (
    CharityCreate,
    CharityListResponse,
    CharityResponse,
    CharityUpdate,
)
from app.services import charity as charity_service

router = APIRouter(prefix="/charities", tags=["charities"])


@router.post("/", response_model=CharityResponse, status_code=status.HTTP_201_CREATED)
async def create_charity(
    body: CharityCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> CharityResponse:
    existing = await charity_service.get_charity_by_cra(db, body.cra_number)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Charity with CRA number {body.cra_number} already exists",
        )
    charity = await charity_service.create_charity(db, body)
    return charity


@router.get("/", response_model=CharityListResponse)
async def list_charities(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    search: Optional[str] = Query(None, description="Search by name or CRA number"),
    sector: Optional[str] = Query(None, description="Filter by sector"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
) -> CharityListResponse:
    items, total = await charity_service.list_charities(db, search, sector, skip, limit)
    return CharityListResponse(items=items, total=total)


@router.get("/{charity_id}", response_model=CharityResponse)
async def get_charity(
    charity_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> CharityResponse:
    charity = await charity_service.get_charity(db, charity_id)
    if charity is None:
        raise HTTPException(status_code=404, detail="Charity not found")
    return charity


@router.put("/{charity_id}", response_model=CharityResponse)
async def update_charity(
    charity_id: str,
    body: CharityUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> CharityResponse:
    charity = await charity_service.update_charity(db, charity_id, body)
    if charity is None:
        raise HTTPException(status_code=404, detail="Charity not found")
    return charity


@router.delete("/{charity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_charity(
    charity_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    deleted = await charity_service.delete_charity(db, charity_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Charity not found")

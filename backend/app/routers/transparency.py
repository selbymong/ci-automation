from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.transparency import TRANSPARENCY_FLAGS, TransparencyConfig
from app.models.user import User
from app.schemas.transparency import (
    TransparencyConfigCreate,
    TransparencyConfigResponse,
    TransparencyConfigUpdate,
)

router = APIRouter(prefix="/transparency", tags=["transparency"])


def _calculate_transparency_score(config: TransparencyConfig) -> int:
    """Derive transparency score (1-3) from flag configuration.

    Score 3 = high transparency (20+ flags true)
    Score 2 = medium transparency (10-19 flags true)
    Score 1 = low transparency (<10 flags true)
    """
    true_count = sum(1 for flag in TRANSPARENCY_FLAGS if getattr(config, flag, None) is True)
    if true_count >= 20:
        return 3
    elif true_count >= 10:
        return 2
    else:
        return 1


@router.post("/", response_model=TransparencyConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_config(
    body: TransparencyConfigCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> TransparencyConfig:
    existing = await db.execute(
        select(TransparencyConfig).where(
            TransparencyConfig.charity_id == body.charity_id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Transparency config already exists for this charity")
    config = TransparencyConfig(charity_id=body.charity_id)
    db.add(config)
    await db.flush()
    config.transparency_score = _calculate_transparency_score(config)
    await db.commit()
    await db.refresh(config)
    return config


@router.get("/charity/{charity_id}", response_model=TransparencyConfigResponse)
async def get_config(
    charity_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> TransparencyConfig:
    result = await db.execute(
        select(TransparencyConfig).where(
            TransparencyConfig.charity_id == charity_id
        )
    )
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="Transparency config not found")
    return config


@router.put("/charity/{charity_id}", response_model=TransparencyConfigResponse)
async def update_config(
    charity_id: str,
    body: TransparencyConfigUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> TransparencyConfig:
    result = await db.execute(
        select(TransparencyConfig).where(
            TransparencyConfig.charity_id == charity_id
        )
    )
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="Transparency config not found")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(config, key, value)
    config.transparency_score = _calculate_transparency_score(config)
    await db.commit()
    await db.refresh(config)
    return config

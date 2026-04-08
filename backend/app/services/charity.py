from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.charity import Charity
from app.schemas.charity import CharityCreate, CharityUpdate


async def create_charity(db: AsyncSession, data: CharityCreate) -> Charity:
    charity = Charity(**data.model_dump())
    db.add(charity)
    await db.commit()
    await db.refresh(charity)
    return charity


async def get_charity(db: AsyncSession, charity_id: str) -> Optional[Charity]:
    result = await db.execute(
        select(Charity).where(Charity.id == charity_id, Charity.deleted_at.is_(None))
    )
    return result.scalar_one_or_none()


async def get_charity_by_cra(db: AsyncSession, cra_number: str) -> Optional[Charity]:
    result = await db.execute(
        select(Charity).where(Charity.cra_number == cra_number, Charity.deleted_at.is_(None))
    )
    return result.scalar_one_or_none()


async def list_charities(
    db: AsyncSession,
    search: Optional[str] = None,
    sector: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[Charity], int]:
    query = select(Charity).where(Charity.deleted_at.is_(None))
    count_query = select(func.count()).select_from(Charity).where(Charity.deleted_at.is_(None))

    if search:
        pattern = f"%{search}%"
        search_filter = or_(
            Charity.formal_name.ilike(pattern),
            Charity.common_name.ilike(pattern),
            Charity.cra_number.ilike(pattern),
        )
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    if sector:
        query = query.where(Charity.sector == sector)
        count_query = count_query.where(Charity.sector == sector)

    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    query = query.order_by(Charity.formal_name).offset(skip).limit(limit)
    result = await db.execute(query)
    items = list(result.scalars().all())

    return items, total


async def update_charity(
    db: AsyncSession, charity_id: str, data: CharityUpdate
) -> Optional[Charity]:
    charity = await get_charity(db, charity_id)
    if charity is None:
        return None
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(charity, key, value)
    await db.commit()
    await db.refresh(charity)
    return charity


async def delete_charity(db: AsyncSession, charity_id: str) -> bool:
    charity = await get_charity(db, charity_id)
    if charity is None:
        return False
    charity.deleted_at = datetime.now(timezone.utc).replace(tzinfo=None)
    await db.commit()
    return True

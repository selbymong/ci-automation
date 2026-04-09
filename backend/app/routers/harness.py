"""F070 + F071: Harness API integration endpoints for CRA T3010 data and scraped data."""

import sys
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.integrations.harness_client import get_harness_client
from app.models.charity import Charity
from app.models.user import User

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[3]))
from shared.api_contracts.harness_cra import T3010Financial
from shared.api_contracts.harness_scrape import ScrapedCharityData

router = APIRouter(prefix="/harness", tags=["harness"])


async def _get_charity_bn(charity_id: str, db: AsyncSession) -> str:
    """Look up a charity's CRA business number by ID."""
    charity = await db.get(Charity, charity_id)
    if not charity:
        raise HTTPException(status_code=404, detail="Charity not found")
    return charity.cra_number


# --- F070: CRA T3010 data retrieval ---

@router.get("/t3010/{charity_id}", response_model=T3010Financial)
async def get_t3010_data(
    charity_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
):
    """Pull CRA T3010 financial data for a charity via Harness API."""
    bn = await _get_charity_bn(charity_id, db)
    client = get_harness_client()
    data = await client.get_t3010_data(bn)
    if data is None:
        raise HTTPException(status_code=404, detail="T3010 data not found for this charity")
    return data


@router.get("/t3010/bn/{business_number}", response_model=T3010Financial)
async def get_t3010_data_by_bn(
    business_number: str,
    _: Annotated[User, Depends(get_current_user)],
):
    """Pull CRA T3010 data directly by business number."""
    client = get_harness_client()
    data = await client.get_t3010_data(business_number)
    if data is None:
        raise HTTPException(status_code=404, detail="T3010 data not found")
    return data


# --- F071: Scraped charity website data ---

@router.get("/scrape/{charity_id}", response_model=ScrapedCharityData)
async def get_scraped_data(
    charity_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
):
    """Pull scraped charity website data via Harness API."""
    bn = await _get_charity_bn(charity_id, db)
    client = get_harness_client()
    data = await client.get_scraped_data(bn)
    if data is None:
        raise HTTPException(status_code=404, detail="Scraped data not found for this charity")
    return data


@router.get("/scrape/bn/{business_number}", response_model=ScrapedCharityData)
async def get_scraped_data_by_bn(
    business_number: str,
    _: Annotated[User, Depends(get_current_user)],
):
    """Pull scraped data directly by business number."""
    client = get_harness_client()
    data = await client.get_scraped_data(business_number)
    if data is None:
        raise HTTPException(status_code=404, detail="Scraped data not found")
    return data


@router.get("/organization/{charity_id}")
async def get_organization(
    charity_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
):
    """Pull organization record from Harness API."""
    bn = await _get_charity_bn(charity_id, db)
    client = get_harness_client()
    data = await client.get_organization(bn)
    if data is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    return data

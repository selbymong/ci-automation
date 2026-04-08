from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class CharityCreate(BaseModel):
    cra_number: str
    formal_name: str
    common_name: Optional[str] = None
    sector: Optional[str] = None
    sub_sector: Optional[str] = None
    fiscal_year_end: Optional[date] = None
    website: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    is_top_100: bool = False


class CharityUpdate(BaseModel):
    formal_name: Optional[str] = None
    common_name: Optional[str] = None
    sector: Optional[str] = None
    sub_sector: Optional[str] = None
    fiscal_year_end: Optional[date] = None
    website: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    is_top_100: Optional[bool] = None


class CharityResponse(BaseModel):
    id: str
    cra_number: str
    formal_name: str
    common_name: Optional[str] = None
    sector: Optional[str] = None
    sub_sector: Optional[str] = None
    fiscal_year_end: Optional[date] = None
    website: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    is_top_100: bool
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class CharityListResponse(BaseModel):
    items: list[CharityResponse]
    total: int

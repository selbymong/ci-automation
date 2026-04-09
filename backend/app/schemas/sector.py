from typing import Optional

from pydantic import BaseModel


class SectorGroupCreate(BaseModel):
    name: str
    description: Optional[str] = None


class SectorGroupResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None

    model_config = {"from_attributes": True}


class SectorCreate(BaseModel):
    name: str
    group_id: Optional[str] = None
    description: Optional[str] = None


class SubSectorResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None

    model_config = {"from_attributes": True}


class SectorResponse(BaseModel):
    id: str
    name: str
    group_id: Optional[str] = None
    description: Optional[str] = None
    sub_sectors: list[SubSectorResponse] = []

    model_config = {"from_attributes": True}


class SectorGroupDetailResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    sectors: list[SectorResponse] = []

    model_config = {"from_attributes": True}


class SubSectorCreate(BaseModel):
    name: str
    sector_id: str
    description: Optional[str] = None


class CharitySectorAssign(BaseModel):
    sector: str
    sub_sector: Optional[str] = None

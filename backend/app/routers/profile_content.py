from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.profile_content import ContentSectionType, ProfileContent
from app.models.user import User
from app.schemas.profile_content import (
    AssembledProfile,
    ProfileContentCreate,
    ProfileContentResponse,
    ProfileContentUpdate,
)

router = APIRouter(prefix="/profile-content", tags=["profile-content"])


@router.post("/", response_model=ProfileContentResponse, status_code=status.HTTP_201_CREATED)
async def create_content(
    body: ProfileContentCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ProfileContent:
    if body.section_type not in [t.value for t in ContentSectionType]:
        raise HTTPException(status_code=400, detail=f"Invalid section type: {body.section_type}")
    content = ProfileContent(
        charity_id=body.charity_id,
        section_type=body.section_type,
        content=body.content,
        author_id=current_user.id,
    )
    db.add(content)
    await db.commit()
    await db.refresh(content)
    return content


@router.get("/charity/{charity_id}", response_model=list[ProfileContentResponse])
async def list_content(
    charity_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> list[ProfileContent]:
    result = await db.execute(
        select(ProfileContent)
        .where(ProfileContent.charity_id == charity_id)
        .order_by(ProfileContent.section_type, ProfileContent.version.desc())
    )
    return list(result.scalars().all())


@router.put("/{content_id}", response_model=ProfileContentResponse)
async def update_content(
    content_id: str,
    body: ProfileContentUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ProfileContent:
    existing = await db.get(ProfileContent, content_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Content not found")

    # Create new version instead of overwriting
    new_version = ProfileContent(
        charity_id=existing.charity_id,
        section_type=existing.section_type,
        content=body.content,
        version=existing.version + 1,
        author_id=current_user.id,
    )
    db.add(new_version)
    await db.commit()
    await db.refresh(new_version)
    return new_version


@router.get("/charity/{charity_id}/assembled", response_model=AssembledProfile)
async def assembled_profile(
    charity_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> AssembledProfile:
    """Assemble the latest version of each section into a complete profile."""
    result = await db.execute(
        select(ProfileContent)
        .where(ProfileContent.charity_id == charity_id)
        .order_by(ProfileContent.section_type, ProfileContent.version.desc())
    )
    all_content = list(result.scalars().all())
    sections: dict[str, ProfileContentResponse] = {}
    for content in all_content:
        if content.section_type not in sections:
            sections[content.section_type] = ProfileContentResponse.model_validate(content)
    return AssembledProfile(charity_id=charity_id, sections=sections)


@router.get("/{content_id}", response_model=ProfileContentResponse)
async def get_content(
    content_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> ProfileContent:
    content = await db.get(ProfileContent, content_id)
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    return content

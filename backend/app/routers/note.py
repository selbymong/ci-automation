from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.note import EvaluationNote, NoteType
from app.models.user import User
from app.schemas.note import NoteCreate, NoteResponse, NoteUpdate

router = APIRouter(prefix="/notes", tags=["notes"])


@router.post("/", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
async def create_note(
    body: NoteCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> EvaluationNote:
    if body.note_type not in [t.value for t in NoteType]:
        raise HTTPException(status_code=400, detail=f"Invalid note type: {body.note_type}")
    note = EvaluationNote(
        charity_id=body.charity_id,
        cycle_id=body.cycle_id,
        note_type=body.note_type,
        content=body.content,
        author_id=current_user.id,
    )
    db.add(note)
    await db.commit()
    await db.refresh(note)
    return note


@router.get("/charity/{charity_id}", response_model=list[NoteResponse])
async def list_notes_for_charity(
    charity_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
    note_type: str = Query(None),
) -> list[EvaluationNote]:
    query = select(EvaluationNote).where(
        EvaluationNote.charity_id == charity_id
    ).order_by(EvaluationNote.created_at.desc())
    if note_type:
        query = query.where(EvaluationNote.note_type == note_type)
    result = await db.execute(query)
    return list(result.scalars().all())


@router.get("/search", response_model=list[NoteResponse])
async def search_notes(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
    q: str = Query(..., min_length=2),
) -> list[EvaluationNote]:
    pattern = f"%{q}%"
    result = await db.execute(
        select(EvaluationNote)
        .where(EvaluationNote.content.ilike(pattern))
        .order_by(EvaluationNote.created_at.desc())
        .limit(50)
    )
    return list(result.scalars().all())


@router.put("/{note_id}", response_model=NoteResponse)
async def update_note(
    note_id: str,
    body: NoteUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> EvaluationNote:
    note = await db.get(EvaluationNote, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    if note.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Can only edit your own notes")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(note, key, value)
    await db.commit()
    await db.refresh(note)
    return note

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_user
from app.db.session import get_session
from app.schemas.progress import ProgressRead, ProgressUpsert
from app.services.progress import get_all_progress, get_progress, upsert_progress

router = APIRouter(prefix="/me/progress", tags=["progress"])


@router.get("", response_model=list[ProgressRead])
async def list_progress(
    session: AsyncSession = Depends(get_session),
    user_id: uuid.UUID = Depends(get_current_user),
) -> list[ProgressRead]:
    entries = await get_all_progress(session, user_id)
    return [ProgressRead.model_validate(e) for e in entries]


@router.get("/{book_id}", response_model=ProgressRead | None)
async def get_book_progress(
    book_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    user_id: uuid.UUID = Depends(get_current_user),
) -> ProgressRead | None:
    entry = await get_progress(session, user_id, book_id)
    if not entry:
        return None
    return ProgressRead.model_validate(entry)


@router.put("/{book_id}", response_model=ProgressRead)
async def upsert_book_progress(
    book_id: uuid.UUID,
    body: ProgressUpsert,
    session: AsyncSession = Depends(get_session),
    user_id: uuid.UUID = Depends(get_current_user),
) -> ProgressRead:
    entry = await upsert_progress(
        session, user_id, book_id, body.current_location, body.percent_complete
    )
    return ProgressRead.model_validate(entry)

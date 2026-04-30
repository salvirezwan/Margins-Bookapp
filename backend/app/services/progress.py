import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ReadingProgress


async def get_all_progress(
    session: AsyncSession, user_id: uuid.UUID
) -> list[ReadingProgress]:
    stmt = select(ReadingProgress).where(
        ReadingProgress.user_id == user_id  # type: ignore[arg-type]
    )
    return list((await session.execute(stmt)).scalars().all())


async def get_progress(
    session: AsyncSession, user_id: uuid.UUID, book_id: uuid.UUID
) -> ReadingProgress | None:
    stmt = select(ReadingProgress).where(
        ReadingProgress.user_id == user_id,  # type: ignore[arg-type]
        ReadingProgress.book_id == book_id,  # type: ignore[arg-type]
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def upsert_progress(
    session: AsyncSession,
    user_id: uuid.UUID,
    book_id: uuid.UUID,
    current_location: str,
    percent_complete: float,
) -> ReadingProgress:
    existing = await get_progress(session, user_id, book_id)
    if existing:
        existing.current_location = current_location
        existing.percent_complete = percent_complete
        existing.last_read_at = datetime.now(UTC)
        session.add(existing)
        await session.commit()
        return existing

    progress = ReadingProgress(
        user_id=user_id,
        book_id=book_id,
        current_location=current_location,
        percent_complete=percent_complete,
        last_read_at=datetime.now(UTC),
    )
    session.add(progress)
    await session.commit()
    return progress

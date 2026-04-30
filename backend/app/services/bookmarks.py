import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Bookmark


async def get_bookmarks(
    session: AsyncSession, user_id: uuid.UUID, book_id: uuid.UUID
) -> list[Bookmark]:
    stmt = select(Bookmark).where(
        Bookmark.user_id == user_id,  # type: ignore[arg-type]
        Bookmark.book_id == book_id,  # type: ignore[arg-type]
    )
    return list((await session.execute(stmt)).scalars().all())


async def create_bookmark(
    session: AsyncSession,
    user_id: uuid.UUID,
    book_id: uuid.UUID,
    location: str,
    note: str | None,
) -> Bookmark:
    bookmark = Bookmark(
        user_id=user_id,
        book_id=book_id,
        location=location,
        note=note,
    )
    session.add(bookmark)
    await session.commit()
    return bookmark


async def delete_bookmark(
    session: AsyncSession, user_id: uuid.UUID, bookmark_id: uuid.UUID
) -> bool:
    stmt = select(Bookmark).where(
        Bookmark.id == bookmark_id,  # type: ignore[arg-type]
        Bookmark.user_id == user_id,  # type: ignore[arg-type]
    )
    bookmark = (await session.execute(stmt)).scalar_one_or_none()
    if not bookmark:
        return False
    await session.delete(bookmark)
    await session.commit()
    return True

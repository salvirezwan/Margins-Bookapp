import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Book, VisibilityEnum


async def list_books(
    session: AsyncSession,
    page: int,
    page_size: int,
    q: str | None,
    language: str | None,
) -> tuple[list[Book], int]:
    base = (
        select(Book)
        .options(selectinload(Book.subjects))  # type: ignore[arg-type]
        .where(Book.visibility == VisibilityEnum.public)  # type: ignore[arg-type]
    )

    if language:
        base = base.where(Book.language == language)  # type: ignore[arg-type]

    if q:
        term = f"%{q}%"
        base = base.where(
            or_(
                Book.title.ilike(term),  # type: ignore[attr-defined]
                Book.author.ilike(term),  # type: ignore[union-attr]
            )
        )

    count_stmt = select(func.count()).select_from(base.subquery())
    total: int = (await session.execute(count_stmt)).scalar_one()

    stmt = (
        base.order_by(Book.download_count.desc())  # type: ignore[attr-defined]
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    books = list((await session.execute(stmt)).scalars().all())

    return books, total


async def get_book(session: AsyncSession, book_id: uuid.UUID) -> Book | None:
    stmt = (
        select(Book)
        .options(selectinload(Book.subjects))  # type: ignore[arg-type]
        .where(Book.id == book_id)  # type: ignore[arg-type]
        .where(Book.visibility == VisibilityEnum.public)  # type: ignore[arg-type]
    )
    return (await session.execute(stmt)).scalar_one_or_none()

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_optional_user
from app.db.session import get_session
from app.schemas.book import BookListRead, BookListResponse, BookRead
from app.services.books import get_book, list_books

router = APIRouter(prefix="/books", tags=["books"])


@router.get("", response_model=BookListResponse)
async def list_books_endpoint(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=24, ge=1, le=100),
    q: str | None = Query(default=None),
    language: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
    _user_id: uuid.UUID | None = Depends(get_optional_user),
) -> BookListResponse:
    books, total = await list_books(session, page, page_size, q, language)
    return BookListResponse(
        items=[BookListRead.model_validate(b) for b in books],
        total=total,
        page=page,
        page_size=page_size,
        has_next=(page * page_size) < total,
    )


@router.get("/{book_id}", response_model=BookRead)
async def get_book_endpoint(
    book_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    _user_id: uuid.UUID | None = Depends(get_optional_user),
) -> BookRead:
    book = await get_book(session, book_id)
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    return BookRead(
        id=book.id,
        source=book.source,
        source_id=book.source_id,
        title=book.title,
        author=book.author,
        language=book.language,
        description=book.description,
        cover_url=book.cover_url,
        file_url=book.file_url,
        file_format=book.file_format,
        file_size_bytes=book.file_size_bytes,
        page_count=book.page_count,
        word_count=book.word_count,
        license=book.license,
        visibility=book.visibility,
        download_count=book.download_count,
        created_at=book.created_at,
        subjects=[s.subject for s in book.subjects],
    )


@router.get("/{book_id}/file")
async def get_book_file(
    book_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> RedirectResponse:
    book = await get_book(session, book_id)
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    return RedirectResponse(url=book.file_url, status_code=status.HTTP_302_FOUND)

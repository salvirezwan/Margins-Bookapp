import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_user
from app.db.session import get_session
from app.schemas.bookmark import BookmarkCreate, BookmarkRead
from app.services.bookmarks import create_bookmark, delete_bookmark, get_bookmarks

router = APIRouter(prefix="/me/bookmarks", tags=["bookmarks"])


@router.get("/{book_id}", response_model=list[BookmarkRead])
async def list_bookmarks(
    book_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    user_id: uuid.UUID = Depends(get_current_user),
) -> list[BookmarkRead]:
    items = await get_bookmarks(session, user_id, book_id)
    return [BookmarkRead.model_validate(b) for b in items]


@router.post("", response_model=BookmarkRead, status_code=status.HTTP_201_CREATED)
async def add_bookmark(
    body: BookmarkCreate,
    session: AsyncSession = Depends(get_session),
    user_id: uuid.UUID = Depends(get_current_user),
) -> BookmarkRead:
    bookmark = await create_bookmark(
        session, user_id, body.book_id, body.location, body.note
    )
    return BookmarkRead.model_validate(bookmark)


@router.delete("/{bookmark_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_bookmark(
    bookmark_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    user_id: uuid.UUID = Depends(get_current_user),
) -> None:
    deleted = await delete_bookmark(session, user_id, bookmark_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bookmark not found")

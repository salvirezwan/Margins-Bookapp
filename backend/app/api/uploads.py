"""User book upload endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_user
from app.db.session import get_session
from app.schemas.book import UserBookRead
from app.services.uploads import (
    MAX_UPLOAD_BYTES,
    create_user_book,
    delete_user_book,
    list_user_books,
)

router = APIRouter(prefix="/me/books", tags=["uploads"])


@router.get("", response_model=list[UserBookRead])
async def list_my_books(
    user_id: uuid.UUID = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[UserBookRead]:
    books = await list_user_books(session, user_id)
    return [UserBookRead.model_validate(b) for b in books]


@router.post("", response_model=UserBookRead, status_code=status.HTTP_201_CREATED)
async def upload_book(
    file: UploadFile,
    user_id: uuid.UUID = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> UserBookRead:
    content = await file.read(MAX_UPLOAD_BYTES + 1)
    try:
        book = await create_user_book(
            session=session,
            user_id=user_id,
            filename=file.filename or "upload",
            content=content,
            content_type=file.content_type or "",
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    return UserBookRead.model_validate(book)


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(
    book_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> None:
    deleted = await delete_user_book(session, user_id, book_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")

"""User book upload: metadata extraction, storage, and DB insert."""

import io
import logging
import re
import uuid
from pathlib import PurePosixPath

from ebooklib import epub
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Book, FileFormatEnum, LicenseEnum, SourceEnum, VisibilityEnum
from app.services.storage import delete_file, upload_file

logger = logging.getLogger(__name__)

MAX_UPLOAD_BYTES = 50 * 1024 * 1024  # 50 MB
ALLOWED_MIME_TYPES = {
    "application/epub+zip": FileFormatEnum.epub,
    "application/pdf": FileFormatEnum.pdf,
}
ALLOWED_EXTENSIONS = {".epub": FileFormatEnum.epub, ".pdf": FileFormatEnum.pdf}


def _storage_key(user_id: uuid.UUID, book_id: uuid.UUID, ext: str) -> str:
    return f"user_uploads/{user_id}/{book_id}{ext}"


def _extract_epub_metadata(content: bytes) -> dict[str, str | int | None]:
    """Best-effort EPUB metadata extraction. Never raises."""
    try:
        book = epub.read_epub(io.BytesIO(content))
        title = next(iter(book.get_metadata("DC", "title") or []), [None])[0]
        author_list = book.get_metadata("DC", "creator") or []
        author = ", ".join(a[0] for a in author_list if a[0]) or None
        language_meta = book.get_metadata("DC", "language") or []
        language = language_meta[0][0][:10] if language_meta else None
        description_meta = book.get_metadata("DC", "description") or []
        description = description_meta[0][0][:5000] if description_meta else None

        words = 0
        for item in book.get_items_of_type(9):  # ITEM_DOCUMENT
            raw = item.get_content()
            words += len(re.sub(rb"<[^>]+>", b" ", raw).split())

        return {
            "title": str(title)[:1000] if title else None,
            "author": author,
            "language": language,
            "description": description,
            "word_count": words or None,
        }
    except Exception as exc:
        logger.warning("Could not extract EPUB metadata: %s", exc)
        return {}


async def create_user_book(
    session: AsyncSession,
    user_id: uuid.UUID,
    filename: str,
    content: bytes,
    content_type: str,
) -> Book:
    """Validate, upload, and insert a user-uploaded book. Returns the new Book."""
    # Determine format from content-type, falling back to extension
    file_format = ALLOWED_MIME_TYPES.get(content_type)
    if file_format is None:
        ext = PurePosixPath(filename).suffix.lower()
        file_format = ALLOWED_EXTENSIONS.get(ext)
    if file_format is None:
        raise ValueError(f"Unsupported file type: {content_type or filename}")

    if len(content) > MAX_UPLOAD_BYTES:
        raise ValueError(f"File exceeds the 50 MB limit ({len(content) // (1024*1024)} MB)")

    book_id = uuid.uuid4()
    ext = ".epub" if file_format == FileFormatEnum.epub else ".pdf"
    storage_key = _storage_key(user_id, book_id, ext)
    mime = "application/epub+zip" if file_format == FileFormatEnum.epub else "application/pdf"

    file_url = await upload_file(storage_key, content, mime)

    meta: dict[str, str | int | None] = {}
    if file_format == FileFormatEnum.epub:
        meta = _extract_epub_metadata(content)

    # Fall back to filename as title if EPUB has no metadata
    title = meta.get("title") or PurePosixPath(filename).stem[:1000]

    book = Book(
        id=book_id,
        source=SourceEnum.user_private,
        source_id=None,
        title=str(title),
        author=str(meta["author"]) if meta.get("author") else None,
        language=str(meta["language"]) if meta.get("language") else None,
        description=str(meta["description"]) if meta.get("description") else None,
        cover_url=None,
        file_url=file_url,
        file_format=file_format,
        file_size_bytes=len(content),
        word_count=_wc if isinstance(_wc := meta.get("word_count"), int) else None,
        license=LicenseEnum.user_private,
        uploaded_by_user_id=user_id,
        visibility=VisibilityEnum.private,
    )
    session.add(book)
    await session.commit()
    await session.refresh(book)
    logger.info("User %s uploaded book %s: %s", user_id, book_id, title)
    return book


async def delete_user_book(
    session: AsyncSession,
    user_id: uuid.UUID,
    book_id: uuid.UUID,
) -> bool:
    """Delete a user's private book (DB row + storage). Returns False if not found/owned."""
    book = await session.get(Book, book_id)
    if book is None or book.uploaded_by_user_id != user_id:
        return False

    # Best-effort storage delete — don't fail if file is already gone
    ext = ".epub" if book.file_format == FileFormatEnum.epub else ".pdf"
    storage_key = _storage_key(user_id, book_id, ext)
    try:
        await delete_file(storage_key)
    except Exception as exc:
        logger.warning("Could not delete storage object %s: %s", storage_key, exc)

    await session.delete(book)
    await session.commit()
    return True


async def list_user_books(
    session: AsyncSession,
    user_id: uuid.UUID,
) -> list[Book]:
    """Return all private books uploaded by this user, newest first."""
    from sqlalchemy import select

    stmt = (
        select(Book)
        .where(Book.uploaded_by_user_id == user_id)  # type: ignore[arg-type]
        .where(Book.visibility == VisibilityEnum.private)  # type: ignore[arg-type]
        .order_by(Book.created_at.desc())  # type: ignore[attr-defined]
    )
    return list((await session.execute(stmt)).scalars().all())

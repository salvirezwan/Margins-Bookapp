"""
Ingest books from Project Gutenberg via the Gutendex API.

Usage:
    python -m scripts.ingest.gutendex --limit 500
    python -m scripts.ingest.gutendex --limit 10 --dry-run
"""

import argparse
import asyncio
import io
import logging
import time
from dataclasses import dataclass

import httpx
from ebooklib import epub
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings
from app.db.models import Book, BookSubject, FileFormatEnum, LicenseEnum, SourceEnum, VisibilityEnum
from app.services.storage import upload_file

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

GUTENDEX_URL = "https://gutendex.com/books"
DELAY_BETWEEN_REQUESTS = 0.25  # seconds between HTTP requests
MAX_CONCURRENCY = 4
EPUB_MIME = "application/epub+zip"
TXT_MIME = "text/plain; charset=utf-8"


@dataclass
class GutenbergBook:
    id: int
    title: str
    authors: list[str]
    languages: list[str]
    subjects: list[str]
    formats: dict[str, str]


def _pick_file_url(formats: dict[str, str]) -> tuple[str, FileFormatEnum] | None:
    """Pick the best available file format. Prefer EPUB without images."""
    # EPUB without images
    for key, url in formats.items():
        if EPUB_MIME in key and ".images" not in url:
            return url, FileFormatEnum.epub
    # EPUB with images (fallback)
    for key, url in formats.items():
        if EPUB_MIME in key:
            return url, FileFormatEnum.epub
    # Plain text fallback
    for key, url in formats.items():
        if TXT_MIME in key:
            return url, FileFormatEnum.txt
    return None


def _parse_word_count(content: bytes, file_format: FileFormatEnum) -> int | None:
    """Parse word count from file content."""
    try:
        if file_format == FileFormatEnum.epub:
            book = epub.read_epub(io.BytesIO(content))
            words = 0
            for item in book.get_items_of_type(9):  # ITEM_DOCUMENT = 9
                raw = item.get_content()
                # Strip HTML tags roughly
                import re
                text = re.sub(rb"<[^>]+>", b" ", raw)
                words += len(text.split())
            return words if words > 0 else None
        elif file_format == FileFormatEnum.txt:
            return len(content.split())
    except Exception as exc:
        logger.warning("Could not parse word count: %s", exc)
    return None


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def _fetch_page(client: httpx.AsyncClient, url: str) -> dict:  # type: ignore[type-arg]
    resp = await client.get(url, timeout=30)
    resp.raise_for_status()
    return resp.json()  # type: ignore[no-any-return]


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def _download_file(client: httpx.AsyncClient, url: str) -> bytes:
    async with client.stream("GET", url, timeout=120, follow_redirects=True) as resp:
        resp.raise_for_status()
        chunks = []
        async for chunk in resp.aiter_bytes(chunk_size=65536):
            chunks.append(chunk)
    return b"".join(chunks)


async def _already_ingested(session: AsyncSession, source_id: str) -> bool:
    result = await session.execute(
        select(Book).where(
            Book.source == SourceEnum.gutenberg,  # type: ignore[arg-type]
            Book.source_id == source_id,  # type: ignore[arg-type]
        )
    )
    return result.scalar_one_or_none() is not None


async def _ingest_book(
    book_data: GutenbergBook,
    session: AsyncSession,
    http: httpx.AsyncClient,
    sem: asyncio.Semaphore,
    dry_run: bool,
) -> bool:
    """Download, upload, and insert a single book. Returns True on success."""
    source_id = str(book_data.id)

    if await _already_ingested(session, source_id):
        logger.info("Skip %s (already ingested)", source_id)
        return False

    picked = _pick_file_url(book_data.formats)
    if picked is None:
        logger.warning("Skip %s — no usable file format", source_id)
        return False

    download_url, file_format = picked
    title = book_data.title[:1000]
    author = ", ".join(book_data.authors)[:500] if book_data.authors else None
    language = book_data.languages[0][:10] if book_data.languages else None

    async with sem:
        await asyncio.sleep(DELAY_BETWEEN_REQUESTS)
        try:
            content = await _download_file(http, download_url)
        except Exception as exc:
            logger.error("Download failed for %s: %s", source_id, exc)
            return False

    file_size = len(content)
    word_count = _parse_word_count(content, file_format)
    ext = "epub" if file_format == FileFormatEnum.epub else "txt"
    storage_key = f"gutenberg/{source_id}.{ext}"
    content_type = "application/epub+zip" if file_format == FileFormatEnum.epub else "text/plain"

    if dry_run:
        logger.info(
            "[dry-run] Would upload %s (%d bytes, ~%s words): %s",
            storage_key, file_size, word_count, title,
        )
        return True

    try:
        file_url = await upload_file(storage_key, content, content_type)
    except Exception as exc:
        logger.error("Upload failed for %s: %s", source_id, exc)
        return False

    book = Book(
        source=SourceEnum.gutenberg,
        source_id=source_id,
        title=title,
        author=author,
        language=language,
        file_url=file_url,
        file_format=file_format,
        file_size_bytes=file_size,
        word_count=word_count,
        license=LicenseEnum.public_domain,
        visibility=VisibilityEnum.public,
    )
    session.add(book)
    await session.flush()  # get book.id

    for subject in book_data.subjects[:20]:  # cap at 20 subjects per book
        session.add(BookSubject(book_id=book.id, subject=subject[:500]))

    await session.commit()
    logger.info("Ingested %s: %s", source_id, title)
    return True


async def run(limit: int, dry_run: bool) -> None:
    engine = create_async_engine(settings.database_url, echo=False)
    SessionFactory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    sem = asyncio.Semaphore(MAX_CONCURRENCY)

    ingested = 0
    skipped = 0
    failed = 0
    page_url: str | None = f"{GUTENDEX_URL}?languages=en&copyright=false&sort=popular"

    async with httpx.AsyncClient(
        headers={"User-Agent": "margins-ingest/0.1 (educational use)"},
        follow_redirects=True,
    ) as http:
        while page_url and ingested < limit:
            logger.info("Fetching page: %s", page_url)
            try:
                page = await _fetch_page(http, page_url)
            except Exception as exc:
                logger.error("Failed to fetch page: %s", exc)
                break

            results = page.get("results", [])
            page_url = page.get("next")

            tasks: list[GutenbergBook] = []
            for raw in results:
                if ingested + len(tasks) >= limit:
                    break
                book_data = GutenbergBook(
                    id=raw["id"],
                    title=raw.get("title", "Untitled"),
                    authors=[p["name"] for p in raw.get("authors", [])],
                    languages=raw.get("languages", []),
                    subjects=raw.get("subjects", []),
                    formats=raw.get("formats", {}),
                )
                tasks.append(book_data)

            async with SessionFactory() as session:
                results_list = await asyncio.gather(
                    *[
                        _ingest_book(b, session, http, sem, dry_run)
                        for b in tasks
                    ],
                    return_exceptions=True,
                )

            for r in results_list:
                if isinstance(r, Exception):
                    failed += 1
                elif r is True:
                    ingested += 1
                else:
                    skipped += 1

            if ingested % 10 == 0 and ingested > 0:
                logger.info(
                    "Progress: %d ingested, %d skipped, %d failed", ingested, skipped, failed
                )

            await asyncio.sleep(DELAY_BETWEEN_REQUESTS)

    logger.info(
        "Done. ingested=%d skipped=%d failed=%d",
        ingested, skipped, failed,
    )
    await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest books from Project Gutenberg")
    parser.add_argument("--limit", type=int, default=500, help="Max books to ingest")
    parser.add_argument("--dry-run", action="store_true", help="Skip upload and DB insert")
    args = parser.parse_args()

    start = time.monotonic()
    asyncio.run(run(args.limit, args.dry_run))
    elapsed = time.monotonic() - start
    logger.info("Total time: %.1fs", elapsed)


if __name__ == "__main__":
    main()

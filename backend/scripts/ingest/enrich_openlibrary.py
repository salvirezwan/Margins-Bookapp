"""
Enrich books with cover URLs and descriptions from Open Library.

Usage:
    python -m scripts.ingest.enrich_openlibrary
    python -m scripts.ingest.enrich_openlibrary --dry-run
    python -m scripts.ingest.enrich_openlibrary --limit 50
"""

import argparse
import asyncio
import logging
import re
import time

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings
from app.db.models import Book

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

OPENLIBRARY_SEARCH = "https://openlibrary.org/search.json"
OPENLIBRARY_COVER = "https://covers.openlibrary.org/b/olid/{olid}-L.jpg"
DELAY = 4.0  # seconds between OL requests — stay well under 1000/hr cap
BATCH_SIZE = 50

# Patterns that pollute Gutenberg titles and confuse OL search
_SUBTITLE_RE = re.compile(r"\s*[;:]\s+.*$")
_VOLUME_RE = re.compile(r",?\s+(vol\.?|volume|part|v\.)\s*\d+.*$", re.IGNORECASE)
_EDITION_RE = re.compile(r",?\s+\d+(st|nd|rd|th)\s+ed.*$", re.IGNORECASE)
_PARENS_RE = re.compile(r"\s*\(.*?\)\s*$")
_BRACKETS_RE = re.compile(r"\s*\[.*?\]\s*$")
_ILLUSTRATED_RE = re.compile(r",?\s*(illustrated|annotated|complete|abridged)$", re.IGNORECASE)


def _clean_title(title: str) -> str:
    t = title.strip()
    _patterns = (_BRACKETS_RE, _PARENS_RE, _SUBTITLE_RE, _VOLUME_RE, _EDITION_RE, _ILLUSTRATED_RE)
    for pattern in _patterns:
        t = pattern.sub("", t).strip()
    return t


def _clean_author(author: str | None) -> str | None:
    if not author:
        return None
    # Gutenberg authors are often "Lastname, Firstname" or "Lastname, Firstname, title"
    # OL prefers "Firstname Lastname" — flip if there's a comma
    parts = author.split(",", 1)
    if len(parts) == 2:
        return f"{parts[1].strip()} {parts[0].strip()}"
    return author


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=15))
async def _search_openlibrary(
    client: httpx.AsyncClient, title: str, author: str | None
) -> dict | None:  # type: ignore[type-arg]
    params: dict[str, str | int] = {"limit": 1}
    if title:
        params["title"] = title
    if author:
        params["author"] = author

    resp = await client.get(OPENLIBRARY_SEARCH, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    docs = data.get("docs", [])
    if not docs:
        return None
    return docs[0]  # type: ignore[no-any-return]


def _extract_cover_url(doc: dict) -> str | None:  # type: ignore[type-arg]
    olid = None
    # Prefer edition OLID
    edition_key = doc.get("key", "")
    if edition_key.startswith("/works/"):
        editions = doc.get("edition_key", [])
        if editions:
            olid = editions[0]
    if not olid:
        cover_edition = doc.get("cover_edition_key")
        if cover_edition:
            olid = cover_edition
    if olid:
        return OPENLIBRARY_COVER.format(olid=olid)
    return None


def _extract_description(doc: dict) -> str | None:  # type: ignore[type-arg]
    first_sentence = doc.get("first_sentence")
    if isinstance(first_sentence, list) and first_sentence:
        return str(first_sentence[0])[:5000]
    if isinstance(first_sentence, str):
        return first_sentence[:5000]
    return None


async def _enrich_book(
    book: Book,
    session_factory: async_sessionmaker,  # type: ignore[type-arg]
    client: httpx.AsyncClient,
    dry_run: bool,
) -> bool:
    """Fetch OL data and update the book. Returns True if updated."""
    doc = None
    try:
        doc = await _search_openlibrary(client, book.title, book.author)
        if not doc:
            cleaned = _clean_title(book.title)
            clean_author = _clean_author(book.author)
            if cleaned != book.title or clean_author != book.author:
                await asyncio.sleep(DELAY)
                doc = await _search_openlibrary(client, cleaned, clean_author)
    except Exception as exc:
        logger.warning("OL search failed for '%s': %s", book.title, exc)
        return False

    if not doc:
        logger.debug("No OL result for '%s'", book.title)
        return False

    cover_url = _extract_cover_url(doc)
    description = _extract_description(doc)

    updated = False
    if cover_url and not book.cover_url:
        updated = True
    if description and not book.description:
        updated = True

    if updated:
        if not dry_run:
            # Fresh session per write — avoids connection timeout on long runs
            async with session_factory() as session:
                result = await session.get(Book, book.id)
                if result:
                    if cover_url and not result.cover_url:
                        result.cover_url = cover_url
                    if description and not result.description:
                        result.description = description
                    session.add(result)
                    await session.commit()
        logger.info(
            "%s '%s' — cover=%s desc=%s",
            "[dry-run]" if dry_run else "Updated",
            book.title[:60],
            bool(cover_url),
            bool(description),
        )

    await asyncio.sleep(DELAY)
    return updated


async def run(limit: int | None, dry_run: bool) -> None:
    engine = create_async_engine(settings.database_url, echo=False)
    SessionFactory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    updated = 0
    skipped = 0
    offset = 0

    async with httpx.AsyncClient(
        headers={"User-Agent": "margins-ingest/0.1 (educational use)"},
    ) as client:
        while True:
            async with SessionFactory() as session:
                from sqlalchemy import asc, null

                stmt = (
                    select(Book)
                    .where(Book.cover_url == null())  # type: ignore[arg-type]
                    .order_by(asc("created_at"))
                    .offset(offset)
                    .limit(BATCH_SIZE)
                )
                result = await session.execute(stmt)
                books = list(result.scalars().all())

            if not books:
                break

            logger.info("Processing batch of %d books (offset=%d)", len(books), offset)

            for book in books:
                if limit is not None and updated + skipped >= limit:
                    break
                was_updated = await _enrich_book(book, SessionFactory, client, dry_run)
                if was_updated:
                    updated += 1
                else:
                    skipped += 1

            offset += BATCH_SIZE

            if limit is not None and updated + skipped >= limit:
                break

    logger.info("Done. updated=%d skipped=%d", updated, skipped)
    await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description="Enrich books with Open Library metadata")
    parser.add_argument("--limit", type=int, default=None, help="Max books to process")
    parser.add_argument("--dry-run", action="store_true", help="Skip DB writes")
    args = parser.parse_args()

    start = time.monotonic()
    asyncio.run(run(args.limit, args.dry_run))
    elapsed = time.monotonic() - start
    logger.info("Total time: %.1fs", elapsed)


if __name__ == "__main__":
    main()

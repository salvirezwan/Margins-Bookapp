import asyncio
import logging
from functools import partial
from typing import IO

from supabase import Client, create_client

from app.config import settings

logger = logging.getLogger(__name__)


def _make_client() -> Client:
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


def _upload_sync(key: str, content: bytes, content_type: str) -> None:
    _make_client().storage.from_(settings.r2_bucket_name).upload(
        path=key,
        file=content,
        file_options={"content-type": content_type, "upsert": "true"},
    )


def _upload_file_obj_sync(key: str, file_obj: "IO[bytes]", content_type: str) -> None:
    _make_client().storage.from_(settings.r2_bucket_name).upload(
        path=key,
        file=file_obj.read(),
        file_options={"content-type": content_type, "upsert": "true"},
    )


def _delete_sync(key: str) -> None:
    _make_client().storage.from_(settings.r2_bucket_name).remove([key])


async def upload_file(key: str, content: bytes, content_type: str) -> str:
    """Upload bytes to Supabase Storage and return the public URL."""
    loop = asyncio.get_running_loop()
    try:
        await loop.run_in_executor(None, partial(_upload_sync, key, content, content_type))
    except Exception as exc:
        logger.error("Storage upload failed for key=%s: %s", key, exc)
        raise
    return get_public_url(key)


async def upload_file_obj(key: str, file_obj: "IO[bytes]", content_type: str) -> str:
    """Upload a file-like object to Supabase Storage and return the public URL."""
    loop = asyncio.get_running_loop()
    try:
        await loop.run_in_executor(
            None, partial(_upload_file_obj_sync, key, file_obj, content_type)
        )
    except Exception as exc:
        logger.error("Storage upload_fileobj failed for key=%s: %s", key, exc)
        raise
    return get_public_url(key)


async def delete_file(key: str) -> None:
    """Delete an object from Supabase Storage."""
    loop = asyncio.get_running_loop()
    try:
        await loop.run_in_executor(None, partial(_delete_sync, key))
    except Exception as exc:
        logger.error("Storage delete failed for key=%s: %s", key, exc)
        raise


def get_public_url(key: str) -> str:
    """Return the public URL for a stored object."""
    base = settings.r2_public_url.rstrip("/")
    return f"{base}/{key}"

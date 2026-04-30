import uuid
from datetime import datetime

from pydantic import BaseModel

from app.db.models import FileFormatEnum, LicenseEnum, SourceEnum, VisibilityEnum


class BookSubjectRead(BaseModel):
    subject: str


class BookRead(BaseModel):
    id: uuid.UUID
    source: SourceEnum
    source_id: str | None
    title: str
    author: str | None
    language: str | None
    description: str | None
    cover_url: str | None
    file_url: str
    file_format: FileFormatEnum
    file_size_bytes: int | None
    page_count: int | None
    word_count: int | None
    license: LicenseEnum
    visibility: VisibilityEnum
    download_count: int
    created_at: datetime
    subjects: list[str]

    model_config = {"from_attributes": True}


class BookListRead(BaseModel):
    id: uuid.UUID
    title: str
    author: str | None
    language: str | None
    cover_url: str | None
    file_format: FileFormatEnum
    word_count: int | None
    license: LicenseEnum
    created_at: datetime

    model_config = {"from_attributes": True}


class BookListResponse(BaseModel):
    items: list[BookListRead]
    total: int
    page: int
    page_size: int
    has_next: bool

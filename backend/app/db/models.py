import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import Column, DateTime, Index, UniqueConstraint, func, text
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, Relationship, SQLModel


class SourceEnum(StrEnum):
    gutenberg = "gutenberg"
    open_library = "open_library"
    standard_ebooks = "standard_ebooks"
    librivox = "librivox"
    comic_book_plus = "comic_book_plus"
    doab = "doab"
    author_upload = "author_upload"
    user_private = "user_private"


class FileFormatEnum(StrEnum):
    epub = "epub"
    pdf = "pdf"
    txt = "txt"
    cbz = "cbz"


class LicenseEnum(StrEnum):
    public_domain = "public_domain"
    cc_by = "cc_by"
    cc_by_sa = "cc_by_sa"
    cc0 = "cc0"
    author_license = "author_license"
    user_private = "user_private"


class VisibilityEnum(StrEnum):
    public = "public"
    private = "private"


class Book(SQLModel, table=True):
    __tablename__ = "books"
    __table_args__ = (
        UniqueConstraint("source", "source_id", name="uq_books_source_source_id"),
        Index("ix_books_visibility_language", "visibility", "language"),
        Index("ix_books_created_at", "created_at"),
    )

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        sa_column_kwargs={"server_default": text("gen_random_uuid()")},
    )
    source: SourceEnum = Field(
        sa_column=Column(SAEnum(SourceEnum, name="sourceenum"), nullable=False)
    )
    source_id: str | None = Field(default=None, max_length=255)
    title: str = Field(max_length=1000)
    author: str | None = Field(default=None, max_length=500)
    language: str | None = Field(default=None, max_length=10)
    description: str | None = Field(default=None)
    cover_url: str | None = Field(default=None, max_length=2000)
    file_url: str = Field(max_length=2000)
    file_format: FileFormatEnum = Field(
        sa_column=Column(SAEnum(FileFormatEnum, name="fileformatenum"), nullable=False)
    )
    file_size_bytes: int | None = Field(default=None)
    page_count: int | None = Field(default=None)
    word_count: int | None = Field(default=None)
    license: LicenseEnum = Field(
        sa_column=Column(SAEnum(LicenseEnum, name="licenseenum"), nullable=False)
    )
    uploaded_by_user_id: uuid.UUID | None = Field(default=None)
    visibility: VisibilityEnum = Field(
        sa_column=Column(
            SAEnum(VisibilityEnum, name="visibilityenum"),
            nullable=False,
            server_default="public",
        )
    )
    download_count: int = Field(default=0)
    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
            server_default=func.now(),
        )
    )
    updated_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
            server_default=func.now(),
            onupdate=func.now(),
        )
    )

    subjects: list["BookSubject"] = Relationship(back_populates="book")
    progress_entries: list["ReadingProgress"] = Relationship(back_populates="book")
    bookmarks: list["Bookmark"] = Relationship(back_populates="book")


class BookSubject(SQLModel, table=True):
    __tablename__ = "book_subjects"

    book_id: uuid.UUID = Field(foreign_key="books.id", primary_key=True, ondelete="CASCADE")
    subject: str = Field(max_length=500, primary_key=True)

    book: Book = Relationship(back_populates="subjects")


class ReadingProgress(SQLModel, table=True):
    __tablename__ = "reading_progress"

    user_id: uuid.UUID = Field(primary_key=True)
    book_id: uuid.UUID = Field(foreign_key="books.id", primary_key=True, ondelete="CASCADE")
    current_location: str = Field(max_length=2000)
    percent_complete: float = Field(default=0.0)
    last_read_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
            server_default=func.now(),
        )
    )

    book: Book = Relationship(back_populates="progress_entries")


class Bookmark(SQLModel, table=True):
    __tablename__ = "bookmarks"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        sa_column_kwargs={"server_default": text("gen_random_uuid()")},
    )
    user_id: uuid.UUID = Field()
    book_id: uuid.UUID = Field(foreign_key="books.id", ondelete="CASCADE")
    location: str = Field(max_length=2000)
    note: str | None = Field(default=None)
    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
            server_default=func.now(),
        )
    )

    book: Book = Relationship(back_populates="bookmarks")

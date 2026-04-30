import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class BookmarkCreate(BaseModel):
    book_id: uuid.UUID
    location: str = Field(max_length=2000)
    note: str | None = Field(default=None)


class BookmarkRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    book_id: uuid.UUID
    location: str
    note: str | None
    created_at: datetime

    model_config = {"from_attributes": True}

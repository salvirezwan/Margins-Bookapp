import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ProgressUpsert(BaseModel):
    current_location: str = Field(max_length=2000)
    percent_complete: float = Field(ge=0.0, le=100.0)


class ProgressRead(BaseModel):
    user_id: uuid.UUID
    book_id: uuid.UUID
    current_location: str
    percent_complete: float
    last_read_at: datetime

    model_config = {"from_attributes": True}

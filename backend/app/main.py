import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.bookmarks import router as bookmarks_router
from app.api.books import router as books_router
from app.api.progress import router as progress_router
from app.auth.deps import get_current_user
from app.config import settings
from app.core.logging import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    configure_logging(settings.log_level)
    yield


app = FastAPI(
    title="margins",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(books_router)
app.include_router(progress_router)
app.include_router(bookmarks_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/me")
async def me(user_id: uuid.UUID = Depends(get_current_user)) -> dict[str, str]:
    return {"user_id": str(user_id)}

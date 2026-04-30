# margins

A web-first e-reader for public domain books. Browse a curated catalog of ~500 Project Gutenberg titles, read them in a distraction-free reader with progress tracking, bookmarks, and light/sepia/dark themes — all from your browser.

---

## Project structure

```
margins/
├── frontend/   # Next.js 15 + TypeScript
├── backend/    # FastAPI + Python 3.12
├── CLAUDE.md   # Architecture, conventions, and build plan
└── BACKLOG.md  # Parked ideas for future phases
```

---

## Setup

### Prerequisites

- [Node.js 20+](https://nodejs.org/) and [Bun](https://bun.sh/)
- [Python 3.12+](https://www.python.org/)
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- A [Supabase](https://supabase.com/) project (free tier)
- A [Cloudflare R2](https://www.cloudflare.com/developer-platform/r2/) bucket

### Frontend

```bash
cd frontend
bun install
cp .env.example .env.local   # fill in your Supabase + backend URL
bun dev                       # starts on http://localhost:3000
```

### Backend

```bash
cd backend
uv venv                        # creates .venv/
source .venv/Scripts/activate  # Windows
# source .venv/bin/activate    # Mac/Linux
uv pip install -e ".[dev]"
cp .env.example .env           # fill in Supabase, R2, and DB credentials
alembic upgrade head           # apply migrations
uvicorn app.main:app --reload --port 8000
```

### Quality gates

```bash
# Frontend
bun run lint && bun run typecheck

# Backend
ruff check . && mypy app && pytest
```

---

## Legal

All books served are public domain titles sourced from [Project Gutenberg](https://www.gutenberg.org/) via the [Gutendex API](https://gutendex.com/). Cover images are linked from [Open Library](https://openlibrary.org/) and never rehosted.

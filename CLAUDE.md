# CLAUDE.md

> Read this file at the start of every session. It defines the project, the conventions, and the phase you are currently executing. If anything below is unclear, ask before guessing.

---

## 1. Project overview

**Working name:** `margins` (rename freely)

A web-first book reader where users can:
- Browse and read a curated catalog of legally-sourced books (public domain + open-licensed)
- Track reading progress, bookmark, highlight, take notes
- Upload their own books to a private personal library
- Request books they want to see added
- (Later) Get AI-powered semantic search, summaries, and Q&A on books

The product bar is **"feels like a quality e-reader, not a webpage with a PDF stuffed inside."** Every UX decision rolls up to that.

---

## 2. Architecture

This is a **two-service monorepo**:

```
margins/
├── frontend/     # Next.js 15 + TypeScript — UI only
├── backend/      # FastAPI + Python 3.12 — all data, auth verification, ingestion
├── CLAUDE.md     # This file
└── BACKLOG.md    # Parking lot for ideas not in current phase
```

**The contract between them:**
- Frontend handles auth UI via Supabase Auth (`@supabase/ssr`). It stores the session and obtains a JWT.
- Frontend talks to backend over HTTPS, sending the JWT in the `Authorization: Bearer <token>` header.
- Backend verifies the JWT using the Supabase JWT secret, extracts `user_id`, and uses that to scope queries.
- Backend is the ONLY thing that talks to the database. The frontend never queries Postgres directly.
- Backend serves OpenAPI docs at `/docs` (FastAPI auto-generated). Frontend types are derived from the OpenAPI schema (Phase 1: manual; Phase 2+: codegen).

---

## 3. Current phase

**PHASE 1 — Walking skeleton with one ingestion source.**

The goal of Phase 1 is to prove the whole stack works end-to-end with **the smallest viable catalog**: ingest ~500 books from Project Gutenberg, enrich with Open Library covers, store in Postgres + R2, and build a reader that lets a user browse, open, and read a book with progress tracking.

We do **not** add more sources, AI, comics, audio, or author uploads until Phase 1 is solid. See section 16 for the full roadmap.

**Phase 1 is "done" when:**
- A user can sign up, browse a grid of ~500 books with real covers
- Search works (title/author full-text)
- Clicking a book opens a reader that renders EPUB content cleanly
- Reading progress auto-saves and resumes correctly across devices
- Reader has light/sepia/dark themes + adjustable font size
- The site (both services) is deployed and works on mobile

---

## 4. Legal foundation (non-negotiable)

**This project only hosts content we have the legal right to host.** This is enforced at the data layer with a `source` and `license` field on every book.

**Phase 1 sources (legal):**
- **Project Gutenberg** via Gutendex API — public domain, freely redistributable. We mirror files to our own R2 storage rather than hot-linking.
- **Open Library** — metadata + covers only. We link to `covers.openlibrary.org` directly, never rehost their covers.

**Hard rules:**
- Never ingest from Z-Library, LibGen, Anna's Archive, or any pirate source. Even one book from these poisons the project.
- Never accept a user upload as public unless the user has accepted a click-through license. User uploads default to `user_private` visibility.
- The `source` field is required on every book row. No nulls, no "unknown."
- When in doubt, ask before adding a source.

---

## 5. Tech stack

### Frontend (`frontend/`)

| Layer | Choice | Why |
|---|---|---|
| Framework | Next.js 15 (App Router) + TypeScript | SSR for fast book pages, great DX |
| Package manager | `bun` (fall back to `npm`) | Faster installs |
| Styling | Tailwind CSS + shadcn/ui | Production-quality components without fighting CSS |
| Animation | Framer Motion | Page-turn animations and route transitions |
| Reader | `epub.js` (via `react-reader` wrapper) for EPUB; `react-pdf` (PDF.js) for PDFs in later phases | Best-in-class open source readers |
| Auth (UI side) | `@supabase/ssr` | Cookie-aware session handling |
| HTTP client | Native `fetch` wrapped in a typed `apiClient` | No need for axios |
| Validation | `zod` | Validate API responses at the boundary |

### Backend (`backend/`)

| Layer | Choice | Why |
|---|---|---|
| Framework | FastAPI + Python 3.12 | Async, Pydantic-native, auto OpenAPI |
| Package manager | `uv` (fall back to `pip + venv`) | Fastest Python tool today |
| ASGI server | Uvicorn (dev), Gunicorn + Uvicorn workers (prod) | Standard |
| ORM | **SQLModel** (Pydantic + SQLAlchemy 2.0) | Same models for DB and API; less boilerplate |
| Migrations | Alembic | Standard for SQLAlchemy |
| DB driver | `asyncpg` | Async Postgres |
| Settings | `pydantic-settings` | Typed env vars |
| JWT verification | `python-jose[cryptography]` | Verifies Supabase tokens |
| HTTP client (ingestion) | `httpx` | Async, modern |
| Object storage | `boto3` (R2 is S3-compatible) | AWS standard |
| EPUB parsing | `ebooklib` | Reading metadata + word counts |
| Retries | `tenacity` | Exponential backoff for ingestion |
| Testing | `pytest`, `pytest-asyncio`, `httpx.AsyncClient` | Standard |
| Linting | `ruff` (lint + format) | Replaces black + isort + flake8 |
| Type checking | `mypy --strict` | Catch type errors before runtime |

### Shared infrastructure

| Layer | Choice | Notes |
|---|---|---|
| Database | **Supabase Postgres** (free 500MB) | Backend connects directly via connection string |
| Auth | **Supabase Auth** | Verified server-side in FastAPI via JWT |
| Object storage | Cloudflare R2 | 10GB free + free egress |
| Frontend hosting | Vercel | Free tier |
| Backend hosting | **Render** (free tier; note cold starts) or Fly.io | Render free has 15min sleep after inactivity — acceptable for Phase 1 |

**Things we are NOT using yet** (resist adding until needed):
- Redis, Celery, or any background job queue (ingestion runs as a CLI command for now)
- Microservices beyond the two we have
- A separate auth service (Clerk, Auth0) — Supabase Auth covers Phase 1 fully
- GraphQL — REST is enough

---

## 6. Project structure

### Top-level

```
margins/
├── frontend/
├── backend/
├── .gitignore
├── README.md
├── CLAUDE.md
└── BACKLOG.md
```

### Frontend (`frontend/`)

```
frontend/
├── app/                          # Next.js App Router
│   ├── (auth)/
│   │   ├── sign-in/
│   │   └── sign-up/
│   ├── (main)/
│   │   ├── library/              # Browse all books
│   │   ├── book/[id]/            # Book detail page
│   │   ├── read/[id]/            # The reader (full-screen)
│   │   └── my-books/             # User's progress, bookmarks
│   └── layout.tsx
├── components/
│   ├── ui/                       # shadcn/ui primitives
│   ├── reader/                   # Reader-specific (TOC, settings panel, etc.)
│   ├── library/                  # Browse grid, filters, search
│   └── shared/
├── lib/
│   ├── api/
│   │   ├── client.ts             # Typed fetch wrapper, attaches JWT automatically
│   │   ├── books.ts              # Endpoint functions: listBooks(), getBook(id), ...
│   │   └── progress.ts
│   ├── supabase/
│   │   ├── client.ts             # Browser client
│   │   └── server.ts             # Server client (cookie-aware)
│   └── utils.ts
├── public/
├── .env.local                    # NEVER commit
├── .env.example
├── tailwind.config.ts
├── next.config.ts
└── package.json
```

**Frontend rules:**
- Server components by default. Add `"use client"` only when state, effects, or browser APIs are needed.
- All API calls go through `lib/api/client.ts`. No raw `fetch` in components.
- Never read or write the database directly from frontend code. The backend is the single point of access.
- The Supabase service role key NEVER appears in frontend code.

### Backend (`backend/`)

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                   # FastAPI app instance, router registration
│   ├── config.py                 # pydantic-settings: env vars
│   ├── db/
│   │   ├── __init__.py
│   │   ├── session.py            # Async engine, session factory
│   │   └── models.py             # SQLModel classes (single source of truth)
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── jwt.py                # Supabase JWT verification
│   │   └── deps.py               # FastAPI dependencies: get_current_user, get_optional_user
│   ├── api/
│   │   ├── __init__.py
│   │   ├── books.py              # /books endpoints
│   │   ├── progress.py           # /progress endpoints
│   │   ├── bookmarks.py          # /bookmarks endpoints
│   │   └── search.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── book.py               # Pydantic request/response models
│   │   ├── progress.py
│   │   └── bookmark.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── books.py              # Business logic, called by api/ routes
│   │   ├── storage.py            # R2 upload/download
│   │   └── search.py
│   └── core/
│       └── logging.py
├── scripts/
│   └── ingest/
│       ├── __init__.py
│       ├── gutendex.py           # Phase 1 ingestion entry point
│       └── enrich_openlibrary.py # Cover + metadata enrichment
├── migrations/                   # Alembic
│   ├── versions/
│   ├── env.py
│   └── alembic.ini
├── tests/
│   ├── conftest.py
│   ├── test_books.py
│   └── test_auth.py
├── pyproject.toml                # uv / pip dependencies + ruff config
├── .env                          # NEVER commit
├── .env.example
└── README.md
```

**Backend rules:**
- Routes (`api/`) are thin: they parse input, call services, return schemas. No SQL or business logic.
- Services (`services/`) hold the business logic. They take a session and typed inputs.
- Models (`db/models.py`) are SQLModel classes used both as DB tables and as the source of truth for shared fields.
- Schemas (`schemas/`) are Pydantic models for API requests/responses. They reference DB models but don't expose them directly.
- All database operations go through async sessions. Never block the event loop with sync I/O.
- Logs use structured logging (JSON), not `print()`.

---

## 7. Database schema (Phase 1)

Defined in `backend/app/db/models.py` using SQLModel. Phase 1 minimum:

```
# Pseudocode-style summary; see actual models.py for real definitions

class Book:
    id: UUID                         # PK
    source: SourceEnum               # 'gutenberg', 'open_library', 'standard_ebooks',
                                     # 'librivox', 'comic_book_plus', 'doab',
                                     # 'author_upload', 'user_private'
    source_id: str | None            # ID at the source (e.g. "1342" for Gutenberg)
    title: str
    author: str | None
    language: str | None             # ISO code
    description: str | None
    cover_url: str | None            # external (covers.openlibrary.org) or our R2 URL
    file_url: str                    # our R2 URL
    file_format: FileFormatEnum      # 'epub', 'pdf', 'txt', 'cbz'
    file_size_bytes: int | None
    page_count: int | None
    word_count: int | None
    license: LicenseEnum             # 'public_domain', 'cc_by', 'cc_by_sa', 'cc0',
                                     # 'author_license', 'user_private'
    uploaded_by_user_id: UUID | None # null for ingested books
    visibility: VisibilityEnum       # 'public' | 'private'
    download_count: int = 0
    created_at: datetime
    updated_at: datetime

    # Indexes:
    # (source, source_id)            UNIQUE
    # GIN trigram index on (title, author)  for ILIKE-based search
    # (visibility, language)
    # (created_at DESC)              for "recently added"

class BookSubject:
    book_id: UUID                    # FK -> books.id, ON DELETE CASCADE
    subject: str
    # PK (book_id, subject)

class ReadingProgress:
    user_id: UUID                    # FK -> auth.users.id (Supabase managed)
    book_id: UUID                    # FK -> books.id, ON DELETE CASCADE
    current_location: str            # EPUB CFI or PDF page
    percent_complete: float
    last_read_at: datetime
    # PK (user_id, book_id)

class Bookmark:
    id: UUID                         # PK
    user_id: UUID                    # FK -> auth.users.id
    book_id: UUID                    # FK -> books.id, ON DELETE CASCADE
    location: str
    note: str | None
    created_at: datetime
```

**Security model (FastAPI + Postgres):**

Since FastAPI is the only thing talking to the database, we **enforce auth at the application layer** via FastAPI dependencies. RLS is optional defense-in-depth, not the primary mechanism.

- Every user-scoped endpoint declares `current_user: User = Depends(get_current_user)`.
- All queries that touch user data filter explicitly by `current_user.id`. No exceptions.
- Write a `tests/test_auth.py` that hits each endpoint without a token and confirms 401.

---

## 8. Environment variables

### `frontend/.env.local`

```
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
NEXT_PUBLIC_BACKEND_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

### `backend/.env`

```
# Database
DATABASE_URL=postgresql+asyncpg://...   # Supabase pooler connection string

# Supabase (for JWT verification)
SUPABASE_URL=
SUPABASE_JWT_SECRET=                    # from Supabase dashboard: Settings > API > JWT Settings

# Cloudflare R2
R2_ACCOUNT_ID=
R2_ACCESS_KEY_ID=
R2_SECRET_ACCESS_KEY=
R2_BUCKET_NAME=margins-books
R2_PUBLIC_URL=                          # CDN URL for serving files

# App
ENVIRONMENT=development                 # 'development' | 'production'
CORS_ORIGINS=http://localhost:3000      # comma-separated
LOG_LEVEL=INFO
```

**Never log or print these values.** When debugging, log the *names* of missing env vars, not their values. The `config.py` settings class should fail loudly on startup if any required var is missing.

---

## 9. Commands

### Frontend (`cd frontend/`)

```
bun install                           # Install dependencies
bun dev                               # Next.js dev server on :3000
bun run lint                          # ESLint
bun run typecheck                     # tsc --noEmit
bun run format                        # Prettier write
bun run build && bun run start        # Production build + serve
```

### Backend (`cd backend/`)

```
uv venv && source .venv/bin/activate  # Create + activate virtualenv
uv pip install -e ".[dev]"            # Install in editable mode with dev deps

uvicorn app.main:app --reload --port 8000   # Dev server

# Quality gates
ruff check .                          # Lint
ruff format .                         # Format
mypy app                              # Type check
pytest                                # Run tests

# Database
alembic revision --autogenerate -m "message"  # Generate migration
alembic upgrade head                          # Apply migrations
alembic downgrade -1                          # Rollback one

# Ingestion (Phase 1)
python -m scripts.ingest.gutendex --limit 500
python -m scripts.ingest.enrich_openlibrary
```

**The contract for "task done":**
- Frontend: `bun run lint && bun run typecheck` must pass.
- Backend: `ruff check . && mypy app && pytest` must pass.

No exceptions. If they fail, the task isn't done.

---

## 10. Conventions

### TypeScript (frontend)
- Strict mode, no `any` (use `unknown` if you must, then narrow).
- Prefer `function` declarations for top-level functions, arrow functions for callbacks.
- React: function components only.
- Co-locate component-specific helpers; promote to `lib/` only when reused.
- Server components fetch data; client components handle interaction.

### Python (backend)
- Python 3.12, async/await everywhere we touch I/O.
- Type hints on every function signature. `mypy --strict` must pass.
- Pydantic models for every request/response — never return raw dicts from routes.
- No bare `except:` clauses. Catch specific exceptions.
- Use `asynccontextmanager` for resource management (DB sessions, HTTP clients).
- Logger per module: `logger = logging.getLogger(__name__)`. No `print()` in app code.

### Naming
- Files: `kebab-case.ts(x)` for utils and components in frontend; `snake_case.py` in backend.
- React components: `PascalCase.tsx`.
- Database: `snake_case` for tables and columns.
- API routes: REST-ish. `GET /books`, `GET /books/{id}`, `POST /books/{id}/progress`, etc.
- Pydantic schemas: `BookCreate`, `BookRead`, `BookUpdate` (Tiangolo-style).

### Components
- Always use shadcn/ui primitives where one exists.
- For new shadcn components: `bunx shadcn@latest add <component>`.
- Keep components under ~200 lines. If bigger, split.

### Git workflow
- One concern per commit. Small, atomic commits over giant ones.
- Commit format: `<area>: <imperative summary>` — e.g. `reader: add sepia theme`, `backend/db: add reading_progress model`.
- Use `frontend/` or `backend/` as the area prefix when the change is service-specific.
- Never commit `.env*`, `node_modules/`, `.next/`, `__pycache__/`, `.venv/`, or any file containing real keys.
- Branch per feature: `feature/<short-name>`.

### Error handling
- Backend: routes return typed Pydantic responses. Use FastAPI's `HTTPException` for expected failures with proper status codes.
- Frontend: API client throws on non-2xx responses. Components catch and show user-friendly error UI.
- Never swallow errors silently. Log with context.
- User-facing errors are human-readable. No raw stack traces shown to users.

---

## 11. Phase 1 build plan (step by step)

Execute these in order. Each step has a clear "done" check. Don't skip ahead.

### Step 1 — Monorepo bootstrap
- [ ] Create `margins/` directory, init git
- [ ] Create `frontend/` and `backend/` subdirectories
- [ ] Add root `.gitignore` covering both Python and Node patterns
- [ ] Add `README.md` with one-paragraph project description and setup instructions
- [ ] Copy `CLAUDE.md` and create empty `BACKLOG.md`
- [ ] **Done when:** `git status` shows a clean tree and the directory structure matches section 6.

### Step 2 — Frontend bootstrap
- [ ] `cd frontend && bunx create-next-app@latest . --typescript --tailwind --app --no-src-dir`
- [ ] Install: `@supabase/ssr`, `@supabase/supabase-js`, `zod`, `lucide-react`, `framer-motion`
- [ ] `bunx shadcn@latest init` — Default style, neutral base color
- [ ] Add baseline shadcn components: `button`, `input`, `dialog`, `dropdown-menu`, `card`, `skeleton`, `sonner`
- [ ] Create `lib/api/client.ts` with a typed `apiClient` that reads `NEXT_PUBLIC_BACKEND_API_URL` and attaches the Supabase JWT to every request
- [ ] **Done when:** `bun dev` shows a placeholder home page; lint and typecheck pass.

### Step 3 — Backend bootstrap
- [ ] `cd backend && uv init` (or `python -m venv .venv` if uv isn't available)
- [ ] Define `pyproject.toml` with dependencies from section 5
- [ ] Configure ruff and mypy in `pyproject.toml`
- [ ] Create `app/main.py` with a minimal FastAPI app, `/health` endpoint, CORS middleware reading from `CORS_ORIGINS`
- [ ] Create `app/config.py` with `pydantic-settings` Settings class — fails loudly if required env vars missing
- [ ] **Done when:** `uvicorn app.main:app --reload` runs, `GET /health` returns `{"status": "ok"}`, ruff and mypy pass.

### Step 4 — Supabase + Postgres setup
- [ ] Create a Supabase project (free tier). Note the JWT secret from Settings > API.
- [ ] Configure backend `.env` with the connection string (use the **session pooler** URL for app, **direct** URL for migrations) and JWT secret.
- [ ] Create `app/db/session.py` with async engine and session factory.
- [ ] Create `app/db/models.py` with the schema from section 7 as SQLModel classes.
- [ ] Initialize Alembic: `alembic init migrations`. Configure `migrations/env.py` to read DATABASE_URL from settings and use SQLModel metadata.
- [ ] Generate first migration: `alembic revision --autogenerate -m "initial schema"`. Review the generated SQL.
- [ ] Apply: `alembic upgrade head`.
- [ ] Verify in Supabase Studio that the tables exist with the correct columns.
- [ ] **Done when:** Migration applies cleanly, all tables visible in Supabase dashboard, models import without errors.

### Step 5 — Auth flow (both services)
- [ ] **Backend:** `app/auth/jwt.py` — function that decodes a JWT using `SUPABASE_JWT_SECRET`, validates `aud=authenticated`, returns the user_id.
- [ ] **Backend:** `app/auth/deps.py` — `get_current_user` dependency that extracts the bearer token, calls the verifier, raises 401 on failure. Also `get_optional_user` for endpoints that work logged-out.
- [ ] **Backend:** Add a `GET /me` test endpoint that returns the authenticated user's id.
- [ ] **Frontend:** Sign-in and sign-up pages under `app/(auth)/`. Email/password to start.
- [ ] **Frontend:** Middleware (`middleware.ts`) that refreshes the Supabase session on every request.
- [ ] **Frontend:** API client attaches `Authorization: Bearer <access_token>` to every backend request.
- [ ] Test: sign in via the UI, hit `/me` from the frontend, verify it returns your user id.
- [ ] **Done when:** A logged-in user can hit `/me` and get their id; an unauthenticated request to a protected endpoint returns 401.

### Step 6 — R2 storage helper
- [ ] Create R2 bucket `margins-books`, configure public CDN URL, set CORS to allow GET from your frontend domain.
- [ ] Backend `app/services/storage.py`: async `upload_file(key, content, content_type)` and `get_public_url(key)` using `boto3` with the R2 endpoint.
- [ ] Test with a single dummy upload from a Python REPL before writing the ingestion script.
- [ ] **Done when:** A test file uploaded via the helper is publicly readable at the CDN URL.

### Step 7 — Gutendex ingestion script (the biggest single piece — write carefully)

`backend/scripts/ingest/gutendex.py` should:

- Hit `https://gutendex.com/books?languages=en&copyright=false&sort=popular`
- Paginate through results up to a `--limit N` flag (default 500)
- For each book:
  - Skip if `(source='gutenberg', source_id=book.id)` already exists in DB
  - Pick the best EPUB format from `book.formats` (prefer `application/epub+zip` without `.images` if both exist; fall back to `text/plain; charset=utf-8` if no EPUB)
  - Stream-download the file with `httpx` (don't load whole thing into memory)
  - Upload to R2 at key `gutenberg/{id}.epub`
  - Parse with `ebooklib` to get word_count
  - Insert row into `books` with: `source='gutenberg'`, `source_id=str(book.id)`, `license='public_domain'`, `visibility='public'`, populated metadata
  - Insert subjects into `book_subjects`
- Use `tenacity` for retry with exponential backoff on network failures
- Cap concurrency at 3-5 parallel downloads (`asyncio.Semaphore`)
- Log progress every 10 books; print summary on completion
- Has `--dry-run` flag that skips R2 upload and DB insert
- Has `--limit` flag to control how many books to ingest

**Critical:** Be a good citizen. 200ms+ delay between requests. Honor any rate-limit responses. Do not hammer Gutendex or Project Gutenberg's servers.

- [ ] Test with `--limit 10 --dry-run`
- [ ] Test with `--limit 10` (real, end-to-end)
- [ ] Run with `--limit 500` for the Phase 1 catalog
- [ ] **Done when:** 500 books are in the database with file URLs that resolve to readable EPUBs in R2.

### Step 8 — Open Library enrichment
`backend/scripts/ingest/enrich_openlibrary.py` should:

- Loop through books missing `cover_url` or with low-quality (Gutenberg default) covers
- Hit `https://openlibrary.org/search.json?title=...&author=...&limit=1`
- If found, set `cover_url = https://covers.openlibrary.org/b/olid/{olid}-L.jpg`
- Update `description` if Open Library has a richer one
- Rate limit: pace at ~1 req/4s (well under 1000/hr cap)

- [ ] Run on the full 500
- [ ] **Done when:** Most books have decent covers; browsing the library doesn't look bland.

### Step 9 — Backend API endpoints (Phase 1 minimum)

Build these endpoints in `backend/app/api/`:

- `GET /books` — list with pagination, filters (`?language=en`, `?q=search`), sort
- `GET /books/{book_id}` — single book detail
- `GET /books/{book_id}/file` — returns a redirect to R2 public URL (or proxies, depending on R2 config)
- `GET /me/progress` — current user's reading progress across all books
- `GET /me/progress/{book_id}` — single book's progress for current user
- `PUT /me/progress/{book_id}` — upsert progress
- `GET /me/bookmarks/{book_id}` — bookmarks for current user on a book
- `POST /me/bookmarks` — create bookmark
- `DELETE /me/bookmarks/{bookmark_id}` — delete bookmark

For each endpoint: route → service → DB. Routes are thin. Services hold logic.

- [ ] Write tests for each endpoint hitting both authenticated and unauthenticated paths
- [ ] **Done when:** OpenAPI docs at `/docs` show all endpoints; tests pass; can hit them with curl + a JWT.

### Step 10 — Library browse page
- [ ] `app/(main)/library/page.tsx` — server component, fetches first 24 books via `apiClient.books.list()`
- [ ] Grid layout with cover art prominent (aspect ratio ~2:3)
- [ ] Search input (client component) — debounced 300ms, refetches with `?q=...`
- [ ] "Continue reading" carousel at top if user has any progress rows
- [ ] Skeleton loaders during initial fetch
- [ ] Infinite scroll for pagination
- [ ] **Done when:** Page loads <1.5s on a cold cache, search returns results in <500ms, mobile layout is clean.

### Step 11 — Book detail page
- [ ] `app/(main)/book/[id]/page.tsx` — server component
- [ ] Large cover, title, author, description, subject tags, metadata (page count, language, source license badge)
- [ ] "Read now" button → `/read/[id]`
- [ ] If user has progress: shows percent complete + "Resume" button
- [ ] **Done when:** Looks polished enough to show someone.

### Step 12 — Reader (the make-or-break feature)

This is the single most important UI in the app. Treat it seriously. Use Opus for the architecture.

- [ ] `app/(main)/read/[id]/page.tsx` — full-screen, no chrome
- [ ] Use `epub.js` (or `react-reader` wrapper) for EPUB rendering
- [ ] Settings panel (toggleable): font size slider, theme picker (light/sepia/dark), font family (serif/sans), line height
- [ ] Auto-save progress: debounced 2s, calls `PUT /me/progress/{book_id}`
- [ ] On open: read current progress and seek to it
- [ ] Keyboard: Left/Right arrows for page turn, Esc to exit
- [ ] Mobile: swipe gestures for page turn
- [ ] Page-turn animation via Framer Motion (subtle slide, ~250ms)
- [ ] Bookmark button (saves CFI via `POST /me/bookmarks`)
- [ ] **Done when:** Reading a book feels good. If it feels janky, fix before moving on.

### Step 13 — Polish + deploy
- [ ] Loading states everywhere (skeleton loaders, never raw spinners)
- [ ] Empty states ("No books yet — explore the library" with CTA)
- [ ] Error boundaries on every route segment
- [ ] Mobile QA: every page tested on iPhone-width and iPad-width viewports
- [ ] Lighthouse audit: 90+ on Performance, Accessibility, Best Practices
- [ ] Backend deploy: Render web service pointing at `backend/`. Set all env vars. Configure health check.
- [ ] Frontend deploy: Vercel pointing at `frontend/`. Set env vars including `NEXT_PUBLIC_BACKEND_API_URL` to the Render URL.
- [ ] Update Supabase Auth redirect URLs to include the production frontend domain.
- [ ] Update backend `CORS_ORIGINS` to include the production frontend domain.
- [ ] **Done when:** A friend can use the deployed app on their phone without you explaining anything.

---

## 12. UI/UX principles

1. **Covers are the visual identity.** Browse pages should feel like walking past a bookshelf. Generous spacing, real cover art, no placeholder gradients unless the cover genuinely doesn't exist.
2. **The reader is sacred.** No ads, no upsells, no chrome. Distraction-free.
3. **Skeleton loaders, not spinners.** Always.
4. **Animations should be subtle and fast (~200-300ms).** Never block interaction.
5. **Type matters.** Ship `Fraunces`, `Source Serif`, and `Inter` as web fonts. Default body to a serif for the reading view, sans for the UI chrome.
6. **Theme tokens, not hardcoded colors.** All colors via Tailwind tokens or CSS vars.
7. **Keyboard-accessible everything.** Tab order makes sense, all interactive elements have focus states.

---

## 13. Claude Code workflow tips

- **Model selection:**
  - **Opus** for: reader architecture (Step 12), ingestion script design (Step 7), backend API design when first laying out endpoints, debugging that crosses 3+ files.
  - **Sonnet** for: writing components, queries, fixes, step-by-step execution of well-defined tasks.
- **Plan before you code on big steps.** For Steps 7 and 12, ask Claude to write a plan first, review it, then execute.
- **Read the schema before writing queries.** Always have `backend/app/db/models.py` in context when writing data access code.
- **Generate frontend types from OpenAPI** once it stabilizes. `openapi-typescript` can do this. Phase 1: optional. Phase 2+: do it.
- **Custom slash commands** to consider after setup:
  - `/component <n>` — scaffold a new client/server component pair (frontend)
  - `/endpoint <verb> <path>` — scaffold a route + service + schema trio (backend)
  - `/migration <n>` — alembic revision + manual review
- **Never commit secrets.** Before any commit, verify with `git diff --cached` that no `.env*` file is staged.
- **Run quality gates before declaring done.** Frontend: lint + typecheck. Backend: ruff + mypy + pytest.

---

## 14. Don'ts (hard guardrails)

- ❌ Don't ingest from any source not listed in section 4 without updating this file first.
- ❌ Don't access the database from frontend code. The backend is the only DB client.
- ❌ Don't use the Supabase service role key anywhere. We don't need it; backend uses the direct DB connection.
- ❌ Don't log env var values or user PII to the console.
- ❌ Don't add new dependencies without justifying them. Every dep is technical debt.
- ❌ Don't write `any` (TS) or skip type hints (Python).
- ❌ Don't fetch data in client components when a server component would do.
- ❌ Don't hardcode strings for things that should be enums.
- ❌ Don't use `localStorage` or `sessionStorage` for anything that should sync across devices — call the backend.
- ❌ Don't skip the lint/typecheck/test gates. If they fail, the task isn't done.
- ❌ Don't return raw dicts from FastAPI routes. Always use Pydantic schemas.
- ❌ Don't write sync I/O in async route handlers. Use async libraries.

---

## 15. Quick reference

- **Stuck on a decision?** Default to "the smallest thing that could possibly work, that we can replace later."
- **Tempted to add a dependency?** Try without it first.
- **Tempted to add a feature not in the current phase?** Write it down in `BACKLOG.md` and move on.
- **The reader feels janky?** Stop everything else and fix the reader.
- **Cross-service change?** Frontend change first OR backend change first — never both at once. Smaller blast radius.

---

## 16. Future phases (not Phase 1 — do not work on these yet)

Listed for context only. Each unlocks when the previous phase is shipped and stable.

- **Phase 2 — Standard Ebooks ingestion.** Manual one-time bulk import; dedupe against Gutenberg by title+author. Their typography is dramatically better.
- **Phase 3 — User uploads (private library).** Drag-drop, auto-extract metadata, generate cover thumbnail. Default `visibility='private'`.
- **Phase 4 — AI features.** pgvector for semantic search, RAG Q&A on individual books (reuse the architecture from the BD Tax RAG project), per-chapter summaries via Groq's free tier. The big differentiator. This is where Python earns its keep.
- **Phase 5 — Author opt-in portal.** Click-through licensing agreement, indie authors upload directly. The growth lever.
- **Phase 6 — LibriVox audio.** Match audiobooks to existing texts. "Read or listen" toggle.
- **Phase 7 — Comics.** Internet Archive API for the Digital Comic Museum collection. Custom CBZ/CBR viewer.
- **Phase 8 — Book requests + community features.** Upvoted request board, public collections/shelves.
- **Phase 9 — Mobile apps.** PWA-first, then React Native if needed.

---

*Last updated: Phase 1 kickoff. Update this file whenever conventions, schema, or phase changes.*

# Build Spec: Unified Media Tracker

You are building a self-hosted personal media tracker that runs as a long-lived service on a Linux server. Build it once, completely, in this session. After this build, it should require no further code changes to run indefinitely.

## Objective

A single web app where I log books, films, TV shows, games, and albums I'm reading/watching/playing/listening to. Search adds items via free external APIs. Track status, rating, dates, and notes. View a "currently consuming" dashboard and stats.

## Locked tech stack — do not deviate

- **Language:** Python 3.11+
- **Framework:** FastAPI
- **Database:** SQLite, single file at `./data/media.db`
- **DB access:** `sqlite3` stdlib with raw SQL — no ORM
- **Templates:** Jinja2
- **Frontend:** server-rendered HTML + HTMX 2.x + Tailwind CSS via CDN — no build step
- **Charts:** Chart.js via CDN
- **Server:** uvicorn
- **Packaging:** `uv` preferred, `pyproject.toml` + `requirements.txt` fallback
- **Process management:** systemd unit (with a Docker Compose alternative)

## Hard constraints

1. No frontend build step. No npm, no Vite, no bundler.
2. SQLite-only. No Postgres, Redis, or separate services.
3. All external API keys are optional — if a key is missing, that provider is disabled but the app still runs.
4. Single-user. No auth. Bind to `127.0.0.1` by default; document reverse-proxy setup.
5. Migrations are forward-only SQL files in `migrations/`, applied at startup.
6. Idempotent inserts: adding the same external item twice updates, never duplicates.

## Repository layout

```
media-tracker/
├── app/
│   ├── main.py            # FastAPI app + startup
│   ├── db.py              # connection + migration runner
│   ├── models.py          # dataclasses + serializers
│   ├── providers/
│   │   ├── base.py
│   │   ├── books.py       # OpenLibrary
│   │   ├── film_tv.py     # TMDB
│   │   ├── games.py       # RAWG
│   │   └── music.py       # MusicBrainz + Cover Art Archive
│   ├── routes/
│   │   ├── pages.py
│   │   ├── api.py
│   │   └── search.py
│   ├── templates/
│   └── static/
├── migrations/
│   └── 001_init.sql
├── scripts/
│   └── test_providers.py
├── data/                  # gitignored; holds media.db
├── deploy/
│   ├── media-tracker.service
│   └── docker-compose.yml
├── .env.example
├── pyproject.toml
└── README.md
```

---

## Phase 0 — Bootstrap

1. Initialize git, create the layout above.
2. `pyproject.toml` deps: `fastapi`, `uvicorn[standard]`, `jinja2`, `httpx`, `python-dotenv`.
3. `.env.example`:
   ```
   TMDB_API_KEY=
   RAWG_API_KEY=
   BIND_HOST=127.0.0.1
   BIND_PORT=8765
   ```
4. `.gitignore`: `data/`, `.env`, `__pycache__/`, `.venv/`.
5. **Verify:** `uv sync` (or `pip install -e .`) completes cleanly.

---

## Phase 1 — Schema & migrations

Create `migrations/001_init.sql`:

```sql
CREATE TABLE media_items (
  id TEXT PRIMARY KEY,                          -- internal uuid
  type TEXT NOT NULL CHECK (type IN ('book','film','tv','game','album')),
  title TEXT NOT NULL,
  creators TEXT NOT NULL DEFAULT '[]',          -- JSON array of strings
  release_year INTEGER,
  cover_url TEXT,
  external_ids TEXT NOT NULL DEFAULT '{}',      -- JSON {provider: id}
  metadata TEXT NOT NULL DEFAULT '{}',          -- JSON, type-specific extras
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_media_type ON media_items(type);
CREATE INDEX idx_media_title ON media_items(title);
CREATE UNIQUE INDEX idx_media_provider_extid
  ON media_items(json_extract(external_ids, '$.provider'),
                 json_extract(external_ids, '$.id'));

CREATE TABLE entries (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  media_id TEXT NOT NULL REFERENCES media_items(id) ON DELETE CASCADE,
  status TEXT NOT NULL CHECK (status IN ('backlog','in_progress','completed','abandoned','dropped')),
  rating INTEGER CHECK (rating BETWEEN 1 AND 10),
  started_at TEXT,
  finished_at TEXT,
  notes TEXT NOT NULL DEFAULT '',
  iteration INTEGER NOT NULL DEFAULT 1,         -- 1 = first time, 2 = re-watch/read
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_entries_media ON entries(media_id);
CREATE INDEX idx_entries_status ON entries(status);

CREATE TABLE tags (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE
);
CREATE TABLE entry_tags (
  entry_id INTEGER NOT NULL REFERENCES entries(id) ON DELETE CASCADE,
  tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
  PRIMARY KEY (entry_id, tag_id)
);

CREATE TABLE schema_migrations (
  filename TEXT PRIMARY KEY,
  applied_at TEXT NOT NULL DEFAULT (datetime('now'))
);
```

In `app/db.py`: a migration runner that, on startup, creates `data/media.db` if missing, then applies any `migrations/*.sql` not present in `schema_migrations`, sorted alphabetically.

**Verify:** start the app; `sqlite3 data/media.db .schema` shows all tables.

---

## Phase 2 — Provider adapters

`app/providers/base.py` defines:

```python
class Provider(Protocol):
    media_type: str
    name: str            # 'openlibrary', 'tmdb', 'rawg', 'musicbrainz'
    enabled: bool
    async def search(self, query: str, limit: int = 10) -> list[SearchResult]: ...
    async def fetch(self, external_id: str) -> MediaDetails: ...
```

`SearchResult`: `{external_id, title, creators, year, cover_url, snippet}`. Normalize across providers.

**Books — OpenLibrary** (no key):
- Search: `GET https://openlibrary.org/search.json?q={q}&limit={n}`
- `external_id` = `docs[].key` (e.g. `/works/OL...W`)
- Cover: `https://covers.openlibrary.org/b/id/{cover_i}-M.jpg`

**Film & TV — TMDB** (key required):
- Multi-search: `GET https://api.themoviedb.org/3/search/multi?query=...`
- Keep results where `media_type` ∈ {`movie`, `tv`}; map to internal types `film`/`tv`.
- Cover: `https://image.tmdb.org/t/p/w342{poster_path}`

**Games — RAWG** (key required):
- `GET https://api.rawg.io/api/games?key={k}&search={q}&page_size={n}`
- Cover: `background_image`

**Music — MusicBrainz** (no key; set `User-Agent: media-tracker/1.0 ( contact@example )`):
- `GET https://musicbrainz.org/ws/2/release-group?query={q}&fmt=json`
- Cover: `https://coverartarchive.org/release-group/{mbid}/front-250` — handle 404 gracefully.

If a provider's required env var is missing, set `enabled=False` at construction and exclude it from search dispatch — never raise.

**Verify:** `python scripts/test_providers.py` runs a fixed query against every enabled provider and prints normalized results.

---

## Phase 3 — Backend routes

**JSON API (`/api/...`):**

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/search?type={t}&q={q}` | fan out to enabled providers; merge results |
| POST | `/api/media` | body: `{provider, external_id}` → fetch + upsert media_item |
| POST | `/api/entries` | body: `{media_id, status, ...}` |
| PATCH | `/api/entries/{id}` | partial update |
| DELETE | `/api/entries/{id}` | delete |
| GET | `/api/entries?status=&type=&tag=&q=` | filtered list |
| GET | `/api/stats` | aggregates for dashboard & stats page |

`POST /api/media` must dedupe on `(provider, external_id)` — the unique index from Phase 1 enforces this.

**Server-rendered pages:**

| Path | Contents |
|---|---|
| `/` | dashboard: in-progress items, recently completed (last 30d), summary cards |
| `/library` | filter by type/status/tag/text; grid + list toggle |
| `/add` | search input; live HTMX results across all enabled providers |
| `/entries/{id}` | detail page; inline-edit notes, status, rating, dates |
| `/stats` | charts driven by `/api/stats` |

---

## Phase 4 — UI

- Base template loads Tailwind via CDN with dark mode default.
- HTMX patterns:
  - Search: `<input hx-get="/api/search" hx-trigger="input changed delay:300ms" hx-target="#results">`
  - Add from result: button `hx-post="/api/media"` → on success redirect to entry creation form.
  - Inline edit: `hx-patch="/api/entries/{id}"` with `hx-swap="outerHTML"` on the row.
- Lazy-load cover images. When `cover_url` is null, render a tinted placeholder with the title's first letter.
- Global keyboard shortcut: `/` focuses the top-bar search anywhere.

---

## Phase 5 — Stats

On `/stats`, render Chart.js charts fed by `/api/stats`:

1. Bar: completed items per month, last 24 months.
2. Doughnut: completed items by type.
3. Histogram: rating distribution.
4. Table: top creators by item count (across types).

Queries are plain SQL aggregates colocated with the endpoint in `app/routes/api.py`.

---

## Phase 6 — Deploy

`deploy/media-tracker.service`:

```
[Unit]
Description=Media Tracker
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/media-tracker
EnvironmentFile=/opt/media-tracker/.env
ExecStart=/opt/media-tracker/.venv/bin/uvicorn app.main:app --host ${BIND_HOST} --port ${BIND_PORT}
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

`deploy/docker-compose.yml`: single service, volume-mount `./data:/app/data`, env from `.env`.

`README.md` covers: install, `.env` setup, dev run (`uvicorn --reload`), systemd install, Docker run, backup (`cp data/media.db backup.db`), and a Caddy reverse-proxy snippet.

---

## Verification — run before declaring done

1. Start the server; open `/`; empty-state dashboard renders.
2. From `/add`, search "dune"; add a book result; create an entry with `status=in_progress`.
3. Repeat for a film, a game, and an album.
4. Edit an entry to `completed` with a rating; confirm it moves on the dashboard.
5. `/stats` charts populate.
6. Stop and restart the server; data persists.
7. `sqlite3 data/media.db .schema` matches Phase 1.
8. `curl localhost:8765/api/stats` returns JSON with expected keys.
9. Disable TMDB by clearing its env var; confirm app starts and search omits film/tv silently.

---

## Out of scope — do not build

- Authentication or multi-user
- Public sharing / social features
- Background scrapers or scheduled jobs
- Mobile app
- Recommendations / ML

---

## Final report

When all phases pass verification, summarize:
- Total files and rough LOC by area (backend / templates / providers / deploy).
- Which providers are configured vs disabled by missing keys.
- The exact commands to run the service (dev and systemd).
- Anything you deviated from in this spec and why.

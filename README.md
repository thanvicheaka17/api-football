# API Football

A local **API-Football proxy** built with FastAPI. It mirrors the [api-football.com v3](https://www.api-football.com/documentation-v3) endpoints, persists responses in **SQLite**, caches upstream calls in **Redis**, and keeps live and recent fixture data fresh via a background worker.

## Features

- **API-Football compatible endpoints** — same paths, parameters, and JSON response format
- **SQLite persistence** — all synced data stored in `database.db`
- **Redis caching** — reduces upstream API usage with endpoint-specific TTLs
- **Smart data freshness** — auto-refreshes stale fixtures (yesterday/today, missing scores, in-progress matches)
- **Live match support** — short-TTL cache + background worker for live scores, events, and statistics
- **Direct upstream for `/status`** — always fetches live account/quota info from the upstream API
- **Database health endpoint** — inspect record counts per endpoint
- **OpenAPI docs** — Swagger UI with query parameters matching api-football documentation
- **Docker ready** — API, Redis, and live worker via Docker Compose

## Architecture

```
Client
  │
  ▼
FastAPI (main.py)
  │
  ├── /status ──────────────────────► Upstream API (always live)
  │
  ├── Live endpoints ──► Redis (15–60s TTL) ──► Upstream API ──► SQLite
  │    fixtures?live=...
  │    fixtures/events?fixture=
  │    odds/live
  │
  └── Static endpoints ──► SQLite (read first)
       countries, leagues, standings, ...
       │
       ├── Stale? ──► Upstream API (if FETCH_ON_MISS=true)
       └── Fresh? ──► Return cached DB response

live_worker.py (every 15s)
  ├── Refresh fixtures for today + yesterday
  ├── Poll fixtures?live=all
  └── Sync events, statistics, lineups, players for live matches
```

## Project Structure

```
football-api/
├── main.py                 # FastAPI app entry point
├── sync.py                 # CLI to sync data from upstream into SQLite
├── live_worker.py          # Background worker for live + recent fixtures
├── database.db             # SQLite database (created at runtime)
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env                    # Environment variables (not committed)
│
└── app/
    ├── config.py           # Settings from environment
    ├── router.py           # API-Football route registration
    ├── endpoint_params.py  # Query parameter definitions (OpenAPI)
    ├── service.py          # Data orchestration layer
    ├── upstream.py         # HTTP client for upstream API
    ├── cache.py            # Redis cache wrapper
    ├── live.py             # Live / direct-upstream request detection
    ├── freshness.py        # Stale fixture detection logic
    │
    └── database/
        ├── connection.py   # SQLite connection manager
        ├── models.py       # Schema and dataclasses
        ├── repository.py   # Save, read, health queries
        └── utils.py        # params_hash, empty responses
```

## Quick Start

### 1. Configure environment

Create a `.env` file in the project root:

```env
API_FOOTBALL_URL=https://api.url
API_FOOTBALL_KEY=your_api_key_here

REDIS_HOST=127.0.0.1
REDIS_PORT=6379

API_PORT=8000
APP_ENV=development

FETCH_ON_MISS=true
LIVE_POLL_INTERVAL=15
LIVE_LEAGUES=all
FIXTURES_REFRESH_DAYS=2
```

### 2. Run with Docker

```bash
docker compose up --build
```

Services:

| Service       | Container           | Description                    |
|---------------|---------------------|--------------------------------|
| `api`         | api-football        | FastAPI server on port 8000    |
| `redis`       | api-football-redis  | Redis cache                    |
| `live-worker` | api-football-live   | Live + recent fixture poller   |

### 3. Run locally (without Docker)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Start Redis separately, then:
python main.py
```

## API Usage

Base URL: `http://localhost:8000`

Interactive docs: `http://localhost:8000/docs`

### Examples

```bash
# Reference data
curl "http://localhost:8000/countries"
curl "http://localhost:8000/leagues?country=England&current=true"

# Fixtures
curl "http://localhost:8000/fixtures?date=2026-06-29"
curl "http://localhost:8000/fixtures?league=39&season=2025"
curl "http://localhost:8000/fixtures?live=all"

# Match details
curl "http://localhost:8000/fixtures?id=1562344"
curl "http://localhost:8000/fixtures/events?fixture=1562344"
curl "http://localhost:8000/fixtures/statistics?fixture=1562344"
curl "http://localhost:8000/fixtures/lineups?fixture=1562344"

# Standings & players
curl "http://localhost:8000/standings?league=39&season=2025"
curl "http://localhost:8000/players/topscorers?league=39&season=2025"

# Account status (always live from upstream)
curl "http://localhost:8000/status"

# Database health
curl "http://localhost:8000/health"
```

### Available Endpoints

All endpoints from [api-football documentation v3](https://www.api-football.com/documentation-v3) are supported:

| Category   | Endpoints |
|------------|-----------|
| Reference  | `/timezone`, `/countries`, `/leagues`, `/leagues/seasons`, `/seasons` |
| Teams      | `/teams`, `/teams/statistics`, `/venues` |
| Fixtures   | `/fixtures`, `/fixtures/rounds`, `/fixtures/headtohead`, `/fixtures/events`, `/fixtures/lineups`, `/fixtures/statistics`, `/fixtures/players` |
| Standings  | `/standings` |
| Players    | `/players`, `/players/squads`, `/players/teams`, `/players/topscorers`, `/players/topassists`, `/players/topyellowcards`, `/players/topredcards` |
| Coaches    | `/coachs` |
| Other      | `/transfers`, `/trophies`, `/injuries`, `/sidelined`, `/predictions` |
| Odds       | `/odds`, `/odds/live`, `/odds/bookmakers`, `/odds/bets`, `/odds/live/bets` |
| System     | `/status`, `/health` |

## Data Flow

### Static data (countries, leagues, standings, …)

1. Read from **SQLite** first
2. If missing and `FETCH_ON_MISS=true` → fetch upstream → save to DB + Redis
3. If missing and `FETCH_ON_MISS=false` → return empty api-football response

### Fixtures (with freshness checks)

1. Read from **SQLite**
2. If data is **stale** (missing scores, old NS status, outdated today/yesterday) → re-fetch upstream
3. Otherwise return cached response

### Live data

Endpoints with `live` param or fixture sub-resources (`events`, `statistics`, …):

1. Read from **Redis** (15–60 second TTL)
2. On cache miss → fetch upstream → save to Redis + SQLite

### `/status`

Always fetched **directly from upstream** on every request (no DB/Redis read).

## Sync CLI

Populate or refresh the database manually:

```bash
# Sync one endpoint
python sync.py countries
python sync.py fixtures --param date=2026-06-29
python sync.py standings --param league=39 --param season=2025
python sync.py teams --param id=33

# Sync common reference data
python sync.py --reference
```

With Docker:

```bash
docker exec api-football python sync.py --reference
docker exec api-football python sync.py fixtures --param date=2026-06-29
```

## Environment Variables

| Variable               | Default                              | Description |
|------------------------|--------------------------------------|-------------|
| `API_FOOTBALL_URL`     | `https://v3.football.api-sports.io`  | Upstream API base URL |
| `API_FOOTBALL_KEY`     | —                                    | Upstream API key (`x-apisports-key` header) |
| `REDIS_HOST`           | `127.0.0.1`                          | Redis host |
| `REDIS_PORT`           | `6379`                               | Redis port |
| `REDIS_DB`             | `0`                                  | Redis database number |
| `DATABASE_PATH`        | `database.db`                        | SQLite file path |
| `API_PORT`             | `8000`                               | Exposed API port (Docker) |
| `APP_ENV`              | `production`                         | Set to `development` for hot reload |
| `FETCH_ON_MISS`        | `false`                              | Fetch upstream when DB has no data or stale fixtures |
| `CACHE_TTL_DEFAULT`    | `300`                                | Default Redis TTL (seconds) |
| `LIVE_POLL_INTERVAL`   | `15`                                 | Live worker poll interval (seconds) |
| `LIVE_LEAGUES`         | `all`                                | Leagues for live polling (`all` or `39-140`) |
| `FIXTURES_REFRESH_DAYS`| `2`                                  | Days back to refresh (today + yesterday = 2) |

## Health Check

```bash
curl http://localhost:8000/health
```

Example response:

```json
{
  "status": "ok",
  "total_records": 256,
  "total_results": 10906,
  "oldest_record_at": "2026-06-29T10:25:43+00:00",
  "latest_record_at": "2026-06-30T02:26:52+00:00",
  "endpoints": [
    { "endpoint": "fixtures", "count": 67 },
    { "endpoint": "fixtures/events", "count": 52 }
  ]
}
```

## Tech Stack

- **Python 3.12**
- **FastAPI** + **Uvicorn**
- **SQLite** — persistent storage
- **Redis** — response caching
- **httpx** — async upstream HTTP client
- **Docker Compose** — API + Redis + live worker

## License

Private project.

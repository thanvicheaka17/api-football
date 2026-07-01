from dataclasses import dataclass
from datetime import datetime

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS api_responses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    endpoint TEXT NOT NULL,
    params TEXT NOT NULL,
    params_hash TEXT NOT NULL,
    response TEXT NOT NULL,
    results INTEGER,
    errors TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(endpoint, params_hash)
);

CREATE INDEX IF NOT EXISTS idx_api_responses_endpoint
    ON api_responses(endpoint);
CREATE INDEX IF NOT EXISTS idx_api_responses_updated
    ON api_responses(updated_at);

CREATE TABLE IF NOT EXISTS cleanup_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_at TEXT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    deleted_count INTEGER NOT NULL
);
"""


@dataclass
class ApiResponseRecord:
    endpoint: str
    params: str
    params_hash: str
    response: str
    results: int | None
    errors: str
    created_at: str
    updated_at: str


@dataclass
class StoredResponse:
    payload: dict
    updated_at: datetime

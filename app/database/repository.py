import json
from datetime import datetime
from typing import Any

from app.config import Settings, get_settings
from app.database.connection import DatabaseConnection
from app.database.models import SCHEMA_SQL, StoredResponse
from app.database.utils import build_empty_response, params_hash, utc_now


class ApiResponseRepository:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._connection = DatabaseConnection(self.settings)

    @property
    def connect(self):
        return self._connection.connect

    def init(self) -> None:
        with self.connect() as conn:
            conn.executescript(SCHEMA_SQL)

    def save_response(
        self,
        endpoint: str,
        params: dict[str, Any],
        payload: dict[str, Any],
    ) -> None:
        now = utc_now()
        serialized_params = json.dumps(params, sort_keys=True)
        serialized_response = json.dumps(payload, separators=(",", ":"))
        key = params_hash(params)
        errors = json.dumps(payload.get("errors", []))
        results = payload.get("results")

        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO api_responses (
                    endpoint, params, params_hash, response, results, errors,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(endpoint, params_hash) DO UPDATE SET
                    params = excluded.params,
                    response = excluded.response,
                    results = excluded.results,
                    errors = excluded.errors,
                    updated_at = excluded.updated_at
                """,
                (
                    endpoint,
                    serialized_params,
                    key,
                    serialized_response,
                    results,
                    errors,
                    now,
                    now,
                ),
            )

    def get_response(self, endpoint: str, params: dict[str, Any]) -> dict[str, Any] | None:
        stored = self.get_stored_response(endpoint, params)
        if stored is None:
            return None
        return stored.payload

    def get_stored_response(
        self,
        endpoint: str,
        params: dict[str, Any],
    ) -> StoredResponse | None:
        key = params_hash(params)
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT response, updated_at FROM api_responses
                WHERE endpoint = ? AND params_hash = ?
                """,
                (endpoint, key),
            ).fetchone()

        if not row:
            return None

        return StoredResponse(
            payload=json.loads(row["response"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def empty_response(
        self,
        endpoint: str,
        params: dict[str, Any],
        message: str = "No data found in database",
    ) -> dict[str, Any]:
        return build_empty_response(endpoint, params, message)

    def health(self) -> dict[str, Any]:
        with self.connect() as conn:
            total = conn.execute("SELECT COUNT(*) FROM api_responses").fetchone()[0]
            endpoints = conn.execute(
                """
                SELECT endpoint, COUNT(*) AS count
                FROM api_responses
                GROUP BY endpoint
                ORDER BY count DESC, endpoint ASC
                """
            ).fetchall()
            latest = conn.execute(
                "SELECT MAX(updated_at) FROM api_responses"
            ).fetchone()[0]
            oldest = conn.execute(
                "SELECT MIN(created_at) FROM api_responses"
            ).fetchone()[0]
            total_results = conn.execute(
                "SELECT COALESCE(SUM(results), 0) FROM api_responses"
            ).fetchone()[0]

        return {
            "status": "ok",
            "database_path": self.settings.database_path,
            "total_records": total,
            "total_results": total_results,
            "oldest_record_at": oldest,
            "latest_record_at": latest,
            "endpoints": [
                {"endpoint": row["endpoint"], "count": row["count"]}
                for row in endpoints
            ],
        }

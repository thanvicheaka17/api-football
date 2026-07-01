import json
from datetime import date, datetime
from typing import Any

from app.config import Settings, get_settings
from app.database.cleanup import PROTECTED_ENDPOINTS, cleanup_window, window_to_timestamps
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

    def cleanup_records(
        self,
        start: date,
        end: date,
        protected: frozenset[str] | None = None,
        dry_run: bool = False,
    ) -> dict:
        protected = protected if protected is not None else PROTECTED_ENDPOINTS
        start_ts, end_ts = window_to_timestamps(start, end)
        placeholders = ",".join("?" for _ in protected)

        with self.connect() as conn:
            count_sql = f"""
                SELECT COUNT(*) FROM api_responses
                WHERE updated_at >= ? AND updated_at <= ?
                AND endpoint NOT IN ({placeholders})
            """
            params = [start_ts, end_ts, *sorted(protected)]
            to_delete = conn.execute(count_sql, params).fetchone()[0]

            if dry_run or to_delete == 0:
                return {
                    "dry_run": dry_run,
                    "start_date": start.isoformat(),
                    "end_date": end.isoformat(),
                    "deleted_count": 0,
                    "would_delete": to_delete,
                    "protected_endpoints": sorted(protected),
                }

            delete_sql = f"""
                DELETE FROM api_responses
                WHERE updated_at >= ? AND updated_at <= ?
                AND endpoint NOT IN ({placeholders})
            """
            conn.execute(delete_sql, params)

        return {
            "dry_run": False,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "deleted_count": to_delete,
            "would_delete": to_delete,
            "protected_endpoints": sorted(protected),
        }

    def _ensure_cleanup_log(self, conn) -> None:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS cleanup_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_at TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                deleted_count INTEGER NOT NULL
            )
            """
        )

    def last_cleanup_at(self) -> str | None:
        with self.connect() as conn:
            self._ensure_cleanup_log(conn)
            row = conn.execute(
                "SELECT run_at FROM cleanup_log ORDER BY id DESC LIMIT 1"
            ).fetchone()
        return row["run_at"] if row else None

    def log_cleanup(self, result: dict) -> None:
        with self.connect() as conn:
            self._ensure_cleanup_log(conn)
            conn.execute(
                """
                INSERT INTO cleanup_log (run_at, start_date, end_date, deleted_count)
                VALUES (?, ?, ?, ?)
                """,
                (
                    utc_now(),
                    result["start_date"],
                    result["end_date"],
                    result["deleted_count"],
                ),
            )

    def already_cleaned_this_month(self, run_date: date) -> bool:
        last = self.last_cleanup_at()
        if not last:
            return False
        last_dt = datetime.fromisoformat(last)
        return last_dt.year == run_date.year and last_dt.month == run_date.month

    def run_scheduled_cleanup(
        self,
        run_date: date | None = None,
        dry_run: bool = False,
    ) -> dict | None:
        settings = self.settings
        run_date = run_date or date.today()
        window = cleanup_window(run_date, settings.cleanup_retention_months)
        if window is None:
            return None

        start, end = window
        result = self.cleanup_records(start, end, dry_run=dry_run)
        if not dry_run:
            self.log_cleanup(result)
        return result

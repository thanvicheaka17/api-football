import sqlite3
from contextlib import contextmanager

from app.config import Settings, get_settings


class DatabaseConnection:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    @contextmanager
    def connect(self):
        conn = sqlite3.connect(self.settings.database_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

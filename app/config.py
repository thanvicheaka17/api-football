import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


class Settings:
    app_env: str = os.getenv("APP_ENV", "production")
    api_football_url: str = os.getenv("API_FOOTBALL_URL", "https://v3.football.api-sports.io").rstrip("/")
    api_football_key: str = os.getenv("API_FOOTBALL_KEY", "")
    redis_host: str = os.getenv("REDIS_HOST", "127.0.0.1")
    redis_port: int = int(os.getenv("REDIS_PORT", "6379"))
    redis_db: int = int(os.getenv("REDIS_DB", "0"))
    database_path: str = os.getenv("DATABASE_PATH", "database.db")
    cache_ttl_default: int = int(os.getenv("CACHE_TTL_DEFAULT", "300"))
    fetch_on_miss: bool = os.getenv("FETCH_ON_MISS", "false").lower() == "true"
    live_poll_interval: int = int(os.getenv("LIVE_POLL_INTERVAL", "15"))
    live_leagues: str = os.getenv("LIVE_LEAGUES", "all")
    fixtures_refresh_days: int = int(os.getenv("FIXTURES_REFRESH_DAYS", "2"))

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()

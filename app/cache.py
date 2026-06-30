import json
from typing import Any

import redis

from app.config import Settings, get_settings

CACHE_PREFIX = "api-football:"


class RedisCache:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._client: redis.Redis | None = None

    @property
    def client(self) -> redis.Redis:
        if self._client is None:
            self._client = redis.Redis(
                host=self.settings.redis_host,
                port=self.settings.redis_port,
                db=self.settings.redis_db,
                decode_responses=True,
            )
        return self._client

    def _key(self, endpoint: str, params: dict[str, Any]) -> str:
        from app.database.utils import params_hash

        return f"{CACHE_PREFIX}{endpoint}:{params_hash(params)}"

    def get(self, endpoint: str, params: dict[str, Any]) -> dict[str, Any] | None:
        raw = self.client.get(self._key(endpoint, params))
        if not raw:
            return None
        return json.loads(raw)

    def set(self, endpoint: str, params: dict[str, Any], payload: dict[str, Any], ttl: int) -> None:
        self.client.setex(
            self._key(endpoint, params),
            ttl,
            json.dumps(payload, separators=(",", ":")),
        )


def get_cache() -> RedisCache:
    return RedisCache()

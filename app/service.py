from typing import Any

from app.cache import RedisCache, get_cache
from app.config import Settings, get_settings
from app.database import Database, get_database
from app.database.utils import is_empty_upstream_response, should_persist
from app.freshness import fixtures_need_refresh, is_fixtures_endpoint
from app.routing import (
    is_direct_upstream_request,
    is_frequent_request,
    is_live_request,
    is_upstream_first_request,
)
from app.upstream import UpstreamClient, cache_ttl_for_endpoint, get_upstream_client


class FootballDataService:
    def __init__(
        self,
        settings: Settings | None = None,
        cache: RedisCache | None = None,
        database: Database | None = None,
        upstream: UpstreamClient | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.cache = cache or get_cache()
        self.database = database or get_database()
        self.upstream = upstream or get_upstream_client()

    async def get(self, endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
        if is_direct_upstream_request(endpoint, params):
            return await self.get_direct(endpoint, params)

        if is_live_request(endpoint, params) or is_frequent_request(endpoint, params):
            return await self.get_upstream_cached(endpoint, params)

        stored = self.database.get_stored_response(endpoint, params)
        if stored is not None:
            payload = stored.payload
            if is_empty_upstream_response(payload) and self.settings.fetch_on_miss:
                return await self.sync(endpoint, params)
            if is_fixtures_endpoint(endpoint) and fixtures_need_refresh(
                payload,
                params,
                stored.updated_at,
            ):
                if self.settings.fetch_on_miss:
                    return await self.sync(endpoint, params)
            else:
                return payload

        if self.settings.fetch_on_miss:
            return await self.sync(endpoint, params)

        return self.database.empty_response(endpoint, params)

    async def get_upstream_cached(self, endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
        """LIVE + FREQUENT: Redis first (TTL varies), then upstream. DB updated but not read first."""
        cached = self.cache.get(endpoint, params)
        if cached is not None:
            return cached

        payload = await self.sync(endpoint, params)

        if payload.get("errors") and not payload.get("response"):
            stale = self.database.get_response(endpoint, params)
            if stale is not None:
                return stale

        return payload

    async def get_live(self, endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
        return await self.get_upstream_cached(endpoint, params)

    async def get_direct(self, endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
        """Always fetch from upstream (no DB/Redis read). Still saves to DB after fetch."""
        try:
            payload = await self.upstream.fetch(endpoint, params)
        except Exception as exc:
            stale = self.database.get_response(endpoint, params)
            if stale is not None:
                return stale
            return self.database.empty_response(
                endpoint,
                params,
                f"Failed to fetch upstream data: {exc}",
            )

        if should_persist(payload):
            self.database.save_response(endpoint, params, payload)

        return payload

    async def sync(self, endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
        if is_direct_upstream_request(endpoint, params):
            return await self.get_direct(endpoint, params)

        if not is_upstream_first_request(endpoint, params):
            cached = self.cache.get(endpoint, params)
            if cached is not None:
                self.database.save_response(endpoint, params, cached)
                return cached

        try:
            payload = await self.upstream.fetch(endpoint, params)
        except Exception as exc:
            return self.database.empty_response(
                endpoint,
                params,
                f"Failed to fetch upstream data: {exc}",
            )

        if should_persist(payload):
            self.database.save_response(endpoint, params, payload)
            ttl = cache_ttl_for_endpoint(
                endpoint,
                params,
                self.settings.cache_ttl_default,
            )
            self.cache.set(endpoint, params, payload, ttl)

        return payload


def get_football_service() -> FootballDataService:
    return FootballDataService()

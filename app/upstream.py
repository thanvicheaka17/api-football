import re
from typing import Any

import httpx

from app.config import Settings, get_settings

UPSTREAM_HEADER = "x-apisports-key"
TTL_RULES: list[tuple[str, int]] = [
    (r"^timezone$", 86_400),
    (r"^countries$", 86_400),
    (r"^leagues/seasons$", 86_400),
    (r"^seasons$", 86_400),
    (r"^odds/bookmakers$", 86_400),
    (r"^odds/bets$", 86_400),
    (r"^odds/live/bets$", 3_600),
    (r"^fixtures/live$", 15),
    (r"^fixtures/events$", 60),
    (r"^fixtures/statistics$", 60),
    (r"^fixtures/players$", 60),
    (r"^fixtures/lineups$", 300),
    (r"^fixtures$", 60),
    (r"^standings$", 3_600),
    (r"^injuries$", 14_400),
    (r"^predictions$", 3_600),
    (r"^teams/statistics$", 43_200),
    (r"^odds/live$", 30),
    (r"^odds$", 10_800),
    (r"^leagues$", 3_600),
    (r"^teams$", 3_600),
    (r"^players/squads$", 3_600),
    (r"^players/profiles$", 3_600),
    (r"^players/seasons$", 86_400),
    (r"^players$", 3_600),
    (r"^coachs$", 86_400),
    (r"^status$", 60),
]


def cache_ttl_for_endpoint(endpoint: str, params: dict[str, Any], default_ttl: int) -> int:
    if params.get("live"):
        return 15

    for pattern, ttl in TTL_RULES:
        if re.fullmatch(pattern, endpoint):
            return ttl

    return default_ttl


def build_upstream_error(
    endpoint: str,
    params: dict[str, Any],
    message: str,
    status_code: int | None = None,
) -> dict[str, Any]:
    errors: dict[str, Any] = {"upstream": message}
    if status_code is not None:
        errors["statusCode"] = status_code

    response_value: Any = {} if endpoint == "status" else []
    return {
        "get": endpoint,
        "parameters": params,
        "errors": errors,
        "results": 0,
        "paging": {"current": 1, "total": 1},
        "response": response_value,
    }


class UpstreamClient:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    async def fetch(self, endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.settings.api_football_url}/{endpoint}"
        headers = {UPSTREAM_HEADER: self.settings.api_football_key}

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.get(url, params=params or None, headers=headers)
            except httpx.RequestError as exc:
                return build_upstream_error(endpoint, params, str(exc))

            payload: dict[str, Any] | None = None
            if response.content:
                try:
                    payload = response.json()
                except ValueError:
                    payload = None

            if isinstance(payload, dict) and "get" in payload:
                return payload

            if response.is_success and isinstance(payload, dict):
                return payload

            message = response.text.strip() or f"HTTP {response.status_code}"
            return build_upstream_error(endpoint, params, message, response.status_code)


def get_upstream_client() -> UpstreamClient:
    return UpstreamClient()

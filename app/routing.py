"""Route endpoints to the correct data source based on api-football update frequency.

Tiers (api-football documentation v3):
  DIRECT   — always fetch upstream (no Redis/DB read)
  LIVE     — Redis first, 15–60s TTL, skip DB read on GET
  FREQUENT — Redis first, minutes–hours TTL, skip DB read on GET
  STATIC   — SQLite first, long TTL / reference data
"""

from enum import Enum
from typing import Callable

ParamCheck = Callable[[dict], bool]


class DataTier(str, Enum):
    DIRECT = "direct"
    LIVE = "live"
    FREQUENT = "frequent"
    STATIC = "static"


# Always hit upstream — account quota, never stale.
DIRECT_ENDPOINTS: frozenset[str] = frozenset({"status"})

# In-play / real-time — poll every 15–60 seconds during matches.
# Matches api-football: fixtures/live, events, statistics, players, odds/live.
LIVE_RULES: list[tuple[str, ParamCheck | None]] = [
    ("odds/live", None),
    ("fixtures", lambda p: bool(p.get("live"))),
    ("fixtures/events", lambda p: bool(p.get("fixture"))),
    ("fixtures/statistics", lambda p: bool(p.get("fixture"))),
    ("fixtures/players", lambda p: bool(p.get("fixture"))),
    ("fixtures/lineups", lambda p: bool(p.get("fixture"))),
]

# Updates every few minutes to hours — Redis-first, medium TTL.
# Matches api-football refresh: fixtures, standings, injuries, predictions, odds.
FREQUENT_ENDPOINTS: frozenset[str] = frozenset({
    "fixtures",
    "standings",
    "injuries",
    "predictions",
    "odds",
})

# Everything else: countries, leagues, teams, players, transfers, trophies, etc.
# DB-first — changes rarely (hours to days).


def get_data_tier(endpoint: str, params: dict) -> DataTier:
    if endpoint in DIRECT_ENDPOINTS:
        return DataTier.DIRECT

    for path, check in LIVE_RULES:
        if endpoint == path and (check is None or check(params)):
            return DataTier.LIVE

    if endpoint in FREQUENT_ENDPOINTS:
        return DataTier.FREQUENT

    return DataTier.STATIC


def is_direct_upstream_request(endpoint: str, params: dict) -> bool:
    return get_data_tier(endpoint, params) == DataTier.DIRECT


def is_live_request(endpoint: str, params: dict) -> bool:
    return get_data_tier(endpoint, params) == DataTier.LIVE


def is_frequent_request(endpoint: str, params: dict) -> bool:
    return get_data_tier(endpoint, params) == DataTier.FREQUENT


def is_upstream_first_request(endpoint: str, params: dict) -> bool:
    """LIVE + FREQUENT — skip DB read, use Redis then upstream."""
    tier = get_data_tier(endpoint, params)
    return tier in (DataTier.LIVE, DataTier.FREQUENT)

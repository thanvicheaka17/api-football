"""Backward-compatible re-exports — see app/routing.py for tier definitions."""

from app.routing import (
    DataTier,
    get_data_tier,
    is_direct_upstream_request,
    is_frequent_request,
    is_live_request,
    is_upstream_first_request,
)

LIVE_FIXTURE_SUB_ENDPOINTS = frozenset({
    "fixtures/events",
    "fixtures/statistics",
    "fixtures/players",
    "fixtures/lineups",
})

DIRECT_UPSTREAM_ENDPOINTS = frozenset({"status"})

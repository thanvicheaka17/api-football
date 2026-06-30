"""Detect and configure live match data requests."""

LIVE_FIXTURE_SUB_ENDPOINTS = frozenset({
    "fixtures/events",
    "fixtures/statistics",
    "fixtures/players",
    "fixtures/lineups",
})


DIRECT_UPSTREAM_ENDPOINTS = frozenset({
    "status",
})


def is_direct_upstream_request(endpoint: str, params: dict) -> bool:
    return endpoint in DIRECT_UPSTREAM_ENDPOINTS


def is_live_request(endpoint: str, params: dict) -> bool:
    if endpoint == "odds/live":
        return True

    if endpoint == "fixtures" and params.get("live"):
        return True

    if endpoint in LIVE_FIXTURE_SUB_ENDPOINTS and params.get("fixture"):
        return True

    return False

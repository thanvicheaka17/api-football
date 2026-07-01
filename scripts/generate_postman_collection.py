#!/usr/bin/env python3
"""Generate Postman collection from app.endpoint_params."""

import json
from pathlib import Path

from app.endpoint_params import ENDPOINT_PARAMETERS

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "postman" / "livescore-api.postman_collection.json"

FOLDER_MAP: dict[str, list[str]] = {
    "Health": ["/", "health"],
    "Reference": [
        "timezone",
        "status",
        "countries",
        "leagues",
        "leagues/seasons",
        "seasons",
    ],
    "Teams & Venues": ["teams", "teams/statistics", "venues"],
    "Fixtures": [
        "fixtures",
        "fixtures/rounds",
        "fixtures/headtohead",
        "fixtures/statistics",
        "fixtures/events",
        "fixtures/lineups",
        "fixtures/players",
    ],
    "Standings & Players": [
        "standings",
        "players",
        "players/squads",
        "players/profiles",
        "players/seasons",
        "players/teams",
        "players/topscorers",
        "players/topassists",
        "players/topyellowcards",
        "players/topredcards",
    ],
    "Staff & Transfers": ["coachs", "transfers", "trophies", "injuries", "sidelined"],
    "Predictions & Odds": [
        "predictions",
        "odds",
        "odds/live",
        "odds/bookmakers",
        "odds/bets",
        "odds/live/bets",
    ],
}


def _query_params(endpoint: str) -> list[dict]:
    params = ENDPOINT_PARAMETERS.get(endpoint, [])
    query: list[dict] = []
    for param in params:
        schema = param.get("schema", {})
        example = schema.get("example")
        query.append(
            {
                "key": param["name"],
                "value": "" if example is None else str(example),
                "description": param.get("description", ""),
                "disabled": not param.get("required", False),
            }
        )
    return query


def _request_name(endpoint: str) -> str:
    if endpoint == "/":
        return "Root"
    return endpoint.replace("/", " - ").title()


def _build_request(endpoint: str) -> dict:
    path = endpoint.lstrip("/")
    url_path = path.split("/") if path else []
    params = ENDPOINT_PARAMETERS.get(endpoint, [])
    query = _query_params(endpoint)

    query_suffix = ""
    enabled = [q for q in query if not q["disabled"] and q["value"]]
    if enabled:
        query_suffix = "?" + "&".join(f"{q['key']}={q['value']}" for q in enabled)

    raw_url = "{{baseUrl}}"
    if path:
        raw_url += f"/{path}"
    raw_url += query_suffix

    return {
        "name": _request_name(endpoint),
        "request": {
            "method": "GET",
            "header": [],
            "url": {
                "raw": raw_url,
                "host": ["{{baseUrl}}"],
                "path": url_path,
                "query": query,
            },
            "description": "GET /" if path else "GET /",
        },
        "response": [],
    }


def _folder_items(endpoints: list[str]) -> list[dict]:
    return [_build_request(endpoint) for endpoint in endpoints]


def build_collection() -> dict:
    assigned = set()
    folders: list[dict] = []

    for folder_name, endpoints in FOLDER_MAP.items():
        assigned.update(endpoints)
        folders.append(
            {
                "name": folder_name,
                "item": _folder_items(endpoints),
            }
        )

    remaining = [ep for ep in ENDPOINT_PARAMETERS if ep not in assigned]
    if remaining:
        folders.append(
            {
                "name": "Other",
                "item": _folder_items(remaining),
            }
        )

    return {
        "info": {
            "_postman_id": "livescore-api-collection",
            "name": "Livescore API",
            "description": "API-Football proxy. Set collection variables `baseUrl` and `apiKey`. All requests send the `API_KEY` header.",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        },
        "auth": {
            "type": "apikey",
            "apikey": [
                {"key": "key", "value": "API_KEY", "type": "string"},
                {"key": "value", "value": "{{apiKey}}", "type": "string"},
                {"key": "in", "value": "header", "type": "string"},
            ],
        },
        "variable": [
            {"key": "baseUrl", "value": "http://localhost:8000", "type": "string"},
            {"key": "apiKey", "value": "", "type": "string"},
        ],
        "item": folders,
    }


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    collection = build_collection()
    OUTPUT.write_text(json.dumps(collection, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()

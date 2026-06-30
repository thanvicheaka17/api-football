"""Fetch data from upstream (Redis-cached) into SQLite."""

import argparse
import asyncio
import json
import sys

from app.database import get_database
from app.service import get_football_service

REFERENCE_ENDPOINTS = [
    ("timezone", {}),
    ("countries", {}),
    ("leagues/seasons", {}),
    ("seasons", {}),
    ("odds/bookmakers", {}),
    ("odds/bets", {}),
    ("odds/live/bets", {}),
    ("leagues", {"current": "true"}),
]


async def sync_endpoint(endpoint: str, params: dict) -> dict:
    service = get_football_service()
    payload = await service.sync(endpoint, params)
    print(f"synced {endpoint} params={json.dumps(params)} results={payload.get('results')}")
    return payload


async def sync_reference() -> None:
    for endpoint, params in REFERENCE_ENDPOINTS:
        await sync_endpoint(endpoint, params)


async def main() -> None:
    parser = argparse.ArgumentParser(description="Sync API-Football data into SQLite")
    parser.add_argument("endpoint", nargs="?", help="Endpoint path, e.g. countries")
    parser.add_argument("--reference", action="store_true", help="Sync common reference data")
    parser.add_argument("--param", action="append", default=[], help="Query param key=value")
    args = parser.parse_args()

    get_database().init()

    if args.reference:
        await sync_reference()
        return

    if not args.endpoint:
        parser.print_help()
        sys.exit(1)

    params = {}
    for item in args.param:
        key, _, value = item.partition("=")
        params[key] = value

    await sync_endpoint(args.endpoint, params)


if __name__ == "__main__":
    asyncio.run(main())

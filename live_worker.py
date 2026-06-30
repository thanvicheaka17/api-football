"""Background worker: poll live fixtures and refresh recent dates."""

import asyncio
import sys
from datetime import date, timedelta

from app.config import get_settings
from app.database import get_database
from app.freshness import _has_incomplete_fixtures, fixture_item_needs_detail_refresh
from app.service import get_football_service

LIVE_SUB_ENDPOINTS = (
    "fixtures/events",
    "fixtures/statistics",
    "fixtures/lineups",
    "fixtures/players",
)


async def sync_fixture_detail(service, fixture_id: int) -> None:
    detail = await service.sync("fixtures", {"id": str(fixture_id)})
    item = (detail.get("response") or [{}])[0]
    print(
        f"  synced fixtures id={fixture_id} "
        f"status={item.get('fixture', {}).get('status', {}).get('short')} "
        f"goals={item.get('goals')}"
    )

    for endpoint in LIVE_SUB_ENDPOINTS:
        params = {"fixture": str(fixture_id)}
        payload = await service.sync(endpoint, params)
        print(
            f"  synced {endpoint} fixture={fixture_id} "
            f"results={payload.get('results')}"
        )


async def refresh_incomplete_from_date(service, payload: dict) -> None:
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    if not _has_incomplete_fixtures(payload, now):
        return

    for item in payload.get("response") or []:
        fixture_id = item.get("fixture", {}).get("id")
        if not fixture_id:
            continue
        if fixture_item_needs_detail_refresh(item, now):
            await sync_fixture_detail(service, fixture_id)


async def refresh_recent_dates(service) -> None:
    settings = get_settings()
    today = date.today()

    for offset in range(settings.fixtures_refresh_days):
        target = today - timedelta(days=offset)
        params = {"date": target.isoformat()}
        payload = await service.sync("fixtures", params)
        print(
            f"refreshed fixtures date={target.isoformat()} "
            f"results={payload.get('results')}"
        )
        await refresh_incomplete_from_date(service, payload)


async def poll_live_once() -> int:
    settings = get_settings()
    service = get_football_service()

    await refresh_recent_dates(service)

    live_params = {"live": settings.live_leagues}
    fixtures = await service.sync("fixtures", live_params)
    count = fixtures.get("results", 0) or 0
    print(f"live fixtures: {count}")

    for item in fixtures.get("response") or []:
        fixture_id = item.get("fixture", {}).get("id")
        if fixture_id:
            await sync_fixture_detail(service, fixture_id)

    return count


async def run_worker() -> None:
    settings = get_settings()
    get_database().init()

    print(
        f"live worker started "
        f"(interval={settings.live_poll_interval}s, leagues={settings.live_leagues})"
    )

    while True:
        try:
            await poll_live_once()
        except Exception as exc:
            print(f"live worker error: {exc}", file=sys.stderr)

        await asyncio.sleep(settings.live_poll_interval)


if __name__ == "__main__":
    asyncio.run(run_worker())

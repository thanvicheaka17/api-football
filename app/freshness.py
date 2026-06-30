"""Decide when stored fixture data should be refreshed from upstream."""

from datetime import date, datetime, timedelta, timezone
from typing import Any

TERMINAL_STATUSES = frozenset({
    "FT", "AET", "PEN", "CANC", "PST", "AWD", "WO", "ABD", "INT",
})
UPCOMING_STATUSES = frozenset({"NS", "TBD", "SUSP"})


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def _fixture_kickoff(item: dict[str, Any]) -> datetime | None:
    fixture = item.get("fixture") or {}
    timestamp = fixture.get("timestamp")
    if timestamp:
        return datetime.fromtimestamp(timestamp, tz=timezone.utc)

    date_str = fixture.get("date")
    if date_str:
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def _fixture_dates_from_payload(payload: dict[str, Any]) -> list[date]:
    dates: list[date] = []
    for item in payload.get("response") or []:
        kickoff = _fixture_kickoff(item)
        if kickoff:
            dates.append(kickoff.date())
    return dates


def _goals_missing(item: dict[str, Any]) -> bool:
    goals = item.get("goals") or {}
    return goals.get("home") is None and goals.get("away") is None


def _has_incomplete_fixtures(payload: dict[str, Any], now: datetime) -> bool:
    for item in payload.get("response") or []:
        fixture = item.get("fixture") or {}
        status = (fixture.get("status") or {}).get("short", "")
        kickoff = _fixture_kickoff(item)

        if _goals_missing(item) and kickoff and kickoff < now - timedelta(hours=1):
            return True

        if status in TERMINAL_STATUSES and _goals_missing(item):
            return True

        if status in UPCOMING_STATUSES and kickoff and kickoff < now - timedelta(hours=2):
            return True

        if status and status not in TERMINAL_STATUSES and status not in UPCOMING_STATUSES:
            return True

        if status in UPCOMING_STATUSES and kickoff and kickoff.date() < now.date():
            return True

    return False


def _max_age_for_params(
    params: dict[str, Any],
    today: date,
    payload: dict[str, Any] | None = None,
) -> int | None:
    target = _parse_date(params.get("date")) or _parse_date(params.get("from"))

    if target is None and payload:
        fixture_dates = _fixture_dates_from_payload(payload)
        if fixture_dates:
            target = max(fixture_dates)

    if target is None and (params.get("id") or params.get("ids") or params.get("fixture")):
        return 300

    if target is None:
        return None

    days_ago = (today - target).days
    if days_ago == 0:
        return 300
    if days_ago == 1:
        return 1800
    if days_ago <= 7:
        return 7200
    return None


def fixtures_need_refresh(
    payload: dict[str, Any],
    params: dict[str, Any],
    updated_at: datetime,
) -> bool:
    if params.get("live"):
        return True

    now = datetime.now(timezone.utc)
    today = now.date()

    if _has_incomplete_fixtures(payload, now):
        return True

    max_age = _max_age_for_params(params, today, payload)
    if max_age is None:
        return False

    age = (now - updated_at).total_seconds()
    return age > max_age


def fixture_item_needs_detail_refresh(item: dict[str, Any], now: datetime) -> bool:
    fixture = item.get("fixture") or {}
    status = (fixture.get("status") or {}).get("short", "")
    kickoff = _fixture_kickoff(item)

    if _goals_missing(item) and kickoff and kickoff < now - timedelta(hours=1):
        return True

    if status in TERMINAL_STATUSES and _goals_missing(item):
        return True

    if status in UPCOMING_STATUSES and kickoff and kickoff < now - timedelta(hours=2):
        return True

    if status and status not in TERMINAL_STATUSES and status not in UPCOMING_STATUSES:
        return True

    return False


def is_fixtures_endpoint(endpoint: str) -> bool:
    return endpoint == "fixtures"

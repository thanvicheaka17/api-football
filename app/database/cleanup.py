"""Compute cleanup windows and delete aged api_responses records."""

from datetime import date, datetime, timedelta, timezone

from app.config import Settings, get_settings

# Reference endpoints kept across cleanups (re-sync is expensive / rarely changes).
PROTECTED_ENDPOINTS: frozenset[str] = frozenset({
    "timezone",
    "countries",
    "leagues/seasons",
    "seasons",
    "odds/bookmakers",
    "odds/bets",
    "odds/live/bets",
})


def cleanup_window(
    run_date: date,
    retention_months: int = 3,
) -> tuple[date, date] | None:
    """Return (start, end) inclusive dates for records to delete.

    On the 15th of July 2026 with retention=3:
      delete records from 2026-04-01 through 2026-06-30.

    The window is the 3 full calendar months immediately before the current month.
    """
    if retention_months < 1:
        return None

    first_of_current = date(run_date.year, run_date.month, 1)
    end = first_of_current - timedelta(days=1)

    start_month = run_date.month - retention_months
    start_year = run_date.year
    while start_month <= 0:
        start_month += 12
        start_year -= 1

    start = date(start_year, start_month, 1)
    return start, end


def window_to_timestamps(start: date, end: date) -> tuple[str, str]:
    start_dt = datetime(start.year, start.month, start.day, tzinfo=timezone.utc)
    end_dt = datetime(end.year, end.month, end.day, 23, 59, 59, tzinfo=timezone.utc)
    return start_dt.isoformat(), end_dt.isoformat()


def should_run_cleanup(run_date: date, cleanup_day: int) -> bool:
    return run_date.day == cleanup_day

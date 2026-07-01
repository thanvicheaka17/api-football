"""Scheduled cleanup: on day 15 each month, delete records older than 3 months."""

import argparse
import asyncio
import json
import sys
from datetime import date

from app.config import get_settings
from app.database import get_database
from app.database.cleanup import cleanup_window, should_run_cleanup


async def run_cleanup_once(force: bool = False, dry_run: bool = False) -> None:
    settings = get_settings()
    db = get_database()
    db.init()

    today = date.today()
    window = cleanup_window(today, settings.cleanup_retention_months)

    if not force and not should_run_cleanup(today, settings.cleanup_day):
        print(f"skip: today is day {today.day}, cleanup runs on day {settings.cleanup_day}")
        if window:
            start, end = window
            print(f"next window when triggered: {start.isoformat()} to {end.isoformat()}")
        return

    if not force and db.already_cleaned_this_month(today):
        print(f"skip: cleanup already ran this month ({today.year}-{today.month:02d})")
        return

    if window is None:
        print("skip: invalid retention months")
        return

    start, end = window
    print(f"cleanup window: {start.isoformat()} to {end.isoformat()} (dry_run={dry_run})")

    result = db.run_scheduled_cleanup(run_date=today, dry_run=dry_run)
    print(json.dumps(result, indent=2))


async def run_scheduler() -> None:
    settings = get_settings()
    db = get_database()
    db.init()

    print(
        f"cleanup scheduler started "
        f"(day={settings.cleanup_day}, retention={settings.cleanup_retention_months} months, "
        f"check every {settings.cleanup_check_interval}s)"
    )

    while True:
        if settings.cleanup_enabled:
            try:
                today = date.today()
                if should_run_cleanup(today, settings.cleanup_day):
                    if not db.already_cleaned_this_month(today):
                        window = cleanup_window(today, settings.cleanup_retention_months)
                        if window:
                            start, end = window
                            print(f"running cleanup: {start.isoformat()} to {end.isoformat()}")
                            result = db.run_scheduled_cleanup(run_date=today)
                            print(json.dumps(result, indent=2))
                    else:
                        print(f"cleanup already done for {today.year}-{today.month:02d}")
            except Exception as exc:
                print(f"cleanup error: {exc}", file=sys.stderr)

        await asyncio.sleep(settings.cleanup_check_interval)


async def main() -> None:
    parser = argparse.ArgumentParser(description="Database cleanup scheduler")
    parser.add_argument("--run-now", action="store_true", help="Run cleanup immediately")
    parser.add_argument("--force", action="store_true", help="Run even if not cleanup day")
    parser.add_argument("--dry-run", action="store_true", help="Count records only, do not delete")
    args = parser.parse_args()

    if args.run_now or args.force or args.dry_run:
        await run_cleanup_once(force=args.force or args.run_now, dry_run=args.dry_run)
        return

    await run_scheduler()


if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""Phase 612 — XNYS session and conservative SEC 13F knowledge-clock audit.

The calendar is a pinned, reproducible dependency. Selected 2026 sessions are
cross-checked against the official NYSE calendar. This module separates:
(1) earliest session open after event knowledge,
(2) first completed daily bar after knowledge, and
(3) execution only after that completed bar.
No SEC requests, price downloads, signals, or return tests are performed.
"""
from __future__ import annotations

import json
from collections import Counter
from datetime import date, datetime, time, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import exchange_calendars as xcals
import pandas as pd

ET = ZoneInfo("America/New_York")
START = "2013-01-01"
AS_OF = "2026-11-24"
CALENDAR_START = "2001-01-01"
CALENDAR_END = "2027-12-31"
EXPECTED_EXCHANGE_CALENDARS_VERSION = "4.13.1"


def parse_aware_timestamp(value: str | datetime) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    else:
        raise TypeError("timestamp_must_be_datetime_or_iso_string")
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timestamp_must_be_timezone_aware")
    return parsed.astimezone(timezone.utc)


def parse_filing_date(value: str | date) -> date:
    if isinstance(value, datetime):
        raise TypeError("filing_date_must_be_date_not_datetime")
    if isinstance(value, date):
        return value
    if not isinstance(value, str):
        raise TypeError("filing_date_must_be_iso_date_or_date")
    return date.fromisoformat(value)


def _iso_utc(value: pd.Timestamp) -> str:
    return value.tz_convert("UTC").isoformat()


def resolve_daily_knowledge_clock(
    accepted_at: str | datetime,
    filing_date: str | date,
    collector_first_seen: str | datetime | None = None,
    calendar=None,
) -> dict:
    """Map a filing to conservative event and daily-bar clocks.

    If a prospective collector first-seen timestamp exists, use the later of
    EDGAR Accepted and collector first-seen. If it does not exist, use the end
    of the legal Filing Date in ET as a conservative fallback; never backdate
    to the report period or assume intraday observability.

    A daily bar is complete only when its scheduled close is strictly later
    than effective knowledge time. A daily-bar-derived signal cannot execute
    until the next XNYS session. Both next-open and next-EOD execution clocks
    are returned so the strategy's actual fill convention can be tested.
    """
    accepted_utc = parse_aware_timestamp(accepted_at)
    filed = parse_filing_date(filing_date)

    if collector_first_seen is not None:
        first_seen_utc = parse_aware_timestamp(collector_first_seen)
        effective = max(accepted_utc, first_seen_utc)
        availability_mode = "OBSERVED_FIRST_SEEN_MAX_ACCEPTED"
        first_seen_value = first_seen_utc.isoformat()
    else:
        filing_date_end_et = datetime.combine(
            filed, time(23, 59, 59), tzinfo=ET
        )
        filing_date_end_utc = filing_date_end_et.astimezone(timezone.utc)
        effective = max(accepted_utc, filing_date_end_utc)
        availability_mode = "FILING_DATE_END_OF_DAY_FALLBACK"
        first_seen_value = None

    cal = calendar or xcals.get_calendar(
        "XNYS", start=CALENDAR_START, end=CALENDAR_END
    )
    schedule = cal.schedule
    effective_ts = pd.Timestamp(effective)

    open_rows = schedule[schedule["open"] > effective_ts]
    close_rows = schedule[schedule["close"] > effective_ts]
    if open_rows.empty or close_rows.empty:
        raise ValueError("knowledge_time_outside_calendar_coverage")

    first_open_session = open_rows.index[0]
    first_open_row = open_rows.iloc[0]

    decision_session = close_rows.index[0]
    decision_row = close_rows.iloc[0]
    decision_position = schedule.index.get_loc(decision_session)
    if decision_position + 1 >= len(schedule):
        raise ValueError("next_execution_session_outside_calendar_coverage")

    next_session = schedule.index[decision_position + 1]
    next_row = schedule.iloc[decision_position + 1]

    return {
        "availability_mode": availability_mode,
        "accepted_at_utc": accepted_utc.isoformat(),
        "collector_first_seen_utc": first_seen_value,
        "effective_knowledge_at_utc": effective.isoformat(),
        "first_event_only_open_session": first_open_session.date().isoformat(),
        "first_event_only_open_at_utc": _iso_utc(first_open_row["open"]),
        "first_completed_daily_bar_session": decision_session.date().isoformat(),
        "first_completed_daily_bar_close_at_utc": _iso_utc(decision_row["close"]),
        "daily_bar_signal_earliest_next_open_session": next_session.date().isoformat(),
        "daily_bar_signal_earliest_next_open_at_utc": _iso_utc(next_row["open"]),
        "daily_bar_signal_earliest_next_eod_session": next_session.date().isoformat(),
        "daily_bar_signal_earliest_next_eod_at_utc": _iso_utc(next_row["close"]),
    }


def audit_calendar(calendar=None) -> dict:
    cal = calendar or xcals.get_calendar(
        "XNYS", start=CALENDAR_START, end=CALENDAR_END
    )
    schedule = cal.schedule.loc[START:AS_OF]
    opens_et = schedule["open"].dt.tz_convert(ET)
    closes_et = schedule["close"].dt.tz_convert(ET)

    open_times = sorted(set(opens_et.dt.strftime("%H:%M")))
    close_counts = Counter(closes_et.dt.strftime("%H:%M"))
    weekend_sessions = [
        session.date().isoformat()
        for session in schedule.index
        if session.weekday() >= 5
    ]

    def is_session(day: str) -> bool:
        return bool(cal.is_session(pd.Timestamp(day)))

    def close_et(day: str) -> str | None:
        stamp = pd.Timestamp(day)
        if not cal.is_session(stamp):
            return None
        return cal.session_close(stamp).tz_convert(ET).strftime("%H:%M")

    official_2026_checks = {
        "2026-07-03": {"is_session": False},
        "2026-11-26": {"is_session": False},
        "2026-11-27": {"is_session": True, "close_et": "13:00"},
        "2026-12-24": {"is_session": True, "close_et": "13:00"},
    }
    official_check_results = {}
    for day, expected in official_2026_checks.items():
        actual_session = is_session(day)
        actual_close = close_et(day)
        official_check_results[day] = {
            "expected": expected,
            "actual": {
                "is_session": actual_session,
                **({"close_et": actual_close} if actual_session else {}),
            },
            "pass": actual_session == expected["is_session"]
            and (
                "close_et" not in expected
                or actual_close == expected["close_et"]
            ),
        }

    special_closures = {
        "2018-12-05": False,
        "2025-01-09": False,
        "2012-10-29": False,
        "2012-10-30": False,
        "2001-09-11": False,
        "2001-09-12": False,
        "2001-09-13": False,
        "2001-09-14": False,
    }
    special_closure_results = {
        day: {"expected_is_session": expected, "actual_is_session": is_session(day),
              "pass": is_session(day) == expected}
        for day, expected in special_closures.items()
    }

    dst_checks = {
        "2026-02-27": cal.session_open(pd.Timestamp("2026-02-27")).strftime("%H:%M"),
        "2026-03-09": cal.session_open(pd.Timestamp("2026-03-09")).strftime("%H:%M"),
    }
    dst_pass = dst_checks == {"2026-02-27": "14:30", "2026-03-09": "13:30"}

    year_counts = {
        str(year): int((schedule.index.year == year).sum())
        for year in sorted(set(schedule.index.year))
    }
    checks = {
        "sessions_nonempty": len(schedule) > 0,
        "no_weekend_sessions": not weekend_sessions,
        "open_time_is_0930_et": open_times == ["09:30"],
        "close_times_are_regular_or_early": set(close_counts).issubset({"13:00", "16:00"}),
        "official_2026_cross_checks": all(x["pass"] for x in official_check_results.values()),
        "historical_special_closures": all(x["pass"] for x in special_closure_results.values()),
        "dst_utc_shift": dst_pass,
    }
    return {
        "status": "PASS" if all(checks.values()) else "REVIEW",
        "exchange": "XNYS",
        "exchange_calendars_version": xcals.__version__,
        "coverage_start": START,
        "coverage_end_as_of": AS_OF,
        "calendar_engine_start": CALENDAR_START,
        "calendar_engine_end": CALENDAR_END,
        "session_count": int(len(schedule)),
        "year_session_counts": year_counts,
        "early_close_count_1300_et": int((closes_et.dt.strftime("%H:%M") == "13:00").sum()),
        "open_time_counts_et": dict(Counter(opens_et.dt.strftime("%H:%M"))),
        "close_time_counts_et": dict(close_counts),
        "weekend_sessions": weekend_sessions,
        "official_2026_cross_checks": official_check_results,
        "historical_special_closures": special_closure_results,
        "dst_open_utc_checks": dst_checks,
        "checks": checks,
        "limitations": [
            "exchange_calendars is a third-party maintained calendar, not the exchange's official data feed",
            "only selected 2026 dates were cross-checked to the official NYSE calendar",
            "historical emergency closures are spot-checked, not exhaustively reconciled against every NYSE notice",
            "a scheduled session close is not proof of the exact timestamp of a vendor's daily-bar publication",
            "no order-type, auction-cutoff, halt, or symbol-specific trading restriction is modeled",
        ],
    }


def main() -> int:
    if xcals.__version__ != EXPECTED_EXCHANGE_CALENDARS_VERSION:
        raise RuntimeError(
            f"exchange_calendars_version_mismatch:{xcals.__version__}"
        )
    cal = xcals.get_calendar("XNYS", start=CALENDAR_START, end=CALENDAR_END)
    calendar_result = audit_calendar(cal)
    examples = [
        resolve_daily_knowledge_clock(
            "2026-08-26T11:11:54-04:00",
            "2026-08-26",
            "2026-08-26T15:30:00Z",
            cal,
        ),
        resolve_daily_knowledge_clock(
            "2026-08-26T18:42:02-04:00",
            "2026-08-27",
            "2026-08-26T23:45:00Z",
            cal,
        ),
        resolve_daily_knowledge_clock(
            "2026-08-26T11:11:54-04:00",
            "2026-08-26",
            None,
            cal,
        ),
        resolve_daily_knowledge_clock(
            "2026-11-27T12:00:00-05:00",
            "2026-11-27",
            "2026-11-27T17:00:00Z",
            cal,
        ),
    ]
    result = {
        "phase": 612,
        "status": "PASS" if calendar_result["status"] == "PASS" else "REVIEW",
        "calendar_audit": calendar_result,
        "clock_examples": examples,
        "signal_eligible": False,
        "alpha_tested": False,
        "production_eligible": False,
        "baseline": "F80_TOP20_PARTIAL50_BASELINE_C20",
        "baseline_changed": False,
        "paid_data_purchased": False,
        "sec_requests_made": False,
    }
    output = Path("phase612_xnys_session_knowledge_clock_audit.json")
    output.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

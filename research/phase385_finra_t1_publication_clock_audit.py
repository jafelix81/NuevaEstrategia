#!/usr/bin/env python3
"""Phase 385: FINRA T1 ATS date-level publication-clock census.

Uses the 209 weekly T1 historic partitions established by Phase 375. It
retrieves only ATS_W_SMBL aggregate rows, verifies the publication date across
all aggregate symbols in each partition, checks the documented T1 delay
against the NYSE calendar, and derives a conservative first eligible session
strictly after the publication date.

No symbols, participant identifiers, raw rows, returns, alpha, OOS, bootstrap,
LOO or holdout data are persisted. This is a date-level PIT bound only; it is
not an exact intraday first-receipt ledger and does not itself authorize a
return test.
"""
from __future__ import annotations

import argparse
import csv
import importlib.metadata
import json
import os
import time
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas_market_calendars as mcal
import requests

import research.phase371_finra_t1_ats_monthly_coverage_audit as P371

EXPECTED_WEEKS = 209
EXPECTED_FIRST = date(2021, 11, 15)
EXPECTED_LAST = date(2025, 11, 10)
TIER = "T1"
SUMMARY_TYPE = "ATS_W_SMBL"
PAGE_LIMIT = 5000
NYSE = mcal.get_calendar("NYSE")


def validate_weekly_anchors(weeks):
    parsed = sorted(date.fromisoformat(str(w)[:10]) for w in weeks)
    duplicates = len(parsed) - len(set(parsed))
    gaps = [
        {"left": a.isoformat(), "right": b.isoformat(), "gap_days": (b-a).days}
        for a, b in zip(parsed, parsed[1:]) if (b-a).days != 7
    ]
    return {
        "count": len(parsed),
        "first": parsed[0].isoformat() if parsed else None,
        "last": parsed[-1].isoformat() if parsed else None,
        "duplicates": duplicates,
        "nonweekly_gaps": gaps,
        "consecutive": bool(parsed) and duplicates == 0 and not gaps
            and len(parsed) == EXPECTED_WEEKS
            and parsed[0] == EXPECTED_FIRST and parsed[-1] == EXPECTED_LAST,
    }


def session_on_or_after(day: date, calendar=NYSE) -> date:
    end = day + timedelta(days=10)
    schedule = calendar.schedule(start_date=day.isoformat(), end_date=end.isoformat())
    if schedule.empty:
        raise RuntimeError(f"No NYSE session found on/after {day}")
    return schedule.index[0].date()


def session_strictly_after(day: date, calendar=NYSE) -> date:
    return session_on_or_after(day + timedelta(days=1), calendar)


def expected_initial_publication(week_start: date, calendar=NYSE) -> date:
    # T1 reporting delay is two weeks after the Friday week-end. Since
    # weekStartDate is Monday, the nominal first Monday is +21 calendar days.
    # If that Monday is a market holiday, the next NYSE session is expected.
    return session_on_or_after(week_start + timedelta(days=21), calendar)


def build_clock_record(
    week: date,
    publication_dates,
    row_count: int,
    record_total: int,
    missing_date_rows: int,
    update_gap_counts,
    pages: int,
    calendar=NYSE,
):
    pubs = sorted(publication_dates)
    unique_count = len(pubs)
    actual = pubs[0] if unique_count == 1 else None
    expected = expected_initial_publication(week, calendar)
    lag = (actual - week).days if actual else None
    eligible = session_strictly_after(actual, calendar) if actual else None
    schedule_match = bool(actual and actual == expected)
    complete = row_count == record_total and record_total > 0
    date_complete = unique_count == 1 and missing_date_rows == 0
    lag_ok = lag in (21, 22)
    gate = complete and date_complete and lag_ok and schedule_match and eligible is not None
    return {
        "week_start_date": week.isoformat(),
        "aggregate_rows": row_count,
        "record_total": record_total,
        "pages": pages,
        "retrieval_count_match": complete,
        "initial_published_date_unique_count": unique_count,
        "initial_published_date": actual.isoformat() if actual else None,
        "missing_or_invalid_date_rows": missing_date_rows,
        "publication_lag_days": lag,
        "expected_publication_date": expected.isoformat(),
        "publication_schedule_match": schedule_match,
        "first_eligible_nyse_session_strictly_after_publication": (
            eligible.isoformat() if eligible else None
        ),
        "rows_last_update_equal_initial": int(update_gap_counts.get(0, 0)),
        "rows_updated_after_initial": sum(v for k, v in update_gap_counts.items() if k > 0),
        "rows_last_update_before_initial": sum(v for k, v in update_gap_counts.items() if k < 0),
        "update_gap_days_counts": {str(k): v for k, v in sorted(update_gap_counts.items())},
        "date_level_clock_gate": "PASS" if gate else "FAIL_OR_REVIEW",
    }


def request_page(session, week, offset):
    body = {
        "compareFilters": [
            {"fieldName": "historicalWeek", "fieldValue": week.isoformat(), "compareType": "EQUAL"},
            {"fieldName": "tierIdentifier", "fieldValue": TIER, "compareType": "EQUAL"},
            {"fieldName": "summaryTypeCode", "fieldValue": SUMMARY_TYPE, "compareType": "EQUAL"},
        ],
        "limit": PAGE_LIMIT,
        "offset": offset,
    }
    for attempt in range(4):
        try:
            response = session.post(P371.DATA_URL, json=body, timeout=(20, 120))
            if response.status_code in {408, 429, 500, 502, 503, 504}:
                if attempt == 3:
                    response.raise_for_status()
                retry = response.headers.get("Retry-After")
                try:
                    delay = float(retry) if retry else 2 ** (attempt + 1)
                except (TypeError, ValueError):
                    delay = 2 ** (attempt + 1)
                time.sleep(max(0, min(delay, 30)))
                continue
            response.raise_for_status()
            rows = P371.parse_rows(response.json())
            headers = {str(k).lower(): v for k, v in response.headers.items()}
            if "record-total" not in headers:
                raise RuntimeError("Missing FINRA Record-Total")
            if "record-offset" in headers and int(headers["record-offset"]) != offset:
                raise RuntimeError("FINRA Record-Offset mismatch")
            if int(headers.get("total-records-on-page", len(rows))) != len(rows):
                raise RuntimeError("FINRA Total-Records-On-Page mismatch")
            if len(rows) > PAGE_LIMIT:
                raise RuntimeError("FINRA page exceeded requested limit")
            return rows, int(headers["record-total"])
        except (requests.RequestException, ValueError) as exc:
            if attempt == 3:
                raise RuntimeError(f"FINRA aggregate page failed ({type(exc).__name__})") from exc
            time.sleep(min(2 ** (attempt + 1), 20))
    raise RuntimeError("FINRA aggregate-page retries exhausted")


def fetch_week(session, week):
    rows_count = 0
    record_total = None
    pages = 0
    publication_dates = set()
    update_gap_counts = Counter()
    missing_date_rows = 0
    offset = 0
    while True:
        batch, total = request_page(session, week, offset)
        if record_total is None:
            record_total = total
        elif total != record_total:
            raise RuntimeError("FINRA Record-Total changed during pagination")
        pages += 1
        for row in batch:
            if P371.norm(row.get("summaryTypeCode")) != SUMMARY_TYPE:
                raise RuntimeError("Unexpected summaryTypeCode in filtered response")
            row_week = P371.parse_date(row.get("weekStartDate") or row.get("historicalWeek"))
            if row_week != week:
                raise RuntimeError("Unexpected historicalWeek in filtered response")
            pub = P371.parse_date(row.get("initialPublishedDate"))
            upd = P371.parse_date(row.get("lastUpdateDate"))
            if pub is None or upd is None:
                missing_date_rows += 1
            else:
                publication_dates.add(pub)
                update_gap_counts[(upd - pub).days] += 1
        rows_count += len(batch)
        if rows_count == record_total:
            break
        if rows_count > record_total or not batch:
            raise RuntimeError("FINRA pagination mismatch or no progress")
        offset += len(batch)
        if offset > P371.MAX_OFFSET:
            raise RuntimeError("FINRA offset exceeded maximum")
        time.sleep(0.12)
    if not record_total:
        raise RuntimeError("No ATS_W_SMBL aggregate rows for partition")
    return build_clock_record(
        week, publication_dates, rows_count, record_total,
        missing_date_rows, update_gap_counts, pages,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="phase385_finra_t1_publication_clock_audit")
    args = parser.parse_args()
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers.update({
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Data-API-Version": "1",
        "User-Agent": "SmartMoneyResearch-Phase385/1.0",
    })
    token = os.getenv("FINRA_API_TOKEN", "").strip()
    if token:
        session.headers["Authorization"] = f"Bearer {token}"

    metadata_before, _ = P371.request_json(session, P371.META_URL)
    partition_payload, _ = P371.request_json(session, P371.PARTITIONS_URL)
    fields, raw_records, unique = P371.parse_partition_payload(
        partition_payload, metadata_before.get("partitionFields") or P371.EXPECTED_PARTITION_FIELDS
    )
    if tuple(metadata_before.get("partitionFields") or fields) != P371.EXPECTED_PARTITION_FIELDS:
        raise RuntimeError("FINRA partition schema changed")
    weeks = sorted({
        date.fromisoformat(str(r["weekStartDate"])[:10])
        for r in unique if r.get("tierIdentifier") == TIER
    })
    inventory = validate_weekly_anchors([d.isoformat() for d in weeks])
    if not inventory["consecutive"]:
        raise RuntimeError("FINRA T1 inventory failed the 209-week consecutive gate")

    partitions = []
    errors = []
    for i, week in enumerate(weeks, start=1):
        try:
            record = fetch_week(session, week)
            partitions.append(record)
            print(
                f"WEEK={i}/{len(weeks)}|DATE={week}|ROWS={record['aggregate_rows']}|"
                f"PUB={record['initial_published_date']}|LAG={record['publication_lag_days']}|"
                f"SCHEDULE={record['publication_schedule_match']}|"
                f"ELIGIBLE={record['first_eligible_nyse_session_strictly_after_publication']}",
                flush=True,
            )
        except Exception as exc:
            errors.append({"week": week.isoformat(), "error_type": type(exc).__name__})
            print(f"WEEK_ERROR={week}|TYPE={type(exc).__name__}", flush=True)

    metadata_after, _ = P371.request_json(session, P371.META_URL)
    metadata_stable = metadata_before.get("rowsUpdatedAt") == metadata_after.get("rowsUpdatedAt")
    complete = len(partitions) == len(weeks) and not errors and all(
        x["retrieval_count_match"] for x in partitions
    )
    date_gate = complete and all(x["date_level_clock_gate"] == "PASS" for x in partitions)
    summary = {
        "phase": 385,
        "source": "FINRA OTCMarket weeklySummaryHistoric / T1 / ATS_W_SMBL",
        "audit_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "partition_fields": list(fields),
        "raw_partition_records": len(raw_records),
        "unique_partition_pairs": len(unique),
        "tier": TIER,
        "summary_type": SUMMARY_TYPE,
        "inventory": inventory,
        "expected_partitions": EXPECTED_WEEKS,
        "completed_partitions": len(partitions),
        "errors": errors,
        "all_partitions_complete": complete,
        "metadata_stable": metadata_stable,
        "total_aggregate_rows": sum(x["aggregate_rows"] for x in partitions),
        "total_pages": sum(x["pages"] for x in partitions),
        "partitions_with_one_publication_date": sum(
            x["initial_published_date_unique_count"] == 1 for x in partitions
        ),
        "partitions_matching_documented_calendar": sum(
            x["publication_schedule_match"] for x in partitions
        ),
        "publication_lag_days_counts": dict(sorted(Counter(
            str(x["publication_lag_days"]) for x in partitions
        ).items())),
        "all_date_level_clock_gates_pass": date_gate,
        "date_level_clock_validated": bool(date_gate and metadata_stable),
        "first_eligible_session_rule": (
            "first NYSE regular session strictly after the actual initialPublishedDate; "
            "never use same-day close/open and do not infer an intraday release time"
        ),
        "expected_publication_rule": (
            "first NYSE session on or after weekStartDate + 21 calendar days, "
            "consistent with T1's two-week delay after the Friday week-end"
        ),
        "calendar": "NYSE via pandas_market_calendars",
        "calendar_package_version": importlib.metadata.version("pandas_market_calendars"),
        "intraday_first_receipt_certified": False,
        "effective_dated_security_master_gate_passed": False,
        "historical_return_test_authorized": False,
        "forward_returns_used": False,
        "alpha_test_authorized": False,
        "oos_test_used": False,
        "bootstrap_used": False,
        "loo_used": False,
        "holdout_used": False,
        "f80_changed": False,
        "production_changed": False,
        "raw_rows_retained": False,
        "raw_identifiers_retained": False,
        "research_disposition": (
            "DATE_LEVEL_PUBLICATION_CLOCK_VALIDATED_NO_RETURN_TEST"
            if date_gate and metadata_stable else "PUBLICATION_CLOCK_NOT_VALIDATED"
        ),
        "partitions": partitions,
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    with (out / "weekly_clock.csv").open("w", newline="", encoding="utf-8") as handle:
        fields_out = [
            "week_start_date", "aggregate_rows", "record_total", "pages",
            "initial_published_date", "publication_lag_days", "expected_publication_date",
            "publication_schedule_match",
            "first_eligible_nyse_session_strictly_after_publication",
            "rows_last_update_equal_initial", "rows_updated_after_initial",
            "rows_last_update_before_initial", "date_level_clock_gate",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields_out)
        writer.writeheader()
        for row in partitions:
            writer.writerow({k: row.get(k) for k in fields_out})
    print(json.dumps({k: v for k, v in summary.items() if k != "partitions"}, indent=2), flush=True)
    if not complete or not date_gate or not metadata_stable:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

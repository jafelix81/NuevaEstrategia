#!/usr/bin/env python3
"""Reproduce the preregistered Russell-only CFTC fixed-reference feature.

This is a data/feature audit only. It never downloads prices, creates outcomes,
fits a model, or emits a trading signal.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from phase384_cftc_tff_prospective_capture import check_oi, digest, num

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "cftc_tff_prospective"
BASELINE = DATA / "historical_backfill.csv"
MANIFEST = DATA / "baseline_manifest.json"
EVENTS = DATA / "events"
CONTRACT_CODE = "239742"
KNOWLEDGE_BOUND = datetime.fromisoformat("2026-11-14T00:44:59+00:00")
EXPECTED_BASELINE_BLOB = "4711abbaeeb6107d1cb8f50a7c2e3627373b6d29"
EXPECTED_MANIFEST_BLOB = "9e58849093f2144ce8cfbf1d3e5efc626a1aa250"
EXCLUDED_DATES = {"2018-09-25", "2019-12-24"}
EXPECTED_ALL_ROWS = 3035
EXPECTED_RUSSELL_ROWS = 482
EXPECTED_REFERENCE_ROWS = 480
HIGH_THRESHOLD = Decimal("0.80")


def git_blob_sha(path: Path) -> str:
    raw = path.read_bytes()
    header = f"blob {len(raw)}\0".encode("ascii")
    return hashlib.sha1(header + raw).hexdigest()


def parse_utc(value: str) -> datetime:
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid first_seen_utc: {value!r}") from exc
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError("first_seen_utc must be timezone-aware")
    if dt.utcoffset().total_seconds() != 0:
        raise ValueError("first_seen_utc must be normalized to UTC")
    return dt


def load_reference(baseline_path: Path = BASELINE,
                   manifest_path: Path = MANIFEST) -> tuple[list[Decimal], dict[str, Any]]:
    if git_blob_sha(baseline_path) != EXPECTED_BASELINE_BLOB:
        raise ValueError("frozen historical_backfill.csv Git blob SHA mismatch")
    if git_blob_sha(manifest_path) != EXPECTED_MANIFEST_BLOB:
        raise ValueError("frozen baseline_manifest.json Git blob SHA mismatch")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("row_count") != EXPECTED_ALL_ROWS:
        raise ValueError("baseline manifest row_count mismatch")
    if manifest.get("signal_eligible") is not False:
        raise ValueError("historical baseline must remain signal-ineligible")
    if manifest.get("historical_availability") != "NOT_CERTIFIED; feature warm-up only":
        raise ValueError("historical PIT status changed")
    if manifest.get("created_utc") != "2026-11-13T23:03:38Z":
        raise ValueError("baseline snapshot creation timestamp changed")

    all_rows: list[dict[str, str]] = []
    with baseline_path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required = {"report_date", "contract_code", "leveraged_money_net_oi",
                    "historical_pit_status", "signal_eligible", "row_sha256"}
        if not required.issubset(set(reader.fieldnames or [])):
            raise ValueError("baseline CSV is missing required columns")
        all_rows.extend(reader)

    if len(all_rows) != EXPECTED_ALL_ROWS:
        raise ValueError(f"expected {EXPECTED_ALL_ROWS} rows, found {len(all_rows)}")

    russell = [row for row in all_rows if row.get("contract_code") == CONTRACT_CODE]
    if len(russell) != EXPECTED_RUSSELL_ROWS:
        raise ValueError(f"expected {EXPECTED_RUSSELL_ROWS} Russell rows, found {len(russell)}")

    by_date: dict[str, dict[str, str]] = {}
    for row in russell:
        report_date = row.get("report_date", "")
        if not report_date or report_date in by_date:
            raise ValueError(f"missing or duplicate Russell report date: {report_date!r}")
        by_date[report_date] = row
        if row.get("historical_pit_status") != "UNVERIFIED_ARCHIVE_PROXY":
            raise ValueError("historical row lost UNVERIFIED_ARCHIVE_PROXY classification")
        if row.get("signal_eligible", "").strip().lower() not in {"false", "0"}:
            raise ValueError("historical archive row became signal-eligible")
        if len(row.get("row_sha256", "")) != 64:
            raise ValueError("historical source-row hash is missing or malformed")

    if not EXCLUDED_DATES.issubset(by_date):
        raise ValueError("the two preregistered archive exceptions are not both present")

    reference: list[Decimal] = []
    for report_date, row in sorted(by_date.items()):
        if report_date in EXCLUDED_DATES:
            continue
        try:
            value = Decimal(row["leveraged_money_net_oi"])
        except (KeyError, InvalidOperation) as exc:
            raise ValueError(f"invalid historical LM net/OI at {report_date}") from exc
        if not value.is_finite():
            raise ValueError(f"non-finite historical LM net/OI at {report_date}")
        reference.append(value)

    if len(reference) != EXPECTED_REFERENCE_ROWS:
        raise ValueError(f"expected {EXPECTED_REFERENCE_ROWS} reference values, found {len(reference)}")
    return reference, {
        "all_contract_rows": len(all_rows),
        "russell_archive_rows": len(russell),
        "excluded_dates": sorted(EXCLUDED_DATES),
        "reference_rows": len(reference),
        "reference_first_date": min(d for d in by_date if d not in EXCLUDED_DATES),
        "reference_last_date": max(d for d in by_date if d not in EXCLUDED_DATES),
        "historical_rows_are_signal_eligible": False,
        "baseline_git_blob_sha": EXPECTED_BASELINE_BLOB,
        "manifest_git_blob_sha": EXPECTED_MANIFEST_BLOB,
        "knowledge_bound_utc": KNOWLEDGE_BOUND.isoformat().replace("+00:00", "Z"),
    }


def prospective_russell_events(events_dir: Path = EVENTS) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for path in sorted(events_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("dataset_id") != "gpe5-46if":
            raise ValueError(f"unexpected CFTC dataset in {path.name}")
        if payload.get("capture_mode") != "scheduled":
            continue
        for event in payload.get("events", []):
            if event.get("contract_code") != CONTRACT_CODE:
                continue
            if event.get("event_type") != "new_report" or event.get("research_observation_eligible") is not True:
                continue
            if event.get("signal_eligible") is not False or event.get("trade_signal_generated") is not False:
                raise ValueError("prospective event unexpectedly carries signal eligibility")
            if event.get("historical_backfill_derived_features_included") is not False:
                raise ValueError("event contains prohibited archive-derived features")

            first_seen = parse_utc(event.get("first_seen_utc", ""))
            if first_seen <= KNOWLEDGE_BOUND:
                raise ValueError("prospective event predates the frozen-reference knowledge bound")

            source_row = event.get("source_row")
            if not isinstance(source_row, dict):
                raise ValueError("prospective event has no raw source_row")
            if source_row.get("cftc_contract_market_code") != CONTRACT_CODE:
                raise ValueError("event/source-row contract mismatch")
            source_date = str(source_row.get("report_date_as_yyyy_mm_dd", ""))[:10]
            if source_date != event.get("report_date"):
                raise ValueError("event/source-row report-date mismatch")
            if event.get("current_row_sha256") != digest(source_row):
                raise ValueError("prospective raw source-row hash mismatch")

            oi = check_oi(source_row)
            lm_long = num(source_row.get("lev_money_positions_long"))
            lm_short = num(source_row.get("lev_money_positions_short"))
            lm_net_oi = (lm_long - lm_short) / oi
            events.append({
                "event_file": path.name,
                "report_date": source_date,
                "first_seen_utc": first_seen.isoformat().replace("+00:00", "Z"),
                "source_row_sha256": event["current_row_sha256"],
                "open_interest": int(oi),
                "leveraged_money_net_oi": format(lm_net_oi, "f"),
            })

    events.sort(key=lambda item: (item["first_seen_utc"], item["report_date"]))
    seen_dates: set[str] = set()
    previous_report_date = ""
    previous_first_seen = ""
    for event in events:
        if event["report_date"] in seen_dates:
            raise ValueError(f"duplicate prospective Russell report date: {event['report_date']}")
        seen_dates.add(event["report_date"])
        if previous_report_date and event["report_date"] <= previous_report_date:
            raise ValueError("prospective report dates are not strictly increasing")
        if previous_first_seen and event["first_seen_utc"] <= previous_first_seen:
            raise ValueError("prospective first-seen timestamps are not strictly increasing")
        previous_report_date = event["report_date"]
        previous_first_seen = event["first_seen_utc"]
    return events


def midrank_percentile(reference: list[Decimal], value: Decimal) -> Decimal:
    if not reference:
        raise ValueError("empty reference distribution")
    less = sum(item < value for item in reference)
    equal = sum(item == value for item in reference)
    return (Decimal(less) + Decimal(equal) / Decimal(2)) / Decimal(len(reference))


def build_report(baseline_path: Path = BASELINE,
                 manifest_path: Path = MANIFEST,
                 events_dir: Path = EVENTS) -> dict[str, Any]:
    reference, reference_audit = load_reference(baseline_path, manifest_path)
    events = prospective_russell_events(events_dir)
    results = []
    for event in events:
        value = Decimal(event["leveraged_money_net_oi"])
        percentile = midrank_percentile(reference, value)
        event["leveraged_money_net_oi"] = float(value)
        results.append({
            **event,
            "reference_percentile": float(percentile),
            "high_lm_crowding": percentile >= HIGH_THRESHOLD,
        })
    return {
        "phase": 648,
        "source": "CFTC TFF Futures Only / CME Russell E-mini",
        "contract_code": CONTRACT_CODE,
        "feature": "Leveraged Money net positions / total open interest",
        "reference_audit": reference_audit,
        "fixed_threshold": {"operator": ">=", "percentile": 0.80},
        "prospective_events": results,
        "prospective_event_count": len(results),
        "outcomes_accessed": False,
        "price_data_accessed": False,
        "signals_admitted": 0,
        "f80_changed": False,
        "interpretation": "feature construction only; no predictive or economic claim",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, default=BASELINE)
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument("--events-dir", type=Path, default=EVENTS)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = build_report(args.baseline, args.manifest, args.events_dir)
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

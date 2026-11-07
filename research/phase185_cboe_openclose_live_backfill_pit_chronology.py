"""Phase 185: Cboe Open-Close live product versus historical backfill PIT chronology.

This is a deterministic, evidence-only contract audit. It does not download data,
contact vendors, buy data, calculate returns, access a holdout, or change production.
"""
from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

DEFAULT_INPUT = Path(__file__).with_name("phase185_cboe_openclose_live_backfill_pit_chronology.json")
EXPECTED_VENUES = {"C1", "C2", "BZX", "EDGX"}
EXPECTED_PRODUCT_FLOORS = {"10m": "2020-08-03", "1m": "2025-07-13"}
EXPECTED_LATENCY = {"10m": (0, 5), "1m": (2, 5)}


def _date(value: str) -> date:
    return date.fromisoformat(value)


def audit(snapshot: dict) -> dict:
    if snapshot.get("phase") != 185:
        raise ValueError("wrong phase")
    rows = snapshot["venue_interval_rows"]
    if len(rows) != 8:
        raise ValueError("expected exactly eight venue/interval rows")
    keys = [(row["venue"], row["interval"]) for row in rows]
    if len(keys) != len(set(keys)):
        raise ValueError("duplicate venue/interval row")
    if {venue for venue, _ in keys} != EXPECTED_VENUES:
        raise ValueError("venue coverage mismatch")
    if {interval for _, interval in keys} != {"10m", "1m"}:
        raise ValueError("interval coverage mismatch")

    audited = []
    for row in rows:
        venue, interval = row["venue"], row["interval"]
        if venue not in EXPECTED_VENUES:
            raise ValueError(f"unsupported venue: {venue}")
        if interval not in EXPECTED_PRODUCT_FLOORS:
            raise ValueError(f"unsupported interval: {interval}")
        product_floor = EXPECTED_PRODUCT_FLOORS[interval]
        if row["product_not_before"] != product_floor:
            raise ValueError(f"product chronology mismatch for {venue}/{interval}")
        if interval == "1m":
            if row.get("operative_delay_days") != 30:
                raise ValueError(f"one-minute operative delay mismatch for {venue}")
            if row.get("first_possible_regular_trading_session") != "2025-07-14":
                raise ValueError(f"one-minute first-session mismatch for {venue}")
            if row.get("actual_first_delivery_verified") is not False:
                raise ValueError(f"one-minute first delivery must remain unverified for {venue}")
        archive_start = row["archive_start_current_page"]
        if _date(archive_start) >= _date(product_floor):
            raise ValueError(f"archive start must precede live product floor for {venue}/{interval}")
        if not row["prelaunch_archive_is_retrospective"]:
            raise ValueError(f"prelaunch archive cannot be marked contemporaneous: {venue}/{interval}")
        if row["strict_pit_admitted"]:
            raise ValueError("no historical row may be PIT-admitted without actual receipt evidence")
        if not row["actual_first_receipt_log_required"]:
            raise ValueError("actual first-receipt log is mandatory")
        if not row["cumulative_snapshot"]:
            raise ValueError("intraday snapshots must remain cumulative")
        expected_min, expected_max = EXPECTED_LATENCY[interval]
        if (row["latency_min_minutes"], row["latency_max_minutes"]) != (expected_min, expected_max):
            raise ValueError(f"latency envelope mismatch for {venue}/{interval}")
        if not row["source_refs"]:
            raise ValueError(f"missing source references for {venue}/{interval}")
        audited.append({
            "venue": venue,
            "interval": interval,
            "archive_start_current_page": archive_start,
            "product_not_before": product_floor,
            "prelaunch_archive_is_retrospective": True,
            "latency_minutes": [expected_min, expected_max],
            "cumulative_snapshot": True,
            "strict_pit_admitted": False,
            "actual_first_receipt_log_required": True
        })

    # Preserve the original 2020 launch announcement's archive-start snapshot
    # separately from the current DataShop page; do not silently overwrite either.
    c1_10m = next(x for x in rows if x["venue"] == "C1" and x["interval"] == "10m")
    if c1_10m["archive_start_at_2020_launch_announcement"] != "2019-10-01":
        raise ValueError("C1 original 10-minute launch archive floor changed")
    other_10m = [x for x in rows if x["interval"] == "10m" and x["venue"] != "C1"]
    if any(x["archive_start_at_2020_launch_announcement"] != "2020-01-01" for x in other_10m):
        raise ValueError("non-C1 original 10-minute launch archive floor changed")

    eod = snapshot["eod_delivery"]
    if eod["typical_window_is_guaranteed"] or not eod["actual_first_receipt_log_required"]:
        raise ValueError("EOD schedule must not be treated as guaranteed first receipt")
    if eod["same_day_close_entry_allowed_from_eod_file"]:
        raise ValueError("EOD file cannot justify same-day close execution")

    sample = snapshot["schema_sample"]
    if sample["v18_effective_date"] != "2026-11-08":
        raise ValueError("unexpected v1.8 effective date")
    if sample["sample_is_production_delivery_evidence"] or sample["sample_is_historical_first_receipt_evidence"]:
        raise ValueError("public format sample is not production or receipt evidence")

    semantics = snapshot["global_semantics"]
    if not semantics["snapshots_are_cumulative"] or semantics["first_difference_is_trade_time_interval_volume"]:
        raise ValueError("cumulative snapshot semantics were weakened")
    if semantics["capacity_is_beneficial_owner_identity"] or semantics["all_opra_coverage"]:
        raise ValueError("participant/venue scope was overstated")

    decisions = snapshot["decisions"]
    required_false = (
        "alpha_test_authorized", "holdout_used", "vendor_contact",
        "data_purchase", "production_changed"
    )
    if any(decisions[name] for name in required_false):
        raise ValueError("scope/control violation")
    if not decisions["f80_frozen"] or decisions["pit_admitted_rows"] != 0:
        raise ValueError("baseline/PIT control violation")
    if decisions["ten_minute_strict_pit_start_confirmed"] is not None:
        raise ValueError("10-minute strict PIT start cannot be confirmed without receipt logs")
    if decisions["one_minute_strict_pit_start_confirmed"] is not None:
        raise ValueError("1-minute strict PIT start cannot be confirmed without receipt logs")

    audited.sort(key=lambda x: (x["interval"], x["venue"]))
    return {
        "phase": 185,
        "audit_date": snapshot["audit_date"],
        "status": "BACKFILL_PRELAUNCH_RETROSPECTIVE_NO_HISTORICAL_STRICT_PIT_ADMITTED",
        "venue_interval_rows": len(audited),
        "prelaunch_backfill_rows": sum(x["prelaunch_archive_is_retrospective"] for x in audited),
        "strict_pit_admitted_rows": 0,
        "product_not_before": EXPECTED_PRODUCT_FLOORS,
        "one_minute_first_possible_regular_session": "2025-07-14",
        "strict_pit_start_confirmed": {"10m": None, "1m": None},
        "reason": "Historical archive start dates predate documented live product introduction; actual first-receipt/vintage logs are absent.",
        "rows": audited,
        "eod_delivery": {
            "typical_next_day_window": "00:05-03:00 ET",
            "may_be_delayed_until_after_open": True,
            "actual_receipt_required": True,
            "same_day_close_execution_from_eod": False
        },
        "controls": {
            "f80_frozen": True,
            "holdout_used": False,
            "vendor_contact": False,
            "data_purchase": False,
            "production_changed": False,
            "alpha_test_authorized": False
        }
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=Path("phase185_output/phase185_cboe_openclose_pit_audit.json"))
    args = parser.parse_args()
    snapshot = json.loads(args.input.read_text(encoding="utf-8"))
    result = audit(snapshot)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

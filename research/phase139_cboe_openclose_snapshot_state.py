#!/usr/bin/env python3
"""PIT-safe comparison of cumulative Cboe Open-Close snapshots."""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SHA256 = re.compile(r"^[0-9a-f]{64}$")
EXCHANGES = {"C1", "C2", "BZX", "EDGX"}
INTERVALS = {1, 10}
CAPTURE_MODES = {"LIVE_FIRST_RECEIPT", "ARCHIVE_BACKFILL"}
IDENTITY = (
    "market_date", "trading_dt", "exchange", "interval_minutes",
    "trading_segment", "schema_version", "contract_map_version",
)


class SnapshotValidationError(ValueError):
    pass


def _text(obj: dict[str, Any], field: str) -> str:
    value = obj.get(field)
    if not isinstance(value, str) or not value.strip():
        raise SnapshotValidationError(f"{field}_missing")
    return value.strip()


def _utc(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise SnapshotValidationError(f"{field}_missing")
    raw = value.strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError as exc:
        raise SnapshotValidationError(f"{field}_invalid_iso8601") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise SnapshotValidationError(f"{field}_timezone_required")
    return parsed.astimezone(timezone.utc)


def validate_snapshot(obj: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(obj, dict):
        raise SnapshotValidationError("snapshot_not_object")

    market_date, trading_dt = _text(obj, "market_date"), _text(obj, "trading_dt")
    for name, value in (("market_date", market_date), ("trading_dt", trading_dt)):
        try:
            datetime.strptime(value, "%Y-%m-%d")
        except ValueError as exc:
            raise SnapshotValidationError(f"{name}_invalid") from exc

    exchange = _text(obj, "exchange").upper()
    if exchange not in EXCHANGES:
        raise SnapshotValidationError("exchange_unsupported")
    interval = obj.get("interval_minutes")
    if isinstance(interval, bool) or interval not in INTERVALS:
        raise SnapshotValidationError("interval_minutes_unsupported")

    segment = obj.get("trading_segment")
    if exchange == "C1":
        if isinstance(segment, bool) or not isinstance(segment, int) or segment not in {1, 2}:
            raise SnapshotValidationError("c1_trading_segment_must_be_1_or_2")
    elif segment is not None:
        raise SnapshotValidationError("non_c1_trading_segment_must_be_null")

    schema = _text(obj, "schema_version")
    contract_map = _text(obj, "contract_map_version")
    _text(obj, "source_file_id")
    mode = _text(obj, "capture_mode").upper()
    if mode not in CAPTURE_MODES:
        raise SnapshotValidationError("capture_mode_unsupported")

    snapshot_at = _utc(obj.get("snapshot_at_utc"), "snapshot_at_utc")
    received_at = _utc(obj.get("first_received_at_utc"), "first_received_at_utc")
    if received_at < snapshot_at:
        raise SnapshotValidationError("received_before_snapshot")

    digest = _text(obj, "raw_file_sha256").lower()
    if not SHA256.fullmatch(digest):
        raise SnapshotValidationError("raw_file_sha256_invalid")

    rows = obj.get("rows")
    if not isinstance(rows, list) or not rows:
        raise SnapshotValidationError("rows_missing_or_empty")
    normalized: dict[str, dict[str, int | None]] = {}
    for i, row in enumerate(rows):
        if not isinstance(row, dict):
            raise SnapshotValidationError(f"row_{i}_not_object")
        key = row.get("series_key")
        if not isinstance(key, str) or not key.strip():
            raise SnapshotValidationError(f"row_{i}_series_key_missing")
        key = key.strip()
        if key in normalized:
            raise SnapshotValidationError(f"duplicate_series_key:{key}")
        values = row.get("values")
        if not isinstance(values, dict) or not values:
            raise SnapshotValidationError(f"row_{i}_values_missing")
        normalized[key] = {}
        for metric, value in values.items():
            if not isinstance(metric, str) or not metric.strip():
                raise SnapshotValidationError(f"row_{i}_metric_name_invalid")
            if value is None or value == "":
                normalized[key][metric.strip()] = None
            elif isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise SnapshotValidationError(f"row_{i}_metric_invalid:{metric}")
            else:
                normalized[key][metric.strip()] = value

    return {
        "market_date": market_date, "trading_dt": trading_dt,
        "exchange": exchange, "interval_minutes": interval,
        "trading_segment": segment, "schema_version": schema,
        "contract_map_version": contract_map, "capture_mode": mode,
        "snapshot_at": snapshot_at, "received_at": received_at,
        "raw_file_sha256": digest, "rows": normalized,
    }


def compare_snapshots(earlier: dict[str, Any], later: dict[str, Any]) -> dict[str, Any]:
    """Return published-state differences, never inferred interval trade volume."""
    old, new = validate_snapshot(earlier), validate_snapshot(later)
    mismatch = [field for field in IDENTITY if old[field] != new[field]]
    if mismatch:
        raise SnapshotValidationError("snapshot_identity_mismatch:" + ",".join(mismatch))
    if new["received_at"] < old["received_at"]:
        raise SnapshotValidationError("knowledge_time_not_monotonic")
    if new["snapshot_at"] < old["snapshot_at"]:
        raise SnapshotValidationError("snapshot_time_not_increasing")
    if new["snapshot_at"] == old["snapshot_at"]:
        same = new["raw_file_sha256"] == old["raw_file_sha256"]
        return {
            "status": "DUPLICATE_SNAPSHOT" if same else "SAME_CUTOFF_REVISION",
            "strict_pit_pair": False, "deltas": [],
            "same_cutoff_revision": not same,
            "revision_requires_separate_state_replay": not same,
        }

    old_keys, new_keys = set(old["rows"]), set(new["rows"])
    common = sorted(old_keys & new_keys)
    deltas, missing = [], 0
    for key in common:
        before, after = old["rows"][key], new["rows"][key]
        missing += len(set(before) ^ set(after))
        for metric in sorted(set(before) & set(after)):
            a, b = before[metric], after[metric]
            if a is None or b is None:
                missing += 1
                continue
            delta = b - a
            deltas.append({
                "series_key": key, "metric": metric,
                "reported_increment": delta, "is_correction": delta < 0,
                "is_positive_reported_increment": delta > 0,
            })

    live_pair = old["capture_mode"] == new["capture_mode"] == "LIVE_FIRST_RECEIPT"
    return {
        "status": "PIT_CAPTURE_PAIR" if live_pair else "ARCHIVE_BACKFILL_NOT_PIT",
        "strict_pit_pair": live_pair,
        **{field: old[field] for field in IDENTITY},
        "earlier_snapshot_at_utc": old["snapshot_at"].isoformat(),
        "later_snapshot_at_utc": new["snapshot_at"].isoformat(),
        "earlier_knowledge_time_utc": old["received_at"].isoformat(),
        "later_knowledge_time_utc": new["received_at"].isoformat(),
        "earlier_sha256": old["raw_file_sha256"], "later_sha256": new["raw_file_sha256"],
        "common_series_count": len(common),
        "new_series_without_prior_baseline": sorted(new_keys - old_keys),
        "removed_series_without_zero_assumption": sorted(old_keys - new_keys),
        "missing_metric_pairs": missing, "deltas": deltas,
        "negative_correction_count": sum(x["is_correction"] for x in deltas),
        "positive_reported_increment_count": sum(x["is_positive_reported_increment"] for x in deltas),
        "economic_interpretation": (
            "change_in_published_cumulative_aggregate_since_prior_received_snapshot; "
            "not_trade_time_interval_volume; may include late-reported trades and corrections"
        ),
        "alpha_admission": "BLOCKED_UNTIL_UNIVERSE_IDENTITY_COVERAGE_AND_COST_GATES_PASS",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--earlier", required=True)
    parser.add_argument("--later", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = compare_snapshots(
        json.loads(Path(args.earlier).read_text(encoding="utf-8")),
        json.loads(Path(args.later).read_text(encoding="utf-8")),
    )
    Path(args.output).write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] in {"PIT_CAPTURE_PAIR", "ARCHIVE_BACKFILL_NOT_PIT"} else 2


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Reproduce Phase 117 FINRA ATS/OTC revision-impact metrics from a Phase 109 ZIP artifact."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import zipfile
from collections import defaultdict
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

AGGREGATE_TYPES = {"ATS_W_SMBL", "OTC_W_SMBL"}
EXPECTED_RAW_GZIP_SHA256 = "45b6b169c1d57a1874438362295a656c5bc6499b2c29d6e3be8bd10a48425231"


def _date(value: str) -> date:
    return date.fromisoformat(value)


def audit_rows(rows: list[dict[str, str]]) -> dict[str, Any]:
    aggregates = [r for r in rows if r.get("summaryTypeCode") in AGGREGATE_TYPES]
    if not aggregates:
        raise ValueError("No symbol-aggregate rows found")

    revised_total = 0
    date_rule_mismatches = 0
    revised_lags: dict[str, list[int]] = defaultdict(list)
    revised_weeks: set[str] = set()
    totals = defaultdict(lambda: {
        "rows": 0, "revised_rows": 0, "symbols": set(), "unrevised_symbols": set(),
        "shares": 0, "unrevised_shares": 0, "trades": 0, "unrevised_trades": 0,
    })

    for row in aggregates:
        tier = row["tierIdentifier"]
        family = row["summaryTypeCode"].split("_", 1)[0]
        initial = _date(row["initialPublishedDate"])
        last_reported = _date(row["lastReportedDate"])
        last_update = _date(row["lastUpdateDate"])
        expected_update = max(initial, last_reported)
        if last_update != expected_update:
            date_rule_mismatches += 1

        revised = last_update > initial
        shares_decimal = Decimal(row["totalWeeklyShareQuantity"])
        trades_decimal = Decimal(row["totalWeeklyTradeCount"])
        if shares_decimal != shares_decimal.to_integral_value() or trades_decimal != trades_decimal.to_integral_value():
            raise ValueError("Non-integer share quantity or trade count")
        shares = int(shares_decimal)
        trades = int(trades_decimal)
        symbol = row["issueSymbolIdentifier"]

        bucket = totals[(tier, family)]
        bucket["rows"] += 1
        bucket["shares"] += shares
        bucket["trades"] += trades
        if symbol:
            bucket["symbols"].add(symbol)

        if revised:
            revised_total += 1
            lag = (last_update - initial).days
            revised_lags[tier].append(lag)
            revised_weeks.add(row["weekStartDate"])
            bucket["revised_rows"] += 1
        else:
            bucket["unrevised_shares"] += shares
            bucket["unrevised_trades"] += trades
            if symbol:
                bucket["unrevised_symbols"].add(symbol)

    output: dict[str, Any] = {
        "aggregate_rows": len(aggregates),
        "revised_rows": revised_total,
        "revised_share": revised_total / len(aggregates),
        "unrevised_rows": len(aggregates) - revised_total,
        "date_rule_mismatches": date_rule_mismatches,
        "weeks_with_revisions": sorted(revised_weeks),
        "by_tier_family": {},
        "by_tier": {},
        "overall": {},
        "revision_lag_days": {},
    }

    for (tier, family), b in sorted(totals.items()):
        rows_n = b["rows"]
        revised_n = b["revised_rows"]
        output["by_tier_family"][f"{tier}_{family}"] = {
            "rows": rows_n,
            "revised_rows": revised_n,
            "revised_pct": revised_n / rows_n,
            "unrevised_rows": rows_n - revised_n,
            "unique_symbols_nonblank": len(b["symbols"]),
            "unrevised_symbols_nonblank": len(b["unrevised_symbols"]),
            "symbols_lost_entirely_if_future_revision_status_used": len(b["symbols"] - b["unrevised_symbols"]),
            "shares_total": b["shares"],
            "shares_unrevised": b["unrevised_shares"],
            "share_volume_retained_if_revised_rows_dropped": (
                b["unrevised_shares"] / b["shares"] if b["shares"] else None
            ),
            "trades_total": b["trades"],
            "trades_unrevised": b["unrevised_trades"],
            "trade_count_retained_if_revised_rows_dropped": (
                b["unrevised_trades"] / b["trades"] if b["trades"] else None
            ),
        }

    for tier in sorted({k[0] for k in totals}):
        tier_buckets = [b for (t, _), b in totals.items() if t == tier]
        rows_n = sum(b["rows"] for b in tier_buckets)
        revised_n = sum(b["revised_rows"] for b in tier_buckets)
        shares = sum(b["shares"] for b in tier_buckets)
        unrev_shares = sum(b["unrevised_shares"] for b in tier_buckets)
        trades = sum(b["trades"] for b in tier_buckets)
        unrev_trades = sum(b["unrevised_trades"] for b in tier_buckets)
        output["by_tier"][tier] = {
            "rows": rows_n,
            "revised_rows": revised_n,
            "revised_pct": revised_n / rows_n,
            "row_retained_if_revised_rows_dropped": (rows_n - revised_n) / rows_n,
            "share_volume_retained_if_revised_rows_dropped": unrev_shares / shares if shares else None,
            "trade_count_retained_if_revised_rows_dropped": unrev_trades / trades if trades else None,
        }

    rows_n = len(aggregates)
    shares = sum(b["shares"] for b in totals.values())
    unrev_shares = sum(b["unrevised_shares"] for b in totals.values())
    trades = sum(b["trades"] for b in totals.values())
    unrev_trades = sum(b["unrevised_trades"] for b in totals.values())
    output["overall"] = {
        "row_retained_if_revised_rows_dropped": (rows_n - revised_total) / rows_n,
        "share_volume_total": shares,
        "share_volume_unrevised": unrev_shares,
        "share_volume_retained_if_revised_rows_dropped": unrev_shares / shares,
        "trade_count_total": trades,
        "trade_count_unrevised": unrev_trades,
        "trade_count_retained_if_revised_rows_dropped": unrev_trades / trades,
    }

    for tier, lags in sorted(revised_lags.items()):
        ordered = sorted(lags)

        def quantile(p: float) -> float:
            pos = (len(ordered) - 1) * p
            lo = int(pos)
            hi = min(lo + 1, len(ordered) - 1)
            frac = pos - lo
            return ordered[lo] * (1 - frac) + ordered[hi] * frac

        output["revision_lag_days"][tier] = {
            "count": len(ordered),
            "median": quantile(0.5),
            "p90": quantile(0.9),
            "p95": quantile(0.95),
            "max": max(ordered),
        }

    return output


def audit_zip(path: str | Path, expected_sha256: str = EXPECTED_RAW_GZIP_SHA256) -> dict[str, Any]:
    with zipfile.ZipFile(path) as archive:
        raw_gzip = archive.read("raw_rows.csv.gz")
    actual_sha256 = hashlib.sha256(raw_gzip).hexdigest()
    if expected_sha256 and actual_sha256 != expected_sha256:
        raise ValueError(f"raw_rows.csv.gz SHA-256 mismatch: {actual_sha256}")
    with gzip.GzipFile(fileobj=io.BytesIO(raw_gzip)) as stream:
        text = io.TextIOWrapper(stream, encoding="utf-8", newline="")
        rows = list(csv.DictReader(text))
    result = audit_rows(rows)
    result["input_raw_gzip_sha256"] = actual_sha256
    result["raw_rows"] = len(rows)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact_zip")
    parser.add_argument("--output", default="phase117_finra_pit_revision_impact.json")
    parser.add_argument("--expected-raw-sha256", default=EXPECTED_RAW_GZIP_SHA256)
    args = parser.parse_args()
    result = audit_zip(args.artifact_zip, args.expected_raw_sha256)
    Path(args.output).write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

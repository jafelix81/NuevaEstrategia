#!/usr/bin/env python3
"""Phase 375: exhaustive weekly FINRA T1 ATS revision-stability audit.

Retrieves every T1 weekly partition in the four-year historic inventory
(2021-11-15 through 2025-11-10; expected 209 consecutive weeks). Reuses the
Phase 371 pagination/metadata code and Phase 374 symbol-week bridge/revision
logic. Computes only anonymized counts and descriptive concentration summaries.

This is not exact intraday PIT proof: initialPublishedDate is date-only and
intermediate row vintages are unavailable. No returns, alpha, OOS, bootstrap,
LOO or holdout tests are run. No raw rows or participant/symbol identifiers
are written to disk or logs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import date, datetime, timezone
from pathlib import Path

import requests

import research.phase371_finra_t1_ats_monthly_coverage_audit as P371
from research.phase374_finra_t1_ats_revision_stable_symbol_panel import (
    analyze_revision_stable_symbols,
)

EXPECTED_WEEKS = 209
EXPECTED_FIRST = date(2021, 11, 15)
EXPECTED_LAST = date(2025, 11, 10)
TIER = "T1"


def validate_weekly_anchors(weeks):
    parsed = sorted(date.fromisoformat(str(w)[:10]) for w in weeks)
    duplicates = len(parsed) - len(set(parsed))
    gaps = []
    for left, right in zip(parsed, parsed[1:]):
        if (right - left).days != 7:
            gaps.append({"left": left.isoformat(), "right": right.isoformat(),
                         "gap_days": (right-left).days})
    return {
        "count": len(parsed),
        "first": parsed[0].isoformat() if parsed else None,
        "last": parsed[-1].isoformat() if parsed else None,
        "duplicates": duplicates,
        "nonweekly_gaps": gaps,
        "consecutive": bool(parsed) and duplicates == 0 and not gaps
            and parsed[0] == EXPECTED_FIRST and parsed[-1] == EXPECTED_LAST
            and len(parsed) == EXPECTED_WEEKS,
    }


def hash_key(value):
    return hashlib.sha256(str(value).strip().upper().encode("utf-8")).hexdigest()


def summarize_partitions(partitions, unique_symbol_hashes, unique_participant_hashes):
    bridge_total = sum(x["bridge_mapped_symbols"] for x in partitions)
    stable_concentration_total = sum(x["revision_stable_concentration_symbols"] for x in partitions)
    mapped_shares = sum(x["total_aggregate_shares_mapped"] for x in partitions)
    stable_shares = sum(x["revision_stable_concentration_shares"] for x in partitions)
    symbol_groups = sum(x["union_symbols"] for x in partitions)
    stable_groups = sum(x["revision_stable_symbols"] for x in partitions)
    revised_groups = sum(x["revised_symbols"] for x in partitions)
    return {
        "weeks_completed": len(partitions),
        "total_rows": sum(x["rows"] for x in partitions),
        "total_pages": sum(x["pages"] for x in partitions),
        "aggregate_symbol_week_groups": symbol_groups,
        "revision_stable_symbol_week_groups": stable_groups,
        "revised_symbol_week_groups": revised_groups,
        "revision_stable_concentration_symbol_week_groups": stable_concentration_total,
        "symbol_week_bridge_mapped": bridge_total,
        "revision_stable_concentration_symbol_coverage_pct": round(
            100 * stable_concentration_total / bridge_total, 6
        ) if bridge_total else None,
        "mapped_aggregate_shares": mapped_shares,
        "revision_stable_concentration_shares": stable_shares,
        "revision_stable_share_volume_coverage_pct": round(
            100 * stable_shares / mapped_shares, 6
        ) if mapped_shares else None,
        "weeks_with_any_revised_symbol": sum(1 for x in partitions if x["revised_symbols"] > 0),
        "weeks_with_schedule_review": sum(
            1 for x in partitions if x["publication_schedule_review_symbols"] > 0
        ),
        "weeks_with_symbol_bridge_failure": sum(
            1 for x in partitions if x["symbol_bridge_gate"] != "PASS"
        ),
        "weeks_with_concentration_gate_failure": sum(
            1 for x in partitions if x["stable_concentration_gate"] != "PASS"
        ),
        "unique_symbols_union_count": len(unique_symbol_hashes),
        "unique_participant_keys_union_count": len(unique_participant_hashes),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="phase375_finra_t1_ats_full_weekly_revision_audit")
    args = parser.parse_args()
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers.update({
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Data-API-Version": "1",
        "User-Agent": "SmartMoneyResearch-Phase375/1.0",
    })
    token = os.getenv("FINRA_API_TOKEN", "").strip()
    if token:
        session.headers["Authorization"] = f"Bearer {token}"

    metadata, _ = P371.request_json(session, P371.META_URL)
    partition_payload, _ = P371.request_json(session, P371.PARTITIONS_URL)
    fields, raw_partition_records, unique = P371.parse_partition_payload(
        partition_payload, metadata.get("partitionFields") or P371.EXPECTED_PARTITION_FIELDS
    )
    if tuple(metadata.get("partitionFields") or fields) != P371.EXPECTED_PARTITION_FIELDS:
        raise RuntimeError("FINRA partition field order differs from expected week/tier schema")

    weeks = sorted({
        str(row["weekStartDate"])[:10]
        for row in unique
        if row.get("tierIdentifier") == TIER
    })
    inventory = validate_weekly_anchors(weeks)
    if not inventory["consecutive"]:
        raise RuntimeError(
            "T1 historical inventory failed the 209-week consecutive-anchor gate: "
            + json.dumps(inventory, sort_keys=True)
        )

    partitions = []
    errors = []
    symbol_hashes = set()
    participant_hashes = set()
    for index, week in enumerate(weeks, start=1):
        try:
            rows, total, pages = P371.fetch_partition(session, week)
            part = analyze_revision_stable_symbols(rows, week, total, pages)
            if not part["retrieval_count_match"]:
                raise RuntimeError("Record-Total mismatch after pagination")
            for row in rows:
                typ = P371.norm(row.get("summaryTypeCode"))
                symbol = P371.norm(row.get("issueSymbolIdentifier"))
                if typ == "ATS_W_SMBL" and symbol:
                    symbol_hashes.add(hash_key(symbol))
                elif typ == "ATS_W_SMBL_FIRM":
                    key = P371.participant_key(row)
                    if key:
                        participant_hashes.add(hash_key(key))
            partitions.append(part)
            print(
                f"WEEK={index}/{len(weeks)}|DATE={week}|ROWS={part['rows']}|"
                f"SYMBOLS={part['union_symbols']}|STABLE={part['revision_stable_concentration_symbols']}|"
                f"REVISED={part['revised_symbols']}|BRIDGE={part['symbol_bridge_gate']}|"
                f"CONCENTRATION={part['stable_concentration_gate']}",
                flush=True,
            )
            del rows
        except Exception as exc:
            errors.append({
                "week": week,
                "error_type": type(exc).__name__,
                "error": str(exc)[:240],
            })
            print(f"WEEK_ERROR={week}|TYPE={type(exc).__name__}", flush=True)

    complete = (
        len(partitions) == len(weeks)
        and not errors
        and all(x["retrieval_count_match"] for x in partitions)
    )
    totals = summarize_partitions(partitions, symbol_hashes, participant_hashes)
    summary = {
        "phase": 375,
        "source": "FINRA OTCMarket weeklySummaryHistoric",
        "audit_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "partition_fields": list(fields),
        "raw_partition_records": len(raw_partition_records),
        "unique_partition_pairs": len(unique),
        "tier": TIER,
        "inventory": inventory,
        "expected_partitions": EXPECTED_WEEKS,
        "completed_partitions": len(partitions),
        "errors": errors,
        "all_partitions_complete": complete,
        "all_symbol_bridges_pass": complete and all(
            x["symbol_bridge_gate"] == "PASS" for x in partitions
        ),
        "all_stable_concentration_gates_pass": complete and all(
            x["stable_concentration_gate"] == "PASS" for x in partitions
        ),
        **totals,
        "pit_availability_established": False,
        "date_level_next_session_candidate_only": True,
        "historical_signal_test_authorized": False,
        "forward_returns_used": False,
        "holdout_used": False,
        "f80_changed": False,
        "production_changed": False,
        "raw_rows_retained": False,
        "raw_identifiers_retained": False,
        "participant_identity_count_scope": (
            "unique MPID/CRD-derived keys observed across all ATS_W_SMBL_FIRM rows; "
            "hashes existed only in memory; count includes revision-affected weeks"
        ),
        "publication_lag_policy": (
            "accept only 21/22 calendar-day lags as schedule-consistent; retain actual "
            "initialPublishedDate; no backdating and no intraday timestamp inferred"
        ),
        "revision_policy": (
            "exclude an entire symbol-week from concentration if any ATS_W_SMBL or "
            "ATS_W_SMBL_FIRM row has missing/invalid dates, a publication lag outside "
            "{21,22}, or lastUpdateDate != initialPublishedDate"
        ),
        "research_disposition": (
            "FULL_WEEKLY_T1_ATS_REVISION_STABLE_DIAGNOSTIC_ONLY"
            if complete else "FULL_WEEKLY_T1_ATS_INCOMPLETE_RETRIEVAL"
        ),
        "partitions": partitions,
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "partitions"}, indent=2), flush=True)
    if not complete:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

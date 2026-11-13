#!/usr/bin/env python3
"""Phase 361: extend FINRA firm-to-symbol reconciliation to five historical weeks.

Reuses the tested Phase 360 bridge logic and the Phase 359 retrieval/pagination
client. The five weeks match the earlier Phase 107 coverage sample, adding
2023-01-09, 2024-01-08 and especially 2025-01-06/T2, where Phase 107 reported
conflicting LND aggregate keys.

This is a data-grain/accounting audit only. No returns, signal, alpha, holdout,
or F80 changes.
"""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import requests

from research.phase359_finra_product_key_diagnostic import TIERS, fetch_partition
from research.phase360_finra_symbol_bridge import audit_partition

WEEKS = (
    "2022-01-03",
    "2023-01-09",
    "2024-01-08",
    "2025-01-06",
    "2025-10-20",
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="phase361_finra_five_week_bridge")
    args = parser.parse_args()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers.update({
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "SmartMoneyResearch-Phase361/1.0",
    })
    token = os.getenv("FINRA_API_TOKEN", "").strip()
    if token:
        session.headers["Authorization"] = f"Bearer {token}"

    partitions = []
    page_hashes = []
    request_errors = []
    total_rows = 0
    for week in WEEKS:
        for tier in TIERS:
            print(f"[Phase361] start {week}/{tier}", flush=True)
            try:
                rows, pages = fetch_partition(session, week, tier)
                result = audit_partition(rows, week, tier)
                result["api_record_total"] = pages[0]["record_total"] if pages else 0
                result["api_records_retrieved"] = len(rows)
                result["api_record_total_match"] = result["api_record_total"] == len(rows)
                partitions.append(result)
                page_hashes.extend(pages)
                total_rows += len(rows)
                print(
                    f"[Phase361] complete {week}/{tier}: rows={len(rows)} "
                    f"status={result['partition_status']}",
                    flush=True,
                )
            except Exception as exc:
                request_errors.append({"week": week, "tier": tier, "error": repr(exc)})

    all_pairs = [
        (p["week"], p["tier"], family, pair)
        for p in partitions
        for family, pair in p.get("pairs", {}).items()
    ]
    lnd_cases = []
    duplicate_key_count = 0
    for week, tier, family, pair in all_pairs:
        duplicate_key_count += pair.get("duplicate_aggregate_symbol_rows", 0)
        for example in pair.get("ambiguous_symbol_examples", []):
            if example.get("symbol") == "LND":
                lnd_cases.append({
                    "week": week,
                    "tier": tier,
                    "family": family,
                    "reason": example.get("reason"),
                    "aggregate_row_count": example.get("aggregate_row_count"),
                    "product_types": example.get("product_types"),
                })

    retrieval_gate = (
        "PASS" if len(partitions) == len(WEEKS) * len(TIERS)
        and not request_errors
        and all(p.get("api_record_total_match") for p in partitions)
        else "FAIL_OR_REVIEW"
    )
    overall_data_gate = (
        "FAIL_OR_REVIEW"
        if retrieval_gate != "PASS" or not all_pairs
        or any(pair.get("data_gate") == "FAIL_OR_REVIEW" for _, _, _, pair in all_pairs)
        else (
            "PASS_WITH_EXCLUSIONS"
            if any(pair.get("data_gate") == "PASS_WITH_EXCLUSIONS" for _, _, _, pair in all_pairs)
            else "PASS"
        )
    )
    summary = {
        "phase": 361,
        "source": "FINRA OTCMarket weeklySummaryHistoric",
        "audit_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "sample_weeks": list(WEEKS),
        "tiers": list(TIERS),
        "partitions_expected": len(WEEKS) * len(TIERS),
        "partitions_completed": len(partitions),
        "rows_total": total_rows,
        "page_count": len(page_hashes),
        "request_errors": request_errors,
        "partitions": partitions,
        "all_partition_retrieval_counts_match": (
            len(partitions) == len(WEEKS) * len(TIERS)
            and all(p.get("api_record_total_match") for p in partitions)
        ),
        "retrieval_gate": retrieval_gate,
        "overall_data_gate": overall_data_gate,
        "duplicate_aggregate_symbol_product_keys_total": duplicate_key_count,
        "lnd_duplicate_cases": lnd_cases,
        "known_phase107_lnd_duplicate_reproduced": (
            any(x["week"] == "2025-01-06" and x["tier"] == "T2" and x["family"] == "ATS_W_SMBL" for x in lnd_cases)
            and any(x["week"] == "2025-01-06" and x["tier"] == "T2" and x["family"] == "OTC_W_SMBL" for x in lnd_cases)
        ),
        "pit_status": "FINAL_HISTORICAL_SNAPSHOT_ONLY; interim vintages unavailable",
        "economic_interpretation": (
            "Reporting intermediaries only; no beneficial-owner identity or trade direction. "
            "Non-ATS de-minimis rows remain censored aggregates."
        ),
        "forward_returns_used": False,
        "alpha_test_authorized": False,
        "holdout_used": False,
        "f80_changed": False,
    }
    (output / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (output / "page_hashes.json").write_text(json.dumps(page_hashes, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2), flush=True)
    print(
        f"[Phase361] complete retrieval={retrieval_gate} data={overall_data_gate} "
        f"rows={total_rows} duplicate_keys={duplicate_key_count} lnd_cases={len(lnd_cases)}",
        flush=True,
    )


if __name__ == "__main__":
    main()

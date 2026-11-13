#!/usr/bin/env python3
"""Phase 363: test lastReportedDate as a FINRA weekly-summary row-grain key.

Phase 362 found two LND aggregate rows per summary family in 2025-01-06/T2.
Both rows had distinct lastReportedDate values, and their combined arithmetic
matched firm rows. FINRA defines lastReportedDate as the last time a firm sent
an update contributing to the aggregate. This phase tests whether
(symbol,lastReportedDate), with a unique product type, is the correct bridge.

No duplicate rows are summed across dates unless each date-level group first
passes its own reconciliation. No returns, alpha, holdout, or F80 changes.
"""
from __future__ import annotations

import argparse
import json
import os
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import requests

from research.phase362_finra_lnd_duplicate_diagnostic import (
    WEEK, TIER, SYMBOL, AGG_TO_FIRM, as_nonnegative_int, fetch_partition, norm,
)


def participant_key(row, aggregate_type):
    mpid = norm(row.get("MPID"))
    crd = norm(row.get("firmCRDNumber"))
    name = norm(row.get("marketParticipantName"))
    if aggregate_type == "ATS_W_SMBL":
        key = mpid or crd
    else:
        key = crd or mpid
    if key:
        return ("MPID:" if key == mpid and mpid else "CRD:") + key
    if "DE MINIMIS" in name:
        return "DE_MINIMIS"
    return "NAME:" + name if name else ""


def audit_family(rows, aggregate_type):
    firm_type = AGG_TO_FIRM[aggregate_type]
    aggregates = [
        r for r in rows
        if norm(r.get("summaryTypeCode")) == aggregate_type
        and norm(r.get("issueSymbolIdentifier"))
    ]
    firms = [
        r for r in rows
        if norm(r.get("summaryTypeCode")) == firm_type
        and norm(r.get("issueSymbolIdentifier"))
    ]

    agg_by_key = defaultdict(list)
    firm_by_key = defaultdict(list)
    missing_aggregate_last_reported = 0
    missing_firm_last_reported = 0
    for row in aggregates:
        last_reported = str(row.get("lastReportedDate") or "").strip()
        if not last_reported:
            missing_aggregate_last_reported += 1
            continue
        agg_by_key[(norm(row.get("issueSymbolIdentifier")), last_reported)].append(row)
    for row in firms:
        last_reported = str(row.get("lastReportedDate") or "").strip()
        if not last_reported:
            missing_firm_last_reported += 1
            continue
        firm_by_key[(norm(row.get("issueSymbolIdentifier")), last_reported)].append(row)

    aggregate_keys = set(agg_by_key)
    firm_keys = set(firm_by_key)
    shared_keys = aggregate_keys & firm_keys
    aggregate_only = sorted(aggregate_keys - firm_keys)
    firm_only = sorted(firm_keys - aggregate_keys)

    duplicate_aggregate_date_keys = []
    multi_product_date_keys = []
    invalid_numeric_keys = []
    participant_duplicate_key_groups = []
    mismatches = []
    exact_matches = 0
    matched_groups = 0
    matched_shares = 0
    matched_trades = 0
    lnd_groups = []

    for key in sorted(shared_keys):
        symbol, last_reported = key
        agg_group = agg_by_key[key]
        firm_group = firm_by_key[key]
        products = sorted({norm(r.get("productTypeCode")) for r in agg_group if norm(r.get("productTypeCode"))})
        if len(agg_group) > 1:
            duplicate_aggregate_date_keys.append({
                "symbol": symbol, "lastReportedDate": last_reported,
                "aggregate_rows": len(agg_group), "product_types": products,
            })
        if len(products) != 1:
            multi_product_date_keys.append({
                "symbol": symbol, "lastReportedDate": last_reported,
                "product_types": products, "aggregate_rows": len(agg_group),
            })

        participant_counts = Counter(
            participant_key(r, aggregate_type) for r in firm_group
            if participant_key(r, aggregate_type)
        )
        duplicate_participants = sum(1 for n in participant_counts.values() if n > 1)
        if duplicate_participants:
            participant_duplicate_key_groups.append({
                "symbol": symbol, "lastReportedDate": last_reported,
                "duplicate_participant_keys": duplicate_participants,
            })

        if len(agg_group) != 1 or len(products) != 1:
            continue

        aggregate_row = agg_group[0]
        aggregate_shares = as_nonnegative_int(aggregate_row.get("totalWeeklyShareQuantity"))
        aggregate_trades = as_nonnegative_int(aggregate_row.get("totalWeeklyTradeCount"))
        firm_shares = [as_nonnegative_int(r.get("totalWeeklyShareQuantity")) for r in firm_group]
        firm_trades = [as_nonnegative_int(r.get("totalWeeklyTradeCount")) for r in firm_group]
        if (
            aggregate_shares is None or aggregate_trades is None
            or any(x is None for x in firm_shares)
            or any(x is None for x in firm_trades)
        ):
            invalid_numeric_keys.append({"symbol": symbol, "lastReportedDate": last_reported})
            continue

        sum_shares = sum(firm_shares)
        sum_trades = sum(firm_trades)
        matched_groups += 1
        matched_shares += aggregate_shares
        matched_trades += aggregate_trades
        is_match = sum_shares == aggregate_shares and sum_trades == aggregate_trades
        exact_matches += int(is_match)
        if not is_match:
            mismatches.append({
                "symbol": symbol, "lastReportedDate": last_reported,
                "aggregate_shares": aggregate_shares, "firm_shares": sum_shares,
                "aggregate_trades": aggregate_trades, "firm_trades": sum_trades,
            })
        if symbol == SYMBOL:
            lnd_groups.append({
                "lastReportedDate": last_reported,
                "aggregate_rows": len(agg_group),
                "product_types": products,
                "firm_rows": len(firm_group),
                "unique_participants": len(participant_counts),
                "duplicate_participant_key_groups": duplicate_participants,
                "aggregate_shares": aggregate_shares,
                "firm_shares": sum_shares,
                "aggregate_trades": aggregate_trades,
                "firm_trades": sum_trades,
                "exact_match": is_match,
            })

    all_keys = aggregate_keys | firm_keys
    gate = (
        "PASS" if all_keys
        and not missing_aggregate_last_reported
        and not missing_firm_last_reported
        and not aggregate_only and not firm_only
        and not duplicate_aggregate_date_keys
        and not multi_product_date_keys
        and not invalid_numeric_keys
        and not participant_duplicate_key_groups
        and matched_groups == len(all_keys)
        and exact_matches == matched_groups
        else "FAIL_OR_REVIEW"
    )
    return {
        "aggregate_type": aggregate_type,
        "firm_type": firm_type,
        "aggregate_rows": len(aggregates),
        "firm_rows": len(firms),
        "aggregate_symbol_last_reported_groups": len(aggregate_keys),
        "firm_symbol_last_reported_groups": len(firm_keys),
        "shared_groups": len(shared_keys),
        "aggregate_only_groups": len(aggregate_only),
        "firm_only_groups": len(firm_only),
        "missing_aggregate_last_reported_rows": missing_aggregate_last_reported,
        "missing_firm_last_reported_rows": missing_firm_last_reported,
        "duplicate_aggregate_symbol_date_keys": duplicate_aggregate_date_keys[:50],
        "duplicate_aggregate_symbol_date_key_count": len(duplicate_aggregate_date_keys),
        "multi_product_symbol_date_keys": multi_product_date_keys[:50],
        "multi_product_symbol_date_key_count": len(multi_product_date_keys),
        "participant_duplicate_key_groups": participant_duplicate_key_groups[:50],
        "participant_duplicate_key_group_count": len(participant_duplicate_key_groups),
        "invalid_numeric_groups": invalid_numeric_keys[:50],
        "invalid_numeric_group_count": len(invalid_numeric_keys),
        "matched_groups": matched_groups,
        "exact_matches": exact_matches,
        "mismatches": mismatches[:50],
        "mismatch_count": len(mismatches),
        "matched_aggregate_shares": matched_shares,
        "matched_aggregate_trades": matched_trades,
        "lnd_date_groups": lnd_groups,
        "data_gate": gate,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="phase363_finra_last_reported_date_grain")
    args = parser.parse_args()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers.update({
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "SmartMoneyResearch-Phase363/1.0",
    })
    token = os.getenv("FINRA_API_TOKEN", "").strip()
    if token:
        session.headers["Authorization"] = f"Bearer {token}"

    rows, pages, expected_total = fetch_partition(session)
    families = {
        aggregate_type: audit_family(rows, aggregate_type)
        for aggregate_type in AGG_TO_FIRM
    }
    summary = {
        "phase": 363,
        "source": "FINRA OTCMarket weeklySummaryHistoric",
        "audit_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "week": WEEK,
        "tier": TIER,
        "candidate_grain": "(issueSymbolIdentifier,lastReportedDate) plus a unique aggregate productTypeCode",
        "partition_rows_retrieved": len(rows),
        "api_record_total": expected_total,
        "api_record_total_match": len(rows) == expected_total,
        "page_count": len(pages),
        "families": families,
        "retrieval_gate": "PASS" if len(rows) == expected_total else "FAIL_OR_REVIEW",
        "overall_data_gate": (
            "PASS" if all(x["data_gate"] == "PASS" for x in families.values())
            else "FAIL_OR_REVIEW"
        ),
        "interpretation": (
            "lastReportedDate is a candidate row-grain dimension, not yet a universal schema guarantee. "
            "A PASS applies only to this tested partition and does not authorize summing across reporting dates."
        ),
        "pit_status": "FINAL_HISTORICAL_SNAPSHOT_ONLY; no interim vintages",
        "forward_returns_used": False,
        "alpha_test_authorized": False,
        "holdout_used": False,
        "f80_changed": False,
    }
    (output / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (output / "page_hashes.json").write_text(json.dumps(pages, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2), flush=True)
    print(
        f"[Phase363] complete retrieval={summary['retrieval_gate']} "
        f"data={summary['overall_data_gate']} rows={len(rows)}",
        flush=True,
    )


if __name__ == "__main__":
    main()

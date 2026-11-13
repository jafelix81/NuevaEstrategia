#!/usr/bin/env python3
"""Phase 360: validate FINRA symbol-only bridge and firm-to-symbol totals.

Phase 359 showed that productTypeCode is populated on symbol aggregates but is
blank on symbol-firm rows. This phase tests whether productTypeCode can be
inherited safely from the symbol aggregate within the same week, tier and
ATS/OTC summary family, and whether firm-grain quantities reconcile to the
symbol aggregate. Ambiguous symbols are excluded rather than multiplied.

Research-only: no returns, signal, alpha, holdout, or F80 changes.
"""
from __future__ import annotations

import argparse
import json
import os
from collections import Counter, defaultdict
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

import requests

from research.phase359_finra_product_key_diagnostic import (
    WEEKS, TIERS, fetch_partition,
)

AGG_TO_FIRM = {
    "ATS_W_SMBL": "ATS_W_SMBL_FIRM",
    "OTC_W_SMBL": "OTC_W_SMBL_FIRM",
}


def norm(value):
    return str(value or "").strip().upper()


def parse_nonnegative_integer(value):
    if value is None or str(value).strip() == "":
        return None
    try:
        number = Decimal(str(value).replace(",", "").strip())
    except (InvalidOperation, ValueError):
        return None
    if not number.is_finite() or number < 0 or number != number.to_integral_value():
        return None
    return int(number)


def _participant_key(row, aggregate_type):
    mpid = norm(row.get("MPID"))
    crd = norm(row.get("firmCRDNumber"))
    name = norm(row.get("marketParticipantName"))
    if aggregate_type == "ATS_W_SMBL":
        identity = mpid or crd
    else:
        identity = crd or mpid
    return identity or name or ""


def audit_pair(rows, week, tier, aggregate_type):
    firm_type = AGG_TO_FIRM[aggregate_type]
    aggregate_by_symbol = defaultdict(list)
    firm_by_symbol = defaultdict(list)
    missing_aggregate_symbol_rows = 0
    missing_firm_symbol_rows = 0
    unexpected_product_on_firm_rows = 0
    partition_errors = []

    for index, row in enumerate(rows):
        actual_week = norm(row.get("weekStartDate"))[:10]
        actual_tier = norm(row.get("tierIdentifier"))
        if actual_week != week:
            partition_errors.append(f"row {index}: weekStartDate={actual_week!r}, expected {week}")
        if actual_tier != tier:
            partition_errors.append(f"row {index}: tierIdentifier={actual_tier!r}, expected {tier}")

        summary_type = norm(row.get("summaryTypeCode"))
        symbol = norm(row.get("issueSymbolIdentifier"))
        if summary_type == aggregate_type:
            if not symbol:
                missing_aggregate_symbol_rows += 1
            else:
                aggregate_by_symbol[symbol].append(row)
        elif summary_type == firm_type:
            if not symbol:
                missing_firm_symbol_rows += 1
            else:
                firm_by_symbol[symbol].append(row)
                if norm(row.get("productTypeCode")):
                    unexpected_product_on_firm_rows += 1

    aggregate_symbols = set(aggregate_by_symbol)
    firm_symbols = set(firm_by_symbol)
    shared_symbols = aggregate_symbols & firm_symbols
    aggregate_only = sorted(aggregate_symbols - firm_symbols)
    firm_only = sorted(firm_symbols - aggregate_symbols)

    ambiguous = []
    mapped = []
    for symbol in sorted(shared_symbols):
        aggregate_rows = aggregate_by_symbol[symbol]
        product_types = sorted({
            norm(row.get("productTypeCode")) or "__MISSING__"
            for row in aggregate_rows
        })
        if len(aggregate_rows) != 1:
            ambiguous.append({
                "symbol": symbol,
                "reason": "MULTIPLE_AGGREGATE_ROWS",
                "aggregate_row_count": len(aggregate_rows),
                "product_types": product_types,
            })
        elif len(product_types) != 1 or product_types[0] == "__MISSING__":
            ambiguous.append({
                "symbol": symbol,
                "reason": "MISSING_OR_NONUNIQUE_PRODUCT_TYPE",
                "aggregate_row_count": len(aggregate_rows),
                "product_types": product_types,
            })
        else:
            mapped.append((symbol, product_types[0], aggregate_rows[0]))

    share_exact = 0
    trades_exact = 0
    both_exact = 0
    invalid_numeric_symbols = []
    participant_missing_identity = 0
    participant_duplicate_symbol_keys = 0
    participant_rows = 0
    de_minimis_rows = 0
    de_minimis_share_quantity = 0
    de_minimis_trade_count = 0
    total_aggregate_shares = 0
    total_firm_shares = 0
    total_aggregate_trades = 0
    total_firm_trades = 0
    mismatch_examples = []

    for symbol, product_type, aggregate_row in mapped:
        symbol_firm_rows = firm_by_symbol[symbol]
        aggregate_shares = parse_nonnegative_integer(
            aggregate_row.get("totalWeeklyShareQuantity")
        )
        aggregate_trades = parse_nonnegative_integer(
            aggregate_row.get("totalWeeklyTradeCount")
        )
        firm_shares = []
        firm_trades = []
        participant_keys = Counter()

        for row in symbol_firm_rows:
            participant_rows += 1
            name = norm(row.get("marketParticipantName"))
            is_de_minimis = "DE MINIMIS" in name
            mpid = norm(row.get("MPID"))
            crd = norm(row.get("firmCRDNumber"))
            if is_de_minimis:
                de_minimis_rows += 1
            elif not (mpid or crd):
                participant_missing_identity += 1

            key = _participant_key(row, aggregate_type)
            if key:
                participant_keys[key] += 1

            shares = parse_nonnegative_integer(row.get("totalWeeklyShareQuantity"))
            trades = parse_nonnegative_integer(row.get("totalWeeklyTradeCount"))
            firm_shares.append(shares)
            firm_trades.append(trades)
            if is_de_minimis:
                if shares is not None:
                    de_minimis_share_quantity += shares
                if trades is not None:
                    de_minimis_trade_count += trades

        participant_duplicate_symbol_keys += sum(
            1 for count in participant_keys.values() if count > 1
        )

        if (
            aggregate_shares is None
            or aggregate_trades is None
            or any(value is None for value in firm_shares)
            or any(value is None for value in firm_trades)
        ):
            invalid_numeric_symbols.append(symbol)
            continue

        sum_firm_shares = sum(firm_shares)
        sum_firm_trades = sum(firm_trades)
        total_aggregate_shares += aggregate_shares
        total_firm_shares += sum_firm_shares
        total_aggregate_trades += aggregate_trades
        total_firm_trades += sum_firm_trades

        shares_match = sum_firm_shares == aggregate_shares
        trades_match = sum_firm_trades == aggregate_trades
        share_exact += int(shares_match)
        trades_exact += int(trades_match)
        both_exact += int(shares_match and trades_match)
        if not (shares_match and trades_match) and len(mismatch_examples) < 20:
            mismatch_examples.append({
                "symbol": symbol,
                "inherited_product_type": product_type,
                "aggregate_shares": aggregate_shares,
                "firm_sum_shares": sum_firm_shares,
                "aggregate_trades": aggregate_trades,
                "firm_sum_trades": sum_firm_trades,
                "share_delta": sum_firm_shares - aggregate_shares,
                "trade_delta": sum_firm_trades - aggregate_trades,
            })

    mapped_count = len(mapped)
    ambiguous_count = len(ambiguous)
    orphan_count = len(aggregate_only) + len(firm_only)
    duplicate_aggregate_symbol_rows = sum(
        max(0, len(v) - 1) for v in aggregate_by_symbol.values()
    )
    has_explicit_exclusions = (
        ambiguous_count > 0
        or missing_aggregate_symbol_rows > 0
        or missing_firm_symbol_rows > 0
    )
    mapping_gate = (
        "FAIL_OR_REVIEW" if orphan_count or duplicate_aggregate_symbol_rows
        else ("PASS_WITH_EXCLUSIONS" if has_explicit_exclusions else "PASS")
    )
    reconciliation_gate = (
        "PASS" if mapped_count > 0
        and both_exact == mapped_count
        and not invalid_numeric_symbols
        and not mismatch_examples
        else "FAIL_OR_REVIEW"
    )
    data_gate = (
        "PASS_WITH_EXCLUSIONS"
        if mapping_gate in {"PASS", "PASS_WITH_EXCLUSIONS"}
        and reconciliation_gate == "PASS"
        else "FAIL_OR_REVIEW"
    )
    concentration_ready = (
        data_gate == "PASS"
        and ambiguous_count == 0
        and missing_aggregate_symbol_rows == 0
        and missing_firm_symbol_rows == 0
        and participant_missing_identity == 0
        and participant_duplicate_symbol_keys == 0
        and de_minimis_rows == 0
    )
    de_minimis_share_pct = (
        round(100.0 * de_minimis_share_quantity / total_firm_shares, 6)
        if total_firm_shares else None
    )

    return {
        "aggregate_summary_type": aggregate_type,
        "firm_summary_type": firm_type,
        "aggregate_unique_symbols": len(aggregate_symbols),
        "firm_unique_symbols": len(firm_symbols),
        "shared_symbols": len(shared_symbols),
        "aggregate_only_symbols": len(aggregate_only),
        "firm_only_symbols": len(firm_only),
        "unambiguous_symbol_bridge_count": mapped_count,
        "ambiguous_symbol_count": ambiguous_count,
        "ambiguous_symbol_examples": ambiguous[:20],
        "unambiguous_bridge_coverage_pct": (
            round(100.0 * mapped_count / len(shared_symbols), 6)
            if shared_symbols else None
        ),
        "missing_aggregate_symbol_rows": missing_aggregate_symbol_rows,
        "missing_firm_symbol_rows": missing_firm_symbol_rows,
        "firm_rows_with_unexpected_product_type": unexpected_product_on_firm_rows,
        "duplicate_aggregate_symbol_rows": duplicate_aggregate_symbol_rows,
        "participant_rows_on_unambiguous_symbols": participant_rows,
        "participant_rows_missing_mpid_and_crd_excluding_de_minimis": participant_missing_identity,
        "duplicate_participant_symbol_keys": participant_duplicate_symbol_keys,
        "de_minimis_rows": de_minimis_rows,
        "de_minimis_share_quantity": de_minimis_share_quantity,
        "de_minimis_trade_count": de_minimis_trade_count,
        "de_minimis_pct_of_firm_shares": de_minimis_share_pct,
        "invalid_numeric_symbols": invalid_numeric_symbols[:20],
        "invalid_numeric_symbol_count": len(invalid_numeric_symbols),
        "share_quantity_exact_matches": share_exact,
        "trade_count_exact_matches": trades_exact,
        "both_exact_matches": both_exact,
        "total_aggregate_shares_on_unambiguous_symbols": total_aggregate_shares,
        "total_firm_shares_on_unambiguous_symbols": total_firm_shares,
        "total_aggregate_trades_on_unambiguous_symbols": total_aggregate_trades,
        "total_firm_trades_on_unambiguous_symbols": total_firm_trades,
        "mismatch_examples": mismatch_examples,
        "mapping_gate": mapping_gate,
        "reconciliation_gate": reconciliation_gate,
        "data_gate": data_gate,
        "intermediary_concentration_ready": concentration_ready,
        "concentration_interpretation": (
            "Reporting-intermediary/ATS concentration only; not beneficial-owner identity, "
            "trade direction, or proof of informed activity."
        ),
        "partition_errors": partition_errors[:20],
        "partition_error_count": len(partition_errors),
    }


def audit_partition(rows, week, tier):
    summary_counts = Counter(norm(r.get("summaryTypeCode")) or "__MISSING__" for r in rows)
    pairs = {
        agg: audit_pair(rows, week, tier, agg)
        for agg in AGG_TO_FIRM
    }
    return {
        "week": week,
        "tier": tier,
        "rows_total": len(rows),
        "summary_type_counts": dict(sorted(summary_counts.items())),
        "firm_product_type_missing_rows": sum(
            1 for r in rows
            if norm(r.get("summaryTypeCode")) in set(AGG_TO_FIRM.values())
            and not norm(r.get("productTypeCode"))
        ),
        "pairs": pairs,
        "partition_status": (
            "PASS" if all(v["data_gate"] in {"PASS", "PASS_WITH_EXCLUSIONS"} for v in pairs.values())
            else "FAIL_OR_REVIEW"
        ),
        "forward_returns_used": False,
        "alpha_test_authorized": False,
        "f80_changed": False,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="phase360_finra_symbol_bridge")
    args = parser.parse_args()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers.update({
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "SmartMoneyResearch-Phase360/1.0",
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
            print(f"[Phase360] start {week}/{tier}", flush=True)
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
                    f"[Phase360] complete {week}/{tier}: rows={len(rows)} "
                    f"status={result['partition_status']}",
                    flush=True,
                )
            except Exception as exc:
                request_errors.append({"week": week, "tier": tier, "error": repr(exc)})

    all_pairs = [
        pair
        for partition in partitions
        for pair in partition.get("pairs", {}).values()
    ]
    summary = {
        "phase": 360,
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
            len(partitions) == 4
            and all(p.get("api_record_total_match") for p in partitions)
        ),
        "retrieval_gate": (
            "PASS" if len(partitions) == 4 and not request_errors
            and all(p.get("api_record_total_match") for p in partitions)
            else "FAIL_OR_REVIEW"
        ),
        "overall_data_gate": (
            "PASS_WITH_EXCLUSIONS"
            if all_pairs and all(p["data_gate"] in {"PASS", "PASS_WITH_EXCLUSIONS"} for p in all_pairs)
            else "FAIL_OR_REVIEW"
        ),
        "pit_status": "FINAL_HISTORICAL_SNAPSHOT_ONLY; interim vintages unavailable",
        "economic_interpretation": (
            "FINRA participant rows identify reporting intermediaries. They do not reveal "
            "beneficial owners or trade direction; non-ATS de-minimis rows are censored aggregates."
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
        f"[Phase360] complete retrieval={summary['retrieval_gate']} "
        f"data={summary['overall_data_gate']} rows={total_rows}",
        flush=True,
    )


if __name__ == "__main__":
    main()

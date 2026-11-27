#!/usr/bin/env python3
"""Reproducible SEC Form 4 code-P cohort and frozen-F80 exact-symbol audit."""
from __future__ import annotations
import argparse
import csv
import json
from collections import defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

SOURCE = {
    "main_commit": "a27340c1866b5e44f2638eb4dc3e0cbd1617b7ea",
    "transaction_details_blob_sha1": "f3ca95feb6f56e43eaac46a5fca4f66a73783a51",
    "reporting_owners_blob_sha1": "9017a22a48e53be0299d85a9a850db0449e6918b",
    "frozen_universe_commit": "1aa1b91f383ce9cef375a43e775c736a27356a5",
    "frozen_universe_blob_sha1": "7edbd62b4fb34a6123276e4ce45cb3c1c62479c7",
    "frozen_universe_sha256": "f850655a22a8843dad90e9562b3152b9ca064560586109022b5bfd205a003dda",
}
LATEST_CAPTURE = {
    "run_id": 45976055356, "artifact_id": 15186742638, "status": "success",
    "new_accessions": 0, "new_event_rows": 0,
    "transaction_detail_rows_appended": 48,
    "linked_footnote_reference_rows_appended": 65,
    "separate_footnote_reference_rows_appended": 60,
    "owner_rows_appended": 10, "form144_proposed_sale_matches": 16,
    "matched_form4_accessions": 15, "signal_eligible_matches": 0,
}
FLAG_KEYS = (
    "open_market_mention", "private_purchase_or_placement_mention",
    "rule_10b5_1_mention", "option_or_cashless_mention", "trust_mention",
    "compensation_or_vesting_mention", "employee_plan_mention",
    "tax_or_withholding_mention", "gift_or_donation_mention",
)
ELIGIBILITY_FIELDS = (
    "research_observation_eligible", "signal_eligible",
    "public_availability_certified", "same_day_intraday_use_authorized",
    "security_identity_verified", "historical_f80_membership_verified",
    "owner_attribution_verified", "transaction_semantics_verified",
    "economic_event_new_trade_authorized",
)


def read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def truthy(value: Any) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "y"}


def as_int(value: Any) -> int:
    try:
        return int(Decimal(str(value or "0").strip()))
    except (InvalidOperation, ValueError):
        return 0


def as_decimal(value: Any) -> Decimal:
    try:
        return Decimal(str(value or "0").strip())
    except (InvalidOperation, ValueError):
        return Decimal("0")


def decimal_text(value: Decimal) -> str:
    rendered = format(value.normalize(), "f")
    return rendered.rstrip("0").rstrip(".") if "." in rendered else rendered


def parse_flags(raw: Any) -> list[dict[str, Any]]:
    if not raw:
        return []
    try:
        parsed = json.loads(str(raw))
    except (TypeError, json.JSONDecodeError):
        return []
    if isinstance(parsed, dict):
        return [parsed]
    return [item for item in parsed if isinstance(item, dict)] if isinstance(parsed, list) else []


def analyze(transactions_path: str | Path, owners_path: str | Path, universe_path: str | Path) -> dict[str, Any]:
    details = read_csv(transactions_path)
    owners = read_csv(owners_path)
    with Path(universe_path).open("r", encoding="utf-8-sig", newline="") as handle:
        universe_rows = list(csv.DictReader(handle))
    universe = {
        str(row.get("Ticker") or row.get("ticker") or "").strip().upper()
        for row in universe_rows
        if str(row.get("Ticker") or row.get("ticker") or "").strip()
    }
    tx = [r for r in details if str(r.get("detail_type") or "").strip() == "transaction_row"]
    p_rows = [r for r in tx if str(r.get("transaction_code") or "").strip().upper() == "P"]
    owner_accessions = {str(r.get("accession") or "").strip() for r in owners if r.get("accession")}
    by_accession: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in p_rows:
        if row.get("accession"):
            by_accession[str(row["accession"]).strip()].append(row)

    records = []
    for accession, rows in by_accession.items():
        first = rows[0]
        symbols = {str(r.get("issuer_trading_symbol_normalized") or "").strip().upper() for r in rows}
        plans = {str(r.get("aff10b5one_filing_flag") or "").strip().lower() for r in rows if r.get("aff10b5one_filing_flag")}
        counts = {as_int(r.get("reporting_owner_count")) for r in rows if r.get("reporting_owner_count")}
        flags = [flag for r in rows for flag in parse_flags(r.get("footnote_flags_json"))]
        records.append({
            "accession": accession,
            "symbol": sorted(s for s in symbols if s)[0] if any(symbols) else "",
            "issuer": str(first.get("issuer_name") or "").strip(),
            "filing_date": str(first.get("filing_date") or "").strip(),
            "transaction_rows": len(rows),
            "shares": decimal_text(sum((as_decimal(r.get("shares_numeric")) for r in rows), Decimal("0"))),
            "plan_flag": sorted(plans)[0] if len(plans) == 1 else ("mixed" if plans else "unknown"),
            "owner_count": max(counts) if counts else 0,
            "owner_sidecar_present": accession in owner_accessions,
            "footnote_flags": flags,
        })
    records.sort(key=lambda x: (x["symbol"], x["filing_date"], x["accession"]))
    filing_dates = sorted(r["filing_date"] for r in p_rows if r.get("filing_date"))
    symbols = {str(r.get("issuer_trading_symbol_normalized") or "").strip().upper() for r in p_rows if r.get("issuer_trading_symbol_normalized")}
    yes_accessions = sum(x["plan_flag"] == "yes" for x in records)
    no_accessions = sum(x["plan_flag"] == "no" for x in records)
    yes_rows = sum(str(r.get("aff10b5one_filing_flag") or "").strip().lower() == "yes" for r in p_rows)
    no_rows = sum(str(r.get("aff10b5one_filing_flag") or "").strip().lower() == "no" for r in p_rows)
    keyword_counts = {
        key: sum(any(truthy(flag.get(key)) for flag in x["footnote_flags"]) for x in records)
        for key in FLAG_KEYS
    }
    clusters: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for x in records:
        if x["symbol"] and x["symbol"] not in {"N/A", "NA"}:
            clusters[x["symbol"]].append(x)
    repeated = [
        {"symbol": symbol, "issuer": xs[0]["issuer"], "accessions": len(xs),
         "transaction_rows": sum(x["transaction_rows"] for x in xs)}
        for symbol, xs in clusters.items() if len(xs) > 1
    ]
    repeated.sort(key=lambda x: (-x["accessions"], x["symbol"]))

    overlap = [x for x in records if x["symbol"] and x["symbol"] in universe]
    overlap_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for x in overlap:
        overlap_groups[x["symbol"]].append(x)
    by_symbol = []
    for symbol, xs in sorted(overlap_groups.items()):
        by_symbol.append({
            "symbol": symbol, "issuer": xs[0]["issuer"], "accessions": len(xs),
            "transaction_rows": sum(x["transaction_rows"] for x in xs),
            "shares": decimal_text(sum((Decimal(x["shares"]) for x in xs), Decimal("0"))),
            "filing_level_10b5_1_flags": sorted({x["plan_flag"] for x in xs}),
            "owner_sidecar_complete_accessions": sum(x["owner_sidecar_present"] for x in xs),
        })
    missing = [{
        "accession": x["accession"], "symbol": x["symbol"], "issuer": x["issuer"],
        "filing_date": x["filing_date"], "transaction_rows": x["transaction_rows"],
        "in_static_f80_snapshot": x["symbol"] in universe,
    } for x in records if not x["owner_sidecar_present"]]
    missing.sort(key=lambda x: x["accession"])
    eligibility = {field: sum(truthy(r.get(field)) for r in p_rows) for field in ELIGIBILITY_FIELDS}
    non_10b5 = sorted(s for s, xs in overlap_groups.items() if all(x["plan_flag"] == "no" for x in xs))
    affirmative_10b5 = sorted(s for s, xs in overlap_groups.items() if any(x["plan_flag"] == "yes" for x in xs))

    return {
        "phase": 660,
        "audit_cutoff_utc": "2026-11-27T09:45:00Z",
        "source": {**SOURCE, "universe_ticker_count": len(universe)},
        "latest_capture": LATEST_CAPTURE,
        "live_ledger": {
            "all_detail_records": len(details), "transaction_rows": len(tx),
            "distinct_transaction_accessions": len({r["accession"] for r in tx if r.get("accession")}),
            "reporting_owner_rows": len(owners), "reporting_owner_accessions": len(owner_accessions),
        },
        "purchase_code_p": {
            "transaction_rows": len(p_rows), "accessions": len(records),
            "symbol_values_including_na": len(symbols),
            "non_na_symbol_values": len(symbols - {"N/A", "NA"}),
            "filing_date_min": filing_dates[0] if filing_dates else None,
            "filing_date_max": filing_dates[-1] if filing_dates else None,
            "filing_level_10b5_1": {
                "yes_accessions": yes_accessions, "no_accessions": no_accessions,
                "yes_rows": yes_rows, "no_rows": no_rows,
            },
            "owner_sidecar": {
                "complete_accessions": sum(x["owner_sidecar_present"] for x in records),
                "missing_accessions": len(missing),
            },
            "multi_owner_accessions": sum(x["owner_count"] > 1 for x in records),
            "footnote_keyword_accessions": keyword_counts,
            "repeated_issuer_clusters": repeated,
        },
        "static_f80_exact_symbol_intersection": {
            "snapshot_tickers": len(universe), "purchase_accessions": len(overlap),
            "transaction_rows": sum(x["transaction_rows"] for x in overlap),
            "symbols": sorted(overlap_groups), "by_symbol": by_symbol,
            "non_10b5_flagged_symbols": non_10b5,
            "affirmative_10b5_flagged_symbols": affirmative_10b5,
            "historical_f80_membership_verified": False,
        },
        "purchase_accessions_missing_owner_sidecar": missing,
        "eligibility_true_counts": eligibility,
        "decision": {
            "disposition": "P_CODE_CONTEXT_ONLY_NO_PROMOTION",
            "non_10b5_flagged_f80_issuer_clusters": len(non_10b5),
            "affirmative_10b5_flagged_f80_issuer_clusters": len(affirmative_10b5),
            "upst_is_one_issuer_cluster_not_two_independent_issuer_observations": True,
            "code_p_execution_venue_resolved": False,
            "incremental_alpha_demonstrated": False,
            "new_signal_promoted": False,
        },
        "controls": {
            "price_or_forward_return_data_inspected_in_phase660": False,
            "event_study_run": False, "oos_run": False, "bootstrap_run": False,
            "loo_run": False, "holdout_touched": False,
            "f80_top20_partial50_baseline_c20_frozen": True,
            "production_or_strategy_changed": False, "vendor_contacted": False,
            "paid_data_purchased": False, "data_budget_usd": 0,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--transactions", required=True)
    parser.add_argument("--owners", required=True)
    parser.add_argument("--universe", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    summary = analyze(args.transactions, args.owners, args.universe)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()

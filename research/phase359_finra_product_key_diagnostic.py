#!/usr/bin/env python3
"""Phase 359: diagnose FINRA symbol/product-type key alignment.

Phase 358 retrieved firm-grain and symbol-grain weekly rows but found zero exact
join keys. This phase does not reconcile or sum firm rows. It isolates whether
productTypeCode, symbol normalization, or row identity explains the zero overlap.

Data feasibility only: no returns, signal, or alpha test.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import requests

BASE = "https://api.finra.org/data/group/otcmarket/name/weeklySummaryHistoric"
WEEKS = ("2022-01-03", "2025-10-20")
TIERS = ("T1", "T2")
PAGE_SIZE = 5000
MAX_OFFSET = 500000
FIELDS = [
    "issueSymbolIdentifier", "weekStartDate", "tierIdentifier",
    "summaryTypeCode", "productTypeCode", "firmCRDNumber", "MPID",
    "marketParticipantName", "totalWeeklyShareQuantity",
    "totalWeeklyTradeCount", "initialPublishedDate", "lastUpdateDate",
    "lastReportedDate",
]
AGG_TO_FIRM = {
    "ATS_W_SMBL": "ATS_W_SMBL_FIRM",
    "OTC_W_SMBL": "OTC_W_SMBL_FIRM",
}
FIRM_TYPES = set(AGG_TO_FIRM.values())
AGG_TYPES = set(AGG_TO_FIRM)
KNOWN_TYPES = {
    "ATS_W_FIRM", "OTC_W_FIRM", "ATS_W_VOL_STATS", "OTC_W_VOL_STATS",
    *FIRM_TYPES, *AGG_TYPES,
}


def norm(value):
    return str(value or "").strip().upper()


def audit_rows(rows, week, tier):
    errors = []
    type_counts = Counter()
    product_counts = defaultdict(Counter)
    missing_symbol_by_type = Counter()
    aggregate = defaultdict(set)
    firm = defaultdict(set)
    firm_rows_missing_id = 0
    firm_rows_missing_name = 0
    examples_missing_symbol = []

    for i, row in enumerate(rows):
        actual_week = norm(row.get("weekStartDate"))[:10]
        actual_tier = norm(row.get("tierIdentifier"))
        if actual_week != week:
            errors.append(f"row {i}: weekStartDate={actual_week!r}, expected {week}")
        if actual_tier != tier:
            errors.append(f"row {i}: tierIdentifier={actual_tier!r}, expected {tier}")

        stype = norm(row.get("summaryTypeCode"))
        product = norm(row.get("productTypeCode")) or "__MISSING__"
        symbol = norm(row.get("issueSymbolIdentifier"))
        type_counts[stype or "__MISSING__"] += 1
        product_counts[stype or "__MISSING__"][product] += 1

        if stype not in KNOWN_TYPES:
            errors.append(f"row {i}: unknown summaryTypeCode={stype!r}")
        if not symbol:
            missing_symbol_by_type[stype or "__MISSING__"] += 1
            if len(examples_missing_symbol) < 10:
                examples_missing_symbol.append({"row_index": i, "summary_type": stype or "__MISSING__", "product_type": product})
            continue

        if stype in AGG_TYPES:
            aggregate[stype].add((symbol, product))
        elif stype in FIRM_TYPES:
            aggregate_type = next(k for k, v in AGG_TO_FIRM.items() if v == stype)
            firm[aggregate_type].add((symbol, product))
            if not norm(row.get("MPID")) and not norm(row.get("firmCRDNumber")):
                firm_rows_missing_id += 1
            if not norm(row.get("marketParticipantName")):
                firm_rows_missing_name += 1

    crosswalks = {}
    for agg_type, firm_type in AGG_TO_FIRM.items():
        a_pairs = aggregate.get(agg_type, set())
        f_pairs = firm.get(agg_type, set())
        a_by_symbol = defaultdict(set)
        f_by_symbol = defaultdict(set)
        for symbol, product in a_pairs:
            a_by_symbol[symbol].add(product)
        for symbol, product in f_pairs:
            f_by_symbol[symbol].add(product)

        a_symbols, f_symbols = set(a_by_symbol), set(f_by_symbol)
        shared = a_symbols & f_symbols
        singleton_equal = 0
        singleton_different = 0
        multivalue = 0
        mismatch_examples = []
        for symbol in sorted(shared):
            ap = a_by_symbol[symbol]
            fp = f_by_symbol[symbol]
            if len(ap) == 1 and len(fp) == 1:
                av, fv = next(iter(ap)), next(iter(fp))
                if av == fv:
                    singleton_equal += 1
                else:
                    singleton_different += 1
                    if len(mismatch_examples) < 20:
                        mismatch_examples.append({
                            "symbol": symbol,
                            "aggregate_product_types": sorted(ap),
                            "firm_product_types": sorted(fp),
                        })
            else:
                multivalue += 1
                if ap != fp and len(mismatch_examples) < 20:
                    mismatch_examples.append({
                        "symbol": symbol,
                        "aggregate_product_types": sorted(ap),
                        "firm_product_types": sorted(fp),
                    })

        crosswalks[agg_type] = {
            "aggregate_summary_type": agg_type,
            "firm_summary_type": firm_type,
            "aggregate_symbol_product_keys": len(a_pairs),
            "firm_symbol_product_keys": len(f_pairs),
            "exact_symbol_product_key_overlap": len(a_pairs & f_pairs),
            "aggregate_unique_symbols": len(a_symbols),
            "firm_unique_symbols": len(f_symbols),
            "shared_symbols_ignoring_product_type": len(shared),
            "aggregate_only_symbols": len(a_symbols - f_symbols),
            "firm_only_symbols": len(f_symbols - a_symbols),
            "shared_symbols_singleton_same_product": singleton_equal,
            "shared_symbols_singleton_different_product": singleton_different,
            "shared_symbols_with_multivalue_product_type": multivalue,
            "product_key_mismatch_examples": mismatch_examples,
        }

    return {
        "week": week,
        "tier": tier,
        "rows_total": len(rows),
        "summary_type_counts": dict(sorted(type_counts.items())),
        "product_type_counts_by_summary_type": {
            stype: dict(sorted(counts.items()))
            for stype, counts in sorted(product_counts.items())
        },
        "missing_symbol_rows_by_summary_type": dict(sorted(missing_symbol_by_type.items())),
        "missing_symbol_examples": examples_missing_symbol,
        "firm_rows_missing_participant_id": firm_rows_missing_id,
        "firm_rows_missing_participant_name": firm_rows_missing_name,
        "key_crosswalks": crosswalks,
        "partition_errors": errors[:50],
        "partition_error_count": len(errors),
        "diagnostic_status": "COMPLETED_WITH_EXCEPTIONS" if errors or missing_symbol_by_type else "COMPLETED",
        "forward_returns_used": False,
        "alpha_test_authorized": False,
        "f80_changed": False,
    }


def parse_rows(payload):
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if isinstance(payload, dict):
        if payload.get("message") or payload.get("statusCode"):
            raise RuntimeError(f"FINRA error response: {payload}")
        data = payload.get("data", [])
        if isinstance(data, dict):
            data = data.get("data", [])
        if isinstance(data, list):
            return [x for x in data if isinstance(x, dict)]
    raise RuntimeError(f"Unexpected FINRA response type: {type(payload).__name__}")


def fetch_partition(session, week, tier):
    rows, pages = [], []
    offset, expected_total = 0, None
    while True:
        payload = {
            "fields": FIELDS,
            "compareFilters": [
                {"compareType": "EQUAL", "fieldName": "historicalWeek", "fieldValue": week},
                {"compareType": "EQUAL", "fieldName": "tierIdentifier", "fieldValue": tier},
            ],
            "limit": PAGE_SIZE,
            "offset": offset,
        }
        response = None
        for attempt in range(4):
            try:
                response = session.post(BASE, json=payload, timeout=(20, 120))
            except requests.RequestException:
                if attempt == 3:
                    raise
                time.sleep(min(3 * (2 ** attempt), 30))
                continue
            if response.status_code in {408, 429, 500, 502, 503, 504}:
                if attempt == 3:
                    response.raise_for_status()
                retry_after = response.headers.get("Retry-After")
                try:
                    delay = float(retry_after) if retry_after else 3 * (2 ** attempt)
                except (TypeError, ValueError):
                    delay = 3 * (2 ** attempt)
                time.sleep(max(0, min(delay, 60)))
                continue
            response.raise_for_status()
            break
        if response is None:
            raise RuntimeError("No FINRA response")

        page_rows = parse_rows(response.json())
        headers = {str(k).lower(): v for k, v in response.headers.items()}
        total_raw = headers.get("record-total")
        if total_raw is None:
            raise RuntimeError(f"Missing Record-Total for {week}/{tier} offset={offset}")
        total = int(total_raw)
        if expected_total is None:
            expected_total = total
        elif total != expected_total:
            raise RuntimeError(f"Record-Total changed for {week}/{tier}: {total} vs {expected_total}")
        page_count_raw = headers.get("total-records-on-page")
        page_count = int(page_count_raw) if page_count_raw is not None else len(page_rows)
        if page_count != len(page_rows):
            raise RuntimeError(f"Page count mismatch for {week}/{tier} offset={offset}")
        record_offset = headers.get("record-offset")
        if record_offset is not None and int(record_offset) != offset:
            raise RuntimeError(f"Record-Offset mismatch for {week}/{tier} offset={offset}")
        if not page_rows and total > offset:
            raise RuntimeError(f"Empty page before Record-Total for {week}/{tier} offset={offset}")

        rows.extend(page_rows)
        pages.append({
            "week": week, "tier": tier, "offset": offset,
            "rows": len(page_rows), "record_total": total,
            "request_id": headers.get("finra-api-request-id"),
            "sha256": hashlib.sha256(response.content).hexdigest(),
        })
        offset += page_count
        if offset >= total:
            break
        if offset > MAX_OFFSET:
            raise RuntimeError(f"Offset ceiling exceeded for {week}/{tier}")

    if expected_total is None or len(rows) != expected_total:
        raise RuntimeError(f"Incomplete partition {week}/{tier}: {len(rows)} != {expected_total}")
    return rows, pages


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="phase359_finra_product_key")
    args = parser.parse_args()
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update({
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "SmartMoneyResearch-Phase359/1.0",
    })
    token = os.getenv("FINRA_API_TOKEN", "").strip()
    if token:
        session.headers["Authorization"] = f"Bearer {token}"

    results, all_pages, request_errors = [], [], []
    total_rows = 0
    for week in WEEKS:
        for tier in TIERS:
            print(f"[Phase359] start {week}/{tier}", flush=True)
            try:
                rows, pages = fetch_partition(session, week, tier)
                total_rows += len(rows)
                all_pages.extend(pages)
                result = audit_rows(rows, week, tier)
                result["api_record_total"] = pages[0]["record_total"] if pages else 0
                result["api_records_retrieved"] = len(rows)
                result["api_record_total_match"] = result["api_record_total"] == len(rows)
                results.append(result)
                print(
                    f"[Phase359] complete {week}/{tier}: rows={len(rows)} "
                    f"exceptions={result['diagnostic_status']}",
                    flush=True,
                )
            except Exception as exc:
                request_errors.append({"week": week, "tier": tier, "error": repr(exc)})
                results.append({"week": week, "tier": tier, "diagnostic_status": "FAIL_REQUEST"})
    summary = {
        "phase": 359,
        "source": "FINRA OTCMarket weeklySummaryHistoric",
        "audit_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "sample_weeks": list(WEEKS),
        "tiers": list(TIERS),
        "requested_fields": FIELDS,
        "finra_api_token_present": bool(token),
        "partitions_expected": len(WEEKS) * len(TIERS),
        "partitions_completed": sum(1 for r in results if r.get("api_record_total_match") is True),
        "rows_total": total_rows,
        "page_count": len(all_pages),
        "partitions": results,
        "request_errors": request_errors,
        "retrieval_gate": "PASS" if len(results) == 4 and not request_errors and all(r.get("api_record_total_match") for r in results) else "FAIL_OR_REVIEW",
        "join_interpretation": "NO_FIRM_AGGREGATE_JOIN_OR_CONCENTRATION_CALCULATED; product-type and symbol key alignment only",
        "pit_status": "FINAL_HISTORICAL_SNAPSHOT_ONLY; interim vintages unavailable",
        "economic_interpretation": "Participant identifiers identify reporting intermediaries, not beneficial owners or trade direction.",
        "forward_returns_used": False,
        "alpha_test_authorized": False,
        "f80_changed": False,
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (out / "page_hashes.json").write_text(json.dumps(all_pages, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2), flush=True)
    print(f"[Phase359] complete retrieval_gate={summary['retrieval_gate']} rows={total_rows} pages={len(all_pages)}", flush=True)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Phase 522: bounded FINRA historical symbol equality-filter probe.

After Phase 521 showed that domainFilters are rejected by weeklySummaryHistoric,
test the documented historical compareFilter=EQUAL path with at most ten
predeclared symbols on one week. Raw rows and all symbol/participant identifiers
remain in memory; the artifact contains only counts, hashes and indexed statuses.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from pathlib import Path

import requests

try:
    from research.phase521_finra_t1_symbol_domain_filter_probe import (
        FIELDS, SAMPLE_SYMBOLS, TIER, WEEK, analyze_symbol, manifest_hash, parse_rows,
    )
except ModuleNotFoundError:
    # Direct script execution places research/ rather than the repository root on sys.path.
    from phase521_finra_t1_symbol_domain_filter_probe import (
        FIELDS, SAMPLE_SYMBOLS, TIER, WEEK, analyze_symbol, manifest_hash, parse_rows,
    )

BASE = "https://api.finra.org"
DATA_URL = f"{BASE}/data/group/otcmarket/name/weeklySummaryHistoric"
PAGE_LIMIT = 5000


class SymbolEqualityFilterRejected(RuntimeError):
    def __init__(self, status_code: int):
        super().__init__(f"FINRA rejected symbol equality filter with HTTP {status_code}")
        self.status_code = status_code


def build_payload(week: str, symbol: str, offset: int = 0):
    return {
        "compareFilters": [
            {"fieldName": "weekStartDate", "fieldValue": week, "compareType": "EQUAL"},
            {"fieldName": "tierIdentifier", "fieldValue": TIER, "compareType": "EQUAL"},
            {"fieldName": "issueSymbolIdentifier", "fieldValue": symbol, "compareType": "EQUAL"},
        ],
        "fields": list(FIELDS),
        "limit": PAGE_LIMIT,
        "offset": int(offset),
    }


def fetch_symbol(session, week: str, symbol: str):
    rows = []
    expected = None
    offset = 0
    while True:
        response = session.post(
            DATA_URL,
            json=build_payload(week, symbol, offset),
            timeout=(20, 90),
        )
        if response.status_code == 400:
            raise SymbolEqualityFilterRejected(400)
        if response.status_code in {401, 403}:
            raise RuntimeError(f"FINRA authorization/access failure: HTTP {response.status_code}")
        response.raise_for_status()
        batch = parse_rows(response.json())
        headers = {str(k).lower(): v for k, v in response.headers.items()}
        total_raw = headers.get("record-total")
        if total_raw is None:
            raise RuntimeError("Missing FINRA Record-Total header")
        total = int(total_raw)
        returned_offset = headers.get("record-offset")
        if returned_offset is not None and int(returned_offset) != offset:
            raise RuntimeError("FINRA Record-Offset mismatch")
        if expected is None:
            expected = total
        elif total != expected:
            raise RuntimeError("FINRA Record-Total changed during pagination")
        rows.extend(batch)
        if len(rows) == expected:
            break
        if len(rows) > expected or not batch:
            raise RuntimeError("FINRA pagination made no progress")
        offset += len(batch)
        if offset > 500000:
            raise RuntimeError("FINRA offset exceeded maximum")
        time.sleep(0.15)
    return rows, expected


def summarize_symbol_result(rows, requested_symbol: str, week: str, record_total: int):
    returned = {
        str(row.get("issueSymbolIdentifier") or "").strip().upper()
        for row in rows if str(row.get("issueSymbolIdentifier") or "").strip()
    }
    requested = requested_symbol.strip().upper()
    exact = returned == {requested} if rows else False
    metrics = analyze_symbol(rows, requested, week) if exact else {
        "bridge_pass": False, "revision_stable": False, "concentration_valid": False
    }
    return {
        "rows_returned": len(rows),
        "record_total": record_total,
        "exact_symbol_match": exact,
        "bridge_pass": bool(metrics["bridge_pass"]),
        "revision_stable": bool(metrics["revision_stable"]),
        "concentration_valid": bool(metrics["concentration_valid"]),
    }


def summarize_results(results, requested_symbols=SAMPLE_SYMBOLS, week=WEEK):
    statuses = []
    for index, item in enumerate(results, start=1):
        statuses.append({
            "symbol_index": index,
            "status": item["status"],
            "rows_returned": item.get("rows_returned", 0),
            "record_total": item.get("record_total", 0),
            "exact_symbol_match": item.get("exact_symbol_match", False),
            "bridge_pass": item.get("bridge_pass", False),
            "revision_stable": item.get("revision_stable", False),
            "concentration_valid": item.get("concentration_valid", False),
        })
    successful = [x for x in statuses if x["status"] == "HTTP_200"]
    return {
        "phase": 522,
        "probe_week": week,
        "dataset": "weeklySummaryHistoric",
        "requested_symbol_count": len(requested_symbols),
        "requested_symbol_manifest_sha256": manifest_hash(requested_symbols),
        "queries_attempted": len(statuses),
        "queries_succeeded": len(successful),
        "queries_rejected": sum(x["status"] == "HTTP_400" for x in statuses),
        "rows_returned_total": sum(x["rows_returned"] for x in statuses),
        "record_total_sum": sum(x["record_total"] for x in statuses),
        "exact_symbol_match_count": sum(x["exact_symbol_match"] for x in statuses),
        "bridge_pass_count": sum(x["bridge_pass"] for x in statuses),
        "revision_stable_count": sum(x["revision_stable"] for x in statuses),
        "concentration_valid_count": sum(x["concentration_valid"] for x in statuses),
        "symbol_status_manifest_sha256": hashlib.sha256(
            json.dumps(statuses, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
        "indexed_symbol_statuses": statuses,
        "probe_pass": bool(
            len(successful) == len(requested_symbols)
            and all(x["exact_symbol_match"] and x["bridge_pass"]
                    and x["revision_stable"] and x["concentration_valid"]
                    for x in statuses)
        ),
        "raw_rows_retained": False,
        "raw_identifiers_retained": False,
        "symbol_strings_retained": False,
        "per_symbol_metrics_retained": False,
        "research_observation_eligible_count": 0,
        "signal_eligible_count": 0,
        "returns_or_alpha_test_authorized": False,
    }


def run_probe(symbols=SAMPLE_SYMBOLS, week=WEEK):
    session = requests.Session()
    session.headers.update({"Accept": "application/json", "Content-Type": "application/json"})
    token = os.environ.get("FINRA_API_TOKEN", "").strip()
    if token:
        session.headers["Authorization"] = f"Bearer {token}"

    results = []
    for symbol in symbols:
        try:
            rows, total = fetch_symbol(session, week, symbol)
            result = summarize_symbol_result(rows, symbol, week, total)
            result["status"] = "HTTP_200"
            results.append(result)
        except SymbolEqualityFilterRejected:
            results.append({"status": "HTTP_400"})
            break
        time.sleep(0.15)
    summary = summarize_results(results, symbols, week)
    summary["probe_status"] = (
        "SYMBOL_EQUALITY_FILTER_SUPPORTED_SAMPLE_PASS"
        if summary["probe_pass"]
        else "SYMBOL_EQUALITY_FILTER_REJECTED_OR_SAMPLE_INCOMPLETE"
    )
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="phase522_output")
    args = parser.parse_args()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    result = run_probe()
    result["audit_timestamp_utc"] = __import__("datetime").datetime.now(
        __import__("datetime").timezone.utc
    ).isoformat()
    (output / "summary.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()

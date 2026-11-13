#!/usr/bin/env python3
"""Phase 365: verify FINRA weekly partition inventory against actual queryable rows.

This is a low-volume data-feasibility probe: 50 targeted POST queries, each
requesting at most 10 sample rows. It tests stale partition metadata, the
documented 12-month current-dataset window, and undocumented NA/NMS tier values.
Only anonymized summaries are written; no raw firm names, MPIDs, CRDs or symbols.
No returns, features, alpha, holdout or F80 changes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import requests

BASE = "https://api.finra.org/data/group/otcmarket/name"
DATASETS = ("weeklySummaryHistoric", "weeklySummary")
WEEKS = ("2021-11-15", "2022-01-03", "2025-10-20", "2025-11-10", "2026-10-19")
TIERS = ("T1", "T2", "OTCE", "NA", "NMS")
SAMPLE_LIMIT = 10
FIELDS = (
    "issueSymbolIdentifier", "issueName", "weekStartDate", "tierIdentifier",
    "tierDescription", "summaryTypeCode", "productTypeCode", "MPID",
    "firmCRDNumber", "marketParticipantName", "totalWeeklyShareQuantity",
    "totalWeeklyTradeCount", "totalNotionalSum", "initialPublishedDate",
    "lastUpdateDate", "lastReportedDate",
)


def build_query(dataset: str, week: str, tier: str) -> dict:
    week_field = "historicalWeek" if dataset == "weeklySummaryHistoric" else "weekStartDate"
    return {
        "fields": list(FIELDS),
        "compareFilters": [
            {"compareType": "EQUAL", "fieldName": week_field, "fieldValue": week},
            {"compareType": "EQUAL", "fieldName": "tierIdentifier", "fieldValue": tier},
        ],
        "limit": SAMPLE_LIMIT,
        "offset": 0,
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
        if data in (None, ""):
            return []
    raise RuntimeError(f"Unexpected FINRA response type: {type(payload).__name__}")


def _values(rows, field):
    return sorted({str(r.get(field)).strip() for r in rows if r.get(field) not in (None, "")})


def summarize_sample(dataset, week, tier, rows, headers):
    summary_counts = Counter(str(r.get("summaryTypeCode") or "__MISSING__") for r in rows)
    participant_id_rows = sum(
        bool(str(r.get("MPID") or "").strip() or str(r.get("firmCRDNumber") or "").strip())
        for r in rows
    )
    de_minimis_rows = sum(
        "de minimis" in str(r.get("marketParticipantName") or "").lower()
        for r in rows
    )
    symbols = {str(r.get("issueSymbolIdentifier") or "").strip() for r in rows}
    symbols.discard("")
    sample_signature = {
        "summary_type_counts": dict(sorted(summary_counts.items())),
        "tier_descriptions": _values(rows, "tierDescription"),
        "product_types": _values(rows, "productTypeCode"),
        "sample_rows": len(rows),
        "unique_symbols": len(symbols),
        "participant_id_rows": participant_id_rows,
        "de_minimis_rows": de_minimis_rows,
        "date_ranges": {
            field: _values(rows, field)
            for field in ("initialPublishedDate", "lastUpdateDate", "lastReportedDate")
        },
    }
    digest = hashlib.sha256(
        json.dumps(sample_signature, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return {
        "dataset": dataset,
        "week": week,
        "tier": tier,
        "requested_week_field": "historicalWeek" if dataset == "weeklySummaryHistoric" else "weekStartDate",
        "record_total": int(headers["record-total"]),
        "records_on_page": int(headers.get("total-records-on-page", len(rows))),
        "record_offset": int(headers.get("record-offset", 0)),
        "sampled_rows": len(rows),
        "page_count_matches": int(headers.get("total-records-on-page", len(rows))) == len(rows),
        "sample_has_rows": bool(rows),
        "sample_summary_type_counts": dict(sorted(summary_counts.items())),
        "sample_tier_descriptions": _values(rows, "tierDescription"),
        "sample_product_types": _values(rows, "productTypeCode"),
        "sample_unique_symbols": len(symbols),
        "sample_participant_id_rows": participant_id_rows,
        "sample_de_minimis_rows": de_minimis_rows,
        "sample_date_values": sample_signature["date_ranges"],
        "sample_signature_sha256": digest,
        "returned_fields": sorted({k for row in rows for k in row}),
        "raw_rows_retained": False,
    }


def fetch_one(session, dataset, week, tier):
    url = f"{BASE}/{dataset}"
    body = build_query(dataset, week, tier)
    last_error = None
    for attempt in range(4):
        try:
            response = session.post(url, json=body, timeout=(20, 90))
            if response.status_code in {408, 429, 500, 502, 503, 504}:
                if attempt == 3:
                    response.raise_for_status()
                retry_after = response.headers.get("Retry-After")
                try:
                    delay = float(retry_after) if retry_after else 2 * (2 ** attempt)
                except (TypeError, ValueError):
                    delay = 2 * (2 ** attempt)
                time.sleep(max(0, min(delay, 30)))
                continue
            response.raise_for_status()
            rows = parse_rows(response.json())
            headers = {str(k).lower(): v for k, v in response.headers.items()}
            if "record-total" not in headers:
                raise RuntimeError(f"Missing Record-Total for {dataset}/{week}/{tier}")
            result = summarize_sample(dataset, week, tier, rows, headers)
            if result["records_on_page"] != len(rows):
                raise RuntimeError(f"Page row count mismatch for {dataset}/{week}/{tier}")
            if result["record_total"] > 0 and not rows:
                raise RuntimeError(f"Positive Record-Total with empty sample for {dataset}/{week}/{tier}")
            if result["record_offset"] != 0:
                raise RuntimeError(f"Unexpected nonzero Record-Offset for {dataset}/{week}/{tier}")
            if len(rows) > SAMPLE_LIMIT:
                raise RuntimeError(f"Sample exceeded requested limit for {dataset}/{week}/{tier}")
            if any(str(r.get("tierIdentifier") or "").strip() != tier for r in rows):
                raise RuntimeError(f"Returned tier mismatch for {dataset}/{week}/{tier}")
            if any(str(r.get("weekStartDate") or "").strip() != week for r in rows):
                raise RuntimeError(f"Returned week mismatch for {dataset}/{week}/{tier}")
            return result
        except (requests.RequestException, ValueError, RuntimeError) as exc:
            last_error = exc
            if attempt == 3:
                raise
            time.sleep(min(2 * (2 ** attempt), 20))
    raise RuntimeError(f"Unable to retrieve {dataset}/{week}/{tier}: {last_error}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="phase365_finra_weekly_partition_data_probe")
    args = parser.parse_args()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers.update({
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Data-API-Version": "1",
        "User-Agent": "SmartMoneyResearch-Phase365/1.0",
    })
    token = os.getenv("FINRA_API_TOKEN", "").strip()
    if token:
        session.headers["Authorization"] = f"Bearer {token}"

    results, errors = [], []
    for dataset in DATASETS:
        for week in WEEKS:
            for tier in TIERS:
                print(f"[Phase365] probe {dataset}/{week}/{tier}", flush=True)
                try:
                    item = fetch_one(session, dataset, week, tier)
                    results.append(item)
                    print(
                        f"[Phase365] result {dataset}/{week}/{tier}: "
                        f"total={item['record_total']} sampled={item['sampled_rows']}",
                        flush=True,
                    )
                except Exception as exc:
                    errors.append({
                        "dataset": dataset, "week": week, "tier": tier,
                        "error": repr(exc),
                    })

    by_key = {(r["dataset"], r["week"], r["tier"]): r for r in results}
    comparisons = []
    for week in WEEKS:
        for tier in TIERS:
            historic = by_key.get(("weeklySummaryHistoric", week, tier))
            current = by_key.get(("weeklySummary", week, tier))
            if historic is not None and current is not None:
                comparisons.append({
                    "week": week,
                    "tier": tier,
                    "historic_record_total": historic["record_total"],
                    "current_record_total": current["record_total"],
                    "record_totals_equal": historic["record_total"] == current["record_total"],
                    "sample_signatures_equal": historic["sample_signature_sha256"] == current["sample_signature_sha256"],
                })

    current_old_rows = [
        r for r in results
        if r["dataset"] == "weeklySummary"
        and r["week"] < "2025-11-13"
        and r["record_total"] > 0
    ]
    undocumented_tier_rows = [
        r for r in results
        if r["tier"] in {"NA", "NMS"} and r["record_total"] > 0
    ]
    summary = {
        "phase": 365,
        "source": "FINRA OTCMarket weeklySummaryHistoric + weeklySummary",
        "audit_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "weeks_probed": list(WEEKS),
        "tiers_probed": list(TIERS),
        "datasets": list(DATASETS),
        "queries_expected": len(DATASETS) * len(WEEKS) * len(TIERS),
        "queries_completed": len(results),
        "query_errors": errors,
        "all_page_counts_match": all(r["page_count_matches"] for r in results),
        "historic_current_overlap_comparisons": comparisons,
        "current_dataset_old_partition_nonzero_count": len(current_old_rows),
        "current_dataset_old_partition_nonzero_examples": [
            {"week": r["week"], "tier": r["tier"], "record_total": r["record_total"]}
            for r in current_old_rows[:25]
        ],
        "undocumented_na_nms_nonzero_count": len(undocumented_tier_rows),
        "undocumented_na_nms_nonzero_examples": [
            {"dataset": r["dataset"], "week": r["week"], "tier": r["tier"],
             "record_total": r["record_total"], "summary_types": r["sample_summary_type_counts"],
             "tier_descriptions": r["sample_tier_descriptions"]}
            for r in undocumented_tier_rows[:25]
        ],
        "results": results,
        "raw_rows_retained": False,
        "forward_returns_used": False,
        "alpha_test_authorized": False,
        "holdout_used": False,
        "f80_changed": False,
    }
    (output / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2), flush=True)
    print(
        f"[Phase365] completed={len(results)}/{summary['queries_expected']} "
        f"errors={len(errors)} current_old_nonzero={len(current_old_rows)} "
        f"na_nms_nonzero={len(undocumented_tier_rows)}",
        flush=True,
    )


if __name__ == "__main__":
    main()

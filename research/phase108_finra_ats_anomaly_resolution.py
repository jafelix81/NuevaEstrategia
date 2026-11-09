#!/usr/bin/env python3
"""Phase 108: targeted FINRA ATS anomaly-resolution probe.

Data-integrity/PIT investigation only. No prices, forward returns or alpha.
"""
from __future__ import annotations

import csv
import hashlib
import json
import time
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from pathlib import Path

import requests

BASE = "https://api.finra.org/data/group/otcmarket/name/weeklySummaryHistoric"
PARTITIONS = (("2022-01-03", "T2"), ("2025-01-06", "T2"))
PAGE_SIZE = 5000
MAX_PAGES = 200
FIELDS = [
    "issueSymbolIdentifier",
    "issueName",
    "firmCRDNumber",
    "MPID",
    "marketParticipantName",
    "tierIdentifier",
    "tierDescription",
    "summaryStartDate",
    "totalWeeklyTradeCount",
    "totalWeeklyShareQuantity",
    "productTypeCode",
    "summaryTypeCode",
    "weekStartDate",
    "lastUpdateDate",
    "initialPublishedDate",
    "lastReportedDate",
]
SYMBOL_BEARING = {
    "ATS_W_SMBL", "ATS_W_SMBL_FIRM",
    "OTC_W_SMBL", "OTC_W_SMBL_FIRM",
}
SYMBOL_AGGREGATES = {"ATS_W_SMBL", "OTC_W_SMBL"}
OUT = Path("phase108_finra_ats_anomaly_resolution")
PAGE_FIELDS = [
    "week", "tier", "page", "offset", "rows", "record_total",
    "page_count_source", "record_limit", "record_offset", "request_attempts",
    "request_id", "sha256",
]


def parse_response(obj) -> list[dict]:
    if isinstance(obj, list):
        return [x for x in obj if isinstance(x, dict)]
    if isinstance(obj, dict):
        if obj.get("message") or obj.get("statusCode"):
            raise ValueError(f"FINRA error object: {obj}")
        data = obj.get("data", [])
        if isinstance(data, dict):
            data = data.get("data", [])
        if isinstance(data, list):
            return [x for x in data if isinstance(x, dict)]
    raise ValueError(f"Unexpected FINRA response shape: {type(obj).__name__}")


def parse_page_metadata(headers, rows, week: str, tier: str, offset: int):
    normalized = {str(k).lower(): v for k, v in headers.items()}
    raw_total = normalized.get("record-total")
    if raw_total is None:
        raise RuntimeError("Missing Record-Total")
    total = int(raw_total)
    raw_count = normalized.get("total-records-on-page")
    count = int(raw_count) if raw_count is not None else len(rows)
    source = "header" if raw_count is not None else "body_length"
    if count != len(rows):
        raise RuntimeError(f"Page count mismatch: {count} != {len(rows)}")
    if count > PAGE_SIZE:
        raise RuntimeError(f"Page exceeds limit: {count}")
    raw_offset = normalized.get("record-offset")
    if raw_offset is not None and int(raw_offset) != offset:
        raise RuntimeError(f"Record-Offset mismatch: {raw_offset} != {offset}")
    return total, count, source


def build_payload(week: str, tier: str, offset: int):
    return {
        "fields": FIELDS,
        "compareFilters": [
            {"compareType": "equal", "fieldName": "historicalWeek", "fieldValue": week},
            {"compareType": "equal", "fieldName": "tierIdentifier", "fieldValue": tier},
        ],
        "limit": PAGE_SIZE,
        "offset": offset,
    }


def post_page(session, payload):
    retryable = {408, 429, 500, 502, 503, 504}
    for attempt in range(4):
        try:
            response = session.post(BASE, json=payload, timeout=(20, 120))
        except requests.RequestException:
            if attempt == 3:
                raise
            time.sleep(min(3 * (2 ** attempt), 30))
            continue
        if response.status_code in retryable:
            if attempt == 3:
                response.raise_for_status()
            try:
                delay = float(response.headers.get("Retry-After", 3 * (2 ** attempt)))
            except (TypeError, ValueError):
                delay = 3 * (2 ** attempt)
            time.sleep(max(0, min(delay, 60)))
            continue
        response.raise_for_status()
        return response, attempt + 1
    raise RuntimeError("FINRA retries exhausted")


def fetch_partition(session, week: str, tier: str):
    rows, pages = [], []
    offset, expected_total = 0, None
    for page in range(MAX_PAGES):
        response, attempts = post_page(session, build_payload(week, tier, offset))
        page_rows = parse_response(response.json())
        total, count, count_source = parse_page_metadata(
            response.headers, page_rows, week, tier, offset
        )
        if expected_total is None:
            expected_total = total
        elif total != expected_total:
            raise RuntimeError(f"Record-Total changed: {total} != {expected_total}")
        pages.append({
            "week": week, "tier": tier, "page": page, "offset": offset,
            "rows": len(page_rows), "record_total": total,
            "page_count_source": count_source,
            "record_limit": response.headers.get("Record-Limit"),
            "record_offset": response.headers.get("Record-Offset"),
            "request_attempts": attempts,
            "request_id": response.headers.get("FINRA-api-request-id"),
            "sha256": hashlib.sha256(response.content).hexdigest(),
        })
        rows.extend(page_rows)
        offset += count
        if offset >= total:
            break
        if count == 0:
            raise RuntimeError("Empty page before Record-Total reached")
    else:
        raise RuntimeError("Pagination guard exceeded")
    if expected_total is None or len(rows) != expected_total:
        raise RuntimeError(f"Partition incomplete: {len(rows)} != {expected_total}")
    return rows, pages, expected_total


def clean(value):
    return "" if value is None else str(value).strip()


def coarse_key(row):
    return (
        clean(row.get("issueSymbolIdentifier")).upper(),
        clean(row.get("weekStartDate"))[:10],
        clean(row.get("tierIdentifier")).upper(),
        clean(row.get("summaryTypeCode")).upper(),
        clean(row.get("productTypeCode")).upper(),
    )


def expanded_candidate_key(row):
    # Candidate row identity: retain participant identifiers and the latest
    # contributing-firm report date. This is a diagnostic key, not yet a
    # declared FINRA natural key.
    return coarse_key(row) + (
        clean(row.get("MPID")).upper(),
        clean(row.get("firmCRDNumber")),
        clean(row.get("lastReportedDate"))[:10],
    )


def partition_issues(rows, week: str, tier: str):
    date_tier = []
    missing_symbol = []
    for i, row in enumerate(rows):
        actual_week = clean(row.get("weekStartDate"))[:10]
        actual_tier = clean(row.get("tierIdentifier")).upper()
        if actual_week != week or actual_tier != tier:
            date_tier.append({
                "row_index": i, "actual_week": actual_week,
                "actual_tier": actual_tier, "expected_week": week,
                "expected_tier": tier,
            })
        st = clean(row.get("summaryTypeCode")).upper()
        if st in SYMBOL_BEARING and not clean(row.get("issueSymbolIdentifier")):
            missing_symbol.append({"row_index": i, **{f: row.get(f) for f in FIELDS}})
    return date_tier, missing_symbol


def grouped_collisions(rows, key_fn):
    groups = defaultdict(list)
    for row in rows:
        groups[key_fn(row)].append(row)
    return [(key, group) for key, group in groups.items() if len(group) > 1]


def analyze_partition(rows, week: str, tier: str, record_total: int, pages: list[dict]):
    date_tier, missing_symbol = partition_issues(rows, week, tier)
    coarse = grouped_collisions(rows, coarse_key)
    expanded = grouped_collisions(rows, expanded_candidate_key)
    symbol_firm = [
        r for r in rows
        if clean(r.get("summaryTypeCode")).upper().endswith("_SMBL_FIRM")
    ]
    symbol_aggregate = [r for r in rows if clean(r.get("summaryTypeCode")).upper() in SYMBOL_AGGREGATES]
    missing_firm_identity = [
        r for r in symbol_firm
        if not clean(r.get("MPID")) and not clean(r.get("firmCRDNumber"))
    ]
    revised = sum(
        1 for r in symbol_aggregate
        if clean(r.get("initialPublishedDate")) and clean(r.get("lastUpdateDate"))
        and clean(r.get("lastUpdateDate")) > clean(r.get("initialPublishedDate"))
    )
    lnd_rows = [
        {f: r.get(f) for f in FIELDS}
        for r in rows
        if clean(r.get("issueSymbolIdentifier")).upper() == "LND"
        and week == "2025-01-06"
        and clean(r.get("summaryTypeCode")).upper() in {"ATS_W_SMBL", "OTC_W_SMBL", "ATS_W_SMBL_FIRM", "OTC_W_SMBL_FIRM"}
    ]
    missing_by_type = Counter(
        clean(r.get("summaryTypeCode")).upper() for r in missing_symbol
    )
    coarse_examples = []
    for key, group in coarse[:50]:
        coarse_examples.append({
            "key": list(key),
            "row_count": len(group),
            "distinct_last_reported_dates": sorted({clean(r.get("lastReportedDate")) for r in group}),
            "distinct_mpids": sorted({clean(r.get("MPID")) for r in group}),
            "distinct_firm_crds": sorted({clean(r.get("firmCRDNumber")) for r in group}),
            "rows": [{f: r.get(f) for f in FIELDS} for r in group[:10]],
        })
    expanded_examples = []
    for key, group in expanded[:50]:
        expanded_examples.append({
            "key": list(key),
            "row_count": len(group),
            "rows": [{f: r.get(f) for f in FIELDS} for r in group[:10]],
        })
    return {
        "week": week,
        "tier": tier,
        "rows_total": len(rows),
        "pages": len(pages),
        "record_total": record_total,
        "record_total_match": len(rows) == record_total,
        "week_tier_mismatch_rows": len(date_tier),
        "week_tier_mismatch_examples": date_tier[:20],
        "missing_symbol_rows": len(missing_symbol),
        "missing_symbol_by_summary_type": dict(missing_by_type),
        "missing_symbol_examples": missing_symbol[:20],
        "symbol_firm_rows": len(symbol_firm),
        "symbol_firm_rows_without_mpid_and_crd": len(missing_firm_identity),
        "symbol_firm_missing_identity_examples": [
            {f: r.get(f) for f in FIELDS} for r in missing_firm_identity[:20]
        ],
        "symbol_aggregate_rows": len(symbol_aggregate),
        "symbol_aggregate_rows_updated_after_first_publication": revised,
        "coarse_key_collision_groups": len(coarse),
        "expanded_candidate_key_collision_groups": len(expanded),
        "coarse_collision_examples": coarse_examples,
        "expanded_collision_examples": expanded_examples,
        "lnd_rows": lnd_rows,
        "lnd_row_count": len(lnd_rows),
        "mpid_nonnull_symbol_firm_pct": round(
            100 * sum(bool(clean(r.get("MPID"))) for r in symbol_firm) / len(symbol_firm), 2
        ) if symbol_firm else None,
        "firm_crd_nonnull_symbol_firm_pct": round(
            100 * sum(bool(clean(r.get("firmCRDNumber"))) for r in symbol_firm) / len(symbol_firm), 2
        ) if symbol_firm else None,
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update({
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "SmartMoneyResearch-Phase108/1.0",
    })
    summaries, page_hashes, errors = [], [], []
    for week, tier in PARTITIONS:
        print(f"[Phase108] start {week}/{tier}", flush=True)
        try:
            rows, pages, total = fetch_partition(session, week, tier)
            page_hashes.extend(pages)
            summary = analyze_partition(rows, week, tier, total, pages)
            summaries.append(summary)
            print(
                f"[Phase108] complete {week}/{tier} rows={len(rows)} "
                f"pages={len(pages)} week_tier_mismatch={summary['week_tier_mismatch_rows']} "
                f"missing_symbol={summary['missing_symbol_rows']} "
                f"coarse_collisions={summary['coarse_key_collision_groups']} "
                f"expanded_collisions={summary['expanded_candidate_key_collision_groups']}",
                flush=True,
            )
        except Exception as exc:
            errors.append({"week": week, "tier": tier, "error": repr(exc)})
            print(f"[Phase108] ERROR {week}/{tier}: {exc!r}", flush=True)

    summary = {
        "phase": 108,
        "source": "FINRA OTCMarket weeklySummaryHistoric",
        "audit_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "partitions_requested": [{"week": w, "tier": t} for w, t in PARTITIONS],
        "partitions_completed": len(summaries),
        "partitions": summaries,
        "page_hash_count": len(page_hashes),
        "errors": errors,
        "fields_requested": FIELDS,
        "expanded_candidate_key": [
            "issueSymbolIdentifier", "weekStartDate", "tierIdentifier",
            "summaryTypeCode", "productTypeCode", "MPID", "firmCRDNumber",
            "lastReportedDate",
        ],
        "interpretation": (
            "The expanded key is diagnostic only. FINRA's definitive natural-key/"
            "revision semantics have not yet been established."
        ),
        "forward_returns_used": False,
        "alpha_test_authorized": False,
        "f80_changed": False,
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (OUT / "anomaly_rows.json").write_text(json.dumps(summaries, indent=2), encoding="utf-8")
    with (OUT / "page_hashes.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=PAGE_FIELDS)
        writer.writeheader()
        writer.writerows(page_hashes)
    print(json.dumps(summary, indent=2), flush=True)
    if errors or len(summaries) != len(PARTITIONS):
        raise RuntimeError("Phase 108 did not complete all targeted partitions")


if __name__ == "__main__":
    main()

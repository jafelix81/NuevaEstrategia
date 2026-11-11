#!/usr/bin/env python3
"""Targeted FINRA ATS duplicate-grain diagnostics; no row adjudication."""
from __future__ import annotations
import csv, hashlib, json
from collections import defaultdict
from pathlib import Path
from typing import Any
import requests
from research.phase100_finra_ats_revalidation import (
    BASE, FIELDS, MAX_OFFSET, MAX_SYNC_PAGES, SYMBOL_AGGREGATES,
    parse_response, parse_sync_page_metadata, post_sync_page, validate_partition_rows,
)

WEEK, TIER = "2025-07-07", "T2"
OUT = Path("phase278_finra_ats_duplicate_grain_followup")
KEY = ("issueSymbolIdentifier", "weekStartDate", "tierIdentifier", "summaryTypeCode", "productTypeCode")
DETAIL = KEY + ("totalWeeklyShareQuantity", "totalWeeklyTradeCount", "initialPublishedDate", "lastUpdateDate", "lastReportedDate")
HEX = set("0123456789abcdef")

class PageBodyParseError(ValueError):
    def __init__(self, diagnostic: dict[str, Any]):
        super().__init__("FINRA_RESPONSE_BODY_PARSE_FAILED")
        self.diagnostic = diagnostic

def clean(v: Any) -> str:
    return "" if v is None else str(v).strip()

def payload(row: dict[str, Any]) -> dict[str, str]:
    return {k: clean(row.get(k)) for k in DETAIL}

def digest(row: dict[str, str]) -> str:
    return hashlib.sha256(json.dumps(row, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

def parse_page_body(content: bytes) -> tuple[list[dict[str, Any]], int]:
    """Accept one JSON value or a stream of adjacent JSON values; reject all other tails."""
    body = content.decode("utf-8-sig")
    decoder, pos, values = json.JSONDecoder(), 0, []
    try:
        while pos < len(body):
            while pos < len(body) and body[pos].isspace(): pos += 1
            if pos == len(body): break
            value, end = decoder.raw_decode(body, pos)
            values.append(value); pos = end
        if not values: raise ValueError("EMPTY_JSON_RESPONSE")
        rows = []
        for value in values:
            if isinstance(value, list):
                if not all(isinstance(x, dict) for x in value): raise ValueError("NON_OBJECT_ARRAY_ITEM")
                rows.extend(value)
            elif isinstance(value, dict) and ("data" in value or "message" in value or "statusCode" in value):
                rows.extend(parse_response(value))
            elif isinstance(value, dict) and "issueSymbolIdentifier" in value and "summaryTypeCode" in value:
                rows.append(value)
            else: raise ValueError("UNEXPECTED_JSON_SHAPE")
        return rows, len(values)
    except (json.JSONDecodeError, ValueError) as exc:
        raise PageBodyParseError({
            "body_bytes": len(content), "body_sha256": hashlib.sha256(content).hexdigest(),
            "top_level_json_values_parsed": len(values), "parse_error_type": type(exc).__name__,
            "parse_error_position": getattr(exc, "pos", None),
            "parse_error_line": getattr(exc, "lineno", None), "parse_error_column": getattr(exc, "colno", None),
            "first_non_whitespace_character": next((c for c in body if not c.isspace()), "")[:1],
            "trailing_first_non_whitespace_character": next((c for c in body[pos:] if not c.isspace()), "")[:1],
            "raw_body_persisted": False,
        }) from exc

def inspect_duplicates(rows: list[dict[str, Any]]) -> dict[str, Any]:
    groups: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        st = clean(row.get("summaryTypeCode")).upper()
        if st not in SYMBOL_AGGREGATES: continue
        key = (clean(row.get("issueSymbolIdentifier")).upper(), clean(row.get("weekStartDate"))[:10],
               clean(row.get("tierIdentifier")).upper(), st, clean(row.get("productTypeCode")).upper())
        groups[key].append(row)
    details = []
    for key, group in sorted(groups.items()):
        if len(group) < 2: continue
        items = [payload(r) for r in group]
        hashes = [digest(x) for x in items]
        reported = sorted({x["lastReportedDate"][:10] for x in items})
        extended_counts = [sum(x["lastReportedDate"][:10] == d for x in items) for d in reported]
        differing = {f: sorted({x[f] for x in items}) for f in DETAIL if len({x[f] for x in items}) > 1}
        details.append({
            "base_key": list(key), "row_count": len(group), "exact_duplicate": len(set(hashes)) == 1,
            "row_sha256": hashes, "unique_last_reported_dates": reported,
            "split_by_last_reported_date": len(reported) > 1,
            "extended_key_duplicate_after_last_reported_date": any(n > 1 for n in extended_counts),
            "differing_fields": differing, "rows": items,
        })
    exact = sum(x["exact_duplicate"] for x in details)
    split = sum(x["split_by_last_reported_date"] for x in details)
    extended = sum(x["extended_key_duplicate_after_last_reported_date"] for x in details)
    return {
        "candidate_key_fields": list(KEY), "candidate_key_group_count": len(details),
        "exact_duplicate_groups": exact, "conflicting_groups": len(details) - exact,
        "groups_split_by_last_reported_date": split,
        "groups_still_duplicate_after_last_reported_date": extended, "groups": details,
        "last_reported_date_interpretation": "Diagnostic split only; not a documented natural key. No row selected, summed or deduplicated.",
    }

def fetch_partition(session: requests.Session) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows, pages, offset, total = [], [], 0, None
    for page_no in range(MAX_SYNC_PAGES):
        response, attempts = post_sync_page(session, WEEK, TIER, offset)
        try:
            page_rows, value_count = parse_page_body(response.content)
        except PageBodyParseError as exc:
            exc.diagnostic.update({
                "http_status": response.status_code, "content_type": response.headers.get("Content-Type"),
                "request_id": response.headers.get("FINRA-api-request-id"),
                "record_total_header": response.headers.get("Record-Total"),
                "page_count_header": response.headers.get("Total-Records-On-Page"),
                "record_offset_header": response.headers.get("Record-Offset"),
                "requested_week": WEEK, "requested_tier": TIER, "requested_offset": offset,
            })
            OUT.mkdir(parents=True, exist_ok=True)
            (OUT / "transport_error.json").write_text(json.dumps(exc.diagnostic, indent=2, sort_keys=True), encoding="utf-8")
            raise
        record_total, page_count, count_source = parse_sync_page_metadata(response.headers, page_rows, WEEK, TIER, offset)
        if total is None: total = record_total
        elif total != record_total: raise RuntimeError("RECORD_TOTAL_CHANGED")
        pages.append({
            "week": WEEK, "tier": TIER, "page": page_no, "offset": offset, "rows": len(page_rows),
            "record_total": record_total, "page_count_source": count_source, "request_attempts": attempts,
            "request_id": response.headers.get("FINRA-api-request-id"),
            "sha256": hashlib.sha256(response.content).hexdigest(), "top_level_json_value_count": value_count,
        })
        rows.extend(page_rows); offset += page_count
        if offset >= record_total: break
        if page_count == 0: raise RuntimeError("EMPTY_PAGE_BEFORE_RECORD_TOTAL")
        if offset > MAX_OFFSET: raise RuntimeError("SYNC_OFFSET_CEILING_EXCEEDED")
    else: raise RuntimeError("SYNC_PAGINATION_GUARD_EXCEEDED")
    if total is None or len(rows) != total: raise RuntimeError("RECORD_TOTAL_NOT_RECONCILED")
    return rows, pages

def build_result(rows: list[dict[str, Any]], pages: list[dict[str, Any]]) -> dict[str, Any]:
    if not pages: raise ValueError("NO_PAGE_METADATA")
    total, offset, hashes = int(pages[0]["record_total"]), 0, []
    for i, p in enumerate(pages):
        if int(p.get("page", -1)) != i: raise ValueError("NONCONTIGUOUS_PAGE_NUMBER")
        if int(p.get("offset", -1)) != offset: raise ValueError("NONCONTIGUOUS_PAGE_OFFSET")
        if int(p.get("record_total", -1)) != total: raise ValueError("RECORD_TOTAL_CHANGED")
        if clean(p.get("week")) != WEEK or clean(p.get("tier")).upper() != TIER: raise ValueError("PAGE_PARTITION_MISMATCH")
        n, h = int(p.get("rows", -1)), clean(p.get("sha256")).lower()
        if n < 0: raise ValueError("NEGATIVE_PAGE_ROW_COUNT")
        if len(h) != 64 or not set(h).issubset(HEX): raise ValueError("INVALID_PAGE_SHA256")
        hashes.append({k: p.get(k) for k in ("page", "offset", "rows", "record_total", "request_id", "sha256", "top_level_json_value_count")})
        offset += n
    if offset != len(rows) or len(rows) != total: raise ValueError("RECORD_TOTAL_NOT_RECONCILED")
    problems = validate_partition_rows(rows, WEEK, TIER)
    if problems: raise ValueError("PARTITION_ROW_VALIDATION_FAILED:" + "|".join(problems[:5]))
    dup = inspect_duplicates(rows)
    return {
        "phase": 278,
        "status": "TARGETED_PARTITION_COMPLETE_WITH_CONFLICTS" if dup["conflicting_groups"] else "TARGETED_PARTITION_COMPLETE_NO_CONFLICTS",
        "source": {"dataset": "FINRA OTCMarket weeklySummaryHistoric", "endpoint": BASE,
                   "request_mode": "synchronous paginated; no FINRA_API_TOKEN supplied", "week": WEEK, "tier": TIER, "fields_requested": FIELDS},
        "retrieval": {"rows_total": len(rows), "api_record_total_reconciled": True, "page_count": len(pages),
                      "page_hash_count": len(hashes), "page_hashes": hashes, "partition_row_validation_problem_count": 0},
        "duplicate_audit": dup,
        "pit": {"strict_pit_admitted": False, "reason": "Current snapshot does not reconstruct immutable as-first-published values or first receipt."},
        "economic_interpretation": {"alpha_test_authorized": False, "forward_returns_used": False,
                                    "bootstrap_loo_oos_used": False, "holdout_used": False,
                                    "beneficial_owner_known": False, "aggressor_direction_known": False},
        "controls": {"f80_frozen": True, "production_changed": False, "universe_changed": False,
                     "capital_changed": False, "data_purchased": False, "vendor_contacted": False,
                     "full_partition_rows_persisted": False},
        "decision": "Keep every conflicting group quarantined. lastReportedDate is diagnostic only, not an admitted natural key. No feature, sum, row selection or alpha test.",
    }

def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    try:
        rows, pages = fetch_partition(requests.Session())
        result = build_result(rows, pages)
    except Exception as exc:
        if not (OUT / "transport_error.json").exists():
            (OUT / "transport_error.json").write_text(json.dumps({
                "status": "TARGETED_FETCH_OR_VALIDATION_FAILED", "error_type": type(exc).__name__,
                "error": str(exc)[:500], "raw_partition_rows_persisted": False,
            }, indent=2, sort_keys=True), encoding="utf-8")
        raise
    (OUT / "summary.json").write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    with (OUT / "page_hashes.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["page", "offset", "rows", "record_total", "request_id", "sha256", "top_level_json_value_count"])
        w.writeheader(); w.writerows(result["retrieval"]["page_hashes"])
    print(f"PHASE278_STATUS={result['status']} rows={len(rows)} pages={len(pages)} "
          f"duplicate_groups={result['duplicate_audit']['candidate_key_group_count']} "
          f"conflicting={result['duplicate_audit']['conflicting_groups']} "
          f"split_by_last_reported={result['duplicate_audit']['groups_split_by_last_reported_date']} "
          f"extended_duplicates={result['duplicate_audit']['groups_still_duplicate_after_last_reported_date']}", flush=True)

if __name__ == "__main__":
    main()

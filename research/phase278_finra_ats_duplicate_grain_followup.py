#!/usr/bin/env python3
"""Phase 278: targeted FINRA ATS duplicate-grain follow-up.

Re-fetches only the Phase 277 exception partition and emits a minimal
conflict-only diagnostic. It never selects, sums, or deduplicates conflicting
rows and does not persist the full partition.
"""
from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import requests

from research.phase100_finra_ats_revalidation import (
    BASE,
    FIELDS,
    SYMBOL_AGGREGATES,
    fetch_partition_sync,
    validate_partition_rows,
)

WEEK = "2025-07-07"
TIER = "T2"
OUT = Path("phase278_finra_ats_duplicate_grain_followup")
BASE_KEY_FIELDS = (
    "issueSymbolIdentifier",
    "weekStartDate",
    "tierIdentifier",
    "summaryTypeCode",
    "productTypeCode",
)
DETAIL_FIELDS = (
    "issueSymbolIdentifier",
    "weekStartDate",
    "tierIdentifier",
    "summaryTypeCode",
    "productTypeCode",
    "totalWeeklyShareQuantity",
    "totalWeeklyTradeCount",
    "initialPublishedDate",
    "lastUpdateDate",
    "lastReportedDate",
)
HEX = set("0123456789abcdef")


def _clean(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _row_payload(row: dict[str, Any]) -> dict[str, str]:
    return {field: _clean(row.get(field)) for field in DETAIL_FIELDS}


def _row_digest(payload: dict[str, str]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def inspect_duplicate_groups(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Describe duplicate symbol-aggregate candidate keys without adjudicating them."""
    groups: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        summary_type = _clean(row.get("summaryTypeCode")).upper()
        if summary_type not in SYMBOL_AGGREGATES:
            continue
        key = (
            _clean(row.get("issueSymbolIdentifier")).upper(),
            _clean(row.get("weekStartDate"))[:10],
            _clean(row.get("tierIdentifier")).upper(),
            summary_type,
            _clean(row.get("productTypeCode")).upper(),
        )
        groups[key].append(row)

    details: list[dict[str, Any]] = []
    for key, group in sorted(groups.items()):
        if len(group) < 2:
            continue
        payloads = [_row_payload(row) for row in group]
        signatures = {_row_digest(payload) for payload in payloads}
        last_reported = sorted({payload["lastReportedDate"][:10] for payload in payloads})
        extended_groups: dict[str, int] = defaultdict(int)
        for value in last_reported:
            extended_groups[value] = sum(
                1 for payload in payloads if payload["lastReportedDate"][:10] == value
            )
        extended_duplicate = any(count > 1 for count in extended_groups.values())
        differing_fields = {
            field: sorted({payload[field] for payload in payloads})
            for field in DETAIL_FIELDS
            if len({payload[field] for payload in payloads}) > 1
        }
        details.append({
            "base_key": list(key),
            "row_count": len(group),
            "exact_duplicate": len(signatures) == 1,
            "row_sha256": [_row_digest(payload) for payload in payloads],
            "unique_last_reported_dates": last_reported,
            "split_by_last_reported_date": len(last_reported) > 1,
            "extended_key_duplicate_after_last_reported_date": extended_duplicate,
            "differing_fields": differing_fields,
            "rows": payloads,
        })

    exact = sum(1 for item in details if item["exact_duplicate"])
    conflicting = len(details) - exact
    split = sum(1 for item in details if item["split_by_last_reported_date"])
    extended = sum(1 for item in details if item["extended_key_duplicate_after_last_reported_date"])
    return {
        "candidate_key_fields": list(BASE_KEY_FIELDS),
        "candidate_key_group_count": len(details),
        "exact_duplicate_groups": exact,
        "conflicting_groups": conflicting,
        "groups_split_by_last_reported_date": split,
        "groups_still_duplicate_after_last_reported_date": extended,
        "groups": details,
        "last_reported_date_interpretation": (
            "A diagnostic split only. FINRA documentation has not established lastReportedDate "
            "as a natural key; no row is selected, summed, or deduplicated."
        ),
    }


def _validate_pages(rows: list[dict[str, Any]], pages: list[dict[str, Any]]) -> dict[str, Any]:
    if not pages:
        raise ValueError("NO_PAGE_METADATA")
    expected_total = int(pages[0]["record_total"])
    expected_offset = 0
    hashes: list[dict[str, Any]] = []
    for page_number, page in enumerate(pages):
        if int(page.get("page", -1)) != page_number:
            raise ValueError("NONCONTIGUOUS_PAGE_NUMBER")
        if int(page.get("offset", -1)) != expected_offset:
            raise ValueError("NONCONTIGUOUS_PAGE_OFFSET")
        if int(page.get("record_total", -1)) != expected_total:
            raise ValueError("RECORD_TOTAL_CHANGED")
        if _clean(page.get("week")) != WEEK or _clean(page.get("tier")).upper() != TIER:
            raise ValueError("PAGE_PARTITION_MISMATCH")
        count = int(page.get("rows", -1))
        if count < 0:
            raise ValueError("NEGATIVE_PAGE_ROW_COUNT")
        digest = _clean(page.get("sha256")).lower()
        if len(digest) != 64 or not set(digest).issubset(HEX):
            raise ValueError("INVALID_PAGE_SHA256")
        hashes.append({
            "page": page_number,
            "offset": expected_offset,
            "rows": count,
            "record_total": expected_total,
            "request_id": _clean(page.get("request_id")),
            "sha256": digest,
        })
        expected_offset += count
    if expected_offset != len(rows) or len(rows) != expected_total:
        raise ValueError("RECORD_TOTAL_NOT_RECONCILED")
    return {"record_total": expected_total, "page_count": len(pages), "page_hashes": hashes}


def build_result(rows: list[dict[str, Any]], pages: list[dict[str, Any]]) -> dict[str, Any]:
    retrieval = _validate_pages(rows, pages)
    problems = validate_partition_rows(rows, WEEK, TIER)
    if problems:
        raise ValueError("PARTITION_ROW_VALIDATION_FAILED:" + "|".join(problems[:5]))
    duplicates = inspect_duplicate_groups(rows)
    return {
        "phase": 278,
        "status": "TARGETED_PARTITION_COMPLETE_WITH_CONFLICTS" if duplicates["conflicting_groups"] else "TARGETED_PARTITION_COMPLETE_NO_CONFLICTS",
        "source": {
            "dataset": "FINRA OTCMarket weeklySummaryHistoric",
            "endpoint": BASE,
            "request_mode": "synchronous paginated; no FINRA_API_TOKEN supplied",
            "week": WEEK,
            "tier": TIER,
            "fields_requested": FIELDS,
        },
        "retrieval": {
            "rows_total": len(rows),
            "api_record_total_reconciled": True,
            "page_count": retrieval["page_count"],
            "page_hash_count": len(retrieval["page_hashes"]),
            "page_hashes": retrieval["page_hashes"],
            "partition_row_validation_problem_count": 0,
        },
        "duplicate_audit": duplicates,
        "pit": {
            "strict_pit_admitted": False,
            "reason": "Current historical snapshot does not reconstruct immutable as-first-published values or first receipt.",
        },
        "economic_interpretation": {
            "alpha_test_authorized": False,
            "forward_returns_used": False,
            "bootstrap_loo_oos_used": False,
            "holdout_used": False,
            "beneficial_owner_known": False,
            "aggressor_direction_known": False,
        },
        "controls": {
            "f80_frozen": True,
            "production_changed": False,
            "universe_changed": False,
            "capital_changed": False,
            "data_purchased": False,
            "vendor_contacted": False,
            "full_partition_rows_persisted": False,
        },
        "decision": (
            "Keep every conflicting group quarantined. lastReportedDate is a candidate diagnostic "
            "dimension only, not an admitted natural key. No feature, sum, row selection or alpha test."
        ),
    }


def main() -> None:
    session = requests.Session()
    rows, pages = fetch_partition_sync(session, WEEK, TIER)
    result = build_result(rows, pages)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "summary.json").write_text(
        json.dumps(result, indent=2, sort_keys=True), encoding="utf-8"
    )
    with (OUT / "page_hashes.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=[
            "page", "offset", "rows", "record_total", "request_id", "sha256"
        ])
        writer.writeheader()
        writer.writerows(result["retrieval"]["page_hashes"])
    print(
        f"PHASE278_STATUS={result['status']} rows={len(rows)} pages={len(pages)} "
        f"duplicate_groups={result['duplicate_audit']['candidate_key_group_count']} "
        f"conflicting={result['duplicate_audit']['conflicting_groups']} "
        f"split_by_last_reported={result['duplicate_audit']['groups_split_by_last_reported_date']} "
        f"extended_duplicates={result['duplicate_audit']['groups_still_duplicate_after_last_reported_date']}",
        flush=True,
    )


if __name__ == "__main__":
    main()

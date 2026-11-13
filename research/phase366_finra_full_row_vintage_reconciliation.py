#!/usr/bin/env python3
"""Phase 366: full-row FINRA weekly partition vintage comparison.

Compares one historical partition that produced a sample-level discrepancy in
Phase 365 and one clean T1 partition. Rows are processed in memory only;
artifacts contain counts and hashes, never symbols or participant identifiers.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

import requests

BASE_URL = "https://api.finra.org/data/group/otcmarket/name"
DATASETS = ("weeklySummaryHistoric", "weeklySummary")
TARGETS = (("2025-10-20", "OTCE"), ("2025-10-20", "T1"))
PAGE_LIMIT = 5000
MAX_OFFSET = 500000
CANONICAL_FIELDS = (
    "MPID",
    "firmCRDNumber",
    "initialPublishedDate",
    "issueName",
    "issueSymbolIdentifier",
    "lastReportedDate",
    "lastUpdateDate",
    "marketParticipantName",
    "productTypeCode",
    "summaryTypeCode",
    "tierDescription",
    "tierIdentifier",
    "totalNotionalSum",
    "totalWeeklyShareQuantity",
    "totalWeeklyTradeCount",
    "weekStartDate",
)
IDENTITY_FIELDS = (
    "summaryTypeCode",
    "issueSymbolIdentifier",
    "productTypeCode",
    "MPID",
    "firmCRDNumber",
    "lastReportedDate",
)
NUMERIC_FIELDS = {
    "totalNotionalSum",
    "totalWeeklyShareQuantity",
    "totalWeeklyTradeCount",
}
DATE_FIELDS = ("initialPublishedDate", "lastUpdateDate", "lastReportedDate")


def build_query(dataset: str, week: str, tier: str, limit: int, offset: int) -> dict:
    week_field = "historicalWeek" if dataset == "weeklySummaryHistoric" else "weekStartDate"
    return {
        "compareFilters": [
            {"fieldName": week_field, "fieldValue": week, "compareType": "EQUAL"},
            {"fieldName": "tierIdentifier", "fieldValue": tier, "compareType": "EQUAL"},
        ],
        "limit": limit,
        "offset": offset,
    }


def parse_rows(payload) -> list[dict]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict):
        if payload.get("message") or payload.get("statusCode"):
            raise RuntimeError("FINRA returned an error envelope")
        data = payload.get("data", [])
        if isinstance(data, dict):
            data = data.get("data", [])
        if isinstance(data, list):
            return [row for row in data if isinstance(row, dict)]
        if data in (None, ""):
            return []
    raise RuntimeError("Unexpected FINRA response envelope")


def normalise_value(field: str, value) -> str:
    if value is None:
        return ""
    raw = str(value).strip()
    if field in NUMERIC_FIELDS and raw:
        try:
            number = Decimal(raw)
            if number == number.to_integral_value():
                return format(number.quantize(Decimal("1")), "f")
            return format(number.normalize(), "f")
        except (InvalidOperation, ValueError):
            return raw
    return raw


def canonical_row(row: dict) -> dict:
    # Fixed field set makes absent and null optional values comparable.
    return {field: normalise_value(field, row.get(field)) for field in CANONICAL_FIELDS}


def _digest_counter(counter: Counter) -> str:
    digest = hashlib.sha256()
    for key, count in sorted(counter.items()):
        digest.update(key.encode("ascii"))
        digest.update(b":")
        digest.update(str(count).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def row_fingerprint(row: dict) -> str:
    payload = json.dumps(canonical_row(row), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def identity_key_fingerprint(row: dict) -> str:
    key = {field: normalise_value(field, row.get(field)) for field in IDENTITY_FIELDS}
    payload = json.dumps(key, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _decimal_add(current: Decimal, value) -> Decimal:
    try:
        return current + Decimal(str(value).replace(",", "").strip())
    except (InvalidOperation, ValueError, AttributeError):
        return current


def summarise_rows(dataset: str, week: str, tier: str, rows: list[dict],
                   record_total: int, pages: int, page_counts_match: bool) -> tuple[dict, Counter, dict]:
    row_hashes = Counter()
    key_to_rows = defaultdict(Counter)
    summary_types = Counter()
    tier_descriptions = Counter()
    product_types = Counter()
    missing = Counter()
    dates = {field: set() for field in DATE_FIELDS}
    symbols = set()
    numeric_totals = defaultdict(lambda: defaultdict(Decimal))
    participant_id_rows = 0
    de_minimis_rows = 0
    returned_fields = set()

    for row in rows:
        returned_fields.update(str(key) for key in row)
        row_hash = row_fingerprint(row)
        key_hash = identity_key_fingerprint(row)
        row_hashes[row_hash] += 1
        key_to_rows[key_hash][row_hash] += 1

        summary_type = normalise_value("summaryTypeCode", row.get("summaryTypeCode")) or "__MISSING__"
        summary_types[summary_type] += 1
        tier_description = normalise_value("tierDescription", row.get("tierDescription")) or "__MISSING__"
        tier_descriptions[tier_description] += 1
        product_type = normalise_value("productTypeCode", row.get("productTypeCode")) or "__MISSING__"
        product_types[product_type] += 1

        symbol = normalise_value("issueSymbolIdentifier", row.get("issueSymbolIdentifier"))
        if symbol:
            symbols.add(symbol)
        if normalise_value("MPID", row.get("MPID")) or normalise_value("firmCRDNumber", row.get("firmCRDNumber")):
            participant_id_rows += 1
        if "de minimis" in normalise_value("marketParticipantName", row.get("marketParticipantName")).lower():
            de_minimis_rows += 1

        for field in (
            "MPID", "firmCRDNumber", "marketParticipantName", "issueSymbolIdentifier",
            "productTypeCode", "totalWeeklyShareQuantity", "totalWeeklyTradeCount",
            "totalNotionalSum",
        ):
            if not normalise_value(field, row.get(field)):
                missing[field] += 1

        for field in DATE_FIELDS:
            value = normalise_value(field, row.get(field))
            if value:
                dates[field].add(value)

        for field in NUMERIC_FIELDS:
            numeric_totals[summary_type][field] = _decimal_add(
                numeric_totals[summary_type][field], row.get(field)
            )

    numeric_output = {
        summary_type: {
            field: format(value, "f")
            for field, value in sorted(values.items())
        }
        for summary_type, values in sorted(numeric_totals.items())
    }
    summary = {
        "dataset": dataset,
        "week": week,
        "tier": tier,
        "record_total": record_total,
        "rows_retrieved": len(rows),
        "pages_retrieved": pages,
        "retrieval_complete": len(rows) == record_total,
        "all_page_counts_match": page_counts_match,
        "summary_type_counts": dict(sorted(summary_types.items())),
        "tier_description_counts": dict(sorted(tier_descriptions.items())),
        "product_type_counts": dict(sorted(product_types.items())),
        "unique_symbols": len(symbols),
        "participant_id_rows": participant_id_rows,
        "de_minimis_rows": de_minimis_rows,
        "missing_field_rows": {field: missing.get(field, 0) for field in sorted((
            "MPID", "firmCRDNumber", "marketParticipantName", "issueSymbolIdentifier",
            "productTypeCode", "totalWeeklyShareQuantity", "totalWeeklyTradeCount",
            "totalNotionalSum",
        ))},
        "date_values": {field: sorted(values) for field, values in dates.items()},
        "numeric_totals_by_summary_type": numeric_output,
        "returned_fields": sorted(returned_fields),
        "distinct_full_rows": len(row_hashes),
        "duplicate_full_rows": sum(count - 1 for count in row_hashes.values()),
        "identity_key_groups": len(key_to_rows),
        "duplicate_identity_key_groups": sum(1 for count in key_to_rows.values() if sum(count.values()) > 1),
        "row_multiset_sha256": _digest_counter(row_hashes),
        "raw_rows_retained": False,
    }
    return summary, row_hashes, dict(key_to_rows)


def compare_vintages(current_hashes: Counter, historic_hashes: Counter,
                     current_keys: dict, historic_keys: dict,
                     current_summary: dict, historic_summary: dict) -> dict:
    matched = sum((current_hashes & historic_hashes).values())
    current_only = sum((current_hashes - historic_hashes).values())
    historic_only = sum((historic_hashes - current_hashes).values())
    all_keys = set(current_keys) | set(historic_keys)
    exact_key_groups = sum(
        1 for key in all_keys if current_keys.get(key, Counter()) == historic_keys.get(key, Counter())
    )
    mismatched_key_groups = len(all_keys) - exact_key_groups
    exact_rows = current_only == 0 and historic_only == 0
    return {
        "record_totals_equal": current_summary["record_total"] == historic_summary["record_total"],
        "row_counts_equal": current_summary["rows_retrieved"] == historic_summary["rows_retrieved"],
        "exact_row_multiset_match": exact_rows,
        "exact_rows_matched": matched,
        "current_only_rows": current_only,
        "historic_only_rows": historic_only,
        "identity_key_groups_total": len(all_keys),
        "exact_identity_key_groups": exact_key_groups,
        "mismatched_identity_key_groups": mismatched_key_groups,
        "returned_fields_equal": current_summary["returned_fields"] == historic_summary["returned_fields"],
        "numeric_totals_equal": (
            current_summary["numeric_totals_by_summary_type"]
            == historic_summary["numeric_totals_by_summary_type"]
        ),
        "participant_id_rows_equal": (
            current_summary["participant_id_rows"] == historic_summary["participant_id_rows"]
        ),
        "de_minimis_rows_equal": (
            current_summary["de_minimis_rows"] == historic_summary["de_minimis_rows"]
        ),
        "current_row_multiset_sha256": current_summary["row_multiset_sha256"],
        "historic_row_multiset_sha256": historic_summary["row_multiset_sha256"],
    }


def _request_page(session: requests.Session, dataset: str, week: str, tier: str, offset: int):
    url = f"{BASE_URL}/{dataset}"
    body = build_query(dataset, week, tier, PAGE_LIMIT, offset)
    last_error = None
    for attempt in range(4):
        try:
            response = session.post(url, json=body, timeout=(20, 120))
            if response.status_code in {408, 429, 500, 502, 503, 504}:
                if attempt == 3:
                    response.raise_for_status()
                retry_after = response.headers.get("Retry-After")
                try:
                    delay = float(retry_after) if retry_after else 2 ** (attempt + 1)
                except (TypeError, ValueError):
                    delay = 2 ** (attempt + 1)
                time.sleep(max(0, min(delay, 30)))
                continue
            response.raise_for_status()
            payload = response.json()
            rows = parse_rows(payload)
            headers = {str(key).lower(): value for key, value in response.headers.items()}
            if "record-total" not in headers:
                raise RuntimeError(f"Missing Record-Total for {dataset}/{week}/{tier}")
            if "record-offset" in headers and int(headers["record-offset"]) != offset:
                raise RuntimeError(f"Record-Offset mismatch for {dataset}/{week}/{tier}")
            page_total = int(headers.get("total-records-on-page", len(rows)))
            if page_total != len(rows):
                raise RuntimeError(f"Page count mismatch for {dataset}/{week}/{tier} offset {offset}")
            if len(rows) > PAGE_LIMIT:
                raise RuntimeError(f"Page exceeded requested limit for {dataset}/{week}/{tier}")
            return rows, int(headers["record-total"]), headers
        except (requests.RequestException, ValueError) as exc:
            last_error = exc
            if attempt == 3:
                raise RuntimeError(f"Request failed for {dataset}/{week}/{tier} offset {offset}: {type(exc).__name__}") from exc
            time.sleep(min(2 ** (attempt + 1), 20))
    raise RuntimeError(f"Unable to retrieve {dataset}/{week}/{tier} offset {offset}: {last_error}")


def fetch_partition(session: requests.Session, dataset: str, week: str, tier: str):
    rows = []
    expected_total = None
    offset = 0
    pages = 0
    page_counts_match = True
    while True:
        page_rows, record_total, headers = _request_page(session, dataset, week, tier, offset)
        if expected_total is None:
            expected_total = record_total
        elif record_total != expected_total:
            raise RuntimeError(f"Record-Total changed while paging {dataset}/{week}/{tier}")
        if not page_rows and offset < record_total:
            raise RuntimeError(f"Empty page before end of partition {dataset}/{week}/{tier}")
        rows.extend(page_rows)
        pages += 1
        page_counts_match = page_counts_match and (
            int(headers.get("total-records-on-page", len(page_rows))) == len(page_rows)
        )
        print(
            f"[Phase366] {dataset}/{week}/{tier} offset={offset} "
            f"page_rows={len(page_rows)} total={record_total}",
            flush=True,
        )
        offset += len(page_rows)
        if offset >= record_total:
            break
        if offset > MAX_OFFSET:
            raise RuntimeError(f"Offset limit exceeded for {dataset}/{week}/{tier}")
        if not page_rows:
            raise RuntimeError(f"No pagination progress for {dataset}/{week}/{tier}")
        time.sleep(0.25)

    if expected_total is None:
        expected_total = 0
    if len(rows) != expected_total:
        raise RuntimeError(
            f"Retrieved row count {len(rows)} differs from Record-Total {expected_total} "
            f"for {dataset}/{week}/{tier}"
        )
    return summarise_rows(dataset, week, tier, rows, expected_total, pages, page_counts_match)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="phase366_finra_full_row_vintage_reconciliation")
    args = parser.parse_args()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers.update({
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Data-API-Version": "1",
        "User-Agent": "SmartMoneyResearch-Phase366/1.0",
    })
    token = os.getenv("FINRA_API_TOKEN", "").strip()
    if token:
        session.headers["Authorization"] = f"Bearer {token}"

    target_results = []
    errors = []
    for week, tier in TARGETS:
        print(f"[Phase366] target {week}/{tier}", flush=True)
        vintage_results = {}
        for dataset in DATASETS:
            try:
                summary, hashes, keys = fetch_partition(session, dataset, week, tier)
                vintage_results[dataset] = (summary, hashes, keys)
            except Exception as exc:
                errors.append({
                    "dataset": dataset,
                    "week": week,
                    "tier": tier,
                    "error_type": type(exc).__name__,
                    "error": str(exc)[:240],
                })
                print(
                    f"[Phase366] ERROR {dataset}/{week}/{tier}: "
                    f"{type(exc).__name__}",
                    flush=True,
                )

        if len(vintage_results) == 2:
            historic_summary, historic_hashes, historic_keys = vintage_results["weeklySummaryHistoric"]
            current_summary, current_hashes, current_keys = vintage_results["weeklySummary"]
            comparison = compare_vintages(
                current_hashes, historic_hashes, current_keys, historic_keys,
                current_summary, historic_summary,
            )
            target_results.append({
                "week": week,
                "tier": tier,
                "current": current_summary,
                "historic": historic_summary,
                "comparison": comparison,
            })

    all_complete = (
        len(target_results) == len(TARGETS)
        and not errors
        and all(
            item["current"]["retrieval_complete"]
            and item["historic"]["retrieval_complete"]
            and item["current"]["all_page_counts_match"]
            and item["historic"]["all_page_counts_match"]
            for item in target_results
        )
    )
    exact_all = all(
        item["comparison"]["exact_row_multiset_match"]
        for item in target_results
    ) if target_results else False

    summary = {
        "phase": 366,
        "source": "FINRA OTCMarket weeklySummaryHistoric + weeklySummary",
        "audit_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "targets": [{"week": week, "tier": tier} for week, tier in TARGETS],
        "queries_expected_minimum": len(TARGETS) * 2,
        "partitions_completed": len(target_results) * 2,
        "errors": errors,
        "results": target_results,
        "all_partitions_complete": all_complete,
        "all_page_counts_match": all_complete,
        "all_vintages_exact_row_match": exact_all,
        "research_disposition": (
            "EXACT_ROW_MATCH" if all_complete and exact_all
            else "MISMATCH_REVIEW" if all_complete
            else "INCOMPLETE_RETRIEVAL"
        ),
        "raw_rows_retained": False,
        "forward_returns_used": False,
        "alpha_test_authorized": False,
        "holdout_used": False,
        "f80_changed": False,
    }
    (output / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2), flush=True)
    print(
        f"[Phase366] complete={all_complete} exact_all={exact_all} "
        f"partitions={summary['partitions_completed']} errors={len(errors)}",
        flush=True,
    )
    if not all_complete:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

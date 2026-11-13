#!/usr/bin/env python3
"""Phase 367: diagnose field-level differences in the FINRA T1 vintage overlap.

Re-fetches 2025-10-20 T1 from current and historic datasets. Raw rows and
identifiers are processed in memory only; the artifact contains anonymized
field-level counts and numeric-difference summaries.
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
WEEK = "2025-10-20"
TIER = "T1"
PAGE_LIMIT = 5000
MAX_OFFSET = 500000
CANONICAL_FIELDS = (
    "MPID", "firmCRDNumber", "initialPublishedDate", "issueName",
    "issueSymbolIdentifier", "lastReportedDate", "lastUpdateDate",
    "marketParticipantName", "productTypeCode", "summaryStartDate",
    "summaryTypeCode", "tierDescription", "tierIdentifier",
    "totalNotionalSum", "totalWeeklyShareQuantity", "totalWeeklyTradeCount",
    "weekStartDate",
)
# Deliberately excludes lastReportedDate: it is a field to compare, not a
# universal row-join key. summaryStartDate helps distinguish repeated records.
IDENTITY_FIELDS = (
    "summaryTypeCode", "issueSymbolIdentifier", "productTypeCode",
    "MPID", "firmCRDNumber", "summaryStartDate",
)
NUMERIC_FIELDS = {
    "totalNotionalSum", "totalWeeklyShareQuantity", "totalWeeklyTradeCount",
}


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


def decimal_value(value) -> Decimal | None:
    if value in (None, ""):
        return None
    try:
        number = Decimal(str(value).replace(",", "").strip())
        if not number.is_finite():
            return None
        return number
    except (InvalidOperation, ValueError, AttributeError):
        return None


def decimal_text(value: Decimal) -> str:
    if value == 0:
        return "0"
    return format(value.normalize(), "f")


def normalise_value(field: str, value) -> str:
    if value is None:
        return ""
    if field in NUMERIC_FIELDS:
        number = decimal_value(value)
        if number is not None:
            return decimal_text(number)
    return str(value).strip()


def canonical_row(row: dict) -> dict:
    # The historic-only historicalweek field is a query helper; it is not a
    # business field. All known business fields, including summaryStartDate,
    # are compared. Missing/null optional values normalize to empty strings.
    return {field: normalise_value(field, row.get(field)) for field in CANONICAL_FIELDS}


def row_json(row: dict) -> str:
    return json.dumps(canonical_row(row), sort_keys=True, separators=(",", ":"))


def row_fingerprint(row: dict) -> str:
    return hashlib.sha256(row_json(row).encode("utf-8")).hexdigest()


def identity_key_fingerprint(row: dict) -> str:
    key = {field: normalise_value(field, row.get(field)) for field in IDENTITY_FIELDS}
    return hashlib.sha256(
        json.dumps(key, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _digest_counter(counter: Counter) -> str:
    digest = hashlib.sha256()
    for key, count in sorted(counter.items()):
        digest.update(key.encode("ascii"))
        digest.update(b":")
        digest.update(str(count).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def _request_page(session: requests.Session, dataset: str, offset: int):
    url = f"{BASE_URL}/{dataset}"
    body = build_query(dataset, WEEK, TIER, PAGE_LIMIT, offset)
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
            rows = parse_rows(response.json())
            headers = {str(key).lower(): value for key, value in response.headers.items()}
            if "record-total" not in headers:
                raise RuntimeError(f"Missing Record-Total for {dataset}")
            if "record-offset" in headers and int(headers["record-offset"]) != offset:
                raise RuntimeError(f"Record-Offset mismatch for {dataset} offset {offset}")
            page_total = int(headers.get("total-records-on-page", len(rows)))
            if page_total != len(rows):
                raise RuntimeError(f"Page count mismatch for {dataset} offset {offset}")
            if len(rows) > PAGE_LIMIT:
                raise RuntimeError(f"Page exceeded requested limit for {dataset}")
            return rows, int(headers["record-total"]), headers
        except (requests.RequestException, ValueError) as exc:
            last_error = exc
            if attempt == 3:
                raise RuntimeError(
                    f"Request failed for {dataset} offset {offset}: {type(exc).__name__}"
                ) from exc
            time.sleep(min(2 ** (attempt + 1), 20))
    raise RuntimeError(f"Unable to retrieve {dataset} offset {offset}: {last_error}")


def fetch_partition(session: requests.Session, dataset: str):
    key_to_rows = defaultdict(list)
    summary_types = Counter()
    tier_descriptions = Counter()
    product_types = Counter()
    symbols = set()
    participant_id_rows = 0
    de_minimis_rows = 0
    returned_fields = set()
    expected_total = None
    offset = 0
    pages = 0
    all_page_counts_match = True
    row_count = 0

    while True:
        rows, record_total, headers = _request_page(session, dataset, offset)
        if expected_total is None:
            expected_total = record_total
        elif record_total != expected_total:
            raise RuntimeError(f"Record-Total changed while paging {dataset}")
        if not rows and offset < record_total:
            raise RuntimeError(f"Empty page before end of {dataset}")
        for row in rows:
            returned_fields.update(str(key) for key in row)
            key_to_rows[identity_key_fingerprint(row)].append(canonical_row(row))
            summary_types[normalise_value("summaryTypeCode", row.get("summaryTypeCode")) or "__MISSING__"] += 1
            tier_descriptions[normalise_value("tierDescription", row.get("tierDescription")) or "__MISSING__"] += 1
            product_types[normalise_value("productTypeCode", row.get("productTypeCode")) or "__MISSING__"] += 1
            symbol = normalise_value("issueSymbolIdentifier", row.get("issueSymbolIdentifier"))
            if symbol:
                symbols.add(symbol)
            if normalise_value("MPID", row.get("MPID")) or normalise_value("firmCRDNumber", row.get("firmCRDNumber")):
                participant_id_rows += 1
            if "de minimis" in normalise_value("marketParticipantName", row.get("marketParticipantName")).lower():
                de_minimis_rows += 1
        row_count += len(rows)
        pages += 1
        all_page_counts_match = all_page_counts_match and (
            int(headers.get("total-records-on-page", len(rows))) == len(rows)
        )
        print(
            f"[Phase367] {dataset} offset={offset} page_rows={len(rows)} total={record_total}",
            flush=True,
        )
        offset += len(rows)
        if offset >= record_total:
            break
        if offset > MAX_OFFSET:
            raise RuntimeError(f"Offset limit exceeded for {dataset}")
        if not rows:
            raise RuntimeError(f"No pagination progress for {dataset}")
        time.sleep(0.25)

    if expected_total is None:
        expected_total = 0
    if row_count != expected_total:
        raise RuntimeError(f"Retrieved {row_count} rows vs Record-Total {expected_total} for {dataset}")

    row_hashes = Counter()
    for key_rows in key_to_rows.values():
        for row in key_rows:
            row_hashes[hashlib.sha256(
                json.dumps(row, sort_keys=True, separators=(",", ":")).encode("utf-8")
            ).hexdigest()] += 1

    summary = {
        "dataset": dataset,
        "week": WEEK,
        "tier": TIER,
        "record_total": expected_total,
        "rows_retrieved": row_count,
        "pages_retrieved": pages,
        "retrieval_complete": row_count == expected_total,
        "all_page_counts_match": all_page_counts_match,
        "summary_type_counts": dict(sorted(summary_types.items())),
        "tier_description_counts": dict(sorted(tier_descriptions.items())),
        "product_type_counts": dict(sorted(product_types.items())),
        "unique_symbols": len(symbols),
        "participant_id_rows": participant_id_rows,
        "de_minimis_rows": de_minimis_rows,
        "returned_fields": sorted(returned_fields),
        "identity_key_groups": len(key_to_rows),
        "duplicate_identity_key_groups": sum(1 for rows in key_to_rows.values() if len(rows) > 1),
        "row_multiset_sha256": _digest_counter(row_hashes),
        "raw_rows_retained": False,
    }
    return summary, dict(key_to_rows)


def _compare_row_pair(current: dict, historic: dict):
    differences = [
        field for field in CANONICAL_FIELDS
        if current.get(field, "") != historic.get(field, "")
    ]
    numeric_differences = {}
    for field in NUMERIC_FIELDS:
        a = decimal_value(current.get(field, ""))
        b = decimal_value(historic.get(field, ""))
        if a is not None and b is not None and a != b:
            numeric_differences[field] = a - b
    return differences, numeric_differences


def compare_key_maps(current_map: dict, historic_map: dict):
    all_keys = set(current_map) | set(historic_map)
    current_only_keys = sum(1 for key in all_keys if key in current_map and key not in historic_map)
    historic_only_keys = sum(1 for key in all_keys if key in historic_map and key not in current_map)
    field_diff_counts = Counter()
    mismatch_summary_types = Counter()
    numeric_diffs = {
        field: {"count": 0, "signed_sum": Decimal(0), "absolute_sum": Decimal(0), "max_absolute": Decimal(0)}
        for field in sorted(NUMERIC_FIELDS)
    }
    exact_pairs = 0
    mismatched_pairs = 0
    only_notional_rows = 0
    rows_with_other_differences = 0
    ambiguous_key_groups = 0
    key_groups_exact = 0
    compared_pairs = 0

    for key in sorted(set(current_map) & set(historic_map)):
        current_rows = current_map[key]
        historic_rows = historic_map[key]
        current_counter = Counter(
            json.dumps(row, sort_keys=True, separators=(",", ":")) for row in current_rows
        )
        historic_counter = Counter(
            json.dumps(row, sort_keys=True, separators=(",", ":")) for row in historic_rows
        )
        common = current_counter & historic_counter
        exact_in_group = sum(common.values())
        exact_pairs += exact_in_group
        current_remaining = list((current_counter - common).elements())
        historic_remaining = list((historic_counter - common).elements())

        if not current_remaining and not historic_remaining:
            key_groups_exact += 1
            continue

        if len(current_rows) > 1 or len(historic_rows) > 1:
            ambiguous_key_groups += 1
        current_remaining.sort()
        historic_remaining.sort()
        pair_count = min(len(current_remaining), len(historic_remaining))
        for index in range(pair_count):
            current_row = json.loads(current_remaining[index])
            historic_row = json.loads(historic_remaining[index])
            compared_pairs += 1
            differences, numeric_differences = _compare_row_pair(current_row, historic_row)
            if differences:
                mismatched_pairs += 1
                for field in differences:
                    field_diff_counts[field] += 1
                if set(differences) == {"totalNotionalSum"}:
                    only_notional_rows += 1
                else:
                    rows_with_other_differences += 1
                summary_type = current_row.get("summaryTypeCode") or "__MISSING__"
                mismatch_summary_types[summary_type] += 1
                for field, delta in numeric_differences.items():
                    item = numeric_diffs[field]
                    item["count"] += 1
                    item["signed_sum"] += delta
                    item["absolute_sum"] += abs(delta)
                    item["max_absolute"] = max(item["max_absolute"], abs(delta))
            else:
                exact_pairs += 1
        if not current_remaining and not historic_remaining:
            key_groups_exact += 1

    unmatched_current_rows = sum(
        max(0, len(current_map.get(key, [])) - len(historic_map.get(key, [])))
        for key in current_only_keys and [] or []
    )
    # Key-only groups are counted separately; row totals remain visible in source summaries.
    numeric_output = {
        field: {
            "mismatched_rows": value["count"],
            "current_minus_historic_sum": decimal_text(value["signed_sum"]),
            "absolute_difference_sum": decimal_text(value["absolute_sum"]),
            "maximum_absolute_difference": decimal_text(value["max_absolute"]),
        }
        for field, value in sorted(numeric_diffs.items())
    }
    return {
        "identity_key_groups_total": len(all_keys),
        "current_only_identity_key_groups": current_only_keys,
        "historic_only_identity_key_groups": historic_only_keys,
        "exact_identity_key_groups": key_groups_exact,
        "ambiguous_identity_key_groups": ambiguous_key_groups,
        "exact_row_pairs": exact_pairs,
        "mismatched_row_pairs": mismatched_pairs,
        "unpaired_rows_in_shared_key_groups": sum(
            abs(len(current_map[key]) - len(historic_map[key]))
            for key in set(current_map) & set(historic_map)
        ),
        "field_mismatch_counts": dict(sorted(field_diff_counts.items())),
        "mismatch_counts_by_summary_type": dict(sorted(mismatch_summary_types.items())),
        "rows_differing_only_in_totalNotionalSum": only_notional_rows,
        "rows_with_other_field_differences": rows_with_other_differences,
        "numeric_field_differences": numeric_output,
        "selected_field_exact_match": (
            current_only_keys == 0 and historic_only_keys == 0
            and mismatched_pairs == 0
            and sum(abs(len(current_map[key]) - len(historic_map[key]))
                    for key in set(current_map) & set(historic_map)) == 0
        ),
        "raw_keys_retained": False,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="phase367_finra_t1_field_level_vintage_diagnostic")
    args = parser.parse_args()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers.update({
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Data-API-Version": "1",
        "User-Agent": "SmartMoneyResearch-Phase367/1.0",
    })
    token = os.getenv("FINRA_API_TOKEN", "").strip()
    if token:
        session.headers["Authorization"] = f"Bearer {token}"

    summaries = {}
    maps = {}
    errors = []
    for dataset in DATASETS:
        try:
            summary, key_map = fetch_partition(session, dataset)
            summaries[dataset] = summary
            maps[dataset] = key_map
        except Exception as exc:
            errors.append({
                "dataset": dataset,
                "error_type": type(exc).__name__,
                "error": str(exc)[:240],
            })

    comparison = None
    if len(maps) == 2:
        comparison = compare_key_maps(maps["weeklySummary"], maps["weeklySummaryHistoric"])

    all_complete = (
        len(summaries) == 2 and not errors
        and all(s["retrieval_complete"] and s["all_page_counts_match"] for s in summaries.values())
    )
    summary = {
        "phase": 367,
        "source": "FINRA OTCMarket weeklySummaryHistoric + weeklySummary",
        "audit_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "week": WEEK,
        "tier": TIER,
        "datasets": summaries,
        "comparison": comparison,
        "errors": errors,
        "all_partitions_complete": all_complete,
        "research_disposition": (
            "FIELD_DIAGNOSTIC_COMPLETE" if all_complete and comparison is not None
            else "INCOMPLETE_RETRIEVAL"
        ),
        "raw_rows_retained": False,
        "raw_keys_retained": False,
        "forward_returns_used": False,
        "alpha_test_authorized": False,
        "holdout_used": False,
        "f80_changed": False,
    }
    (output / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2), flush=True)
    print(
        f"[Phase367] complete={all_complete} "
        f"mismatched_pairs={(comparison or {}).get('mismatched_row_pairs')} "
        f"field_diffs={(comparison or {}).get('field_mismatch_counts')} errors={len(errors)}",
        flush=True,
    )
    if not all_complete:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

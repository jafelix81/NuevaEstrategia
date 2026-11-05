#!/usr/bin/env python3
"""Phase 100: corrected FINRA weekly ATS/off-exchange coverage and PIT audit.

Data feasibility only. No forward returns or alpha testing.
"""
from __future__ import annotations

import ast
import csv
import hashlib
import json
import time
from urllib.parse import urljoin
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path

import requests

BASE = "https://api.finra.org/data/group/otcmarket/name/weeklySummaryHistoric"
SOURCE = Path("Nueva_Estrategia_Fase11_Real1000_LTM_v4.py")
OUT = Path("phase100_finra_ats_revalidation")
WEEKS = ("2022-01-03", "2023-01-09", "2024-01-08", "2025-01-06", "2025-10-20")
TIERS = ("T1", "T2")
ASYNC_PAGE_SIZE = 100000
MAX_OFFSET = 500000
MAX_PAGES = 6
POLL_INTERVAL_SECONDS = 60
MAX_POLL_CYCLES = 10
FIELDS = [
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
]
SYMBOL_AGGREGATES = {"ATS_W_SMBL", "OTC_W_SMBL"}
NON_SYMBOL_TYPES = {"ATS_W_FIRM", "OTC_W_FIRM", "ATS_W_VOL_STATS", "OTC_W_VOL_STATS"}
SYMBOL_BEARING_TYPES = {"ATS_W_SMBL", "ATS_W_SMBL_FIRM", "OTC_W_SMBL", "OTC_W_SMBL_FIRM"}
KNOWN_SUMMARY_TYPES = NON_SYMBOL_TYPES | SYMBOL_BEARING_TYPES


def load_legacy_universe() -> set[str]:
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "DEFAULT_UNIVERSE":
                    values = {str(x).strip().upper() for x in ast.literal_eval(node.value)}
                    if len(values) != 335:
                        raise RuntimeError(f"Expected 335 legacy names, got {len(values)}")
                    return values
    raise RuntimeError("DEFAULT_UNIVERSE not found")


def parse_response(obj) -> list[dict]:
    if isinstance(obj, list):
        return [x for x in obj if isinstance(x, dict)]
    if isinstance(obj, dict):
        if obj.get("message") or obj.get("statusCode"):
            raise ValueError(f"FINRA returned an error object: {obj}")
        data = obj.get("data", [])
        if isinstance(data, dict):
            data = data.get("data", [])
        if isinstance(data, list):
            return [x for x in data if isinstance(x, dict)]
    raise ValueError(f"Unexpected FINRA response shape: {type(obj).__name__}")


def parse_date(value):
    if value in (None, ""):
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def parse_nonnegative_number(value):
    if value in (None, ""):
        return None
    try:
        number = float(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return None
    if number < 0:
        return None
    return number


def validate_partition_rows(rows: list[dict], week: str, tier: str) -> list[str]:
    problems = []
    for i, row in enumerate(rows):
        actual_week = str(row.get("weekStartDate") or "")[:10]
        actual_tier = str(row.get("tierIdentifier") or "").upper()
        if actual_week != week:
            problems.append(f"row {i}: weekStartDate={actual_week!r}, expected {week}")
        if actual_tier != tier:
            problems.append(f"row {i}: tierIdentifier={actual_tier!r}, expected {tier}")
        summary_type = str(row.get("summaryTypeCode") or "").strip().upper()
        if summary_type not in KNOWN_SUMMARY_TYPES:
            problems.append(f"row {i}: unknown or missing summaryTypeCode={summary_type!r}")
        # Firm-level totals and volume statistics intentionally have no security symbol.
        # Symbol and symbol-by-firm summary types must retain the exact symbol.
        if summary_type in SYMBOL_BEARING_TYPES and not str(row.get("issueSymbolIdentifier") or "").strip():
            problems.append(
                f"row {i}: missing issueSymbolIdentifier for summaryTypeCode={summary_type!r}"
            )
    return problems


def build_async_payload(week: str, tier: str, offset: int = 0) -> dict:
    return {
        "fields": FIELDS,
        "compareFilters": [
            {"compareType": "equal", "fieldName": "historicalWeek", "fieldValue": week},
            {"compareType": "equal", "fieldName": "tierIdentifier", "fieldValue": tier},
        ],
        "limit": ASYNC_PAGE_SIZE,
        "offset": offset,
        "async": True,
    }


def _download_async_result(session: requests.Session, week: str, tier: str, offset: int):
    payload = build_async_payload(week, tier, offset)
    response = session.post(BASE, json=payload, timeout=(20, 120))
    if response.status_code == 200:
        rows = parse_response(response.json())
        record_total_raw = response.headers.get("Record-Total")
        if record_total_raw is None:
            raise RuntimeError(f"FINRA synchronous response lacks Record-Total for {week}/{tier}")
        record_total = int(record_total_raw)
        return rows, record_total, {
            "week": week, "tier": tier, "offset": offset, "rows": len(rows),
            "record_total": record_total, "status_polls": 0,
            "request_id": response.headers.get("FINRA-api-request-id"),
            "sha256": hashlib.sha256(response.content).hexdigest(),
            "async_status": "completed_synchronously",
        }
    if response.status_code != 202:
        raise RuntimeError(
            f"FINRA async submit failed {week}/{tier} offset={offset}: "
            f"HTTP {response.status_code}: {response.text[:800]}"
        )
    location = response.headers.get("Location")
    if not location:
        raise RuntimeError(f"FINRA async submit returned 202 without Location for {week}/{tier}")
    status_url = urljoin("https://api.finra.org", location)
    request_id = response.headers.get("FINRA-api-request-id")
    status_response = None
    status_json = None
    polls = 0
    for polls in range(1, MAX_POLL_CYCLES + 1):
        time.sleep(POLL_INTERVAL_SECONDS)
        status_response = session.get(status_url, timeout=(20, 60))
        if status_response.status_code == 202:
            continue
        if status_response.status_code != 200:
            raise RuntimeError(
                f"FINRA async status failed {week}/{tier}: HTTP {status_response.status_code}: "
                f"{status_response.text[:800]}"
            )
        status_json = status_response.json()
        break
    else:
        raise TimeoutError(
            f"FINRA async request did not complete within {MAX_POLL_CYCLES} one-minute polls "
            f"for {week}/{tier}; request_id={request_id}"
        )

    result_link = status_json.get("resultLink")
    if isinstance(result_link, dict):
        result_link = result_link.get("url") or result_link.get("href") or result_link.get("link")
    if not result_link:
        raise RuntimeError(
            f"FINRA async completed without resultLink for {week}/{tier}; "
            f"request_id={request_id}; status={status_json}"
        )
    # FINRA's pre-signed S3 resultLink embeds its own authorization. Do not
    # attach API authorization headers to this request.
    result_response = requests.get(
        result_link, headers={"Accept": "application/json"}, timeout=(20, 180)
    )
    result_response.raise_for_status()
    rows = parse_response(result_response.json())
    record_total_raw = (
        status_response.headers.get("Record-Total")
        or result_response.headers.get("Record-Total")
        or status_json.get("recordTotal")
    )
    if record_total_raw is None:
        raise RuntimeError(
            f"FINRA async result lacks Record-Total header for {week}/{tier}; "
            f"request_id={request_id}"
        )
    record_total = int(record_total_raw)
    meta = {
        "week": week, "tier": tier, "offset": offset, "rows": len(rows),
        "record_total": record_total, "status_polls": polls,
        "request_id": request_id or status_json.get("requestId"),
        "async_status": status_json.get("status"),
        "result_expires": status_json.get("expires"),
        "sha256": hashlib.sha256(result_response.content).hexdigest(),
    }
    return rows, record_total, meta


def fetch_partition(session: requests.Session, week: str, tier: str):
    rows, pages = [], []
    offset = 0
    expected_total = None
    for page in range(MAX_PAGES):
        page_rows, record_total, meta = _download_async_result(session, week, tier, offset)
        meta["page"] = page
        pages.append(meta)
        if expected_total is None:
            expected_total = record_total
        elif record_total != expected_total:
            raise RuntimeError(
                f"FINRA Record-Total changed across pages for {week}/{tier}: "
                f"{record_total} vs {expected_total}"
            )
        if len(page_rows) != meta["rows"]:
            raise RuntimeError(f"FINRA row-count mismatch for {week}/{tier} offset={offset}")
        if not page_rows and record_total:
            raise RuntimeError(
                f"FINRA returned zero rows before Record-Total={record_total} for {week}/{tier}"
            )
        rows.extend(page_rows)
        offset += len(page_rows)
        if offset >= record_total:
            break
        if offset > MAX_OFFSET:
            raise RuntimeError(f"FINRA offset ceiling exceeded for {week}/{tier}")
        if len(page_rows) < ASYNC_PAGE_SIZE:
            raise RuntimeError(
                f"FINRA async page shorter than requested but Record-Total not reached "
                f"for {week}/{tier}: retrieved={offset}, total={record_total}"
            )
    else:
        raise RuntimeError(f"Async pagination guard exceeded for {week}/{tier}")
    if expected_total is None or len(rows) != expected_total:
        raise RuntimeError(
            f"FINRA incomplete partition {week}/{tier}: retrieved={len(rows)}, total={expected_total}"
        )
    return rows, pages
def summarize_partition(rows: list[dict], week: str, tier: str, legacy: set[str]):
    type_counts = Counter(str(r.get("summaryTypeCode") or "MISSING").upper() for r in rows)
    missing_symbol_by_type = Counter(
        str(r.get("summaryTypeCode") or "MISSING").upper()
        for r in rows if not str(r.get("issueSymbolIdentifier") or "").strip()
    )
    unknown_summary_types = Counter(
        str(r.get("summaryTypeCode") or "MISSING").upper()
        for r in rows if str(r.get("summaryTypeCode") or "MISSING").upper() not in KNOWN_SUMMARY_TYPES
    )
    all_symbols = {
        str(r.get("issueSymbolIdentifier") or "").strip().upper()
        for r in rows
        if str(r.get("issueSymbolIdentifier") or "").strip()
    }
    aggregate_rows = [
        r for r in rows
        if str(r.get("summaryTypeCode") or "").upper() in SYMBOL_AGGREGATES
    ]
    ats_symbols = {
        str(r.get("issueSymbolIdentifier") or "").strip().upper()
        for r in aggregate_rows
        if str(r.get("summaryTypeCode") or "").upper() == "ATS_W_SMBL"
    }
    otc_symbols = {
        str(r.get("issueSymbolIdentifier") or "").strip().upper()
        for r in aggregate_rows
        if str(r.get("summaryTypeCode") or "").upper() == "OTC_W_SMBL"
    }
    aggregate_symbols = ats_symbols | otc_symbols

    publication_dates = [parse_date(r.get("initialPublishedDate")) for r in aggregate_rows]
    update_dates = [parse_date(r.get("lastUpdateDate")) for r in aggregate_rows]
    reported_dates = [parse_date(r.get("lastReportedDate")) for r in aggregate_rows]
    valid_publications = [x for x in publication_dates if x]
    valid_updates = [x for x in update_dates if x]
    valid_reported = [x for x in reported_dates if x]
    week_date = date.fromisoformat(week)
    expected_delay = 14 if tier == "T1" else 28
    publication_lags = [(x - week_date).days for x in valid_publications]
    early_publications = sum(x < expected_delay for x in publication_lags)
    post_publish_updates = sum(
        1 for pub, upd in zip(publication_dates, update_dates)
        if pub and upd and upd > pub
    )
    reported_after_publish = sum(
        1 for pub, reported in zip(publication_dates, reported_dates)
        if pub and reported and reported > pub
    )

    duplicate_groups = {}
    invalid_quantities = 0
    missing_symbol_by_type = Counter()
    unknown_summary_types = Counter()
    for row in aggregate_rows:
        summary_type = str(row.get("summaryTypeCode") or "MISSING").upper()
        if not str(row.get("issueSymbolIdentifier") or "").strip():
            missing_symbol_by_type[summary_type] += 1
        if summary_type not in KNOWN_SUMMARY_TYPES:
            unknown_summary_types[summary_type] += 1
        key = (
            str(row.get("issueSymbolIdentifier") or "").strip().upper(),
            str(row.get("weekStartDate") or "")[:10],
            str(row.get("tierIdentifier") or "").upper(),
            summary_type,
            str(row.get("productTypeCode") or "").upper(),
        )
        duplicate_groups.setdefault(key, []).append(row)
        if parse_nonnegative_number(row.get("totalWeeklyShareQuantity")) is None:
            invalid_quantities += 1
        if parse_nonnegative_number(row.get("totalWeeklyTradeCount")) is None:
            invalid_quantities += 1

    duplicate_key_groups = {k: v for k, v in duplicate_groups.items() if len(v) > 1}
    duplicates = sum(len(v) - 1 for v in duplicate_key_groups.values())
    exact_duplicate_groups = 0
    conflicting_duplicate_groups = 0
    duplicate_examples = []
    for key, group in list(duplicate_key_groups.items())[:10]:
        normalized = {
            tuple(str(row.get(field) or "") for field in FIELDS)
            for row in group
        }
        if len(normalized) == 1:
            exact_duplicate_groups += 1
        else:
            conflicting_duplicate_groups += 1
        duplicate_examples.append({
            "key": list(key),
            "row_count": len(group),
            "exact_duplicate_rows": len(normalized) == 1,
            "rows": [
                {field: row.get(field) for field in FIELDS}
                for row in group[:3]
            ],
        })
    union_coverage = len(legacy & aggregate_symbols) / len(legacy)
    ats_coverage = len(legacy & ats_symbols) / len(legacy)
    otc_coverage = len(legacy & otc_symbols) / len(legacy)
    summary = {
        "week": week,
        "tier": tier,
        "rows_total": len(rows),
        "unique_symbols_all_rows": len(all_symbols),
        "summary_type_counts": dict(sorted(type_counts.items())),
        "missing_symbol_by_summary_type": dict(sorted(missing_symbol_by_type.items())),
        "unknown_summary_type_counts": dict(sorted(unknown_summary_types.items())),
        "symbol_aggregate_rows": len(aggregate_rows),
        "ats_symbol_rows": sum(1 for r in aggregate_rows if str(r.get("summaryTypeCode") or "").upper() == "ATS_W_SMBL"),
        "otc_symbol_rows": sum(1 for r in aggregate_rows if str(r.get("summaryTypeCode") or "").upper() == "OTC_W_SMBL"),
        "ats_unique_symbols": len(ats_symbols),
        "otc_unique_symbols": len(otc_symbols),
        "aggregate_unique_symbols": len(aggregate_symbols),
        "legacy_335_ats_coverage_pct": round(100 * ats_coverage, 2),
        "legacy_335_otc_coverage_pct": round(100 * otc_coverage, 2),
        "legacy_335_union_coverage_pct": round(100 * union_coverage, 2),
        "initial_published_date_nonnull_pct": round(100 * len(valid_publications) / len(aggregate_rows), 2) if aggregate_rows else 0.0,
        "last_update_date_nonnull_pct": round(100 * len(valid_updates) / len(aggregate_rows), 2) if aggregate_rows else 0.0,
        "last_reported_date_nonnull_pct": round(100 * len(valid_reported) / len(aggregate_rows), 2) if aggregate_rows else 0.0,
        "last_reported_lag_days_min": min((x - week_date).days for x in valid_reported) if valid_reported else None,
        "last_reported_lag_days_median": sorted((x - week_date).days for x in valid_reported)[len(valid_reported)//2] if valid_reported else None,
        "last_reported_lag_days_max": max((x - week_date).days for x in valid_reported) if valid_reported else None,
        "last_reported_after_initial_publish_rows": reported_after_publish,
        "missing_symbol_by_summary_type": dict(sorted(missing_symbol_by_type.items())),
        "unknown_summary_type_counts": dict(sorted(unknown_summary_types.items())),
        "duplicate_aggregate_key_groups": len(duplicate_key_groups),
        "duplicate_aggregate_keys": duplicates,
        "exact_duplicate_key_groups": exact_duplicate_groups,
        "conflicting_duplicate_key_groups": conflicting_duplicate_groups,
        "duplicate_aggregate_key_examples": duplicate_examples,
        "publication_lag_days_min": min(publication_lags) if publication_lags else None,
        "publication_lag_days_median": sorted(publication_lags)[len(publication_lags)//2] if publication_lags else None,
        "publication_lag_days_max": max(publication_lags) if publication_lags else None,
        "publication_before_minimum_delay_rows": early_publications,
        "last_update_after_initial_publish_rows": post_publish_updates,
        "invalid_or_negative_quantity_fields": invalid_quantities,
        "type_counts_json": json.dumps(dict(sorted(type_counts.items())), sort_keys=True),
    }
    return summary, ats_symbols, otc_symbols


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    legacy = load_legacy_universe()
    session = requests.Session()
    session.headers.update({
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "SmartMoneyResearch-Phase100/1.0",
    })

    partition_summaries, page_hashes, errors, sample_rows = [], [], [], []
    week_ats_symbols = {week: set() for week in WEEKS}
    week_otc_symbols = {week: set() for week in WEEKS}
    for week in WEEKS:
        for tier in TIERS:
            try:
                print(f"[FINRA ATS] start week={week} tier={tier}", flush=True)
                rows, pages = fetch_partition(session, week, tier)
                page_hashes.extend(pages)
                record_total = pages[0]["record_total"] if pages else 0
                retrieved_total = len(rows)
                mismatches = validate_partition_rows(rows, week, tier)
                if mismatches:
                    errors.append({
                        "week": week, "tier": tier,
                        "error": "ROW_PARTITION_MISMATCH",
                        "examples": mismatches[:10],
                        "mismatch_count": len(mismatches),
                    })
                summary, ats_symbols, otc_symbols = summarize_partition(rows, week, tier, legacy)
                week_ats_symbols[week].update(ats_symbols)
                week_otc_symbols[week].update(otc_symbols)
                summary["row_partition_mismatch_count"] = len(mismatches)
                summary["api_record_total"] = record_total
                summary["api_records_retrieved"] = retrieved_total
                summary["api_record_total_match"] = record_total == retrieved_total
                partition_summaries.append(summary)
                print(f"[FINRA ATS] complete week={week} tier={tier} rows={retrieved_total} record_total={record_total}", flush=True)
                if len(sample_rows) < 100:
                    for row in rows:
                        if str(row.get("summaryTypeCode") or "").upper() in SYMBOL_AGGREGATES:
                            sample_rows.append({key: row.get(key) for key in FIELDS})
                            if len(sample_rows) >= 100:
                                break
            except Exception as exc:
                errors.append({"week": week, "tier": tier, "error": repr(exc)})
                partition_summaries.append({
                    "week": week, "tier": tier, "rows_total": 0,
                    "symbol_aggregate_rows": 0, "aggregate_unique_symbols": 0,
                    "legacy_335_union_coverage_pct": 0.0,
                    "row_partition_mismatch_count": None,
                })

    per_week = []
    for week in WEEKS:
        ats = week_ats_symbols[week]
        otc = week_otc_symbols[week]
        combined = ats | otc
        parts = [x for x in partition_summaries if x.get("week") == week]
        per_week.append({
            "week": week,
            "tier_partition_count": len(parts),
            "ats_unique_symbols": len(ats),
            "otc_unique_symbols": len(otc),
            "union_unique_symbols": len(combined),
            "legacy_335_ats_coverage_pct": round(100 * len(legacy & ats) / len(legacy), 2),
            "legacy_335_otc_coverage_pct": round(100 * len(legacy & otc) / len(legacy), 2),
            "legacy_335_union_coverage_pct": round(100 * len(legacy & combined) / len(legacy), 2),
            "all_tiers_have_symbol_aggregates": len(parts) == 2 and all(x.get("symbol_aggregate_rows", 0) > 0 for x in parts),
        })

    no_partition_errors = not errors
    exact_rows = no_partition_errors and all(
        x.get("row_partition_mismatch_count") == 0 for x in partition_summaries
    )
    coverage_pass = bool(per_week) and all(
        x["tier_partition_count"] == 2
        and x["legacy_335_union_coverage_pct"] >= 90.0
        and x["all_tiers_have_symbol_aggregates"]
        for x in per_week
    )
    publication_pass = bool(partition_summaries) and all(
        x.get("initial_published_date_nonnull_pct", 0.0) >= 99.0
        and x.get("publication_before_minimum_delay_rows", 0) == 0
        for x in partition_summaries
    )

    summary = {
        "phase": 100,
        "source": "FINRA OTCMarket weeklySummaryHistoric",
        "audit_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "sample_weeks": list(WEEKS),
        "tiers": list(TIERS),
        "legacy_f80_universe_size": len(legacy),
        "partitions_expected": len(WEEKS) * len(TIERS),
        "partitions_completed": sum(1 for x in partition_summaries if x.get("rows_total", 0) > 0),
        "partitions": partition_summaries,
        "per_week": per_week,
        "page_hashes": page_hashes,
        "errors": errors,
        "gates": {
            "no_request_or_partition_errors": no_partition_errors,
            "exact_requested_week_and_tier": exact_rows,
            "at_least_90pct_legacy_union_coverage_each_week": coverage_pass,
            "initial_published_date_at_least_99pct_and_delay_plausible": publication_pass,
        },
        "data_gate": "PASS_COVERAGE_SCHEMA" if no_partition_errors and exact_rows and coverage_pass and all(x.get("api_record_total_match") is True for x in partition_summaries) else "FAIL_OR_PARTIAL",
        "publication_gate": "PASS" if publication_pass else "FAIL_OR_PARTIAL",
        "pit_vintage_status": "CONDITIONAL_CURRENT_VALUE_REVISION_HISTORY_NOT_PROVEN",
        "pit_rule_candidate": "Use the later of initialPublishedDate and lastUpdateDate, then delay execution to the next trading session; do not use current revised values before the latest update date. This is a conservative candidate rule, not a validated historical-vintage guarantee.",
        "economic_interpretation": "ATS/OTC symbol aggregates measure reported off-exchange activity, not aggressor direction, beneficial owner, or informed trading.",
        "broad_universe_status": "NOT_ESTABLISHED; 335-name overlap is legacy comparability only, and ticker-only rows require PIT security identity before broad-universe returns.",
        "forward_returns_used": False,
        "alpha_test_authorized": False,
        "f80_changed": False,
    }
    with (OUT / "partition_summary.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(partition_summaries[0].keys()) if partition_summaries else ["week", "tier"])
        writer.writeheader()
        writer.writerows(partition_summaries)
    with (OUT / "page_hashes.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "week", "tier", "page", "offset", "rows", "record_total",
                "status_polls", "request_id", "async_status", "result_expires", "sha256",
            ],
        )
        writer.writeheader()
        writer.writerows(page_hashes)
    (OUT / "sample_symbol_rows.json").write_text(json.dumps(sample_rows, indent=2), encoding="utf-8")
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2), flush=True)

    if summary["data_gate"] != "PASS_COVERAGE_SCHEMA" or not publication_pass or not summary["gates"]["api_record_total_reconciled"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()

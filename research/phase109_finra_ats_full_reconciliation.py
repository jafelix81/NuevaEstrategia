#!/usr/bin/env python3
"""Phase 109: full-field FINRA ATS cohort and aggregation reconciliation.

Data-feasibility only. No prices, forward returns, alpha tests or F80 changes.
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import json
import os
import time
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

import requests

BASE = "https://api.finra.org/data/group/otcmarket/name/weeklySummaryHistoric"
WEEKS = ("2022-01-03", "2023-01-09", "2024-01-08", "2025-01-06", "2025-10-20")
TIERS = ("T1", "T2")
PARTITIONS = tuple((week, tier) for week in WEEKS for tier in TIERS)
PAGE_SIZE = 5000
MAX_PAGES = 200
OUT = Path("phase109_finra_ats_full_reconciliation")
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
SYMBOL_AGGREGATES = {"ATS_W_SMBL", "OTC_W_SMBL"}
SYMBOL_FIRM = {"ATS_W_SMBL_FIRM", "OTC_W_SMBL_FIRM"}
SYMBOL_BEARING = SYMBOL_AGGREGATES | SYMBOL_FIRM
KNOWN_TYPES = {
    "ATS_W_SMBL", "ATS_W_SMBL_FIRM", "OTC_W_SMBL", "OTC_W_SMBL_FIRM",
    "ATS_W_FIRM", "OTC_W_FIRM", "ATS_W_VOL_STATS", "OTC_W_VOL_STATS",
}
PAGE_FIELDS = [
    "week", "tier", "page", "offset", "rows", "record_total",
    "page_count_source", "record_limit", "record_offset",
    "request_attempts", "request_id", "sha256",
]
RECON_FIELDS = [
    "week", "tier", "family", "symbol", "cohort_last_reported_date",
    "previous_aggregate_date", "firm_dates_in_cohort",
    "aggregate_rows_for_date", "firm_rows_in_cohort",
    "aggregate_quantity", "firm_quantity", "quantity_match",
    "aggregate_trades", "firm_trades", "trade_match",
    "cohort_match", "trailing_unmatched_firm_rows",
]
SYMBOL_SUMMARY_FIELDS = [
    "week", "tier", "family", "symbol", "aggregate_dates",
    "firm_dates", "aggregate_rows", "firm_rows",
    "aggregate_quantity_total", "firm_quantity_total",
    "total_quantity_match", "total_trades_match",
    "cohort_count", "cohort_matches", "all_cohorts_match",
    "missing_aggregate_date_rows", "missing_firm_date_rows",
    "trailing_unmatched_firm_rows", "fully_reconciled",
]


def clean(value) -> str:
    return "" if value is None else str(value).strip()


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


def parse_date(value):
    raw = clean(value)
    if not raw:
        return None
    try:
        return date.fromisoformat(raw[:10])
    except ValueError:
        return None


def parse_decimal(value):
    raw = clean(value)
    if not raw:
        return None
    try:
        number = Decimal(raw.replace(",", ""))
    except (InvalidOperation, ValueError):
        return None
    if not number.is_finite():
        return None
    return number


def parse_page_metadata(headers, rows, offset: int):
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


def fetch_partition(session, week: str, tier: str, raw_writer):
    rows, pages = [], []
    offset, expected_total = 0, None
    for page in range(MAX_PAGES):
        response, attempts = post_page(session, build_payload(week, tier, offset))
        page_rows = parse_response(response.json())
        total, count, count_source = parse_page_metadata(response.headers, page_rows, offset)
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
        for row in page_rows:
            raw_writer.writerow({
                "requested_week": week,
                "requested_tier": tier,
                **{field: clean(row.get(field)) for field in FIELDS},
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


def expanded_candidate_key(row):
    return (
        clean(row.get("issueSymbolIdentifier")).upper(),
        clean(row.get("weekStartDate"))[:10],
        clean(row.get("tierIdentifier")).upper(),
        clean(row.get("summaryTypeCode")).upper(),
        clean(row.get("productTypeCode")).upper(),
        clean(row.get("MPID")).upper(),
        clean(row.get("firmCRDNumber")),
        clean(row.get("lastReportedDate"))[:10],
    )


def grouped_collisions(rows, key_fn):
    groups = defaultdict(list)
    for row in rows:
        groups[key_fn(row)].append(row)
    return {key: group for key, group in groups.items() if len(group) > 1}


def sum_field(rows, field):
    values = [parse_decimal(row.get(field)) for row in rows]
    valid = [value for value in values if value is not None]
    return sum(valid, Decimal("0")), len(values) - len(valid)


def family_for(summary_type):
    value = clean(summary_type).upper()
    if value.startswith("ATS_"):
        return "ATS"
    if value.startswith("OTC_"):
        return "OTC"
    return None


def cohort_reconcile(rows, week: str, tier: str):
    aggregate_groups = defaultdict(list)
    firm_groups = defaultdict(list)
    missing_symbol_rows = 0
    missing_aggregate_date_rows = 0
    missing_firm_date_rows = 0
    for row in rows:
        st = clean(row.get("summaryTypeCode")).upper()
        if st not in SYMBOL_BEARING:
            continue
        symbol = clean(row.get("issueSymbolIdentifier")).upper()
        if not symbol:
            missing_symbol_rows += 1
            continue
        family = family_for(st)
        key = (family, symbol)
        if st in SYMBOL_AGGREGATES:
            aggregate_groups[key].append(row)
            if parse_date(row.get("lastReportedDate")) is None:
                missing_aggregate_date_rows += 1
        else:
            firm_groups[key].append(row)
            if parse_date(row.get("lastReportedDate")) is None:
                missing_firm_date_rows += 1

    detail_rows = []
    symbol_rows = []
    family_stats = {}
    for family in ("ATS", "OTC"):
        keys = sorted(
            key for key in set(aggregate_groups) | set(firm_groups)
            if key[0] == family
        )
        stats = Counter()
        for key in keys:
            _, symbol = key
            agg_rows = aggregate_groups.get(key, [])
            firm_rows = firm_groups.get(key, [])
            agg_by_date = defaultdict(list)
            firm_by_date = defaultdict(list)
            agg_missing_date = []
            firm_missing_date = []
            for row in agg_rows:
                d = parse_date(row.get("lastReportedDate"))
                (agg_by_date[d] if d else agg_missing_date).append(row)
            for row in firm_rows:
                d = parse_date(row.get("lastReportedDate"))
                (firm_by_date[d] if d else firm_missing_date).append(row)

            agg_dates = sorted(agg_by_date)
            firm_dates = sorted(firm_by_date)
            agg_qty, agg_qty_invalid = sum_field(agg_rows, "totalWeeklyShareQuantity")
            firm_qty, firm_qty_invalid = sum_field(firm_rows, "totalWeeklyShareQuantity")
            agg_trades, agg_trade_invalid = sum_field(agg_rows, "totalWeeklyTradeCount")
            firm_trades, firm_trade_invalid = sum_field(firm_rows, "totalWeeklyTradeCount")
            total_qty_match = (
                agg_qty_invalid == 0 and firm_qty_invalid == 0 and agg_qty == firm_qty
            )
            total_trade_match = (
                agg_trade_invalid == 0 and firm_trade_invalid == 0 and agg_trades == firm_trades
            )
            if agg_rows and firm_rows:
                stats["keys_with_both_levels"] += 1
            elif agg_rows:
                stats["aggregate_only_keys"] += 1
            else:
                stats["firm_only_keys"] += 1
            if total_qty_match:
                stats["total_quantity_match_keys"] += 1
            if total_trade_match:
                stats["total_trade_match_keys"] += 1

            previous_date = None
            cohort_matches = 0
            cohort_count = 0
            trailing_rows = []
            for agg_date in agg_dates:
                lower_dates = [
                    d for d in firm_dates
                    if (previous_date is None or d > previous_date) and d <= agg_date
                ]
                cohort_firms = [
                    row for d in lower_dates for row in firm_by_date[d]
                ]
                cohort_aggs = agg_by_date[agg_date]
                a_qty, a_qty_invalid = sum_field(cohort_aggs, "totalWeeklyShareQuantity")
                f_qty, f_qty_invalid = sum_field(cohort_firms, "totalWeeklyShareQuantity")
                a_trades, a_trade_invalid = sum_field(cohort_aggs, "totalWeeklyTradeCount")
                f_trades, f_trade_invalid = sum_field(cohort_firms, "totalWeeklyTradeCount")
                qty_match = (
                    a_qty_invalid == 0 and f_qty_invalid == 0 and a_qty == f_qty
                )
                trade_match = (
                    a_trade_invalid == 0 and f_trade_invalid == 0 and a_trades == f_trades
                )
                cohort_match = qty_match and trade_match and bool(cohort_firms)
                cohort_count += 1
                if cohort_match:
                    cohort_matches += 1
                detail_rows.append({
                    "week": week, "tier": tier, "family": family, "symbol": symbol,
                    "cohort_last_reported_date": agg_date.isoformat(),
                    "previous_aggregate_date": previous_date.isoformat() if previous_date else "",
                    "firm_dates_in_cohort": ";".join(d.isoformat() for d in lower_dates),
                    "aggregate_rows_for_date": len(cohort_aggs),
                    "firm_rows_in_cohort": len(cohort_firms),
                    "aggregate_quantity": str(a_qty),
                    "firm_quantity": str(f_qty),
                    "quantity_match": qty_match,
                    "aggregate_trades": str(a_trades),
                    "firm_trades": str(f_trades),
                    "trade_match": trade_match,
                    "cohort_match": cohort_match,
                    "trailing_unmatched_firm_rows": 0,
                })
                previous_date = agg_date
            if agg_dates:
                trailing_dates = [d for d in firm_dates if d > agg_dates[-1]]
                trailing_rows = [r for d in trailing_dates for r in firm_by_date[d]]
            else:
                trailing_dates = firm_dates
                trailing_rows = firm_rows
            if trailing_rows:
                stats["keys_with_trailing_firm_rows"] += 1
                detail_rows.append({
                    "week": week, "tier": tier, "family": family, "symbol": symbol,
                    "cohort_last_reported_date": "",
                    "previous_aggregate_date": agg_dates[-1].isoformat() if agg_dates else "",
                    "firm_dates_in_cohort": ";".join(d.isoformat() for d in trailing_dates),
                    "aggregate_rows_for_date": 0,
                    "firm_rows_in_cohort": len(trailing_rows),
                    "aggregate_quantity": "0",
                    "firm_quantity": str(sum_field(trailing_rows, "totalWeeklyShareQuantity")[0]),
                    "quantity_match": False,
                    "aggregate_trades": "0",
                    "firm_trades": str(sum_field(trailing_rows, "totalWeeklyTradeCount")[0]),
                    "trade_match": False,
                    "cohort_match": False,
                    "trailing_unmatched_firm_rows": len(trailing_rows),
                })
            all_cohorts_match = cohort_count > 0 and cohort_matches == cohort_count
            fully_reconciled = (
                bool(agg_rows) and bool(firm_rows)
                and all_cohorts_match
                and not trailing_rows
                and not agg_missing_date
                and not firm_missing_date
                and agg_qty_invalid == 0 and firm_qty_invalid == 0
                and agg_trade_invalid == 0 and firm_trade_invalid == 0
            )
            if fully_reconciled:
                stats["fully_reconciled_keys"] += 1
            stats["cohort_count"] += cohort_count
            stats["cohort_matches"] += cohort_matches
            symbol_rows.append({
                "week": week, "tier": tier, "family": family, "symbol": symbol,
                "aggregate_dates": ";".join(d.isoformat() for d in agg_dates),
                "firm_dates": ";".join(d.isoformat() for d in firm_dates),
                "aggregate_rows": len(agg_rows), "firm_rows": len(firm_rows),
                "aggregate_quantity_total": str(agg_qty),
                "firm_quantity_total": str(firm_qty),
                "total_quantity_match": total_qty_match,
                "total_trades_match": total_trade_match,
                "cohort_count": cohort_count, "cohort_matches": cohort_matches,
                "all_cohorts_match": all_cohorts_match,
                "missing_aggregate_date_rows": len(agg_missing_date),
                "missing_firm_date_rows": len(firm_missing_date),
                "trailing_unmatched_firm_rows": len(trailing_rows),
                "fully_reconciled": fully_reconciled,
            })
        family_stats[family] = {
            "symbol_keys": len(keys),
            "keys_with_both_levels": stats["keys_with_both_levels"],
            "aggregate_only_keys": stats["aggregate_only_keys"],
            "firm_only_keys": stats["firm_only_keys"],
            "total_quantity_match_keys": stats["total_quantity_match_keys"],
            "total_trade_match_keys": stats["total_trade_match_keys"],
            "cohort_count": stats["cohort_count"],
            "cohort_matches": stats["cohort_matches"],
            "keys_with_trailing_firm_rows": stats["keys_with_trailing_firm_rows"],
            "fully_reconciled_keys": stats["fully_reconciled_keys"],
        }
    return {
        "missing_symbol_rows": missing_symbol_rows,
        "missing_aggregate_date_rows": missing_aggregate_date_rows,
        "missing_firm_date_rows": missing_firm_date_rows,
        "families": family_stats,
    }, detail_rows, symbol_rows


def analyze_partition(rows, week: str, tier: str, record_total: int, pages: list[dict]):
    date_tier_mismatches = []
    missing_symbol_examples = []
    type_counts = Counter()
    product_counts = Counter()
    unknown_types = Counter()
    symbol_rows = [r for r in rows if clean(r.get("summaryTypeCode")).upper() in SYMBOL_BEARING]
    aggregate_rows = [r for r in rows if clean(r.get("summaryTypeCode")).upper() in SYMBOL_AGGREGATES]
    firm_rows = [r for r in rows if clean(r.get("summaryTypeCode")).upper() in SYMBOL_FIRM]
    for i, row in enumerate(rows):
        actual_week = clean(row.get("weekStartDate"))[:10]
        actual_tier = clean(row.get("tierIdentifier")).upper()
        if actual_week != week or actual_tier != tier:
            date_tier_mismatches.append({
                "row_index": i, "actual_week": actual_week, "actual_tier": actual_tier,
            })
        st = clean(row.get("summaryTypeCode")).upper()
        type_counts[st or "<blank>"] += 1
        if st not in KNOWN_TYPES:
            unknown_types[st or "<blank>"] += 1
        if st in SYMBOL_BEARING and not clean(row.get("issueSymbolIdentifier")):
            if len(missing_symbol_examples) < 25:
                missing_symbol_examples.append({
                    "row_index": i,
                    **{field: row.get(field) for field in FIELDS},
                })
        product_counts[clean(row.get("productTypeCode")) or "<blank>"] += 1

    revised = sum(
        1 for row in aggregate_rows
        if parse_date(row.get("initialPublishedDate"))
        and parse_date(row.get("lastUpdateDate"))
        and parse_date(row.get("lastUpdateDate")) > parse_date(row.get("initialPublishedDate"))
    )
    pub_lags = []
    for row in aggregate_rows:
        start = parse_date(row.get("weekStartDate"))
        published = parse_date(row.get("initialPublishedDate"))
        if start and published:
            pub_lags.append((published - start).days)
    key_collisions = grouped_collisions(rows, expanded_candidate_key)
    aggregate_key_collisions = grouped_collisions(
        aggregate_rows,
        lambda r: (
            clean(r.get("issueSymbolIdentifier")).upper(),
            clean(r.get("weekStartDate"))[:10],
            clean(r.get("tierIdentifier")).upper(),
            clean(r.get("summaryTypeCode")).upper(),
            clean(r.get("productTypeCode")).upper(),
            clean(r.get("lastReportedDate"))[:10],
        ),
    )
    participant_id_missing = sum(
        1 for row in firm_rows
        if not clean(row.get("MPID"))
        and clean(row.get("firmCRDNumber")) in {"", "0"}
    )
    numeric_invalid = Counter()
    negative_numeric = Counter()
    for row in rows:
        for field in ("totalWeeklyShareQuantity", "totalWeeklyTradeCount"):
            value = parse_decimal(row.get(field))
            if value is None:
                numeric_invalid[field] += 1
            elif value < 0:
                negative_numeric[field] += 1

    reconciliation, detail_rows, symbol_reconciliation = cohort_reconcile(rows, week, tier)
    return {
        "week": week, "tier": tier,
        "rows_total": len(rows), "record_total": record_total,
        "record_total_match": len(rows) == record_total,
        "pages": len(pages),
        "week_tier_mismatch_rows": len(date_tier_mismatches),
        "week_tier_mismatch_examples": date_tier_mismatches[:10],
        "summary_type_counts": dict(type_counts),
        "unknown_summary_type_counts": dict(unknown_types),
        "product_type_counts": dict(product_counts),
        "symbol_bearing_rows": len(symbol_rows),
        "symbol_aggregate_rows": len(aggregate_rows),
        "symbol_firm_rows": len(firm_rows),
        "missing_symbol_rows": sum(
            1 for row in symbol_rows if not clean(row.get("issueSymbolIdentifier"))
        ),
        "missing_symbol_examples": missing_symbol_examples,
        "expanded_candidate_key_collision_groups": len(key_collisions),
        "aggregate_candidate_key_collision_groups": len(aggregate_key_collisions),
        "participant_identity_missing_symbol_firm_rows": participant_id_missing,
        "aggregate_rows_missing_initial_publication_date": sum(
            1 for row in aggregate_rows if not parse_date(row.get("initialPublishedDate"))
        ),
        "aggregate_rows_missing_last_update_date": sum(
            1 for row in aggregate_rows if not parse_date(row.get("lastUpdateDate"))
        ),
        "aggregate_rows_missing_last_reported_date": sum(
            1 for row in aggregate_rows if not parse_date(row.get("lastReportedDate"))
        ),
        "aggregate_rows_updated_after_first_publication": revised,
        "publication_lag_days_min": min(pub_lags) if pub_lags else None,
        "publication_lag_days_max": max(pub_lags) if pub_lags else None,
        "publication_lag_days_counts": dict(Counter(pub_lags)),
        "numeric_invalid_counts": dict(numeric_invalid),
        "negative_numeric_counts": dict(negative_numeric),
        "cohort_reconciliation": reconciliation,
    }, detail_rows, symbol_reconciliation


def sha256_file(path: Path):
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update({
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "SmartMoneyResearch-Phase109/1.0",
    })
    token = os.getenv("FINRA_API_TOKEN", "").strip()
    if token:
        session.headers["Authorization"] = f"Bearer {token}"

    summaries, page_hashes, details, symbol_summaries, errors = [], [], [], [], []
    raw_path = OUT / "raw_rows.csv.gz"
    with gzip.open(raw_path, "wt", newline="", encoding="utf-8") as raw_file:
        writer = csv.DictWriter(
            raw_file,
            fieldnames=["requested_week", "requested_tier", *FIELDS],
            extrasaction="ignore",
        )
        writer.writeheader()
        for week, tier in PARTITIONS:
            print(f"[Phase109] start {week}/{tier}", flush=True)
            try:
                rows, pages, total = fetch_partition(session, week, tier, writer)
                page_hashes.extend(pages)
                summary, partition_details, partition_symbols = analyze_partition(
                    rows, week, tier, total, pages
                )
                summaries.append(summary)
                details.extend(partition_details)
                symbol_summaries.extend(partition_symbols)
                fam = summary["cohort_reconciliation"]["families"]
                print(
                    f"[Phase109] complete {week}/{tier} rows={len(rows)} pages={len(pages)} "
                    f"ATS_fully_reconciled={fam['ATS']['fully_reconciled_keys']}/"
                    f"{fam['ATS']['symbol_keys']} OTC_fully_reconciled="
                    f"{fam['OTC']['fully_reconciled_keys']}/{fam['OTC']['symbol_keys']}",
                    flush=True,
                )
            except Exception as exc:
                errors.append({"week": week, "tier": tier, "error": repr(exc)})
                print(f"[Phase109] ERROR {week}/{tier}: {exc!r}", flush=True)

    with (OUT / "page_hashes.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=PAGE_FIELDS)
        writer.writeheader()
        writer.writerows(page_hashes)
    with (OUT / "partition_summary.csv").open("w", newline="", encoding="utf-8") as f:
        fields = [
            "week", "tier", "rows_total", "record_total", "record_total_match",
            "pages", "week_tier_mismatch_rows", "symbol_aggregate_rows",
            "symbol_firm_rows", "missing_symbol_rows",
            "expanded_candidate_key_collision_groups",
            "aggregate_candidate_key_collision_groups",
            "aggregate_rows_updated_after_first_publication",
        ]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in summaries:
            writer.writerow({field: row.get(field) for field in fields})
    with (OUT / "cohort_reconciliation.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=RECON_FIELDS)
        writer.writeheader()
        writer.writerows(details)
    with (OUT / "symbol_reconciliation.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=SYMBOL_SUMMARY_FIELDS)
        writer.writeheader()
        writer.writerows(symbol_summaries)

    summary = {
        "phase": 109,
        "source": "FINRA OTCMarket weeklySummaryHistoric",
        "audit_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "partitions_requested": [{"week": w, "tier": t} for w, t in PARTITIONS],
        "partitions_completed": len(summaries),
        "partitions": summaries,
        "page_hash_count": len(page_hashes),
        "total_rows": sum(x["rows_total"] for x in summaries),
        "errors": errors,
        "fields_requested": FIELDS,
        "candidate_firm_key": [
            "issueSymbolIdentifier", "weekStartDate", "tierIdentifier",
            "summaryTypeCode", "MPID", "firmCRDNumber", "lastReportedDate",
        ],
        "cohort_reconciliation_rule": (
            "For each symbol/family, symbol-only aggregate rows are ordered by "
            "lastReportedDate. Each aggregate row is compared with the sum of "
            "symbol-firm rows whose lastReportedDate is after the previous "
            "aggregate date and on/before the current aggregate date. This is "
            "a falsifiable diagnostic rule, not an assumed FINRA specification."
        ),
        "raw_rows_file": raw_path.name,
        "raw_rows_sha256": sha256_file(raw_path),
        "forward_returns_used": False,
        "alpha_test_authorized": False,
        "f80_changed": False,
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    (OUT / "reconciliation_mismatches.json").write_text(
        json.dumps(
            [row for row in symbol_summaries if not row["fully_reconciled"]],
            indent=2,
        ),
        encoding="utf-8",
    )
    print(json.dumps({
        "phase": 109,
        "partitions_completed": len(summaries),
        "total_rows": summary["total_rows"],
        "page_hash_count": len(page_hashes),
        "errors": errors,
        "raw_rows_sha256": summary["raw_rows_sha256"],
    }, indent=2), flush=True)
    if errors or len(summaries) != len(PARTITIONS):
        raise RuntimeError("Phase 109 did not complete all ten FINRA partitions")


if __name__ == "__main__":
    main()

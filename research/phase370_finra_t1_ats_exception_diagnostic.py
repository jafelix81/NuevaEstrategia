#!/usr/bin/env python3
"""Phase 370: diagnose the two residual FINRA T1 ATS exceptions from Phase 369.

This is a source-feasibility diagnostic only. It retrieves the full boundary
week (2021-11-15) and the single bridge-review week (2025-11-10), then emits
date-gap distributions and a hashed, identifier-free description of any
ambiguous ATS symbol aggregate. No raw symbols, MPIDs, CRDs or firm names are
written to disk. No returns or alpha tests are run.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

import requests

BASE_URL = "https://api.finra.org/data/group/otcmarket/name/weeklySummaryHistoric"
PAGE_LIMIT = 5000
MAX_OFFSET = 500000
WEEKS = ("2021-11-15", "2025-11-10")
TIER = "T1"
ATS_TYPES = {"ATS_W_FIRM", "ATS_W_SMBL", "ATS_W_SMBL_FIRM", "ATS_W_VOL_STATS"}


def norm(value):
    return str(value or "").strip().upper()


def parse_date(value):
    if value is None or str(value).strip() == "":
        return None
    try:
        return date.fromisoformat(str(value).strip()[:10])
    except ValueError:
        return None


def parse_integer(value):
    if value is None or str(value).strip() == "":
        return None
    try:
        x = Decimal(str(value).replace(",", "").strip())
    except (InvalidOperation, ValueError):
        return None
    if not x.is_finite() or x < 0 or x != x.to_integral_value():
        return None
    return int(x)


def hash_symbol(symbol):
    """Stable pseudonymous diagnostic key; never emit the source symbol."""
    return hashlib.sha256(norm(symbol).encode("utf-8")).hexdigest()[:16]


def build_query(week, limit, offset):
    return {
        "compareFilters": [
            {"fieldName": "historicalWeek", "fieldValue": week, "compareType": "EQUAL"},
            {"fieldName": "tierIdentifier", "fieldValue": TIER, "compareType": "EQUAL"},
        ],
        "limit": limit,
        "offset": offset,
    }


def parse_rows(payload):
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if isinstance(payload, dict):
        if payload.get("message") or payload.get("statusCode"):
            raise RuntimeError("FINRA returned an error envelope")
        data = payload.get("data", [])
        if isinstance(data, dict):
            data = data.get("data", [])
        if isinstance(data, list):
            return [x for x in data if isinstance(x, dict)]
        if data in (None, ""):
            return []
    raise RuntimeError("Unexpected FINRA response envelope")


def request_page(session, week, offset):
    for attempt in range(4):
        try:
            response = session.post(
                BASE_URL, json=build_query(week, PAGE_LIMIT, offset), timeout=(20, 120)
            )
            if response.status_code in {408, 429, 500, 502, 503, 504}:
                if attempt == 3:
                    response.raise_for_status()
                retry = response.headers.get("Retry-After")
                try:
                    delay = float(retry) if retry else 2 ** (attempt + 1)
                except (TypeError, ValueError):
                    delay = 2 ** (attempt + 1)
                time.sleep(max(0, min(delay, 30)))
                continue
            response.raise_for_status()
            rows = parse_rows(response.json())
            headers = {str(k).lower(): v for k, v in response.headers.items()}
            if "record-total" not in headers:
                raise RuntimeError("Missing Record-Total")
            if "record-offset" in headers and int(headers["record-offset"]) != offset:
                raise RuntimeError("Record-Offset mismatch")
            if int(headers.get("total-records-on-page", len(rows))) != len(rows):
                raise RuntimeError("Total-Records-On-Page mismatch")
            if len(rows) > PAGE_LIMIT:
                raise RuntimeError("Page exceeded requested limit")
            return rows, int(headers["record-total"])
        except (requests.RequestException, ValueError) as exc:
            if attempt == 3:
                raise RuntimeError(f"FINRA request failed ({type(exc).__name__})") from exc
            time.sleep(min(2 ** (attempt + 1), 20))
    raise RuntimeError("FINRA request retries exhausted")


def fetch_partition(session, week):
    rows, total, offset, pages = [], None, 0, 0
    while True:
        batch, record_total = request_page(session, week, offset)
        if total is None:
            total = record_total
        elif total != record_total:
            raise RuntimeError("Record-Total changed during pagination")
        pages += 1
        rows.extend(batch)
        print(f"[Phase370] {week} offset={offset} rows={len(batch)} total={record_total}", flush=True)
        if len(rows) == total:
            break
        if len(rows) > total or not batch:
            raise RuntimeError("Pagination count mismatch or no progress")
        offset += len(batch)
        if offset > MAX_OFFSET:
            raise RuntimeError("Offset exceeded FINRA maximum")
        time.sleep(0.15)
    return rows, total, pages


def sum_int(rows, field):
    values = [parse_integer(r.get(field)) for r in rows]
    if any(v is None for v in values):
        return None
    return sum(values)


def participant_key(row):
    mpid = norm(row.get("MPID"))
    crd = norm(row.get("firmCRDNumber"))
    name = norm(row.get("marketParticipantName"))
    return mpid or (crd if crd != "0" else "") or name


def grouped_date_summary(rows):
    grouped = defaultdict(lambda: {"rows": 0, "shares": 0, "trades": 0, "invalid_numeric_rows": 0})
    for row in rows:
        key = str(row.get("lastReportedDate") or "__MISSING__")[:10]
        g = grouped[key]
        g["rows"] += 1
        shares = parse_integer(row.get("totalWeeklyShareQuantity"))
        trades = parse_integer(row.get("totalWeeklyTradeCount"))
        if shares is None or trades is None:
            g["invalid_numeric_rows"] += 1
        else:
            g["shares"] += shares
            g["trades"] += trades
    return [{"last_reported_date": k, **grouped[k]} for k in sorted(grouped)]


def ambiguous_symbol_diagnostics(rows):
    aggregates = defaultdict(list)
    firms = defaultdict(list)
    for row in rows:
        typ = norm(row.get("summaryTypeCode"))
        symbol = norm(row.get("issueSymbolIdentifier"))
        if not symbol:
            continue
        if typ == "ATS_W_SMBL":
            aggregates[symbol].append(row)
        elif typ == "ATS_W_SMBL_FIRM":
            firms[symbol].append(row)

    details = []
    for symbol, agg_rows in aggregates.items():
        product_types = sorted({norm(x.get("productTypeCode")) or "__MISSING__" for x in agg_rows})
        if len(agg_rows) == 1 and len(product_types) == 1 and product_types[0] != "__MISSING__":
            continue
        firm_rows = firms.get(symbol, [])
        agg_shares = sum_int(agg_rows, "totalWeeklyShareQuantity")
        agg_trades = sum_int(agg_rows, "totalWeeklyTradeCount")
        firm_shares = sum_int(firm_rows, "totalWeeklyShareQuantity")
        firm_trades = sum_int(firm_rows, "totalWeeklyTradeCount")
        participant_keys = [participant_key(x) for x in firm_rows]
        participant_counts = Counter(k for k in participant_keys if k)
        agg_dates = grouped_date_summary(agg_rows)
        firm_dates = grouped_date_summary(firm_rows)
        agg_date_map = {x["last_reported_date"]: (x["shares"], x["trades"]) for x in agg_dates}
        firm_date_map = {x["last_reported_date"]: (x["shares"], x["trades"]) for x in firm_dates}
        common_dates = sorted(set(agg_date_map) & set(firm_date_map))
        details.append({
            "symbol_hash": hash_symbol(symbol),
            "aggregate_row_count": len(agg_rows),
            "product_type_codes": product_types,
            "aggregate_rows": [{
                "product_type_code": norm(x.get("productTypeCode")) or None,
                "week_start_date": str(x.get("weekStartDate") or "")[:10] or None,
                "summary_start_date": str(x.get("summaryStartDate") or "")[:10] or None,
                "initial_published_date": str(x.get("initialPublishedDate") or "")[:10] or None,
                "last_update_date": str(x.get("lastUpdateDate") or "")[:10] or None,
                "last_reported_date": str(x.get("lastReportedDate") or "")[:10] or None,
                "shares": parse_integer(x.get("totalWeeklyShareQuantity")),
                "trades": parse_integer(x.get("totalWeeklyTradeCount")),
            } for x in sorted(agg_rows, key=lambda z: str(z.get("lastReportedDate") or ""))],
            "firm_row_count": len(firm_rows),
            "firm_unique_participant_keys": len(participant_counts),
            "firm_repeated_participant_keys": sum(1 for n in participant_counts.values() if n > 1),
            "aggregate_total_shares": agg_shares,
            "firm_total_shares": firm_shares,
            "aggregate_total_trades": agg_trades,
            "firm_total_trades": firm_trades,
            "combined_totals_match": (
                agg_shares is not None and firm_shares is not None
                and agg_trades is not None and firm_trades is not None
                and agg_shares == firm_shares and agg_trades == firm_trades
            ),
            "aggregate_by_last_reported_date": agg_dates,
            "firm_by_last_reported_date": firm_dates,
            "last_reported_date_diagnostic_matches": [
                {
                    "last_reported_date": dt,
                    "aggregate_shares": agg_date_map[dt][0],
                    "firm_shares": firm_date_map[dt][0],
                    "aggregate_trades": agg_date_map[dt][1],
                    "firm_trades": firm_date_map[dt][1],
                    "exact_match": agg_date_map[dt] == firm_date_map[dt],
                } for dt in common_dates
            ],
            "last_reported_date_diagnostic_only_not_an_approved_join": True,
        })
    return details


def date_gap_diagnostics(rows):
    by_type = defaultdict(Counter)
    date_triples = defaultdict(Counter)
    for row in rows:
        typ = norm(row.get("summaryTypeCode"))
        if typ not in ATS_TYPES:
            continue
        base = parse_date(row.get("initialPublishedDate"))
        update = parse_date(row.get("lastUpdateDate"))
        if base is None or update is None:
            gap = "__INVALID_OR_MISSING__"
        else:
            gap = str((update - base).days)
        by_type[typ][gap] += 1
        triple = (
            str(row.get("weekStartDate") or "")[:10],
            str(row.get("initialPublishedDate") or "")[:10],
            str(row.get("lastUpdateDate") or "")[:10],
        )
        date_triples[typ][triple] += 1
    return {
        "gap_days_counts_by_summary_type": {
            typ: dict(sorted(counts.items(), key=lambda kv: (kv[0] == "__INVALID_OR_MISSING__", kv[0])))
            for typ, counts in sorted(by_type.items())
        },
        "date_triples_by_summary_type": {
            typ: [
                {"week_start_date": k[0], "initial_published_date": k[1],
                 "last_update_date": k[2], "rows": n}
                for k, n in sorted(counts.items())
            ] for typ, counts in sorted(date_triples.items())
        },
    }


def analyze_partition(rows, week, record_total, pages):
    summary_counts = Counter(norm(r.get("summaryTypeCode")) or "__MISSING__" for r in rows)
    ats_rows = [r for r in rows if norm(r.get("summaryTypeCode")) in ATS_TYPES]
    positive_gaps = 0
    missing_dates = 0
    for row in ats_rows:
        base = parse_date(row.get("initialPublishedDate"))
        update = parse_date(row.get("lastUpdateDate"))
        if base is None or update is None:
            missing_dates += 1
        elif (update - base).days > 0:
            positive_gaps += 1
    anomalies = ambiguous_symbol_diagnostics(rows)
    return {
        "week": week,
        "rows": len(rows),
        "record_total": record_total,
        "pages": pages,
        "retrieval_count_match": len(rows) == record_total,
        "summary_type_counts": dict(sorted(summary_counts.items())),
        "ats_rows": len(ats_rows),
        "ats_positive_update_gaps": positive_gaps,
        "ats_missing_or_invalid_date_pairs": missing_dates,
        "ats_date_gate": len(ats_rows) > 0 and positive_gaps == 0 and missing_dates == 0,
        "date_gap_diagnostics": date_gap_diagnostics(rows),
        "ambiguous_ats_aggregate_symbols": anomalies,
        "ambiguous_ats_aggregate_symbol_count": len(anomalies),
        "raw_rows_retained": False,
        "raw_identifiers_retained": False,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="phase370_finra_t1_ats_exception_diagnostic")
    args = parser.parse_args()
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update({
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Data-API-Version": "1",
        "User-Agent": "SmartMoneyResearch-Phase370/1.0",
    })
    token = os.getenv("FINRA_API_TOKEN", "").strip()
    if token:
        session.headers["Authorization"] = f"Bearer {token}"

    partitions, errors = [], []
    for week in WEEKS:
        try:
            rows, total, pages = fetch_partition(session, week)
            partitions.append(analyze_partition(rows, week, total, pages))
            del rows
        except Exception as exc:
            errors.append({"week": week, "error_type": type(exc).__name__, "error": str(exc)[:240]})

    complete = len(partitions) == len(WEEKS) and not errors and all(p["retrieval_count_match"] for p in partitions)
    summary = {
        "phase": 370,
        "source": "FINRA OTCMarket weeklySummaryHistoric",
        "audit_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "sample_weeks": list(WEEKS),
        "expected_partitions": len(WEEKS),
        "completed_partitions": len(partitions),
        "total_rows": sum(p["rows"] for p in partitions),
        "total_pages": sum(p["pages"] for p in partitions),
        "errors": errors,
        "all_partitions_complete": complete,
        "pit_availability_established": False,
        "historical_signal_test_authorized": False,
        "forward_returns_used": False,
        "holdout_used": False,
        "f80_changed": False,
        "raw_rows_retained": False,
        "raw_identifiers_retained": False,
        "partitions": partitions,
        "research_disposition": (
            "BOUNDARY_WEEK_AND_SINGLE_AMBIGUOUS_SYMBOL_DIAGNOSED"
            if complete else "INCOMPLETE_RETRIEVAL_REQUIRES_REVIEW"
        ),
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({
        "phase": 370,
        "all_partitions_complete": complete,
        "total_rows": summary["total_rows"],
        "total_pages": summary["total_pages"],
        "errors": errors,
        "pit_availability_established": False,
        "historical_signal_test_authorized": False,
        "exception_counts": {
            p["week"]: {
                "ats_positive_update_gaps": p["ats_positive_update_gaps"],
                "ambiguous_ats_aggregate_symbol_count": p["ambiguous_ats_aggregate_symbol_count"],
            } for p in partitions
        },
    }, indent=2), flush=True)
    if not complete:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

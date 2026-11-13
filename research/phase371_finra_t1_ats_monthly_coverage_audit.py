#!/usr/bin/env python3
"""Phase 371: monthly T1 ATS coverage, PIT-date and broker-concentration audit.

Selects one historic T1 week per month (closest weekStartDate to day 15) from
2022-01 through the latest available 2025-11 partition. Every selected
partition is retrieved in full. Symbol aggregates are reconciled to firm
rows; multiple aggregate rows are combined only when there is exactly one row
per distinct, nonmissing productTypeCode and the combined symbol total matches
the firm total. Firm rows have no productTypeCode, so no tape-level attribution
is attempted.

Concentration is reported only as broker-dealer reporting-participant
concentration (HHI/top shares), never as beneficial-owner or "smart money"
identity. Raw symbols, MPIDs, CRDs and firm names are not retained.
No returns, alpha, OOS, bootstrap, LOO or holdout tests are run.
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import time
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import requests

BASE = "https://api.finra.org"
GROUP = "otcmarket"
DATASET = "weeklySummaryHistoric"
DATA_URL = f"{BASE}/data/group/{GROUP}/name/{DATASET}"
META_URL = f"{BASE}/metadata/group/{GROUP}/name/{DATASET}"
PARTITIONS_URL = f"{BASE}/partitions/group/{GROUP}/name/{DATASET}"
PAGE_LIMIT = 5000
MAX_OFFSET = 500000
EXPECTED_PARTITION_FIELDS = ("weekStartDate", "tierIdentifier")
START_MONTH = (2022, 1)
END_MONTH = (2025, 11)
TIER = "T1"
ATS_TYPES = {"ATS_W_FIRM", "ATS_W_SMBL", "ATS_W_SMBL_FIRM", "ATS_W_VOL_STATS"}


def request_json(session, url):
    last_error = None
    for attempt in range(4):
        try:
            response = session.get(url, timeout=(20, 90))
            if response.status_code in {408, 429, 500, 502, 503, 504}:
                if attempt == 3:
                    response.raise_for_status()
                retry = response.headers.get("Retry-After")
                try:
                    delay = float(retry) if retry else 3 * (2 ** attempt)
                except (TypeError, ValueError):
                    delay = 3 * (2 ** attempt)
                time.sleep(max(0, min(delay, 60)))
                continue
            response.raise_for_status()
            return response.json(), response.headers
        except (requests.RequestException, ValueError) as exc:
            last_error = exc
            if attempt == 3:
                raise
            time.sleep(min(3 * (2 ** attempt), 30))
    raise RuntimeError(f"Unable to retrieve JSON: {last_error}")


def normalise_partition_object(value, fields):
    if isinstance(value, dict):
        return {str(k): v for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        if value and isinstance(value[0], (list, tuple, dict)):
            return None
        if len(value) == len(fields):
            return dict(zip(fields, value))
        if len(fields) == 1 and len(value) == 1:
            return {fields[0]: value[0]}
    if isinstance(value, str) and len(fields) == 1:
        return {fields[0]: value}
    return None


def parse_partition_payload(payload, fallback_fields=EXPECTED_PARTITION_FIELDS):
    declared = tuple(payload.get("partitionFields") or ())
    fallback = tuple(fallback_fields)
    if declared and fallback and declared != fallback:
        raise ValueError(f"Partition field-order mismatch: {declared} vs {fallback}")
    fields = declared or fallback
    available = payload.get("availablePartitions") or payload.get("partitions") or []
    records = []
    for item in available:
        versions = None
        if isinstance(item, dict):
            raw = item.get("partitions")
            versions = item.get("versions", item.get("version"))
            if isinstance(raw, list) and raw and isinstance(raw[0], (list, tuple, dict)):
                candidates = raw
            else:
                candidates = [raw] if raw is not None else [item]
        else:
            candidates = [item]
        for candidate in candidates:
            record = normalise_partition_object(candidate, fields)
            if record is None:
                continue
            if isinstance(item, dict):
                for field in fields:
                    if field in item and field not in record:
                        record[field] = item[field]
            week = record.get("weekStartDate") or record.get("historicalWeek")
            tier = record.get("tierIdentifier")
            if week is None or tier is None:
                continue
            records.append({
                "weekStartDate": str(week)[:10],
                "tierIdentifier": str(tier),
                "version_count": len(versions) if isinstance(versions, list) else int(versions is not None),
            })
    seen, unique = set(), []
    for row in records:
        key = (row["weekStartDate"], row["tierIdentifier"])
        if key not in seen:
            seen.add(key)
            unique.append(row)
    return fields, records, unique


def month_range(start=START_MONTH, end=END_MONTH):
    y, m = start
    while (y, m) <= end:
        yield y, m
        if m == 12:
            y, m = y + 1, 1
        else:
            m += 1


def select_monthly_weeks(records, start=START_MONTH, end=END_MONTH):
    by_month = defaultdict(list)
    for row in records:
        if row.get("tierIdentifier") != TIER:
            continue
        try:
            d = date.fromisoformat(str(row["weekStartDate"])[:10])
        except (KeyError, ValueError):
            continue
        key = (d.year, d.month)
        if start <= key <= end:
            by_month[key].append(d)
    selected, missing = [], []
    for ym in month_range(start, end):
        candidates = sorted(set(by_month.get(ym, [])))
        if not candidates:
            missing.append(f"{ym[0]:04d}-{ym[1]:02d}")
            continue
        chosen = min(candidates, key=lambda d: (abs(d.day - 15), d))
        selected.append(chosen.isoformat())
    return selected, missing


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
    body = {
        "compareFilters": [
            {"fieldName": "historicalWeek", "fieldValue": week, "compareType": "EQUAL"},
            {"fieldName": "tierIdentifier", "fieldValue": TIER, "compareType": "EQUAL"},
        ],
        "limit": PAGE_LIMIT,
        "offset": offset,
    }
    for attempt in range(4):
        try:
            response = session.post(DATA_URL, json=body, timeout=(20, 120))
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
                raise RuntimeError(f"FINRA page failed ({type(exc).__name__})") from exc
            time.sleep(min(2 ** (attempt + 1), 20))
    raise RuntimeError("FINRA retries exhausted")


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
        print(f"[Phase371] {week} offset={offset} rows={len(batch)} total={record_total}", flush=True)
        if len(rows) == total:
            break
        if len(rows) > total or not batch:
            raise RuntimeError("Pagination mismatch or no progress")
        offset += len(batch)
        if offset > MAX_OFFSET:
            raise RuntimeError("Offset exceeded FINRA maximum")
        time.sleep(0.15)
    return rows, total, pages


def norm(value):
    return str(value or "").strip().upper()


def parse_date(value):
    if value is None or str(value).strip() == "":
        return None
    try:
        return date.fromisoformat(str(value).strip()[:10])
    except ValueError:
        return None


def parse_int(value):
    from decimal import Decimal, InvalidOperation
    if value is None or str(value).strip() == "":
        return None
    try:
        x = Decimal(str(value).replace(",", "").strip())
    except (InvalidOperation, ValueError):
        return None
    if not x.is_finite() or x < 0 or x != x.to_integral_value():
        return None
    return int(x)


def sum_field(rows, field):
    vals = [parse_int(r.get(field)) for r in rows]
    return None if any(v is None for v in vals) else sum(vals)


def participant_key(row):
    mpid = norm(row.get("MPID"))
    crd = norm(row.get("firmCRDNumber"))
    name = norm(row.get("marketParticipantName"))
    return mpid or (crd if crd != "0" else "")


def percentile(values, p):
    values = sorted(values)
    if not values:
        return None
    idx = max(0, min(len(values) - 1, int((len(values) * p + 0.999999999)) - 1))
    return values[idx]


def concentration_stats(symbol_metrics):
    hhi = [x["hhi"] for x in symbol_metrics]
    top1 = [x["top1_share"] for x in symbol_metrics]
    top3 = [x["top3_share"] for x in symbol_metrics]
    nfirms = [x["participant_count"] for x in symbol_metrics]
    def stats(v):
        return {
            "n_symbols": len(v),
            "mean": round(statistics.mean(v), 6) if v else None,
            "median": round(statistics.median(v), 6) if v else None,
            "p90": round(percentile(v, .90), 6) if v else None,
        }
    return {
        "hhi": stats(hhi),
        "top1_share": stats(top1),
        "top3_share": stats(top3),
        "participant_count": stats(nfirms),
    }


def audit_bridge(rows):
    aggregates, firms = defaultdict(list), defaultdict(list)
    missing_aggregate_symbol = missing_firm_symbol = 0
    for row in rows:
        typ = norm(row.get("summaryTypeCode"))
        symbol = norm(row.get("issueSymbolIdentifier"))
        if typ == "ATS_W_SMBL":
            if symbol:
                aggregates[symbol].append(row)
            else:
                missing_aggregate_symbol += 1
        elif typ == "ATS_W_SMBL_FIRM":
            if symbol:
                firms[symbol].append(row)
            else:
                missing_firm_symbol += 1

    agg_symbols, firm_symbols = set(aggregates), set(firms)
    shared = agg_symbols & firm_symbols
    aggregate_only, firm_only = agg_symbols - firm_symbols, firm_symbols - agg_symbols
    ambiguous = multi_product = invalid_numeric = mismatches = 0
    exact = exact_shares = exact_trades = 0
    missing_identity = duplicate_keys = deminimis_rows = 0
    total_agg_shares = total_firm_shares = total_agg_trades = total_firm_trades = 0
    all_participant_keys = set()
    hhi_rows = []
    mapped_symbols = 0

    for symbol in shared:
        ar, fr = aggregates[symbol], firms[symbol]
        product_types = [norm(x.get("productTypeCode")) for x in ar]
        unique_products = set(product_types)
        if any(not p for p in product_types) or len(unique_products) != len(ar):
            ambiguous += 1
            continue
        if len(ar) > 1:
            multi_product += 1
        a_shares, a_trades = sum_field(ar, "totalWeeklyShareQuantity"), sum_field(ar, "totalWeeklyTradeCount")
        f_shares, f_trades = sum_field(fr, "totalWeeklyShareQuantity"), sum_field(fr, "totalWeeklyTradeCount")
        if None in (a_shares, a_trades, f_shares, f_trades):
            invalid_numeric += 1
            continue
        mapped_symbols += 1
        total_agg_shares += a_shares
        total_firm_shares += f_shares
        total_agg_trades += a_trades
        total_firm_trades += f_trades
        sm, tm = a_shares == f_shares, a_trades == f_trades
        exact_shares += int(sm)
        exact_trades += int(tm)
        exact += int(sm and tm)
        mismatches += int(not (sm and tm))

        keys = []
        shares_by_key = defaultdict(int)
        valid_identity = True
        has_deminimis = False
        for row in fr:
            name = norm(row.get("marketParticipantName"))
            is_de_minimis = "DE MINIMIS" in name
            if is_de_minimis:
                deminimis_rows += 1
                has_deminimis = True
                valid_identity = False
                continue
            key = participant_key(row)
            if not key:
                missing_identity += 1
                valid_identity = False
                continue
            keys.append(key)
            all_participant_keys.add(key)
            shares = parse_int(row.get("totalWeeklyShareQuantity"))
            if shares is None:
                valid_identity = False
            else:
                shares_by_key[key] += shares
        counts = Counter(keys)
        duplicate_keys += sum(1 for n in counts.values() if n > 1)
        if valid_identity and not has_deminimis and len(keys) == len(set(keys)) and a_shares > 0:
            vals = sorted(shares_by_key.values(), reverse=True)
            total = sum(vals)
            if total == a_shares and total > 0:
                weights = [v / total for v in vals]
                hhi_rows.append({
                    "hhi": sum(w * w for w in weights),
                    "top1_share": weights[0] if weights else 0.0,
                    "top3_share": sum(weights[:3]),
                    "participant_count": len(weights),
                })

    bridge_gate = (
        bool(mapped_symbols)
        and not aggregate_only and not firm_only
        and not ambiguous and not missing_aggregate_symbol and not missing_firm_symbol
        and not invalid_numeric and mismatches == 0
    )
    concentration_gate = (
        bridge_gate and not missing_identity and not duplicate_keys and not deminimis_rows
        and len(hhi_rows) == mapped_symbols
    )
    return {
        "aggregate_unique_symbols": len(agg_symbols),
        "firm_unique_symbols": len(firm_symbols),
        "shared_symbols": len(shared),
        "aggregate_only_symbols": len(aggregate_only),
        "firm_only_symbols": len(firm_only),
        "mapped_symbols": mapped_symbols,
        "symbol_bridge_coverage_pct": round(100 * mapped_symbols / len(shared), 6) if shared else None,
        "ambiguous_symbols": ambiguous,
        "multi_product_combined_symbols": multi_product,
        "missing_aggregate_symbol_rows": missing_aggregate_symbol,
        "missing_firm_symbol_rows": missing_firm_symbol,
        "exact_share_matches": exact_shares,
        "exact_trade_matches": exact_trades,
        "exact_both_matches": exact,
        "mismatched_symbols": mismatches,
        "invalid_numeric_symbols": invalid_numeric,
        "missing_participant_identity_rows": missing_identity,
        "duplicate_participant_symbol_keys": duplicate_keys,
        "de_minimis_rows": deminimis_rows,
        "unique_participant_keys": len(all_participant_keys),
        "aggregate_shares_total": total_agg_shares,
        "firm_shares_total": total_firm_shares,
        "aggregate_trades_total": total_agg_trades,
        "firm_trades_total": total_firm_trades,
        "share_total_delta": total_firm_shares - total_agg_shares,
        "trade_total_delta": total_firm_trades - total_agg_trades,
        "bridge_gate": "PASS" if bridge_gate else "FAIL_OR_REVIEW",
        "concentration_ready_symbols": len(hhi_rows),
        "concentration_gate": "PASS" if concentration_gate else "FAIL_OR_REVIEW",
        "broker_dealer_reporting_concentration": concentration_stats(hhi_rows),
    }


def analyze_partition(rows, week, record_total, pages):
    summary_counts = Counter(norm(r.get("summaryTypeCode")) or "__MISSING__" for r in rows)
    ats_rows = [r for r in rows if norm(r.get("summaryTypeCode")) in ATS_TYPES]
    gap_counts = Counter()
    publication_lags = Counter()
    missing_invalid = 0
    for row in ats_rows:
        w = parse_date(row.get("weekStartDate"))
        pub = parse_date(row.get("initialPublishedDate"))
        upd = parse_date(row.get("lastUpdateDate"))
        if w is None or pub is None or upd is None:
            missing_invalid += 1
            gap_counts["__MISSING_OR_INVALID__"] += 1
            continue
        gap_counts[str((upd - pub).days)] += 1
        publication_lags[str((pub - w).days)] += 1
    positive = sum(n for k, n in gap_counts.items() if k not in {"__MISSING_OR_INVALID__"} and int(k) > 0)
    negative = sum(n for k, n in gap_counts.items() if k not in {"__MISSING_OR_INVALID__"} and int(k) < 0)
    date_gate = (
        bool(ats_rows) and missing_invalid == 0 and positive == 0 and negative == 0
        and set(publication_lags) == {"21"}
    )
    bridge = audit_bridge(rows)
    symbol_counts = {
        typ: len({norm(r.get("issueSymbolIdentifier")) for r in rows
                  if norm(r.get("summaryTypeCode")) == typ and norm(r.get("issueSymbolIdentifier"))})
        for typ in ("ATS_W_SMBL", "ATS_W_SMBL_FIRM")
    }
    return {
        "week": week,
        "rows": len(rows),
        "record_total": record_total,
        "pages": pages,
        "retrieval_count_match": len(rows) == record_total,
        "summary_type_counts": dict(sorted(summary_counts.items())),
        "ats_rows": len(ats_rows),
        "ats_update_gap_days_counts": dict(sorted(gap_counts.items())),
        "ats_publication_lag_days_counts": dict(sorted(publication_lags.items())),
        "ats_positive_update_gap_rows": positive,
        "ats_negative_update_gap_rows": negative,
        "ats_missing_invalid_date_rows": missing_invalid,
        "ats_date_gate": date_gate,
        "symbol_counts": symbol_counts,
        "bridge": bridge,
        "raw_rows_retained": False,
        "raw_identifiers_retained": False,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="phase371_finra_t1_ats_monthly_coverage_audit")
    args = parser.parse_args()
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update({
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Data-API-Version": "1",
        "User-Agent": "SmartMoneyResearch-Phase371/1.0",
    })
    token = os.getenv("FINRA_API_TOKEN", "").strip()
    if token:
        session.headers["Authorization"] = f"Bearer {token}"

    metadata, _ = request_json(session, META_URL)
    partitions_payload, _ = request_json(session, PARTITIONS_URL)
    fields, raw_partition_records, partition_records = parse_partition_payload(
        partitions_payload, metadata.get("partitionFields") or EXPECTED_PARTITION_FIELDS
    )
    if tuple(metadata.get("partitionFields") or fields) != EXPECTED_PARTITION_FIELDS:
        raise RuntimeError("FINRA partition field order differs from the expected week/tier schema")
    t1_records = [r for r in partition_records if r["tierIdentifier"] == TIER]
    weeks, missing_months = select_monthly_weeks(t1_records)
    expected_months = len(list(month_range()))
    if missing_months or len(weeks) != expected_months:
        raise RuntimeError(f"Monthly partition sample incomplete: missing={missing_months}")

    partitions, errors = [], []
    symbol_union_hashes = set()
    participant_union_hashes = set()
    import hashlib
    for week in weeks:
        try:
            rows, total, pages = fetch_partition(session, week)
            for row in rows:
                typ = norm(row.get("summaryTypeCode"))
                value = norm(row.get("issueSymbolIdentifier"))
                if typ == "ATS_W_SMBL" and value:
                    symbol_union_hashes.add(hashlib.sha256(value.encode("utf-8")).hexdigest())
                if typ == "ATS_W_SMBL_FIRM":
                    key = participant_key(row)
                    if key:
                        participant_union_hashes.add(hashlib.sha256(key.encode("utf-8")).hexdigest())
            partitions.append(analyze_partition(rows, week, total, pages))
            del rows
        except Exception as exc:
            errors.append({"week": week, "error_type": type(exc).__name__, "error": str(exc)[:240]})

    complete = len(partitions) == len(weeks) and not errors and all(p["retrieval_count_match"] for p in partitions)
    summary = {
        "phase": 371,
        "source": "FINRA OTCMarket weeklySummaryHistoric",
        "audit_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "partition_fields": list(fields),
        "raw_partition_records": len(raw_partition_records),
        "unique_partition_pairs": len(partition_records),
        "t1_partition_weeks_available": len(t1_records),
        "sample_rule": "one T1 partition per month, closest weekStartDate to day 15; 2022-01 through 2025-11",
        "expected_months": expected_months,
        "selected_weeks": weeks,
        "missing_months": missing_months,
        "expected_partitions": len(weeks),
        "completed_partitions": len(partitions),
        "total_rows": sum(p["rows"] for p in partitions),
        "total_pages": sum(p["pages"] for p in partitions),
        "errors": errors,
        "all_partitions_complete": complete,
        "all_date_gates_pass": complete and all(p["ats_date_gate"] for p in partitions),
        "all_symbol_bridges_pass": complete and all(p["bridge"]["bridge_gate"] == "PASS" for p in partitions),
        "all_concentration_gates_pass": complete and all(p["bridge"]["concentration_gate"] == "PASS" for p in partitions),
        "unique_symbols_union_count": len(symbol_union_hashes),
        "unique_participant_keys_union_count": len(participant_union_hashes),
        "pit_availability_established": False,
        "historical_signal_test_authorized": False,
        "forward_returns_used": False,
        "holdout_used": False,
        "f80_changed": False,
        "raw_rows_retained": False,
        "raw_identifiers_retained": False,
        "partitions": partitions,
        "research_disposition": (
            "MONTHLY_T1_ATS_DESCRIPTIVE_CANDIDATE"
            if complete and all(p["ats_date_gate"] and p["bridge"]["concentration_gate"] == "PASS" for p in partitions)
            else "MONTHLY_T1_ATS_REQUIRES_EXCLUSIONS_OR_REVIEW"
        ),
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({
        "phase": 371,
        "all_partitions_complete": complete,
        "total_rows": summary["total_rows"],
        "total_pages": summary["total_pages"],
        "all_date_gates_pass": summary["all_date_gates_pass"],
        "all_symbol_bridges_pass": summary["all_symbol_bridges_pass"],
        "all_concentration_gates_pass": summary["all_concentration_gates_pass"],
        "errors": errors,
    }, indent=2), flush=True)
    if not complete:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

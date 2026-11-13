#!/usr/bin/env python3
"""Phase 358: FINRA weekly symbol/firm grain and aggregate reconciliation audit.

Downloads two historical weeklySummaryHistoric partitions (early and late sample),
requests firm identifiers omitted from Phase 100, and tests whether per-firm
symbol rows reconcile to the corresponding symbol-level aggregates.

Data feasibility only. No returns, signal, or alpha test.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import requests

BASE = "https://api.finra.org/data/group/otcmarket/name/weeklySummaryHistoric"
WEEKS = ("2022-01-03", "2025-10-20")
TIERS = ("T1", "T2")
PAGE_SIZE = 5000
MAX_OFFSET = 500000
FIELDS = [
    "issueSymbolIdentifier",
    "weekStartDate",
    "tierIdentifier",
    "summaryTypeCode",
    "productTypeCode",
    "firmCrdNumber",
    "marketParticipantIdentifier",
    "marketParticipantName",
    "totalWeeklyShareQuantity",
    "totalWeeklyTradeCount",
    "initialPublishedDate",
    "lastUpdateDate",
    "lastReportedDate",
]
AGG_TO_FIRM = {
    "ATS_W_SMBL": "ATS_W_SMBL_FIRM",
    "OTC_W_SMBL": "OTC_W_SMBL_FIRM",
}
FIRM_TYPES = set(AGG_TO_FIRM.values())
AGG_TYPES = set(AGG_TO_FIRM)
KNOWN_TYPES = {
    "ATS_W_FIRM", "OTC_W_FIRM", "ATS_W_VOL_STATS", "OTC_W_VOL_STATS",
    *FIRM_TYPES, *AGG_TYPES,
}


def number(value):
    if value in (None, ""):
        return None
    try:
        return float(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return None


def participant_id(row):
    mpid = str(row.get("marketParticipantIdentifier") or "").strip().upper()
    crd = str(row.get("firmCrdNumber") or "").strip()
    if mpid:
        return "MPID:" + mpid
    if crd:
        return "CRD:" + crd
    return None


def _safe_sum(rows, field):
    values = [number(row.get(field)) for row in rows]
    if any(value is None or value < 0 for value in values):
        return None
    return sum(values)


def _percentiles(values):
    if not values:
        return {"p50": None, "p90": None, "max": None}
    values = sorted(float(x) for x in values)
    def q(p):
        idx = (len(values) - 1) * p
        lo = int(idx)
        hi = min(lo + 1, len(values) - 1)
        frac = idx - lo
        return round(values[lo] * (1 - frac) + values[hi] * frac, 6)
    return {"p50": q(0.50), "p90": q(0.90), "max": round(values[-1], 6)}


def audit_rows(rows, week, tier):
    errors = []
    type_counts = Counter()
    aggregates = defaultdict(list)
    firm_rows = defaultdict(list)
    firm_key_groups = defaultdict(list)
    agg_key_groups = defaultdict(list)
    missing_symbol_firm = 0
    missing_participant_firm = 0
    missing_name_firm = 0
    invalid_quantity_rows = 0
    initial_dates, update_dates, reported_dates = [], [], []

    for i, row in enumerate(rows):
        actual_week = str(row.get("weekStartDate") or "")[:10]
        actual_tier = str(row.get("tierIdentifier") or "").upper()
        if actual_week != week:
            errors.append(f"row {i}: weekStartDate={actual_week!r}, expected {week}")
        if actual_tier != tier:
            errors.append(f"row {i}: tierIdentifier={actual_tier!r}, expected {tier}")
        stype = str(row.get("summaryTypeCode") or "").strip().upper()
        type_counts[stype or "MISSING"] += 1
        if stype not in KNOWN_TYPES:
            errors.append(f"row {i}: unknown summaryTypeCode={stype!r}")

        symbol = str(row.get("issueSymbolIdentifier") or "").strip().upper()
        product = str(row.get("productTypeCode") or "").strip().upper()
        if stype in AGG_TYPES:
            if not symbol:
                errors.append(f"row {i}: symbol aggregate missing issueSymbolIdentifier")
                continue
            key = (symbol, product, stype)
            aggregates[key].append(row)
            agg_key_groups[key].append(row)
            for field, target in (
                ("initialPublishedDate", initial_dates),
                ("lastUpdateDate", update_dates),
                ("lastReportedDate", reported_dates),
            ):
                value = str(row.get(field) or "").strip()
                if value:
                    target.append(value)
            for field in ("totalWeeklyShareQuantity", "totalWeeklyTradeCount"):
                value = number(row.get(field))
                if value is None or value < 0:
                    invalid_quantity_rows += 1
        elif stype in FIRM_TYPES:
            if not symbol:
                missing_symbol_firm += 1
                errors.append(f"row {i}: firm-level row missing issueSymbolIdentifier")
                continue
            pid = participant_id(row)
            if not pid:
                missing_participant_firm += 1
            if not str(row.get("marketParticipantName") or "").strip():
                missing_name_firm += 1
            agg_type = next(k for k, v in AGG_TO_FIRM.items() if v == stype)
            key = (symbol, product, agg_type)
            firm_rows[key].append(row)
            firm_key = (symbol, product, stype, pid or "")
            firm_key_groups[firm_key].append(row)
            for field in ("totalWeeklyShareQuantity", "totalWeeklyTradeCount"):
                value = number(row.get(field))
                if value is None or value < 0:
                    invalid_quantity_rows += 1

    duplicate_aggregate_groups = []
    for key, group in agg_key_groups.items():
        if len(group) > 1:
            values = {
                (str(r.get("totalWeeklyShareQuantity") or ""),
                 str(r.get("totalWeeklyTradeCount") or ""),
                 str(r.get("lastReportedDate") or ""))
                for r in group
            }
            duplicate_aggregate_groups.append({
                "symbol": key[0], "product_type": key[1], "summary_type": key[2],
                "rows": len(group), "conflicting": len(values) > 1,
            })

    duplicate_firm_groups = []
    for key, group in firm_key_groups.items():
        if len(group) > 1:
            values = {
                (str(r.get("totalWeeklyShareQuantity") or ""),
                 str(r.get("totalWeeklyTradeCount") or ""),
                 str(r.get("lastReportedDate") or ""))
                for r in group
            }
            duplicate_firm_groups.append({
                "symbol": key[0], "product_type": key[1], "summary_type": key[2],
                "rows": len(group), "conflicting": len(values) > 1,
            })

    matched = 0
    exact_volume = 0
    exact_trades = 0
    mismatch_examples = []
    missing_firm_groups = 0
    invalid_compare_groups = 0
    volume_abs_diffs = []
    trade_abs_diffs = []
    concentration_hhi = []
    concentration_top1 = []
    concentration_symbol_count = 0
    concentration_excluded_duplicate_symbols = set()

    for key, agg_group in aggregates.items():
        symbol, product, agg_type = key
        if len(agg_group) != 1:
            continue
        participant_rows = firm_rows.get(key, [])
        if not participant_rows:
            missing_firm_groups += 1
            continue
        firm_type = AGG_TO_FIRM[agg_type]
        if any(
            len(group) > 1
            for fk, group in firm_key_groups.items()
            if fk[0] == symbol and fk[1] == product and fk[2] == firm_type
        ):
            concentration_excluded_duplicate_symbols.add((symbol, product, agg_type))
            continue

        agg_volume = number(agg_group[0].get("totalWeeklyShareQuantity"))
        agg_trades = number(agg_group[0].get("totalWeeklyTradeCount"))
        firm_volume = _safe_sum(participant_rows, "totalWeeklyShareQuantity")
        firm_trades = _safe_sum(participant_rows, "totalWeeklyTradeCount")
        if None in (agg_volume, agg_trades, firm_volume, firm_trades):
            invalid_compare_groups += 1
            continue
        matched += 1
        dv = firm_volume - agg_volume
        dt = firm_trades - agg_trades
        volume_abs_diffs.append(abs(dv))
        trade_abs_diffs.append(abs(dt))
        if abs(dv) < 1e-9:
            exact_volume += 1
        if abs(dt) < 1e-9:
            exact_trades += 1
        if (abs(dv) >= 1e-9 or abs(dt) >= 1e-9) and len(mismatch_examples) < 20:
            mismatch_examples.append({
                "symbol": symbol, "product_type": product, "summary_type": agg_type,
                "aggregate_volume": agg_volume, "firm_sum_volume": firm_volume,
                "aggregate_trades": agg_trades, "firm_sum_trades": firm_trades,
            })

        pvol = defaultdict(float)
        for row in participant_rows:
            pid = participant_id(row)
            if pid:
                pvol[pid] += number(row.get("totalWeeklyShareQuantity")) or 0.0
        total = sum(pvol.values())
        if total > 0 and len(pvol) > 0:
            shares = [v / total for v in pvol.values()]
            concentration_hhi.append(sum(x * x for x in shares))
            concentration_top1.append(max(shares))
            concentration_symbol_count += 1

    firm_symbol_keys = set(firm_rows)
    aggregate_keys = set(aggregates)
    orphan_firm_groups = sorted(firm_symbol_keys - aggregate_keys)
    aggregate_symbols = {key[0] for key in aggregates}
    firm_symbols = {key[0] for key in firm_rows}

    return {
        "week": week,
        "tier": tier,
        "rows_total": len(rows),
        "summary_type_counts": dict(sorted(type_counts.items())),
        "aggregate_symbol_product_groups": len(aggregates),
        "firm_symbol_product_groups": len(firm_rows),
        "aggregate_unique_symbols": len(aggregate_symbols),
        "firm_unique_symbols": len(firm_symbols),
        "firm_rows_missing_symbol": missing_symbol_firm,
        "firm_rows_missing_participant_id": missing_participant_firm,
        "firm_rows_missing_participant_name": missing_name_firm,
        "invalid_or_negative_quantity_cells": invalid_quantity_rows,
        "duplicate_aggregate_groups": duplicate_aggregate_groups,
        "duplicate_firm_groups": duplicate_firm_groups,
        "firm_orphan_symbol_product_groups": len(orphan_firm_groups),
        "firm_orphan_examples": [
            {"symbol": x[0], "product_type": x[1], "aggregate_type": x[2]}
            for x in orphan_firm_groups[:20]
        ],
        "firm_to_aggregate_reconciliation": {
            "matched_symbol_product_groups": matched,
            "aggregate_groups_without_firm_rows": missing_firm_groups,
            "invalid_comparison_groups": invalid_compare_groups,
            "exact_volume_matches": exact_volume,
            "exact_trade_matches": exact_trades,
            "volume_match_pct": round(100 * exact_volume / matched, 2) if matched else None,
            "trade_match_pct": round(100 * exact_trades / matched, 2) if matched else None,
            "absolute_volume_difference": _percentiles(volume_abs_diffs),
            "absolute_trade_difference": _percentiles(trade_abs_diffs),
            "mismatch_examples": mismatch_examples,
        },
        "participant_concentration_diagnostic": {
            "symbol_groups": concentration_symbol_count,
            "excluded_duplicate_symbol_groups": len(concentration_excluded_duplicate_symbols),
            "hhi": _percentiles(concentration_hhi),
            "top_participant_volume_share": _percentiles(concentration_top1),
        },
        "publication_fields": {
            "initialPublishedDate_nonnull": len(initial_dates),
            "lastUpdateDate_nonnull": len(update_dates),
            "lastReportedDate_nonnull": len(reported_dates),
            "max_last_update_after_initial": (
                sum(1 for p, u in zip(initial_dates, update_dates) if u > p)
                if len(initial_dates) == len(update_dates) else None
            ),
        },
        "partition_errors": errors[:50],
        "partition_error_count": len(errors),
        "data_gate": "PASS_PARTITION_SCHEMA" if not errors and invalid_quantity_rows == 0 else "FAIL_OR_REVIEW",
        "alpha_test_authorized": False,
        "f80_changed": False,
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
    raise RuntimeError(f"Unexpected FINRA response type: {type(payload).__name__}")


def fetch_partition(session, week, tier):
    rows = []
    pages = []
    offset = 0
    expected_total = None
    while True:
        payload = {
            "fields": FIELDS,
            "compareFilters": [
                {"compareType": "EQUAL", "fieldName": "historicalWeek", "fieldValue": week},
                {"compareType": "EQUAL", "fieldName": "tierIdentifier", "fieldValue": tier},
            ],
            "limit": PAGE_SIZE,
            "offset": offset,
        }
        response = None
        for attempt in range(4):
            try:
                response = session.post(BASE, json=payload, timeout=(20, 120))
            except requests.RequestException:
                if attempt == 3:
                    raise
                time.sleep(min(3 * (2 ** attempt), 30))
                continue
            if response.status_code in {408, 429, 500, 502, 503, 504}:
                if attempt == 3:
                    response.raise_for_status()
                retry_after = response.headers.get("Retry-After")
                try:
                    delay = float(retry_after) if retry_after else 3 * (2 ** attempt)
                except (TypeError, ValueError):
                    delay = 3 * (2 ** attempt)
                time.sleep(max(0, min(delay, 60)))
                continue
            response.raise_for_status()
            break
        if response is None:
            raise RuntimeError("No FINRA response")
        page_rows = parse_rows(response.json())
        headers = {str(k).lower(): v for k, v in response.headers.items()}
        total_raw = headers.get("record-total")
        if total_raw is None:
            raise RuntimeError(f"Missing Record-Total for {week}/{tier} offset={offset}")
        total = int(total_raw)
        if expected_total is None:
            expected_total = total
        elif total != expected_total:
            raise RuntimeError(f"Record-Total changed for {week}/{tier}: {total} vs {expected_total}")
        page_count_raw = headers.get("total-records-on-page")
        page_count = int(page_count_raw) if page_count_raw is not None else len(page_rows)
        if page_count != len(page_rows):
            raise RuntimeError(f"Page count mismatch for {week}/{tier} offset={offset}")
        record_offset = headers.get("record-offset")
        if record_offset is not None and int(record_offset) != offset:
            raise RuntimeError(f"Record-Offset mismatch for {week}/{tier} offset={offset}")
        if not page_rows and total > offset:
            raise RuntimeError(f"Empty page before Record-Total for {week}/{tier} offset={offset}")
        rows.extend(page_rows)
        pages.append({
            "week": week, "tier": tier, "offset": offset,
            "rows": len(page_rows), "record_total": total,
            "request_id": headers.get("finra-api-request-id"),
            "sha256": hashlib.sha256(response.content).hexdigest(),
            "page_count_source": "header" if page_count_raw is not None else "body_length",
        })
        offset += page_count
        if offset >= total:
            break
        if offset > MAX_OFFSET:
            raise RuntimeError(f"Offset ceiling exceeded for {week}/{tier}")
    if expected_total is None or len(rows) != expected_total:
        raise RuntimeError(f"Incomplete partition {week}/{tier}: {len(rows)} != {expected_total}")
    return rows, pages


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="phase358_finra_firm_grain")
    args = parser.parse_args()
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update({
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "SmartMoneyResearch-Phase358/1.0",
    })
    token = os.getenv("FINRA_API_TOKEN", "").strip()
    if token:
        session.headers["Authorization"] = f"Bearer {token}"

    results = []
    all_pages = []
    errors = []
    total_rows = 0
    for week in WEEKS:
        for tier in TIERS:
            try:
                print(f"[Phase358] start {week}/{tier}", flush=True)
                rows, pages = fetch_partition(session, week, tier)
                total_rows += len(rows)
                all_pages.extend(pages)
                result = audit_rows(rows, week, tier)
                result["api_record_total"] = pages[0]["record_total"] if pages else 0
                result["api_records_retrieved"] = len(rows)
                result["api_record_total_match"] = result["api_record_total"] == len(rows)
                results.append(result)
                print(
                    f"[Phase358] complete {week}/{tier}: rows={len(rows)} "
                    f"aggregates={result['aggregate_symbol_product_groups']} "
                    f"firm_groups={result['firm_symbol_product_groups']} "
                    f"recon={result['firm_to_aggregate_reconciliation']['volume_match_pct']}%",
                    flush=True,
                )
            except Exception as exc:
                errors.append({"week": week, "tier": tier, "error": repr(exc)})
                results.append({
                    "week": week, "tier": tier, "data_gate": "FAIL_REQUEST",
                    "partition_errors": [repr(exc)], "alpha_test_authorized": False,
                    "f80_changed": False,
                })

    summary = {
        "phase": 358,
        "source": "FINRA OTCMarket weeklySummaryHistoric",
        "audit_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "sample_weeks": list(WEEKS),
        "tiers": list(TIERS),
        "requested_fields": FIELDS,
        "finra_api_token_present": bool(token),
        "partitions_expected": len(WEEKS) * len(TIERS),
        "partitions_completed": sum(1 for r in results if r.get("api_record_total_match") is True),
        "rows_total": total_rows,
        "page_count": len(all_pages),
        "partitions": results,
        "request_errors": errors,
        "schema_and_partition_gate": (
            "PASS" if len(results) == len(WEEKS) * len(TIERS)
            and not errors
            and all(r.get("data_gate") == "PASS_PARTITION_SCHEMA" for r in results)
            and all(r.get("api_record_total_match") is True for r in results)
            else "FAIL_OR_REVIEW"
        ),
        "firm_to_aggregate_reconciliation": "DIAGNOSTIC_ONLY",
        "participant_concentration": "DIAGNOSTIC_ONLY_NOT_SMART_MONEY",
        "pit_status": "FINAL_HISTORICAL_SNAPSHOT_ONLY; lastUpdateDate must not be backdated; interim vintages unavailable in this audit",
        "economic_interpretation": "Firm/ATS participant identifiers identify reporting intermediaries, not beneficial owners or trade direction.",
        "forward_returns_used": False,
        "alpha_test_authorized": False,
        "f80_changed": False,
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (out / "page_hashes.json").write_text(json.dumps(all_pages, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2), flush=True)
    print(
        "[Phase358] complete "
        f"schema_gate={summary['schema_and_partition_gate']} "
        f"rows={total_rows} pages={len(all_pages)}",
        flush=True,
    )


if __name__ == "__main__":
    main()

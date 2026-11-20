#!/usr/bin/env python3
"""Phase 521: one-week FINRA historical symbol-domain-filter feasibility probe.

Only a predeclared 10-symbol sample is queried. Raw rows and participant
identifiers remain in memory; the artifact contains aggregate counts and
manifest hashes only. This is a query-feasibility test, not an alpha test.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from collections import defaultdict
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

import requests

BASE = "https://api.finra.org"
DATA_URL = f"{BASE}/data/group/otcmarket/name/weeklySummaryHistoric"
WEEK = "2024-05-20"
TIER = "T1"
SAMPLE_SYMBOLS = (
    "AAPL", "AMZN", "AMD", "GOOGL", "JPM",
    "META", "MSFT", "NVDA", "TSLA", "XOM",
)
SUMMARY_TYPES = ("ATS_W_SMBL", "ATS_W_SMBL_FIRM")
FIELDS = (
    "weekStartDate", "initialPublishedDate", "lastUpdateDate",
    "issueSymbolIdentifier", "summaryTypeCode", "productTypeCode",
    "totalWeeklyShareQuantity", "totalWeeklyTradeCount",
    "MPID", "firmCRDNumber", "marketParticipantName",
)
ALLOWED_LAGS = {21, 22}
PAGE_LIMIT = 5000


class DomainFilterRejected(RuntimeError):
    def __init__(self, status_code: int):
        super().__init__(f"FINRA rejected domain-filter request with HTTP {status_code}")
        self.status_code = status_code


def manifest_hash(values) -> str:
    payload = "\n".join(sorted(str(x).strip().upper() for x in values))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_payload(week: str, symbols, offset: int = 0, limit: int = PAGE_LIMIT):
    normalized = sorted({str(x).strip().upper() for x in symbols if str(x).strip()})
    if not normalized:
        raise ValueError("At least one symbol is required")
    return {
        "compareFilters": [
            {"fieldName": "weekStartDate", "fieldValue": week, "compareType": "EQUAL"},
            {"fieldName": "tierIdentifier", "fieldValue": TIER, "compareType": "EQUAL"},
        ],
        "domainFilters": [
            {"fieldName": "issueSymbolIdentifier", "values": normalized},
            {"fieldName": "summaryTypeCode", "values": list(SUMMARY_TYPES)},
        ],
        "fields": list(FIELDS),
        "limit": int(limit),
        "offset": int(offset),
    }


def parse_rows(payload):
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
    raise RuntimeError("Unexpected FINRA response envelope")


def parse_int(value):
    if value is None or str(value).strip() == "":
        return None
    try:
        number = Decimal(str(value).replace(",", "").strip())
    except (InvalidOperation, ValueError):
        return None
    if not number.is_finite() or number < 0 or number != number.to_integral_value():
        return None
    return int(number)


def sum_field(rows, field):
    values = [parse_int(row.get(field)) for row in rows]
    return None if any(value is None for value in values) else sum(values)


def parse_date(value):
    if value is None or str(value).strip() == "":
        return None
    try:
        return date.fromisoformat(str(value).strip()[:10])
    except ValueError:
        return None


def participant_key(row):
    mpid = str(row.get("MPID") or "").strip().upper()
    crd = str(row.get("firmCRDNumber") or "").strip()
    return mpid or (crd if crd not in ("", "0") else "")


def analyze_symbol(rows, symbol: str, week: str):
    aggregate = [r for r in rows if str(r.get("summaryTypeCode", "")).strip().upper() == "ATS_W_SMBL"]
    firms = [r for r in rows if str(r.get("summaryTypeCode", "")).strip().upper() == "ATS_W_SMBL_FIRM"]
    if not aggregate or not firms:
        return {"bridge_pass": False, "revision_stable": False, "concentration_valid": False}

    product_types = [str(r.get("productTypeCode") or "").strip().upper() for r in aggregate]
    if any(not value for value in product_types) or len(set(product_types)) != len(product_types):
        bridge = False
    else:
        a_shares = sum_field(aggregate, "totalWeeklyShareQuantity")
        a_trades = sum_field(aggregate, "totalWeeklyTradeCount")
        f_shares = sum_field(firms, "totalWeeklyShareQuantity")
        f_trades = sum_field(firms, "totalWeeklyTradeCount")
        bridge = None not in (a_shares, a_trades, f_shares, f_trades) and (
            a_shares == f_shares and a_trades == f_trades
        )

    publication_dates = set()
    stable = True
    for row in aggregate + firms:
        week_date = parse_date(row.get("weekStartDate"))
        pub_date = parse_date(row.get("initialPublishedDate"))
        update_date = parse_date(row.get("lastUpdateDate"))
        if week_date is None or week_date.isoformat() != week or pub_date is None or update_date is None:
            stable = False
            continue
        publication_dates.add(pub_date)
        if (pub_date - week_date).days not in ALLOWED_LAGS or update_date != pub_date:
            stable = False
    stable = stable and len(publication_dates) == 1

    keys = []
    identity_valid = True
    has_de_minimis = False
    for row in firms:
        if "DE MINIMIS" in str(row.get("marketParticipantName") or "").upper():
            has_de_minimis = True
            identity_valid = False
        key = participant_key(row)
        shares = parse_int(row.get("totalWeeklyShareQuantity"))
        if not key or shares is None:
            identity_valid = False
        keys.append(key)

    participant_shares = defaultdict(int)
    for row in firms:
        key = participant_key(row)
        shares = parse_int(row.get("totalWeeklyShareQuantity"))
        if key and shares is not None:
            participant_shares[key] += shares
    concentration_valid = bool(
        bridge and stable and identity_valid and not has_de_minimis
        and len(keys) == len(set(keys))
        and sum(participant_shares.values()) == sum_field(aggregate, "totalWeeklyShareQuantity")
        and sum(participant_shares.values()) > 0
    )
    return {
        "bridge_pass": bool(bridge),
        "revision_stable": bool(stable),
        "concentration_valid": concentration_valid,
    }


def summarize_rows(rows, requested_symbols, week=WEEK, record_total=None):
    requested = {str(x).strip().upper() for x in requested_symbols}
    returned = {
        str(row.get("issueSymbolIdentifier") or "").strip().upper()
        for row in rows if str(row.get("issueSymbolIdentifier") or "").strip()
    }
    unexpected = returned - requested
    matched = returned & requested
    per_symbol = {
        symbol: analyze_symbol(
            [row for row in rows if str(row.get("issueSymbolIdentifier") or "").strip().upper() == symbol],
            symbol,
            week,
        )
        for symbol in matched
    }
    bridge_count = sum(x["bridge_pass"] for x in per_symbol.values())
    stable_count = sum(x["revision_stable"] for x in per_symbol.values())
    concentration_count = sum(x["concentration_valid"] for x in per_symbol.values())
    type_counts = defaultdict(int)
    for row in rows:
        typ = str(row.get("summaryTypeCode") or "").strip().upper()
        if typ in SUMMARY_TYPES:
            type_counts[typ] += 1
    filter_applied = bool(rows) and not unexpected
    all_requested = matched == requested
    return {
        "phase": 521,
        "probe_week": week,
        "dataset": "weeklySummaryHistoric",
        "tier": TIER,
        "requested_symbol_count": len(requested),
        "requested_symbol_manifest_sha256": manifest_hash(requested),
        "returned_symbol_count": len(returned),
        "matched_requested_symbol_count": len(matched),
        "matched_symbol_manifest_sha256": manifest_hash(matched),
        "missing_requested_symbol_count": len(requested - matched),
        "unexpected_symbol_count": len(unexpected),
        "domain_filter_applied": filter_applied,
        "all_requested_symbols_returned": all_requested,
        "record_total": record_total,
        "rows_returned": len(rows),
        "summary_type_row_counts": dict(type_counts),
        "symbols_with_both_types_and_exact_aggregate_bridge": bridge_count,
        "revision_stable_symbols": stable_count,
        "valid_symbol_concentration_rows": concentration_count,
        "probe_pass": bool(
            filter_applied and all_requested and bridge_count == len(requested)
            and stable_count == len(requested) and concentration_count == len(requested)
        ),
        "raw_rows_retained": False,
        "raw_identifiers_retained": False,
        "symbol_strings_retained": False,
        "per_symbol_metrics_retained": False,
        "research_observation_eligible_count": 0,
        "signal_eligible_count": 0,
        "returns_or_alpha_test_authorized": False,
    }


def fetch_page(session, week, symbols, offset):
    response = session.post(
        DATA_URL,
        json=build_payload(week, symbols, offset=offset),
        timeout=(20, 90),
    )
    if response.status_code == 400:
        raise DomainFilterRejected(400)
    if response.status_code in {401, 403}:
        raise RuntimeError(f"FINRA authorization/access failure: HTTP {response.status_code}")
    response.raise_for_status()
    rows = parse_rows(response.json())
    headers = {str(k).lower(): v for k, v in response.headers.items()}
    total_raw = headers.get("record-total")
    if total_raw is None:
        raise RuntimeError("Missing FINRA Record-Total header")
    total = int(total_raw)
    returned_offset = headers.get("record-offset")
    if returned_offset is not None and int(returned_offset) != offset:
        raise RuntimeError("FINRA Record-Offset mismatch")
    if len(rows) > PAGE_LIMIT:
        raise RuntimeError("FINRA exceeded requested page limit")
    return rows, total


def run_probe(symbols=SAMPLE_SYMBOLS, week=WEEK):
    session = requests.Session()
    session.headers.update({"Accept": "application/json", "Content-Type": "application/json"})
    token = os.environ.get("FINRA_API_TOKEN", "").strip()
    if token:
        session.headers["Authorization"] = f"Bearer {token}"

    rows = []
    expected = None
    offset = 0
    try:
        while True:
            batch, total = fetch_page(session, week, symbols, offset)
            if expected is None:
                expected = total
            elif expected != total:
                raise RuntimeError("FINRA Record-Total changed during pagination")
            rows.extend(batch)
            if len(rows) == expected:
                break
            if len(rows) > expected or not batch:
                raise RuntimeError("FINRA pagination made no progress")
            offset += len(batch)
            if offset > 500000:
                raise RuntimeError("FINRA offset exceeded maximum")
            time.sleep(0.15)
        result = summarize_rows(rows, symbols, week, expected)
        result["http_status"] = 200
        result["probe_status"] = (
            "DOMAIN_FILTER_SUPPORTED_EXACT_SAMPLE_PASS"
            if result["probe_pass"]
            else "DOMAIN_FILTER_RETURNED_DATA_BUT_COVERAGE_OR_BRIDGE_INCOMPLETE"
        )
        return result
    except DomainFilterRejected as exc:
        return {
            "phase": 521,
            "probe_week": week,
            "dataset": "weeklySummaryHistoric",
            "requested_symbol_count": len(symbols),
            "requested_symbol_manifest_sha256": manifest_hash(symbols),
            "http_status": exc.status_code,
            "probe_status": "DOMAIN_FILTER_REJECTED_BY_HISTORICAL_ENDPOINT",
            "domain_filter_supported": False,
            "raw_rows_retained": False,
            "raw_identifiers_retained": False,
            "symbol_strings_retained": False,
            "per_symbol_metrics_retained": False,
            "research_observation_eligible_count": 0,
            "signal_eligible_count": 0,
            "returns_or_alpha_test_authorized": False,
        }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="phase521_output")
    args = parser.parse_args()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    result = run_probe()
    result["audit_timestamp_utc"] = __import__("datetime").datetime.now(
        __import__("datetime").timezone.utc
    ).isoformat()
    (output / "summary.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()

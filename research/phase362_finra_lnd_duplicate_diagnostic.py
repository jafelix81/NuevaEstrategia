#!/usr/bin/env python3
"""Phase 362: inspect the known FINRA LND duplicate aggregate groups.

FINRA weeklySummaryHistoric only permits week/tier partition filters. The
script therefore retrieves one complete partition, then isolates LND locally.
It preserves the conflicting aggregate rows and compares their combined
arithmetic with firm-grain rows without authorizing an aggregation or join.

Research-only: no returns, alpha, holdout, or F80 changes.
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

from research.phase359_finra_product_key_diagnostic import BASE, parse_rows

WEEK = "2025-01-06"
TIER = "T2"
SYMBOL = "LND"
PAGE_SIZE = 5000
MAX_OFFSET = 500000
FIELDS = [
    "issueSymbolIdentifier", "issueName", "firmCRDNumber", "MPID",
    "marketParticipantName", "tierIdentifier", "tierDescription",
    "summaryStartDate", "totalWeeklyTradeCount", "totalWeeklyShareQuantity",
    "productTypeCode", "summaryTypeCode", "weekStartDate",
    "lastUpdateDate", "initialPublishedDate", "lastReportedDate",
    "totalNotionalSum",
]
AGG_TO_FIRM = {
    "ATS_W_SMBL": "ATS_W_SMBL_FIRM",
    "OTC_W_SMBL": "OTC_W_SMBL_FIRM",
}


def norm(value):
    return str(value or "").strip().upper()


def as_nonnegative_int(value):
    if value is None or str(value).strip() == "":
        return None
    try:
        d = Decimal(str(value).replace(",", "").strip())
    except (InvalidOperation, ValueError):
        return None
    if not d.is_finite() or d < 0 or d != d.to_integral_value():
        return None
    return int(d)


def participant_identity(row, aggregate_type):
    mpid = norm(row.get("MPID"))
    crd = norm(row.get("firmCRDNumber"))
    name = norm(row.get("marketParticipantName"))
    identity = (mpid or crd) if aggregate_type == "ATS_W_SMBL" else (crd or mpid)
    if identity:
        return ("MPID:" if identity == mpid and mpid else "CRD:") + identity
    if "DE MINIMIS" in name:
        return "DE_MINIMIS"
    return "NAME:" + name if name else ""


def identity_hash(identity):
    return hashlib.sha256(identity.encode("utf-8")).hexdigest() if identity else None


def safe_aggregate_row(row):
    return {
        key: row.get(key)
        for key in (
            "issueSymbolIdentifier", "issueName", "weekStartDate",
            "tierIdentifier", "summaryTypeCode", "productTypeCode",
            "summaryStartDate", "totalWeeklyShareQuantity",
            "totalWeeklyTradeCount", "totalNotionalSum",
            "initialPublishedDate", "lastUpdateDate", "lastReportedDate",
        )
    }


def summarize_family(rows, aggregate_type):
    firm_type = AGG_TO_FIRM[aggregate_type]
    aggregates = [
        r for r in rows
        if norm(r.get("summaryTypeCode")) == aggregate_type
        and norm(r.get("issueSymbolIdentifier")) == SYMBOL
    ]
    firms = [
        r for r in rows
        if norm(r.get("summaryTypeCode")) == firm_type
        and norm(r.get("issueSymbolIdentifier")) == SYMBOL
    ]

    aggregate_values = []
    for row in aggregates:
        aggregate_values.append({
            "shares": as_nonnegative_int(row.get("totalWeeklyShareQuantity")),
            "trades": as_nonnegative_int(row.get("totalWeeklyTradeCount")),
        })

    firm_values = []
    identity_counts = Counter()
    missing_identity = 0
    de_minimis_rows = 0
    for row in firms:
        identity = participant_identity(row, aggregate_type)
        if identity:
            identity_counts[identity] += 1
        else:
            missing_identity += 1
        is_de_minimis = identity == "DE_MINIMIS"
        de_minimis_rows += int(is_de_minimis)
        firm_values.append({
            "identity_hash": identity_hash(identity),
            "shares": as_nonnegative_int(row.get("totalWeeklyShareQuantity")),
            "trades": as_nonnegative_int(row.get("totalWeeklyTradeCount")),
            "de_minimis": is_de_minimis,
        })

    aggregate_shares = [x["shares"] for x in aggregate_values]
    aggregate_trades = [x["trades"] for x in aggregate_values]
    firm_shares = [x["shares"] for x in firm_values]
    firm_trades = [x["trades"] for x in firm_values]
    valid_aggregate = all(x is not None for x in aggregate_shares + aggregate_trades)
    valid_firm = all(x is not None for x in firm_shares + firm_trades)

    sum_aggregate_shares = sum(aggregate_shares) if valid_aggregate else None
    sum_aggregate_trades = sum(aggregate_trades) if valid_aggregate else None
    sum_firm_shares = sum(firm_shares) if valid_firm else None
    sum_firm_trades = sum(firm_trades) if valid_firm else None

    aggregate_fingerprints = [
        hashlib.sha256(
            json.dumps(safe_aggregate_row(r), sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        for r in aggregates
    ]
    duplicate_fingerprints = len(aggregate_fingerprints) - len(set(aggregate_fingerprints))
    duplicate_participant_keys = sum(1 for n in identity_counts.values() if n > 1)

    if not aggregates:
        diagnosis = "NO_SYMBOL_AGGREGATE"
    elif len(aggregates) == 1:
        diagnosis = "SINGLE_AGGREGATE_ROW"
    elif duplicate_fingerprints:
        diagnosis = "EXACT_DUPLICATE_AGGREGATE_ROWS"
    else:
        diagnosis = "MULTIPLE_DISTINCT_AGGREGATE_ROWS_SAME_SYMBOL_PRODUCT"

    sum_matches = (
        valid_aggregate and valid_firm
        and sum_aggregate_shares == sum_firm_shares
        and sum_aggregate_trades == sum_firm_trades
    )
    return {
        "aggregate_type": aggregate_type,
        "firm_type": firm_type,
        "aggregate_row_count": len(aggregates),
        "firm_row_count": len(firms),
        "aggregate_rows": [safe_aggregate_row(r) for r in aggregates],
        "aggregate_row_fingerprints": aggregate_fingerprints,
        "aggregate_exact_duplicate_count": duplicate_fingerprints,
        "aggregate_diagnosis": diagnosis,
        "aggregate_values": aggregate_values,
        "firm_participant_count": len(identity_counts),
        "firm_duplicate_participant_key_count": duplicate_participant_keys,
        "firm_rows_missing_identity": missing_identity,
        "de_minimis_rows": de_minimis_rows,
        "firm_rows_anonymized": firm_values,
        "sum_aggregate_shares_diagnostic_only": sum_aggregate_shares,
        "sum_aggregate_trades_diagnostic_only": sum_aggregate_trades,
        "sum_firm_shares": sum_firm_shares,
        "sum_firm_trades": sum_firm_trades,
        "combined_aggregate_matches_firm_arithmetically": bool(sum_matches),
        "arithmetic_interpretation": (
            "A match does not establish that duplicate aggregate rows are additive or share the same economic grain. "
            "No aggregation, deduplication, or feature use is authorized."
        ),
        "data_gate": (
            "PASS" if len(aggregates) == 1 and sum_matches
            and duplicate_participant_keys == 0 and missing_identity == 0
            else "FAIL_OR_REVIEW"
        ),
    }


def fetch_partition(session):
    rows, pages = [], []
    offset, expected_total = 0, None
    while True:
        payload = {
            "fields": FIELDS,
            "compareFilters": [
                {"compareType": "EQUAL", "fieldName": "historicalWeek", "fieldValue": WEEK},
                {"compareType": "EQUAL", "fieldName": "tierIdentifier", "fieldValue": TIER},
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
            raise RuntimeError(f"Missing Record-Total at offset={offset}")
        total = int(total_raw)
        if expected_total is None:
            expected_total = total
        elif total != expected_total:
            raise RuntimeError(f"Record-Total changed: {total} vs {expected_total}")
        page_count_raw = headers.get("total-records-on-page")
        page_count = int(page_count_raw) if page_count_raw is not None else len(page_rows)
        if page_count != len(page_rows):
            raise RuntimeError(f"Page count mismatch at offset={offset}")
        record_offset = headers.get("record-offset")
        if record_offset is not None and int(record_offset) != offset:
            raise RuntimeError(f"Record-Offset mismatch at offset={offset}")
        if not page_rows and total > offset:
            raise RuntimeError(f"Empty page before Record-Total at offset={offset}")

        rows.extend(page_rows)
        pages.append({
            "offset": offset,
            "rows": len(page_rows),
            "record_total": total,
            "request_id": headers.get("finra-api-request-id"),
            "sha256": hashlib.sha256(response.content).hexdigest(),
        })
        offset += page_count
        if offset >= total:
            break
        if offset > MAX_OFFSET:
            raise RuntimeError("Offset ceiling exceeded")

    if expected_total is None or len(rows) != expected_total:
        raise RuntimeError(f"Incomplete partition: {len(rows)} != {expected_total}")
    return rows, pages, expected_total


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="phase362_finra_lnd_diagnostic")
    args = parser.parse_args()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers.update({
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "SmartMoneyResearch-Phase362/1.0",
    })
    token = os.getenv("FINRA_API_TOKEN", "").strip()
    if token:
        session.headers["Authorization"] = f"Bearer {token}"

    rows, pages, expected_total = fetch_partition(session)
    lnd_rows = [
        r for r in rows
        if norm(r.get("issueSymbolIdentifier")) == SYMBOL
    ]
    families = {
        aggregate_type: summarize_family(lnd_rows, aggregate_type)
        for aggregate_type in AGG_TO_FIRM
    }
    summary = {
        "phase": 362,
        "source": "FINRA OTCMarket weeklySummaryHistoric",
        "audit_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "week": WEEK,
        "tier": TIER,
        "partition_rows_retrieved": len(rows),
        "api_record_total": expected_total,
        "api_record_total_match": len(rows) == expected_total,
        "page_count": len(pages),
        "lnd_rows_total": len(lnd_rows),
        "lnd_summary_type_counts": dict(sorted(Counter(norm(r.get("summaryTypeCode")) for r in lnd_rows).items())),
        "families": families,
        "retrieval_gate": "PASS" if len(rows) == expected_total else "FAIL_OR_REVIEW",
        "overall_data_gate": (
            "PASS" if all(x["data_gate"] == "PASS" for x in families.values())
            else "FAIL_OR_REVIEW"
        ),
        "pit_status": "FINAL_HISTORICAL_SNAPSHOT_ONLY; no interim vintages",
        "forward_returns_used": False,
        "alpha_test_authorized": False,
        "holdout_used": False,
        "f80_changed": False,
    }
    (output / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (output / "page_hashes.json").write_text(json.dumps(pages, indent=2), encoding="utf-8")
    (output / "lnd_rows_anonymized.json").write_text(
        json.dumps({
            "aggregate_rows": {
                k: v["aggregate_rows"] for k, v in families.items()
            },
            "firm_rows": {
                k: v["firm_rows_anonymized"] for k, v in families.items()
            },
        }, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2), flush=True)
    print(
        f"[Phase362] complete retrieval={summary['retrieval_gate']} "
        f"data={summary['overall_data_gate']} LND_rows={len(lnd_rows)}",
        flush=True,
    )


if __name__ == "__main__":
    main()

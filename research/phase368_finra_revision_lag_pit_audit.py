#!/usr/bin/env python3
"""Phase 368: quantify FINRA weekly-summary date-field gaps.

Source/PIT-feasibility audit only. Downloads five complete weeklySummaryHistoric
partitions and emits anonymized date-field distributions. Raw rows, symbols,
MPIDs, CRDs and firm names are never retained.

Date-field gaps are not publication timestamps. lastUpdateDate and
lastReportedDate must not be treated as proof of when a revised public value
first became available.
"""
from __future__ import annotations

import argparse
import json
import os
import time
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from math import ceil
from pathlib import Path

import requests

BASE_URL = "https://api.finra.org/data/group/otcmarket/name"
DATASET = "weeklySummaryHistoric"
PAGE_LIMIT = 5000
MAX_OFFSET = 500000
PARTITIONS = (
    ("2022-01-03", "T1"),
    ("2025-01-06", "T1"),
    ("2025-10-20", "T1"),
    ("2025-10-20", "OTCE"),
    ("2025-11-10", "T1"),
)
DATE_FIELDS = ("weekStartDate", "initialPublishedDate", "lastUpdateDate", "lastReportedDate")
LAG_PAIRS = {
    "initialPublishedDate_minus_weekStartDate": ("weekStartDate", "initialPublishedDate"),
    "lastUpdateDate_minus_initialPublishedDate": ("initialPublishedDate", "lastUpdateDate"),
    "lastReportedDate_minus_initialPublishedDate": ("initialPublishedDate", "lastReportedDate"),
    "lastUpdateDate_minus_weekStartDate": ("weekStartDate", "lastUpdateDate"),
    "lastReportedDate_minus_weekStartDate": ("weekStartDate", "lastReportedDate"),
    "lastUpdateDate_minus_lastReportedDate": ("lastReportedDate", "lastUpdateDate"),
}
THRESHOLDS = (1, 7, 30, 90, 180, 365, 730)


def build_query(dataset: str, week: str, tier: str, limit: int, offset: int) -> dict:
    if dataset != DATASET:
        raise ValueError("Phase 368 is restricted to weeklySummaryHistoric")
    return {
        "compareFilters": [
            {"fieldName": "historicalWeek", "fieldValue": week, "compareType": "EQUAL"},
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


def parse_date(value) -> date | None:
    if value is None or str(value).strip() == "":
        return None
    raw = str(value).strip()
    try:
        return date.fromisoformat(raw[:10])
    except ValueError:
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00")).date()
        except ValueError:
            return None


def _pct(count: int, denominator: int) -> float | None:
    return round(100.0 * count / denominator, 4) if denominator else None


def _nearest_rank(values: list[int], q: float) -> int | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, ceil(q * len(ordered)) - 1))
    return ordered[index]


class DateAccumulator:
    def __init__(self):
        self.rows = 0
        self.missing = 0
        self.invalid = 0
        self.values = Counter()

    def add(self, raw):
        self.rows += 1
        if raw is None or str(raw).strip() == "":
            self.missing += 1
            return
        parsed = parse_date(raw)
        if parsed is None:
            self.invalid += 1
            return
        self.values[parsed.isoformat()] += 1

    def summary(self) -> dict:
        keys = sorted(self.values)
        return {
            "rows": self.rows,
            "missing": self.missing,
            "invalid": self.invalid,
            "distinct_dates": len(self.values),
            "minimum_date": keys[0] if keys else None,
            "maximum_date": keys[-1] if keys else None,
            "most_common_dates": [
                {"date": day, "rows": count}
                for day, count in self.values.most_common(8)
            ],
        }


class LagAccumulator:
    def __init__(self):
        self.rows = 0
        self.missing_base = 0
        self.missing_target = 0
        self.invalid_base = 0
        self.invalid_target = 0
        self.values: list[int] = []

    def add(self, base_raw, target_raw):
        self.rows += 1
        base_missing = base_raw is None or str(base_raw).strip() == ""
        target_missing = target_raw is None or str(target_raw).strip() == ""
        if base_missing:
            self.missing_base += 1
        if target_missing:
            self.missing_target += 1
        if base_missing or target_missing:
            return
        base = parse_date(base_raw)
        target = parse_date(target_raw)
        if base is None:
            self.invalid_base += 1
        if target is None:
            self.invalid_target += 1
        if base is None or target is None:
            return
        self.values.append((target - base).days)

    def summary(self) -> dict:
        values = self.values
        positive = sum(value > 0 for value in values)
        zero = sum(value == 0 for value in values)
        negative = sum(value < 0 for value in values)
        return {
            "rows": self.rows,
            "comparable_rows": len(values),
            "missing_base": self.missing_base,
            "missing_target": self.missing_target,
            "invalid_base": self.invalid_base,
            "invalid_target": self.invalid_target,
            "positive_gap_rows": positive,
            "positive_gap_pct_of_comparable": _pct(positive, len(values)),
            "zero_gap_rows": zero,
            "negative_gap_rows": negative,
            "minimum_days": min(values) if values else None,
            "p50_days_nearest_rank": _nearest_rank(values, 0.50),
            "p90_days_nearest_rank": _nearest_rank(values, 0.90),
            "p95_days_nearest_rank": _nearest_rank(values, 0.95),
            "p99_days_nearest_rank": _nearest_rank(values, 0.99),
            "maximum_days": max(values) if values else None,
            "threshold_counts": {
                f"gte_{threshold}_days": sum(value >= threshold for value in values)
                for threshold in THRESHOLDS
            },
        }


def analyze_rows(rows: list[dict], week: str, tier: str) -> dict:
    summary_types = Counter()
    symbols = set()
    participant_id_rows = 0
    de_minimis_rows = 0
    date_accumulators = {field: DateAccumulator() for field in DATE_FIELDS}
    lag_all = {name: LagAccumulator() for name in LAG_PAIRS}
    lag_by_type = {name: defaultdict(LagAccumulator) for name in LAG_PAIRS}

    for row in rows:
        summary_type = str(row.get("summaryTypeCode") or "__MISSING__")
        summary_types[summary_type] += 1
        symbol = str(row.get("issueSymbolIdentifier") or "").strip()
        if symbol:
            symbols.add(symbol)
        mpid = str(row.get("MPID") or "").strip()
        crd = str(row.get("firmCRDNumber") or "").strip()
        if mpid or (crd and crd != "0"):
            participant_id_rows += 1
        if str(row.get("marketParticipantName") or "").strip().lower() == "de minimis firms":
            de_minimis_rows += 1

        for field, accumulator in date_accumulators.items():
            accumulator.add(row.get(field))

        for metric, (base_field, target_field) in LAG_PAIRS.items():
            base_raw = row.get(base_field)
            target_raw = row.get(target_field)
            lag_all[metric].add(base_raw, target_raw)
            lag_by_type[metric][summary_type].add(base_raw, target_raw)

    return {
        "week": week,
        "tier": tier,
        "rows_retrieved": len(rows),
        "unique_symbols_count_only": len(symbols),
        "participant_id_rows": participant_id_rows,
        "de_minimis_rows": de_minimis_rows,
        "summary_type_counts": dict(sorted(summary_types.items())),
        "date_field_distributions": {
            field: accumulator.summary()
            for field, accumulator in date_accumulators.items()
        },
        "date_gap_distributions": {
            metric: {
                "all_rows": lag_all[metric].summary(),
                "by_summary_type": {
                    summary_type: accumulator.summary()
                    for summary_type, accumulator in sorted(lag_by_type[metric].items())
                },
            }
            for metric in LAG_PAIRS
        },
        "raw_rows_retained": False,
        "raw_identifiers_retained": False,
    }


def request_page(session: requests.Session, week: str, tier: str, offset: int):
    url = f"{BASE_URL}/{DATASET}"
    body = build_query(DATASET, week, tier, PAGE_LIMIT, offset)
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
                raise RuntimeError("Missing Record-Total")
            if "record-offset" in headers and int(headers["record-offset"]) != offset:
                raise RuntimeError("Record-Offset mismatch")
            page_total = int(headers.get("total-records-on-page", len(rows)))
            if page_total != len(rows):
                raise RuntimeError("Total-Records-On-Page mismatch")
            if len(rows) > PAGE_LIMIT:
                raise RuntimeError("Page exceeded requested limit")
            return rows, int(headers["record-total"])
        except (requests.RequestException, ValueError) as exc:
            if attempt == 3:
                raise RuntimeError(f"FINRA request failed ({type(exc).__name__})") from exc
            time.sleep(min(2 ** (attempt + 1), 20))
    raise RuntimeError("FINRA request retries exhausted")


def fetch_partition(session: requests.Session, week: str, tier: str) -> dict:
    rows = []
    offset = 0
    expected_total = None
    pages = 0
    while True:
        page_rows, record_total = request_page(session, week, tier, offset)
        if expected_total is None:
            expected_total = record_total
        elif record_total != expected_total:
            raise RuntimeError("Record-Total changed during pagination")
        pages += 1
        rows.extend(page_rows)
        print(
            f"[Phase368] week={week} tier={tier} offset={offset} "
            f"page_rows={len(page_rows)} record_total={record_total}",
            flush=True,
        )
        if len(rows) == expected_total:
            break
        if len(rows) > expected_total:
            raise RuntimeError("Retrieved rows exceeded Record-Total")
        if not page_rows:
            raise RuntimeError("Pagination made no progress")
        offset += len(page_rows)
        if offset > MAX_OFFSET:
            raise RuntimeError("Offset exceeded FINRA maximum")
        time.sleep(0.20)

    result = analyze_rows(rows, week, tier)
    result.update({
        "dataset": DATASET,
        "record_total": expected_total,
        "pages_retrieved": pages,
        "retrieval_complete": len(rows) == expected_total,
    })
    del rows
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="phase368_finra_revision_lag_pit_audit")
    args = parser.parse_args()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers.update({
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Data-API-Version": "1",
        "User-Agent": "SmartMoneyResearch-Phase368/1.0",
    })
    token = os.getenv("FINRA_API_TOKEN", "").strip()
    if token:
        session.headers["Authorization"] = f"Bearer {token}"

    partitions = []
    errors = []
    for week, tier in PARTITIONS:
        try:
            partitions.append(fetch_partition(session, week, tier))
        except Exception as exc:
            errors.append({
                "week": week,
                "tier": tier,
                "error_type": type(exc).__name__,
                "error": str(exc)[:240],
            })

    all_complete = (
        len(partitions) == len(PARTITIONS)
        and not errors
        and all(item.get("retrieval_complete") for item in partitions)
    )
    summary = {
        "phase": 368,
        "source": "FINRA OTCMarket weeklySummaryHistoric",
        "audit_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "planned_partitions": [
            {"week": week, "tier": tier} for week, tier in PARTITIONS
        ],
        "partitions": partitions,
        "errors": errors,
        "all_partitions_complete": all_complete,
        "field_semantics": {
            "initialPublishedDate": "FINRA first-publication date field; date only in the sampled schema",
            "lastUpdateDate": "FINRA latest-update date field; not an exact public release timestamp",
            "lastReportedDate": "FINRA last-contributing-firm-report date field; not a public release timestamp",
        },
        "pit_availability_established": False,
        "revision_vintage_history_reconstructed": False,
        "forward_returns_used": False,
        "alpha_test_authorized": False,
        "holdout_used": False,
        "f80_changed": False,
        "raw_rows_retained": False,
        "raw_identifiers_retained": False,
        "research_disposition": (
            "DATE_FIELD_LAGS_MEASURED_PIT_NOT_ESTABLISHED"
            if all_complete else "INCOMPLETE_RETRIEVAL"
        ),
    }
    (output / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({
        "phase": 368,
        "all_partitions_complete": all_complete,
        "partition_rows": [
            {"week": p["week"], "tier": p["tier"], "rows": p["rows_retrieved"]}
            for p in partitions
        ],
        "errors": errors,
        "pit_availability_established": False,
        "alpha_test_authorized": False,
    }, indent=2), flush=True)
    if not all_complete:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

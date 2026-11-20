#!/usr/bin/env python3
"""Phase 518: extend FINRA T1 ATS concentration history with the live 12-month dataset.

Only aggregate, revision-stable, symbol-week concentration statistics are retained.
MPIDs, CRDs, names, tickers and raw FINRA rows never leave memory. The feature is
reporting-participant concentration, not beneficial-owner or institutional identity.
No returns, alpha, backtest, OOS, bootstrap, LOO or holdout are used here.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import statistics
import time
from bisect import bisect_left
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas_market_calendars as mcal
import requests

BASE = "https://api.finra.org"
GROUP = "otcmarket"
DATASET = "weeklySummary"
DATA_URL = f"{BASE}/data/group/{GROUP}/name/{DATASET}"
META_URL = f"{BASE}/metadata/group/{GROUP}/name/{DATASET}"
PARTITIONS_URL = f"{BASE}/partitions/group/{GROUP}/name/{DATASET}"
TIER = "T1"
PAGE_LIMIT = 5000
MAX_OFFSET = 500000
EXPECTED_FIELDS = ("weekStartDate", "tierIdentifier")
SYMBOL_TYPES = {"ATS_W_SMBL", "ATS_W_SMBL_FIRM"}
ALLOWED_LAGS = {21, 22}
COVERAGE_FLOOR = 90.0
LOOKBACK = 52
MIN_HISTORY_VALID = 48
HIGH_RANK = 0.80
MIN_TRAIN = 52
MIN_EVAL = 150
MIN_HIGH = 30
MIN_NONHIGH = 100


def request_json(session: requests.Session, url: str):
    last = None
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
            return response.json()
        except (requests.RequestException, ValueError) as exc:
            last = exc
            if attempt == 3:
                raise
            time.sleep(min(3 * (2 ** attempt), 30))
    raise RuntimeError(f"FINRA GET failed: {last}")


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
    raise RuntimeError("Unexpected FINRA data response envelope")


def parse_partitions(payload, fields=EXPECTED_FIELDS):
    declared = tuple(payload.get("partitionFields") or ())
    if declared and declared != tuple(fields):
        raise RuntimeError(f"Partition fields mismatch: {declared}")
    records = []
    available = payload.get("availablePartitions") or payload.get("partitions") or []
    for item in available:
        if isinstance(item, dict):
            raw = item.get("partitions")
            if raw is None:
                candidates = [item]
            elif isinstance(raw, list) and raw and isinstance(raw[0], (list, tuple, dict)):
                candidates = raw
            else:
                candidates = [raw]
        else:
            candidates = [item]
        for candidate in candidates:
            if isinstance(candidate, dict):
                row = dict(candidate)
            elif isinstance(candidate, (list, tuple)) and len(candidate) == len(fields):
                row = dict(zip(fields, candidate))
            else:
                continue
            if isinstance(item, dict):
                for key in fields:
                    if key not in row and key in item:
                        row[key] = item[key]
            if row.get("weekStartDate") is not None and row.get("tierIdentifier") is not None:
                records.append({
                    "weekStartDate": str(row["weekStartDate"])[:10],
                    "tierIdentifier": str(row["tierIdentifier"]).strip().upper(),
                })
    unique = sorted({(x["weekStartDate"], x["tierIdentifier"]) for x in records})
    return records, unique


def request_page(session, week, offset):
    body = {
        "compareFilters": [
            {"fieldName": "weekStartDate", "fieldValue": week, "compareType": "EQUAL"},
            {"fieldName": "tierIdentifier", "fieldValue": TIER, "compareType": "EQUAL"},
        ],
        "limit": PAGE_LIMIT,
        "offset": offset,
    }
    last = None
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
            total_raw = headers.get("record-total")
            if total_raw is None:
                raise RuntimeError("Missing FINRA Record-Total header")
            total = int(total_raw)
            returned_offset = headers.get("record-offset")
            if returned_offset is not None and int(returned_offset) != offset:
                raise RuntimeError("FINRA Record-Offset mismatch")
            if len(rows) > PAGE_LIMIT:
                raise RuntimeError("FINRA page exceeded requested limit")
            return rows, total
        except (requests.RequestException, ValueError) as exc:
            last = exc
            if attempt == 3:
                raise
            time.sleep(min(2 ** (attempt + 1), 30))
    raise RuntimeError(f"FINRA POST failed: {last}")


def fetch_week(session, week):
    rows, expected, offset, pages = [], None, 0, 0
    while True:
        batch, total = request_page(session, week, offset)
        if expected is None:
            expected = total
        elif total != expected:
            raise RuntimeError("FINRA Record-Total changed during pagination")
        pages += 1
        rows.extend(batch)
        if len(rows) == expected:
            break
        if len(rows) > expected or not batch:
            raise RuntimeError("FINRA pagination mismatch or no progress")
        offset += len(batch)
        if offset > MAX_OFFSET:
            raise RuntimeError("FINRA offset exceeded maximum")
        time.sleep(0.15)
    return rows, expected, pages


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
        number = Decimal(str(value).replace(",", "").strip())
    except (InvalidOperation, ValueError):
        return None
    if not number.is_finite() or number < 0 or number != number.to_integral_value():
        return None
    return int(number)


def sum_field(rows, field):
    values = [parse_int(row.get(field)) for row in rows]
    return None if any(value is None for value in values) else sum(values)


def participant_key(row):
    mpid = norm(row.get("MPID"))
    crd = norm(row.get("firmCRDNumber"))
    return mpid or (crd if crd != "0" else "")


def percentile(values, p):
    ordered = sorted(values)
    if not ordered:
        return None
    index = max(0, min(len(ordered) - 1, int((len(ordered) * p + 0.999999999)) - 1))
    return ordered[index]


def describe(values):
    if not values:
        return {"n": 0, "mean": None, "median": None, "p90": None}
    return {
        "n": len(values),
        "mean": round(statistics.mean(values), 8),
        "median": round(statistics.median(values), 8),
        "p90": round(percentile(values, 0.90), 8),
    }


def analyze_week(rows, week, record_total, pages):
    aggregate, firms = defaultdict(list), defaultdict(list)
    symbol_rows = []
    week_publication_dates = set()
    missing_invalid_dates = 0
    for row in rows:
        typ = norm(row.get("summaryTypeCode"))
        if typ not in SYMBOL_TYPES:
            continue
        symbol = norm(row.get("issueSymbolIdentifier"))
        if not symbol:
            continue
        symbol_rows.append(row)
        (aggregate if typ == "ATS_W_SMBL" else firms)[symbol].append(row)
        week_date = parse_date(row.get("weekStartDate"))
        pub_date = parse_date(row.get("initialPublishedDate"))
        update_date = parse_date(row.get("lastUpdateDate"))
        if week_date is None or week_date.isoformat() != week or pub_date is None or update_date is None:
            missing_invalid_dates += 1
        else:
            week_publication_dates.add(pub_date)

    stable_symbols = revised_symbols = bridge_mapped = 0
    bridge_missing = bridge_ambiguous = bridge_invalid = bridge_mismatch = 0
    mapped_shares = stable_shares = stable_concentration_symbols = 0
    stable_participant_keys = set()
    concentration = []

    for symbol in set(aggregate) | set(firms):
        ar, fr = aggregate.get(symbol, []), firms.get(symbol, [])
        group = ar + fr
        publication_dates = set()
        dates_valid = revision_stable = schedule_ok = True
        positive_revision = False
        for row in group:
            week_date = parse_date(row.get("weekStartDate"))
            pub_date = parse_date(row.get("initialPublishedDate"))
            update_date = parse_date(row.get("lastUpdateDate"))
            if week_date is None or week_date.isoformat() != week or pub_date is None or update_date is None:
                dates_valid = revision_stable = schedule_ok = False
                continue
            publication_dates.add(pub_date)
            lag = (pub_date - week_date).days
            gap = (update_date - pub_date).days
            if lag not in ALLOWED_LAGS:
                schedule_ok = False
            if gap != 0:
                revision_stable = False
                positive_revision = positive_revision or gap > 0
        same_publication = len(publication_dates) == 1
        stable_date_group = bool(group) and dates_valid and revision_stable and schedule_ok and same_publication
        if stable_date_group:
            stable_symbols += 1
        if positive_revision:
            revised_symbols += 1

        if not ar or not fr:
            bridge_missing += 1
            continue
        product_types = [norm(row.get("productTypeCode")) for row in ar]
        if any(not item for item in product_types) or len(set(product_types)) != len(product_types):
            bridge_ambiguous += 1
            continue
        a_shares, a_trades = sum_field(ar, "totalWeeklyShareQuantity"), sum_field(ar, "totalWeeklyTradeCount")
        f_shares, f_trades = sum_field(fr, "totalWeeklyShareQuantity"), sum_field(fr, "totalWeeklyTradeCount")
        if None in (a_shares, a_trades, f_shares, f_trades):
            bridge_invalid += 1
            continue
        if a_shares != f_shares or a_trades != f_trades:
            bridge_mismatch += 1
            continue
        bridge_mapped += 1
        mapped_shares += a_shares
        if not stable_date_group:
            continue

        shares_by_participant = defaultdict(int)
        participant_keys = []
        identity_valid = True
        has_de_minimis = False
        for row in fr:
            if "DE MINIMIS" in norm(row.get("marketParticipantName")):
                has_de_minimis = True
                identity_valid = False
                continue
            key = participant_key(row)
            shares = parse_int(row.get("totalWeeklyShareQuantity"))
            if not key or shares is None:
                identity_valid = False
                continue
            participant_keys.append(key)
            shares_by_participant[key] += shares
        if (
            identity_valid and not has_de_minimis
            and len(participant_keys) == len(set(participant_keys))
            and sum(shares_by_participant.values()) == a_shares
            and a_shares > 0
        ):
            weights = sorted((value / a_shares for value in shares_by_participant.values()), reverse=True)
            concentration.append({
                "hhi": sum(weight * weight for weight in weights),
                "top1": weights[0],
                "top3": sum(weights[:3]),
                "participant_count": len(weights),
            })
            stable_concentration_symbols += 1
            stable_shares += a_shares
            stable_participant_keys.update(participant_keys)

    pub = next(iter(week_publication_dates)) if len(week_publication_dates) == 1 and missing_invalid_dates == 0 else None
    week_date = date.fromisoformat(week)
    lag = (pub - week_date).days if pub else None
    clock_valid = pub is not None and lag in ALLOWED_LAGS
    hhi = [x["hhi"] for x in concentration]
    top1 = [x["top1"] for x in concentration]
    top3 = [x["top3"] for x in concentration]
    participant_count = [x["participant_count"] for x in concentration]
    return {
        "week_start_date": week,
        "rows": len(rows),
        "record_total": record_total,
        "pages": pages,
        "retrieval_count_match": len(rows) == record_total,
        "aggregate_symbols": len(aggregate),
        "firm_symbols": len(firms),
        "union_symbols": len(set(aggregate) | set(firms)),
        "revision_stable_symbols": stable_symbols,
        "revised_symbols": revised_symbols,
        "bridge_mapped_symbols": bridge_mapped,
        "bridge_missing_symbols": bridge_missing,
        "bridge_ambiguous_symbols": bridge_ambiguous,
        "bridge_invalid_numeric_symbols": bridge_invalid,
        "bridge_mismatched_symbols": bridge_mismatch,
        "symbol_bridge_gate": "PASS" if bridge_mapped > 0 and not any((bridge_missing, bridge_ambiguous, bridge_invalid, bridge_mismatch)) else "FAIL_OR_REVIEW",
        "revision_stable_concentration_symbols": stable_concentration_symbols,
        "share_coverage_pct": round(100 * stable_shares / mapped_shares, 6) if mapped_shares else None,
        "symbol_coverage_pct": round(100 * stable_concentration_symbols / bridge_mapped, 6) if bridge_mapped else None,
        "mapped_aggregate_shares": mapped_shares,
        "revision_stable_concentration_shares": stable_shares,
        "stable_unique_participant_keys": len(stable_participant_keys),
        "hhi_mean": describe(hhi)["mean"],
        "hhi_median": describe(hhi)["median"],
        "hhi_p90": describe(hhi)["p90"],
        "top1_share_mean": describe(top1)["mean"],
        "top1_share_median": describe(top1)["median"],
        "top1_share_p90": describe(top1)["p90"],
        "top3_share_mean": describe(top3)["mean"],
        "top3_share_median": describe(top3)["median"],
        "top3_share_p90": describe(top3)["p90"],
        "participant_count_mean": describe(participant_count)["mean"],
        "participant_count_median": describe(participant_count)["median"],
        "participant_count_p90": describe(participant_count)["p90"],
        "initial_published_date": pub.isoformat() if pub else None,
        "publication_lag_days": lag,
        "date_level_clock_valid": clock_valid,
        "raw_rows_retained": False,
        "raw_identifiers_retained": False,
    }


def next_nyse_session(publication_date, session_dates):
    from bisect import bisect_right
    position = bisect_right(session_dates, publication_date)
    if position >= len(session_dates):
        raise RuntimeError("NYSE calendar does not extend beyond publication date")
    return session_dates[position]


def load_historical(summary_path, clock_summary_path, clock_csv_path):
    summary = json.loads(Path(summary_path).read_text(encoding="utf-8"))
    clock_summary = json.loads(Path(clock_summary_path).read_text(encoding="utf-8"))
    if summary.get("phase") != 375 or not summary.get("all_partitions_complete"):
        raise RuntimeError("Phase 375 artifact is not a complete historical baseline")
    if not summary.get("inventory", {}).get("consecutive"):
        raise RuntimeError("Phase 375 historical week inventory is not consecutive")
    if not summary.get("all_symbol_bridges_pass") or not summary.get("all_stable_concentration_gates_pass"):
        raise RuntimeError("Phase 375 aggregate bridge/concentration gate did not pass")
    if summary.get("raw_rows_retained") or summary.get("raw_identifiers_retained"):
        raise RuntimeError("Historical artifact violates aggregate-only retention policy")
    if clock_summary.get("phase") != 385 or not clock_summary.get("date_level_clock_validated"):
        raise RuntimeError("Phase 385 date-level publication clock did not pass")
    if clock_summary.get("intraday_first_receipt_certified") is not False:
        raise RuntimeError("Unexpected Phase 385 intraday-clock status")
    with open(clock_csv_path, newline="", encoding="utf-8") as handle:
        clock_rows = list(csv.DictReader(handle))
    clock = {row["week_start_date"]: row for row in clock_rows}
    output = []
    for part in summary.get("partitions", []):
        week = part["week"]
        if week not in clock:
            raise RuntimeError(f"Missing historical publication-clock row: {week}")
        c = clock[week]
        conc = part["stable_broker_dealer_reporting_concentration"]
        pub = parse_date(c["initial_published_date"])
        entry = parse_date(c["first_eligible_nyse_session_strictly_after_publication"])
        if pub is None or entry is None or entry <= pub:
            raise RuntimeError(f"Invalid historical next-session clock: {week}")
        output.append({
            "week_start_date": week,
            "initial_published_date": pub.isoformat(),
            "first_eligible_nyse_session": entry.isoformat(),
            "share_coverage_pct": part["revision_stable_share_volume_coverage_pct"],
            "symbol_coverage_pct": part["revision_stable_symbol_coverage_pct"],
            "hhi_mean": conc["hhi"]["mean"],
            "hhi_median": conc["hhi"]["median"],
            "hhi_p90": conc["hhi"]["p90"],
            "top1_share_mean": conc["top1_share"]["mean"],
            "top1_share_median": conc["top1_share"]["median"],
            "top1_share_p90": conc["top1_share"]["p90"],
            "top3_share_mean": conc["top3_share"]["mean"],
            "top3_share_median": conc["top3_share"]["median"],
            "top3_share_p90": conc["top3_share"]["p90"],
            "participant_count_mean": conc["participant_count"]["mean"],
            "participant_count_median": conc["participant_count"]["median"],
            "participant_count_p90": conc["participant_count"]["p90"],
            "stable_unique_participant_keys": part["stable_unique_participant_keys"],
            "revision_stable_symbols": part["revision_stable_symbols"],
            "revised_symbols": part["revised_symbols"],
            "revision_stable_concentration_symbols": part["revision_stable_concentration_symbols"],
            "source_window": "weeklySummaryHistoric",
            "date_level_clock_valid": True,
            "symbol_bridge_gate": "PASS",
            "revision_stable_concentration_symbols": part["revision_stable_concentration_symbols"],
        })
    output.sort(key=lambda row: row["week_start_date"])
    if len(output) != 209:
        raise RuntimeError(f"Expected 209 Phase 375 weeks, found {len(output)}")
    return output



def audit_current_inventory(session):
    metadata = request_json(session, META_URL)
    fields = tuple(metadata.get("partitionFields") or ())
    if fields != EXPECTED_FIELDS:
        raise RuntimeError(f"Current weeklySummary partition schema changed: {fields}")
    partitions = request_json(session, PARTITIONS_URL)
    raw, unique = parse_partitions(partitions, fields)
    tier_counts = Counter(tier for _, tier in unique)
    weeks = sorted({week for week, tier in unique if tier == TIER})
    if not weeks:
        raise RuntimeError("Current weeklySummary partition inventory contains no T1 weeks")
    sample_weeks = {weeks[0], weeks[len(weeks)//2], weeks[-1]}
    boundary = "2025-11-17"
    if boundary in weeks:
        sample_weeks.add(boundary)
    nyse = mcal.get_calendar("NYSE")
    parsed_samples = [date.fromisoformat(week) for week in sample_weeks]
    schedule = nyse.schedule(
        start_date=(min(parsed_samples)-timedelta(days=10)).isoformat(),
        end_date=(max(parsed_samples)+timedelta(days=120)).isoformat(),
    )
    sessions = sorted(ts.date() for ts in schedule.index)
    samples = []
    for week in sorted(sample_weeks):
        rows, total, pages = fetch_week(session, week)
        part = analyze_week(rows, week, total, pages)
        pub = parse_date(part["initial_published_date"])
        entry = next_nyse_session(pub, sessions) if pub and part["date_level_clock_valid"] else None
        samples.append({
            "week_start_date": week,
            "rows": total,
            "pages": pages,
            "publication_date": pub.isoformat() if pub else None,
            "publication_lag_days": part["publication_lag_days"],
            "date_level_clock_valid": part["date_level_clock_valid"],
            "first_eligible_nyse_session": entry.isoformat() if entry else None,
            "symbol_bridge_gate": part["symbol_bridge_gate"],
            "aggregate_symbols": part["aggregate_symbols"],
            "firm_symbols": part["firm_symbols"],
            "revision_stable_symbols": part["revision_stable_symbols"],
            "revised_symbols": part["revised_symbols"],
            "revision_stable_concentration_symbols": part["revision_stable_concentration_symbols"],
            "share_coverage_pct": part["share_coverage_pct"],
            "hhi_mean": part["hhi_mean"],
        })
        print(
            f"INVENTORY_SAMPLE|WEEK={week}|ROWS={total}|PUB={pub}|"
            f"LAG={part['publication_lag_days']}|BRIDGE={part['symbol_bridge_gate']}|"
            f"SHARE_COVERAGE={part['share_coverage_pct']}",
            flush=True,
        )
        del rows
    return {
        "metadata_status": metadata.get("status"),
        "partition_fields": list(fields),
        "partition_payload_keys": sorted(partitions.keys()) if isinstance(partitions, dict) else [],
        "raw_partition_records": len(raw),
        "unique_partition_pairs": len(unique),
        "tier_counts": dict(tier_counts),
        "t1_week_count": len(weeks),
        "first_t1_week": weeks[0],
        "last_t1_week": weeks[-1],
        "sample_weeks": samples,
        "raw_rows_retained": False,
        "raw_identifiers_retained": False,
    }


def fetch_current(session, after_week, historical):
    metadata = request_json(session, META_URL)
    fields = tuple(metadata.get("partitionFields") or ())
    if fields != EXPECTED_FIELDS:
        raise RuntimeError(f"Current weeklySummary partition schema changed: {fields}")
    if metadata.get("status") not in (None, "Active"):
        raise RuntimeError(f"Current weeklySummary status is not Active: {metadata.get('status')}")
    partitions = request_json(session, PARTITIONS_URL)
    raw, unique = parse_partitions(partitions, fields)
    tier_counts = Counter(tier for _, tier in unique)
    all_weeks = sorted({week for week, tier in unique if tier == TIER})
    if len(all_weeks) < 200 or len(all_weeks) > 300:
        raise RuntimeError(f"Unexpected current T1 partition inventory: {len(all_weeks)}")
    parsed_all = [date.fromisoformat(week) for week in all_weeks]
    if any(day.weekday() != 0 for day in parsed_all):
        raise RuntimeError("Current T1 week anchor is not Monday")
    all_gaps = [(a.isoformat(), b.isoformat()) for a, b in zip(parsed_all, parsed_all[1:]) if (b-a).days != 7]
    if all_gaps:
        raise RuntimeError(f"Current T1 partition inventory has gaps: {all_gaps[:5]}")

    incremental_weeks = [week for week in all_weeks if week > after_week]
    if len(incremental_weeks) < 40 or len(incremental_weeks) > 60:
        raise RuntimeError(f"Unexpected incremental T1 extension after {after_week}: {len(incremental_weeks)} weeks")
    parsed = [date.fromisoformat(week) for week in incremental_weeks]
    gaps = [(a.isoformat(), b.isoformat()) for a, b in zip(parsed, parsed[1:]) if (b-a).days != 7]
    if gaps:
        raise RuntimeError(f"Incremental current T1 weeks are not consecutive: {gaps[:5]}")
    if parsed and (parsed[0] - date.fromisoformat(after_week)).days != 7:
        raise RuntimeError(f"Current T1 extension does not begin one week after historical end {after_week}")

    overlap_candidates = ["2021-12-06", "2024-05-20"]
    overlap_weeks = [week for week in overlap_candidates if week in all_weeks]
    historical_map = {row["week_start_date"]: row for row in historical}
    if len(overlap_weeks) != len(overlap_candidates) or any(week not in historical_map for week in overlap_weeks):
        raise RuntimeError("Required historical/current overlap validation weeks are unavailable")

    nyse = mcal.get_calendar("NYSE")
    all_sample_dates = [date.fromisoformat(week) for week in incremental_weeks + overlap_weeks]
    cal_start = min(all_sample_dates) - timedelta(days=10)
    cal_end = max(all_sample_dates) + timedelta(days=120)
    schedule = nyse.schedule(start_date=cal_start.isoformat(), end_date=cal_end.isoformat())
    sessions = sorted(ts.date() for ts in schedule.index)

    output = []
    for index, week in enumerate(incremental_weeks, start=1):
        rows, total, pages = fetch_week(session, week)
        part = analyze_week(rows, week, total, pages)
        if not part["retrieval_count_match"]:
            raise RuntimeError(f"Current T1 Record-Total mismatch: {week}")
        pub = parse_date(part["initial_published_date"])
        if not part["date_level_clock_valid"] or pub is None:
            raise RuntimeError(f"Current T1 week has no single schedule-consistent publication date: {week}")
        entry = next_nyse_session(pub, sessions)
        part["first_eligible_nyse_session"] = entry.isoformat()
        part["source_window"] = "weeklySummary"
        output.append(part)
        print(
            f"CURRENT_WEEK={index}/{len(incremental_weeks)}|WEEK={week}|ROWS={total}|"
            f"STABLE_SYMBOLS={part['revision_stable_concentration_symbols']}|"
            f"SHARE_COVERAGE={part['share_coverage_pct']}|CLOCK=PASS",
            flush=True,
        )
        del rows

    overlap_results = []
    for week in overlap_weeks:
        rows, total, pages = fetch_week(session, week)
        part = analyze_week(rows, week, total, pages)
        old = historical_map[week]
        checks = {
            "publication_date": part["initial_published_date"] == old["initial_published_date"],
            "share_coverage": (
                old.get("share_coverage_pct") is not None
                and part.get("share_coverage_pct") is not None
                and abs(float(old["share_coverage_pct"]) - float(part["share_coverage_pct"])) < 1e-5
            ),
            "hhi_mean": (
                old.get("hhi_mean") is not None and part.get("hhi_mean") is not None
                and abs(float(old["hhi_mean"]) - float(part["hhi_mean"])) < 1e-6
            ),
            "top1_share_mean": (
                old.get("top1_share_mean") is not None and part.get("top1_share_mean") is not None
                and abs(float(old["top1_share_mean"]) - float(part["top1_share_mean"])) < 1e-6
            ),
            "top3_share_mean": (
                old.get("top3_share_mean") is not None and part.get("top3_share_mean") is not None
                and abs(float(old["top3_share_mean"]) - float(part["top3_share_mean"])) < 1e-6
            ),
            "participant_count_mean": (
                old.get("participant_count_mean") is not None and part.get("participant_count_mean") is not None
                and abs(float(old["participant_count_mean"]) - float(part["participant_count_mean"])) < 1e-6
            ),
            "revision_stable_symbols": old.get("revision_stable_symbols") == part.get("revision_stable_symbols"),
            "revised_symbols": old.get("revised_symbols") == part.get("revised_symbols"),
            "bridge_gate": part.get("symbol_bridge_gate") == "PASS",
            "retrieval_count": part.get("retrieval_count_match") is True,
        }
        overlap_results.append({
            "week_start_date": week,
            "checks": checks,
            "metrics_match": all(checks.values()),
            "current_rows": total,
            "current_pages": pages,
            "historical_hhi_mean": old.get("hhi_mean"),
            "current_hhi_mean": part.get("hhi_mean"),
            "historical_share_coverage_pct": old.get("share_coverage_pct"),
            "current_share_coverage_pct": part.get("share_coverage_pct"),
        })
        print(
            f"OVERLAP_VALIDATION|WEEK={week}|MATCH={all(checks.values())}|"
            f"HHI_OLD={old.get('hhi_mean')}|HHI_NEW={part.get('hhi_mean')}",
            flush=True,
        )
        del rows
    if not all(item["metrics_match"] for item in overlap_results):
        raise RuntimeError("Current/historic overlap validation failed")

    return {
        "metadata_status": metadata.get("status"),
        "partition_fields": list(fields),
        "raw_partition_pairs": len(raw),
        "unique_partition_pairs": len(unique),
        "tier_counts": dict(tier_counts),
        "inventory_total_t1_weeks": len(all_weeks),
        "inventory_first_t1_week": all_weeks[0],
        "inventory_last_t1_week": all_weeks[-1],
        "incremental_weeks_count": len(output),
        "incremental_first_week": output[0]["week_start_date"],
        "incremental_last_week": output[-1]["week_start_date"],
        "overlap_validation": overlap_results,
        "all_incremental_pages_reconciled": all(row["retrieval_count_match"] for row in output),
        "all_incremental_date_level_clocks_valid": all(row["date_level_clock_valid"] for row in output),
        "all_incremental_symbol_bridges_pass": all(row["symbol_bridge_gate"] == "PASS" for row in output),
        "weeks": output,
    }

def consecutive_weekly(rows):
    weeks = [date.fromisoformat(row["week_start_date"]) for row in rows]
    return {
        "count": len(weeks),
        "first": weeks[0].isoformat() if weeks else None,
        "last": weeks[-1].isoformat() if weeks else None,
        "duplicates": len(weeks) - len(set(weeks)),
        "gaps": [
            {"left": a.isoformat(), "right": b.isoformat(), "days": (b-a).days}
            for a, b in zip(weeks, weeks[1:]) if (b-a).days != 7
        ],
    }


def autocorrelation(rows, lag):
    pairs = []
    for i in range(lag, len(rows)):
        segment = rows[i-lag:i+1]
        if all(
            row.get("share_coverage_pct") is not None
            and float(row["share_coverage_pct"]) >= COVERAGE_FLOOR
            and row.get("hhi_mean") is not None
            for row in segment
        ):
            pairs.append((float(segment[0]["hhi_mean"]), float(segment[-1]["hhi_mean"])))
    if len(pairs) < 3:
        return {"n_pairs": len(pairs), "correlation": None}
    xs = [x for x, _ in pairs]
    ys = [y for _, y in pairs]
    mx, my = statistics.mean(xs), statistics.mean(ys)
    vx = sum((x-mx)**2 for x in xs)
    vy = sum((y-my)**2 for y in ys)
    corr = sum((x-mx)*(y-my) for x, y in pairs) / (vx*vy)**0.5 if vx > 0 and vy > 0 else None
    return {"n_pairs": len(pairs), "correlation": round(corr, 6) if corr is not None else None}


def build_sample_diagnostics(rows, as_of_date):
    nyse = mcal.get_calendar("NYSE")
    start = date.fromisoformat(rows[0]["first_eligible_nyse_session"])
    end = date.fromisoformat(rows[-1]["first_eligible_nyse_session"]) + timedelta(days=180)
    schedule = nyse.schedule(start_date=start.isoformat(), end_date=end.isoformat())
    sessions = sorted(ts.date() for ts in schedule.index)
    for row in rows:
        entry = parse_date(row["first_eligible_nyse_session"])
        if entry not in sessions:
            raise RuntimeError(f"Entry date is not an NYSE session: {entry}")
        pos = bisect_left(sessions, entry)
        for horizon in (5, 10, 20):
            maturity_key = f"outcome_maturity_date_{horizon}s"
            if pos + horizon - 1 >= len(sessions):
                row[maturity_key] = None
            else:
                row[maturity_key] = sessions[pos + horizon - 1].isoformat()

    strict_count = sensitivity_count = strict_high = sensitivity_high = 0
    for i, row in enumerate(rows):
        row["rank_hhi_52of52"] = None
        row["rank_hhi_48of52"] = None
        if i < LOOKBACK:
            continue
        prior = rows[i-LOOKBACK:i]
        current_ok = (
            row.get("share_coverage_pct") is not None
            and float(row["share_coverage_pct"]) >= COVERAGE_FLOOR
            and row.get("hhi_mean") is not None
            and row.get("date_level_clock_valid", True)
            and row.get("symbol_bridge_gate", "PASS") == "PASS"
            and int(row.get("revision_stable_concentration_symbols", 1) or 0) > 0
        )
        history = [
            float(x["hhi_mean"]) for x in prior
            if x.get("share_coverage_pct") is not None
            and float(x["share_coverage_pct"]) >= COVERAGE_FLOOR
            and x.get("hhi_mean") is not None
            and x.get("date_level_clock_valid", True)
            and x.get("symbol_bridge_gate", "PASS") == "PASS"
            and int(x.get("revision_stable_concentration_symbols", 1) or 0) > 0
        ]
        if not current_ok:
            continue
        if len(history) >= MIN_HISTORY_VALID:
            rank = sum(value < float(row["hhi_mean"]) for value in history) / len(history)
            row["rank_hhi_48of52"] = round(rank, 8)
            sensitivity_count += 1
            if rank >= HIGH_RANK:
                sensitivity_high += 1
        if len(history) == LOOKBACK:
            rank = sum(value < float(row["hhi_mean"]) for value in history) / LOOKBACK
            row["rank_hhi_52of52"] = round(rank, 8)
            strict_count += 1
            if rank >= HIGH_RANK:
                strict_high += 1

    horizon_plans = {}
    for horizon in (5, 10, 20):
        maturity_key = f"outcome_maturity_date_{horizon}s"
        valid = [
            row for row in rows
            if row.get("rank_hhi_48of52") is not None
            and row.get(maturity_key) is not None
            and parse_date(row[maturity_key]) <= as_of_date
        ]
        evaluation_start = None
        training_count_at_start = 0
        for j, current in enumerate(valid):
            current_entry = parse_date(current["first_eligible_nyse_session"])
            matured_prior = [
                prior for prior in valid[:j]
                if parse_date(prior[maturity_key]) < current_entry
            ]
            if len(matured_prior) >= MIN_TRAIN:
                evaluation_start = j
                training_count_at_start = len(matured_prior)
                break
        evaluation = valid[evaluation_start:] if evaluation_start is not None else []
        high = sum(float(row["rank_hhi_48of52"]) >= HIGH_RANK for row in evaluation)
        nonhigh = len(evaluation) - high
        horizon_plans[str(horizon)] = {
            "outcome_horizon_sessions": horizon,
            "matured_feature_observations": len(valid),
            "minimum_mature_training_observations": MIN_TRAIN,
            "evaluation_observations": len(evaluation),
            "evaluation_high": high,
            "evaluation_nonhigh": nonhigh,
            "evaluation_start_week": evaluation[0]["week_start_date"] if evaluation else None,
            "training_mature_count_at_start": training_count_at_start,
            "minimum_evaluation_observations": MIN_EVAL,
            "minimum_high": MIN_HIGH,
            "minimum_nonhigh": MIN_NONHIGH,
            "sample_gate_pass": len(evaluation) >= MIN_EVAL and high >= MIN_HIGH and nonhigh >= MIN_NONHIGH,
            "warning": "Sample feasibility only. No returns, labels, model fitting, alpha, OOS, bootstrap or LOO were run.",
        }
    return {
        "as_of_date_utc": as_of_date.isoformat(),
        "coverage_floor_pct": COVERAGE_FLOOR,
        "rolling_reference_weeks": LOOKBACK,
        "strict_52_of_52": {
            "valid_observations": strict_count,
            "high_at_80th_percentile": strict_high,
        },
        "exploratory_48_of_52_sensitivity": {
            "minimum_valid_reference_weeks": MIN_HISTORY_VALID,
            "valid_observations": sensitivity_count,
            "high_at_80th_percentile": sensitivity_high,
            "nonhigh": sensitivity_count - sensitivity_high,
            "warning": "48/52 and the 80th-percentile cut are feasibility sensitivities only, not a preregistered or admitted signal definition",
        },
        "chronological_sample_plan_by_horizon": horizon_plans,
        "hhi_autocorrelation": {
            "lag1": autocorrelation(rows, 1),
            "lag4": autocorrelation(rows, 4),
        },
    }


def combine_history(historical, current):
    by_week = {row["week_start_date"]: row for row in historical}
    overlap = []
    conflicts = []
    for row in current:
        week = row["week_start_date"]
        if week in by_week:
            old = by_week[week]
            same = (
                old.get("initial_published_date") == row.get("initial_published_date")
                and old.get("share_coverage_pct") is not None
                and row.get("share_coverage_pct") is not None
                and abs(float(old["share_coverage_pct"]) - float(row["share_coverage_pct"])) < 1e-5
                and old.get("hhi_mean") is not None and row.get("hhi_mean") is not None
                and abs(float(old["hhi_mean"]) - float(row["hhi_mean"])) < 1e-6
            )
            overlap.append({"week": week, "metrics_match": same})
            if not same:
                conflicts.append(week)
                del by_week[week]
        else:
            by_week[week] = row
    combined = sorted(by_week.values(), key=lambda row: row["week_start_date"])
    inventory = consecutive_weekly(combined)
    inventory["consecutive"] = inventory["duplicates"] == 0 and not inventory["gaps"]
    return combined, {
        "overlap_weeks": overlap,
        "overlap_conflicts": conflicts,
        "inventory": inventory,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--historical-summary", required=True)
    parser.add_argument("--historical-clock-summary", required=True)
    parser.add_argument("--historical-clock-csv", required=True)
    parser.add_argument("--output", default="phase518_output")
    parser.add_argument("--inventory-only", action="store_true")
    args = parser.parse_args()
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    historical = load_historical(
        args.historical_summary, args.historical_clock_summary, args.historical_clock_csv
    )
    session = requests.Session()
    session.headers.update({
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Data-API-Version": "1",
        "User-Agent": "SmartMoneyResearch-Phase518/1.0",
    })
    token = os.getenv("FINRA_API_TOKEN", "").strip()
    if token:
        session.headers["Authorization"] = f"Bearer {token}"
    if args.inventory_only:
        inventory = audit_current_inventory(session)
        summary = {
            "phase": 518,
            "mode": "CURRENT_WEEKLYSUMMARY_PARTITION_AND_SAMPLE_AUDIT",
            "audit_timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "historical_artifacts_validated": True,
            "current_inventory": inventory,
            "interpretation": "The official FINRA documentation describes weeklySummary as a rolling 12-month production dataset. This audit independently checks the live partition inventory and samples boundary/middle weeks before assuming its effective history.",
            "authorization": {
                "data_feasibility_only": True,
                "historical_signal_test_authorized": False,
                "return_or_alpha_test_authorized": False,
                "forward_returns_used": False,
                "oos_used": False,
                "bootstrap_used": False,
                "loo_used": False,
                "holdout_used": False,
                "signal_admitted": False,
                "f80_changed": False,
                "production_changed": False,
            },
        }
        (output_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(json.dumps({
            "phase": 518,
            "mode": summary["mode"],
            "status": inventory["metadata_status"],
            "t1_week_count": inventory["t1_week_count"],
            "first_t1_week": inventory["first_t1_week"],
            "last_t1_week": inventory["last_t1_week"],
            "sample_weeks": inventory["sample_weeks"],
            "signal_admitted": False,
        }, indent=2), flush=True)
        return
    current_result = fetch_current(session)
    combined, reconciliation = combine_history(historical, current_result["weeks"])
    if not reconciliation["inventory"]["consecutive"]:
        raise RuntimeError(
            "Combined historic+production T1 weeks are not consecutive: "
            + json.dumps(reconciliation["inventory"], sort_keys=True)
        )
    if reconciliation["overlap_conflicts"]:
        raise RuntimeError(f"Historic/production overlap conflicts: {reconciliation['overlap_conflicts']}")

    diagnostics = build_sample_diagnostics(combined)
    summary = {
        "phase": 518,
        "audit_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "source": "FINRA OTCMarket weeklySummaryHistoric + weeklySummary",
        "historical_artifacts": {
            "phase375_run_id": 43493465495,
            "phase375_artifact_id": 14081855428,
            "phase375_artifact_sha256": "0b246e2b784db2c713df999a27b744d5ed8a3111f200e860f7cc79ccf9c7bb3d",
            "phase385_run_id": 43536490386,
            "phase385_artifact_id": 14100393795,
            "phase385_artifact_sha256": "3630ce815040a2487ebfc86369552f21da3ee1b58e235f169cd0f604cffc3a46",
        },
        "current_dataset": {
            "dataset": DATASET,
            "status": current_result["metadata_status"],
            "partition_fields": current_result["partition_fields"],
            "weeks_retrieved": len(current_result["weeks"]),
            "first_week": current_result["weeks"][0]["week_start_date"] if current_result["weeks"] else None,
            "last_week": current_result["weeks"][-1]["week_start_date"] if current_result["weeks"] else None,
            "all_pages_reconciled": all(row["retrieval_count_match"] for row in current_result["weeks"]),
            "all_date_level_clocks_valid": all(row["date_level_clock_valid"] for row in current_result["weeks"]),
            "all_symbol_bridges_pass": all(row["symbol_bridge_gate"] == "PASS" for row in current_result["weeks"]),
        },
        "combined_history": reconciliation,
        "sample_diagnostics": diagnostics,
        "interpretation": {
            "proxy": "equal-weighted cross-sectional concentration of FINRA ATS reporting participants by symbol-week",
            "not": [
                "beneficial-owner identity",
                "institutional ownership",
                "informed-trader identity",
                "buy/sell direction",
                "proof of smart money",
            ],
            "date_clock": "first NYSE regular session strictly after initialPublishedDate; date-level conservative clock only, not intraday first receipt",
            "coverage": "exclude current symbol-week concentration unless all row dates are valid, publication lag is 21/22 days, no post-initial revision exists, aggregate/firms reconcile, and participant rows are complete",
        },
        "authorization": {
            "data_feasibility_only": True,
            "historical_signal_test_authorized": False,
            "return_or_alpha_test_authorized": False,
            "forward_returns_used": False,
            "oos_used": False,
            "bootstrap_used": False,
            "loo_used": False,
            "holdout_used": False,
            "signal_admitted": False,
            "f80_changed": False,
            "production_changed": False,
        },
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    columns = [
        "week_start_date", "initial_published_date", "first_eligible_nyse_session",
        "share_coverage_pct", "symbol_coverage_pct", "hhi_mean", "hhi_median", "hhi_p90",
        "top1_share_mean", "top1_share_median", "top3_share_mean",
        "participant_count_mean", "stable_unique_participant_keys",
        "rank_hhi_52of52", "rank_hhi_48of52", "outcome_maturity_date_20s",
    ]
    with open(output_dir / "combined_weekly.csv", "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(combined)
    print(json.dumps({
        "phase": 518,
        "current_weeks": len(current_result["weeks"]),
        "combined_weeks": len(combined),
        "combined_first": combined[0]["week_start_date"],
        "combined_last": combined[-1]["week_start_date"],
        "consecutive": reconciliation["inventory"]["consecutive"],
        "strict_52of52_valid": diagnostics["strict_52_of_52"]["valid_observations"],
        "sensitivity_48of52_valid": diagnostics["exploratory_48_of_52_sensitivity"]["valid_observations"],
        "evaluation_observations": diagnostics["chronological_sample_plan"]["evaluation_observations"],
        "evaluation_high": diagnostics["chronological_sample_plan"]["evaluation_high"],
        "evaluation_nonhigh": diagnostics["chronological_sample_plan"]["evaluation_nonhigh"],
        "sample_gate_pass": diagnostics["chronological_sample_plan"]["sample_gate_pass"],
        "signal_admitted": False,
    }, indent=2), flush=True)


if __name__ == "__main__":
    main()

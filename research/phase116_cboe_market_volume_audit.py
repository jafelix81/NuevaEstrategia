#!/usr/bin/env python3
"""Audit Cboe's public US-equity historical market-volume CSV archive.

This is market-center/tape aggregate data, not symbol-level order flow.
No returns or strategy features are calculated here.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import os
from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Dict, List, Tuple

import requests

BASE = "https://cdn.cboe.com/resources/us/equities/market-statistics/historical-market-volume"
YEARS = range(2009, 2027)
NUMERIC = [
    "Tape A Shares", "Tape B Shares", "Tape C Shares", "Total Shares",
    "Tape A Notional", "Tape B Notional", "Tape C Notional", "Total Notional",
    "Tape A Trade Count", "Tape B Trade Count", "Tape C Trade Count", "Total Trade Count",
]
SHARES = ["Tape A Shares", "Tape B Shares", "Tape C Shares"]
NOTIONAL = ["Tape A Notional", "Tape B Notional", "Tape C Notional"]
TRADES = ["Tape A Trade Count", "Tape B Trade Count", "Tape C Trade Count"]
DAILY_HEADER = ["Day", "Market Participant"] + NUMERIC
MONTHLY_HEADER = ["Month", "Market Participant"] + NUMERIC
TOL_NOTIONAL = Decimal("0.10")
TOL_SHARES = Decimal("0.000001")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def dec(value: str, field: str) -> Decimal:
    try:
        x = Decimal(value.strip())
    except (InvalidOperation, AttributeError):
        raise ValueError("invalid numeric value in " + field + ": " + repr(value))
    if not x.is_finite() or x < 0:
        raise ValueError("negative or non-finite numeric value in " + field)
    return x


def parse_csv(data: bytes, kind: str, year: int) -> dict:
    text = data.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    expected = DAILY_HEADER if kind == "daily" else MONTHLY_HEADER
    if reader.fieldnames != expected:
        raise ValueError(kind + " header mismatch for " + str(year) + ": " + repr(reader.fieldnames))
    key_field = "Day" if kind == "daily" else "Month"
    rows = 0
    keys = set()
    dates = set()
    participants = set()
    month_agg: Dict[Tuple[str, str], Dict[str, Decimal]] = defaultdict(lambda: defaultdict(Decimal))
    anomalies = []
    trf_summary: Dict[str, Dict[str, Decimal]] = defaultdict(lambda: defaultdict(Decimal))
    total_summary: Dict[str, Decimal] = defaultdict(Decimal)

    for line_no, row in enumerate(reader, start=2):
        rows += 1
        raw_period = (row.get(key_field) or "").strip()
        participant = (row.get("Market Participant") or "").strip()
        if not raw_period or not participant:
            raise ValueError("blank key at " + kind + " " + str(year) + " line " + str(line_no))
        if kind == "daily":
            d = date.fromisoformat(raw_period)
            if d.year != year:
                raise ValueError("date outside requested year at line " + str(line_no))
            period = raw_period
            dates.add(d)
        else:
            dt = datetime.strptime(raw_period, "%Y-%m")
            if dt.year != year:
                raise ValueError("month outside requested year at line " + str(line_no))
            period = raw_period
        key = (period, participant)
        if key in keys:
            raise ValueError("duplicate " + kind + " key " + repr(key))
        keys.add(key)
        participants.add(participant)
        vals = {name: dec(row.get(name, ""), name) for name in NUMERIC}
        for total, parts, tol in [
            ("Total Shares", SHARES, TOL_SHARES),
            ("Total Notional", NOTIONAL, TOL_NOTIONAL),
            ("Total Trade Count", TRADES, Decimal("0")),
        ]:
            summed = sum((vals[x] for x in parts), Decimal("0"))
            if abs(vals[total] - summed) > tol:
                anomalies.append({"line": line_no, "key": key, "check": total,
                                  "reported": str(vals[total]), "sum": str(summed)})
        month = period[:7] if kind == "daily" else period
        agg_key = (month, participant)
        for name, value in vals.items():
            month_agg[agg_key][name] += value
        if kind == "daily":
            if "TRF" in participant.upper():
                for name, value in vals.items():
                    trf_summary[period][name] += value
            for name, value in vals.items():
                total_summary[period + "|" + name] += value

    if rows == 0:
        raise ValueError("empty " + kind + " file for " + str(year))
    if anomalies:
        raise ValueError("internal tape-total arithmetic mismatches: " + json.dumps(anomalies[:5]))

    return {
        "year": year, "kind": kind, "rows": rows, "keys": keys,
        "dates": dates, "participants": participants, "month_agg": month_agg,
        "sha256": sha256(data), "bytes": len(data),
        "trf_summary": trf_summary, "total_summary": total_summary,
    }


def compare_monthly(daily: dict, monthly: dict, year: int, current_month: str) -> dict:
    complete_months = sorted(m for (m, _p) in monthly["month_agg"].keys() if m < current_month)
    comparisons = 0
    mismatches = []
    missing_daily = []
    missing_monthly = []
    for month in complete_months:
        mkeys = {(m, p) for (m, p) in monthly["month_agg"] if m == month}
        dkeys = {(m, p) for (m, p) in daily["month_agg"] if m == month}
        for key in sorted(mkeys - dkeys):
            missing_daily.append(key)
        for key in sorted(dkeys - mkeys):
            missing_monthly.append(key)
        for key in sorted(mkeys & dkeys):
            comparisons += 1
            for field in NUMERIC:
                a = monthly["month_agg"][key][field]
                b = daily["month_agg"][key][field]
                tol = TOL_NOTIONAL if "Notional" in field else (TOL_SHARES if "Shares" in field else Decimal("0"))
                if abs(a - b) > tol:
                    mismatches.append({"key": key, "field": field, "monthly": str(a), "daily_sum": str(b)})
    return {
        "complete_months_compared": complete_months,
        "participant_month_comparisons": comparisons,
        "missing_daily_keys": missing_daily[:50],
        "missing_monthly_keys": missing_monthly[:50],
        "mismatches": mismatches[:50],
        "missing_daily_count": len(missing_daily),
        "missing_monthly_count": len(missing_monthly),
        "mismatch_count": len(mismatches),
    }


def download(session: requests.Session, year: int, kind: str, out: Path) -> dict:
    filename = ("market_history_" if kind == "daily" else "market_history_monthly_") + str(year) + ".csv"
    url = BASE + "/" + filename
    response = session.get(url, timeout=90)
    response.raise_for_status()
    if len(response.content) < 100:
        raise ValueError("implausibly small " + kind + " file for " + str(year))
    (out / filename).write_bytes(response.content)
    return parse_csv(response.content, kind, year)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="phase116_cboe_market_volume_output")
    args = parser.parse_args()
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update({"User-Agent": "NuevaEstrategia-Phase116/1.0 research audit"})

    current_month = date.today().strftime("%Y-%m")
    annual = []
    comparisons = []
    daily_market_rows = []
    for year in YEARS:
        daily = download(session, year, "daily", out)
        monthly = download(session, year, "monthly", out)
        if not daily["dates"]:
            raise ValueError("no daily dates for " + str(year))
        first_date = min(daily["dates"])
        last_date = max(daily["dates"])
        gaps = []
        ordered_dates = sorted(daily["dates"])
        for left, right in zip(ordered_dates, ordered_dates[1:]):
            if (right - left).days > 10:
                gaps.append({"from": left.isoformat(), "to": right.isoformat(),
                             "calendar_gap_days": (right - left).days})
        cmp = compare_monthly(daily, monthly, year, current_month)
        comparisons.append({"year": year, **cmp})
        annual.append({
            "year": year, "daily_rows": daily["rows"], "monthly_rows": monthly["rows"],
            "trading_dates": len(daily["dates"]), "first_date": first_date.isoformat(),
            "last_date": last_date.isoformat(), "daily_participants": sorted(daily["participants"]),
            "monthly_participants": sorted(monthly["participants"]),
            "daily_sha256": daily["sha256"], "monthly_sha256": monthly["sha256"],
            "daily_bytes": daily["bytes"], "monthly_bytes": monthly["bytes"],
            "calendar_gaps_over_10_days": gaps, "monthly_reconciliation": cmp,
        })
        for d in sorted(daily["dates"]):
            period = d.isoformat()
            trf = daily["trf_summary"].get(period, {})
            total_shares = daily["total_summary"].get(period + "|Total Shares", Decimal("0"))
            total_notional = daily["total_summary"].get(period + "|Total Notional", Decimal("0"))
            trf_shares = trf.get("Total Shares", Decimal("0"))
            trf_notional = trf.get("Total Notional", Decimal("0"))
            daily_market_rows.append({
                "date": period, "total_market_shares": str(total_shares),
                "trf_shares": str(trf_shares),
                "trf_share_fraction": str(trf_shares / total_shares) if total_shares else None,
                "total_market_notional": str(total_notional),
                "trf_notional": str(trf_notional),
                "trf_notional_fraction": str(trf_notional / total_notional) if total_notional else None,
            })

    result = {
        "source": "Cboe U.S. Equities Historical Market Volume",
        "retrieved_at_utc": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "coverage_years": [min(YEARS), max(YEARS)],
        "scope_warning": "Market-center/tape aggregates only; no symbol, participant identity, side, order or beneficial-owner fields.",
        "pit_warning": "Historical first-publication timestamps and correction vintages are not supplied by the public page/files; strict PIT is not established.",
        "annual": annual, "monthly_vs_daily": comparisons,
        "marketwide_daily_trf_context": daily_market_rows,
    }
    (out / "phase116_audit.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    with (out / "marketwide_daily_trf_context.csv").open("w", newline="", encoding="utf-8") as f:
        fields = list(daily_market_rows[0].keys())
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(daily_market_rows)

    failures = []
    for item in annual:
        if item["monthly_reconciliation"]["missing_daily_count"] or item["monthly_reconciliation"]["missing_monthly_count"] or item["monthly_reconciliation"]["mismatch_count"]:
            failures.append({"year": item["year"], "monthly_reconciliation": item["monthly_reconciliation"]})
    if failures:
        (out / "reconciliation_failures.json").write_text(json.dumps(failures, indent=2), encoding="utf-8")
        raise SystemExit("monthly/daily reconciliation failed: " + json.dumps(failures[:3]))
    print(json.dumps({
        "status": "PASS", "years": len(annual),
        "daily_rows": sum(x["daily_rows"] for x in annual),
        "monthly_rows": sum(x["monthly_rows"] for x in annual),
        "date_min": annual[0]["first_date"], "date_max": annual[-1]["last_date"],
        "participant_month_comparisons": sum(x["participant_month_comparisons"] for x in comparisons),
        "trf_context_days": len(daily_market_rows),
        "output": str(out),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

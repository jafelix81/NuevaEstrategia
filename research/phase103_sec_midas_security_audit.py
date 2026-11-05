#!/usr/bin/env python3
"""Phase 103: SEC MIDAS individual-security actual-file feasibility audit.

Source/schema/coverage/PIT audit only. No forward returns or alpha testing.
"""
from __future__ import annotations

import ast
import csv
import hashlib
import io
import json
import re
import time
import zipfile
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

import requests

SEC_PAGE = "https://www.sec.gov/data-research/sec-markets-data/marketstructuredata-security"
CATALOG_URL = "https://catalog.data.gov/dataset/metrics-by-individual-security"
UNIVERSE_SOURCE = Path("Nueva_Estrategia_Fase11_Real1000_LTM_v4.py")
OUT = Path("phase103_sec_midas_security_audit")
USER_AGENT = "Felix and Sarmiento Abogados S.C. research jose.felix@felixsarmiento.com"
REQUIRED = {
    "ticker", "date", "security", "mcaprank", "turnrank", "volatilityrank",
    "pricerank", "cancels", "trades", "littrades", "oddlots", "hidden",
    "tradesforhidden", "ordervol", "tradevol", "litvol", "oddlotvol",
    "hiddenvol", "tradevolforhidden",
}
NUMERIC_FIELDS = [
    "McapRank", "TurnRank", "VolatilityRank", "PriceRank", "Cancels", "Trades",
    "LitTrades", "OddLots", "Hidden", "TradesForHidden", "OrderVol", "TradeVol",
    "LitVol", "OddLotVol", "HiddenVol", "TradeVolForHidden",
]
SAMPLES = [
    {"key": "2012q1", "url": "https://www.sec.gov/files/opa/data/market-structure/metrics-individual-security/individual_security_2012_q10.zip",
     "start": "2012-01-01", "end": "2012-03-31", "regime": "earliest_catalogued_quarter"},
    {"key": "2016q1", "url": "https://www.sec.gov/files/opa/data/market-structure/metrics-individual-security/individual_security_2016_q1.zip",
     "start": "2016-01-01", "end": "2016-03-31", "regime": "pre_2017_feed_change"},
    {"key": "2017q2", "url": "https://www.sec.gov/files/opa/data/market-structure/metrics-individual-security/individual_security_2017_q2.zip",
     "start": "2017-04-01", "end": "2017-06-30", "regime": "contains_2017_05_01_nyse_integrated_feed_change"},
    {"key": "2019q4", "url": "https://www.sec.gov/files/node/add/data_distribution/individual_security_2019_q4.zip",
     "start": "2019-10-01", "end": "2019-12-31", "regime": "quarterly_continuity_check"},
    {"key": "2025q4", "url": "https://www.sec.gov/files/opa/data/market-structure/metrics-individual-security/individual_security_2025_q4.zip",
     "start": "2025-10-01", "end": "2025-12-31", "regime": "contains_2025_11_03_round_lot_change"},
    {"key": "2026q2", "url": "https://www.sec.gov/files/opa/data/market-structure/metrics-individual-security/individual_security_2026_q2.zip",
     "start": "2026-04-01", "end": "2026-06-30", "regime": "latest_published_quarter"},
]
FEED_BREAK = date(2017, 5, 1)
ROUND_LOT_BREAK = date(2025, 11, 3)


def load_legacy_universe() -> set[str]:
    tree = ast.parse(UNIVERSE_SOURCE.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "DEFAULT_UNIVERSE":
                    values = {str(x).strip().upper() for x in ast.literal_eval(node.value)}
                    if len(values) != 335:
                        raise RuntimeError(f"Expected 335 legacy names, got {len(values)}")
                    return values
    raise RuntimeError("DEFAULT_UNIVERSE not found")


def parse_date(value: str):
    value = (value or "").strip()
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%Y%m%d", "%m/%d/%Y", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(value[:19], fmt).date()
        except ValueError:
            pass
    return None


def detect_delimiter(header_line: str) -> str:
    return "|" if header_line.count("|") > header_line.count(",") else ","


def parse_last_modified(value: str | None):
    if not value:
        return None
    try:
        return parsedate_to_datetime(value).astimezone(timezone.utc).isoformat()
    except Exception:
        return None


def parse_csv_member(raw_stream, member_name: str, legacy: set[str], spec: dict) -> dict:
    text = io.TextIOWrapper(raw_stream, encoding="utf-8-sig", errors="replace", newline="")
    first = text.readline()
    if not first:
        raise ValueError(f"{member_name}: empty member")
    delimiter = detect_delimiter(first)
    header = next(csv.reader([first], delimiter=delimiter))
    normalized = [x.strip().lower().replace(" ", "") for x in header]
    missing = sorted(REQUIRED - set(normalized))
    if missing:
        raise ValueError(f"{member_name}: missing columns {missing}; header={header!r}")
    indices = {name: i for i, name in enumerate(normalized)}
    start, end = date.fromisoformat(spec["start"]), date.fromisoformat(spec["end"])
    rows = 0
    dates = set()
    tickers = set()
    ticker_days = defaultdict(set)
    date_tickers = defaultdict(set)
    ticker_security_pairs = set()
    security_values = Counter()
    numeric_nonnull = Counter()
    numeric_invalid = Counter()
    numeric_negative = Counter()
    malformed = 0
    bad_dates = 0
    blank_tickers = 0
    out_of_range = 0
    duplicates = Counter()
    security_samples = []
    row_samples = []
    rows_before_feed = rows_after_feed = 0
    rows_before_round = rows_after_round = 0

    for raw in csv.reader(text, delimiter=delimiter):
        if not raw or not any(x.strip() for x in raw):
            continue
        if len(raw) != len(header):
            malformed += 1
            continue
        row = {name: raw[idx].strip() for name, idx in indices.items()}
        ticker = row.get("ticker", "").upper()
        dt = parse_date(row.get("date", ""))
        security = row.get("security", "")
        if not ticker:
            blank_tickers += 1
            continue
        if dt is None:
            bad_dates += 1
            continue
        if dt < start or dt > end:
            out_of_range += 1
        rows += 1
        dates.add(dt)
        tickers.add(ticker)
        ticker_days[ticker].add(dt)
        date_tickers[dt].add(ticker)
        ticker_security_pairs.add((ticker, security))
        if security:
            security_values[security] += 1
        duplicates[(ticker, dt.isoformat(), security)] += 1
        for field in NUMERIC_FIELDS:
            value = row.get(field.lower(), "")
            if value in ("", ".", "NA", "N/A", "NULL"):
                continue
            numeric_nonnull[field] += 1
            try:
                number = float(value.replace(",", ""))
                if number < 0:
                    numeric_negative[field] += 1
            except ValueError:
                numeric_invalid[field] += 1
        if dt < FEED_BREAK:
            rows_before_feed += 1
        else:
            rows_after_feed += 1
        if dt < ROUND_LOT_BREAK:
            rows_before_round += 1
        else:
            rows_after_round += 1
        if len(row_samples) < 5:
            row_samples.append({
                k: row.get(k.lower(), "")
                for k in ["Ticker", "Date", "Security", "McapRank", "TurnRank", "VolatilityRank", "PriceRank"]
            })
        if security and len(security_samples) < 20 and security not in security_samples:
            security_samples.append(security)

    duplicate_groups = sum(1 for n in duplicates.values() if n > 1)
    duplicate_rows = sum(n - 1 for n in duplicates.values() if n > 1)
    daily_coverage = [len(legacy & date_tickers[d]) / len(legacy) for d in sorted(dates)]
    unique_legacy = legacy & tickers
    return {
        "member": member_name,
        "delimiter": "pipe" if delimiter == "|" else "comma",
        "header": header,
        "missing_required_columns": missing,
        "records": rows,
        "unique_dates": len(dates),
        "min_date": min(dates).isoformat() if dates else None,
        "max_date": max(dates).isoformat() if dates else None,
        "out_of_quarter_records": out_of_range,
        "bad_dates": bad_dates,
        "blank_tickers": blank_tickers,
        "malformed_rows": malformed,
        "unique_tickers": len(tickers),
        "legacy_335_symbols_seen": len(unique_legacy),
        "legacy_335_coverage_pct": round(100 * len(unique_legacy) / len(legacy), 2),
        "legacy_335_missing_sample": sorted(legacy - tickers)[:25],
        "legacy_335_daily_coverage_min_pct": round(100 * min(daily_coverage), 2) if daily_coverage else None,
        "legacy_335_daily_coverage_median_pct": round(100 * sorted(daily_coverage)[len(daily_coverage)//2], 2) if daily_coverage else None,
        "legacy_335_daily_coverage_max_pct": round(100 * max(daily_coverage), 2) if daily_coverage else None,
        "legacy_335_full_coverage_days": sum(x == 1.0 for x in daily_coverage),
        "duplicate_key_groups": duplicate_groups,
        "duplicate_rows_beyond_first": duplicate_rows,
        "ticker_security_pairs": len(ticker_security_pairs),
        "unique_security_field_values": len(security_values),
        "security_field_sample": security_samples,
        "numeric_nonnull_counts": dict(numeric_nonnull),
        "numeric_invalid_counts": dict(numeric_invalid),
        "numeric_negative_counts": dict(numeric_negative),
        "rows_before_2017_05_01": rows_before_feed,
        "rows_on_or_after_2017_05_01": rows_after_feed,
        "rows_before_2025_11_03": rows_before_round,
        "rows_on_or_after_2025_11_03": rows_after_round,
        "sample_rows": row_samples,
        "schema_status": "PASS" if rows and not missing and not out_of_range and not bad_dates and not blank_tickers and not malformed else "FAIL",
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    legacy = load_legacy_universe()
    session = requests.Session()
    session.headers.update({
        "User-Agent": USER_AGENT,
        "Accept": "application/zip,*/*",
        "Accept-Encoding": "identity",
    })
    page = session.get(SEC_PAGE, timeout=60)
    page.raise_for_status()
    page_review = re.search(r"Last Reviewed or Updated:\s*([^<\n]+)", page.text, re.I)
    page_reviewed = page_review.group(1).strip() if page_review else None

    samples, errors, hashes = [], [], []
    for spec in SAMPLES:
        try:
            head_error = None
            try:
                head = session.head(spec["url"], timeout=60, allow_redirects=True)
            except Exception as exc:
                head = None
                head_error = repr(exc)
            response = session.get(spec["url"], timeout=180, allow_redirects=True)
            response.raise_for_status()
            payload = response.content
            download = {
                "url": spec["url"],
                "http_status": response.status_code,
                "bytes": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
                "head_error": head_error,
                "head_status": head.status_code if head is not None else None,
                "head_last_modified": head.headers.get("Last-Modified") if head is not None else None,
                "head_etag": head.headers.get("ETag") if head is not None else None,
                "head_content_length": head.headers.get("Content-Length") if head is not None else None,
                "get_last_modified": response.headers.get("Last-Modified"),
                "get_last_modified_utc": parse_last_modified(response.headers.get("Last-Modified")),
                "get_etag": response.headers.get("ETag"),
                "get_content_length": response.headers.get("Content-Length"),
                "http_date": response.headers.get("Date"),
            }
            with zipfile.ZipFile(io.BytesIO(payload)) as zf:
                members = [n for n in zf.namelist() if n.lower().endswith(".csv")]
                if not members:
                    members = [n for n in zf.namelist() if n.lower().endswith(".txt")]
                if not members:
                    raise RuntimeError(f"No CSV/TXT data members in archive: {zf.namelist()}")
                parsed = [parse_csv_member(zf.open(n), n, legacy, spec) for n in members]
            lastmod = download.get("get_last_modified_utc")
            samples.append({
                **spec,
                "download": download,
                "last_modified_days_after_quarter_end": (
                    (datetime.fromisoformat(lastmod).date() - date.fromisoformat(spec["end"])).days
                    if lastmod else None
                ),
                "members": parsed,
                "records": sum(x["records"] for x in parsed),
                "unique_dates": max((x["unique_dates"] for x in parsed), default=0),
                "unique_tickers": max((x["unique_tickers"] for x in parsed), default=0),
                "legacy_335_coverage_pct": min((x["legacy_335_coverage_pct"] for x in parsed), default=0),
                "schema_status": "PASS" if parsed and all(x["schema_status"] == "PASS" for x in parsed) else "FAIL",
            })
            hashes.append({"key": spec["key"], "sha256": download["sha256"], "bytes": download["bytes"]})
            print(f"[MIDAS] {spec['key']} rows={samples[-1]['records']} tickers={samples[-1]['unique_tickers']} schema={samples[-1]['schema_status']}", flush=True)
            time.sleep(0.5)
        except Exception as exc:
            errors.append({"key": spec["key"], "url": spec["url"], "error": repr(exc)})
            print(f"[MIDAS] ERROR {spec['key']}: {exc!r}", flush=True)

    summary = {
        "phase": 103,
        "source": "SEC MIDAS Metrics by Individual Security",
        "source_page": SEC_PAGE,
        "data_catalog": CATALOG_URL,
        "data_catalog_resource_count": 58,
        "data_catalog_temporal_range": "2012-01-01 through 2026-06-30",
        "data_catalog_last_modified": "2017-10-30T17:43:20Z (stale catalog metadata; not a file publication timestamp)",
        "source_page_last_reviewed": page_reviewed,
        "audit_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "samples_expected": len(SAMPLES),
        "samples_completed": len(samples),
        "legacy_335_size": len(legacy),
        "samples": samples,
        "download_hashes": hashes,
        "errors": errors,
        "gates": {
            "all_sample_files_downloaded": len(samples) == len(SAMPLES) and not errors,
            "all_sample_schemas_valid": len(samples) == len(SAMPLES) and all(x["schema_status"] == "PASS" for x in samples),
            "daily_legacy_coverage_measured": bool(samples),
            "historical_security_identity_verified": False,
            "inactive_delisted_coverage_verified": False,
            "historical_publication_vintage_verified": False,
        },
        "universe_status": "SEC-defined >4,800-security panel; not a complete US listed-equity universe",
        "pit_status": "NOT_PASSED; HTTP Last-Modified/ETag/Date are recorded but not accepted as a validated historical public-availability vintage. The Data.gov catalog modified timestamp is stale (2017-10-30) despite current 2026 resources.",
        "methodology_breaks": {
            "2017_05_01": "SEC says NYSE moved from Ultrabook level feed to Integrated Feed; pre/post measures must be regime-separated.",
            "2025_11_03": "SEC says round-lot definition changed; odd-lot features must be regime-separated or normalized.",
        },
        "economic_interpretation": "Daily market-structure aggregates are not investor identity or aggressor-side flow. Hidden/odd-lot/trade-to-order features remain hypotheses.",
        "forward_returns_used": False,
        "alpha_test_authorized": False,
        "f80_changed": False,
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (OUT / "download_hashes.json").write_text(json.dumps(hashes, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2), flush=True)
    if not summary["gates"]["all_sample_files_downloaded"] or not summary["gates"]["all_sample_schemas_valid"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()

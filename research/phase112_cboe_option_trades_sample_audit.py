#!/usr/bin/env python3
"""Phase 112: inspect Cboe Option Trades public sample and reference mappings."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import re
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

SAMPLE_URL = "https://datashop.cboe.com/download/sample/216"
EXCHANGE_MAP_URL = "https://datashop.cboe.com/documents/livevol_exchange_ids.csv"
CONDITION_MAP_URL = "https://datashop.cboe.com/documents/livevol_trade_condition_ids.xlsx"

REQUIRED = {
    "underlying_symbol", "market_date", "quote_datetime", "sequence_number",
    "root", "expiration", "strike", "option_type", "exchange_id",
    "trade_size", "trade_price", "trade_condition_id",
    "canceled_trade_condition_id", "best_bid_size", "best_bid",
    "best_ask", "best_ask_size", "underlying_bid", "underlying_ask",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def to_int(value: str | None) -> int | None:
    if value is None or not value.strip():
        return None
    return int(float(value))


def to_float(value: str | None) -> float | None:
    if value is None or not value.strip():
        return None
    return float(value)


def parse_market_date(value: str):
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y%m%d"):
        try:
            return datetime.strptime(value, fmt).date(), fmt
        except ValueError:
            continue
    return None, None


def classify_quote_datetime(value: str):
    value = value.strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?", value):
        try:
            return "full_datetime", datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return "unrecognized", None
    if re.fullmatch(r"\d{2}:\d{2}\.\d+", value):
        return "two_component_clock", None
    if re.fullmatch(r"\d{2}:\d{2}:\d{2}(?:\.\d+)?", value):
        return "time_only", None
    return "unrecognized", None


def parse_trade_csv(payload: bytes) -> dict[str, Any]:
    text = payload.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    fields = [str(x).strip().lower() for x in (reader.fieldnames or [])]
    field_set = set(fields)
    missing = sorted(REQUIRED - field_set)
    rows = []
    errors = Counter()
    exchanges = Counter()
    conditions = Counter()
    underlyings = set()
    roots = set()
    series = set()
    sequence_keys = []
    quote_states = Counter()
    trade_locations = Counter()
    date_values = set()
    optional_calcs = Counter()
    timestamp_mismatch = 0
    full_datetime_count = 0
    quote_time_formats = Counter()
    market_date_formats = Counter()

    for row_no, raw in enumerate(reader, start=2):
        row = {str(k).strip().lower(): (v or "").strip() for k, v in raw.items() if k is not None}
        if not row or not any(row.values()):
            continue
        try:
            underlying = row["underlying_symbol"]
            market_date = row["market_date"]
            quote_raw = row["quote_datetime"]
            quote_format, quote_dt = classify_quote_datetime(quote_raw)
            quote_time_formats[quote_format] += 1
            sequence = to_int(row["sequence_number"])
            root = row["root"]
            expiration = row["expiration"]
            strike = to_float(row["strike"])
            option_type = row["option_type"].upper()
            exchange_id = to_int(row["exchange_id"])
            size = to_int(row["trade_size"])
            price = to_float(row["trade_price"])
            condition = to_int(row["trade_condition_id"])
            bid = to_float(row["best_bid"])
            ask = to_float(row["best_ask"])
            bid_size = to_int(row["best_bid_size"])
            ask_size = to_int(row["best_ask_size"])
        except KeyError as exc:
            errors["missing_field:" + str(exc)] += 1
            continue
        except (ValueError, TypeError) as exc:
            errors["parse_error:" + str(exc)[:80]] += 1
            continue

        if not underlying:
            errors["blank_underlying"] += 1
        if not root:
            errors["blank_root"] += 1
        if option_type not in {"C", "P"}:
            errors["invalid_option_type"] += 1
        if sequence is None:
            errors["missing_sequence"] += 1
        if exchange_id is None:
            errors["missing_exchange_id"] += 1
        if size is None or size <= 0:
            errors["invalid_trade_size"] += 1
        if price is None or price < 0:
            errors["invalid_trade_price"] += 1
        if strike is None or strike < 0:
            errors["invalid_strike"] += 1
        if condition is None:
            errors["missing_trade_condition"] += 1

        market_dt, market_fmt = parse_market_date(market_date)
        if market_dt is None:
            errors["invalid_market_date"] += 1
        else:
            market_date_formats[market_fmt] += 1
            date_values.add(market_dt.isoformat())
            if quote_dt is not None:
                full_datetime_count += 1
                if quote_dt.date() != market_dt:
                    timestamp_mismatch += 1

        if bid is None or ask is None or bid <= 0 or ask <= 0:
            quote_states["zero_or_missing_nbbo"] += 1
            location = "unclassified_invalid_nbbo"
        elif ask < bid:
            quote_states["crossed_nbbo"] += 1
            location = "unclassified_crossed_nbbo"
        elif ask == bid:
            quote_states["locked_nbbo"] += 1
            if price is not None and price >= ask:
                location = "at_or_above_locked"
            else:
                location = "at_or_below_locked"
        else:
            quote_states["valid_nbbo"] += 1
            if price is None:
                location = "unclassified_missing_price"
            elif price >= ask:
                location = "at_or_above_ask"
            elif price <= bid:
                location = "at_or_below_bid"
            elif abs(price - (bid + ask) / 2.0) < 1e-9:
                location = "exact_midpoint"
            else:
                location = "inside_spread"
        trade_locations[location] += 1

        underlyings.add(underlying)
        roots.add(root)
        series.add((underlying, root, expiration, strike, option_type))
        if exchange_id is not None:
            exchanges[str(exchange_id)] += 1
        if condition is not None:
            conditions[str(condition)] += 1
        if sequence is not None and market_dt is not None and exchange_id is not None:
            sequence_keys.append((market_dt.isoformat(), sequence, exchange_id))

        for field in ("trade_iv", "trade_delta", "trade_gamma", "trade_vega", "trade_theta", "trade_rho"):
            if field in row:
                if row[field] and row[field] != "0":
                    optional_calcs[field + "_nonzero"] += 1
                optional_calcs[field + "_present"] += 1

        rows.append(row)

    duplicate_count = len(sequence_keys) - len(set(sequence_keys))
    key_text = "\n".join(sorted(f"{d}|{seq}|{ex}" for d, seq, ex in sequence_keys))
    sequence_key_sha256 = hashlib.sha256(key_text.encode("utf-8")).hexdigest()
    return {
        "fields": fields,
        "raw_sample_lines": text.splitlines()[:6],
        "missing_required_fields": missing,
        "row_count": len(rows),
        "unique_underlyings": len(underlyings),
        "unique_roots": len(roots),
        "unique_option_series": len(series),
        "market_dates": sorted(date_values),
        "timestamp_calendar_date_mismatch_count": timestamp_mismatch,
        "quote_datetime_full_parseable_count": full_datetime_count,
        "quote_datetime_format_counts": dict(quote_time_formats),
        "market_date_format_counts": dict(market_date_formats),
        "exchange_id_counts": dict(exchanges),
        "trade_condition_counts": dict(conditions),
        "quote_state_counts": dict(quote_states),
        "trade_location_counts": dict(trade_locations),
        "sequence_key_duplicate_count": duplicate_count,
        "sequence_key_sha256": sequence_key_sha256,
        "optional_calcs": dict(optional_calcs),
        "errors": dict(errors),
        "sample_rows": rows[:5],
    }


def download(session: requests.Session, url: str, timeout: int = 120) -> tuple[int | None, dict[str, str], bytes, str | None]:
    try:
        response = session.get(url, timeout=timeout)
        return response.status_code, dict(response.headers), response.content, None
    except requests.RequestException as exc:
        return None, {}, b"", type(exc).__name__


def collect_csv_payloads(payload: bytes, prefix: str = "", depth: int = 0) -> tuple[list[tuple[str, bytes]], list[dict[str, Any]]]:
    found: list[tuple[str, bytes]] = []
    entries: list[dict[str, Any]] = []
    if depth > 3:
        return found, entries
    try:
        with zipfile.ZipFile(io.BytesIO(payload)) as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue
                data = zf.read(info.filename)
                name = f"{prefix}{info.filename}"
                entries.append({"name": name, "bytes": len(data)})
                if zipfile.is_zipfile(io.BytesIO(data)):
                    nested_found, nested_entries = collect_csv_payloads(data, prefix=name + "!", depth=depth + 1)
                    found.extend(nested_found)
                    entries.extend(nested_entries)
                    continue
                if data[:2] == b"\x1f\x8b":
                    try:
                        data = gzip.decompress(data)
                        name = name.removesuffix(".gz")
                    except OSError:
                        pass
                first_line = data.splitlines()[0].decode("utf-8-sig", errors="replace").lower() if data.splitlines() else ""
                if "underlying_symbol" in first_line and "," in first_line:
                    found.append((name, data))
    except zipfile.BadZipFile:
        pass
    return found, entries


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="phase112_cboe_option_trades_output")
    args = parser.parse_args()
    out = Path(args.output)
    raw_dir = out / "raw"
    extract_dir = out / "extracted"
    raw_dir.mkdir(parents=True, exist_ok=True)
    extract_dir.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers.update({
        "User-Agent": "NuevaEstrategia-Research/Phase112",
        "Accept": "*/*",
    })

    artifacts = {}
    sample_status, sample_headers, sample_bytes, sample_error = download(session, SAMPLE_URL)
    (raw_dir / "cboe_option_trades_sample.zip").write_bytes(sample_bytes)
    artifacts["sample_zip"] = {
        "url": SAMPLE_URL,
        "http_status": sample_status,
        "content_type": sample_headers.get("Content-Type"),
        "last_modified": sample_headers.get("Last-Modified"),
        "bytes": len(sample_bytes),
        "sha256": sha256(sample_bytes),
        "error": sample_error,
    }

    csv_results = []
    zip_error = None
    zip_entries = []
    if sample_status == 200:
        try:
            csv_payloads, zip_entries = collect_csv_payloads(sample_bytes)
            for index, (filename, data) in enumerate(csv_payloads):
                target = extract_dir / f"sample_{index}_{Path(filename.split('!')[-1]).name}"
                target.write_bytes(data)
                parsed = parse_trade_csv(data)
                csv_results.append({
                    "file": filename,
                    "bytes": len(data),
                    "sha256": sha256(data),
                    "audit": parsed,
                })
        except (zipfile.BadZipFile, OSError) as exc:
            zip_error = type(exc).__name__

    mapping_results = {}
    for label, url, filename in (
        ("exchange_mapping", EXCHANGE_MAP_URL, "livevol_exchange_ids.csv"),
        ("trade_condition_mapping", CONDITION_MAP_URL, "livevol_trade_condition_ids.xlsx"),
    ):
        status, headers, data, error = download(session, url)
        (raw_dir / filename).write_bytes(data)
        mapping_results[label] = {
            "url": url,
            "http_status": status,
            "content_type": headers.get("Content-Type"),
            "bytes": len(data),
            "sha256": sha256(data),
            "error": error,
        }

    variant_match = None
    if len(csv_results) >= 2:
        calcs = next((x for x in csv_results if "Calcs" in x["file"]), None)
        base = next((x for x in csv_results if "Calcs" not in x["file"]), None)
        if calcs and base:
            variant_match = {
                "row_count_match": calcs["audit"]["row_count"] == base["audit"]["row_count"],
                "sequence_key_hash_match": calcs["audit"]["sequence_key_sha256"] == base["audit"]["sequence_key_sha256"],
                "calcs_rows": calcs["audit"]["row_count"],
                "base_rows": base["audit"]["row_count"],
            }

    schema_pass = (
        sample_status == 200
        and len(csv_results) > 0
        and all(
            item["audit"]["row_count"] > 0
            and not item["audit"]["missing_required_fields"]
            and not item["audit"]["errors"]
            for item in csv_results
        )
    )
    summary = {
        "phase": 112,
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "product": "Cboe Option Trades",
        "sample": artifacts["sample_zip"],
        "zip_error": zip_error,
        "zip_entries": zip_entries,
        "csv_results": csv_results,
        "calcs_vs_base_variant_match": variant_match,
        "mappings": mapping_results,
        "data_gate": "PASS_SAMPLE_SCHEMA" if schema_pass else "FAIL_OR_INCOMPLETE_SAMPLE",
        "limitations": [
            "Public sample is not a full-market coverage audit.",
            "Trade direction is not supplied; NBBO-relative location is descriptive only.",
            "Trade-condition exclusions and correction handling are not yet preregistered.",
            "No historical files were purchased and no vendor was contacted.",
        ],
    }
    (out / "phase112_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

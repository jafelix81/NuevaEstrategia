#!/usr/bin/env python3
"""Phase 174: public Cboe Option Quotes / Option Quote Intervals sample audit.

The auditor stores aggregate metadata only. It does not persist raw option rows,
underlying symbols, option roots, strikes, expirations, or contract-level keys.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import math
import re
import urllib.request
import zipfile
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any

SAMPLE_URL = "https://datashop.cboe.com/download/sample/215"
PRODUCT_URL = "https://datashop.cboe.com/option-quote-intervals"
SPEC_URL = "https://datashop.cboe.com/documents/Option_Quotes_Layout.pdf"
FAQ_URL = "https://datashop.cboe.com/faqs"

BASE_REQUIRED = (
    "underlying_symbol", "quote_datetime", "root", "expiration", "strike",
    "option_type", "open", "high", "low", "close", "trade_volume",
    "bid_size", "bid", "ask_size", "ask", "underlying_bid", "underlying_ask",
)
CALCS_FIELDS = (
    "active_underlying_price", "implied_volatility", "delta", "gamma",
    "theta", "vega", "rho",
)
OPTIONAL_FIELDS = {"open_interest", "implied_underlying_price"}
DEPRECATED_FIELDS = {"implied_underlying_price", "number_of_exchanges", "level2"}
KNOWN_FIELDS = set(BASE_REQUIRED) | set(CALCS_FIELDS) | OPTIONAL_FIELDS | DEPRECATED_FIELDS | {
    "trade_date", "quote_date", "interval", "interval_minutes", "source"
}
NONNEGATIVE_NUMERIC = {
    "open", "high", "low", "close", "bid", "ask", "underlying_bid",
    "underlying_ask", "active_underlying_price", "implied_underlying_price",
    "implied_volatility",
}
INTEGER_FIELDS = {"trade_volume", "bid_size", "ask_size", "open_interest"}


def normalize_header(value: str) -> str:
    return str(value or "").replace("\ufeff", "").strip().lower()


def parse_quote_datetime(value: str) -> datetime:
    raw = str(value or "").strip()
    if not raw:
        raise ValueError("missing_quote_datetime")
    # Cboe documents an ET wall-clock end-of-interval timestamp without a zone.
    if raw.endswith("Z") or "+" in raw[10:] or ("-" in raw[10:] and raw.count("-") > 2):
        raise ValueError("unexpected_timezone_in_et_wall_clock")
    parsed = datetime.fromisoformat(raw.replace("T", " "))
    if parsed.tzinfo is not None:
        raise ValueError("unexpected_timezone_in_et_wall_clock")
    return parsed


def parse_expiration(value: str) -> date:
    raw = str(value or "").strip()
    if not raw:
        raise ValueError("missing_expiration")
    try:
        return date.fromisoformat(raw)
    except ValueError as exc:
        # Do not leak Python's raw exception text or silently guess a locale.
        raise ValueError("invalid_expiration_format") from exc


def expiration_format_candidates(value: str) -> tuple[str, ...]:
    """Return diagnostic parse candidates only; never selects a non-ISO format."""
    raw = str(value or "").strip()
    if not raw:
        return ()
    candidates = (
        ("iso_extended", "%Y-%m-%d"),
        ("iso_basic", "%Y%m%d"),
        ("us_slash", "%m/%d/%Y"),
        ("dmy_slash", "%d/%m/%Y"),
        ("year_slash", "%Y/%m/%d"),
        ("us_dash", "%m-%d-%Y"),
    )
    matched = []
    for label, fmt in candidates:
        try:
            datetime.strptime(raw, fmt)
        except ValueError:
            continue
        matched.append(label)
    return tuple(matched)


def parse_number(value: str, field: str) -> float | None:
    raw = str(value or "").strip()
    if raw == "":
        return None
    try:
        number = float(raw)
    except ValueError as exc:
        raise ValueError(f"invalid_numeric:{field}") from exc
    if not math.isfinite(number):
        raise ValueError(f"nonfinite_numeric:{field}")
    if field in NONNEGATIVE_NUMERIC and number < 0:
        raise ValueError(f"negative_numeric:{field}")
    return number


def parse_integer(value: str, field: str) -> int | None:
    raw = str(value or "").strip()
    if raw == "":
        return None
    try:
        number = int(raw)
    except ValueError as exc:
        raise ValueError(f"invalid_integer:{field}") from exc
    if number < 0:
        raise ValueError(f"negative_integer:{field}")
    return number


def _contract_key(row: dict[str, str]) -> tuple[str, str, str, str, str]:
    # Used only in memory; never emitted to artifacts.
    return (
        row["underlying_symbol"].strip(), row["root"].strip(),
        row["expiration"].strip(), row["strike"].strip(),
        row["option_type"].strip().upper(),
    )


def audit_csv_bytes(data: bytes, member_index: int = 0) -> dict[str, Any]:
    text = data.decode("utf-8-sig")
    reader = csv.reader(io.StringIO(text, newline=""))
    try:
        raw_header = next(reader)
    except StopIteration:
        return {"member_index": member_index, "status": "EMPTY_CSV", "row_gate_pass": False}
    header = [normalize_header(x) for x in raw_header]
    if not header or any(not x for x in header) or len(set(header)) != len(header):
        return {"member_index": member_index, "status": "INVALID_OR_DUPLICATE_HEADER", "row_gate_pass": False}

    missing = sorted(set(BASE_REQUIRED) - set(header))
    unknown = sorted(set(header) - KNOWN_FIELDS)
    calcs_present = set(CALCS_FIELDS).issubset(header)
    oi_present = "open_interest" in header
    header_ok = not missing and not unknown
    if missing:
        return {
            "member_index": member_index, "status": "MISSING_REQUIRED_HEADER_FIELDS",
            "header_columns": len(header), "missing_required_fields": missing,
            "unknown_fields": unknown,
            "deprecated_fields_present": sorted(set(header) & DEPRECATED_FIELDS),
            "calcs_present": calcs_present, "open_interest_present": oi_present,
            "populated_rows": 0, "empty_rows": 0, "row_gate_pass": False,
            "schema_gate_pass": False, "raw_symbols_persisted": False,
            "raw_rows_persisted": False,
        }

    row_count = empty_rows = short_rows = long_rows = 0
    invalid_timestamp = invalid_contract = numeric_errors = 0
    bid_gt_ask = zero_iv_nonzero_greeks = zero_oi = zero_volume = 0
    duplicate_keys = 0
    keys: set[tuple[Any, ...]] = set()
    underlyings: set[str] = set()
    quote_times: set[datetime] = set()
    quote_dates: set[date] = set()
    series: set[tuple[str, str, str, str, str]] = set()
    oi_by_contract_day: dict[tuple[Any, ...], set[int]] = defaultdict(set)
    error_codes: Counter[str] = Counter()
    populated_field_counts: Counter[int] = Counter()
    timestamp_shapes: Counter[str] = Counter()
    expiration_shapes: Counter[str] = Counter()
    expiration_candidate_counts: Counter[str] = Counter()

    for values in reader:
        if not values or all(str(x).strip() == "" for x in values):
            empty_rows += 1
            continue
        row_count += 1
        populated_field_counts[sum(str(x).strip() != "" for x in values)] += 1
        if len(values) < len(header):
            short_rows += 1
            error_codes["short_row"] += 1
            continue
        if len(values) > len(header):
            long_rows += 1
            error_codes["long_row"] += 1
            continue
        row = dict(zip(header, values))
        raw_qdt = str(row.get("quote_datetime", "")).strip()
        if raw_qdt:
            shape = re.sub(r"[A-Za-z]", "A", re.sub(r"\d", "9", raw_qdt))[:64]
            timestamp_shapes[shape] += 1
        raw_expiration = str(row.get("expiration", "")).strip()
        if raw_expiration:
            expiration_shape = re.sub(r"[A-Za-z]", "A", re.sub(r"\d", "9", raw_expiration))[:64]
            expiration_shapes[expiration_shape] += 1
            for candidate in expiration_format_candidates(raw_expiration):
                expiration_candidate_counts[candidate] += 1
        try:
            if any(not str(row.get(k, "")).strip() for k in
                   ("underlying_symbol", "root", "expiration", "strike", "option_type")):
                raise ValueError("missing_contract_identity")
            if row["option_type"].strip().upper() not in {"C", "P"}:
                raise ValueError("invalid_option_type")
            parse_expiration(row["expiration"])
            strike = parse_number(row["strike"], "strike")
            if strike is None or strike <= 0:
                raise ValueError("invalid_strike")
        except ValueError as exc:
            code = str(exc).split(":", 1)[0]
            invalid_contract += 1
            error_codes[code] += 1
            continue
        try:
            qdt = parse_quote_datetime(raw_qdt)
        except ValueError as exc:
            code = str(exc).split(":", 1)[0]
            invalid_timestamp += 1
            error_codes[code] += 1
            continue

        numeric_row: dict[str, float | int | None] = {}
        try:
            for field in set(header) & INTEGER_FIELDS:
                numeric_row[field] = parse_integer(row.get(field, ""), field)
            for field in (set(header) - INTEGER_FIELDS) & (set(BASE_REQUIRED) | set(CALCS_FIELDS) | OPTIONAL_FIELDS):
                if field in {"underlying_symbol", "quote_datetime", "root", "expiration", "option_type"}:
                    continue
                numeric_row[field] = parse_number(row.get(field, ""), field)
        except ValueError as exc:
            numeric_errors += 1
            error_codes[str(exc).split(":", 1)[0]] += 1
            continue

        bid, ask = numeric_row.get("bid"), numeric_row.get("ask")
        if bid is not None and ask is not None and bid > 0 and ask > 0 and bid > ask:
            bid_gt_ask += 1
        iv = numeric_row.get("implied_volatility")
        greek_values = [numeric_row.get(x) for x in ("delta", "gamma", "theta", "vega", "rho")]
        if iv == 0 and any(v not in (None, 0) for v in greek_values):
            zero_iv_nonzero_greeks += 1
        oi, volume = numeric_row.get("open_interest"), numeric_row.get("trade_volume")
        if oi == 0:
            zero_oi += 1
        if volume == 0:
            zero_volume += 1

        ckey = _contract_key(row)
        series.add(ckey)
        underlyings.add(row["underlying_symbol"].strip())
        quote_times.add(qdt)
        quote_dates.add(qdt.date())
        full_key = ckey + (qdt.isoformat(),)
        if full_key in keys:
            duplicate_keys += 1
        else:
            keys.add(full_key)
        if oi is not None:
            oi_by_contract_day[ckey + (qdt.date().isoformat(),)].add(int(oi))

    interval_counts = Counter()
    sorted_times = sorted(quote_times)
    for left, right in zip(sorted_times, sorted_times[1:]):
        seconds = int((right - left).total_seconds())
        if seconds > 0:
            interval_counts[seconds] += 1
    inconsistent_oi_groups = sum(1 for values in oi_by_contract_day.values() if len(values) > 1)
    row_gate_pass = (
        row_count > 0 and short_rows == 0 and long_rows == 0
        and invalid_timestamp == 0 and invalid_contract == 0
        and numeric_errors == 0 and duplicate_keys == 0
    )
    schema_gate_pass = header_ok and row_gate_pass
    return {
        "member_index": member_index,
        "status": "PASS" if schema_gate_pass else "DIAGNOSTIC_COMPLETE_ROW_OR_SCHEMA_GATE_FAIL",
        "header_columns": len(header), "missing_required_fields": missing,
        "unknown_fields": unknown,
        "deprecated_fields_present": sorted(set(header) & DEPRECATED_FIELDS),
        "calcs_present": calcs_present, "open_interest_present": oi_present,
        "populated_rows": row_count, "empty_rows": empty_rows,
        "short_rows": short_rows, "long_rows": long_rows,
        "invalid_timestamp_rows": invalid_timestamp,
        "quote_datetime_shape_counts": dict(sorted(timestamp_shapes.items())),
        "expiration_shape_counts": dict(sorted(expiration_shapes.items())),
        "expiration_candidate_format_counts": dict(sorted(expiration_candidate_counts.items())),
        "invalid_contract_rows": invalid_contract, "numeric_error_rows": numeric_errors,
        "duplicate_contract_interval_keys": duplicate_keys,
        "underlying_count": len(underlyings), "unique_series_count": len(series),
        "quote_date_count": len(quote_dates),
        "quote_dates_min": min(quote_dates).isoformat() if quote_dates else None,
        "quote_dates_max": max(quote_dates).isoformat() if quote_dates else None,
        "unique_interval_timestamps": len(quote_times),
        "modal_interval_seconds": interval_counts.most_common(1)[0][0] if interval_counts else None,
        "interval_gap_counts_top5": [{"seconds": k, "count": v} for k, v in interval_counts.most_common(5)],
        "bid_above_ask_rows": bid_gt_ask,
        "zero_iv_nonzero_greeks_rows": zero_iv_nonzero_greeks,
        "zero_open_interest_rows": zero_oi, "zero_trade_volume_rows": zero_volume,
        "contract_days_with_inconsistent_sod_oi": inconsistent_oi_groups,
        "row_gate_pass": row_gate_pass, "schema_gate_pass": schema_gate_pass,
        "error_code_counts": dict(sorted(error_codes.items())),
        "populated_field_count_distribution": {str(k): v for k, v in sorted(populated_field_counts.items())},
        "raw_symbols_persisted": False, "raw_rows_persisted": False,
    }


def _extension_chain(name: str) -> str:
    suffixes = Path(name).suffixes
    return "".join(suffixes[-2:]).lower() if suffixes else "[none]"


def _looks_like_option_csv(payload: bytes) -> bool:
    try:
        first_line = payload.decode("utf-8-sig").splitlines()[0]
        header = [normalize_header(x) for x in next(csv.reader([first_line]))]
    except (UnicodeDecodeError, IndexError, StopIteration):
        return False
    return len(set(header) & set(BASE_REQUIRED)) >= 5


def _walk_archive_member(name: str, payload: bytes, depth: int, counter: list[int],
                         metadata: list[dict[str, Any]], data_members: list[dict[str, Any]]) -> None:
    if depth > 3:
        raise ValueError("nested_archive_depth_exceeded")
    counter[0] += 1
    if counter[0] > 500:
        raise ValueError("too_many_nested_archive_members")
    if payload.startswith(b"PK\x03\x04"):
        metadata.append({"member_index": counter[0], "extension_chain": _extension_chain(name),
                         "container_type": "zip", "bytes": len(payload)})
        with zipfile.ZipFile(io.BytesIO(payload)) as nested:
            for info in nested.infolist():
                if info.is_dir():
                    continue
                if info.file_size > 500_000_000:
                    raise ValueError("nested_member_too_large")
                _walk_archive_member(info.filename, nested.read(info), depth + 1,
                                     counter, metadata, data_members)
        return
    if payload.startswith(b"\x1f\x8b"):
        metadata.append({"member_index": counter[0], "extension_chain": _extension_chain(name),
                         "container_type": "gzip", "bytes": len(payload)})
        expanded = gzip.decompress(payload)
        if len(expanded) > 500_000_000:
            raise ValueError("gzip_member_too_large")
        inner_name = name[:-3] if name.lower().endswith(".gz") else name + ".decompressed"
        _walk_archive_member(inner_name, expanded, depth + 1, counter, metadata, data_members)
        return
    if _looks_like_option_csv(payload):
        audit = audit_csv_bytes(payload, len(data_members))
        audit["extension_chain"] = _extension_chain(name)
        audit["uncompressed_bytes"] = len(payload)
        audit["raw_member_name_persisted"] = False
        data_members.append(audit)
        metadata.append({"member_index": counter[0], "extension_chain": _extension_chain(name),
                         "container_type": "option_csv_candidate", "bytes": len(payload)})
    else:
        try:
            payload.decode("utf-8-sig")
            kind = "text_non_option_csv"
        except UnicodeDecodeError:
            kind = "binary_non_data"
        metadata.append({"member_index": counter[0], "extension_chain": _extension_chain(name),
                         "container_type": kind, "bytes": len(payload)})


def audit_archive(payload: bytes) -> dict[str, Any]:
    result: dict[str, Any] = {
        "phase": 174, "source": "Cboe Option Quotes / Option Quote Intervals",
        "sample_url": SAMPLE_URL, "download_status": "PASS",
        "archive_bytes": len(payload), "archive_sha256": hashlib.sha256(payload).hexdigest(),
        "members": [], "archive_member_metadata": [], "sample_schema_gate_pass": False,
        "sample_admission": False, "pit_admission": False, "alpha_admission": False,
        "first_receipt_vintages_verified": False,
        "broad_pit_universe_coverage_verified": False,
        "license_and_price_verified": False, "forward_returns_tested": False,
        "bootstrap_loo_tested": False, "chronological_oos_tested": False,
        "final_holdout_used": False, "production_changed": False, "f80_changed": False,
    }
    if not payload.startswith(b"PK\x03\x04"):
        raise ValueError("sample_not_zip")
    with zipfile.ZipFile(io.BytesIO(payload)) as zf:
        infos = [i for i in zf.infolist() if not i.is_dir()]
        if len(infos) > 100:
            raise ValueError("too_many_archive_members")
        result["archive_member_count"] = len(infos)
        counter = [0]
        for info in infos:
            if info.file_size > 500_000_000:
                raise ValueError("archive_member_too_large")
            _walk_archive_member(info.filename, zf.read(info), 0, counter,
                                 result["archive_member_metadata"], result["members"])
    result["archive_node_count"] = counter[0]
    result["data_member_count"] = len(result["members"])
    result["total_populated_rows"] = sum(m.get("populated_rows", 0) for m in result["members"])
    result["total_invalid_timestamp_rows"] = sum(m.get("invalid_timestamp_rows", 0) for m in result["members"])
    result["total_invalid_contract_rows"] = sum(m.get("invalid_contract_rows", 0) for m in result["members"])
    result["schema_variant_counts"] = dict(Counter(
        f"{m.get('header_columns')}cols_calcs{int(m.get('calcs_present', False))}_oi{int(m.get('open_interest_present', False))}"
        for m in result["members"]
    ))
    result["container_type_counts"] = dict(Counter(x["container_type"] for x in result["archive_member_metadata"]))
    result["extension_chain_counts"] = dict(Counter(x["extension_chain"] for x in result["archive_member_metadata"]))
    result["sample_schema_gate_pass"] = bool(result["members"]) and all(
        m.get("schema_gate_pass", False) for m in result["members"]
    )
    result["overall_status"] = (
        "SAMPLE_SCHEMA_PASS_PIT_BLOCKED" if result["sample_schema_gate_pass"]
        else "DIAGNOSTIC_COMPLETE_SAMPLE_GATE_FAIL"
    )
    return result

def download_sample(timeout: int = 45, max_bytes: int = 200_000_000) -> bytes:
    request = urllib.request.Request(
        SAMPLE_URL,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; NuevaEstrategia-Research/1.0)",
            "Accept": "application/zip, application/octet-stream, */*",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        content_type = response.headers.get("Content-Type", "").lower()
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > max_bytes:
                raise ValueError("sample_download_exceeds_size_limit")
            chunks.append(chunk)
    payload = b"".join(chunks)
    if not payload.startswith(b"PK\x03\x04"):
        raise ValueError(f"sample_not_zip:{content_type or 'unknown_content_type'}")
    return payload


def build_blocked_audit(error: Exception) -> dict[str, Any]:
    return {
        "phase": 174, "source": "Cboe Option Quotes / Option Quote Intervals",
        "sample_url": SAMPLE_URL, "download_status": "BLOCKED",
        "download_error_class": type(error).__name__,
        "download_error_code": str(error).split(":", 1)[0][:100],
        "sample_schema_gate_pass": False, "sample_admission": False,
        "pit_admission": False, "alpha_admission": False,
        "first_receipt_vintages_verified": False,
        "broad_pit_universe_coverage_verified": False,
        "license_and_price_verified": False, "forward_returns_tested": False,
        "bootstrap_loo_tested": False, "chronological_oos_tested": False,
        "final_holdout_used": False, "production_changed": False, "f80_changed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="phase174_output/phase174_cboe_option_quotes_sample_audit.json")
    parser.add_argument("--no-download", action="store_true")
    args = parser.parse_args()
    try:
        result = (
            {"phase": 174, "source": "Cboe Option Quotes / Option Quote Intervals",
             "download_status": "SKIPPED", "sample_schema_gate_pass": False,
             "sample_admission": False, "pit_admission": False, "alpha_admission": False,
             "forward_returns_tested": False, "final_holdout_used": False,
             "production_changed": False, "f80_changed": False}
            if args.no_download else audit_archive(download_sample())
        )
    except Exception as exc:
        result = build_blocked_audit(exc)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

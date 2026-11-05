#!/usr/bin/env python3
"""Phase 136: audit the public Cboe Volatility Surfaces sample.

Only aggregate schema/quality metadata is written. Raw sample files and symbol
lists are never uploaded as workflow artifacts.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import time
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

SAMPLE_URL = "https://datashop.cboe.com/download/sample/281"
OUT_DIR = Path("phase136_cboe_volatility_surface_sample_audit")
USER_AGENT = "Mozilla/5.0 (compatible; NuevaEstrategiaResearch/1.0)"
NEGATIVE_CONFIDENCE_CODES = {-1.0, -2.0, -5.0, -6.0}


def norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value or "").lower())


def parse_num(value):
    if value is None or str(value).strip() == "":
        return None
    try:
        number = float(str(value).strip().replace(",", ""))
    except (TypeError, ValueError):
        return None
    return number if number == number and abs(number) != float("inf") else None


def parse_time(value: str) -> bool:
    value = str(value or "").strip()
    for fmt in ("%H:%M:%S.%f", "%H:%M:%S"):
        try:
            datetime.strptime(value, fmt)
            return True
        except ValueError:
            pass
    return False


def classify_surface(headers, filename: str) -> str | None:
    text = norm(filename)
    if "expiration" in text and "delta" in text:
        return "expiration_specific_delta"
    if "expiration" in text and "price" in text:
        return "expiration_specific_price"
    if "constantmaturity" in text and "delta" in text:
        return "constant_maturity_delta"
    if "constantmaturity" in text and "price" in text:
        return "constant_maturity_price"
    keys = {norm(x) for x in headers}
    has_delta = any(x.startswith("iv") and "delta" in x for x in keys)
    has_price = any(x.startswith("iv") and "price" in x for x in keys)
    if "maturity" in keys:
        if has_delta:
            return "constant_maturity_delta"
        if has_price:
            return "constant_maturity_price"
    if "expiry" in keys or "expiration" in keys:
        if has_delta:
            return "expiration_specific_delta"
        if has_price:
            return "expiration_specific_price"
    return None


def inspect_csv(payload: bytes, filename: str) -> dict:
    text = payload.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    raw_headers = reader.fieldnames or []
    headers = [norm(x) for x in raw_headers]
    mapping = {norm(x): x for x in raw_headers}
    kind = classify_surface(raw_headers, filename)
    rows = list(reader)
    iv_cols = [mapping[x] for x in headers if x.startswith("iv") and x in mapping]
    strike_cols = [mapping[x] for x in headers if x.startswith("strike") and x in mapping]
    conf_cols = [mapping[x] for x in headers if x.startswith("conf") and x in mapping]
    symbol_col = mapping.get("underlyingsymbol")
    time_col = mapping.get("timestamp")
    price_col = mapping.get("underlyingprice")
    expiry_col = mapping.get("expiry") or mapping.get("expiration")
    maturity_col = mapping.get("maturity")
    required = [symbol_col, time_col, price_col, (expiry_col or maturity_col)]
    schema_ok = bool(kind and all(required) and len(iv_cols) >= 3 and len(strike_cols) >= 3 and len(conf_cols) >= 3)

    symbols = set()
    times = Counter()
    valid_times = 0
    valid_iv = invalid_iv = 0
    valid_strike = invalid_strike = 0
    valid_conf = invalid_conf = low_conf = negative_codes = 0
    valid_underlying_price = invalid_underlying_price = 0
    keys = []
    for row in rows:
        row_norm = {norm(k): (v or "").strip() for k, v in row.items() if k is not None}
        symbol = row_norm.get("underlyingsymbol", "").upper()
        if symbol:
            symbols.add(symbol)
        stamp = row_norm.get("timestamp", "")
        if stamp:
            times[stamp] += 1
            valid_times += int(parse_time(stamp))
        for col in iv_cols:
            value = parse_num(row.get(col))
            if value is None or value <= 0:
                invalid_iv += 1
            else:
                valid_iv += 1
        for col in strike_cols:
            value = parse_num(row.get(col))
            if value is None or value <= 0:
                invalid_strike += 1
            else:
                valid_strike += 1
        for col in conf_cols:
            value = parse_num(row.get(col))
            if value is None:
                invalid_conf += 1
            elif 0.0 <= value <= 1.0 or value in NEGATIVE_CONFIDENCE_CODES:
                valid_conf += 1
                if 0.0 <= value < 0.5:
                    low_conf += 1
                if value in NEGATIVE_CONFIDENCE_CODES:
                    negative_codes += 1
            else:
                invalid_conf += 1
        if price_col:
            value = parse_num(row.get(price_col))
            if value is None or value < 0:
                invalid_underlying_price += 1
            else:
                valid_underlying_price += 1
        key_parts = [
            symbol,
            row_norm.get("expiry", row_norm.get("expiration", "")),
            row_norm.get("maturity", ""),
            stamp,
        ]
        if symbol and stamp:
            keys.append("|".join(key_parts))
    unique_keys = set(keys)
    return {
        "filename": Path(filename).name,
        "sha256": hashlib.sha256(payload).hexdigest(),
        "bytes": len(payload),
        "surface_type": kind,
        "schema_ok": schema_ok,
        "row_count": len(rows),
        "underlying_count": len(symbols),
        "timestamp_valid_rows": valid_times,
        "timestamp_nonblank_rows": sum(times.values()),
        "timestamp_values": dict(sorted(times.items())),
        "iv_cells_valid": valid_iv,
        "iv_cells_invalid": invalid_iv,
        "strike_cells_valid": valid_strike,
        "strike_cells_invalid": invalid_strike,
        "confidence_cells_valid": valid_conf,
        "confidence_cells_invalid": invalid_conf,
        "confidence_below_0_5_cells": low_conf,
        "negative_confidence_code_cells": negative_codes,
        "underlying_price_valid_rows": valid_underlying_price,
        "underlying_price_invalid_rows": invalid_underlying_price,
        "surface_key_rows": len(keys),
        "unique_surface_keys": len(unique_keys),
        "duplicate_surface_key_rows": len(keys) - len(unique_keys),
        "iv_valid_rate": valid_iv / (valid_iv + invalid_iv) if valid_iv + invalid_iv else 0.0,
        "confidence_domain_rate": valid_conf / (valid_conf + invalid_conf) if valid_conf + invalid_conf else 0.0,
        "timestamp_parse_rate": valid_times / sum(times.values()) if times else 0.0,
    }


def collect_csvs(raw: bytes):
    if not zipfile.is_zipfile(io.BytesIO(raw)):
        raise ValueError("public sample response is not a ZIP archive")
    records = []
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        bad_member = archive.testzip()
        if bad_member:
            raise ValueError(f"ZIP CRC failure: {bad_member}")
        for name in archive.namelist():
            if name.endswith("/"):
                continue
            data = archive.read(name)
            if zipfile.is_zipfile(io.BytesIO(data)):
                with zipfile.ZipFile(io.BytesIO(data)) as nested:
                    nested_bad = nested.testzip()
                    if nested_bad:
                        raise ValueError(f"nested ZIP CRC failure: {nested_bad}")
                    for nested_name in nested.namelist():
                        if nested_name.lower().endswith(".csv"):
                            records.append((f"{name}!{nested_name}", nested.read(nested_name)))
            elif name.lower().endswith(".csv"):
                records.append((name, data))
    return records


def fetch_sample() -> tuple[bytes, dict]:
    request = Request(SAMPLE_URL, headers={
        "User-Agent": USER_AGENT,
        "Accept": "application/zip,application/octet-stream,*/*",
    })
    last_error = None
    for attempt in range(1, 4):
        try:
            with urlopen(request, timeout=60) as response:
                raw = response.read()
                return raw, {
                    "http_status": response.status,
                    "content_type": response.headers.get("Content-Type"),
                    "http_date": response.headers.get("Date"),
                    "last_modified": response.headers.get("Last-Modified"),
                    "etag": response.headers.get("ETag"),
                    "bytes": len(raw),
                    "sha256": hashlib.sha256(raw).hexdigest(),
                    "attempts": attempt,
                    "final_url": response.geturl(),
                }
        except HTTPError as exc:
            last_error = f"HTTP{exc.code} {exc.reason}"
            if exc.code not in (408, 429, 500, 502, 503, 504):
                break
        except (URLError, TimeoutError, OSError, ValueError) as exc:
            last_error = f"{type(exc).__name__}: {exc}"
        if attempt < 3:
            time.sleep(attempt * 2)
    raise RuntimeError(last_error or "sample download failed")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    raw, http = fetch_sample()
    csvs = collect_csvs(raw)
    files = [inspect_csv(data, name) for name, data in csvs]
    expected = {
        "expiration_specific_delta",
        "expiration_specific_price",
        "constant_maturity_delta",
        "constant_maturity_price",
    }
    present = {item["surface_type"] for item in files if item["surface_type"]}
    all_files_valid = bool(files) and all(
        item["schema_ok"]
        and item["row_count"] > 0
        and item["timestamp_parse_rate"] >= 0.99
        and item["iv_valid_rate"] >= 0.95
        and item["confidence_domain_rate"] >= 0.99
        and item["duplicate_surface_key_rows"] == 0
        for item in files
    )
    gates = {
        "all_four_documented_surface_types_present": expected.issubset(present),
        "each_present_file_has_valid_schema_and_rows": all_files_valid,
    }
    summary = {
        "phase": 136,
        "status": "PASS_PUBLIC_SAMPLE_SCHEMA" if all(gates.values()) else "PARTIAL_OR_FAIL_PUBLIC_SAMPLE",
        "source_url": SAMPLE_URL,
        "http": http,
        "zip_csv_member_count": len(csvs),
        "surface_types_present": sorted(present),
        "file_results": files,
        "gate_checks": gates,
        "historical_coverage": "PRODUCT_PAGE_ADVERTISES_AUG_2011; SAMPLE_DOES_NOT_PROVE_DATE_COVERAGE",
        "point_in_time": "NOT_VERIFIED; calculation timestamp is not first-publication or file-receipt timestamp",
        "universe_coverage": "SAMPLE_ONLY; no broad PIT or inactive/delisted coverage claim",
        "raw_sample_retained": False,
        "raw_sample_uploaded": False,
        "forward_returns_used": False,
        "vendor_contact_or_purchase": False,
        "f80_baseline_frozen": True,
        "audit_timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }
    (OUT_DIR / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    with (OUT_DIR / "file_summary.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = sorted({key for item in files for key in item})
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for item in files:
            row = dict(item)
            row["timestamp_values"] = json.dumps(row.get("timestamp_values", {}), sort_keys=True)
            writer.writerow(row)
    print(json.dumps(summary, indent=2), flush=True)
    return 0 if all(gates.values()) else 2


if __name__ == "__main__":
    raise SystemExit(main())

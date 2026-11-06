#!/usr/bin/env python3
"""Phase 170: public Cboe Option Trades sample audit.

The sample is parsed in memory. Only hashes, schema/quality counts and
non-identifying aggregate metadata are written. No raw trades or symbols persist.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import time
import zipfile
from collections import Counter
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

SOURCE_URL = "https://datashop.cboe.com/download/sample/216"
MAX_COMPRESSED_BYTES = 100_000_000
MAX_UNCOMPRESSED_BYTES = 1_000_000_000
MAX_MEMBERS = 64
ET = ZoneInfo("America/New_York")

BASE_FIELDS = (
    "underlying_symbol", "market_date", "quote_datetime", "sequence_number",
    "root", "expiration", "strike", "option_type", "exchange_id", "trade_size",
    "trade_price", "trade_condition_id", "canceled_trade_condition_id",
    "best_bid_size", "best_bid", "best_ask", "best_ask_size",
    "underlying_bid", "underlying_ask",
)
CALCS_FIELDS = (
    "trade_iv", "trade_delta", "trade_gamma", "trade_vega", "trade_theta", "trade_rho",
)
OPTIONAL_LEGACY_FIELDS = ("number_of_exchanges",)
ALLOWED_FIELDS = frozenset(BASE_FIELDS + CALCS_FIELDS + OPTIONAL_LEGACY_FIELDS)

def _text(value: object) -> str:
    return "" if value is None else str(value).strip()

def _decimal(value: object, field: str, *, blank_ok: bool = False) -> Decimal | None:
    raw = _text(value)
    if not raw and blank_ok:
        return None
    try:
        out = Decimal(raw)
    except InvalidOperation as exc:
        raise ValueError(f"invalid_decimal:{field}") from exc
    if not out.is_finite():
        raise ValueError(f"nonfinite_decimal:{field}")
    return out

def _integer(value: object, field: str, *, blank_ok: bool = False) -> int | None:
    raw = _text(value)
    if not raw and blank_ok:
        return None
    if not re.fullmatch(r"-?\d+", raw):
        raise ValueError(f"invalid_integer:{field}")
    return int(raw)

def _market_date(value: object) -> date:
    try:
        return date.fromisoformat(_text(value))
    except ValueError as exc:
        raise ValueError("invalid_market_date") from exc

def _quote_datetime(value: object) -> datetime:
    raw = _text(value)
    parsed = None
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
        try:
            parsed = datetime.strptime(raw, fmt)
            break
        except ValueError:
            pass
    if parsed is None:
        raise ValueError("invalid_quote_datetime")
    return parsed.replace(tzinfo=ET)

def _safe_url(value: str) -> str:
    p = urlsplit(value)
    return f"{p.scheme}://{p.netloc}{p.path}"

def schema_check(headers: list[str]) -> dict[str, object]:
    normalized = [str(x).strip().lower() for x in headers]
    counts = Counter(normalized)
    duplicates = sorted(k for k, v in counts.items() if v > 1)
    observed = set(normalized)
    missing = sorted(set(BASE_FIELDS) - observed)
    extras = sorted(observed - ALLOWED_FIELDS)
    present_calcs = set(CALCS_FIELDS) & observed
    partial_calcs = bool(present_calcs) and present_calcs != set(CALCS_FIELDS)
    legacy_present = sorted(set(OPTIONAL_LEGACY_FIELDS) & observed)
    schema_ok = not duplicates and not missing and not extras and not partial_calcs
    return {
        "schema_status": "PASS" if schema_ok else "FAIL",
        "expected_base_columns": len(BASE_FIELDS),
        "expected_calcs_columns": len(CALCS_FIELDS),
        "observed_columns": len(normalized),
        "observed_column_names": normalized,
        "calcs_included": present_calcs == set(CALCS_FIELDS),
        "missing_columns": missing,
        "extra_columns": extras,
        "duplicate_columns": duplicates,
        "partial_calcs_group": partial_calcs,
        "optional_legacy_columns_present": legacy_present,
        "optional_legacy_columns_absent": sorted(set(OPTIONAL_LEGACY_FIELDS) - observed),
        "header_sha256": hashlib.sha256(",".join(normalized).encode("utf-8")).hexdigest(),
    }

def classify_trade_vs_nbbo(price: Decimal, bid: Decimal | None, ask: Decimal | None) -> str:
    if bid is None or ask is None:
        return "missing_nbbo"
    if bid < 0 or ask < 0 or ask < bid:
        return "invalid_or_crossed_nbbo"
    if bid == 0 and ask == 0:
        return "missing_nbbo"
    if bid == ask:
        return "locked_nbbo_unclassified"
    if price > ask:
        return "outside_above_ask"
    if price == ask:
        return "at_ask_candidate"
    if price < bid:
        return "outside_below_bid"
    if price == bid:
        return "at_bid_candidate"
    midpoint = (bid + ask) / Decimal("2")
    if price == midpoint:
        return "midpoint_unclassified"
    return "inside_spread_unclassified"

def audit_csv(member_name: str, payload: bytes) -> dict[str, object]:
    try:
        decoded = payload.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("csv_not_utf8") from exc
    reader = csv.DictReader(io.StringIO(decoded, newline=""))
    raw_headers = reader.fieldnames or []
    schema = schema_check(raw_headers)
    summary: dict[str, object] = {
        "member_basename": member_name.replace("\\", "/").rsplit("/", 1)[-1],
        "member_sha256": hashlib.sha256(payload).hexdigest(),
        **schema,
        "row_count": 0,
        "distinct_market_dates": 0,
        "quote_datetime_min_et": None,
        "quote_datetime_max_et": None,
        "quote_datetime_market_date_mismatch_rows": 0,
        "underlying_count": 0,
        "contract_count": 0,
        "trade_key_count": 0,
        "duplicate_trade_key_rows": 0,
        "trade_size_sum": 0,
        "invalid_core_rows": 0,
        "zero_or_missing_nbbo_rows": 0,
        "crossed_nbbo_rows": 0,
        "locked_nbbo_rows": 0,
        "outside_nbbo_rows": 0,
        "trade_vs_nbbo_counts": {},
        "trade_condition_counts": {},
        "nonzero_canceled_trade_condition_rows": 0,
        "blank_canceled_trade_condition_rows": 0,
        "zero_trade_price_rows": 0,
        "nonzero_number_of_exchanges_rows": 0,
        "zero_underlying_bid_rows": 0,
        "zero_underlying_ask_rows": 0,
        "missing_underlying_bid_rows": 0,
        "missing_underlying_ask_rows": 0,
        "calcs_zero_counts": {},
        "calcs_blank_counts": {},
        "raw_rows_persisted": False,
        "raw_symbols_persisted": False,
    }
    if schema["schema_status"] != "PASS":
        return summary

    underlyings: set[str] = set()
    contracts: set[tuple[str, ...]] = set()
    trade_keys: set[tuple[str, int, int]] = set()
    market_dates: set[str] = set()
    condition_counts: Counter[str] = Counter()
    quote_counts: Counter[str] = Counter()
    calcs_zero: Counter[str] = Counter()
    calcs_blank: Counter[str] = Counter()
    min_dt: datetime | None = None
    max_dt: datetime | None = None
    invalid_rows = mismatch_rows = nonzero_cancel = nonzero_exchanges = blank_cancel = zero_trade_price = 0
    zero_under_bid = zero_under_ask = missing_under_bid = missing_under_ask = 0
    zero_missing_nbbo = crossed_nbbo = locked_nbbo = outside_nbbo = 0
    size_sum = 0

    for raw_row in reader:
        summary["row_count"] = int(summary["row_count"]) + 1
        row = {str(k).strip().lower(): v for k, v in raw_row.items() if k is not None}
        row_bad = None in raw_row
        try:
            symbol = _text(row.get("underlying_symbol"))
            root = _text(row.get("root"))
            option_type = _text(row.get("option_type")).upper()
            mdate = _market_date(row.get("market_date"))
            qdt = _quote_datetime(row.get("quote_datetime"))
            expiry = _market_date(row.get("expiration"))
            strike = _decimal(row.get("strike"), "strike")
            seq = _integer(row.get("sequence_number"), "sequence_number")
            exchange = _integer(row.get("exchange_id"), "exchange_id")
            size = _integer(row.get("trade_size"), "trade_size")
            price = _decimal(row.get("trade_price"), "trade_price")
            condition = _integer(row.get("trade_condition_id"), "trade_condition_id")
            cancel_condition = _integer(row.get("canceled_trade_condition_id"), "canceled_trade_condition_id", blank_ok=True)
            bid_size = _integer(row.get("best_bid_size"), "best_bid_size", blank_ok=True)
            ask_size = _integer(row.get("best_ask_size"), "best_ask_size", blank_ok=True)
            bid = _decimal(row.get("best_bid"), "best_bid", blank_ok=True)
            ask = _decimal(row.get("best_ask"), "best_ask", blank_ok=True)
            under_bid = _decimal(row.get("underlying_bid"), "underlying_bid", blank_ok=True)
            under_ask = _decimal(row.get("underlying_ask"), "underlying_ask", blank_ok=True)
            exchange_count = (
                _integer(row.get("number_of_exchanges"), "number_of_exchanges")
                if "number_of_exchanges" in row else None
            )
            if not symbol or not root or option_type not in {"C", "P"}:
                raise ValueError("contract_identity_invalid")
            if strike is None or strike <= 0 or size is None or size <= 0 or price is None or price < 0:
                raise ValueError("trade_economics_invalid")
            if price == 0:
                zero_trade_price += 1
            required_ints = [seq, exchange, condition]
            optional_ints = [x for x in (cancel_condition, bid_size, ask_size, exchange_count) if x is not None]
            if min(required_ints + optional_ints) < 0:
                raise ValueError("negative_integer_field")
            if any(x is not None and x < 0 for x in (bid, ask, under_bid, under_ask)):
                raise ValueError("negative_quote_field")
            if under_bid is None:
                missing_under_bid += 1
            elif under_bid == 0:
                zero_under_bid += 1
            if under_ask is None:
                missing_under_ask += 1
            elif under_ask == 0:
                zero_under_ask += 1
            if cancel_condition is None:
                blank_cancel += 1
            elif cancel_condition != 0:
                nonzero_cancel += 1
            if exchange_count is not None and exchange_count != 0:
                nonzero_exchanges += 1
            if mdate.isoformat() != qdt.date().isoformat():
                mismatch_rows += 1
            if min_dt is None or qdt < min_dt:
                min_dt = qdt
            if max_dt is None or qdt > max_dt:
                max_dt = qdt
            quote_class = classify_trade_vs_nbbo(price, bid, ask)
            quote_counts[quote_class] += 1
            if quote_class == "missing_nbbo":
                zero_missing_nbbo += 1
            if quote_class == "invalid_or_crossed_nbbo":
                crossed_nbbo += 1
            if quote_class == "locked_nbbo_unclassified":
                locked_nbbo += 1
            if quote_class in {"outside_above_ask", "outside_below_bid"}:
                outside_nbbo += 1
            condition_counts[str(condition)] += 1
            trade_keys.add((mdate.isoformat(), seq, exchange))
            contracts.add((symbol, root, expiry.isoformat(), str(strike.normalize()), option_type))
            underlyings.add(symbol)
            market_dates.add(mdate.isoformat())
            size_sum += size
            if schema["calcs_included"]:
                for field in CALCS_FIELDS:
                    value = _decimal(row.get(field), field, blank_ok=True)
                    if value is None:
                        calcs_blank[field] += 1
                    elif value == 0:
                        calcs_zero[field] += 1
        except (ValueError, TypeError):
            row_bad = True
        if row_bad:
            invalid_rows += 1

    summary.update({
        "distinct_market_dates": len(market_dates),
        "quote_datetime_min_et": min_dt.isoformat() if min_dt else None,
        "quote_datetime_max_et": max_dt.isoformat() if max_dt else None,
        "quote_datetime_market_date_mismatch_rows": mismatch_rows,
        "underlying_count": len(underlyings),
        "contract_count": len(contracts),
        "trade_key_count": len(trade_keys),
        "duplicate_trade_key_rows": max(0, int(summary["row_count"]) - len(trade_keys)),
        "trade_size_sum": size_sum,
        "invalid_core_rows": invalid_rows,
        "zero_or_missing_nbbo_rows": zero_missing_nbbo,
        "crossed_nbbo_rows": crossed_nbbo,
        "locked_nbbo_rows": locked_nbbo,
        "outside_nbbo_rows": outside_nbbo,
        "trade_vs_nbbo_counts": dict(sorted(quote_counts.items())),
        "trade_condition_counts": dict(sorted(condition_counts.items())),
        "nonzero_canceled_trade_condition_rows": nonzero_cancel,
        "blank_canceled_trade_condition_rows": blank_cancel,
        "zero_trade_price_rows": zero_trade_price,
        "nonzero_number_of_exchanges_rows": nonzero_exchanges,
        "zero_underlying_bid_rows": zero_under_bid,
        "zero_underlying_ask_rows": zero_under_ask,
        "missing_underlying_bid_rows": missing_under_bid,
        "missing_underlying_ask_rows": missing_under_ask,
        "calcs_zero_counts": dict(sorted(calcs_zero.items())),
        "calcs_blank_counts": dict(sorted(calcs_blank.items())),
    })
    return summary

def csv_members(raw_zip: bytes) -> list[tuple[str, bytes]]:
    if len(raw_zip) > MAX_COMPRESSED_BYTES:
        raise ValueError("compressed_archive_exceeds_limit")
    if not zipfile.is_zipfile(io.BytesIO(raw_zip)):
        raise ValueError("sample_not_zip")
    found: list[tuple[str, bytes]] = []
    total = 0
    with zipfile.ZipFile(io.BytesIO(raw_zip)) as archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            total += info.file_size
            if total > MAX_UNCOMPRESSED_BYTES:
                raise ValueError("archive_uncompressed_size_exceeds_limit")
            if info.filename.lower().endswith(".csv"):
                found.append((info.filename, archive.read(info)))
            elif info.filename.lower().endswith(".zip"):
                nested_bytes = archive.read(info)
                if not zipfile.is_zipfile(io.BytesIO(nested_bytes)):
                    raise ValueError("nested_zip_invalid")
                with zipfile.ZipFile(io.BytesIO(nested_bytes)) as nested:
                    for nested_info in nested.infolist():
                        if nested_info.is_dir():
                            continue
                        total += nested_info.file_size
                        if total > MAX_UNCOMPRESSED_BYTES:
                            raise ValueError("archive_uncompressed_size_exceeds_limit")
                        if nested_info.filename.lower().endswith(".csv"):
                            found.append((nested_info.filename, nested.read(nested_info)))
            if len(found) > MAX_MEMBERS:
                raise ValueError("too_many_csv_members")
    if not found:
        raise ValueError("archive_has_no_csv")
    return found

def audit_archive(raw_zip: bytes, headers: dict[str, str] | None = None,
                  retrieved_at_utc: str | None = None, final_url: str = SOURCE_URL) -> dict[str, object]:
    headers = {str(k).lower(): str(v) for k, v in (headers or {}).items()}
    members = csv_members(raw_zip)
    audits = [audit_csv(name, payload) for name, payload in members]
    all_pass = all(
        x["schema_status"] == "PASS" and int(x["row_count"]) > 0 and int(x["invalid_core_rows"]) == 0
        for x in audits
    )
    return {
        "phase": 170,
        "source": "Cboe Option Trades",
        "status": "PASS_SCHEMA_SAMPLE" if all_pass else "FAIL_SAMPLE_SCHEMA_OR_ROWS",
        "capture_mode": "PUBLIC_SAMPLE_BACKFILL",
        "sample_url": SOURCE_URL,
        "final_url": _safe_url(final_url),
        "retrieved_at_utc": retrieved_at_utc or datetime.now(timezone.utc).isoformat(),
        "http_date": headers.get("date"),
        "http_last_modified": headers.get("last-modified"),
        "http_etag": headers.get("etag"),
        "http_content_type": headers.get("content-type"),
        "archive_sha256": hashlib.sha256(raw_zip).hexdigest(),
        "compressed_bytes": len(raw_zip),
        "member_count": len(audits),
        "total_rows": sum(int(x["row_count"]) for x in audits),
        "member_audits": audits,
        "historical_start_product_page_advertised": "2012-01",
        "historical_start_faq_table": "2010-01",
        "historical_start_resolved": False,
        "historical_coverage_complete": False,
        "first_receipt_verified": False,
        "strict_pit": False,
        "alpha_admission": False,
        "raw_archive_persisted": False,
        "raw_rows_persisted": False,
        "raw_symbols_persisted": False,
        "vendor_contact_or_purchase": False,
        "production_change": False,
        "f80_change": False,
    }

def download_sample() -> tuple[bytes, dict[str, str], str]:
    request = Request(SOURCE_URL, headers={"User-Agent": "NuevaEstrategia-Research/Phase170 public sample audit"})
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            with urlopen(request, timeout=60) as response:
                payload = response.read(MAX_COMPRESSED_BYTES + 1)
                return payload, dict(response.headers.items()), response.geturl()
        except HTTPError as exc:
            if exc.code not in {429, 500, 502, 503, 504}:
                raise
            last_error = exc
        except URLError as exc:
            last_error = exc
        if attempt < 2:
            time.sleep(2 ** attempt)
    raise RuntimeError(f"sample_download_failed:{type(last_error).__name__ if last_error else 'unknown'}")

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="phase170_output")
    args = parser.parse_args()
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    try:
        raw, headers, final_url = download_sample()
        summary = audit_archive(raw, headers, final_url=final_url)
    except Exception as exc:
        summary = {
            "phase": 170,
            "source": "Cboe Option Trades",
            "status": "BLOCKED_DOWNLOAD",
            "error_type": type(exc).__name__,
            "error": str(exc)[:300],
            "sample_url": SOURCE_URL,
            "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
            "strict_pit": False,
            "alpha_admission": False,
            "raw_archive_persisted": False,
            "raw_rows_persisted": False,
            "raw_symbols_persisted": False,
            "vendor_contact_or_purchase": False,
            "production_change": False,
            "f80_change": False,
        }
    path = out / "phase170_cboe_option_trades_public_sample_summary.json"
    path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["status"] == "PASS_SCHEMA_SAMPLE" else 2

if __name__ == "__main__":
    raise SystemExit(main())

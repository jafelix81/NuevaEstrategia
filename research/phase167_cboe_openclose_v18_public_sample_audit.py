#!/usr/bin/env python3
"""Phase 167: audit the public Cboe Open-Close 1-minute sample without retaining raw rows."""
from __future__ import annotations
import argparse, csv, gzip, hashlib, io, json, re, time
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

SAMPLE_URL = "https://datashop.cboe.com/documents/Cboe_OpenClose_2026-09-30_15_20_1.csv.gz"
MAX_COMPRESSED_BYTES = 100_000_000
MAX_DECOMPRESSED_BYTES = 500_000_000
FILENAME_RE = re.compile(r"^Cboe_OpenClose_(\d{4}-\d{2}-\d{2})_(\d{2})_(\d{2})_(\d+)\.csv\.gz$")
ET = ZoneInfo("America/New_York")
EOD_FIELDS_SAMPLE = (
    "first_trade_price", "high_trade_price", "low_trade_price", "last_trade_price",
    "total_cboe_vol", "total_industry_vol", "open_interest", "previous_open_interest",
)


class SampleAuditError(ValueError):
    pass


def bucket_columns() -> list[str]:
    fields: list[str] = []
    for prefix in ("firm", "bd"):
        for action in ("open_buy", "close_buy", "open_sell", "close_sell"):
            fields.extend((f"{prefix}_{action}_qty", f"{prefix}_{action}_vol"))
    for action in ("buy", "sell"):
        fields.extend((f"mm_{action}_qty", f"mm_{action}_vol"))
    for prefix in ("cust", "procust"):
        for size in ("lt_100", "100_199", "gt_199"):
            for action in ("open_buy", "close_buy", "open_sell", "close_sell"):
                fields.extend((f"{prefix}_{size}_{action}_qty", f"{prefix}_{size}_{action}_vol"))
    return fields


def expected_columns(interval_minutes: int) -> list[str]:
    if interval_minutes not in (1, 10):
        raise ValueError("unsupported_interval")
    call_field = "call_or_put" if interval_minutes == 1 else "call_put_flag"
    return [
        "trade_datetime", "underlying", "security_type", "option_symbol",
        "expiration_date", "strike_price", call_field, "days_to_expire",
        "series_type", "first_trade_price", "high_trade_price", "low_trade_price",
        "last_trade_price", "total_exchange_vol", "total_industry_vol",
        "open_interest", "previous_open_interest", "previous_close",
        *bucket_columns(), "trading_dt", "trading_segment",
    ]


def sample_columns_1m() -> list[str]:
    columns = expected_columns(1)
    return [("total_cboe_vol" if c == "total_exchange_vol" else c) for c in columns]


def parse_sample_filename(url: str) -> dict[str, object]:
    name = urlparse(url).path.rsplit("/", 1)[-1]
    match = FILENAME_RE.fullmatch(name)
    if not match:
        raise SampleAuditError("sample_filename_unrecognized")
    date_s, hour_s, minute_s, segment_s = match.groups()
    try:
        market_date = datetime.strptime(date_s, "%Y-%m-%d").date()
    except ValueError as exc:
        raise SampleAuditError("sample_market_date_invalid") from exc
    hour, minute, segment = int(hour_s), int(minute_s), int(segment_s)
    if hour > 23 or minute > 59 or segment not in (1, 2):
        raise SampleAuditError("sample_filename_time_or_segment_invalid")
    return {
        "filename": name, "market_date": market_date.isoformat(),
        "snapshot_time_et": f"{hour:02d}:{minute:02d}",
        "trading_segment_suffix": segment,
        "exchange_inference": "C1_FROM_SEGMENT_SUFFIX",
    }


def _parse_int(value: object) -> int | None:
    text = "" if value is None else str(value).strip()
    if not text:
        return None
    if not re.fullmatch(r"\d+", text):
        raise ValueError("integer_invalid")
    return int(text)


def _parse_integral_decimal(value: object) -> tuple[int | None, bool]:
    text = "" if value is None else str(value).strip()
    if not text:
        return None, False
    try:
        parsed = Decimal(text)
    except InvalidOperation as exc:
        raise ValueError("decimal_invalid") from exc
    if parsed != parsed.to_integral_value():
        raise ValueError("not_integral")
    return int(parsed), "." in text


def _parse_decimal(value: object) -> Decimal | None:
    text = "" if value is None else str(value).strip()
    if not text:
        return None
    try:
        return Decimal(text)
    except InvalidOperation as exc:
        raise ValueError("decimal_invalid") from exc


def _parse_trade_datetime(value: object) -> datetime | None:
    text = "" if value is None else str(value).strip()
    if not text:
        return None
    try:
        parsed = datetime.strptime(text, "%Y-%m-%d %H:%M:%S")
    except ValueError as exc:
        raise ValueError("trade_datetime_not_spec_format") from exc
    return parsed.replace(tzinfo=ET)


def _parse_date(value: object, fmt: str) -> str | None:
    text = "" if value is None else str(value).strip()
    if not text:
        return None
    try:
        return datetime.strptime(text, fmt).date().isoformat()
    except ValueError as exc:
        raise ValueError("date_invalid") from exc


def audit_payload(raw_gzip: bytes, headers: dict[str, str] | None = None, *,
                  url: str = SAMPLE_URL, retrieved_at_utc: str | None = None) -> dict[str, object]:
    headers = {str(k).lower(): str(v) for k, v in (headers or {}).items()}
    filename = parse_sample_filename(url)
    if len(raw_gzip) > MAX_COMPRESSED_BYTES:
        raise SampleAuditError("compressed_sample_exceeds_limit")
    if not raw_gzip.startswith(b"\x1f\x8b"):
        raise SampleAuditError("sample_is_not_gzip")
    try:
        payload = gzip.decompress(raw_gzip)
    except OSError as exc:
        raise SampleAuditError("gzip_decompression_failed") from exc
    if len(payload) > MAX_DECOMPRESSED_BYTES:
        raise SampleAuditError("decompressed_sample_exceeds_limit")
    try:
        decoded = payload.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise SampleAuditError("sample_not_utf8") from exc

    reader = csv.DictReader(io.StringIO(decoded, newline=""))
    actual_columns = reader.fieldnames or []
    sample_expected = sample_columns_1m()
    spec_expected = expected_columns(1)
    missing = sorted(set(sample_expected) - set(actual_columns))
    extra = sorted(set(actual_columns) - set(sample_expected))
    duplicate_headers = len(actual_columns) - len(set(actual_columns))
    rows = list(reader)
    if not rows:
        raise SampleAuditError("sample_has_no_rows")

    invalid_bucket_values = blank_bucket_values = 0
    invalid_base_values = blank_base_values = 0
    blank_underlying_rows = blank_option_symbol_rows = 0
    invalid_strike_price_rows = invalid_days_to_expire_rows = 0
    days_to_expire_decimal_format_rows = 0
    blank_previous_close_rows = zero_previous_close_rows = negative_previous_close_rows = positive_previous_close_rows = invalid_previous_close_format_rows = 0
    invalid_trade_datetime = invalid_trading_dt = invalid_expiration_date = 0
    invalid_call_put = invalid_series_type = invalid_security_type = invalid_segment = 0
    segment_missing = duplicate_series_rows = rows_with_extra_values = rows_with_any_issue = 0
    seen_series: set[tuple[str, ...]] = set()
    underlying_values: set[str] = set()
    trade_datetimes: Counter[str] = Counter()
    trading_dates: Counter[str] = Counter()
    segment_values: Counter[str] = Counter()
    security_type_values: Counter[str] = Counter()
    series_type_values: Counter[str] = Counter()
    call_put_values: Counter[str] = Counter()
    eod_nonblank_counts: Counter[str] = Counter()
    filename_time_match_rows = filename_date_match_rows = trading_date_match_rows = 0
    segment_suffix_match_rows = segment_suffix_mismatch_rows = 0

    for row in rows:
        row_issue = False
        if None in row:
            rows_with_extra_values += 1
            row_issue = True

        for field in EOD_FIELDS_SAMPLE:
            if str(row.get(field) or "").strip():
                eod_nonblank_counts[field] += 1

        underlying = str(row.get("underlying") or "").strip()
        option_symbol = str(row.get("option_symbol") or "").strip()
        expiration = str(row.get("expiration_date") or "").strip()
        strike = str(row.get("strike_price") or "").strip()
        call_put = str(row.get("call_or_put") or "").strip().upper()
        series_type = str(row.get("series_type") or "").strip().upper()
        if underlying:
            underlying_values.add(underlying)
        else:
            blank_underlying_rows += 1
            invalid_base_values += 1
            row_issue = True
        if not option_symbol:
            blank_option_symbol_rows += 1
            invalid_base_values += 1
            row_issue = True
        try:
            _parse_date(expiration, "%Y%m%d")
        except ValueError:
            invalid_expiration_date += 1
            row_issue = True
        try:
            strike_value = _parse_decimal(strike)
            if strike_value is None or strike_value <= 0:
                raise ValueError("strike_nonpositive_or_blank")
        except ValueError:
            invalid_strike_price_rows += 1
            invalid_base_values += 1
            row_issue = True
        if call_put not in {"C", "P"}:
            invalid_call_put += 1
            row_issue = True
        if series_type not in {"S", "N", "F"}:
            invalid_series_type += 1
            row_issue = True

        key = (underlying, option_symbol, expiration, strike, call_put, series_type)
        if key in seen_series:
            duplicate_series_rows += 1
            row_issue = True
        else:
            seen_series.add(key)

        try:
            trade_dt = _parse_trade_datetime(row.get("trade_datetime"))
            if trade_dt is None:
                raise ValueError("trade_datetime_blank")
            trade_datetimes[trade_dt.isoformat()] += 1
            if trade_dt.strftime("%H:%M") == filename["snapshot_time_et"]:
                filename_time_match_rows += 1
            if trade_dt.date().isoformat() == filename["market_date"]:
                filename_date_match_rows += 1
        except ValueError:
            invalid_trade_datetime += 1
            row_issue = True

        try:
            trading_dt = _parse_date(row.get("trading_dt"), "%Y-%m-%d")
            if trading_dt is None:
                raise ValueError("trading_dt_blank")
            trading_dates[trading_dt] += 1
            if trading_dt == filename["market_date"]:
                trading_date_match_rows += 1
        except ValueError:
            invalid_trading_dt += 1
            row_issue = True

        try:
            security_type = _parse_int(row.get("security_type"))
            if security_type not in {1, 2, 3, 4}:
                raise ValueError("security_type_out_of_range")
            security_type_values[str(security_type)] += 1
        except ValueError:
            invalid_security_type += 1
            row_issue = True

        try:
            days, decimal_format = _parse_integral_decimal(row.get("days_to_expire"))
            if days is None or days < 0:
                raise ValueError("days_to_expire_invalid")
            if decimal_format:
                days_to_expire_decimal_format_rows += 1
        except ValueError:
            invalid_days_to_expire_rows += 1
            invalid_base_values += 1
            row_issue = True

        try:
            close_value = _parse_decimal(row.get("previous_close"))
            if close_value is None:
                blank_previous_close_rows += 1
                blank_base_values += 1
            elif close_value == 0:
                zero_previous_close_rows += 1
            elif close_value < 0:
                negative_previous_close_rows += 1
                invalid_base_values += 1
                row_issue = True
            else:
                positive_previous_close_rows += 1
        except ValueError:
            invalid_previous_close_format_rows += 1
            invalid_base_values += 1
            row_issue = True

        segment_raw = str(row.get("trading_segment") or "").strip()
        if not segment_raw:
            segment_missing += 1
        else:
            try:
                segment = _parse_int(segment_raw)
                if segment not in {1, 2}:
                    raise ValueError("segment_out_of_range")
                segment_values[str(segment)] += 1
                if segment == filename["trading_segment_suffix"]:
                    segment_suffix_match_rows += 1
                else:
                    segment_suffix_mismatch_rows += 1
                    row_issue = True
            except ValueError:
                invalid_segment += 1
                row_issue = True

        for field in bucket_columns():
            value = str(row.get(field) or "").strip()
            if not value:
                blank_bucket_values += 1
                continue
            try:
                parsed = _parse_int(value)
                if parsed is None or parsed < 0:
                    raise ValueError("bucket_negative_or_blank")
            except ValueError:
                invalid_bucket_values += 1
                row_issue = True

        series_type_values[series_type or "<blank>"] += 1
        call_put_values[call_put or "<blank>"] += 1
        if row_issue:
            rows_with_any_issue += 1

    eod_nonblank_total = sum(eod_nonblank_counts.values())
    schema_exact_sample = not missing and not extra and duplicate_headers == 0 and len(actual_columns) == 88
    if schema_exact_sample and eod_nonblank_total == 0:
        status = "PASS_SCHEMA_SAMPLE_WITH_EMPTY_EOD_COLUMNS"
    elif schema_exact_sample:
        status = "FAIL_EOD_FIELDS_POPULATED_IN_INTRADAY_SAMPLE"
    else:
        status = "FAIL_SCHEMA_SAMPLE"
    retrieved = retrieved_at_utc or datetime.now(timezone.utc).isoformat()
    row_quality_issues = (
        invalid_bucket_values + invalid_base_values + invalid_trade_datetime +
        invalid_trading_dt + invalid_expiration_date + invalid_call_put +
        invalid_series_type + invalid_security_type + invalid_segment +
        duplicate_series_rows + rows_with_extra_values + segment_suffix_mismatch_rows
    )
    return {
        "phase": 167, "status": status,
        "row_quality_status": (
            "PASS_WITH_PREVIOUS_CLOSE_GAPS"
            if row_quality_issues == 0 and (zero_previous_close_rows > 0 or blank_previous_close_rows > 0)
            else "CLEAN" if row_quality_issues == 0 else "PASS_WITH_ROW_DIAGNOSTICS"
        ),
        "source_url": url, "capture_mode": "PUBLIC_SAMPLE_ARCHIVE_BACKFILL",
        "strict_pit": False, "first_publication_time_verified": False,
        "historical_coverage_verified": False, "broad_universe_coverage_verified": False,
        "post_cutover_live_file_verified": False, "alpha_admission": "BLOCKED",
        "raw_rows_persisted": False, "raw_sample_persisted": False,
        "retrieved_at_utc": retrieved, "http_date": headers.get("date"),
        "http_last_modified": headers.get("last-modified"), "http_etag": headers.get("etag"),
        "http_content_type": headers.get("content-type"), "http_content_length": headers.get("content-length"),
        "raw_file_sha256": hashlib.sha256(raw_gzip).hexdigest(),
        "compressed_bytes": len(raw_gzip), "decompressed_bytes": len(payload),
        "header_sha256": hashlib.sha256(",".join(actual_columns).encode("utf-8")).hexdigest(),
        **filename,
        "sample_file_date_pre_cutover": filename["market_date"] < "2026-11-08",
        "expected_interval_minutes": 1, "sample_exchange_inference": "C1_FROM_SEGMENT_SUFFIX_NOT_EXCHANGE_FIELD",
        "expected_schema_version": "C1_1M_V1.8_20261108",
        "actual_column_count": len(actual_columns), "expected_column_count": 88,
        "official_spec_column_count": len(spec_expected),
        "all_columns_lowercase": all(name == name.lower() for name in actual_columns),
        "missing_columns": missing, "extra_columns": extra,
        "sample_total_volume_field_alias": (
            "total_cboe_vol_in_sample_vs_total_exchange_vol_in_pdf_spec"
            if "total_cboe_vol" in actual_columns and "total_exchange_vol" not in actual_columns
            else "no_alias_difference"
        ),
        "duplicate_header_count": duplicate_headers, "row_count": len(rows),
        "unique_underlying_count": len(underlying_values), "unique_series_key_count": len(seen_series),
        "duplicate_series_rows": duplicate_series_rows, "unique_trade_datetime_count": len(trade_datetimes),
        "trade_datetime_filename_time_match_rows": filename_time_match_rows,
        "trade_datetime_filename_date_match_rows": filename_date_match_rows,
        "trading_dt_market_date_match_rows": trading_date_match_rows,
        "trading_dt_value_counts": dict(trading_dates), "trading_segment_value_counts": dict(segment_values),
        "trading_segment_missing_rows": segment_missing,
        "trading_segment_filename_suffix_match_rows": segment_suffix_match_rows,
        "trading_segment_filename_suffix_mismatch_rows": segment_suffix_mismatch_rows,
        "security_type_counts": dict(security_type_values), "series_type_counts": dict(series_type_values),
        "call_put_counts": dict(call_put_values),
        "eod_placeholder_nonblank_counts": dict(eod_nonblank_counts),
        "eod_placeholder_nonblank_total": eod_nonblank_total,
        "invalid_bucket_values": invalid_bucket_values, "blank_bucket_values": blank_bucket_values,
        "invalid_base_values": invalid_base_values, "blank_base_values": blank_base_values,
        "blank_underlying_rows": blank_underlying_rows, "blank_option_symbol_rows": blank_option_symbol_rows,
        "invalid_strike_price_rows": invalid_strike_price_rows,
        "invalid_days_to_expire_rows": invalid_days_to_expire_rows,
        "days_to_expire_decimal_format_rows": days_to_expire_decimal_format_rows,
        "blank_previous_close_rows": blank_previous_close_rows,
        "zero_previous_close_rows": zero_previous_close_rows,
        "negative_previous_close_rows": negative_previous_close_rows,
        "invalid_previous_close_format_rows": invalid_previous_close_format_rows,
        "positive_previous_close_rows": positive_previous_close_rows,
        "positive_previous_close_coverage": positive_previous_close_rows / len(rows),
        "zero_previous_close_fraction": zero_previous_close_rows / len(rows),
        "previous_close_zero_semantics": "not specified by the source specification; preserve zero separately and do not use as a positive price or automatically impute as missing",
        "invalid_trade_datetime": invalid_trade_datetime, "invalid_trading_dt": invalid_trading_dt,
        "invalid_expiration_date": invalid_expiration_date, "invalid_call_put": invalid_call_put,
        "invalid_series_type": invalid_series_type, "invalid_security_type": invalid_security_type,
        "invalid_segment": invalid_segment, "rows_with_extra_values": rows_with_extra_values,
        "rows_with_any_issue": rows_with_any_issue, "row_quality_issue_count": row_quality_issues,
        "eod_only_fields_are_empty": eod_nonblank_total == 0,
        "interpretation": (
            "single public format sample; EOD-only placeholder columns are permitted only if empty; "
            "cumulative intraday snapshot; later snapshots can reflect late trades and corrections; "
            "not interval trade volume and not participant identity"
        ),
    }


def download_sample(url: str = SAMPLE_URL) -> tuple[bytes, dict[str, str]]:
    request = Request(url, headers={
        "User-Agent": "jafelix81/NuevaEstrategia research-only",
        "Accept": "application/gzip,application/octet-stream,*/*",
        "Accept-Encoding": "identity",
    })
    last_error = None
    for attempt in range(3):
        try:
            with urlopen(request, timeout=45) as response:
                raw = response.read(MAX_COMPRESSED_BYTES + 1)
                if len(raw) > MAX_COMPRESSED_BYTES:
                    raise SampleAuditError("compressed_sample_exceeds_limit")
                if response.status != 200:
                    raise SampleAuditError(f"http_status_{response.status}")
                headers = {key.lower(): value for key, value in response.headers.items()}
                return raw, headers
        except HTTPError as exc:
            last_error = f"http_{exc.code}"
            if exc.code not in {408, 429, 500, 502, 503, 504} or attempt == 2:
                break
            time.sleep(min(2 ** attempt, 5))
        except (URLError, TimeoutError, OSError, SampleAuditError) as exc:
            last_error = str(exc)
            if attempt == 2:
                break
            time.sleep(min(2 ** attempt, 5))
    raise SampleAuditError(last_error or "sample_download_failed")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default=SAMPLE_URL)
    parser.add_argument("--output-dir", default="phase167_output")
    args = parser.parse_args()
    raw, headers = download_sample(args.url)
    summary = audit_payload(raw, headers, url=args.url)
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    path = output / "phase167_cboe_openclose_public_sample_summary.json"
    path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Phase 168: audit the public Cboe Open-Close EOD sample in memory.

Only aggregate metadata, counts, hashes and validation diagnostics are written.
Raw option rows and underlying symbols are never persisted.
"""
from __future__ import annotations
import argparse, csv, hashlib, io, json, re, zipfile
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

SAMPLE_URL = "https://datashop.cboe.com/download/sample/218"
MAX_COMPRESSED_BYTES = 100_000_000
MAX_DECOMPRESSED_BYTES = 500_000_000
MAX_CSV_MEMBERS = 32
FILENAME_RE = re.compile(r"^(C1|BZX|C2|EDGX)OpenClose_(\d{4}-\d{2}-\d{2})(_p)?\.csv$", re.I)


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


def expected_columns_eod() -> list[str]:
    return [
        "quote_date", "underlying_symbol", "security_type", "option_symbol",
        "expiration_date", "strike_price", "call_put_flag", "days_to_expire",
        "series_type", "first_trade_price", "high_trade_price", "low_trade_price",
        "last_trade_price", "total_exchange_vol", "total_industry_vol",
        "open_interest", "previous_open_interest", "previous_close",
        *bucket_columns(),
    ]


def parse_member_name(name: str) -> dict[str, object]:
    base = name.replace("\\", "/").rsplit("/", 1)[-1]
    match = FILENAME_RE.fullmatch(base)
    if not match:
        raise ValueError("eod_member_filename_unrecognized")
    exchange, date_s, prelim = match.groups()
    try:
        datetime.strptime(date_s, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError("eod_member_date_invalid") from exc
    return {"exchange": exchange.upper(), "quote_date": date_s,
            "file_kind": "PRELIMINARY" if prelim else "FINAL"}


def _text(value: object) -> str:
    return "" if value is None else str(value).strip()


def _int_value(value: object, field: str, *, allow_blank: bool = False) -> int | None:
    raw = _text(value)
    if not raw and allow_blank:
        return None
    if not re.fullmatch(r"\d+", raw):
        raise ValueError(f"invalid_nonnegative_integer:{field}")
    return int(raw)


def _decimal_value(value: object, field: str, *, allow_blank: bool = True) -> Decimal | None:
    raw = _text(value)
    if not raw and allow_blank:
        return None
    try:
        return Decimal(raw)
    except InvalidOperation as exc:
        raise ValueError(f"invalid_decimal:{field}") from exc


def _safe_final_url(url: str) -> str:
    parts = urlsplit(url)
    return f"{parts.scheme}://{parts.netloc}{parts.path}"


def _csv_members(raw_zip: bytes) -> list[tuple[str, bytes]]:
    if len(raw_zip) > MAX_COMPRESSED_BYTES:
        raise ValueError("compressed_archive_exceeds_limit")
    if not zipfile.is_zipfile(io.BytesIO(raw_zip)):
        raise ValueError("sample_is_not_zip")
    found: list[tuple[str, bytes]] = []
    total_uncompressed = 0
    with zipfile.ZipFile(io.BytesIO(raw_zip)) as archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            if info.file_size < 0 or info.file_size > MAX_DECOMPRESSED_BYTES:
                raise ValueError("archive_member_exceeds_limit")
            total_uncompressed += info.file_size
            if total_uncompressed > MAX_DECOMPRESSED_BYTES:
                raise ValueError("archive_uncompressed_size_exceeds_limit")
            suffix = info.filename.lower()
            if suffix.endswith(".csv"):
                found.append((info.filename, archive.read(info)))
            elif suffix.endswith(".zip"):
                nested = archive.read(info)
                if not zipfile.is_zipfile(io.BytesIO(nested)):
                    raise ValueError("nested_archive_invalid")
                with zipfile.ZipFile(io.BytesIO(nested)) as nested_archive:
                    for nested_info in nested_archive.infolist():
                        if nested_info.is_dir():
                            continue
                        total_uncompressed += nested_info.file_size
                        if total_uncompressed > MAX_DECOMPRESSED_BYTES:
                            raise ValueError("archive_uncompressed_size_exceeds_limit")
                        if nested_info.filename.lower().endswith(".csv"):
                            found.append((nested_info.filename, nested_archive.read(nested_info)))
            if len(found) > MAX_CSV_MEMBERS:
                raise ValueError("too_many_csv_members")
    if not found:
        raise ValueError("archive_contains_no_csv")
    return found


def _audit_csv(member_name: str, payload: bytes) -> tuple[dict[str, object], dict[tuple[str, ...], dict[str, str]]]:
    try:
        meta = parse_member_name(member_name)
    except ValueError:
        base = member_name.replace("\\\\", "/").rsplit("/", 1)[-1]
        meta = {"member_basename": base, "exchange": "UNKNOWN", "quote_date": None,
                "file_kind": "UNKNOWN", "filename_identity_basis": "UNRESOLVED_GENERIC_MEMBER_NAME"}
    try:
        decoded = payload.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("csv_not_utf8") from exc
    reader = csv.DictReader(io.StringIO(decoded, newline=""))
    raw_headers = reader.fieldnames or []
    headers = [h.strip().lower() for h in raw_headers]
    expected = expected_columns_eod()
    missing = sorted(set(expected) - set(headers))
    extra = sorted(set(headers) - set(expected))
    duplicate_headers = len(headers) - len(set(headers))
    summary: dict[str, object] = {
        **meta, "actual_column_count": len(headers), "expected_column_count": len(expected),
        "missing_columns": missing, "extra_columns": extra, "duplicate_header_count": duplicate_headers,
        "detected_schema": ("EOD" if not missing and not extra and duplicate_headers == 0 else
                            "INTRADAY_LIKE" if {"trade_datetime", "underlying"}.issubset(set(headers)) else "UNKNOWN"),
        "header_case_normalized": raw_headers != headers, "row_count": 0,
        "quote_date_from_rows": None, "distinct_quote_dates_in_rows": 0,
        "unique_underlying_count": 0, "unique_series_count": 0, "duplicate_series_rows": 0,
        "quote_date_mismatch_rows": 0, "invalid_required_field_count": 0, "invalid_bucket_values": 0,
        "blank_previous_close_rows": 0, "zero_previous_close_rows": 0, "negative_previous_close_rows": 0,
        "positive_previous_close_rows": 0, "invalid_previous_close_format_rows": 0,
        "security_type_counts": {}, "series_type_counts": {}, "call_put_counts": {},
        "oi_zero_rows": 0, "oi_positive_rows": 0,
        "total_exchange_volume_zero_rows": 0, "total_exchange_volume_positive_rows": 0,
        "raw_rows_persisted": False, "raw_symbols_persisted": False,
    }
    if missing or extra or duplicate_headers:
        return summary, {}

    underlying_set: set[str] = set()
    series_set: set[tuple[str, ...]] = set()
    state: dict[tuple[str, ...], dict[str, str]] = {}
    security_counts: Counter[str] = Counter()
    series_counts: Counter[str] = Counter()
    call_put_counts: Counter[str] = Counter()
    invalid_required = invalid_buckets = 0
    quote_date_values: set[str] = set()
    for raw_row in reader:
        row = {str(k).strip().lower(): v for k, v in raw_row.items() if k is not None}
        summary["row_count"] = int(summary["row_count"]) + 1
        if None in raw_row:
            invalid_required += 1
        underlying = _text(row.get("underlying_symbol"))
        option_symbol = _text(row.get("option_symbol"))
        expiration = _text(row.get("expiration_date"))
        strike = _text(row.get("strike_price"))
        call_put = _text(row.get("call_put_flag")).upper()
        series_type = _text(row.get("series_type")).upper()
        try:
            quote_date = datetime.strptime(_text(row.get("quote_date")), "%m/%d/%Y").date().isoformat()
            quote_date_values.add(quote_date)
            if meta["quote_date"] is not None and quote_date != meta["quote_date"]:
                summary["quote_date_mismatch_rows"] = int(summary["quote_date_mismatch_rows"]) + 1
        except ValueError:
            invalid_required += 1
        try:
            datetime.strptime(expiration, "%Y-%m-%d")
        except ValueError:
            invalid_required += 1
        try:
            strike_value = _decimal_value(strike, "strike_price", allow_blank=False)
            if strike_value is None or strike_value <= 0:
                raise ValueError("strike_not_positive")
        except ValueError:
            invalid_required += 1
        if not underlying or not option_symbol:
            invalid_required += 1
        if call_put not in {"C", "P"}:
            invalid_required += 1
        if series_type not in {"S", "N", "F"}:
            invalid_required += 1
        try:
            security_type = _int_value(row.get("security_type"), "security_type")
            if security_type not in {1, 2, 3, 4}:
                raise ValueError("security_type_out_of_range")
            security_counts[str(security_type)] += 1
        except ValueError:
            invalid_required += 1
        try:
            _int_value(row.get("days_to_expire"), "days_to_expire")
            _int_value(row.get("total_exchange_vol"), "total_exchange_vol")
            _int_value(row.get("total_industry_vol"), "total_industry_vol")
            oi = _int_value(row.get("open_interest"), "open_interest")
            _int_value(row.get("previous_open_interest"), "previous_open_interest")
            if oi == 0:
                summary["oi_zero_rows"] = int(summary["oi_zero_rows"]) + 1
            else:
                summary["oi_positive_rows"] = int(summary["oi_positive_rows"]) + 1
            exchange_volume = int(_text(row.get("total_exchange_vol")))
            if exchange_volume == 0:
                summary["total_exchange_volume_zero_rows"] = int(summary["total_exchange_volume_zero_rows"]) + 1
            else:
                summary["total_exchange_volume_positive_rows"] = int(summary["total_exchange_volume_positive_rows"]) + 1
        except (ValueError, TypeError):
            invalid_required += 1
        for field in ("first_trade_price", "high_trade_price", "low_trade_price", "last_trade_price", "previous_close"):
            try:
                value = _decimal_value(row.get(field), field, allow_blank=True)
                if field == "previous_close":
                    if value is None:
                        summary["blank_previous_close_rows"] = int(summary["blank_previous_close_rows"]) + 1
                    elif value == 0:
                        summary["zero_previous_close_rows"] = int(summary["zero_previous_close_rows"]) + 1
                    elif value < 0:
                        summary["negative_previous_close_rows"] = int(summary["negative_previous_close_rows"]) + 1
                    else:
                        summary["positive_previous_close_rows"] = int(summary["positive_previous_close_rows"]) + 1
            except ValueError:
                if field == "previous_close":
                    summary["invalid_previous_close_format_rows"] = int(summary["invalid_previous_close_format_rows"]) + 1
                else:
                    invalid_required += 1
        for field in bucket_columns():
            try:
                _int_value(row.get(field), field)
            except ValueError:
                invalid_buckets += 1
        key = (underlying, option_symbol, expiration, strike, call_put, series_type)
        if key in series_set:
            summary["duplicate_series_rows"] = int(summary["duplicate_series_rows"]) + 1
        else:
            series_set.add(key)
        underlying_set.add(underlying)
        call_put_counts[call_put] += 1
        series_counts[series_type] += 1
        state[key] = {
            "open_interest": _text(row.get("open_interest")),
            "previous_open_interest": _text(row.get("previous_open_interest")),
            "total_industry_vol": _text(row.get("total_industry_vol")),
            "total_exchange_vol": _text(row.get("total_exchange_vol")),
        }
    summary["unique_underlying_count"] = len(underlying_set)
    summary["distinct_quote_dates_in_rows"] = len(quote_date_values)
    if len(quote_date_values) == 1:
        row_quote_date = next(iter(quote_date_values))
        summary["quote_date_from_rows"] = row_quote_date
        if summary["quote_date"] is None:
            summary["quote_date"] = row_quote_date
    elif len(quote_date_values) != 1:
        invalid_required += 1
    summary["unique_series_count"] = len(series_set)
    summary["invalid_required_field_count"] = invalid_required
    summary["invalid_bucket_values"] = invalid_buckets
    summary["security_type_counts"] = dict(sorted(security_counts.items()))
    summary["series_type_counts"] = dict(sorted(series_counts.items()))
    summary["call_put_counts"] = dict(sorted(call_put_counts.items()))
    return summary, state


def audit_archive(raw_zip: bytes, headers: dict[str, str] | None = None, *,
                  retrieved_at_utc: str | None = None, final_url: str = SAMPLE_URL) -> dict[str, object]:
    headers = {str(k).lower(): str(v) for k, v in (headers or {}).items()}
    retrieved = retrieved_at_utc or datetime.now(timezone.utc).isoformat()
    members = _csv_members(raw_zip)
    file_summaries = []
    states: dict[tuple[str, str, str, str], dict[tuple[str, ...], dict[str, str]]] = {}
    schema_failures = 0
    total_rows = total_underlyings = total_series = total_duplicates = 0
    for name, payload in members:
        summary, state = _audit_csv(name, payload)
        if summary["missing_columns"] or summary["extra_columns"] or summary["duplicate_header_count"]:
            schema_failures += 1
        if int(summary["row_count"]) == 0:
            schema_failures += 1
        if int(summary["quote_date_mismatch_rows"]) > 0 or int(summary["invalid_required_field_count"]) > 0 or int(summary["invalid_bucket_values"]) > 0:
            schema_failures += 1
        key = (str(summary["exchange"]), str(summary["quote_date"]), str(summary["file_kind"]), str(summary["member_basename"]))
        if key in states:
            schema_failures += 1
        states[key] = state
        file_summaries.append({k: v for k, v in summary.items()})
        total_rows += int(summary["row_count"])
        total_underlyings += int(summary["unique_underlying_count"])
        total_series += int(summary["unique_series_count"])
        total_duplicates += int(summary["duplicate_series_rows"])

    comparisons = []
    grouped_states: dict[tuple[str, str], dict[str, dict[tuple[str, ...], dict[str, str]]]] = {}
    for (exchange, day, kind, _member), state in states.items():
        if exchange != "UNKNOWN" and kind in {"FINAL", "PRELIMINARY"}:
            grouped_states.setdefault((exchange, day), {})[kind] = state
    pair_keys = {key for key, versions in grouped_states.items() if {"FINAL", "PRELIMINARY"}.issubset(versions)}
    for exchange, day in sorted(pair_keys):
        prelim = grouped_states[(exchange, day)]["PRELIMINARY"]
        final = grouped_states[(exchange, day)]["FINAL"]
        common = set(prelim) & set(final)
        changed = {field: sum(prelim[k][field] != final[k][field] for k in common)
                   for field in ("open_interest", "previous_open_interest", "total_industry_vol")}
        comparisons.append({"exchange": exchange, "quote_date": day,
                            "preliminary_series": len(prelim), "final_series": len(final),
                            "common_series": len(common), "preliminary_only_series": len(set(prelim)-set(final)),
                            "final_only_series": len(set(final)-set(prelim)),
                            "changed_values_on_common_series": changed})

    all_headers = all(not x["missing_columns"] and not x["extra_columns"] and x["duplicate_header_count"] == 0 for x in file_summaries)
    all_rows_valid = all(x["row_count"] > 0 and x["quote_date_mismatch_rows"] == 0 and
                         x["invalid_required_field_count"] == 0 and x["negative_previous_close_rows"] == 0 and
                         x["invalid_previous_close_format_rows"] == 0 and x["invalid_bucket_values"] == 0 and
                         x["duplicate_series_rows"] == 0 for x in file_summaries)
    identity_resolved = all(x["exchange"] != "UNKNOWN" and x["file_kind"] != "UNKNOWN" for x in file_summaries)
    detected = {str(x["detected_schema"]) for x in file_summaries}
    if detected == {"INTRADAY_LIKE"}:
        status = "BLOCKED_SAMPLE_IS_INTRADAY_NOT_EOD"
    elif all_headers and all_rows_valid and schema_failures == 0:
        status = "PASS_EOD_SAMPLE_SCHEMA" if identity_resolved else "PASS_EOD_SAMPLE_SCHEMA_IDENTITY_UNRESOLVED"
    else:
        status = "FAIL_EOD_SAMPLE_SCHEMA"
    return {
        "phase": 168, "status": status, "sample_url": SAMPLE_URL,
        "final_url_without_query": _safe_final_url(final_url), "retrieved_at_utc": retrieved,
        "http_content_type": headers.get("content-type"), "http_content_length": headers.get("content-length"),
        "http_last_modified": headers.get("last-modified"), "http_etag": headers.get("etag"),
        "compressed_bytes": len(raw_zip), "raw_zip_sha256": hashlib.sha256(raw_zip).hexdigest(),
        "csv_member_count": len(members), "member_filename_identity_resolved": identity_resolved,
        "total_rows": total_rows,
        "sum_of_file_unique_underlyings_not_deduplicated": total_underlyings,
        "sum_of_file_unique_series_not_deduplicated": total_series,
        "duplicate_series_rows": total_duplicates, "schema_failure_count": schema_failures,
        "preliminary_final_pairs": comparisons, "preliminary_final_pair_count": len(comparisons),
        "file_summaries": file_summaries,
        "eod_delivery_expectation_et": "typically 00:30-01:00 next morning; actual first receipt not supplied by public sample",
        "preliminary_semantics": "OPRA-sourced total industry volume and open interest; may differ from final",
        "final_semantics": "OCC-sourced authoritative total industry volume and open interest per specification",
        "historical_convention_breaks": {
            "C1_open_interest_previous_open_interest_shifted_one_day_through": "2019-10-04",
            "C2_open_interest_previous_open_interest_shifted_one_day_through": "2018-05-11",
            "C2_total_industry_volume_doubled_through": "2018-05-11",
            "C1_total_exchange_volume_formula_through": "2019-10-04",
            "C1_previous_close_exchange_only_through": "2019-10-04",
            "C2_previous_close_exchange_only_through": "2018-05-11",
            "C1_global_trading_hours_available_from": "2023-12-11",
        },
        "strict_pit": False, "historical_coverage_proven": False, "first_receipt_proven": False,
        "delisted_underlying_coverage_proven": False, "raw_rows_persisted": False,
        "raw_symbols_persisted": False, "decision": "SCHEMA_SAMPLE_ONLY; no feature or return test authorized",
    }


def download_sample(url: str = SAMPLE_URL, timeout: int = 60) -> tuple[bytes, dict[str, str], str]:
    request = Request(url, headers={
        "User-Agent": "jafelix81/NuevaEstrategia Smart Money Research (research-only)",
        "Accept": "application/zip,application/octet-stream,*/*", "Accept-Encoding": "identity",
    })
    with urlopen(request, timeout=timeout) as response:
        payload = response.read(MAX_COMPRESSED_BYTES + 1)
        if len(payload) > MAX_COMPRESSED_BYTES:
            raise ValueError("download_exceeds_compressed_limit")
        return payload, dict(response.headers.items()), response.geturl()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="phase168_output")
    parser.add_argument("--url", default=SAMPLE_URL)
    args = parser.parse_args()
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    try:
        raw, headers, final_url = download_sample(args.url)
        summary = audit_archive(raw, headers, final_url=final_url)
    except (HTTPError, URLError, TimeoutError, ValueError, zipfile.BadZipFile) as exc:
        summary = {"phase": 168, "status": "BLOCKED_SAMPLE_RETRIEVAL_OR_PARSE",
                   "sample_url": args.url, "error_type": type(exc).__name__, "error": str(exc)[:500],
                   "strict_pit": False, "raw_rows_persisted": False, "raw_symbols_persisted": False}
    path = output / "phase168_cboe_openclose_eod_sample_summary.json"
    path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if str(summary.get("status", "")).startswith("PASS_") else 2


if __name__ == "__main__":
    raise SystemExit(main())

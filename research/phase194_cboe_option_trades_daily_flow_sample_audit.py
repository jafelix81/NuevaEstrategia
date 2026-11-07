#!/usr/bin/env python3
"""Phase 194: Cboe Option Trades daily-flow sample audit with opaque time quarantine.

The public sample is parsed in memory. market_date is normalized for daily
aggregation; quote_datetime is never interpreted as a timestamp. Only hashes,
counts and aggregate NBBO-side diagnostics are persisted.
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
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.request import Request, urlopen

from research.phase170_cboe_option_trades_public_sample_audit import (
    BASE_FIELDS,
    CALCS_FIELDS,
    MAX_COMPRESSED_BYTES,
    MAX_UNCOMPRESSED_BYTES,
    SOURCE_URL,
    classify_trade_vs_nbbo,
    schema_check,
)

MAX_DOWNLOAD_BYTES = 100_000_000
TIME_ONLY_RE = re.compile(r"(?P<first>\d{2}):(?P<second>\d{2})\.(?P<digit>\d)")


def text_value(value: object) -> str:
    return "" if value is None else str(value).strip()


def parse_market_date(value: object) -> date:
    raw = text_value(value)
    for fmt in ("%m/%d/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            pass
    raise ValueError("market_date_unparsed")


def parse_integer(value: object, field: str, blank_ok: bool = False) -> int | None:
    raw = text_value(value)
    if not raw and blank_ok:
        return None
    if not re.fullmatch(r"-?\d+", raw):
        raise ValueError(f"invalid_integer:{field}")
    return int(raw)


def parse_decimal(value: object, field: str, blank_ok: bool = False) -> Decimal | None:
    raw = text_value(value)
    if not raw and blank_ok:
        return None
    try:
        parsed = Decimal(raw)
    except InvalidOperation as exc:
        raise ValueError(f"invalid_decimal:{field}") from exc
    if not parsed.is_finite():
        raise ValueError(f"nonfinite_decimal:{field}")
    return parsed


def filename_market_date(member_name: str) -> date | None:
    base = member_name.replace("\\", "/").rsplit("/", 1)[-1]
    match = re.search(r"_(\d{4}-\d{2}-\d{2})\.csv$", base, re.I)
    if not match:
        return None
    try:
        return date.fromisoformat(match.group(1))
    except ValueError:
        return None


def audit_member(member_name: str, payload: bytes) -> dict[str, object]:
    try:
        decoded = payload.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("csv_not_utf8") from exc
    reader = csv.DictReader(io.StringIO(decoded, newline=""))
    headers = [str(x).strip().lower() for x in (reader.fieldnames or [])]
    schema = schema_check(headers)
    result: dict[str, object] = {
        "member_basename": member_name.replace("\\", "/").rsplit("/", 1)[-1],
        "member_sha256": hashlib.sha256(payload).hexdigest(),
        **schema,
        "row_count_including_blank_padding": 0,
        "nonblank_trade_rows": 0,
        "all_columns_blank_rows": 0,
        "trailing_all_columns_blank_rows": 0,
        "all_blank_rows_only_trailing": False,
        "internal_blank_row_detected": False,
        "first_nonblank_row_index": None,
        "last_nonblank_row_index": None,
        "market_date_format_counts": {},
        "market_date_filename_match_rows": 0,
        "market_date_filename_mismatch_rows": 0,
        "distinct_market_dates": 0,
        "market_date_min": None,
        "market_date_max": None,
        "quote_time_shape_signature_counts": {},
        "quote_time_length_counts": {},
        "quote_time_only_shape_rows": 0,
        "quote_time_blank_rows": 0,
        "quote_time_other_shape_rows": 0,
        "quote_time_hhmm_range_valid_rows": 0,
        "quote_time_hhmm_range_invalid_rows": 0,
        "quote_time_mmss_range_valid_rows": 0,
        "quote_time_first_component_gt59_rows": 0,
        "quote_time_second_component_gt59_rows": 0,
        "quote_time_semantics_assigned": False,
        "quote_time_values_persisted": False,
        "underlying_count": 0,
        "contract_count": 0,
        "valid_trade_rows": 0,
        "invalid_trade_rows": 0,
        "trade_key_count": 0,
        "duplicate_trade_key_rows": 0,
        "trade_size_sum_contracts": 0,
        "trade_price_times_size_sum_no_multiplier": "0",
        "trade_condition_counts": {},
        "trade_vs_nbbo_counts": {},
        "contract_volume_by_nbbo_class": {},
        "at_ask_contract_volume": 0,
        "at_bid_contract_volume": 0,
        "candidate_signed_contract_volume": 0,
        "at_ask_price_times_size_no_multiplier": "0",
        "at_bid_price_times_size_no_multiplier": "0",
        "candidate_signed_price_times_size_no_multiplier": "0",
        "unclassified_contract_volume": 0,
        "nonzero_cancel_condition_rows": 0,
        "blank_cancel_condition_rows": 0,
        "adjusted_root_candidate_rows": 0,
        "calcs_zero_counts": {},
        "calcs_blank_counts": {},
        "parse_error_counts": {},
        "first_parse_error": None,
        "core_trade_rows_sha256": None,
        "member_row_gate_pass": False,
        "raw_rows_persisted": False,
        "raw_symbols_persisted": False,
        "raw_contracts_persisted": False,
    }
    if schema["schema_status"] != "PASS":
        result["parse_error_counts"] = {"schema_gate_failed": 1}
        return result

    filename_day = filename_market_date(member_name)
    seen_blank = False
    internal_blank = False
    blank_rows = nonblank_rows = valid_rows = invalid_rows = 0
    first_nonblank = last_nonblank = None
    market_formats: Counter[str] = Counter()
    market_dates: set[date] = set()
    quote_shapes: Counter[str] = Counter()
    quote_lengths: Counter[str] = Counter()
    quote_time_shape = quote_time_blank = quote_time_other = 0
    hhmm_valid = hhmm_invalid = mmss_valid = first_gt59 = second_gt59 = 0
    underlyings: set[str] = set()
    contracts: set[tuple[str, ...]] = set()
    trade_keys: set[tuple[str, int, int]] = set()
    condition_counts: Counter[str] = Counter()
    quote_counts: Counter[str] = Counter()
    volume_by_class: Counter[str] = Counter()
    calcs_zero: Counter[str] = Counter()
    calcs_blank: Counter[str] = Counter()
    parse_errors: Counter[str] = Counter()
    core_digest = hashlib.sha256()
    filename_matches = filename_mismatches = 0
    size_sum = 0
    price_size_sum = Decimal("0")
    ask_volume = bid_volume = 0
    ask_price_size = bid_price_size = Decimal("0")
    unclassified_volume = 0
    nonzero_cancel = blank_cancel = adjusted_root = 0

    for row_index, raw_row in enumerate(reader, 1):
        result["row_count_including_blank_padding"] += 1
        row = {str(k).strip().lower(): v for k, v in raw_row.items() if k is not None}
        all_blank = all(not text_value(row.get(field)) for field in headers)
        if all_blank:
            blank_rows += 1
            seen_blank = True
            continue
        if seen_blank:
            internal_blank = True
        nonblank_rows += 1
        if first_nonblank is None:
            first_nonblank = row_index
        last_nonblank = row_index

        canonical = "\x1f".join(text_value(row.get(field)) for field in BASE_FIELDS)
        core_digest.update(canonical.encode("utf-8"))
        core_digest.update(b"\n")

        md_raw = text_value(row.get("market_date"))
        qt_raw = text_value(row.get("quote_datetime"))
        if not md_raw:
            market_formats["blank"] += 1
        elif re.fullmatch(r"\d{1,2}/\d{1,2}/\d{4}", md_raw):
            market_formats["us_m_d_yyyy"] += 1
        elif re.fullmatch(r"\d{4}-\d{2}-\d{2}", md_raw):
            market_formats["iso_yyyy_mm_dd"] += 1
        else:
            market_formats["other"] += 1

        if not qt_raw:
            quote_time_blank += 1
        else:
            quote_lengths[str(len(qt_raw))] += 1
            signature = "".join("9" if ch.isdigit() else "A" if ch.isalpha() else ch for ch in qt_raw)
            quote_shapes[signature] += 1
            match = TIME_ONLY_RE.fullmatch(qt_raw)
            if match:
                quote_time_shape += 1
                first = int(match.group("first"))
                second = int(match.group("second"))
                if first <= 23 and second <= 59:
                    hhmm_valid += 1
                else:
                    hhmm_invalid += 1
                if first <= 59 and second <= 59:
                    mmss_valid += 1
                if first > 59:
                    first_gt59 += 1
                if second > 59:
                    second_gt59 += 1
            else:
                quote_time_other += 1

        row_bad = False
        extra_values = raw_row.get(None)
        if isinstance(extra_values, list) and extra_values:
            row_bad = True
            parse_errors["extra_csv_fields"] += 1
        missing_required = [
            field for field in BASE_FIELDS
            if field in row and row.get(field) is None
        ]
        if missing_required:
            row_bad = True
            parse_errors["missing_required_values"] += 1

        try:
            symbol = text_value(row.get("underlying_symbol"))
            root = text_value(row.get("root"))
            option_type = text_value(row.get("option_type")).upper()
            market_day = parse_market_date(md_raw)
            expiry = parse_market_date(row.get("expiration"))
            strike = parse_decimal(row.get("strike"), "strike")
            sequence = parse_integer(row.get("sequence_number"), "sequence_number")
            exchange = parse_integer(row.get("exchange_id"), "exchange_id")
            size = parse_integer(row.get("trade_size"), "trade_size")
            price = parse_decimal(row.get("trade_price"), "trade_price")
            condition = parse_integer(row.get("trade_condition_id"), "trade_condition_id")
            cancel_condition = parse_integer(row.get("canceled_trade_condition_id"), "canceled_trade_condition_id", blank_ok=True)
            bid = parse_decimal(row.get("best_bid"), "best_bid", blank_ok=True)
            ask = parse_decimal(row.get("best_ask"), "best_ask", blank_ok=True)
            if not symbol or not root or option_type not in {"C", "P"}:
                raise ValueError("contract_identity_invalid")
            if strike is None or strike <= 0 or size is None or size <= 0 or price is None or price < 0:
                raise ValueError("trade_economics_invalid")
            if sequence is None or exchange is None or condition is None or min(sequence, exchange, condition) < 0:
                raise ValueError("trade_key_or_condition_invalid")
            if any(value is not None and value < 0 for value in (bid, ask)):
                raise ValueError("negative_nbbo")
            if cancel_condition is None:
                blank_cancel += 1
            elif cancel_condition != 0:
                nonzero_cancel += 1
            if any(ch.isdigit() for ch in root):
                adjusted_root += 1

            if filename_day is not None:
                if market_day == filename_day:
                    filename_matches += 1
                else:
                    filename_mismatches += 1
            market_dates.add(market_day)
            underlyings.add(symbol)
            contracts.add((symbol, root, expiry.isoformat(), str(strike.normalize()), option_type))
            trade_keys.add((market_day.isoformat(), sequence, exchange))
            condition_counts[str(condition)] += 1
            size_sum += size
            price_size = price * size
            price_size_sum += price_size
            quote_class = classify_trade_vs_nbbo(price, bid, ask)
            quote_counts[quote_class] += 1
            volume_by_class[quote_class] += size
            if quote_class == "at_ask_candidate":
                ask_volume += size
                ask_price_size += price_size
            elif quote_class == "at_bid_candidate":
                bid_volume += size
                bid_price_size += price_size
            else:
                unclassified_volume += size

            if schema["calcs_included"]:
                for field in CALCS_FIELDS:
                    value = parse_decimal(row.get(field), field, blank_ok=True)
                    if value is None:
                        calcs_blank[field] += 1
                    elif value == 0:
                        calcs_zero[field] += 1

            if not row_bad:
                valid_rows += 1
            else:
                invalid_rows += 1
        except (ValueError, TypeError) as exc:
            reason = str(exc) or type(exc).__name__
            parse_errors[reason] += 1
            if result["first_parse_error"] is None:
                result["first_parse_error"] = reason
            invalid_rows += 1

    trailing_blank_rows = blank_rows if not internal_blank else 0
    blank_only_trailing = blank_rows > 0 and not internal_blank
    duplicate_rows = max(0, valid_rows - len(trade_keys))
    market_min = min(market_dates).isoformat() if market_dates else None
    market_max = max(market_dates).isoformat() if market_dates else None
    member_gate = (
        schema["schema_status"] == "PASS"
        and nonblank_rows > 0
        and valid_rows == nonblank_rows
        and not internal_blank
        and filename_mismatches == 0
        and len(market_dates) == 1
    )

    result.update({
        "row_count_including_blank_padding": nonblank_rows + blank_rows,
        "nonblank_trade_rows": nonblank_rows,
        "all_columns_blank_rows": blank_rows,
        "trailing_all_columns_blank_rows": trailing_blank_rows,
        "all_blank_rows_only_trailing": blank_only_trailing,
        "internal_blank_row_detected": internal_blank,
        "first_nonblank_row_index": first_nonblank,
        "last_nonblank_row_index": last_nonblank,
        "market_date_format_counts": dict(sorted(market_formats.items())),
        "market_date_filename_match_rows": filename_matches,
        "market_date_filename_mismatch_rows": filename_mismatches,
        "distinct_market_dates": len(market_dates),
        "market_date_min": market_min,
        "market_date_max": market_max,
        "quote_time_shape_signature_counts": dict(sorted(quote_shapes.items())),
        "quote_time_length_counts": dict(sorted(quote_lengths.items(), key=lambda item: int(item[0]))),
        "quote_time_only_shape_rows": quote_time_shape,
        "quote_time_blank_rows": quote_time_blank,
        "quote_time_other_shape_rows": quote_time_other,
        "quote_time_hhmm_range_valid_rows": hhmm_valid,
        "quote_time_hhmm_range_invalid_rows": hhmm_invalid,
        "quote_time_mmss_range_valid_rows": mmss_valid,
        "quote_time_first_component_gt59_rows": first_gt59,
        "quote_time_second_component_gt59_rows": second_gt59,
        "underlying_count": len(underlyings),
        "contract_count": len(contracts),
        "valid_trade_rows": valid_rows,
        "invalid_trade_rows": invalid_rows,
        "trade_key_count": len(trade_keys),
        "duplicate_trade_key_rows": duplicate_rows,
        "trade_size_sum_contracts": size_sum,
        "trade_price_times_size_sum_no_multiplier": str(price_size_sum),
        "trade_condition_counts": dict(sorted(condition_counts.items())),
        "trade_vs_nbbo_counts": dict(sorted(quote_counts.items())),
        "contract_volume_by_nbbo_class": dict(sorted(volume_by_class.items())),
        "at_ask_contract_volume": ask_volume,
        "at_bid_contract_volume": bid_volume,
        "candidate_signed_contract_volume": ask_volume - bid_volume,
        "at_ask_price_times_size_no_multiplier": str(ask_price_size),
        "at_bid_price_times_size_no_multiplier": str(bid_price_size),
        "candidate_signed_price_times_size_no_multiplier": str(ask_price_size - bid_price_size),
        "unclassified_contract_volume": unclassified_volume,
        "nonzero_cancel_condition_rows": nonzero_cancel,
        "blank_cancel_condition_rows": blank_cancel,
        "adjusted_root_candidate_rows": adjusted_root,
        "calcs_zero_counts": dict(sorted(calcs_zero.items())),
        "calcs_blank_counts": dict(sorted(calcs_blank.items())),
        "parse_error_counts": dict(sorted(parse_errors.items())),
        "core_trade_rows_sha256": core_digest.hexdigest(),
        "member_row_gate_pass": member_gate,
        "raw_rows_persisted": False,
        "raw_symbols_persisted": False,
        "raw_contracts_persisted": False,
    })
    return result


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
                        if not nested_info.is_dir() and nested_info.filename.lower().endswith(".csv"):
                            found.append((nested_info.filename, nested.read(nested_info)))
    return found


def audit_archive(raw_zip: bytes, retrieved_at_utc: str | None = None) -> dict[str, object]:
    members = [(name, audit_member(name, payload)) for name, payload in csv_members(raw_zip)]
    core_hashes = [item["core_trade_rows_sha256"] for _, item in members]
    row_counts = [item["nonblank_trade_rows"] for _, item in members]
    core_match = bool(members) and len(set(core_hashes)) == 1 and len(set(row_counts)) == 1
    members_pass = bool(members) and all(item["member_row_gate_pass"] for _, item in members)
    daily_candidate = members_pass and core_match
    return {
        "phase": 194,
        "source": "Cboe Option Trades public sample",
        "sample_url": SOURCE_URL,
        "archive_sha256": hashlib.sha256(raw_zip).hexdigest(),
        "compressed_bytes": len(raw_zip),
        "retrieved_at_utc": retrieved_at_utc or datetime.now(timezone.utc).isoformat(),
        "member_count": len(members),
        "member_audits": [item for _, item in members],
        "core_trade_rows_match_across_members": core_match,
        "daily_flow_measurement_candidate": daily_candidate,
        "signed_flow_feature_admitted": False,
        "quote_time_semantics_admitted": False,
        "trade_condition_mapping_verified": False,
        "first_receipt_verified": False,
        "historical_coverage_verified": False,
        "strict_pit_admitted": False,
        "alpha_admission": False,
        "holdout_used": False,
        "production_changed": False,
        "vendor_contact_or_purchase": False,
        "f80_frozen": True,
        "raw_archive_persisted": False,
        "raw_rows_persisted": False,
        "raw_symbols_persisted": False,
        "raw_contracts_persisted": False,
        "raw_clock_values_persisted": False,
        "status": "DAILY_SAMPLE_ROW_GATE_PASS_TIME_FIELD_QUARANTINED" if daily_candidate else "SAMPLE_ROW_GATE_FAIL",
        "decision": "A daily NBBO-side measurement may be feasible from the sample if the row and cross-member gates pass. quote_datetime remains an opaque time-only field and is not converted; trade-condition semantics, adjusted-contract deliverables, first receipt, historical vintages and historical coverage remain unresolved. No signed-flow feature or alpha test is admitted."
    }


def download_sample() -> bytes:
    request = Request(SOURCE_URL, headers={"User-Agent": "NuevaEstrategia research audit"})
    with urlopen(request, timeout=60) as response:
        payload = response.read(MAX_DOWNLOAD_BYTES + 1)
    if len(payload) > MAX_DOWNLOAD_BYTES:
        raise ValueError("sample_download_exceeds_limit")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="phase194_output")
    args = parser.parse_args()
    raw_zip = download_sample()
    summary = audit_archive(raw_zip)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "phase194_cboe_option_trades_daily_flow_sample_audit.json"
    output_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Phase 171: value-free Cboe Option Trades date/time shape audit.

Reuses Phase 170's bounded ZIP-member reader and schema contract. Raw rows,
symbols, contracts, timestamps and trade values are never persisted.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from research.phase170_cboe_option_trades_public_sample_audit import (
    SOURCE_URL,
    csv_members,
    schema_check,
)

ET = ZoneInfo("America/New_York")
MAX_DOWNLOAD_BYTES = 100_000_000

CORE_FIELDS = (
    "underlying_symbol", "sequence_number", "root", "expiration", "strike",
    "option_type", "exchange_id", "trade_size", "trade_price", "trade_condition_id",
)

QUOTE_FORMATS = (
    ("%m/%d/%Y %I:%M:%S.%f %p", "us_12h_fractional"),
    ("%m/%d/%Y %I:%M:%S %p", "us_12h"),
    ("%m/%d/%Y %H:%M:%S.%f", "us_24h_fractional"),
    ("%m/%d/%Y %H:%M:%S", "us_24h"),
    ("%Y-%m-%d %H:%M:%S.%f", "iso_space_fractional"),
    ("%Y-%m-%d %H:%M:%S", "iso_space"),
    ("%Y-%m-%dT%H:%M:%S.%f", "iso_t_fractional"),
    ("%Y-%m-%dT%H:%M:%S", "iso_t"),
    ("%Y-%m-%dT%H:%M:%S.%f%z", "iso_t_fractional_offset"),
    ("%Y-%m-%dT%H:%M:%S%z", "iso_t_offset"),
)

def _text(value: object) -> str:
    return "" if value is None else str(value).strip()

def shape_signature(value: object) -> str:
    """Replace every digit/letter with a class marker; retain punctuation only."""
    raw = _text(value)
    return "".join("9" if ch.isdigit() else "A" if ch.isalpha() else ch for ch in raw)

def market_date_shape(value: object) -> str:
    raw = _text(value)
    if not raw:
        return "blank"
    if re.fullmatch(r"\d{1,2}/\d{1,2}/\d{4}", raw):
        return "us_m_d_yyyy"
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw):
        return "yyyy_mm_dd"
    if re.fullmatch(r"\d{8}", raw):
        return "yyyymmdd"
    return "other"

def quote_datetime_shape(value: object) -> str:
    raw = _text(value)
    if not raw:
        return "blank"
    if re.fullmatch(r"\d{1,2}/\d{1,2}/\d{4} \d{1,2}:\d{2}:\d{2}(?:\.\d+)?\s*(?:AM|PM)", raw, re.I):
        return "us_12h"
    if re.fullmatch(r"\d{1,2}/\d{1,2}/\d{4} \d{1,2}:\d{2}:\d{2}(?:\.\d+)?", raw):
        return "us_24h"
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?", raw):
        return "iso"
    return "other"

def parse_market_date(value: object) -> tuple[date | None, str]:
    raw = _text(value)
    if not raw:
        return None, "blank"
    try:
        if re.fullmatch(r"\d{1,2}/\d{1,2}/\d{4}", raw):
            return datetime.strptime(raw, "%m/%d/%Y").date(), "us_m_d_yyyy"
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw):
            return date.fromisoformat(raw), "yyyy_mm_dd"
        if re.fullmatch(r"\d{8}", raw):
            return datetime.strptime(raw, "%Y%m%d").date(), "yyyymmdd"
    except ValueError:
        return None, "invalid_calendar_date"
    return None, "unrecognized_shape"

def parse_quote_datetime(value: object) -> tuple[datetime | None, str]:
    raw = _text(value)
    if not raw:
        return None, "blank"
    for fmt, label in QUOTE_FORMATS:
        try:
            parsed = datetime.strptime(raw, fmt)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=ET)
            else:
                parsed = parsed.astimezone(ET)
            return parsed, label
        except ValueError:
            continue
    return None, "unparsed"

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
    decoded = payload.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(decoded, newline=""))
    headers = reader.fieldnames or []
    schema = schema_check(headers)
    summary: dict[str, object] = {
        "member_basename": member_name.replace("\\", "/").rsplit("/", 1)[-1],
        "member_sha256": hashlib.sha256(payload).hexdigest(),
        **schema,
        "row_count": 0,
        "market_date_shape_counts": {},
        "market_date_parse_counts": {},
        "market_date_distinct_count": 0,
        "market_date_min": None,
        "market_date_max": None,
        "market_date_filename_match_rows": 0,
        "market_date_filename_mismatch_rows": 0,
        "quote_datetime_shape_counts": {},
        "quote_datetime_signature_counts_top12": [],
        "quote_datetime_length_counts": {},
        "quote_datetime_parse_counts": {},
        "quote_datetime_min_et": None,
        "quote_datetime_max_et": None,
        "quote_datetime_market_date_comparable_rows": 0,
        "quote_datetime_market_date_match_rows": 0,
        "quote_datetime_market_date_mismatch_rows": 0,
        "date_time_joint_blankness": {},
        "core_required_blank_field_counts": {},
        "both_date_fields_blank_core_complete_rows": 0,
        "both_date_fields_blank_core_incomplete_rows": 0,
        "raw_rows_persisted": False,
        "raw_symbols_persisted": False,
        "raw_contracts_persisted": False,
        "raw_timestamps_persisted": False,
    }
    if schema["schema_status"] != "PASS":
        return summary

    market_shapes: Counter[str] = Counter()
    market_parses: Counter[str] = Counter()
    quote_shapes: Counter[str] = Counter()
    quote_signatures: Counter[str] = Counter()
    quote_lengths: Counter[str] = Counter()
    quote_parses: Counter[str] = Counter()
    joint: Counter[str] = Counter()
    core_blanks: Counter[str] = Counter()
    market_dates: set[date] = set()
    min_qdt: datetime | None = None
    max_qdt: datetime | None = None
    filename_date = filename_market_date(member_name)
    filename_match = filename_mismatch = comparable = date_matches = date_mismatches = 0
    both_blank_complete = both_blank_incomplete = 0

    for raw_row in reader:
        summary["row_count"] = int(summary["row_count"]) + 1
        row = {str(k).strip().lower(): v for k, v in raw_row.items() if k is not None}
        md_raw = _text(row.get("market_date"))
        qdt_raw = _text(row.get("quote_datetime"))
        md_shape = market_date_shape(md_raw)
        qdt_shape = quote_datetime_shape(qdt_raw)
        market_shapes[md_shape] += 1
        quote_shapes[qdt_shape] += 1
        if qdt_raw:
            quote_signatures[shape_signature(qdt_raw)] += 1
            quote_lengths[str(len(qdt_raw))] += 1

        if not md_raw and not qdt_raw:
            joint["both_blank"] += 1
        elif not md_raw:
            joint["market_date_blank_only"] += 1
        elif not qdt_raw:
            joint["quote_datetime_blank_only"] += 1
        else:
            joint["both_nonblank"] += 1

        core_complete = True
        for field in CORE_FIELDS:
            if not _text(row.get(field)):
                core_blanks[field] += 1
                core_complete = False
        if not md_raw and not qdt_raw:
            if core_complete:
                both_blank_complete += 1
            else:
                both_blank_incomplete += 1

        md, md_label = parse_market_date(md_raw)
        market_parses[md_label] += 1
        if md is not None:
            market_dates.add(md)
            if filename_date is not None:
                if md == filename_date:
                    filename_match += 1
                else:
                    filename_mismatch += 1

        qdt, qdt_label = parse_quote_datetime(qdt_raw)
        quote_parses[qdt_label] += 1
        if qdt is not None:
            min_qdt = qdt if min_qdt is None or qdt < min_qdt else min_qdt
            max_qdt = qdt if max_qdt is None or qdt > max_qdt else max_qdt
        if md is not None and qdt is not None:
            comparable += 1
            if md == qdt.date():
                date_matches += 1
            else:
                date_mismatches += 1

    top_signatures = [
        {"signature": signature, "count": count}
        for signature, count in sorted(quote_signatures.items(), key=lambda item: (-item[1], item[0]))[:12]
    ]
    summary.update({
        "market_date_shape_counts": dict(sorted(market_shapes.items())),
        "market_date_parse_counts": dict(sorted(market_parses.items())),
        "market_date_distinct_count": len(market_dates),
        "market_date_min": min(market_dates).isoformat() if market_dates else None,
        "market_date_max": max(market_dates).isoformat() if market_dates else None,
        "market_date_filename_match_rows": filename_match,
        "market_date_filename_mismatch_rows": filename_mismatch,
        "quote_datetime_shape_counts": dict(sorted(quote_shapes.items())),
        "quote_datetime_signature_counts_top12": top_signatures,
        "quote_datetime_length_counts": dict(sorted(quote_lengths.items(), key=lambda item: int(item[0]))),
        "quote_datetime_parse_counts": dict(sorted(quote_parses.items())),
        "quote_datetime_min_et": min_qdt.isoformat() if min_qdt else None,
        "quote_datetime_max_et": max_qdt.isoformat() if max_qdt else None,
        "quote_datetime_market_date_comparable_rows": comparable,
        "quote_datetime_market_date_match_rows": date_matches,
        "quote_datetime_market_date_mismatch_rows": date_mismatches,
        "date_time_joint_blankness": dict(sorted(joint.items())),
        "core_required_blank_field_counts": dict(sorted(core_blanks.items())),
        "both_date_fields_blank_core_complete_rows": both_blank_complete,
        "both_date_fields_blank_core_incomplete_rows": both_blank_incomplete,
    })
    return summary

def audit_archive(raw_zip: bytes, retrieved_at_utc: str | None = None) -> dict[str, object]:
    members = csv_members(raw_zip)
    member_audits = [audit_member(name, payload) for name, payload in members]
    return {
        "phase": 171,
        "source": "Cboe Option Trades",
        "sample_url": SOURCE_URL,
        "archive_sha256": hashlib.sha256(raw_zip).hexdigest(),
        "compressed_bytes": len(raw_zip),
        "retrieved_at_utc": retrieved_at_utc or datetime.now(timezone.utc).isoformat(),
        "member_count": len(member_audits),
        "member_audits": member_audits,
        "status": "DIAGNOSTIC_COMPLETE",
        "date_time_shape_resolved": all(
            audit["schema_status"] == "PASS"
            and audit["quote_datetime_parse_counts"].get("unparsed", 0) == 0
            and audit["quote_datetime_parse_counts"].get("blank", 0) == 0
            for audit in member_audits
        ) if member_audits else False,
        "alpha_admission": False,
        "strict_pit": False,
        "raw_archive_persisted": False,
        "raw_rows_persisted": False,
        "raw_symbols_persisted": False,
        "raw_contracts_persisted": False,
        "raw_timestamps_persisted": False,
        "vendor_contact_or_purchase": False,
        "production_change": False,
        "f80_change": False,
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
    parser.add_argument("--output-dir", default="phase171_output")
    args = parser.parse_args()
    raw_zip = download_sample()
    summary = audit_archive(raw_zip)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "phase171_cboe_option_trades_datetime_shape_summary.json"
    output_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

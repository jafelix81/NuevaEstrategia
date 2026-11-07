#!/usr/bin/env python3
"""Phase 175: conservative locale/format diagnostics for Cboe Option Quotes.

Only aggregate format counts and date ranges are emitted. Raw rows, symbols,
contract identifiers, strikes, expirations and timestamps are never persisted.
No non-ISO date is silently selected for research use.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import zipfile
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from research import phase174_cboe_option_quotes_sample_audit as phase174

EXPIRATION_FORMATS = (
    ("iso_extended", "%Y-%m-%d"),
    ("iso_basic", "%Y%m%d"),
    ("us_slash", "%m/%d/%Y"),
    ("dmy_slash", "%d/%m/%Y"),
    ("year_slash", "%Y/%m/%d"),
    ("us_dash", "%m-%d-%Y"),
)
QUOTE_DATETIME_FORMATS = (
    ("iso_minute", "%Y-%m-%d %H:%M"),
    ("iso_second", "%Y-%m-%d %H:%M:%S"),
    ("iso_fraction", "%Y-%m-%d %H:%M:%S.%f"),
    ("us_slash_minute", "%m/%d/%Y %H:%M"),
    ("us_slash_second", "%m/%d/%Y %H:%M:%S"),
    ("us_slash_fraction", "%m/%d/%Y %H:%M:%S.%f"),
    ("dmy_slash_minute", "%d/%m/%Y %H:%M"),
    ("dmy_slash_second", "%d/%m/%Y %H:%M:%S"),
    ("dmy_slash_fraction", "%d/%m/%Y %H:%M:%S.%f"),
)


def _candidate_interpretations(raw: str, formats: tuple[tuple[str, str], ...]):
    found: dict[str, datetime] = {}
    for label, fmt in formats:
        try:
            found[label] = datetime.strptime(raw.strip(), fmt)
        except (TypeError, ValueError):
            continue
    distinct = {value.isoformat() for value in found.values()}
    if not found:
        classification = "no_parse"
        unique_value = None
    elif len(distinct) > 1:
        classification = "ambiguous_multiple_interpretations"
        unique_value = None
    elif len(found) > 1:
        classification = "equivalent_multiple_formats"
        unique_value = next(iter(found.values()))
    else:
        classification = "single_format_interpretation"
        unique_value = next(iter(found.values()))
    return found, classification, unique_value


def diagnose_csv_bytes(payload: bytes) -> dict[str, Any]:
    text = payload.decode("utf-8-sig")
    reader = csv.reader(io.StringIO(text, newline=""))
    try:
        header = [phase174.normalize_header(x) for x in next(reader)]
    except StopIteration:
        return {"diagnostic_complete": False, "reason": "empty_member"}
    if len(set(header)) != len(header):
        return {"diagnostic_complete": False, "reason": "duplicate_header"}
    try:
        qidx, eidx = header.index("quote_datetime"), header.index("expiration")
    except ValueError:
        return {"diagnostic_complete": False, "reason": "date_fields_missing"}

    rows = short_rows = long_rows = empty_rows = 0
    exp_classes: Counter[str] = Counter()
    quote_classes: Counter[str] = Counter()
    exp_formats: Counter[str] = Counter()
    quote_formats: Counter[str] = Counter()
    quote_values: set[datetime] = set()
    expiration_values: set[datetime] = set()
    expiry_before_quote = expiry_same_quote = expiry_after_quote = 0
    date_relation_not_tested = 0

    for values in reader:
        if not values or all(str(x).strip() == "" for x in values):
            empty_rows += 1
            continue
        rows += 1
        if len(values) < len(header):
            short_rows += 1
            continue
        if len(values) > len(header):
            long_rows += 1
            continue

        raw_exp = str(values[eidx]).strip()
        raw_quote = str(values[qidx]).strip()
        exp_found, exp_class, exp_value = _candidate_interpretations(
            raw_exp, EXPIRATION_FORMATS
        ) if raw_exp else ({}, "missing", None)
        quote_found, quote_class, quote_value = _candidate_interpretations(
            raw_quote, QUOTE_DATETIME_FORMATS
        ) if raw_quote else ({}, "missing", None)
        exp_classes[exp_class] += 1
        quote_classes[quote_class] += 1
        exp_formats.update(exp_found.keys())
        quote_formats.update(quote_found.keys())

        if exp_value is not None:
            expiration_values.add(exp_value)
        if quote_value is not None:
            quote_values.add(quote_value)
        if exp_value is not None and quote_value is not None:
            if exp_value.date() < quote_value.date():
                expiry_before_quote += 1
            elif exp_value.date() == quote_value.date():
                expiry_same_quote += 1
            else:
                expiry_after_quote += 1
        else:
            date_relation_not_tested += 1

    return {
        "diagnostic_complete": True,
        "populated_rows": rows,
        "empty_rows": empty_rows,
        "short_rows": short_rows,
        "long_rows": long_rows,
        "expiration_interpretation_counts": dict(sorted(exp_classes.items())),
        "expiration_candidate_format_counts": dict(sorted(exp_formats.items())),
        "quote_datetime_interpretation_counts": dict(sorted(quote_classes.items())),
        "quote_datetime_candidate_format_counts": dict(sorted(quote_formats.items())),
        "expiration_unique_interpretation_count": len(expiration_values),
        "expiration_min_unique_interpretation": min(expiration_values).date().isoformat() if expiration_values else None,
        "expiration_max_unique_interpretation": max(expiration_values).date().isoformat() if expiration_values else None,
        "quote_datetime_unique_interpretation_count": len(quote_values),
        "quote_datetime_min_unique_interpretation": min(quote_values).isoformat() if quote_values else None,
        "quote_datetime_max_unique_interpretation": max(quote_values).isoformat() if quote_values else None,
        "expiry_before_quote_date_rows": expiry_before_quote,
        "expiry_same_as_quote_date_rows": expiry_same_quote,
        "expiry_after_quote_date_rows": expiry_after_quote,
        "date_relation_not_tested_rows": date_relation_not_tested,
        "raw_dates_persisted": False,
        "raw_timestamps_persisted": False,
        "raw_rows_persisted": False,
        "raw_symbols_persisted": False,
        "contract_keys_persisted": False,
    }


def audit_archive(payload: bytes) -> dict[str, Any]:
    original = phase174.audit_csv_bytes

    def instrumented(data: bytes, member_index: int = 0):
        result = original(data, member_index)
        result["date_locale_diagnostics"] = diagnose_csv_bytes(data)
        return result

    phase174.audit_csv_bytes = instrumented
    try:
        result = phase174.audit_archive(payload)
    finally:
        phase174.audit_csv_bytes = original

    diagnostics = [m.get("date_locale_diagnostics", {}) for m in result.get("members", [])]
    result["phase"] = 175
    result["date_locale_diagnostic_complete"] = bool(diagnostics) and all(
        d.get("diagnostic_complete", False) for d in diagnostics
    )
    result["date_locale_diagnostic_member_count"] = len(diagnostics)
    result["sample_admission"] = False
    result["pit_admission"] = False
    result["alpha_admission"] = False
    result["forward_returns_tested"] = False
    result["bootstrap_loo_tested"] = False
    result["chronological_oos_tested"] = False
    result["final_holdout_used"] = False
    result["production_changed"] = False
    result["f80_changed"] = False
    result["overall_status"] = (
        "DIAGNOSTIC_COMPLETE_SAMPLE_NOT_ADMITTED"
        if result["download_status"] == "PASS" and result["date_locale_diagnostic_complete"]
        else "DIAGNOSTIC_INCOMPLETE"
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="phase175_output/phase175_cboe_option_quotes_date_locale_audit.json")
    args = parser.parse_args()
    try:
        result = audit_archive(phase174.download_sample())
    except Exception as exc:
        result = {
            "phase": 175,
            "source": "Cboe Option Quotes / Option Quote Intervals",
            "download_status": "BLOCKED",
            "download_error_class": type(exc).__name__,
            "download_error_code": str(exc).split(":", 1)[0][:100],
            "date_locale_diagnostic_complete": False,
            "sample_admission": False,
            "pit_admission": False,
            "alpha_admission": False,
            "final_holdout_used": False,
            "production_changed": False,
            "f80_changed": False,
            "overall_status": "DIAGNOSTIC_INCOMPLETE",
        }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True), flush=True)
    return 0 if result.get("download_status") == "PASS" and result.get("date_locale_diagnostic_complete") else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Phase 200: field-level duplicate and negative Hidden/HiddenVol diagnostics.

Re-downloads only the six disputed SEC MIDAS quarters, extracts nested ZIP
containers by schema, and records duplicate-field differences plus negative
value distributions. Metadata/samples only; no PIT or alpha inference.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import time
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from itertools import chain
from pathlib import Path

from research.phase199_sec_midas_disputed_quarter_content_audit import (
    REQUIRED,
    detect_delimiter,
    download_archive,
    normalize_header,
)
from research.phase198_sec_midas_archive_inventory import fetch_sec_page, parse_inventory

QUARTERS = ("2014 Q2", "2016 Q1", "2016 Q2", "2016 Q3", "2016 Q4", "2019 Q4")
RANK_FIELDS = {"mcaprank", "turnrank", "volatilityrank", "pricerank"}
NUMERIC_FIELDS = (
    "mcaprank", "turnrank", "volatilityrank", "pricerank", "litvol('000)",
    "ordervol('000)", "hidden", "tradesforhidden", "hiddenvol('000)",
    "tradevolforhidden('000)", "cancels", "littrades", "oddlots",
    "tradesforoddlots", "oddlotvol('000)", "tradevolforoddLots('000)",
)
NEGATIVE_FIELDS = {
    "hidden": "tradesforhidden",
    "hiddenvol('000)": "tradevolforhidden('000)",
}


def parse_number(value: str) -> float | None:
    value = (value or "").strip()
    if value in ("", ".", "NA", "N/A", "NULL"):
        return None
    try:
        number = float(value.replace(",", ""))
    except ValueError:
        return None
    return number if math.isfinite(number) else None


def find_midas_member(content: bytes, nesting: int = 0) -> tuple[bytes, dict[str, object]]:
    archive_sha = hashlib.sha256(content).hexdigest()
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        bad_member = archive.testzip()
        if bad_member is not None:
            raise ValueError(f"zip_crc_failure:{bad_member}")
        members = [item for item in archive.infolist() if not item.is_dir()]
        layer = {
            "sha256": archive_sha,
            "bytes": len(content),
            "zip_crc_passed": True,
            "member_count": len(members),
            "members": [
                {"name": item.filename, "bytes": item.file_size, "crc32": f"{item.CRC:08x}"}
                for item in members
            ],
        }
        for item in members:
            with archive.open(item, "r") as stream:
                prefix = stream.read(8192).decode("utf-8-sig", errors="replace")
            first_line = prefix.splitlines()[0] if prefix.splitlines() else ""
            delimiter = detect_delimiter(first_line)
            try:
                header = next(csv.reader([first_line], delimiter=delimiter))
            except (StopIteration, csv.Error):
                continue
            if REQUIRED.issubset({normalize_header(value) for value in header}):
                data = archive.read(item)
                return data, {
                    "data_member": item.filename,
                    "container_depth": nesting,
                    "archive_layers": [layer],
                    "data_sha256": hashlib.sha256(data).hexdigest(),
                    "data_bytes": len(data),
                }
        nested = [item for item in members if item.filename.lower().endswith(".zip")]
        if len(nested) == 1 and nesting < 3:
            nested_bytes = archive.read(nested[0])
            data, metadata = find_midas_member(nested_bytes, nesting + 1)
            metadata["archive_layers"].insert(0, layer)
            metadata["container_depth"] = nesting + 1
            metadata["nested_member_path"] = nested[0].filename
            return data, metadata
        inventory = [{"name": item.filename, "bytes": item.file_size} for item in members]
        raise ValueError(f"no_schema_member_or_single_nested_zip:{inventory}")


def audit_csv_bytes(data: bytes, quarter: str) -> dict[str, object]:
    text = io.TextIOWrapper(io.BytesIO(data), encoding="utf-8-sig", errors="replace", newline="")
    first_line = text.readline()
    if not first_line:
        raise ValueError("empty_midas_csv")
    delimiter = detect_delimiter(first_line)
    reader = csv.reader(chain([first_line], text), delimiter=delimiter)
    header = next(reader)
    normalized = [normalize_header(value) for value in header]
    if len(normalized) != len(set(normalized)):
        raise ValueError("duplicate_normalized_header")
    missing = sorted(REQUIRED - set(normalized))
    if missing:
        raise ValueError(f"missing_required_columns:{missing}")
    idx = {name: i for i, name in enumerate(normalized)}

    rows = malformed = blank_rows = blank_ticker = invalid_date = 0
    dates: set[str] = set()
    tickers: set[str] = set()
    security_counts: Counter[str] = Counter()
    first_packed: dict[tuple[str, str, str], str] = {}
    key_counts: Counter[tuple[str, str, str]] = Counter()
    diff_by_key: dict[tuple[str, str, str], set[str]] = defaultdict(set)
    duplicate_examples: list[dict[str, object]] = []
    field_diff_groups: Counter[str] = Counter()
    negative: dict[str, dict[str, object]] = {
        field: {
            "count": 0, "histogram": Counter(), "min": None, "max": None,
            "denominator_zero_count": 0, "denominator_missing_count": 0,
            "denominator_negative_count": 0, "examples": [],
        }
        for field in NEGATIVE_FIELDS
    }
    nonnegative_ranges = {field: {"count": 0, "min": None, "max": None, "greater_than_one": 0}
                          for field in NEGATIVE_FIELDS}
    derived_volume_share = {"count": 0, "min": None, "max": None, "greater_than_one": 0,
                            "denominator_zero_count": 0, "negative_or_missing_rows": 0}
    numeric_invalid: Counter[str] = Counter()
    numeric_negative: Counter[str] = Counter()
    quarter_parts = quarter.split()
    year, qtr = int(quarter_parts[0]), int(quarter_parts[1][1])
    start_month = (qtr - 1) * 3 + 1
    start = f"{year:04d}-{start_month:02d}-01"
    end_month = start_month + 2
    if end_month == 12:
        end = f"{year:04d}-12-31"
    else:
        from datetime import date, timedelta
        end = (date(year, end_month + 1, 1) - timedelta(days=1)).isoformat()
    out_of_quarter = 0

    for raw in reader:
        if not raw or not any(value.strip() for value in raw):
            blank_rows += 1
            continue
        if len(raw) != len(header):
            malformed += 1
            continue
        ticker = raw[idx["ticker"]].strip().upper()
        day = raw[idx["date"]].strip()
        security = raw[idx["security"]].strip()
        if not ticker:
            blank_ticker += 1
            continue
        if len(day) == 8 and day.isdigit():
            day = f"{day[:4]}-{day[4:6]}-{day[6:]}"
        if len(day) >= 10:
            day = day[:10]
        if len(day) != 10 or day[4] != "-" or day[7] != "-":
            invalid_date += 1
            continue
        rows += 1
        dates.add(day)
        tickers.add(ticker)
        if security:
            security_counts[security] += 1
        if day < start or day > end:
            out_of_quarter += 1

        key = (ticker, day, security)
        packed = "\x1f".join(raw)
        if key not in first_packed:
            first_packed[key] = packed
            key_counts[key] = 1
        else:
            key_counts[key] += 1
            first = first_packed[key].split("\x1f")
            changed = [header[i] for i, (a, b) in enumerate(zip(first, raw)) if a != b]
            normalized_changed = {normalize_header(value) for value in changed}
            diff_by_key[key].update(normalized_changed)
            if len(duplicate_examples) < 20:
                duplicate_examples.append({
                    "ticker": ticker, "date": day, "security": security,
                    "changed_fields": changed,
                    "first_values": {header[i]: first[i] for i, value in enumerate(header)
                                     if normalize_header(value) in normalized_changed},
                    "duplicate_values": {header[i]: raw[i] for i, value in enumerate(header)
                                         if normalize_header(value) in normalized_changed},
                })

        for field in NUMERIC_FIELDS:
            number = parse_number(raw[idx[field]])
            if number is None:
                if raw[idx[field]].strip() not in ("", ".", "NA", "N/A", "NULL"):
                    numeric_invalid[field] += 1
            elif number < 0:
                numeric_negative[field] += 1

        for field, denominator_field in NEGATIVE_FIELDS.items():
            number = parse_number(raw[idx[field]])
            denominator = parse_number(raw[idx[denominator_field]])
            stats = negative[field]
            if number is not None and number < 0:
                stats["count"] += 1
                value_key = format(number, ".15g")
                stats["histogram"][value_key] = stats["histogram"].get(value_key, 0) + 1
                stats["min"] = number if stats["min"] is None else min(stats["min"], number)
                stats["max"] = number if stats["max"] is None else max(stats["max"], number)
                if denominator is None:
                    stats["denominator_missing_count"] += 1
                elif denominator == 0:
                    stats["denominator_zero_count"] += 1
                elif denominator < 0:
                    stats["denominator_negative_count"] += 1
                if len(stats["examples"]) < 12:
                    stats["examples"].append({
                        "ticker": ticker, "date": day, "security": security,
                        "value": number, "denominator_field": denominator_field,
                        "denominator_value": denominator,
                    })
            elif number is not None:
                rng = nonnegative_ranges[field]
                rng["count"] += 1
                rng["min"] = number if rng["min"] is None else min(rng["min"], number)
                rng["max"] = number if rng["max"] is None else max(rng["max"], number)
                if number > 1:
                    rng["greater_than_one"] += 1

        hidden_vol = parse_number(raw[idx["hiddenvol('000)"]])
        trade_vol = parse_number(raw[idx["tradevolforhidden('000)"]])
        if hidden_vol is not None and hidden_vol >= 0 and trade_vol is not None and trade_vol > 0:
            share = hidden_vol / trade_vol
            derived_volume_share["count"] += 1
            derived_volume_share["min"] = share if derived_volume_share["min"] is None else min(derived_volume_share["min"], share)
            derived_volume_share["max"] = share if derived_volume_share["max"] is None else max(derived_volume_share["max"], share)
            if share > 1:
                derived_volume_share["greater_than_one"] += 1
        else:
            derived_volume_share["negative_or_missing_rows"] += 1
            if trade_vol == 0:
                derived_volume_share["denominator_zero_count"] += 1

    duplicate_keys = [key for key, count in key_counts.items() if count > 1]
    exact_groups = sum(not diff_by_key[key] for key in duplicate_keys)
    rank_only_groups = sum(bool(diff_by_key[key]) and diff_by_key[key].issubset(RANK_FIELDS) for key in duplicate_keys)
    activity_groups = sum(bool(diff_by_key[key]) and bool(diff_by_key[key] - RANK_FIELDS) for key in duplicate_keys)
    for key in duplicate_keys:
        for field in diff_by_key[key]:
            field_diff_groups[field] += 1

    return {
        "quarter": quarter,
        "csv_sha256": hashlib.sha256(data).hexdigest(),
        "header": header,
        "header_sha256": hashlib.sha256("\x1f".join(header).encode()).hexdigest(),
        "rows_with_valid_ticker_and_date": rows,
        "unique_dates": len(dates),
        "min_date": min(dates) if dates else None,
        "max_date": max(dates) if dates else None,
        "unique_tickers": len(tickers),
        "security_class_counts": dict(sorted(security_counts.items())),
        "blank_rows": blank_rows,
        "malformed_rows": malformed,
        "blank_ticker_rows": blank_ticker,
        "invalid_date_rows": invalid_date,
        "out_of_quarter_rows": out_of_quarter,
        "duplicate_key_groups": len(duplicate_keys),
        "duplicate_rows_beyond_first": sum(key_counts[key] - 1 for key in duplicate_keys),
        "exact_duplicate_key_groups": exact_groups,
        "rank_only_conflicting_groups": rank_only_groups,
        "activity_conflicting_groups": activity_groups,
        "field_difference_group_counts": dict(sorted(field_diff_groups.items())),
        "duplicate_examples": duplicate_examples,
        "negative_fields": {
            field: {
                **{k: v for k, v in stats.items() if k != "histogram"},
                "histogram": dict(sorted(stats["histogram"].items())),
            }
            for field, stats in negative.items()
        },
        "nonnegative_value_ranges": nonnegative_ranges,
        "derived_hidden_volume_share": derived_volume_share,
        "numeric_invalid_by_field": dict(sorted(numeric_invalid.items())),
        "numeric_negative_by_field": dict(sorted(numeric_negative.items())),
    }


def build_result(quarter_results: list[dict[str, object]]) -> dict[str, object]:
    complete = {item["quarter"] for item in quarter_results} == set(QUARTERS)
    return {
        "phase": 200,
        "status": "SIX_QUARTER_DUPLICATE_AND_NEGATIVE_VALUE_DIAGNOSTICS_COMPLETED" if complete else "PARTIAL_DIAGNOSTIC",
        "audit_as_of_utc": datetime.now(timezone.utc).isoformat(),
        "quarters_audited": list(QUARTERS),
        "quarter_results": quarter_results,
        "interpretation": {
            "duplicate_fields_compared": True,
            "negative_hidden_values_distribution_captured": True,
            "negative_hiddenvol_values_distribution_captured": True,
            "negative_values_are_officially_documented_sentinels": False,
            "duplicate_rows_deduplicated": False,
            "daily_calendar_completeness_verified": False,
            "first_publication_time_verified_for_all": False,
            "strict_pit_admitted": False,
            "alpha_test_authorized": False,
            "holdout_used": False,
            "production_changed": False,
            "data_purchase": False,
            "vendor_contact": False,
            "f80_frozen": True,
        },
        "decision": (
            "This is a data-quality diagnostic only. Duplicate security-day keys are compared "
            "field-by-field and negative Hidden/HiddenVol values are counted with value "
            "histograms and denominator context. No deduplication or sentinel interpretation "
            "is applied automatically. PIT, security identity and alpha remain unadmitted."
        ),
    }


def run_audit() -> dict[str, object]:
    inventory = parse_inventory(fetch_sec_page())
    urls = inventory["quarter_urls"]
    missing = [q for q in QUARTERS if q not in urls]
    if missing:
        raise RuntimeError(f"quarters_missing_from_sec_inventory:{missing}")
    results = []
    for index, quarter in enumerate(QUARTERS):
        if index:
            time.sleep(1.0)
        archive_bytes, http_metadata = download_archive(urls[quarter])
        csv_bytes, archive_metadata = find_midas_member(archive_bytes)
        csv_result = audit_csv_bytes(csv_bytes, quarter)
        results.append({
            **csv_result,
            "archive_metadata": archive_metadata,
            "http_metadata": http_metadata,
        })
    return build_result(results)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="phase200_output")
    args = parser.parse_args()
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    result = run_audit()
    target = output / "phase200_sec_midas_duplicate_negative_diagnostics.json"
    target.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

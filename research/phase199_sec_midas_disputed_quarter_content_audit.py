#!/usr/bin/env python3
"""Phase 199: full-content audit of four disputed SEC MIDAS quarterly ZIPs.

Downloads only 2014 Q2 and 2016 Q2-Q4, validates ZIP CRC and the actual CSV
member/schema/row shape, and persists metadata only. Publication-time/PIT and
alpha are deliberately not inferred.
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
from datetime import date, datetime, timezone, timedelta
from itertools import chain
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from research.phase198_sec_midas_archive_inventory import (
    SEC_USER_AGENT,
    fetch_sec_page,
    parse_inventory,
)

QUARTERS = ("2014 Q2", "2016 Q2", "2016 Q3", "2016 Q4")
REQUIRED = {
    "date", "security", "ticker", "mcaprank", "turnrank", "volatilityrank",
    "pricerank", "litvol('000)", "ordervol('000)", "hidden", "tradesforhidden",
    "hiddenvol('000)", "tradevolforhidden('000)", "cancels", "littrades",
    "oddlots", "tradesforoddlots", "oddlotvol('000)", "tradevolforoddlots('000)",
}
NUMERIC = (
    "mcaprank", "turnrank", "volatilityrank", "pricerank", "litvol('000)",
    "ordervol('000)", "hidden", "tradesforhidden", "hiddenvol('000)",
    "tradevolforhidden('000)", "cancels", "littrades", "oddlots",
    "tradesforoddlots", "oddlotvol('000)", "tradevolforoddlots('000)",
)
MAX_ARCHIVE_BYTES = 250_000_000


def quarter_bounds(label: str) -> tuple[date, date]:
    match = re.fullmatch(r"(\d{4}) Q([1-4])", label)
    if not match:
        raise ValueError(f"invalid_quarter:{label}")
    year, quarter = int(match.group(1)), int(match.group(2))
    month = 1 + (quarter - 1) * 3
    start = date(year, month, 1)
    end_month = month + 2
    if end_month == 12:
        end = date(year, 12, 31)
    else:
        end = date(year, end_month + 1, 1) - timedelta(days=1)
    return start, end


def parse_date(value: str) -> date | None:
    value = (value or "").strip()
    if not value:
        return None
    if re.fullmatch(r"\d{8}\.0+", value):
        value = value.split(".", 1)[0]
    for fmt in ("%Y-%m-%d", "%Y%m%d", "%m/%d/%Y", "%m/%d/%y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            pass
    if re.fullmatch(r"\d{5}(?:\.0+)?", value):
        try:
            return date(1899, 12, 30) + timedelta(days=int(float(value)))
        except (ValueError, OverflowError):
            return None
    return None


def normalize_header(value: str) -> str:
    return re.sub(r"\s+", "", value.strip().lower())


def detect_delimiter(first_line: str) -> str:
    return "|" if first_line.count("|") > first_line.count(",") else ","


def audit_csv_member(binary_stream, member_name: str, quarter: str) -> dict[str, object]:
    start, end = quarter_bounds(quarter)
    text = io.TextIOWrapper(binary_stream, encoding="utf-8-sig", errors="replace", newline="")
    first_line = text.readline()
    if not first_line:
        raise ValueError(f"{member_name}:empty_csv_member")
    delimiter = detect_delimiter(first_line)
    reader = csv.reader(chain([first_line], text), delimiter=delimiter)
    header = next(reader)
    normalized = [normalize_header(item) for item in header]
    if len(normalized) != len(set(normalized)):
        raise ValueError(f"{member_name}:duplicate_normalized_header")
    missing = sorted(REQUIRED - set(normalized))
    if missing:
        return {
            "member": member_name,
            "delimiter": "pipe" if delimiter == "|" else "comma",
            "header": header,
            "header_sha256": hashlib.sha256("\x1f".join(header).encode()).hexdigest(),
            "missing_required_columns": missing,
            "schema_passed": False,
        }
    index = {name: i for i, name in enumerate(normalized)}
    rows = blank_rows = malformed_rows = invalid_date_rows = blank_ticker_rows = 0
    out_of_quarter_rows = 0
    dates: set[date] = set()
    tickers: set[str] = set()
    security_counts: Counter[str] = Counter()
    numeric_invalid: Counter[str] = Counter()
    numeric_negative: Counter[str] = Counter()
    key_signatures: dict[tuple[str, str, str], set[str]] = {}
    key_counts: Counter[tuple[str, str, str]] = Counter()

    for raw in reader:
        if not raw or not any(value.strip() for value in raw):
            blank_rows += 1
            continue
        if len(raw) != len(header):
            malformed_rows += 1
            continue
        ticker = raw[index["ticker"]].strip().upper()
        dt = parse_date(raw[index["date"]])
        security = raw[index["security"]].strip()
        if not ticker:
            blank_ticker_rows += 1
            continue
        if dt is None:
            invalid_date_rows += 1
            continue
        rows += 1
        dates.add(dt)
        tickers.add(ticker)
        if security:
            security_counts[security] += 1
        if dt < start or dt > end:
            out_of_quarter_rows += 1
        key = (ticker, dt.isoformat(), security)
        signature = hashlib.sha256("\x1f".join(raw).encode("utf-8", errors="replace")).hexdigest()
        key_counts[key] += 1
        key_signatures.setdefault(key, set()).add(signature)
        for field in NUMERIC:
            value = raw[index[field]].strip()
            if value in ("", ".", "NA", "N/A", "NULL"):
                continue
            try:
                number = float(value.replace(",", ""))
                if number < 0:
                    numeric_negative[field] += 1
            except ValueError:
                numeric_invalid[field] += 1

    duplicate_keys = [key for key, count in key_counts.items() if count > 1]
    conflicting_groups = sum(len(key_signatures[key]) > 1 for key in duplicate_keys)
    exact_groups = len(duplicate_keys) - conflicting_groups
    duplicate_rows = sum(key_counts[key] - 1 for key in duplicate_keys)
    return {
        "member": member_name,
        "delimiter": "pipe" if delimiter == "|" else "comma",
        "header": header,
        "header_sha256": hashlib.sha256("\x1f".join(header).encode()).hexdigest(),
        "missing_required_columns": [],
        "schema_passed": True,
        "rows_with_valid_ticker_and_date": rows,
        "blank_rows": blank_rows,
        "malformed_rows": malformed_rows,
        "invalid_date_rows": invalid_date_rows,
        "blank_ticker_rows": blank_ticker_rows,
        "out_of_quarter_rows": out_of_quarter_rows,
        "unique_dates": len(dates),
        "min_date": min(dates).isoformat() if dates else None,
        "max_date": max(dates).isoformat() if dates else None,
        "unique_tickers": len(tickers),
        "security_class_counts": dict(sorted(security_counts.items())),
        "duplicate_key_groups": len(duplicate_keys),
        "duplicate_rows_beyond_first": duplicate_rows,
        "exact_duplicate_key_groups": exact_groups,
        "conflicting_duplicate_key_groups": conflicting_groups,
        "numeric_invalid_by_field": dict(sorted(numeric_invalid.items())),
        "numeric_negative_by_field": dict(sorted(numeric_negative.items())),
    }


def audit_zip_bytes(
    content: bytes,
    quarter: str,
    metadata: dict[str, object] | None = None,
    nesting: int = 0,
) -> dict[str, object]:
    archive_sha = hashlib.sha256(content).hexdigest()
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        members = [item for item in archive.infolist() if not item.is_dir()]
        bad_member = archive.testzip()
        data_members = []
        for item in members:
            with archive.open(item, "r") as stream:
                prefix = stream.read(8192).decode("utf-8-sig", errors="replace")
            first_line = prefix.splitlines()[0] if prefix.splitlines() else ""
            delimiter = detect_delimiter(first_line)
            try:
                header = next(csv.reader([first_line], delimiter=delimiter))
            except (StopIteration, csv.Error):
                continue
            normalized = {normalize_header(value) for value in header}
            if REQUIRED.issubset(normalized):
                data_members.append(item)
        if not data_members:
            nested_members = [item for item in members if item.filename.lower().endswith(".zip")]
            if len(nested_members) == 1 and nesting < 3:
                with archive.open(nested_members[0], "r") as stream:
                    nested_bytes = stream.read()
                nested_result = audit_zip_bytes(nested_bytes, quarter, metadata, nesting + 1)
                nested_result["nested_archive_sha256"] = nested_result.get(
                    "data_archive_sha256", nested_result["archive_sha256"]
                )
                nested_result["nested_archive_bytes"] = nested_result.get(
                    "data_archive_bytes", nested_result["archive_bytes"]
                )
                nested_result["data_archive_sha256"] = nested_result.get(
                    "data_archive_sha256", nested_result["archive_sha256"]
                )
                nested_result["data_archive_bytes"] = nested_result.get(
                    "data_archive_bytes", nested_result["archive_bytes"]
                )
                nested_result["archive_sha256"] = archive_sha
                nested_result["archive_bytes"] = len(content)
                nested_result["zip_crc_passed"] = (
                    bad_member is None and nested_result["zip_crc_passed"]
                )
                nested_result["outer_crc_failure_member"] = bad_member
                nested_result["outer_member_count"] = len(members)
                nested_result["outer_members"] = [
                    {"name": item.filename, "compressed_bytes": item.compress_size,
                     "uncompressed_bytes": item.file_size, "crc32": f"{item.CRC:08x}"}
                    for item in members
                ]
                nested_result["container_depth"] = nesting + 1
                nested_result["http_metadata"] = metadata or {}
                nested_result["last_modified_is_not_publication_time"] = True
                return nested_result
            inventory = [{"name": item.filename, "bytes": item.file_size} for item in members]
            raise ValueError(
                f"{quarter}:no_midas_schema_member_and_no_single_nested_zip;members={inventory}"
            )
        if len(data_members) != 1:
            inventory = [{"name": item.filename, "bytes": item.file_size} for item in data_members]
            raise ValueError(f"{quarter}:multiple_midas_schema_members:{inventory}")
        with archive.open(data_members[0], "r") as stream:
            csv_result = audit_csv_member(stream, data_members[0].filename, quarter)
        return {
            "quarter": quarter,
            "archive_sha256": archive_sha,
            "data_archive_sha256": archive_sha,
            "archive_bytes": len(content),
            "data_archive_bytes": len(content),
            "zip_crc_passed": bad_member is None,
            "crc_failure_member": bad_member,
            "container_depth": nesting,
            "member_count": len(members),
            "members": [
                {"name": item.filename, "compressed_bytes": item.compress_size,
                 "uncompressed_bytes": item.file_size, "crc32": f"{item.CRC:08x}"}
                for item in members
            ],
            "data_member": data_members[0].filename,
            "csv": csv_result,
            "http_metadata": metadata or {},
            "last_modified_is_not_publication_time": True,
        }

def download_archive(url: str, retries: int = 3) -> tuple[bytes, dict[str, object]]:
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        request = Request(
            url,
            headers={
                "User-Agent": SEC_USER_AGENT,
                "Accept": "application/zip,application/octet-stream,*/*",
            },
        )
        try:
            with urlopen(request, timeout=180) as response:
                if response.status != 200:
                    raise RuntimeError(f"unexpected_http_status:{response.status}")
                chunks: list[bytes] = []
                total = 0
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > MAX_ARCHIVE_BYTES:
                        raise RuntimeError(f"archive_exceeds_limit:{total}")
                    chunks.append(chunk)
                data = b"".join(chunks)
                metadata = {
                    "http_status": response.status,
                    "final_url": response.geturl(),
                    "content_length_header": response.headers.get("Content-Length"),
                    "last_modified": response.headers.get("Last-Modified"),
                    "http_date": response.headers.get("Date"),
                    "etag": response.headers.get("ETag"),
                    "download_attempt": attempt,
                }
                return data, metadata
        except (HTTPError, URLError, TimeoutError, RuntimeError) as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(2 * attempt)
    raise RuntimeError(f"download_failed:{url}:{type(last_error).__name__}:{last_error}")


def build_result(quarter_audits: list[dict[str, object]]) -> dict[str, object]:
    by_quarter = {item["quarter"]: item for item in quarter_audits}
    complete = set(by_quarter) == set(QUARTERS)
    valid = complete and all(
        item["zip_crc_passed"]
        and item["csv"]["schema_passed"]
        and item["csv"].get("rows_with_valid_ticker_and_date", 0) > 0
        and item["csv"].get("invalid_date_rows", 0) == 0
        and item["csv"].get("blank_ticker_rows", 0) == 0
        and item["csv"].get("malformed_rows", 0) == 0
        and item["csv"].get("out_of_quarter_rows", 0) == 0
        for item in quarter_audits
    )
    return {
        "phase": 199,
        "status": "ALL_FOUR_DISPUTED_QUARTERS_FULL_CONTENT_VALIDATED" if valid else "PARTIAL_OR_FAILED_CONTENT_AUDIT",
        "audit_as_of_utc": datetime.now(timezone.utc).isoformat(),
        "source": "SEC Metrics by Individual Security quarterly public archive",
        "quarters_audited": list(QUARTERS),
        "quarter_audits": quarter_audits,
        "prior_phase103_content_validated_disputed_quarters": ["2016 Q1", "2019 Q4"],
        "interpretation": {
            "full_zip_downloaded_for_all_four": complete and all(x["archive_bytes"] > 0 for x in quarter_audits),
            "zip_crc_passed_for_all_four": valid,
            "csv_schema_passed_for_all_four": valid,
            "populated_daily_rows_verified": valid,
            "all_six_third_party_disputed_assets_content_validated_across_phases_103_199": valid,
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
            "Full ZIP/CSV content validation addresses only archive reachability, CRC, schema, "
            "populated rows and quarter date bounds. Phase 103 previously validated 2016 Q1 "
            "and 2019 Q4; if this phase passes, all six disputed SEC-hosted assets have actual "
            "content evidence. This does not prove daily-calendar completeness, first public "
            "release time, PIT availability, permanent security identity, off-exchange flow, "
            "participant identity or predictive value. No alpha test is authorized."
        ),
    }


def run_audit() -> dict[str, object]:
    inventory = parse_inventory(fetch_sec_page())
    urls = inventory["quarter_urls"]
    missing = [quarter for quarter in QUARTERS if quarter not in urls]
    if missing:
        raise RuntimeError(f"quarters_missing_from_sec_inventory:{missing}")
    results = []
    for index, quarter in enumerate(QUARTERS):
        if index:
            time.sleep(1.0)
        data, metadata = download_archive(urls[quarter])
        results.append(audit_zip_bytes(data, quarter, metadata))
    return build_result(results)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="phase199_output")
    args = parser.parse_args()
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    result = run_audit()
    target = output / "phase199_sec_midas_disputed_quarter_content_audit.json"
    target.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

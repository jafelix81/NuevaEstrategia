"""Phase 354: cross-validate Cboe Open-Close EOD OI against OCC daily OI.

Cboe's EOD `option_symbol` field is an option ROOT, not a full OSI symbol.
The audit reconstructs OSI from root/expiration/strike/call-put, quarantines
duplicate reconstructed keys, and validates the OCC response schema before
any comparison. Aggregate metadata only; no raw rows, returns, alpha or PIT
admission.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import re
import statistics
import sys
import zipfile
from collections import Counter, defaultdict
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

SAMPLE_URL = "https://datashop.cboe.com/download/sample/218"
OCC_OI_URL = "https://marketdata.theocc.com/daily-open-interest"
SAMPLE_DATE = "2025-03-28"
OCC_REPORT_DATES = ("2025-03-26", "2025-03-27", "2025-03-28")
USER_AGENT = (
    "Mozilla/5.0 (compatible; NuevaEstrategiaResearch/1.0; "
    "https://github.com/jafelix81/NuevaEstrategia)"
)
MAX_DOWNLOAD_BYTES = 100 * 1024 * 1024
TIMEOUT_SECONDS = 120
OUTPUT_DIR = Path("phase354_output")

SYMBOL_HEADERS = {
    "option_symbol", "osi_symbol", "contract_symbol", "symbol"
}
OI_HEADERS = {"open_interest", "openinterest", "oi", "open_int"}


def normalize_header(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value or "").strip().lower()).strip("_")


def normalize_option_symbol(value: str) -> str | None:
    text = re.sub(r"\s+", "", str(value or "").replace("\ufeff", "")).upper()
    return text or None


def parse_integer(value: str | int | float | Decimal | None) -> int | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        number = Decimal(str(value).replace(",", "").strip())
    except (InvalidOperation, ValueError):
        return None
    if not number.is_finite() or number != number.to_integral_value():
        return None
    return int(number)


def parse_date(value: str) -> str | None:
    raw = str(value or "").strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y%m%d"):
        try:
            return datetime.strptime(raw, fmt).date().isoformat()
        except ValueError:
            pass
    return None


def build_osi_symbol(root: str, expiration: str, strike: str, call_put: str) -> str | None:
    """Build the normalized 21-character OSI key from Cboe's EOD root fields."""
    normalized_root = re.sub(r"\s+", "", str(root or "")).upper()
    if not re.fullmatch(r"[A-Z0-9]{1,6}", normalized_root):
        return None
    normalized_expiration = parse_date(expiration)
    if normalized_expiration is None:
        return None
    side = str(call_put or "").strip().upper()
    if side not in {"C", "P"}:
        return None
    try:
        scaled_strike = Decimal(str(strike).replace(",", "").strip()) * Decimal(1000)
    except (InvalidOperation, ValueError):
        return None
    if (
        not scaled_strike.is_finite()
        or scaled_strike != scaled_strike.to_integral_value()
        or scaled_strike < 0
        or scaled_strike > 99_999_999
    ):
        return None
    expiry = datetime.strptime(normalized_expiration, "%Y-%m-%d")
    osi = (
        normalized_root.ljust(6)
        + expiry.strftime("%y%m%d")
        + side
        + f"{int(scaled_strike):08d}"
    )
    return normalize_option_symbol(osi)


def _decode_csv(payload: bytes, label: str) -> tuple[list[str], list[dict[str, str]]]:
    text = payload.decode("utf-8-sig")
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        raise ValueError(f"{label}: empty CSV")

    header_index = 0
    for index, line in enumerate(lines[:40]):
        normalized = {normalize_header(x) for x in next(csv.reader([line]))}
        if normalized & SYMBOL_HEADERS and normalized & OI_HEADERS:
            header_index = index
            break

    sample = "\n".join(lines[header_index:header_index + 12])
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",\t|;")
    except csv.Error:
        dialect = csv.excel
    reader = csv.DictReader(lines[header_index:], dialect=dialect)
    if not reader.fieldnames:
        raise ValueError(f"{label}: missing CSV header")
    rows = []
    for raw in reader:
        if not raw or not any(value not in (None, "") for value in raw.values()):
            continue
        rows.append({
            normalize_header(key): (value or "").strip()
            for key, value in raw.items() if key is not None
        })
    return [normalize_header(x) for x in reader.fieldnames], rows


def extract_csv_members(payload: bytes) -> list[tuple[str, bytes]]:
    found: list[tuple[str, bytes]] = []

    def scan(data: bytes, name: str, depth: int) -> None:
        if depth > 5:
            raise ValueError("nested archive depth exceeded")
        if data.startswith(b"PK\x03\x04"):
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                bad = archive.testzip()
                if bad:
                    raise ValueError(f"{name}: ZIP CRC failure: {bad}")
                for member in archive.infolist():
                    if member.is_dir():
                        continue
                    scan(archive.read(member), f"{name}!{member.filename}", depth + 1)
            return
        if data.startswith(b"\x1f\x8b"):
            scan(gzip.decompress(data), name + ".gz", depth + 1)
            return
        lower = name.lower()
        if lower.endswith(".csv") or lower.endswith(".txt"):
            found.append((name, data))
            return
        try:
            _decode_csv(data, name)
        except (UnicodeDecodeError, ValueError, csv.Error):
            return
        found.append((name, data))

    scan(payload, "sample", 0)
    return found


def download(url: str) -> dict:
    request = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/csv,text/plain,application/zip,application/octet-stream,*/*",
            "Accept-Encoding": "gzip, deflate",
        },
    )
    with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        payload = response.read(MAX_DOWNLOAD_BYTES + 1)
        if len(payload) > MAX_DOWNLOAD_BYTES:
            raise ValueError("download exceeds configured byte limit")
        encoding = response.headers.get("Content-Encoding", "")
        if encoding.lower() == "gzip" or payload.startswith(b"\x1f\x8b"):
            payload = gzip.decompress(payload)
        return {
            "payload": payload,
            "http_status": response.status,
            "content_type": response.headers.get("Content-Type", ""),
            "etag": response.headers.get("ETag"),
            "last_modified": response.headers.get("Last-Modified"),
            "final_url": response.geturl(),
            "sha256": hashlib.sha256(payload).hexdigest(),
            "bytes": len(payload),
        }


def occ_report_url(report_date: str, parameter: str = "reportDate", encode_slash: bool = True) -> str:
    parsed = datetime.strptime(report_date, "%Y-%m-%d")
    date_text = parsed.strftime("%m/%d/%Y")
    if encode_slash:
        query = urlencode({parameter: date_text, "action": "download", "format": "csv"})
    else:
        query = f"{parameter}={date_text}&action=download&format=csv"
    return OCC_OI_URL + "?" + query


def _first_value(row: dict[str, str], candidates: tuple[str, ...]) -> str:
    for candidate in candidates:
        key = normalize_header(candidate)
        if key in row and row[key] != "":
            return row[key]
    return ""


def parse_occ_report(payload: bytes, report_date: str) -> dict:
    headers, rows = _decode_csv(payload, f"OCC {report_date}")
    symbol_candidates = (
        "option symbol", "option_symbol", "osi symbol", "contract symbol", "symbol"
    )
    oi_candidates = ("open interest", "open_interest", "open int", "oi")
    if not set(headers) & SYMBOL_HEADERS:
        preview = payload[:260].decode("utf-8-sig", "replace").replace("\n", " ")
        raise ValueError(f"OCC schema missing OSI/option-symbol column; preview={preview!r}")
    if not set(headers) & OI_HEADERS:
        preview = payload[:260].decode("utf-8-sig", "replace").replace("\n", " ")
        raise ValueError(f"OCC schema missing open-interest column; preview={preview!r}")

    indexed: dict[str, list[int]] = defaultdict(list)
    missing_symbol = 0
    invalid_oi = 0
    for row in rows:
        symbol = normalize_option_symbol(_first_value(row, symbol_candidates))
        oi = parse_integer(_first_value(row, oi_candidates))
        if symbol is None:
            missing_symbol += 1
            continue
        if oi is None:
            invalid_oi += 1
            continue
        indexed[symbol].append(oi)
    if not indexed:
        preview = payload[:260].decode("utf-8-sig", "replace").replace("\n", " ")
        raise ValueError(f"OCC response has no parseable OSI/OI rows; preview={preview!r}")
    duplicate_symbols = sum(1 for values in indexed.values() if len(values) > 1)
    return {
        "report_date": report_date,
        "row_count": len(rows),
        "header": headers,
        "unique_symbol_count": len(indexed),
        "duplicate_symbol_count": duplicate_symbols,
        "missing_symbol_rows": missing_symbol,
        "invalid_oi_rows": invalid_oi,
        "index": dict(indexed),
    }


def parse_cboe_eod_sample(payload: bytes) -> dict:
    members = extract_csv_members(payload)
    selected = []
    required = {
        "quote_date", "underlying_symbol", "option_symbol", "expiration_date",
        "strike_price", "call_put_flag", "series_type", "open_interest",
        "previous_open_interest",
    }
    for name, raw in members:
        try:
            headers, rows = _decode_csv(raw, name)
        except (UnicodeDecodeError, ValueError, csv.Error):
            continue
        if required.issubset(set(headers)):
            selected.append((name, rows))
    if not selected:
        raise ValueError("no Open-Close EOD CSV member with required OI/series fields")
    if len(selected) != 1:
        raise ValueError(f"expected one EOD member, found {len(selected)}")

    name, rows = selected[0]
    quote_dates = sorted({
        parse_date(row.get("quote_date", "")) for row in rows
        if parse_date(row.get("quote_date", ""))
    })
    underlyings = sorted({
        row.get("underlying_symbol", "").strip().upper()
        for row in rows if row.get("underlying_symbol", "").strip()
    })
    if quote_dates != [SAMPLE_DATE]:
        raise ValueError(f"unexpected sample quote dates: {quote_dates}")
    if not rows:
        raise ValueError("empty EOD sample")

    normalized_rows = []
    series_types = Counter()
    invalid_osi_rows = 0
    for row in rows:
        series_type = row.get("series_type", "").strip().upper()
        if series_type:
            series_types[series_type] += 1
        osi_symbol = build_osi_symbol(
            row.get("option_symbol", ""),
            row.get("expiration_date", ""),
            row.get("strike_price", ""),
            row.get("call_put_flag", ""),
        )
        if osi_symbol is None or series_type not in {"S", "N", "F"}:
            invalid_osi_rows += 1
        normalized_rows.append({
            "osi_symbol": osi_symbol if series_type in {"S", "N", "F"} else None,
            "series_type": series_type,
            "open_interest": parse_integer(row.get("open_interest")),
            "previous_open_interest": parse_integer(row.get("previous_open_interest")),
        })
    symbol_counts = Counter(
        row["osi_symbol"] for row in normalized_rows if row["osi_symbol"]
    )
    duplicate_osi_rows = sum(
        count for count in symbol_counts.values() if count > 1
    )
    return {
        "member": name,
        "quote_dates": quote_dates,
        "row_count": len(rows),
        "underlying_count": len(underlyings),
        "series_type_counts": dict(sorted(series_types.items())),
        "invalid_osi_rows": invalid_osi_rows,
        "duplicate_osi_rows": duplicate_osi_rows,
        "sample_sha256": hashlib.sha256(payload).hexdigest(),
        "rows": normalized_rows,
    }


def compare_field(sample_rows: list[dict], field: str, occ_index: dict[str, list[int]]) -> dict:
    symbol_counts = Counter(
        row.get("osi_symbol") for row in sample_rows if row.get("osi_symbol")
    )
    valid = matched = exact = missing = ambiguous_occ = ambiguous_cboe = invalid = 0
    absolute_differences = []
    for row in sample_rows:
        symbol = row.get("osi_symbol")
        value = row.get(field)
        if not symbol or value is None:
            invalid += 1
            continue
        valid += 1
        if symbol_counts[symbol] > 1:
            ambiguous_cboe += 1
            continue
        candidates = occ_index.get(symbol, [])
        if not candidates:
            missing += 1
            continue
        if len(candidates) != 1:
            ambiguous_occ += 1
            continue
        matched += 1
        difference = abs(value - candidates[0])
        absolute_differences.append(difference)
        if difference == 0:
            exact += 1
    return {
        "field": field,
        "valid_cboe_rows": valid,
        "matched_unique_occ_rows": matched,
        "missing_occ_rows": missing,
        "ambiguous_occ_rows": ambiguous_occ,
        "ambiguous_cboe_rows": ambiguous_cboe,
        "invalid_cboe_rows": invalid,
        "exact_matches": exact,
        "mismatches": matched - exact,
        "coverage_rate": matched / valid if valid else None,
        "exact_match_rate": exact / matched if matched else None,
        "median_absolute_difference": statistics.median(absolute_differences) if absolute_differences else None,
        "max_absolute_difference": max(absolute_differences) if absolute_differences else None,
    }


def choose_alignment(comparisons: list[dict], field: str) -> dict:
    candidates = [item for item in comparisons if item["field"] == field and item["matched_unique_occ_rows"] > 0]
    candidates.sort(
        key=lambda item: (
            item["exact_match_rate"] if item["exact_match_rate"] is not None else -1,
            item["coverage_rate"] if item["coverage_rate"] is not None else -1,
            item["matched_unique_occ_rows"],
        ),
        reverse=True,
    )
    if not candidates:
        return {"status": "NO_MATCHABLE_OCC_ROWS", "best_report_date": None}
    best = candidates[0]
    second_rate = candidates[1]["exact_match_rate"] if len(candidates) > 1 else -1
    strong = (
        best["matched_unique_occ_rows"] >= 1000
        and best["coverage_rate"] is not None and best["coverage_rate"] >= 0.80
        and best["exact_match_rate"] is not None and best["exact_match_rate"] >= 0.98
        and best["exact_match_rate"] - second_rate >= 0.01
    )
    return {
        "status": "UNIQUE_STRONG_MATCH" if strong else "UNRESOLVED_OR_AMBIGUOUS",
        "best_report_date": best["report_date"],
        "best_exact_match_rate": best["exact_match_rate"],
        "best_coverage_rate": best["coverage_rate"],
        "best_matched_rows": best["matched_unique_occ_rows"],
        "runner_up_exact_match_rate": second_rate if second_rate >= 0 else None,
    }


def _response_preview(payload: bytes) -> str:
    return payload[:260].decode("utf-8-sig", "replace").replace("\n", " ").replace("\r", " ")


def _resolve_occ_parameter() -> tuple[str | None, bool | None, dict | None, dict | None, list[dict]]:
    attempts = []
    candidates = (
        ("reportDate", True),
        ("dailyDate", True),
        ("reportDate", False),
        ("dailyDate", False),
    )
    for parameter, encode_slash in candidates:
        url = occ_report_url(SAMPLE_DATE, parameter, encode_slash)
        try:
            item = download(url)
            try:
                parsed = parse_occ_report(item["payload"], SAMPLE_DATE)
            except ValueError as error:
                attempts.append({
                    "parameter": parameter,
                    "slash_encoded": encode_slash,
                    "http_status": item["http_status"],
                    "content_type": item["content_type"],
                    "bytes": item["bytes"],
                    "sha256": item["sha256"],
                    "preview": _response_preview(item["payload"]),
                    "error": str(error),
                })
                continue
            return parameter, encode_slash, item, parsed, attempts
        except (HTTPError, URLError, TimeoutError, OSError, ValueError) as error:
            attempts.append({
                "parameter": parameter,
                "slash_encoded": encode_slash,
                "error": f"{type(error).__name__}: {error}",
            })
    return None, None, None, None, attempts


def run_audit() -> dict:
    sample_download = download(SAMPLE_URL)
    sample = parse_cboe_eod_sample(sample_download["payload"])

    parameter, encode_slash, first_item, first_parsed, attempts = _resolve_occ_parameter()
    if first_item is None or first_parsed is None:
        return {
            "phase": 354,
            "status": "OCC_ENDPOINT_SCHEMA_UNRESOLVED",
            "sample": {
                "url": SAMPLE_URL,
                "http_status": sample_download["http_status"],
                "content_type": sample_download["content_type"],
                "sha256": sample_download["sha256"],
                "bytes": sample_download["bytes"],
                "member": sample["member"],
                "quote_dates": sample["quote_dates"],
                "rows": sample["row_count"],
                "underlyings": sample["underlying_count"],
                "series_type_counts": sample["series_type_counts"],
                "invalid_osi_rows": sample["invalid_osi_rows"],
                "duplicate_osi_rows": sample["duplicate_osi_rows"],
            },
            "occ_parameter_attempts": attempts,
            "interpretation": (
                "The OCC endpoint returned no parseable OSI/open-interest report. "
                "No Cboe-to-OCC comparison is valid until the request parameter and "
                "response schema are resolved."
            ),
            "gates": {
                "historical_pit_admitted": False,
                "prospective_pit_admitted": False,
                "licensing_confirmed": False,
                "return_test_authorized": False,
                "alpha_admission": False,
                "holdout_used": False,
                "f80_frozen": True,
            },
        }

    occ_downloads = {SAMPLE_DATE: first_item}
    occ_parsed = {SAMPLE_DATE: first_parsed}
    errors = []
    for report_date in OCC_REPORT_DATES:
        if report_date == SAMPLE_DATE:
            continue
        try:
            item = download(occ_report_url(report_date, parameter, encode_slash))
            parsed = parse_occ_report(item["payload"], report_date)
            occ_downloads[report_date] = item
            occ_parsed[report_date] = parsed
        except (HTTPError, URLError, TimeoutError, OSError, ValueError, zipfile.BadZipFile) as error:
            errors.append({"report_date": report_date, "error": f"{type(error).__name__}: {error}"})

    comparisons = []
    for report_date, parsed in sorted(occ_parsed.items()):
        for field in ("open_interest", "previous_open_interest"):
            result = compare_field(sample["rows"], field, parsed["index"])
            result["report_date"] = report_date
            comparisons.append(result)

    alignments = {
        field: choose_alignment(comparisons, field)
        for field in ("open_interest", "previous_open_interest")
    }
    complete_downloads = len(occ_parsed) == len(OCC_REPORT_DATES)
    result = {
        "phase": 354,
        "status": "COMPLETED_CROSS_SOURCE_OI_DIAGNOSTIC" if complete_downloads else "PARTIAL_CROSS_SOURCE_OI_DIAGNOSTIC",
        "sample": {
            "url": SAMPLE_URL,
            "http_status": sample_download["http_status"],
            "content_type": sample_download["content_type"],
            "sha256": sample_download["sha256"],
            "bytes": sample_download["bytes"],
            "member": sample["member"],
            "quote_dates": sample["quote_dates"],
            "rows": sample["row_count"],
            "underlyings": sample["underlying_count"],
            "series_type_counts": sample["series_type_counts"],
            "invalid_osi_rows": sample["invalid_osi_rows"],
            "duplicate_osi_rows": sample["duplicate_osi_rows"],
        },
        "occ_request": {"parameter": parameter, "slash_encoded": encode_slash},
        "occ_parameter_attempts": attempts,
        "occ_reports": {
            report_date: {
                "http_status": item["http_status"],
                "content_type": item["content_type"],
                "etag": item["etag"],
                "last_modified": item["last_modified"],
                "final_url": item["final_url"],
                "sha256": item["sha256"],
                "bytes": item["bytes"],
                "rows": occ_parsed[report_date]["row_count"],
                "unique_symbols": occ_parsed[report_date]["unique_symbol_count"],
                "duplicate_symbols": occ_parsed[report_date]["duplicate_symbol_count"],
                "missing_symbol_rows": occ_parsed[report_date]["missing_symbol_rows"],
                "invalid_oi_rows": occ_parsed[report_date]["invalid_oi_rows"],
            }
            for report_date, item in sorted(occ_downloads.items())
        },
        "retrieval_errors": errors,
        "comparisons": comparisons,
        "alignment_by_field": alignments,
        "interpretation": (
            "Cboe option_symbol is a root, so the join key is reconstructed OSI from "
            "root/expiration/strike/call-put. Duplicate reconstructed Cboe keys and "
            "duplicate OCC keys are quarantined. This diagnostic can validate OI source/date "
            "conventions for one sample only; it does not establish PIT, all-market coverage, "
            "deliverable equivalence, predictive value or alpha."
        ),
        "gates": {
            "historical_pit_admitted": False,
            "prospective_pit_admitted": False,
            "licensing_confirmed": False,
            "return_test_authorized": False,
            "alpha_admission": False,
            "holdout_used": False,
            "f80_frozen": True,
        },
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=str(OUTPUT_DIR / "audit.json"))
    args = parser.parse_args()
    try:
        result = run_audit()
    except (HTTPError, URLError, TimeoutError, OSError, ValueError, zipfile.BadZipFile) as error:
        result = {
            "phase": 354,
            "status": "AUDIT_EXECUTION_ERROR",
            "error": f"{type(error).__name__}: {error}",
            "gates": {
                "historical_pit_admitted": False,
                "prospective_pit_admitted": False,
                "licensing_confirmed": False,
                "return_test_authorized": False,
                "alpha_admission": False,
                "holdout_used": False,
                "f80_frozen": True,
            },
        }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

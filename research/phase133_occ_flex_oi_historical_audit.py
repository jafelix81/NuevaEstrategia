#!/usr/bin/env python3
"""Phase 133: OCC Flex Reports historical equity-option OI feasibility audit.

Uses only the public documented batch endpoint. It does not infer trade direction
or public knowledge time and performs no forward-return/alpha test.
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import re
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE_URL = "https://marketdata.theocc.com/flex-reports"
SAMPLE_DATES = (
    "2018-01-03",
    "2020-01-03",
    "2022-01-03",
    "2024-01-03",
    "2025-01-03",
    "2026-01-05",
    "2026-11-04",
)
OUT_DIR = Path("phase133_occ_flex_oi_historical_audit")
USER_AGENT = "Mozilla/5.0 (compatible; NuevaEstrategiaResearch/1.0)"


def flex_url(day: str) -> str:
    ymd = datetime.strptime(day, "%Y-%m-%d").strftime("%Y%m%d")
    return BASE_URL + "?" + urlencode({
        "reportType": "OI",
        "optionType": "E",
        "reportDate": ymd,
    })


def norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value or "").lower())


def parse_number(value):
    if value in (None, ""):
        return None
    text = str(value).strip().replace(",", "").replace("$", "")
    if text in {"-", "NA", "N/A", "NULL", "null"}:
        return None
    try:
        number = float(text)
        if number != number:
            return None
        return number
    except (TypeError, ValueError):
        return None


def parse_osi_root(value):
    text = str(value or "").strip().upper()
    match = re.match(r"^(.{1,6})\s*\d{6}[CP]\d{8}$", text)
    return match.group(1).strip() if match else None


def parse_csv_bytes(raw: bytes):
    text = raw.decode("utf-8-sig", errors="replace")
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        return {"header": [], "rows": [], "delimiter": None, "text_status": "EMPTY"}
    if lines[0].lstrip().startswith("<") or "<html" in text[:500].lower():
        return {"header": [], "rows": [], "delimiter": None, "text_status": "HTML_OR_XML"}
    header_index = 0
    for i, line in enumerate(lines[:40]):
        low = norm(line)
        if any(token in low for token in ("openinterest", "option", "contract", "underlying", "expiration")):
            if any(delimiter in line for delimiter in (",", "\t", "|", ";")):
                header_index = i
                break
    sample = "\n".join(lines[header_index:header_index + 15])
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",\t|;")
    except csv.Error:
        dialect = csv.excel
    reader = csv.DictReader(lines[header_index:], dialect=dialect)
    rows = [row for row in reader if row and any(v not in (None, "") for v in row.values())]
    return {
        "header": reader.fieldnames or [],
        "rows": rows,
        "delimiter": dialect.delimiter,
        "text_status": "TABULAR",
    }


def parse_flex_payload(raw: bytes):
    members = []
    payloads = []
    if raw.startswith(b"PK\x03\x04"):
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            names = [name for name in archive.namelist() if not name.endswith("/")]
            members = names
            for name in names:
                lower = name.lower()
                if lower.endswith((".csv", ".txt", ".dat")):
                    payloads.append((name, archive.read(name)))
        if not payloads:
            return {"format": "ZIP_NO_TABULAR_MEMBER", "members": members, "header": [], "rows": []}
        parsed = [(name, parse_csv_bytes(data)) for name, data in payloads]
        name, table = max(parsed, key=lambda item: len(item[1]["rows"]))
        return {"format": "ZIP", "members": members, "member": name, **table}
    if raw[:2] == b"\x1f\x8b":
        decoded = gzip.decompress(raw)
        return {"format": "GZIP", "members": [], "member": None, **parse_csv_bytes(decoded)}
    if raw.startswith(b"%PDF"):
        return {"format": "PDF", "members": [], "header": [], "rows": [], "text_status": "PDF"}
    return {"format": "TEXT_OR_CSV", "members": [], "member": None, **parse_csv_bytes(raw)}


def find_col(headers, candidates):
    mapping = {norm(header): header for header in headers}
    for candidate in candidates:
        key = norm(candidate)
        if key in mapping:
            return mapping[key]
    return None


def inspect_table(parsed):
    headers = parsed.get("header") or []
    rows = parsed.get("rows") or []
    underlying_col = find_col(headers, (
        "Underlying", "Underlying Symbol", "UnderlyingSymbol", "Underlying Root", "Root",
    ))
    contract_col = find_col(headers, (
        "Option Symbol", "OptionSymbol", "OSI", "OSI Symbol", "Contract Symbol",
        "Series Symbol", "Symbol",
    ))
    oi_col = find_col(headers, (
        "Open Interest", "OpenInterest", "OI", "Open Int", "OpenInterestQuantity",
    ))
    expiry_col = find_col(headers, ("Expiration", "Expiration Date", "Expiry", "Maturity"))
    strike_col = find_col(headers, ("Strike", "Strike Price"))
    put_call_col = find_col(headers, ("Put/Call", "Put Call", "Call Put", "Option Type", "Type"))
    valid_oi = []
    contract_keys = []
    roots = set()
    for row in rows:
        oi = parse_number(row.get(oi_col)) if oi_col else None
        if oi is not None:
            valid_oi.append(oi)
        contract = str(row.get(contract_col) or "").strip().upper() if contract_col else ""
        underlying = str(row.get(underlying_col) or "").strip().upper() if underlying_col else ""
        if not underlying and contract:
            underlying = parse_osi_root(contract) or ""
        if underlying:
            roots.add(underlying)
        if contract:
            contract_keys.append(contract)
        elif expiry_col and strike_col and put_call_col and underlying:
            contract_keys.append("|".join((
                underlying,
                str(row.get(expiry_col) or "").strip(),
                str(row.get(put_call_col) or "").strip().upper(),
                str(row.get(strike_col) or "").strip(),
            )))
    unique_keys = set(contract_keys)
    return {
        "row_count": len(rows),
        "open_interest_nonnull_rows": len(valid_oi),
        "open_interest_nonnull_rate": len(valid_oi) / len(rows) if rows else 0.0,
        "total_open_interest": sum(valid_oi) if valid_oi else None,
        "underlying_column": underlying_col,
        "contract_column": contract_col,
        "open_interest_column": oi_col,
        "expiration_column": expiry_col,
        "strike_column": strike_col,
        "put_call_column": put_call_col,
        "unique_underlying_roots": len(roots),
        "unique_contract_keys": len(unique_keys),
        "duplicate_contract_rows": len(contract_keys) - len(unique_keys),
        "contract_level_schema": bool(oi_col and contract_keys and len(unique_keys) > 0),
        "header": headers,
    }


def fetch_one(day: str):
    url = flex_url(day)
    request = Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept": "text/csv,text/plain,application/zip,application/octet-stream,*/*",
        "Accept-Encoding": "gzip, deflate",
    })
    last_error = None
    for attempt in range(4):
        try:
            with urlopen(request, timeout=60) as response:
                raw = response.read()
                headers = {k.lower(): v for k, v in response.headers.items()}
                parsed = parse_flex_payload(raw)
                metrics = inspect_table(parsed)
                return {
                    "report_date": day,
                    "url": url,
                    "http_status": response.status,
                    "content_type": headers.get("content-type"),
                    "last_modified": headers.get("last-modified"),
                    "etag": headers.get("etag"),
                    "http_date": headers.get("date"),
                    "response_bytes": len(raw),
                    "response_sha256": hashlib.sha256(raw).hexdigest(),
                    "container_format": parsed.get("format"),
                    "inner_members": parsed.get("members"),
                    "selected_member": parsed.get("member"),
                    "parse_status": parsed.get("text_status", "UNKNOWN"),
                    **metrics,
                    "error": None,
                }
        except HTTPError as exc:
            last_error = "HTTP{} {}".format(exc.code, exc.reason)
            if exc.code not in (408, 429, 500, 502, 503, 504):
                break
        except (URLError, TimeoutError, OSError, ValueError, zipfile.BadZipFile) as exc:
            last_error = "{}: {}".format(type(exc).__name__, exc)
        if attempt < 3:
            time.sleep(min(8, 2 ** attempt))
    return {
        "report_date": day,
        "url": url,
        "parse_status": "REQUEST_FAILED",
        "contract_level_schema": False,
        "row_count": 0,
        "open_interest_nonnull_rows": 0,
        "open_interest_nonnull_rate": 0.0,
        "unique_underlying_roots": 0,
        "unique_contract_keys": 0,
        "error": last_error,
    }


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    for i, day in enumerate(SAMPLE_DATES, 1):
        result = fetch_one(day)
        rows.append(result)
        print(json.dumps({
            "stage": "DATE_COMPLETE",
            "date": day,
            "parse_status": result.get("parse_status"),
            "rows": result.get("row_count", 0),
            "contract_level_schema": result.get("contract_level_schema", False),
        }), flush=True)
        if i < len(SAMPLE_DATES):
            time.sleep(0.5)

    valid = [r for r in rows if r.get("contract_level_schema") and r.get("open_interest_nonnull_rows", 0) > 0]
    earliest = min((r["report_date"] for r in valid), default=None)
    latest = max((r["report_date"] for r in valid), default=None)
    span_years = 0.0
    if earliest and latest:
        span_years = (
            datetime.strptime(latest, "%Y-%m-%d") - datetime.strptime(earliest, "%Y-%m-%d")
        ).days / 365.25
    min_nonnull_rate = min((r["open_interest_nonnull_rate"] for r in valid), default=0.0)
    gates = {
        "at_least_5_of_7_contract_level_dates": len(valid) >= 5,
        "successful_dates_span_at_least_5_years": span_years >= 5.0,
        "at_least_95pct_nonnull_oi_rows_on_each_successful_date": min_nonnull_rate >= 0.95,
        "contract_identifier_present": all(r.get("unique_contract_keys", 0) > 0 for r in valid) if valid else False,
    }
    summary = {
        "phase": "133_OCC_FLEX_EQUITY_OI_HISTORICAL_FEASIBILITY",
        "status": "PASS_CONDITIONAL_SOURCE_CANDIDATE" if all(gates.values()) else "FAIL_OR_PARTIAL_HISTORICAL_FEASIBILITY",
        "sample_dates": list(SAMPLE_DATES),
        "successful_contract_level_dates": len(valid),
        "earliest_successful_date": earliest,
        "latest_successful_date": latest,
        "successful_history_span_years": span_years,
        "minimum_nonnull_oi_rate": min_nonnull_rate,
        "date_results": rows,
        "gate_checks": gates,
        "pit_publication_timestamp": "NOT_VERIFIED",
        "pit_limitation": "Report date and HTTP Last-Modified/ETag/Date are not proof of first public dissemination. Do not use reportDate as KnowledgeDate.",
        "universe_limitation": "No fixed 335-name list is used. Unique underlying/root breadth is measured from the returned full-market file; issuer/security coverage versus the broad historical universe remains unverified pending an effective-dated security master including inactive/delisted securities.",
        "economic_interpretation": "Open interest is outstanding contract inventory, not buy/sell aggressor direction, opening/closing intent, beneficial-owner identity or proof of informed trading.",
        "volatility_limitation": "The endpoint does not establish historical IV/skew/Greeks coverage; those require a separate quote/volatility source.",
        "forward_returns_used": False,
        "vendor_purchase_or_contact": False,
        "f80_baseline_frozen": True,
        "audit_timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }
    with (OUT_DIR / "date_audit.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = sorted({key for row in rows for key in row})
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    (OUT_DIR / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()

"""Phase 353: audit the Cboe daily participant-flow + OPRA option-context pair.

Downloads public sample files and official specifications only. Raw data is never
written to the artifact; only hashes and aggregate diagnostics are emitted.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import re
import time
import zipfile
from collections import Counter
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

OPEN_CLOSE_PAGE = "https://datashop.cboe.com/cboe-options-open-close-volume-summary"
OPTION_EOD_PAGE = "https://datashop.cboe.com/option-eod-summary"
OPEN_CLOSE_SPEC = "https://datashop.cboe.com/documents/Open_Close_EOD_Spec_v1.3.pdf"
OPTION_EOD_SPEC = "https://datashop.cboe.com/documents/Option_EOD_Summary_Layout.pdf"
OPEN_CLOSE_SAMPLE = "https://datashop.cboe.com/download/sample/218"
OPTION_EOD_SAMPLE = "https://datashop.cboe.com/download/sample/217"
INTRADAY_SAMPLE = "https://datashop.cboe.com/documents/Cboe_OpenClose_2026-09-30_15_20_1.csv.gz"
USER_AGENT = "Mozilla/5.0 (compatible; NuevaEstrategiaResearch/1.0)"
OPEN_CLOSE_BASE = [
    "quote_date", "underlying_symbol", "security_type", "option_symbol",
    "expiration_date", "strike_price", "call_put_flag", "days_to_expire",
    "series_type", "first_trade_price", "high_trade_price", "low_trade_price",
    "last_trade_price", "total_exchange_vol", "total_industry_vol",
    "open_interest", "previous_open_interest", "previous_close",
]
CAPACITY_GROUPS = {
    "firm": ["open_buy", "close_buy", "open_sell", "close_sell"],
    "bd": ["open_buy", "close_buy", "open_sell", "close_sell"],
    "mm": ["buy", "sell"],
}
BUCKETS = ["lt_100", "100_199", "gt_199"]
OPEN_CLOSE_VOLUME_FIELDS = []
for prefix, actions in CAPACITY_GROUPS.items():
    for action in actions:
        OPEN_CLOSE_VOLUME_FIELDS.append(f"{prefix}_{action}_vol")
for prefix in ("cust", "procust"):
    for bucket in BUCKETS:
        for action in ("open_buy", "close_buy", "open_sell", "close_sell"):
            OPEN_CLOSE_VOLUME_FIELDS.append(f"{prefix}_{bucket}_{action}_vol")
OPEN_CLOSE_REQUIRED = OPEN_CLOSE_BASE + [
    field.replace("_vol", "_qty") for field in OPEN_CLOSE_VOLUME_FIELDS
] + OPEN_CLOSE_VOLUME_FIELDS
OPTION_EOD_REQUIRED = [
    "underlying_symbol", "quote_date", "root", "expiration", "strike",
    "option_type", "open", "high", "low", "close", "trade_volume",
    "bid_size_1545", "bid_1545", "ask_size_1545", "ask_1545",
    "bid_size_eod", "bid_eod", "ask_size_eod", "ask_eod", "vwap",
    "open_interest",
]
OPTION_EOD_CALCS = [
    "active_underlying_price_1545", "implied_volatility_1545", "delta_1545",
    "gamma_1545", "theta_1545", "vega_1545", "rho_1545",
]
OPTION_EOD_SERIES_KEY = (
    "underlying_symbol", "root", "expiration", "strike", "option_type"
)
OPEN_CLOSE_SERIES_KEY = (
    "underlying_symbol", "option_symbol", "expiration_date", "strike_price",
    "call_put_flag", "series_type",
)


class _Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        if data and data.strip():
            self.parts.append(data.strip())


def _norm(value: str) -> str:
    value = (value or "").replace("\ufeff", "").strip().lower()
    return re.sub(r"\s+", "_", value)


def _download(url: str, *, accept: str = "*/*", retries: int = 3) -> dict:
    last_error = None
    for attempt in range(retries):
        request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": accept})
        try:
            with urlopen(request, timeout=90) as response:
                payload = response.read()
                return {
                    "payload": payload,
                    "http_status": response.status,
                    "content_type": response.headers.get("Content-Type", ""),
                    "final_url": response.geturl(),
                    "etag": response.headers.get("ETag"),
                    "last_modified": response.headers.get("Last-Modified"),
                }
        except HTTPError as error:
            last_error = f"HTTP {error.code}"
            if error.code not in (408, 429, 500, 502, 503, 504):
                raise
        except (URLError, TimeoutError, OSError) as error:
            last_error = f"{type(error).__name__}: {error}"
        if attempt + 1 < retries:
            time.sleep(2 ** attempt)
    raise RuntimeError(f"download failed after {retries} attempts: {last_error}")


def _decode_csv(payload: bytes, name: str) -> tuple[str, list[str]]:
    text = payload.decode("utf-8-sig")
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        raise ValueError(f"{name}: empty CSV")
    header = [_norm(x) for x in next(csv.reader([lines[0]]))]
    if len(header) < 5 or len(header) != len(set(header)):
        raise ValueError(f"{name}: invalid/duplicate CSV header ({len(header)} columns)")
    return text, header


def _extract_csv_members(payload: bytes) -> list[tuple[str, bytes]]:
    found: list[tuple[str, bytes]] = []

    def scan(data: bytes, label: str, depth: int):
        if depth > 4:
            raise ValueError("nested archive depth exceeds safety limit")
        if data.startswith(b"PK\x03\x04"):
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                bad = archive.testzip()
                if bad:
                    raise ValueError(f"{label}: ZIP CRC failure in {bad}")
                for member in archive.namelist():
                    if member.endswith("/"):
                        continue
                    scan(archive.read(member), f"{label}!{member}", depth + 1)
            return
        if data.startswith(b"\x1f\x8b"):
            scan(gzip.decompress(data), label + ".gz", depth + 1)
            return
        try:
            text, header = _decode_csv(data, label)
        except (UnicodeDecodeError, ValueError, csv.Error):
            return
        if len(header) >= 5:
            found.append((label, text.encode("utf-8")))

    scan(payload, "root", 0)
    return found


def _parse_date(value: str):
    value = (value or "").strip()
    if not value:
        return None
    for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            continue
    return "UNPARSED"


def _audit_csv(text_bytes: bytes, *, name: str, product: str) -> dict:
    text = text_bytes.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text, newline=""))
    if not reader.fieldnames:
        raise ValueError(f"{name}: no header")
    headers = [_norm(x) for x in reader.fieldnames]
    if len(headers) != len(set(headers)):
        raise ValueError(f"{name}: duplicate normalized headers")
    required = OPEN_CLOSE_REQUIRED if product == "open_close_eod" else OPTION_EOD_REQUIRED
    missing_columns = sorted(set(required) - set(headers))
    if missing_columns:
        return {
            "member": name, "status": "FAIL_REQUIRED_COLUMNS",
            "column_count": len(headers), "missing_columns": missing_columns,
            "header_sha256": hashlib.sha256("\n".join(headers).encode()).hexdigest(),
        }

    key_fields = OPEN_CLOSE_SERIES_KEY if product == "open_close_eod" else OPTION_EOD_SERIES_KEY
    date_field = "quote_date"
    numeric_fields = (
        OPEN_CLOSE_VOLUME_FIELDS + ["open_interest", "previous_open_interest", "total_industry_vol"]
        if product == "open_close_eod"
        else ["trade_volume", "open_interest", "implied_volatility_1545", "delta_1545"]
    )
    rows = 0
    width_errors = 0
    missing_cells = Counter()
    zero_cells = Counter()
    invalid_numeric = Counter()
    underlyings = set()
    quote_dates = set()
    series_keys = set()
    duplicate_series = 0
    capacity_nonzero_rows = 0
    series_type_counts = Counter()
    call_put_counts = Counter()

    for raw in reader:
        rows += 1
        if None in raw:
            width_errors += 1
        row = {_norm(k): (v or "").strip() for k, v in raw.items() if k is not None}
        for field in ("underlying_symbol", date_field, *key_fields[1:]):
            if not row.get(field):
                missing_cells[field] += 1
        symbol = row.get("underlying_symbol", "")
        if symbol:
            underlyings.add(symbol)
        parsed_date = _parse_date(row.get(date_field, ""))
        if parsed_date:
            quote_dates.add(parsed_date)
        key = tuple(row.get(field, "") for field in key_fields)
        if all(key):
            if key in series_keys:
                duplicate_series += 1
            else:
                series_keys.add(key)
        if product == "open_close_eod":
            series_type_counts[row.get("series_type", "") or "BLANK"] += 1
            call_put_counts[row.get("call_put_flag", "") or "BLANK"] += 1
            if any(row.get(field, "").strip() not in ("", "0", "0.0") for field in OPEN_CLOSE_VOLUME_FIELDS):
                capacity_nonzero_rows += 1
        else:
            call_put_counts[row.get("option_type", "") or "BLANK"] += 1
        for field in numeric_fields:
            value = row.get(field, "")
            if value == "":
                missing_cells[field] += 1
                continue
            try:
                number = float(value.replace(",", ""))
                if number == 0:
                    zero_cells[field] += 1
                if number < 0 and field not in ("delta_1545", "theta_1545", "rho_1545"):
                    invalid_numeric[field] += 1
            except ValueError:
                invalid_numeric[field] += 1

    calc_columns = [field for field in OPTION_EOD_CALCS if field in headers]
    result = {
        "member": name,
        "status": "PASS_SAMPLE_SCHEMA" if rows > 0 and width_errors == 0 else "FAIL_SAMPLE_ROWS",
        "column_count": len(headers),
        "row_count": rows,
        "underlying_count": len(underlyings),
        "unique_series_count": len(series_keys),
        "duplicate_series_key_rows": duplicate_series,
        "quote_dates": sorted(quote_dates),
        "row_width_errors": width_errors,
        "missing_cells": dict(sorted(missing_cells.items())),
        "zero_cells": dict(sorted(zero_cells.items())),
        "invalid_numeric_cells": dict(sorted(invalid_numeric.items())),
        "call_put_counts": dict(sorted(call_put_counts.items())),
        "header_sha256": hashlib.sha256("\n".join(headers).encode()).hexdigest(),
    }
    if product == "open_close_eod":
        result.update({
            "series_type_counts": dict(sorted(series_type_counts.items())),
            "participant_volume_fields_present": len(set(OPEN_CLOSE_VOLUME_FIELDS) & set(headers)),
            "rows_with_any_nonzero_participant_volume": capacity_nonzero_rows,
            "participant_volume_fields": len(OPEN_CLOSE_VOLUME_FIELDS),
        })
    else:
        result.update({
            "calc_columns_present": calc_columns,
            "calc_columns_missing": sorted(set(OPTION_EOD_CALCS) - set(calc_columns)),
            "implied_volatility_zero_is_not_missing": True,
            "open_interest_semantics": "START_OF_DAY_OCC",
        })
    return result


def audit_archive(payload: bytes, *, product: str) -> dict:
    archive_hash = hashlib.sha256(payload).hexdigest()
    members = _extract_csv_members(payload)
    if not members:
        raise ValueError("sample archive contains no readable CSV member")
    audits = [_audit_csv(member, name=name, product=product) for name, member in members]
    return {
        "status": "PASS_SAMPLE_SCHEMA" if all(x["status"] == "PASS_SAMPLE_SCHEMA" for x in audits) else "FAIL_SAMPLE_SCHEMA",
        "archive_bytes": len(payload),
        "archive_sha256": archive_hash,
        "csv_members": audits,
        "member_count": len(audits),
        "row_count": sum(x.get("row_count", 0) for x in audits),
        "underlying_count_max_member": max((x.get("underlying_count", 0) for x in audits), default=0),
    }


def audit_intraday_sample(payload: bytes) -> dict:
    decoded = gzip.decompress(payload) if payload.startswith(b"\x1f\x8b") else payload
    text, headers = _decode_csv(decoded, "intraday_sample")
    reader = csv.DictReader(io.StringIO(text, newline=""))
    row_count = sum(1 for _ in reader)
    date_match = re.search(r"(\d{4}-\d{2}-\d{2})", INTRADAY_SAMPLE)
    market_date = date_match.group(1) if date_match else None
    return {
        "status": "PRE_CUTOVER_SAMPLE_LINK" if market_date and market_date < "2026-11-08" else "POST_CUTOVER_SAMPLE_LINK",
        "market_date_from_filename": market_date,
        "row_count": row_count,
        "column_count": len(headers),
        "headers_lowercase": all(x == x.lower() for x in headers),
        "trading_dt_present": "trading_dt" in headers,
        "trading_segment_present": "trading_segment" in headers,
        "v18_schema_present": all(x in headers for x in ("trading_dt", "trading_segment")),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "note": "The linked file's market date is before the 2026-11-08 v1.8 effective date; it cannot validate post-cutover schema or corrections.",
    }


def normalize_text(value: str) -> str:
    value = value.lower().replace("\u00a0", " ")
    return re.sub(r"\s+", " ", value).strip()


def audit_spec_text(open_close_text: str, option_eod_text: str) -> dict:
    oc = normalize_text(open_close_text)
    oe = normalize_text(option_eod_text)
    checks = {
        "open_close_v13": "v1.3 20251110" in oc,
        "preliminary_and_final_daily_files": "1 preliminary file and 1 final file per day" in oc,
        "next_morning_delivery_window": "typically delivered between 00:30am to 01:00am u.s. est the next morning" in oc,
        "final_oi_from_occ": "final file sources authoritative values from the occ" in oc,
        "capacity_mapping": all(x in oc for x in ("firm f, l, j", "broker-dealer b", "market maker m, n", "pro-customer u, w")),
        "option_eod_sod_oi": "start-of-day (sod) open interest" in oe,
        "option_eod_1545_greeks": all(x in oe for x in ("implied_volatility_1545", "delta_1545", "gamma_1545", "15:45")),
        "iv_zero_can_mean_unavailable_model_input": "implied volatility will be zero" in oe,
        "early_close_1545_field_uses_1245": "12:45 pm et" in oe,
        "option_eod_opra_coverage": "opra market data feed" in oe,
    }
    failed = [key for key, value in checks.items() if not value]
    return {
        "status": "PASS_EOD_SPEC_SEMANTICS" if not failed else "FAIL_EOD_SPEC_SEMANTICS",
        "checks": checks,
        "failed_checks": failed,
        "open_close_version": "v1.3",
        "option_eod_version": "v1.1",
        "open_close_preliminary_final_policy": "FINAL_FILE_ONLY_FOR_OCC_OPEN_INTEREST_AND_TOTAL_INDUSTRY_VOLUME",
        "open_close_documented_typical_delivery": "00:30-01:00 US Eastern next morning; not a per-file receipt SLA",
        "option_eod_open_interest": "START_OF_DAY_OCC",
        "option_eod_greeks_snapshot": "15:45 ET; early-close days use 12:45 ET while field name remains 1545",
    }


def _pdf_text(payload: bytes) -> tuple[str, int]:
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(payload), strict=True)
    return "\n".join(page.extract_text() or "" for page in reader.pages), len(reader.pages)


def _page_text(payload: bytes) -> str:
    parser = _Text()
    parser.feed(payload.decode("utf-8", errors="replace"))
    return normalize_text(" ".join(parser.parts))


def run_audit() -> dict:
    retrieved_at = datetime.now(timezone.utc).isoformat()
    oc_page = _download(OPEN_CLOSE_PAGE, accept="text/html,*/*")
    oe_page = _download(OPTION_EOD_PAGE, accept="text/html,*/*")
    oc_spec = _download(OPEN_CLOSE_SPEC, accept="application/pdf,*/*")
    oe_spec = _download(OPTION_EOD_SPEC, accept="application/pdf,*/*")
    oc_sample = _download(OPEN_CLOSE_SAMPLE, accept="application/zip,application/octet-stream,*/*")
    oe_sample = _download(OPTION_EOD_SAMPLE, accept="application/zip,application/octet-stream,*/*")

    oc_pdf_text, oc_pages = _pdf_text(oc_spec["payload"])
    oe_pdf_text, oe_pages = _pdf_text(oe_spec["payload"])
    spec_audit = audit_spec_text(oc_pdf_text, oe_pdf_text)
    oc_product_text = _page_text(oc_page["payload"])
    oe_product_text = _page_text(oe_page["payload"])
    product_checks = {
        "open_close_eod_history_c1_2005": "2005-01-03" in oc_product_text,
        "open_close_eod_history_other_venues_2018": "2018-01-02" in oc_product_text,
        "open_close_eod_overnight_delivery": "overnight after midnight u.s. eastern" in oc_product_text,
        "open_close_oi_and_industry_volume_are_value_adds": "total industry volume and open interest" in oc_product_text and "third-party vendors" in oc_product_text,
        "option_eod_history_2012": "available from january 2012 to present" in oe_product_text,
        "option_eod_opra_and_daily": "opra market data feed" in oe_product_text and "daily file delivery" in oe_product_text,
    }

    oc_audit = audit_archive(oc_sample["payload"], product="open_close_eod")
    oe_audit = audit_archive(oe_sample["payload"], product="option_eod")
    try:
        intraday_download = _download(INTRADAY_SAMPLE, accept="application/gzip,application/octet-stream,*/*")
        intraday_audit = audit_intraday_sample(intraday_download["payload"])
        intraday_audit["http_status"] = intraday_download["http_status"]
        intraday_audit["content_type"] = intraday_download["content_type"]
    except Exception as error:
        intraday_audit = {
            "status": "SAMPLE_DOWNLOAD_FAILED",
            "error_type": type(error).__name__,
            "error": str(error)[:400],
            "market_date_from_filename": "2026-09-30",
            "v18_schema_present": False,
        }

    all_product_checks = all(product_checks.values())
    samples_pass = oc_audit["status"] == "PASS_SAMPLE_SCHEMA" and oe_audit["status"] == "PASS_SAMPLE_SCHEMA"
    result = {
        "status": "PASS_DAILY_EOD_PAIR_SAMPLE_AND_SPEC_AUDIT" if spec_audit["status"] == "PASS_EOD_SPEC_SEMANTICS" and all_product_checks and samples_pass else "FAIL_DAILY_EOD_PAIR_AUDIT",
        "retrieved_at_utc": retrieved_at,
        "specifications": {
            "open_close_eod": {
                "url": OPEN_CLOSE_SPEC, "sha256": hashlib.sha256(oc_spec["payload"]).hexdigest(),
                "bytes": len(oc_spec["payload"]), "pages": oc_pages,
            },
            "option_eod_summary": {
                "url": OPTION_EOD_SPEC, "sha256": hashlib.sha256(oe_spec["payload"]).hexdigest(),
                "bytes": len(oe_spec["payload"]), "pages": oe_pages,
            },
            **spec_audit,
        },
        "product_pages": {
            "open_close": {"url": OPEN_CLOSE_PAGE, "sha256": hashlib.sha256(oc_page["payload"]).hexdigest(), "checks": {k:v for k,v in product_checks.items() if k.startswith("open_close")}},
            "option_eod": {"url": OPTION_EOD_PAGE, "sha256": hashlib.sha256(oe_page["payload"]).hexdigest(), "checks": {k:v for k,v in product_checks.items() if k.startswith("option_eod")}},
            "checks": product_checks,
        },
        "samples": {
            "open_close_eod": {"url": OPEN_CLOSE_SAMPLE, **oc_audit},
            "option_eod_summary": {"url": OPTION_EOD_SAMPLE, **oe_audit},
            "open_close_1m_v18_linked_sample": {"url": INTRADAY_SAMPLE, **intraday_audit},
        },
        "source_interpretation": {
            "daily_pair": "Cboe Open-Close EOD participant-capacity/open-close volumes plus OPRA Option EOD Summary 15:45 IV/Greeks and SOD OCC open interest",
            "combined_full_four_venue_start": "2018-01-02",
            "c1_only_start": "2005-01-03",
            "option_eod_context_start": "2012-01",
            "open_close_venues": ["C1", "C2", "BZX", "EDGX"],
            "option_eod_scope": "OPRA-listed U.S. stock, ETF and index options; RTH only",
            "session_alignment_warning": "Open-Close product page says C1 includes RTH and GTH, while Option EOD specification says RTH only; do not assume a fully aligned C1 denominator until clarified.",
            "contract_join_warning": "Open-Close EOD has series_type (S/N/F); Option EOD Summary does not. Do not blindly join nonstandard/Flex contracts by root/expiry/strike/type without a deterministic class/deliverable crosswalk.",
            "preliminary_final_warning": "Open-Close subscriptions have preliminary and final files; use final only for OCC-sourced OI and total-industry volume, and preserve both vintages if ever captured.",
            "availability_warning": "Documented typical next-morning delivery is not an immutable historical first-receipt ledger. Do not claim strict historical PIT from backfilled samples.",
            "license_warning": "Cboe raw data is internal-use only; derived external distribution requires additional approval/licensing.",
        },
        "gates": {
            "eod_sample_schema_pass": samples_pass,
            "historical_coverage_established": False,
            "historical_pit_admitted": False,
            "prospective_pit_admitted": False,
            "licensing_confirmed": False,
            "return_test_authorized": False,
            "alpha_admission": False,
            "holdout_used": False,
            "f80_frozen": True,
        },
        "decision": "PRIORITIZE_DAILY_EOD_PAIR_FOR_NEXT_FEASIBILITY_GATE_NO_PIT_NO_ALPHA",
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("phase353_output/audit.json"))
    args = parser.parse_args()
    try:
        result = run_audit()
        code = 0 if result["status"] == "PASS_DAILY_EOD_PAIR_SAMPLE_AND_SPEC_AUDIT" else 2
    except Exception as error:
        result = {
            "status": "AUDIT_EXECUTION_FAILED",
            "error_type": type(error).__name__,
            "error": str(error)[:500],
            "historical_pit_admitted": False,
            "return_test_authorized": False,
            "alpha_admission": False,
            "f80_frozen": True,
        }
        code = 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True), flush=True)
    return code


if __name__ == "__main__":
    raise SystemExit(main())

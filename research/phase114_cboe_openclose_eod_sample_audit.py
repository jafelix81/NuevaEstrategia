#!/usr/bin/env python3
"""Phase 114: audit Cboe Open-Close EOD public sample and bucket accounting."""
from __future__ import annotations
import argparse, csv, gzip, hashlib, io, json, time, zipfile
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any
import requests

SAMPLE_URL = "https://datashop.cboe.com/download/sample/218"
EOD_SPEC_URL = "https://datashop.cboe.com/documents/Open_Close_EOD_Spec_v1.3.pdf"
LEGACY_SPEC_URL = "https://datashop.cboe.com/documents/Legacy_C1_Open_Close_EOD_Spec_v2.7.pdf"
PRODUCT_URL = "https://datashop.cboe.com/cboe-options-open-close-volume-summary"

BASE_FIELDS = [
    "quote_date", "underlying_symbol", "security_type", "option_symbol",
    "expiration_date", "strike_price", "call_put_flag", "days_to_expire",
    "series_type", "first_trade_price", "high_trade_price", "low_trade_price",
    "last_trade_price", "total_exchange_vol", "total_industry_vol",
    "open_interest", "previous_open_interest", "previous_close",
]

def category_fields() -> list[str]:
    fields: list[str] = []
    for category in ("firm", "bd"):
        for action in ("open", "close"):
            for side in ("buy", "sell"):
                for metric in ("qty", "vol"):
                    fields.append(f"{category}_{action}_{side}_{metric}")
    for side in ("buy", "sell"):
        for metric in ("qty", "vol"):
            fields.append(f"mm_{side}_{metric}")
    for category in ("cust", "procust"):
        for bucket in ("lt_100", "100_199", "gt_199"):
            for action in ("open", "close"):
                for side in ("buy", "sell"):
                    for metric in ("qty", "vol"):
                        fields.append(f"{category}_{bucket}_{action}_{side}_{metric}")
    return fields

POST_2011_REQUIRED = BASE_FIELDS + category_fields()
VOLUME_FIELDS = [x for x in POST_2011_REQUIRED if x.endswith("_vol") and x != "total_exchange_vol"]
COUNT_FIELDS = [x for x in POST_2011_REQUIRED if x.endswith("_qty")]
TOTAL_FIELDS = ["total_exchange_vol", "total_industry_vol", "open_interest", "previous_open_interest"]
PRICE_FIELDS = ["strike_price", "first_trade_price", "high_trade_price", "low_trade_price", "last_trade_price", "previous_close"]

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def request_bytes(session: requests.Session, url: str) -> dict[str, Any]:
    attempts = []
    response = None
    for attempt in range(1, 4):
        try:
            response = session.get(url, timeout=90)
            attempts.append({"attempt": attempt, "status": response.status_code, "bytes": len(response.content)})
            if response.status_code == 200:
                break
            if response.status_code not in (429, 500, 502, 503, 504):
                break
        except requests.RequestException as exc:
            attempts.append({"attempt": attempt, "error": type(exc).__name__})
        if attempt < 3:
            time.sleep(attempt * 2)
    if response is None:
        return {"url": url, "available": False, "attempts": attempts, "error": "request_failed"}
    payload = response.content
    return {
        "url": response.url, "available": response.status_code == 200,
        "http_status": response.status_code, "content_type": response.headers.get("Content-Type"),
        "last_modified": response.headers.get("Last-Modified"), "etag": response.headers.get("ETag"),
        "bytes": len(payload), "sha256": sha256(payload), "attempts": attempts, "content": payload,
    }

def looks_like_csv(data: bytes) -> bool:
    preview = data[:20000].decode("utf-8-sig", errors="replace").lower()
    return "quote_date" in preview and "underlying_symbol" in preview and "total_exchange_vol" in preview

def collect_csv_payloads(data: bytes, name: str = "sample", depth: int = 0):
    found: list[dict[str, Any]] = []
    entries: list[dict[str, Any]] = []
    if depth > 6:
        return found, entries
    bio = io.BytesIO(data)
    if zipfile.is_zipfile(bio):
        with zipfile.ZipFile(bio) as archive:
            for info in archive.infolist():
                if info.is_dir():
                    continue
                payload = archive.read(info)
                child = f"{name}!{info.filename}"
                entries.append({"name": child, "bytes": len(payload), "sha256": sha256(payload)})
                nested, nested_entries = collect_csv_payloads(payload, child, depth + 1)
                found.extend(nested)
                entries.extend(nested_entries)
        return found, entries
    if data[:2] == b"\x1f\x8b":
        try:
            payload = gzip.decompress(data)
        except OSError:
            return found, entries
        child = f"{name}!gzip"
        entries.append({"name": child, "bytes": len(payload), "sha256": sha256(payload)})
        nested, nested_entries = collect_csv_payloads(payload, child, depth + 1)
        found.extend(nested)
        entries.extend(nested_entries)
        return found, entries
    if looks_like_csv(data):
        found.append({"name": name, "content": data, "bytes": len(data), "sha256": sha256(data)})
    return found, entries

def parse_date(value: str):
    value = (value or "").strip()
    for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%Y%m%d"):
        try:
            return datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            pass
    return None

def parse_int(value: str | None) -> int | None:
    if value is None or not value.strip():
        return None
    try:
        number = Decimal(value.strip().replace(",", ""))
    except InvalidOperation:
        return None
    if number != number.to_integral_value():
        return None
    return int(number)

def parse_decimal(value: str | None) -> Decimal | None:
    if value is None or not value.strip():
        return None
    try:
        return Decimal(value.strip().replace(",", ""))
    except InvalidOperation:
        return None

def parse_csv_bytes(payload: bytes, source_name: str = "sample.csv") -> dict[str, Any]:
    text = payload.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    fields = [str(x or "").strip().lower() for x in (reader.fieldnames or [])]
    field_set = set(fields)
    missing = sorted(set(POST_2011_REQUIRED) - field_set)
    rows = list(reader)
    errors = Counter()
    blanks = Counter()
    dates = Counter()
    underlyings = set()
    keys = []
    buy_bucket_total = sell_bucket_total = side_bucket_total = 0
    exchange_total = industry_total = 0
    match_rows = eligible_rows = 0
    mismatch_samples = []
    category_totals = Counter()
    security_types = Counter()
    series_types = Counter()
    volume_fields_present = [x for x in VOLUME_FIELDS if x in field_set]
    qty_fields_present = [x for x in COUNT_FIELDS if x in field_set]
    price_fields_present = [x for x in PRICE_FIELDS if x in field_set]
    total_fields_present = [x for x in TOTAL_FIELDS if x in field_set]

    for row_no, raw in enumerate(rows, start=2):
        row = {str(k or "").strip().lower(): (v or "").strip() for k, v in raw.items()}
        date_value = parse_date(row.get("quote_date", ""))
        if not date_value:
            errors["invalid_quote_date"] += 1
        else:
            dates[date_value] += 1
        underlying = row.get("underlying_symbol", "")
        underlyings.add(underlying)
        security_types[row.get("security_type", "")] += 1
        series_types[row.get("series_type", "")] += 1
        keys.append((date_value, underlying, row.get("security_type", ""), row.get("option_symbol", ""),
                     row.get("expiration_date", ""), row.get("strike_price", ""),
                     row.get("call_put_flag", ""), row.get("series_type", "")))

        parsed_volumes = {}
        row_volume_complete = True
        for field in volume_fields_present:
            value = row.get(field, "")
            if not value:
                blanks[field] += 1
                row_volume_complete = False
                continue
            number = parse_int(value)
            if number is None:
                errors[f"invalid_{field}"] += 1
                row_volume_complete = False
                continue
            if number < 0:
                errors["negative_volume"] += 1
            parsed_volumes[field] = number
            category_totals[field] += number

        for field in qty_fields_present:
            value = row.get(field, "")
            if not value:
                blanks[field] += 1
                continue
            number = parse_int(value)
            if number is None:
                errors[f"invalid_{field}"] += 1
            elif number < 0:
                errors["negative_quantity"] += 1

        for field in total_fields_present:
            value = row.get(field, "")
            if not value:
                blanks[field] += 1
                continue
            number = parse_int(value)
            if number is None:
                errors[f"invalid_{field}"] += 1
            elif number < 0:
                errors[f"negative_{field}"] += 1
            elif field == "total_exchange_vol":
                exchange_total += number
            elif field == "total_industry_vol":
                industry_total += number

        for field in price_fields_present:
            value = row.get(field, "")
            if not value:
                continue
            number = parse_decimal(value)
            if number is None:
                errors[f"invalid_{field}"] += 1
            elif number < 0:
                errors[f"negative_{field}"] += 1

        if row_volume_complete and "total_exchange_vol" in field_set:
            total = parse_int(row.get("total_exchange_vol", ""))
            if total is not None:
                buy = sum(v for k, v in parsed_volumes.items() if "_buy_vol" in k)
                sell = sum(v for k, v in parsed_volumes.items() if "_sell_vol" in k)
                bucket_total = buy + sell
                eligible_rows += 1
                buy_bucket_total += buy
                sell_bucket_total += sell
                side_bucket_total += bucket_total
                if bucket_total == total:
                    match_rows += 1
                elif len(mismatch_samples) < 25:
                    mismatch_samples.append({
                        "source_row": row_no, "underlying": underlying,
                        "option_symbol": row.get("option_symbol"), "total_exchange_vol": total,
                        "bucket_buy_vol": buy, "bucket_sell_vol": sell, "bucket_total": bucket_total,
                        "difference": bucket_total - total,
                    })

    duplicate_excess = len(keys) - len(set(keys))
    duplicate_samples = []
    if duplicate_excess:
        seen = set()
        for idx, key in enumerate(keys, start=2):
            if key in seen and len(duplicate_samples) < 25:
                duplicate_samples.append({"source_row": idx, "key": list(key)})
            seen.add(key)
    match_rate = (match_rows / eligible_rows) if eligible_rows else None
    return {
        "source_name": source_name, "source_bytes": len(payload), "source_sha256": sha256(payload),
        "field_count": len(fields), "fields": fields, "missing_required_fields": missing,
        "row_count": len(rows), "date_counts": dict(sorted(dates.items())),
        "underlying_count": len(underlyings), "underlying_preview": sorted(underlyings)[:50],
        "security_type_counts": dict(security_types), "series_type_counts": dict(series_types),
        "duplicate_key_excess": duplicate_excess, "duplicate_key_samples": duplicate_samples,
        "numeric_error_counts": dict(errors), "blank_numeric_counts": dict(blanks),
        "volume_fields_present": volume_fields_present, "quantity_fields_present": qty_fields_present,
        "total_fields_present": total_fields_present, "price_fields_present": price_fields_present,
        "buy_bucket_volume_sum": buy_bucket_total, "sell_bucket_volume_sum": sell_bucket_total,
        "participant_side_bucket_volume_sum": side_bucket_total,
        "total_exchange_volume_sum": exchange_total, "total_industry_volume_sum": industry_total,
        "volume_reconciliation_eligible_rows": eligible_rows, "volume_reconciliation_exact_rows": match_rows,
        "volume_reconciliation_exact_rate": match_rate, "volume_reconciliation_mismatch_samples": mismatch_samples,
        "category_volume_totals": dict(category_totals),
    }

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="phase114_cboe_openclose_output")
    args = parser.parse_args()
    output = Path(args.output)
    raw_dir = output / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update({"User-Agent": "NuevaEstrategia-Research/Phase114", "Accept": "*/*"})
    sample = request_bytes(session, SAMPLE_URL)
    spec = request_bytes(session, EOD_SPEC_URL)
    legacy = request_bytes(session, LEGACY_SPEC_URL)
    for name, record in (("openclose_public_sample.zip", sample), ("openclose_eod_spec_v1.3.pdf", spec),
                         ("openclose_legacy_c1_spec_v2.7.pdf", legacy)):
        content = record.pop("content", None)
        if content is not None:
            (raw_dir / name).write_bytes(content)
            record["raw_file"] = name
    csv_payloads, archive_entries = collect_csv_payloads((raw_dir / "openclose_public_sample.zip").read_bytes()) if sample.get("available") else ([], [])
    parsed = [parse_csv_bytes(item["content"], item["name"]) for item in csv_payloads]
    summary = {
        "phase": 114, "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "product_url": PRODUCT_URL, "sample": sample, "current_spec": spec, "legacy_spec": legacy,
        "archive_entries": archive_entries, "csv_payload_count": len(parsed),
        "parsed_files": parsed, "total_parsed_rows": sum(x["row_count"] for x in parsed),
        "data_gate": "PASS_SAMPLE_SCHEMA" if parsed and all(not p["missing_required_fields"] and
            p["duplicate_key_excess"] == 0 and not p["numeric_error_counts"] for p in parsed) else "FAIL_OR_INCOMPLETE",
        "volume_reconciliation_gate": "EXACT" if parsed and all(
            p["volume_reconciliation_eligible_rows"] > 0 and
            p["volume_reconciliation_exact_rows"] == p["volume_reconciliation_eligible_rows"] for p in parsed
        ) else "NOT_EXACT_OR_NOT_TESTABLE",
        "limitations": [
            "Public sample does not establish historical file completeness, full-market coverage, or license cost.",
            "C1-only data are not whole-OPRA market coverage.",
            "Customer, ProCustomer, BrokerDealer, Firm and MarketMaker are clearing origin/capacity categories, not beneficial-owner identities.",
            "Pre-2011 customer size buckets are based on order size; post-2011 buckets are based on execution size.",
            "C1 total_exchange_vol convention changes through 2019-10-04; C1 OI fields are shifted one day ahead through that date.",
            "C1 Global Trading Hours coverage starts 2023-12-11.",
            "No forward returns, alpha tests, purchases, subscriptions, authentication or vendor contact occurred.",
        ],
    }
    (output / "phase114_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["data_gate"] == "PASS_SAMPLE_SCHEMA" else 1

if __name__ == "__main__":
    raise SystemExit(main())

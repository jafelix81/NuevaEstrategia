#!/usr/bin/env python3
"""Phase 187: ORATS Near-EOD public sample and PIT-feasibility audit."""
from __future__ import annotations
import argparse, csv, hashlib, io, json, math, re, zipfile
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

SOURCE_URL = "https://s3.amazonaws.com/assets.orats.com/ORATS_SMV_Strikes_20240103.zip"
EXPECTED_SAMPLE_DATE = "2024-01-03"
MAX_COMPRESSED_BYTES = 200_000_000
MAX_UNCOMPRESSED_BYTES = 1_000_000_000
MAX_MEMBERS = 32
ET = ZoneInfo("America/New_York")

FIELD_ALIASES = {
    "ticker": {"ticker", "underlyingsymbol"},
    "trade_date": {"tradedate", "tradedt", "marketdate"},
    "expiration": {"expirdate", "expiration", "expirationdate"},
    "strike": {"strike"},
    "call_volume": {"callvolume", "cvolu"},
    "put_volume": {"putvolume", "pvolu"},
    "call_oi": {"callopeninterest", "coi", "calloi"},
    "put_oi": {"putopeninterest", "poi", "putoi"},
}
OPTIONAL_TIMESTAMP_ALIASES = {
    "updated_at": {"updatedat", "updatedtime", "updatetime"},
}
OPTIONAL_IV_ALIASES = {
    "call_mid_iv": {"callmidiv", "cmidiv"},
    "put_mid_iv": {"putmidiv", "pmidiv"},
    "smv_vol": {"smvvol"},
    "call_bid_iv": {"callbidiv", "cbidiv"},
    "put_bid_iv": {"putbidiv", "pbidiv"},
}
OPTIONAL_REFERENCE_ALIASES = {
    "root": {"root", "optionroot"},
    "dte": {"dte", "yte"},
    "stock_price_reference": {"stockprice", "stkpx", "spotprice", "spotpx"},
}

def _norm(value):
    return re.sub(r"[^a-z0-9]", "", str(value or "").strip().lower())

def _parse_date(value):
    raw = str(value or "").strip()
    if not raw:
        return None
    for fmt in ("%Y-%m-%d", "%Y%m%d", "%m/%d/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            pass
    return None

def _parse_number(value):
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        result = float(raw)
    except ValueError:
        return None
    return result if math.isfinite(result) else None

def _parse_timestamp(value):
    raw = str(value or "").strip()
    if not raw:
        return None
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        return None

def _field_map(headers):
    by_norm = {}
    duplicates = []
    for header in headers:
        key = _norm(header)
        if key in by_norm:
            duplicates.append(key)
        else:
            by_norm[key] = header
    resolved, missing = {}, []
    for canonical, aliases in FIELD_ALIASES.items():
        found = next((by_norm[a] for a in sorted(aliases) if a in by_norm), None)
        if found is None:
            missing.append(canonical)
        else:
            resolved[canonical] = found
    for canonical, aliases in {**OPTIONAL_TIMESTAMP_ALIASES, **OPTIONAL_IV_ALIASES, **OPTIONAL_REFERENCE_ALIASES}.items():
        found = next((by_norm[a] for a in aliases if a in by_norm), None)
        if found is not None:
            resolved[canonical] = found
    return resolved, sorted(set(missing)), sorted(set(duplicates))

def audit_csv(member_name, payload):
    try:
        text = payload.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("sample_csv_not_utf8") from exc
    reader = csv.DictReader(io.StringIO(text, newline=""))
    headers = reader.fieldnames or []
    fields, missing, duplicates = _field_map(headers)
    out = {
        "member_basename": Path(member_name).name,
        "member_sha256": hashlib.sha256(payload).hexdigest(),
        "header_sha256": hashlib.sha256(",".join(_norm(x) for x in headers).encode()).hexdigest(),
        "column_count": len(headers),
        "header_names": list(headers),
        "timestamp_field_present": "updated_at" in fields,
        "timestamp_field_name": fields.get("updated_at"),
        "missing_required_fields": missing,
        "duplicate_normalized_headers": duplicates,
        "schema_pass": not missing and not duplicates,
        "row_count": 0, "blank_rows": 0, "unique_underlying_count": 0,
        "unique_contract_key_count": 0, "duplicate_contract_key_rows": 0,
        "trade_date_counts": {}, "trade_date_filename_mismatch_rows": 0,
        "expiration_parse_fail_rows": 0, "invalid_strike_rows": 0,
        "missing_required_value_rows": 0, "invalid_volume_or_oi_rows": 0,
        "zero_call_volume_rows": 0, "zero_put_volume_rows": 0,
        "zero_call_oi_rows": 0, "zero_put_oi_rows": 0,
        "iv_zero_or_missing_counts": {}, "updated_at_missing_rows": 0,
        "updated_at_absent_rows": 0, "updated_at_parse_fail_rows": 0,
        "updated_at_naive_rows": 0, "updated_at_aware_rows": 0,
        "updated_at_et_time_counts": {}, "updated_at_et_min": None,
        "updated_at_et_max": None, "raw_rows_persisted": False,
        "raw_symbols_persisted": False, "raw_contracts_persisted": False,
    }
    if missing or duplicates:
        return out
    tickers, contract_keys = set(), set()
    trade_dates, iv_zero_missing, updated_times = Counter(), Counter(), Counter()
    updated_min = updated_max = None
    mismatch = expiration_fail = strike_fail = missing_values = invalid_vol_oi = 0
    zero_call_vol = zero_put_vol = zero_call_oi = zero_put_oi = 0
    blank_rows = duplicate_keys = parse_fail = naive_ts = aware_ts = missing_ts = 0
    match = re.search(r"(\d{8})", Path(member_name).name)
    expected_date = _parse_date(match.group(1)) if match else date.fromisoformat(EXPECTED_SAMPLE_DATE)
    for raw in reader:
        row = {str(k).strip(): v for k, v in raw.items() if k is not None}
        if not any(str(v or "").strip() for v in row.values()):
            blank_rows += 1
            continue
        out["row_count"] += 1
        values = {k: str(row.get(col, "") or "").strip() for k, col in fields.items()}
        if any(not values.get(k) for k in ("ticker", "trade_date", "expiration", "strike",
                                             "call_volume", "put_volume", "call_oi", "put_oi")):
            missing_values += 1
        ticker = values.get("ticker", "").upper()
        trade_day = _parse_date(values.get("trade_date"))
        expiration = _parse_date(values.get("expiration"))
        if ticker:
            tickers.add(ticker)
        if trade_day:
            trade_dates[trade_day.isoformat()] += 1
            if expected_date and trade_day != expected_date:
                mismatch += 1
        if expiration is None:
            expiration_fail += 1
        strike = _parse_number(values.get("strike"))
        if strike is None or strike <= 0:
            strike_fail += 1
        root = values.get("root", "").upper()
        if ticker and trade_day and expiration and strike is not None:
            key = (ticker, trade_day.isoformat(), expiration.isoformat(), str(strike), root)
            if key in contract_keys:
                duplicate_keys += 1
            else:
                contract_keys.add(key)
        for field, label in (("call_volume", "call"), ("put_volume", "put"),
                             ("call_oi", "call_oi"), ("put_oi", "put_oi")):
            n = _parse_number(values.get(field))
            if n is None or n < 0:
                invalid_vol_oi += 1
            elif n == 0:
                if label == "call": zero_call_vol += 1
                elif label == "put": zero_put_vol += 1
                elif label == "call_oi": zero_call_oi += 1
                else: zero_put_oi += 1
        for field in OPTIONAL_IV_ALIASES:
            if field in fields:
                n = _parse_number(values.get(field))
                if n is None or n <= 0:
                    iv_zero_missing[field] += 1
        if "updated_at" in fields:
            raw_stamp = values.get("updated_at", "")
            if not raw_stamp:
                missing_ts += 1
            else:
                stamp = _parse_timestamp(raw_stamp)
                if stamp is None:
                    parse_fail += 1
                elif stamp.tzinfo is None:
                    naive_ts += 1
                else:
                    aware_ts += 1
                    et_stamp = stamp.astimezone(ET)
                    updated_times[et_stamp.strftime("%H:%M:%S")] += 1
                    updated_min = et_stamp if updated_min is None or et_stamp < updated_min else updated_min
                    updated_max = et_stamp if updated_max is None or et_stamp > updated_max else updated_max
    out.update({
        "blank_rows": blank_rows, "unique_underlying_count": len(tickers),
        "unique_contract_key_count": len(contract_keys), "duplicate_contract_key_rows": duplicate_keys,
        "trade_date_counts": dict(sorted(trade_dates.items())),
        "trade_date_filename_mismatch_rows": mismatch,
        "expiration_parse_fail_rows": expiration_fail, "invalid_strike_rows": strike_fail,
        "missing_required_value_rows": missing_values, "invalid_volume_or_oi_rows": invalid_vol_oi,
        "zero_call_volume_rows": zero_call_vol, "zero_put_volume_rows": zero_put_vol,
        "zero_call_oi_rows": zero_call_oi, "zero_put_oi_rows": zero_put_oi,
        "iv_zero_or_missing_counts": dict(sorted(iv_zero_missing.items())),
        "updated_at_missing_rows": missing_ts,
        "updated_at_absent_rows": out["row_count"] if "updated_at" not in fields else 0,
        "updated_at_parse_fail_rows": parse_fail, "updated_at_naive_rows": naive_ts,
        "updated_at_aware_rows": aware_ts, "updated_at_et_time_counts": dict(sorted(updated_times.items())),
        "updated_at_et_min": updated_min.isoformat() if updated_min else None,
        "updated_at_et_max": updated_max.isoformat() if updated_max else None,
    })
    return out

def audit_archive(payload, retrieved_at_utc=None):
    if len(payload) > MAX_COMPRESSED_BYTES:
        raise ValueError("sample_archive_exceeds_compressed_limit")
    try:
        archive = zipfile.ZipFile(io.BytesIO(payload))
    except zipfile.BadZipFile as exc:
        raise ValueError("sample_archive_not_zip") from exc
    infos = archive.infolist()
    if len(infos) > MAX_MEMBERS:
        raise ValueError("sample_archive_too_many_members")
    if sum(x.file_size for x in infos) > MAX_UNCOMPRESSED_BYTES:
        raise ValueError("sample_archive_exceeds_uncompressed_limit")
    audits = []
    for info in infos:
        parts = Path(info.filename).parts
        if Path(info.filename).is_absolute() or ".." in parts:
            raise ValueError("unsafe_archive_member_path")
        if info.filename.lower().endswith(".csv"):
            audits.append(audit_csv(info.filename, archive.read(info)))
    if not audits:
        raise ValueError("sample_archive_has_no_csv_members")
    schema_pass = all(bool(x["schema_pass"]) for x in audits)
    rows = sum(int(x["row_count"]) for x in audits)
    underlyings = max(int(x["unique_underlying_count"]) for x in audits)
    mismatch = sum(int(x["trade_date_filename_mismatch_rows"]) for x in audits)
    parse_errors = sum(int(x["updated_at_parse_fail_rows"]) for x in audits)
    naive = sum(int(x["updated_at_naive_rows"]) for x in audits)
    missing_ts = sum(int(x["updated_at_missing_rows"]) for x in audits)
    timestamp_members = sum(bool(x["timestamp_field_present"]) for x in audits)
    timestamp_aware = sum(int(x["updated_at_aware_rows"]) for x in audits)
    timestamp_diagnostic_pass = (timestamp_members == len(audits) and timestamp_aware == rows
                                 and missing_ts == 0 and parse_errors == 0 and naive == 0)
    missing = sum(int(x["missing_required_value_rows"]) for x in audits)
    invalid = sum(int(x["invalid_volume_or_oi_rows"]) + int(x["invalid_strike_rows"]) +
                  int(x["expiration_parse_fail_rows"]) for x in audits)
    duplicate_keys = sum(int(x["duplicate_contract_key_rows"]) for x in audits)
    passed = schema_pass and rows > 0 and underlyings > 0 and mismatch == 0 and missing == 0 and invalid == 0 and duplicate_keys == 0
    if not passed:
        status = "PUBLIC_SAMPLE_DIAGNOSTIC_REQUIRES_REVIEW"
    elif timestamp_members == 0:
        status = "PUBLIC_SAMPLE_SCHEMA_AND_ROW_DIAGNOSTICS_PASS_TIMESTAMP_ABSENT"
    elif timestamp_diagnostic_pass:
        status = "PUBLIC_SAMPLE_SCHEMA_AND_ROW_DIAGNOSTICS_PASS_TIMESTAMP_PRESENT"
    else:
        status = "PUBLIC_SAMPLE_SCHEMA_AND_ROW_DIAGNOSTICS_PASS_OPTIONAL_TIMESTAMP_INCOMPLETE"
    return {
        "phase": 187, "source": "ORATS Near End-of-Day historical options chain",
        "sample_url": SOURCE_URL, "expected_sample_date": EXPECTED_SAMPLE_DATE,
        "archive_sha256": hashlib.sha256(payload).hexdigest(), "compressed_bytes": len(payload),
        "retrieved_at_utc": retrieved_at_utc or datetime.now(timezone.utc).isoformat(),
        "csv_member_count": len(audits), "member_audits": audits,
        "sample_schema_pass": schema_pass, "sample_overall_pass": passed,
        "timestamp_field_present": timestamp_members == len(audits),
        "timestamp_field_members": timestamp_members,
        "timestamp_aware_rows": timestamp_aware,
        "timestamp_missing_rows": missing_ts,
        "timestamp_parse_fail_rows": parse_errors,
        "timestamp_naive_rows": naive,
        "timestamp_diagnostic_pass": timestamp_diagnostic_pass,
        "duplicate_contract_key_rows": duplicate_keys,
        "overall_status": status,
        "historical_coverage_verified": False, "inactive_delisted_coverage_verified": False,
        "historical_first_receipt_vintages_verified": False, "strict_pit_admitted": False,
        "aggressor_side_available": False, "open_close_available": False,
        "participant_capacity_available": False, "beneficial_owner_identity_available": False,
        "measurement_semantics": {
            "near_eod_snapshot_minutes_before_close": 14,
            "call_put_volume": "cumulative daily total as of the observed snapshot; not interval increments or signed flow",
            "open_interest": "OCC prior-night open interest; not same-day opening activity",
            "greeks_and_iv": "vendor-smoothed/model-derived values",
            "underlying_reference_price": "put-call-parity-derived reference; not an independent stock price"
        },
        "delivery_and_pit": {
            "recurring_daily_file_claim": "ready each night at midnight ET",
            "historical_archive_first_receipt_verified": False,
            "per_file_receipt_log_required": True,
            "immutable_revision_vintages_verified": False,
            "historical_backfill_is_not_live_vintage_proof": True,
            "next_session_execution_required_for_future_daily_use": True
        },
        "published_individual_pricing_usd": {
            "near_eod_historical_one_time": 599, "near_eod_recurring_monthly": 99,
            "one_minute_historical_one_time": 1500, "one_minute_recurring_monthly": 199,
            "one_minute_storage_transfer_estimate_range": [1000, 2000],
            "professional_institutional_terms": "not established by individual pricing display; separate terms/quote must be confirmed"
        },
        "controls": {
            "alpha_test_authorized": False, "holdout_used": False, "vendor_contact": False,
            "data_purchase": False, "production_changed": False, "f80_frozen": True,
            "raw_rows_persisted": False, "raw_symbols_persisted": False
        }
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("phase187_output/phase187_orats_near_eod_sample_audit.json"))
    args = parser.parse_args()
    request = Request(SOURCE_URL, headers={"User-Agent": "NuevaEstrategia research audit"})
    with urlopen(request, timeout=90) as response:
        payload = response.read(MAX_COMPRESSED_BYTES + 1)
    if len(payload) > MAX_COMPRESSED_BYTES:
        raise ValueError("sample_archive_exceeds_compressed_limit")
    result = audit_archive(payload)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["sample_overall_pass"] else 1

if __name__ == "__main__":
    raise SystemExit(main())

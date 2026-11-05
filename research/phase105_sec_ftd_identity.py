#!/usr/bin/env python3
"""Phase 105: same-day CUSIP/symbol identity diagnostics for official SEC FTD files.

Data identity/PIT feasibility only. No forward returns or alpha tests.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import sys
import zipfile
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from research.phase102_sec_ftd_multiperiod_audit import SAMPLES, USER_AGENT, parse_text_member

OUT = Path("phase105_sec_ftd_identity")


def build_mapping_diagnostics(records: list[dict]):
    date_cusip_symbols = defaultdict(set)
    date_symbol_cusips = defaultdict(set)
    date_cusip_descriptions = defaultdict(set)
    date_symbol_descriptions = defaultdict(set)
    cusip_symbols_over_sample = defaultdict(set)
    symbol_cusips_over_sample = defaultdict(set)
    key_counts = Counter()
    blank_symbol_rows = blank_cusip_rows = invalid_cusip_rows = 0
    unique_dates = set()

    for row in records:
        dt = str(row.get("settlement_date") or "")
        cusip = str(row.get("cusip") or "").strip().upper()
        symbol = str(row.get("symbol") or "").strip().upper()
        description = str(row.get("description") or "").strip()
        if not dt:
            continue
        unique_dates.add(dt)
        if not cusip:
            blank_cusip_rows += 1
        elif not re.fullmatch(r"[A-Z0-9]{9}", cusip):
            invalid_cusip_rows += 1
        if not symbol:
            blank_symbol_rows += 1

        if cusip:
            if symbol:
                date_cusip_symbols[(dt, cusip)].add(symbol)
                cusip_symbols_over_sample[cusip].add(symbol)
            if description:
                date_cusip_descriptions[(dt, cusip)].add(description)
        if symbol:
            if cusip:
                date_symbol_cusips[(dt, symbol)].add(cusip)
                symbol_cusips_over_sample[symbol].add(cusip)
            if description:
                date_symbol_descriptions[(dt, symbol)].add(description)
        if cusip and symbol:
            key_counts[(dt, cusip, symbol)] += 1

    cusip_multi = [
        (dt, cusip, sorted(symbols))
        for (dt, cusip), symbols in date_cusip_symbols.items() if len(symbols) > 1
    ]
    symbol_multi = [
        (dt, symbol, sorted(cusips))
        for (dt, symbol), cusips in date_symbol_cusips.items() if len(cusips) > 1
    ]
    duplicate_keys = {k: n for k, n in key_counts.items() if n > 1}
    ambiguity_rows = []
    for dt, cusip, symbols in cusip_multi:
        ambiguity_rows.append({
            "ambiguity_type": "same_day_cusip_multiple_symbols",
            "settlement_date": dt, "cusip": cusip, "symbol": ";".join(symbols),
            "description": ";".join(sorted(date_cusip_descriptions[(dt, cusip)])),
        })
    for dt, symbol, cusips in symbol_multi:
        ambiguity_rows.append({
            "ambiguity_type": "same_day_symbol_multiple_cusips",
            "settlement_date": dt, "cusip": ";".join(cusips), "symbol": symbol,
            "description": ";".join(sorted(date_symbol_descriptions[(dt, symbol)])),
        })

    summary = {
        "records": len(records),
        "unique_settlement_dates": len(unique_dates),
        "unique_cusips": len({str(r.get("cusip") or "").strip().upper() for r in records if r.get("cusip")}),
        "unique_symbols": len({str(r.get("symbol") or "").strip().upper() for r in records if r.get("symbol")}),
        "blank_cusip_rows": blank_cusip_rows,
        "blank_symbol_rows": blank_symbol_rows,
        "invalid_nine_character_cusip_rows": invalid_cusip_rows,
        "same_day_cusip_multiple_symbol_keys": len(cusip_multi),
        "same_day_symbol_multiple_cusip_keys": len(symbol_multi),
        "cusips_with_multiple_symbols_across_sample": sum(1 for x in cusip_symbols_over_sample.values() if len(x) > 1),
        "symbols_with_multiple_cusips_across_sample": sum(1 for x in symbol_cusips_over_sample.values() if len(x) > 1),
        "duplicate_date_cusip_symbol_keys": len(duplicate_keys),
        "duplicate_rows_beyond_first": sum(n - 1 for n in duplicate_keys.values()),
        "same_day_cusip_multiple_symbol_examples": [
            {"settlement_date": dt, "cusip": cusip, "symbols": symbols}
            for dt, cusip, symbols in cusip_multi[:20]
        ],
        "same_day_symbol_multiple_cusip_examples": [
            {"settlement_date": dt, "symbol": symbol, "cusips": cusips}
            for dt, symbol, cusips in symbol_multi[:20]
        ],
    }
    return summary, ambiguity_rows


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept": "application/zip,*/*"})
    results, downloads, ambiguity_rows, errors = [], [], [], []

    for spec in SAMPLES:
        url = spec["url"]
        head_meta = {"head_status": None, "head_last_modified": None, "head_etag": None,
                     "head_content_length": None, "head_error": None}
        try:
            head = session.head(url, timeout=60, allow_redirects=True)
            head_meta.update({
                "head_status": head.status_code,
                "head_last_modified": head.headers.get("Last-Modified"),
                "head_etag": head.headers.get("ETag"),
                "head_content_length": head.headers.get("Content-Length"),
            })
        except Exception as exc:
            head_meta["head_error"] = repr(exc)

        try:
            response = session.get(url, timeout=180, allow_redirects=True)
            response.raise_for_status()
            payload = response.content
            with zipfile.ZipFile(io.BytesIO(payload)) as zf:
                names = [n for n in zf.namelist() if n.lower().endswith(".txt")]
                if not names:
                    raise RuntimeError(f"{spec['filename']}: no TXT members")
                parsed = [parse_text_member(zf.read(name), name) for name in names]
            records = [row for member in parsed for row in member["records"]]
            mapping, ambiguities = build_mapping_diagnostics(records)
            ambiguity_rows.extend([{**x, "sample": spec["key"]} for x in ambiguities])
            download = {
                "sample": spec["key"], "label": spec["label"], "url": url,
                "http_status": response.status_code, "bytes": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
                "get_date": response.headers.get("Date"),
                "get_last_modified": response.headers.get("Last-Modified"),
                "get_etag": response.headers.get("ETag"),
                "get_content_length": response.headers.get("Content-Length"),
                **head_meta,
            }
            downloads.append(download)
            member_errors = [
                {"member": m["member"], "malformed": len(m["malformed"]), "bad_fields": m["bad_fields"]}
                for m in parsed if m["malformed"] or m["bad_fields"]
            ]
            results.append({
                "sample": spec["key"], "label": spec["label"], "regime": spec["regime"],
                **mapping, "schema_member_count": len(parsed), "schema_errors": member_errors,
                "schema_status": "PASS" if not member_errors and records else "FAIL",
                "download": download,
            })
        except Exception as exc:
            errors.append({"sample": spec["key"], "label": spec["label"], "error": repr(exc)})

    summary = {
        "phase": 105,
        "source": "SEC official Fails-to-Deliver Data",
        "audit_timestamp_utc": datetime.utcnow().isoformat() + "Z",
        "samples_expected": len(SAMPLES),
        "samples_completed": len(results),
        "samples": results,
        "download_hashes_and_http_metadata": downloads,
        "same_day_ambiguity_rows": len(ambiguity_rows),
        "errors": errors,
        "release_schedule": {
            "first_half": "available at month-end",
            "second_half": "available about the 15th of the next month",
            "sec_warning": "SEC does not guarantee posting by a particular date",
            "pit_conclusion": "NOT_PASSED; schedule is a conservative convention, not an exact historical public-availability ledger",
        },
        "gates": {
            "all_sample_files_downloaded": len(results) == len(SAMPLES) and not errors,
            "all_sample_schemas_valid": len(results) == len(SAMPLES) and all(x["schema_status"] == "PASS" for x in results),
            "same_day_cusip_symbol_ambiguity_measured": len(results) == len(SAMPLES),
            "permanent_security_id_linkage": False,
            "inactive_delisted_return_linkage": False,
            "historical_publication_vintage_verified": False,
        },
        "interpretation": "CUSIP is a stronger effective-dated security key than ticker, but is not a permanent return-source identifier. FTD is an aggregate settlement balance, not a daily flow or investor identity.",
        "forward_returns_used": False, "alpha_test_authorized": False, "f80_changed": False,
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    with (OUT / "same_day_ambiguities.csv").open("w", newline="", encoding="utf-8") as f:
        fields = ["sample", "ambiguity_type", "settlement_date", "cusip", "symbol", "description"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(ambiguity_rows)
    print(json.dumps(summary, indent=2), flush=True)
    if not summary["gates"]["all_sample_files_downloaded"] or not summary["gates"]["all_sample_schemas_valid"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()

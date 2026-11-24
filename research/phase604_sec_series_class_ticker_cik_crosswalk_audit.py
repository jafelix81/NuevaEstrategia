#!/usr/bin/env python3
"""SEC registered-fund series/class ticker-to-CIK crosswalk feasibility audit.

Mapping audit only. SEC series/class snapshots are not effective-dated security
master records and do not prove historical F80 membership.
"""
from __future__ import annotations

import argparse
import ast
import csv
import gzip
import hashlib
import io
import json
import os
import random
import re
import time
import zlib
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

PHASE = 604
BASE_SOURCE = Path("Nueva_Estrategia_Fase0_Descubrimiento.py")
SEC_FILES = {
    "company_tickers_json": {
        "url": "https://www.sec.gov/files/company_tickers.json", "kind": "json",
        "snapshot_date": "current SEC ticker file; exact effective date not supplied", "required": True,
    },
    "company_tickers_exchange_json": {
        "url": "https://www.sec.gov/files/company_tickers_exchange.json", "kind": "json",
        "snapshot_date": "current SEC ticker file; exact effective date not supplied", "required": True,
    },
    "company_tickers_mf_json": {
        "url": "https://www.sec.gov/files/company_tickers_mf.json", "kind": "json",
        "snapshot_date": "current SEC mutual-fund ticker file; exact effective date not supplied", "required": True,
    },
    "series_class_2026_csv": {
        "url": "https://www.sec.gov/files/investment/data/other/investment-company-series-class-information/investment-company-series-class-2026.csv",
        "kind": "csv", "snapshot_date": "2026-06-01", "required": True,
    },
    "series_class_2025_csv": {
        "url": "https://www.sec.gov/files/investment/data/other/investment-company-series-class-information/investment-company-series-class-2025.csv",
        "kind": "csv", "snapshot_date": "2025-06-02", "required": False,
    },
    "series_class_2024_csv": {
        "url": "https://www.sec.gov/files/investment/data/other/investment-company-series-class-information/investment-company-series-class-2024.csv",
        "kind": "csv", "snapshot_date": "2024-06-05", "required": False,
    },
    "series_class_2020_csv": {
        "url": "https://www.sec.gov/files/investment/data/other/investment-company-series-class-information/investment-company-series-class-2020.csv",
        "kind": "csv", "snapshot_date": "2020-07-13", "required": False,
    },
    "series_class_2016_csv": {
        "url": "https://www.sec.gov/files/investment/data/other/investment-company-series-class-information/investment-company-series-class-2016.csv",
        "kind": "csv", "snapshot_date": "2016-09-23", "required": False,
    },
    "series_class_2010_csv": {
        "url": "https://www.sec.gov/files/investment/data/other/investment-company-series-class-information/investment-company-series-class-2010.csv",
        "kind": "csv", "snapshot_date": "2010; exact update day not stated", "required": False,
    },
}
TARGET_UNMAPPED_PHASE603 = [
    "ARKF", "ARKG", "ARKK", "ARKQ", "ARKW", "AVB", "BITO", "EA", "EQR",
    "IEFA", "IWM", "JETS", "KRE", "LPRO", "OIH", "QQQ", "ROKU", "SMH",
    "SOXX", "VEA", "VNQ", "VWO", "WBD", "WBS", "XBI", "XLB", "XLE",
    "XLF", "XLI", "XLK", "XLP", "XLRE", "XLU", "XLV", "XLY",
]
_last_request = 0.0


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_key(value: object) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value or "").lower())


def normalize_cik(value: object) -> str | None:
    digits = re.sub(r"\D", "", str(value or ""))
    return digits.zfill(10) if digits and len(digits) <= 10 else None


def normalize_ticker(value: object) -> str:
    return str(value or "").strip().upper()


def load_universe(path: Path = BASE_SOURCE) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            if any(isinstance(t, ast.Name) and t.id == "DEFAULT_UNIVERSE" for t in node.targets):
                values = sorted({normalize_ticker(x) for x in ast.literal_eval(node.value)})
                if len(values) != 335:
                    raise ValueError(f"expected_335_f80_names_got_{len(values)}")
                return values
    raise ValueError("DEFAULT_UNIVERSE_not_found")


def resolve_user_agent() -> tuple[str, str]:
    secret = os.environ.get("SEC_USER_AGENT", "").strip()
    if secret and "@" in secret and "example.com" not in secret.lower():
        return secret, "repository_secret"
    from research import phase401_form144a_full_parent_identity_census as p401
    fallback = str(getattr(p401, "SEC_UA", "")).strip()
    if not fallback or "@" not in fallback or "example.com" in fallback.lower():
        raise RuntimeError("no_valid_sec_user_agent_or_shared_contact")
    return fallback, "shared_phase401_contact_fallback"


def fetch_sec_bytes(url: str, user_agent: str, timeout: int = 90, retries: int = 5) -> tuple[bytes, int]:
    global _last_request
    last_error = None
    for attempt in range(retries):
        wait = 0.25 - (time.monotonic() - _last_request)
        if wait > 0:
            time.sleep(wait)
        _last_request = time.monotonic()
        request = Request(url, headers={
            "User-Agent": user_agent,
            "Accept-Encoding": "gzip, deflate",
            "Accept": "text/csv,application/json,text/plain,*/*",
        })
        try:
            with urlopen(request, timeout=timeout) as response:
                raw = response.read()
                encoding = str(response.headers.get("Content-Encoding", "")).lower()
                if encoding == "gzip" or raw[:2] == b"\x1f\x8b":
                    raw = gzip.decompress(raw)
                elif encoding == "deflate":
                    try:
                        raw = zlib.decompress(raw)
                    except zlib.error:
                        raw = zlib.decompress(raw, -zlib.MAX_WBITS)
                return raw, int(getattr(response, "status", 200))
        except HTTPError as exc:
            last_error = exc
            if exc.code not in (408, 429, 500, 502, 503, 504):
                raise
            retry_after = exc.headers.get("Retry-After") if exc.headers else None
            try:
                delay = float(retry_after) if retry_after else min(45, 2 ** attempt)
            except (TypeError, ValueError):
                delay = min(45, 2 ** attempt)
            time.sleep(delay + random.uniform(0.1, 0.5))
        except (URLError, TimeoutError, OSError, zlib.error) as exc:
            last_error = exc
            time.sleep(min(30, 2 ** attempt) + random.uniform(0.1, 0.5))
    raise RuntimeError(f"sec_get_failed:{type(last_error).__name__}:{url}")


def iter_json_rows(obj: object):
    if isinstance(obj, dict) and isinstance(obj.get("data"), list):
        fields = obj.get("fields") or []
        for values in obj["data"]:
            if isinstance(values, dict):
                yield values
            elif isinstance(values, (list, tuple)) and fields:
                yield {str(fields[i]): values[i] for i in range(min(len(fields), len(values)))}
    elif isinstance(obj, dict):
        for row in obj.values():
            if isinstance(row, dict):
                yield row
    elif isinstance(obj, list):
        for row in obj:
            if isinstance(row, dict):
                yield row


def field_value(row: dict, aliases: tuple[str, ...]):
    normalized = {normalize_key(k): v for k, v in row.items()}
    for alias in aliases:
        key = normalize_key(alias)
        if key in normalized:
            return normalized[key]
    return None


def parse_json_ticker_rows(raw: bytes, source: str, snapshot_date: str) -> tuple[list[dict], int]:
    obj = json.loads(raw.decode("utf-8-sig"))
    output = []
    parsed_rows = 0
    for row in iter_json_rows(obj):
        parsed_rows += 1
        cik = normalize_cik(field_value(row, ("cik", "cik_str", "fund_cik", "owner_cik")))
        ticker = normalize_ticker(field_value(row, (
            "ticker", "class_ticker", "class_contract_ticker_symbol",
            "class_contract_ticker", "symbol",
        )))
        if not cik or not ticker:
            continue
        output.append({
            "source": source, "snapshot_date": snapshot_date, "ticker": ticker, "cik": cik,
            "series_id": str(field_value(row, ("series_id", "seriesid")) or ""),
            "class_id": str(field_value(row, ("class_id", "classid", "class_contract_id")) or ""),
            "series_name": str(field_value(row, ("series_name", "seriesname", "name")) or ""),
            "class_name": str(field_value(row, ("class_name", "classname", "title")) or ""),
            "status": str(field_value(row, ("class_status", "series_status", "status")) or ""),
        })
    return output, parsed_rows


def parse_series_class_csv(raw: bytes, source: str, snapshot_date: str) -> tuple[list[dict], int, int]:
    text = raw.decode("utf-8-sig", "replace")
    try:
        dialect = csv.Sniffer().sniff(text[:10000], delimiters=",\t|")
    except csv.Error:
        dialect = csv.excel
    rows = list(csv.reader(io.StringIO(text), dialect))
    header_index = None
    header = []
    for i, row in enumerate(rows[:100]):
        keys = [normalize_key(x) for x in row]
        if "cik" in keys and ("classticker" in keys or "classcontracttickersymbol" in keys):
            header_index, header = i, keys
            break
    if header_index is None:
        raise ValueError("series_class_csv_header_with_CIK_and_Class_Ticker_not_found")
    index = {key: i for i, key in enumerate(header) if key}

    def get(row, aliases):
        for alias in aliases:
            pos = index.get(normalize_key(alias))
            if pos is not None and pos < len(row):
                return row[pos]
        return ""

    output = []
    data_rows = 0
    for row in rows[header_index + 1:]:
        if not row or not any(str(x).strip() for x in row):
            continue
        data_rows += 1
        cik = normalize_cik(get(row, ("cik",)))
        ticker = normalize_ticker(get(row, (
            "class_ticker", "class_contract_ticker_symbol", "ticker",
        )))
        if not cik or not ticker:
            continue
        output.append({
            "source": source, "snapshot_date": snapshot_date, "ticker": ticker, "cik": cik,
            "series_id": str(get(row, ("series_id",))),
            "class_id": str(get(row, ("class_id",))),
            "series_name": str(get(row, ("series_name",))),
            "class_name": str(get(row, ("class_name",))),
            "status": str(get(row, ("class_status", "series_status", "status"))),
        })
    return output, data_rows, header_index


def source_mapping(records: list[dict]) -> tuple[dict[str, set[str]], dict[str, list[dict]]]:
    mapping = defaultdict(set)
    details = defaultdict(list)
    for row in records:
        mapping[row["ticker"]].add(row["cik"])
        details[row["ticker"]].append(row)
    return dict(mapping), dict(details)


def mapping_summary(mapping: dict[str, set[str]], universe: set[str]) -> dict:
    target = {t: ciks for t, ciks in mapping.items() if t in universe}
    conflicts = {t: sorted(ciks) for t, ciks in target.items() if len(ciks) > 1}
    return {
        "tickers_mapped": len(target),
        "unique_ciks": len({cik for ciks in target.values() for cik in ciks}),
        "conflicting_tickers": conflicts,
        "unmapped_tickers": sorted(universe - set(target)),
    }


def run(output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    universe_list = load_universe()
    universe = set(universe_list)
    ua, ua_source = resolve_user_agent()
    manifest = {}
    all_records = []
    source_mappings = {}
    required_failures = []

    for source, spec in SEC_FILES.items():
        meta = {
            "url": spec["url"], "kind": spec["kind"],
            "snapshot_date": spec["snapshot_date"], "required": spec["required"],
        }
        try:
            raw, status = fetch_sec_bytes(spec["url"], ua)
            meta.update({"http_status": status, "bytes": len(raw),
                         "sha256": hashlib.sha256(raw).hexdigest()})
            if status != 200:
                raise RuntimeError(f"http_status_{status}")
            if spec["kind"] == "json":
                records, parsed_rows = parse_json_ticker_rows(raw, source, spec["snapshot_date"])
                meta.update({"parsed_source_rows": parsed_rows, "ticker_cik_rows": len(records)})
            else:
                records, data_rows, header_index = parse_series_class_csv(raw, source, spec["snapshot_date"])
                meta.update({"parsed_source_rows": data_rows, "header_line_zero_based": header_index,
                             "ticker_cik_rows": len(records)})
            target_records = [r for r in records if r["ticker"] in universe]
            meta["target_universe_rows"] = len(target_records)
            all_records.extend(target_records)
            mapping, _ = source_mapping(records)
            source_mappings[source] = mapping
            meta["target_mapping"] = mapping_summary(mapping, universe)
            meta["status"] = "PASS"
        except Exception as exc:
            meta.update({"status": "FAIL", "error": f"{type(exc).__name__}:{exc}"})
            if spec["required"]:
                required_failures.append(source)
        manifest[source] = meta

    current_sources = ("company_tickers_json", "company_tickers_exchange_json",
                       "company_tickers_mf_json", "series_class_2026_csv")
    current_union = defaultdict(set)
    for source in current_sources:
        for ticker, ciks in source_mappings.get(source, {}).items():
            if ticker in universe:
                current_union[ticker].update(ciks)
    baseline_union = defaultdict(set)
    for source in ("company_tickers_json", "company_tickers_exchange_json"):
        for ticker, ciks in source_mappings.get(source, {}).items():
            if ticker in universe:
                baseline_union[ticker].update(ciks)

    series_sources = [s for s in source_mappings if s.startswith("series_class_")]
    historical_by_ticker = defaultdict(dict)
    for source in series_sources:
        snapshot = manifest[source]["snapshot_date"]
        for ticker, ciks in source_mappings[source].items():
            if ticker in universe:
                historical_by_ticker[ticker][snapshot] = sorted(ciks)
    stability = {"same_cik_all_available_snapshots": [], "changed_or_conflicting_cik": [],
                 "one_snapshot_only": []}
    for ticker, snapshots in sorted(historical_by_ticker.items()):
        values = [tuple(v) for _, v in sorted(snapshots.items())]
        if len(values) == 1:
            stability["one_snapshot_only"].append(ticker)
        elif all(v == values[0] for v in values[1:]) and len(values[0]) == 1:
            stability["same_cik_all_available_snapshots"].append(ticker)
        else:
            stability["changed_or_conflicting_cik"].append({"ticker": ticker, "snapshots": snapshots})

    target_rows = [r for r in all_records if r["ticker"] in universe]
    target_rows.sort(key=lambda r: (r["ticker"], r["source"], r["cik"], r["series_id"], r["class_id"]))
    with (output_dir / "ticker_cik_rows.csv").open("w", newline="", encoding="utf-8") as f:
        fields = ["ticker", "cik", "source", "snapshot_date", "series_id", "class_id",
                  "series_name", "class_name", "status"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows({k: row.get(k, "") for k in fields} for row in target_rows)

    baseline_summary = mapping_summary(dict(baseline_union), universe)
    combined_summary = mapping_summary(dict(current_union), universe)
    newly_mapped = sorted((set(universe) - set(baseline_summary["unmapped_tickers"])) &
                          (set(universe) - set(combined_summary["unmapped_tickers"])))
    newly_mapped = sorted(set(newly_mapped) - set(baseline_union))
    still_unmapped = combined_summary["unmapped_tickers"]
    phase603_unmapped = set(TARGET_UNMAPPED_PHASE603)
    phase603_recovered = sorted(phase603_unmapped - set(still_unmapped))
    phase603_still_unmapped = sorted(phase603_unmapped & set(still_unmapped))

    summary = {
        "phase": PHASE, "audit": "SEC_SERIES_CLASS_TICKER_CIK_CROSSWALK",
        "audit_timestamp_utc": utc_now(), "configured_f80_tickers": len(universe),
        "phase603_unmapped_tickers_checked": len(TARGET_UNMAPPED_PHASE603),
        "phase603_unmapped_tickers_recovered": phase603_recovered,
        "phase603_unmapped_tickers_still_unmapped": phase603_still_unmapped,
        "baseline_company_ticker_sources": baseline_summary,
        "combined_current_discovery_sources": combined_summary,
        "newly_mapped_vs_company_ticker_files": newly_mapped,
        "series_class_snapshot_stability": stability,
        "source_manifest": manifest, "user_agent_source": ua_source,
        "user_agent_value_logged": False, "historical_effective_dates_certified": False,
        "historical_f80_membership_certified": False, "public_availability_certified": False,
        "signal_eligible_rows": 0, "returns_or_alpha_test_performed": False,
        "oos_bootstrap_loo_performed": False, "production_changed": False,
        "frozen_baseline": "F80_TOP20_PARTIAL50_BASELINE_C20", "options_budget_usd": 0,
        "required_source_failures": required_failures,
        "status": "PASS" if not required_failures and
                  manifest.get("series_class_2026_csv", {}).get("status") == "PASS" and
                  manifest.get("company_tickers_mf_json", {}).get("status") == "PASS" else "FAIL",
        "limitations": [
            "SEC ticker files are periodically updated discovery aids; SEC does not guarantee accuracy or scope.",
            "Series/class reports are annual snapshots, not effective-dated ticker/CIK histories.",
            "Series/class CIK identifies the investment-company registrant; series/class IDs are separate identifiers.",
            "The SEC says the series/class report is not comprehensive for all closed-end funds and unit investment trusts.",
            "Records may include not-yet-launched or ceased funds whose registrant has not updated inactive status.",
            "A ticker-to-CIK match does not prove the CIK is a particular 13D/G SUBJECT COMPANY.",
            "No exact public-dissemination time, historical F80 membership, security continuity, or return edge is established.",
        ],
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output_dir / "source_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "phase": PHASE, "status": summary["status"],
        "baseline_mapped": baseline_summary["tickers_mapped"],
        "combined_current_mapped": combined_summary["tickers_mapped"],
        "newly_mapped_vs_company_ticker_files": newly_mapped,
        "phase603_unmapped_recovered": phase603_recovered,
        "phase603_unmapped_still_unmapped": phase603_still_unmapped,
        "series_class_stable_tickers": len(stability["same_cik_all_available_snapshots"]),
        "series_class_changed_or_conflicting": len(stability["changed_or_conflicting_cik"]),
        "required_source_failures": required_failures,
        "user_agent_source": ua_source, "signal_eligible_rows": 0,
    }, indent=2))
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("phase604_output"))
    args = parser.parse_args()
    result = run(args.output)
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

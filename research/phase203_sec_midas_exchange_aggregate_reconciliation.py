#!/usr/bin/env python3
"""Phase 203: SEC MIDAS exchange-level to aggregate row reconciliation.

A deterministic ticker sample is reconciled across the official per-exchange
and aggregate quarterly archives for 2016 Q2, 2017 Q2 and 2019 Q4. This is a
data-integrity audit only: no PIT, return or alpha inference is made.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import re
import time
import zipfile
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from itertools import chain
from pathlib import Path

from research.phase198_sec_midas_archive_inventory import (
    fetch_sec_page,
    parse_inventory,
)
from research.phase199_sec_midas_disputed_quarter_content_audit import (
    download_archive,
    detect_delimiter,
    parse_date,
    quarter_bounds,
)
from research.phase202_sec_midas_per_exchange_archive_structure import (
    fetch_exchange_inventory,
)

QUARTERS = ("2016 Q2", "2017 Q2", "2019 Q4")
SAMPLE_SIZE = 250
CONTROL_TICKERS = ("BRK.A", "FTNW", "NTN", "TGC", "NAVB", "YCBD", "BTN", "DPW")
AGG_REQUIRED = {
    "date", "security", "ticker", "cancels", "littrades", "oddlots", "hidden",
    "tradesforhidden", "ordervol", "litvol", "oddlotvol", "hiddenvol",
    "tradevolforhidden", "tradesforoddlots", "tradevolforoddlots",
}
EX_REQUIRED = {
    "date", "security", "ticker", "exchange", "cancels", "trades", "littrades",
    "oddlots", "hidden", "tradesforhidden", "ordervol", "tradevol", "litvol",
    "oddlotvol", "hiddenvol", "tradevolforhidden",
}
COMMON_FIELDS = (
    "cancels", "littrades", "oddlots", "hidden", "tradesforhidden",
    "ordervol", "litvol", "oddlotvol", "hiddenvol", "tradevolforhidden",
)
AGG_FIELDS = COMMON_FIELDS + ("tradesforoddlots", "tradevolforoddlots")
EX_FIELDS = COMMON_FIELDS + ("trades", "tradevol")
COUNT_FIELDS = {
    "cancels", "littrades", "oddlots", "hidden", "tradesforhidden",
    "tradesforoddlots",
}
TOLERANCE = {field: (1e-6 if field in COUNT_FIELDS else 0.0011) for field in AGG_FIELDS}


def canonical_column(value: str) -> str:
    value = re.sub(r"\s+", "", value.strip().lower())
    return value.replace("('000)", "")


def parse_number(value: str) -> float | None:
    value = (value or "").strip()
    if value in ("", ".", "NA", "N/A", "NULL"):
        return None
    try:
        number = float(value.replace(",", ""))
    except ValueError:
        return None
    return number if math.isfinite(number) else None


def same_vector(left: tuple, right: tuple, tolerance: float = 1e-9) -> bool:
    if len(left) != len(right):
        return False
    for a, b in zip(left, right):
        if a is None or b is None:
            if a is not b:
                return False
        elif abs(a - b) > tolerance:
            return False
    return True


def deterministic_sample(tickers: set[str], size: int = SAMPLE_SIZE) -> list[str]:
    ranked = sorted(
        tickers,
        key=lambda ticker: (hashlib.sha256(ticker.encode("utf-8")).hexdigest(), ticker),
    )
    selected = ranked[:size]
    selected.extend(t for t in CONTROL_TICKERS if t in tickers and t not in selected)
    return selected


def parse_order_based_base(readme: str) -> set[str]:
    match = re.search(r"(?im)^Order-based exchanges:\s*(.+)$", readme)
    if not match:
        raise ValueError("README_order_based_exchange_line_missing")
    return {item.strip().upper() for item in match.group(1).split(",") if item.strip()}


def order_based_for_date(readme: str, base: set[str], day: date) -> set[str]:
    result = set(base)
    if re.search(r"NYSE beginning May,?\s*2017", readme, re.I) and day >= date(2017, 5, 1):
        result.add("NYSE")
    if re.search(r"NSX beginning May 21,?\s*2018", readme, re.I) and day >= date(2018, 5, 21):
        result.add("NSX")
    if re.search(r"CHX beginning November 4,?\s*2019", readme, re.I) and day >= date(2019, 11, 4):
        result.add("CHX")
    return result


def sum_present(values: list[float | None]) -> float | None:
    present = [value for value in values if value is not None]
    return sum(present) if present else None


def record_unique(store: dict, conflicts: set, duplicate_groups: set, exact_activity_duplicate_groups: set, key, vector: tuple) -> None:
    if key not in store:
        store[key] = vector
        return
    duplicate_groups.add(key)
    if same_vector(store[key], vector):
        exact_activity_duplicate_groups.add(key)
    else:
        conflicts.add(key)


def find_data_members(archive: zipfile.ZipFile, required: set[str]) -> list[zipfile.ZipInfo]:
    found = []
    for item in archive.infolist():
        if item.is_dir() or item.filename.lower().endswith(".zip"):
            continue
        with archive.open(item, "r") as stream:
            prefix = stream.read(16384)
        first_line = prefix.decode("utf-8-sig", errors="replace").splitlines()
        if not first_line:
            continue
        delimiter = detect_delimiter(first_line[0])
        try:
            header = next(csv.reader([first_line[0]], delimiter=delimiter))
        except (StopIteration, csv.Error):
            continue
        if required.issubset({canonical_column(value) for value in header}):
            found.append(item)
    return found


def read_readme(archive: zipfile.ZipFile) -> tuple[str, dict[str, object]]:
    candidates = [item for item in archive.infolist() if "readme" in item.filename.lower()]
    if len(candidates) != 1:
        raise ValueError(f"expected_one_readme_found:{len(candidates)}")
    raw = archive.read(candidates[0])
    return raw.decode("utf-8-sig", errors="replace"), {
        "member": candidates[0].filename,
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }


def parse_header_and_rows(archive: zipfile.ZipFile, item: zipfile.ZipInfo):
    raw = archive.open(item, "r")
    text = io.TextIOWrapper(raw, encoding="utf-8-sig", errors="replace", newline="")
    first = text.readline()
    if not first:
        text.close()
        raise ValueError(f"empty_csv:{item.filename}")
    delimiter = detect_delimiter(first)
    reader = csv.reader(chain([first], text), delimiter=delimiter)
    try:
        header = next(reader)
    except StopIteration:
        text.close()
        raise ValueError(f"missing_header:{item.filename}")
    return text, header, reader, delimiter


def scan_aggregate_archive(content: bytes, quarter: str, selected: set[str] | None = None):
    archive_sha = hashlib.sha256(content).hexdigest()
    ticker_set: set[str] = set()
    dates: set[str] = set()
    row_count = malformed = blank = invalid_date = blank_ticker = out_of_quarter = 0
    start, end = quarter_bounds(quarter)
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        crc_failure = archive.testzip()
        if crc_failure is not None:
            raise ValueError(f"aggregate_zip_crc_failure:{crc_failure}")
        members = find_data_members(archive, AGG_REQUIRED)
        if len(members) != 1:
            raise ValueError(f"aggregate_expected_one_data_member_found:{len(members)}")
        item = members[0]
        text, header, reader, delimiter = parse_header_and_rows(archive, item)
        idx = {canonical_column(name): i for i, name in enumerate(header)}
        records = {}
        conflicts = set()
        duplicates = set()
        exact_duplicates = set()
        for raw in reader:
            if not raw or not any(value.strip() for value in raw):
                blank += 1
                continue
            if len(raw) != len(header):
                malformed += 1
                continue
            ticker = raw[idx["ticker"]].strip().upper()
            if not ticker:
                blank_ticker += 1
                continue
            day = parse_date(raw[idx["date"]])
            if day is None:
                invalid_date += 1
                continue
            row_count += 1
            ticker_set.add(ticker)
            dates.add(day.isoformat())
            if day < start or day > end:
                out_of_quarter += 1
            if selected is None or ticker in selected:
                key = (day.isoformat(), ticker, raw[idx["security"]].strip())
                vector = tuple(parse_number(raw[idx[field]]) for field in AGG_FIELDS)
                record_unique(records, conflicts, duplicates, exact_duplicates, key, vector)
        text.close()
        member_meta = {
            "member": item.filename,
            "compressed_bytes": item.compress_size,
            "uncompressed_bytes": item.file_size,
            "crc32": f"{item.CRC:08x}",
            "header": header,
            "delimiter": "pipe" if delimiter == "|" else "comma",
        }
    return {
        "archive_sha256": archive_sha,
        "archive_bytes": len(content),
        "zip_crc_passed": True,
        "member": member_meta,
        "row_count": row_count,
        "unique_dates": len(dates),
        "min_date": min(dates) if dates else None,
        "max_date": max(dates) if dates else None,
        "unique_tickers": len(ticker_set),
        "malformed_rows": malformed,
        "blank_rows": blank,
        "blank_ticker_rows": blank_ticker,
        "invalid_date_rows": invalid_date,
        "out_of_quarter_rows": out_of_quarter,
        "ticker_set": ticker_set,
        "sample_records": records,
        "sample_conflicts": conflicts,
        "sample_duplicate_groups": duplicates,
        "sample_exact_activity_duplicate_groups": exact_duplicates,
    }


def scan_exchange_archive(content: bytes, quarter: str, selected: set[str]):
    archive_sha = hashlib.sha256(content).hexdigest()
    start, end = quarter_bounds(quarter)
    total_rows = malformed = blank = invalid_date = blank_ticker = out_of_quarter = 0
    all_dates: set[str] = set()
    all_exchanges: Counter[str] = Counter()
    monthly_members = []
    records = {}
    conflicts = set()
    duplicates = set()
    exact_duplicates = set()
    negative_by_exchange = {"hidden": Counter(), "hiddenvol": Counter()}
    order_based_readme = ""
    readme_meta = {}
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        crc_failure = archive.testzip()
        if crc_failure is not None:
            raise ValueError(f"exchange_zip_crc_failure:{crc_failure}")
        order_based_readme, readme_meta = read_readme(archive)
        base_order_based = parse_order_based_base(order_based_readme)
        members = find_data_members(archive, EX_REQUIRED)
        if len(members) != 3:
            raise ValueError(f"exchange_expected_three_monthly_csv_members_found:{len(members)}")
        for item in members:
            member_rows = member_malformed = member_blank = 0
            text, header, reader, delimiter = parse_header_and_rows(archive, item)
            idx = {canonical_column(name): i for i, name in enumerate(header)}
            for raw in reader:
                if not raw or not any(value.strip() for value in raw):
                    blank += 1
                    member_blank += 1
                    continue
                if len(raw) != len(header):
                    malformed += 1
                    member_malformed += 1
                    continue
                ticker = raw[idx["ticker"]].strip().upper()
                if not ticker:
                    blank_ticker += 1
                    continue
                day = parse_date(raw[idx["date"]])
                if day is None:
                    invalid_date += 1
                    continue
                total_rows += 1
                member_rows += 1
                all_dates.add(day.isoformat())
                if day < start or day > end:
                    out_of_quarter += 1
                exchange = raw[idx["exchange"]].strip()
                all_exchanges[exchange] += 1
                if ticker not in selected:
                    continue
                base_key = (day.isoformat(), ticker, raw[idx["security"]].strip())
                key = base_key + (exchange.upper(),)
                vector = tuple(parse_number(raw[idx[field]]) for field in EX_FIELDS)
                record_unique(records, conflicts, duplicates, exact_duplicates, key, vector)
                for field in ("hidden", "hiddenvol"):
                    value = vector[EX_FIELDS.index(field)]
                    if value is not None and value < 0:
                        negative_by_exchange[field][exchange] += 1
            text.close()
            monthly_members.append({
                "member": item.filename,
                "compressed_bytes": item.compress_size,
                "uncompressed_bytes": item.file_size,
                "crc32": f"{item.CRC:08x}",
                "header": header,
                "delimiter": "pipe" if delimiter == "|" else "comma",
                "valid_rows": member_rows,
                "blank_rows": member_blank,
                "malformed_rows": member_malformed,
            })
    return {
        "archive_sha256": archive_sha,
        "archive_bytes": len(content),
        "zip_crc_passed": True,
        "readme": readme_meta,
        "order_based_base": sorted(base_order_based),
        "order_based_rule_text": [
            line.strip() for line in order_based_readme.splitlines()
            if re.search(r"order-based exchanges|NYSE beginning|NSX beginning|CHX beginning", line, re.I)
        ],
        "monthly_members": monthly_members,
        "row_count": total_rows,
        "unique_dates": len(all_dates),
        "min_date": min(all_dates) if all_dates else None,
        "max_date": max(all_dates) if all_dates else None,
        "unique_exchanges": sorted(all_exchanges),
        "rows_by_exchange": dict(sorted(all_exchanges.items())),
        "malformed_rows": malformed,
        "blank_rows": blank,
        "blank_ticker_rows": blank_ticker,
        "invalid_date_rows": invalid_date,
        "out_of_quarter_rows": out_of_quarter,
        "sample_records": records,
        "sample_conflicts": conflicts,
        "sample_duplicate_groups": duplicates,
        "sample_exact_activity_duplicate_groups": exact_duplicates,
        "negative_by_exchange": {
            field: dict(sorted(counts.items())) for field, counts in negative_by_exchange.items()
        },
        "order_based_readme_text": order_based_readme,
    }


def aggregate_exchange_records(exchange_result: dict[str, object]):
    totals: dict[tuple, dict[str, float | None]] = {}
    conflict_base = {key[:3] for key in exchange_result["sample_conflicts"]}
    for key, vector in exchange_result["sample_records"].items():
        if key[:3] in conflict_base:
            continue
        day = date.fromisoformat(key[0])
        exchange = key[3]
        values = dict(zip(EX_FIELDS, vector))
        target = totals.setdefault(key[:3], {field: None for field in AGG_FIELDS})
        for field in COMMON_FIELDS:
            value = values[field]
            if value is not None:
                target[field] = (target[field] or 0.0) + value
        if exchange in order_based_for_date(
            exchange_result["order_based_readme_text"],
            set(exchange_result["order_based_base"]),
            day,
        ):
            for target_field, source_field in (
                ("tradesforoddlots", "trades"),
                ("tradevolforoddlots", "tradevol"),
            ):
                value = values[source_field]
                if value is not None:
                    target[target_field] = (target[target_field] or 0.0) + value
    return totals, conflict_base


def compare_sample(aggregate_result: dict[str, object], exchange_result: dict[str, object]):
    aggregate = aggregate_result["sample_records"]
    exchange_totals, exchange_conflicts = aggregate_exchange_records(exchange_result)
    aggregate_conflicts = aggregate_result["sample_conflicts"]
    valid_aggregate = set(aggregate) - aggregate_conflicts
    valid_exchange = set(exchange_totals) - exchange_conflicts
    common = valid_aggregate & valid_exchange
    metrics = {}
    for field in AGG_FIELDS:
        exact = within = mismatch = one_sided_missing = both_missing = 0
        max_diff = 0.0
        examples = []
        for key in sorted(common):
            a = aggregate[key][AGG_FIELDS.index(field)]
            b = exchange_totals[key][field]
            if a is None and b is None:
                both_missing += 1
                continue
            if a is None or b is None:
                one_sided_missing += 1
                mismatch += 1
                if len(examples) < 8:
                    examples.append({"date": key[0], "ticker": key[1], "security": key[2], "aggregate": a, "exchange_sum": b})
                continue
            diff = abs(a - b)
            max_diff = max(max_diff, diff)
            if diff <= 1e-9:
                exact += 1
                within += 1
            elif diff <= TOLERANCE[field]:
                within += 1
            else:
                mismatch += 1
                if len(examples) < 8:
                    examples.append({"date": key[0], "ticker": key[1], "security": key[2], "aggregate": a, "exchange_sum": b, "absolute_difference": diff})
        metrics[field] = {
            "keys_compared": len(common),
            "exact_matches": exact,
            "within_tolerance_matches": within,
            "mismatch_count": mismatch,
            "one_sided_missing_count": one_sided_missing,
            "both_missing_count": both_missing,
            "tolerance": TOLERANCE[field],
            "max_absolute_difference": max_diff,
            "mismatch_examples": examples,
        }
    coverage = {
        "aggregate_sample_keys": len(valid_aggregate),
        "exchange_sample_keys": len(valid_exchange),
        "common_keys": len(common),
        "aggregate_only_keys": len(valid_aggregate - valid_exchange),
        "exchange_only_keys": len(valid_exchange - valid_aggregate),
        "aggregate_conflict_keys_quarantined": len(aggregate_conflicts),
        "exchange_base_keys_quarantined": len(exchange_conflicts),
        "aggregate_activity_duplicate_groups": len(aggregate_result["sample_duplicate_groups"]),
        "exchange_activity_duplicate_groups": len(exchange_result["sample_duplicate_groups"]),
        "aggregate_activity_conflict_groups": len(aggregate_conflicts),
        "exchange_activity_conflict_groups": len(exchange_result["sample_conflicts"]),
    }
    negative_attribution = {
        "hidden": {"aggregate_negative_keys": 0, "negative_exchange_contributions": Counter(), "only_nyse_amex": 0, "examples": []},
        "hiddenvol": {"aggregate_negative_keys": 0, "negative_exchange_contributions": Counter(), "only_nyse_amex": 0, "examples": []},
    }
    by_base = defaultdict(dict)
    for key, vector in exchange_result["sample_records"].items():
        if key[:3] not in exchange_conflicts:
            by_base[key[:3]][key[3]] = dict(zip(EX_FIELDS, vector))
    for key in sorted(common):
        agg_values = dict(zip(AGG_FIELDS, aggregate[key]))
        for field in ("hidden", "hiddenvol"):
            aggregate_value = agg_values[field]
            if aggregate_value is None or aggregate_value >= 0:
                continue
            negative_attribution[field]["aggregate_negative_keys"] += 1
            contributors = []
            for exchange, values in by_base.get(key, {}).items():
                value = values.get(field)
                if value is not None and value < 0:
                    contributors.append((exchange, value))
                    negative_attribution[field]["negative_exchange_contributions"][exchange] += 1
            if contributors and all(name in {"NYSE", "AMEX"} for name, _ in contributors):
                negative_attribution[field]["only_nyse_amex"] += 1
            if len(negative_attribution[field]["examples"]) < 12:
                negative_attribution[field]["examples"].append({
                    "date": key[0], "ticker": key[1], "aggregate_value": aggregate_value,
                    "negative_exchange_contributions": [
                        {"exchange": name, "value": value} for name, value in contributors
                    ],
                })
    for field in negative_attribution:
        negative_attribution[field]["negative_exchange_contributions"] = dict(
            sorted(negative_attribution[field]["negative_exchange_contributions"].items())
        )
    all_reconciled = all(
        item["mismatch_count"] == 0 and item["one_sided_missing_count"] == 0
        for item in metrics.values()
    )
    return {
        "coverage": coverage,
        "field_metrics": metrics,
        "all_shared_additive_fields_reconcile_within_tolerance": all_reconciled,
        "negative_attribution": negative_attribution,
    }


def run_audit() -> dict[str, object]:
    aggregate_inventory = parse_inventory(fetch_sec_page())
    exchange_inventory = fetch_exchange_inventory()
    missing = [
        quarter for quarter in QUARTERS
        if quarter not in aggregate_inventory["quarter_urls"]
        or quarter not in exchange_inventory["quarter_urls"]
    ]
    if missing:
        raise RuntimeError(f"sample_quarters_missing_from_one_or_both_SEC_indexes:{missing}")
    if aggregate_inventory["quarter_count"] != 58 or exchange_inventory["quarter_count"] != 58:
        raise RuntimeError("unexpected_SEC_quarter_inventory_count")
    quarter_results = []
    for index, quarter in enumerate(QUARTERS):
        if index:
            time.sleep(1.0)
        aggregate_bytes, aggregate_http = download_archive(aggregate_inventory["quarter_urls"][quarter])
        aggregate_scan = scan_aggregate_archive(aggregate_bytes, quarter, selected=None)
        sample_tickers = deterministic_sample(aggregate_scan["ticker_set"])
        aggregate_scan = scan_aggregate_archive(aggregate_bytes, quarter, selected=set(sample_tickers))
        exchange_bytes, exchange_http = download_archive(exchange_inventory["quarter_urls"][quarter])
        exchange_scan = scan_exchange_archive(exchange_bytes, quarter, set(sample_tickers))
        comparison = compare_sample(aggregate_scan, exchange_scan)
        quarter_results.append({
            "quarter": quarter,
            "sample_rule": {
                "method": "SHA-256 lexical ranking of aggregate-file ticker symbols",
                "base_sample_size": SAMPLE_SIZE,
                "control_tickers_added_if_present": list(CONTROL_TICKERS),
                "selected_ticker_count": len(sample_tickers),
                "selected_ticker_sha256": hashlib.sha256(
                    "\n".join(sorted(sample_tickers)).encode("utf-8")
                ).hexdigest(),
                "selected_ticker_examples": sample_tickers[:12],
            },
            "aggregate": {
                key: value for key, value in aggregate_scan.items()
                if key not in {"ticker_set", "sample_records", "sample_conflicts", "sample_duplicate_groups", "sample_exact_activity_duplicate_groups"}
            },
            "aggregate_http": aggregate_http,
            "exchange": {
                key: value for key, value in exchange_scan.items()
                if key not in {"sample_records", "sample_conflicts", "sample_duplicate_groups", "sample_exact_activity_duplicate_groups", "order_based_readme_text"}
            },
            "exchange_http": exchange_http,
            "comparison": comparison,
        })
    all_reconciled = all(
        item["comparison"]["all_shared_additive_fields_reconcile_within_tolerance"]
        for item in quarter_results
    )
    return {
        "phase": 203,
        "status": "THREE_QUARTER_EXCHANGE_TO_AGGREGATE_SAMPLE_RECONCILIATION_COMPLETED",
        "audit_as_of_utc": datetime.now(timezone.utc).isoformat(),
        "aggregate_archive_quarter_count": aggregate_inventory["quarter_count"],
        "exchange_archive_quarter_count": exchange_inventory["quarter_count"],
        "quarters_audited": list(QUARTERS),
        "quarter_results": quarter_results,
        "interpretation": {
            "full_zip_crc_validated_for_all_six_archives": True,
            "monthly_exchange_csvs_fully_parsed": True,
            "deterministic_ticker_sample_used": True,
            "sample_size_is_not_a_universe_coverage_estimate": True,
            "exchange_to_aggregate_reconciliation_performed": True,
            "all_sampled_shared_additive_fields_reconcile": all_reconciled,
            "first_publication_time_verified": False,
            "strict_pit_admitted": False,
            "historical_permanent_security_identity_admitted": False,
            "off_exchange_flow_measure": False,
            "participant_identity_available": False,
            "alpha_test_authorized": False,
            "holdout_used": False,
            "production_changed": False,
            "data_purchase": False,
            "vendor_contact": False,
            "f80_frozen": True,
        },
        "decision": (
            "This is a deterministic sample-level data-integrity audit, not a complete universe "
            "reconciliation. The per-exchange archive is monthly CSV data with an Exchange column. "
            "Only sampled tickers are reconciled; publication-time PIT, permanent security identity, "
            "off-exchange flow, participant identity and predictive value remain unestablished."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="phase203_output")
    args = parser.parse_args()
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    result = run_audit()
    target = output / "phase203_sec_midas_exchange_aggregate_reconciliation.json"
    target.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

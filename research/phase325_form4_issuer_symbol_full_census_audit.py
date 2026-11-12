#!/usr/bin/env python3
"""Phase 325: full-census SEC Form 4/4-A as-filed issuer-symbol quality audit.

Input is the immutable Phase 321 artifact. Issuer CIK remains the primary issuer
key; ISSUERTRADINGSYMBOL is only an as-filed issuer label. This audit does not
map transactions to a security/share class and is not an alpha test.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import zipfile
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

PHASE = 325
SOURCE_RUN_ID = 43177940904
SOURCE_ARTIFACT_ID = 13925636412
SOURCE_ARTIFACT_SHA256 = "e45cab68d1ebe15248cc76bad70b015c8f0bd2052689c0690478bbca4526965c"
EXPECTED_ROWS = 317267
EXPECTED_QUARTERS = {
    "2006Q1": 71679, "2012Q1": 63678, "2023Q1": 63844,
    "2023Q2": 51791, "2025Q3": 32127, "2026Q3": 34148,
}
PLACEHOLDERS = {"", "NONE", "(NONE)", "[NONE]", "NO SYMBOL", "N/A", "NA", "NULL", "NAN", "NONE]"}
SINGLE = re.compile(r"^[A-Z0-9][A-Z0-9.-]{0,9}$")
EXCHANGE = re.compile(r"^([A-Z0-9.-]{1,8}):\s*([A-Z0-9.-]{1,10})$")


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def classify_symbol(raw: str | None) -> tuple[str, str | None]:
    value = (raw or "").strip().upper()
    if value in PLACEHOLDERS:
        return "MISSING_OR_PLACEHOLDER", None
    match = EXCHANGE.fullmatch(value)
    if match:
        return "EXCHANGE_PREFIXED_SINGLE", match.group(2)
    if SINGLE.fullmatch(value):
        return "SINGLE_TOKEN", value
    if any(char in value for char in (",", ";", "/", " ", "\t")):
        return "MULTI_OR_FREEFORM", None
    return "OTHER_NONCANONICAL", None


def same_day_symbol_collision_rows(records: list[dict]) -> list[dict]:
    """Return issuer-CIK pairs sharing an exact as-filed symbol on an exact filing date.

    This is a collision diagnostic, not proof that two securities were simultaneously
    listed or economically identical. It is deliberately stricter than date-range overlap.
    """
    by_symbol_cik = defaultdict(lambda: {
        "issuer_name": "",
        "filing_dates": set(),
        "quarters": set(),
        "accessions": 0,
    })
    for row in records:
        raw = (row.get("ticker_as_filed") or "").strip().upper()
        _, candidate = classify_symbol(raw)
        if not candidate:
            continue
        item = by_symbol_cik[(candidate, row["issuer_cik"])]
        item["issuer_name"] = row.get("issuer_name", "") or item["issuer_name"]
        item["filing_dates"].add(row["filing_date"])
        item["quarters"].add(row["quarter"])
        item["accessions"] += 1

    by_symbol = defaultdict(dict)
    for (symbol, cik), item in by_symbol_cik.items():
        by_symbol[symbol][cik] = item

    collisions = []
    for symbol, issuers in sorted(by_symbol.items()):
        for (cik_a, a), (cik_b, b) in combinations(sorted(issuers.items()), 2):
            shared_dates = sorted(a["filing_dates"] & b["filing_dates"])
            if not shared_dates:
                continue
            collisions.append({
                "ticker_candidate": symbol,
                "issuer_cik_a": cik_a,
                "issuer_name_a": a["issuer_name"],
                "issuer_cik_b": cik_b,
                "issuer_name_b": b["issuer_name"],
                "shared_filing_dates": ";".join(shared_dates),
                "shared_filing_date_count": len(shared_dates),
                "issuer_a_min_filing_date": min(a["filing_dates"]),
                "issuer_a_max_filing_date": max(a["filing_dates"]),
                "issuer_b_min_filing_date": min(b["filing_dates"]),
                "issuer_b_max_filing_date": max(b["filing_dates"]),
                "issuer_a_quarters": ";".join(sorted(a["quarters"])),
                "issuer_b_quarters": ";".join(sorted(b["quarters"])),
                "issuer_a_accessions": a["accessions"],
                "issuer_b_accessions": b["accessions"],
            })
    return collisions


def _period_summary(period: str, records: list[dict]) -> dict:
    classes = Counter()
    ciks = set()
    raw_by_cik = defaultdict(set)
    candidates_by_cik = defaultdict(set)
    candidate_to_ciks = defaultdict(set)
    candidate_cik_dates = defaultdict(lambda: defaultdict(list))
    for row in records:
        cik = row["issuer_cik"]
        ciks.add(cik)
        raw = (row.get("ticker_as_filed") or "").strip().upper()
        cls, candidate = classify_symbol(raw)
        classes[cls] += 1
        if raw:
            raw_by_cik[cik].add(raw)
        if candidate:
            candidates_by_cik[cik].add(candidate)
            candidate_to_ciks[candidate].add(cik)
            candidate_cik_dates[candidate][cik].append(row["filing_date"])
    canonical = classes["SINGLE_TOKEN"] + classes["EXCHANGE_PREFIXED_SINGLE"]
    raw_ciks = {k: v for k, v in raw_by_cik.items() if v}
    candidate_ciks = {k: v for k, v in candidates_by_cik.items() if v}
    collisions = {k: v for k, v in candidate_to_ciks.items() if len(v) > 1}
    overlapping_pairs = 0
    for _, by_cik in candidate_cik_dates.items():
        if len(by_cik) < 2:
            continue
        ciks_for_symbol = sorted(by_cik)
        ranges = {cik: (min(dates), max(dates)) for cik, dates in by_cik.items()}
        for i, cik_a in enumerate(ciks_for_symbol):
            for cik_b in ciks_for_symbol[i + 1:]:
                a0, a1 = ranges[cik_a]
                b0, b1 = ranges[cik_b]
                if max(a0, b0) <= min(a1, b1):
                    overlapping_pairs += 1
    n = len(records)
    return {
        "quarter": period,
        "accessions": n,
        "unique_issuer_ciks": len(ciks),
        "symbol_class_counts": dict(sorted(classes.items())),
        "canonical_symbol_rows": canonical,
        "canonical_symbol_coverage_pct": round(100 * canonical / n, 4) if n else 0,
        "issuer_ciks_with_one_raw_symbol_value": sum(len(v) == 1 for v in raw_ciks.values()),
        "issuer_ciks_with_multiple_raw_symbol_values": sum(len(v) > 1 for v in raw_ciks.values()),
        "issuer_ciks_with_one_canonical_candidate": sum(len(v) == 1 for v in candidate_ciks.values()),
        "issuer_ciks_with_multiple_canonical_candidates": sum(len(v) > 1 for v in candidate_ciks.values()),
        "issuer_ciks_without_canonical_candidate": len(ciks - set(candidate_ciks)),
        "issuer_ciks_with_no_nonblank_symbol_value": len(ciks - set(raw_ciks)),
        "unique_canonical_symbol_candidates": len(candidate_to_ciks),
        "ticker_candidates_reused_across_ciks": len(collisions),
        "max_ciks_per_ticker_candidate": max((len(v) for v in candidate_to_ciks.values()), default=0),
        "multi_cik_candidate_symbol_groups_with_overlapping_filing_date_ranges": overlapping_pairs,
    }


def summarize_records(records: list[dict]) -> dict:
    by_period = defaultdict(list)
    all_ciks = set()
    raw_by_cik = defaultdict(set)
    candidates_by_cik = defaultdict(set)
    candidate_to_ciks = defaultdict(set)
    class_totals = Counter()
    for row in records:
        by_period[row["quarter"]].append(row)
        cik = row["issuer_cik"]
        all_ciks.add(cik)
        raw = (row.get("ticker_as_filed") or "").strip().upper()
        cls, candidate = classify_symbol(raw)
        class_totals[cls] += 1
        if raw:
            raw_by_cik[cik].add(raw)
        if candidate:
            candidates_by_cik[cik].add(candidate)
            candidate_to_ciks[candidate].add(cik)
    period_summaries = [_period_summary(q, by_period[q]) for q in sorted(by_period)]
    canonical = class_totals["SINGLE_TOKEN"] + class_totals["EXCHANGE_PREFIXED_SINGLE"]
    raw_ciks = {k: v for k, v in raw_by_cik.items() if v}
    candidate_ciks = {k: v for k, v in candidates_by_cik.items() if v}
    collisions = {k: v for k, v in candidate_to_ciks.items() if len(v) > 1}
    exact_collisions = same_day_symbol_collision_rows(records)
    return {
        "total_accessions": len(records),
        "unique_issuer_ciks": len(all_ciks),
        "symbol_class_counts": dict(sorted(class_totals.items())),
        "canonical_symbol_rows": canonical,
        "canonical_symbol_coverage_pct": round(100 * canonical / len(records), 4) if records else 0,
        "issuer_ciks_with_multiple_raw_symbol_values_across_sampled_quarters": sum(len(v) > 1 for v in raw_ciks.values()),
        "issuer_ciks_with_multiple_canonical_candidates_across_sampled_quarters": sum(len(v) > 1 for v in candidate_ciks.values()),
        "issuer_ciks_without_canonical_candidate_across_sampled_quarters": len(all_ciks - set(candidate_ciks)),
        "unique_canonical_symbol_candidates_across_sampled_quarters": len(candidate_to_ciks),
        "ticker_candidates_reused_across_ciks_across_sampled_quarters": len(collisions),
        "max_ciks_per_ticker_candidate_across_sampled_quarters": max((len(v) for v in candidate_to_ciks.values()), default=0),
        "same_day_symbol_collision_pairs_across_sampled_quarters": len(exact_collisions),
        "ticker_candidates_with_same_day_multiple_issuer_ciks": len({r["ticker_candidate"] for r in exact_collisions}),
        "same_day_symbol_collision_shared_dates": sum(r["shared_filing_date_count"] for r in exact_collisions),
        "periods": period_summaries,
        "same_day_symbol_collisions": exact_collisions,
    }


def audit(input_zip: Path) -> dict:
    raw = input_zip.read_bytes()
    digest = sha256(raw)
    if digest != SOURCE_ARTIFACT_SHA256:
        raise ValueError(f"Phase 321 artifact SHA-256 mismatch: {digest}")
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        names = [n for n in archive.namelist() if n.endswith("phase321_bulk_daily_index_census.csv")]
        if len(names) != 1:
            raise ValueError("expected one Phase 321 full census CSV")
        reader = csv.DictReader(io.StringIO(archive.read(names[0]).decode("utf-8-sig")))
        required = {"quarter", "accession", "form_type", "filing_date", "issuer_cik", "ticker_as_filed"}
        if not required.issubset(set(reader.fieldnames or [])):
            raise ValueError("Phase 321 census schema mismatch")
        records = []
        seen = set()
        for row in reader:
            if row["form_type"].strip().upper() not in {"4", "4/A"}:
                raise ValueError("unexpected form in Phase 321 census")
            if not re.fullmatch(r"\d{1,10}", row["issuer_cik"].strip()):
                raise ValueError("invalid issuer CIK")
            if not re.fullmatch(r"\d{10}-\d{2}-\d{6}", row["accession"].strip()):
                raise ValueError("invalid accession")
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", row["filing_date"].strip()):
                raise ValueError("invalid filing date")
            key = row["accession"].strip()
            if key in seen:
                raise ValueError("duplicate accession in Phase 321 census")
            seen.add(key)
            records.append({
                "quarter": row["quarter"].strip(),
                "accession": key,
                "form_type": row["form_type"].strip().upper(),
                "filing_date": row["filing_date"].strip(),
                "issuer_cik": row["issuer_cik"].strip(),
                "issuer_name": row.get("issuer_name", ""),
                "ticker_as_filed": row["ticker_as_filed"],
            })
    if len(records) != EXPECTED_ROWS:
        raise ValueError("full-census row count mismatch")
    observed_quarters = Counter(row["quarter"] for row in records)
    if dict(observed_quarters) != EXPECTED_QUARTERS:
        raise ValueError("quarter population mismatch")
    summary = summarize_records(records)
    return {
        "phase": PHASE,
        "status": "COMPLETED_SIX_QUARTER_AS_FILED_ISSUER_SYMBOL_QUALITY_AUDIT",
        "source": {
            "provider": "U.S. Securities and Exchange Commission",
            "run_id": SOURCE_RUN_ID,
            "artifact_id": SOURCE_ARTIFACT_ID,
            "artifact_name": "phase321-sec-bulk-daily-index-full-census",
            "artifact_sha256": digest,
            "input_csv": names[0],
            "input_accessions": EXPECTED_ROWS,
            "quarters": list(EXPECTED_QUARTERS),
        },
        "summary": summary,
        "interpretation": {
            "issuer_cik_is_primary_issuer_key": True,
            "issuer_trading_symbol_is_security_key": False,
            "canonical_symbol_is_not_proof_of_share_class": True,
            "same_quarter_symbol_reuse_is_not_proof_of_simultaneous_listings": True,
            "same_day_symbol_collision_is_diagnostic_not_security_identity": True,
            "ticker_collisions_across_ciks_may_include_temporal_reuse": True,
            "strict_pit_security_master_admitted": False,
            "alpha_test_authorized": False,
        },
        "controls": {
            "f80_frozen": True,
            "production_changed": False,
            "universe_changed": False,
            "capital_changed": False,
            "parameters_changed": False,
            "return_test_run": False,
            "alpha_test_run": False,
            "bootstrap_loo_run": False,
            "chronological_oos_run": False,
            "holdout_used": False,
            "vendor_contacted": False,
            "data_purchased": False,
            "raw_sec_bytes_uploaded": False,
            "email_sent": False,
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-zip", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--output-collision-csv", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.input_zip)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with args.output_csv.open("w", newline="", encoding="utf-8") as handle:
        fields = list(result["summary"]["periods"][0].keys())
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(result["summary"]["periods"])
    with args.output_collision_csv.open("w", newline="", encoding="utf-8") as handle:
        rows = result["summary"]["same_day_symbol_collisions"]
        fields = list(rows[0].keys()) if rows else [
            "ticker_candidate", "issuer_cik_a", "issuer_name_a", "issuer_cik_b",
            "issuer_name_b", "shared_filing_dates", "shared_filing_date_count",
            "issuer_a_min_filing_date", "issuer_a_max_filing_date",
            "issuer_b_min_filing_date", "issuer_b_max_filing_date",
            "issuer_a_quarters", "issuer_b_quarters", "issuer_a_accessions", "issuer_b_accessions"
        ]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps({"phase": result["phase"], "status": result["status"], "summary": {
        k: v for k, v in result["summary"].items() if k != "same_day_symbol_collisions"
    }}, sort_keys=True))


if __name__ == "__main__":
    main()

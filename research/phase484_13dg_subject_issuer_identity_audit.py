#!/usr/bin/env python3
"""Fail-closed identity audit for the Phase 28D/35 SEC Schedule 13D/G panel.

An accession prefix identifies the filing CIK, not automatically the subject
issuer. The artifact's stored issuer_cik is not accepted as a verified subject
issuer CIK unless its provenance is independently established.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path
from typing import Iterable, Mapping

ACCESSION_RE = re.compile(r"^(\d{10})-\d{2}-\d{6}$")
REVIEW_TICKERS = {"BLK", "STT", "MS", "JPM", "GS", "BAC", "BEN", "TFC", "WFC"}


def normalize_cik(value: object) -> str | None:
    raw = "" if value is None else str(value).strip()
    if not raw or not raw.isdigit() or len(raw) > 10:
        return None
    return raw.zfill(10)


def accession_filer_cik(accession: object) -> str | None:
    raw = "" if accession is None else str(accession).strip()
    match = ACCESSION_RE.fullmatch(raw)
    return match.group(1) if match else None


def classify_identity_row(row: Mapping[str, object]) -> dict:
    accession = str(row.get("accession") or "").strip()
    filer_cik = accession_filer_cik(accession)
    stored_cik = normalize_cik(row.get("issuer_cik"))
    ticker = str(row.get("ticker") or "").strip().upper()

    if filer_cik is None:
        status = "INVALID_OR_MISSING_ACCESSION"
    elif stored_cik is None:
        status = "MISSING_STORED_CIK"
    elif filer_cik == stored_cik:
        status = "FILER_CIK_COLLISION_REVIEW"
    else:
        status = "SUBJECT_IDENTITY_UNVERIFIED"

    return {
        "accession_filer_cik": filer_cik,
        "stored_issuer_cik": stored_cik,
        "stored_ticker": ticker or None,
        "identity_status": status,
        "subject_issuer_identity_verified": False,
        "signal_eligible": False,
    }


def summarize_rows(rows: Iterable[Mapping[str, object]]) -> dict:
    total = 0
    filer_ciks = set()
    stored_ciks = set()
    accessions = []
    missing_accessions = 0
    invalid_accessions = 0
    missing_stored_ciks = 0
    collision_count = 0
    ticker_counts = Counter()
    review_cohort_rows = 0
    review_cohort_collisions = 0
    reporting_person_present = 0
    reporting_person_type_present = 0
    statuses = Counter()

    for row in rows:
        total += 1
        result = classify_identity_row(row)
        status = result["identity_status"]
        statuses[status] += 1
        filer = result["accession_filer_cik"]
        stored = result["stored_issuer_cik"]
        ticker = result["stored_ticker"]

        if filer:
            filer_ciks.add(filer)
            accessions.append(str(row.get("accession") or "").strip())
        else:
            if str(row.get("accession") or "").strip():
                invalid_accessions += 1
            else:
                missing_accessions += 1
        if stored:
            stored_ciks.add(stored)
        else:
            missing_stored_ciks += 1

        if status == "FILER_CIK_COLLISION_REVIEW":
            collision_count += 1
        if ticker:
            ticker_counts[ticker] += 1
            if ticker in REVIEW_TICKERS:
                review_cohort_rows += 1
                if status == "FILER_CIK_COLLISION_REVIEW":
                    review_cohort_collisions += 1

        if str(row.get("reporting_person") or "").strip():
            reporting_person_present += 1
        if str(row.get("reporting_person_type") or "").strip():
            reporting_person_type_present += 1

    unique_accessions = len(set(accessions))
    duplicate_accession_rows = len(accessions) - unique_accessions
    return {
        "rows": total,
        "unique_accessions": unique_accessions,
        "duplicate_accession_rows": duplicate_accession_rows,
        "missing_accession_rows": missing_accessions,
        "invalid_accession_rows": invalid_accessions,
        "missing_stored_cik_rows": missing_stored_ciks,
        "unique_accession_filer_ciks": len(filer_ciks),
        "unique_stored_ciks": len(stored_ciks),
        "filer_cik_equals_stored_issuer_cik_rows": collision_count,
        "filer_cik_equals_stored_issuer_cik_pct": round(100 * collision_count / total, 2) if total else 0.0,
        "review_ticker_cohort": sorted(REVIEW_TICKERS),
        "review_ticker_cohort_rows": review_cohort_rows,
        "review_ticker_cohort_rows_pct": round(100 * review_cohort_rows / total, 2) if total else 0.0,
        "review_ticker_cohort_filer_cik_collisions": review_cohort_collisions,
        "review_ticker_cohort_collision_pct_of_all_collisions": round(100 * review_cohort_collisions / collision_count, 2) if collision_count else 0.0,
        "top_stored_tickers": dict(ticker_counts.most_common(20)),
        "reporting_person_present_rows": reporting_person_present,
        "reporting_person_present_pct": round(100 * reporting_person_present / total, 2) if total else 0.0,
        "reporting_person_type_present_rows": reporting_person_type_present,
        "reporting_person_type_present_pct": round(100 * reporting_person_type_present / total, 2) if total else 0.0,
        "identity_status_counts": dict(sorted(statuses.items())),
        "subject_issuer_identity_verified_rows": 0,
        "signal_eligible": False,
        "forward_returns_used": False,
        "identity_rule": "accession prefix is filing CIK; stored issuer_cik is not accepted as subject issuer CIK without independent subject-issuer evidence",
    }


def audit_csv(input_path: str | Path) -> dict:
    with open(input_path, "r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"ticker", "issuer_cik", "accession", "reporting_person", "reporting_person_type"}
        missing = required.difference(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Missing required columns: {sorted(missing)}")
        rows = list(reader)
    if not rows:
        raise ValueError("Input CSV is empty")
    return summarize_rows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Existing Phase 28D/35 events CSV")
    parser.add_argument("--output", required=True, help="Aggregate identity-audit JSON")
    args = parser.parse_args()
    result = audit_csv(args.input)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

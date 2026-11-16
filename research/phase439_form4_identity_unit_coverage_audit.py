#!/usr/bin/env python3
"""Recount Phase 346 Form 4 legacy-identity evidence at independent units.

This is a denominator audit, not a new identity classifier or alpha test.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Iterable

EXPECTED_CSV_SHA256 = "418c66f70c5ad67e065f59de312a961a0061dae79441ef116c1173424aedeb0b"
ARTIFACT_ID = 13985120745
ARTIFACT_SHA256 = "b526112713cc4942db3c4a9050000e2da4190a17c1fe1f9cc6ded962693b6e9c"
MEMBER = "phase346_output/phase346_candidate_evidence.csv"


def as_bool(value: object) -> bool | None:
    s = str(value or "").strip().lower()
    if s in {"true", "1", "yes", "y"}:
        return True
    if s in {"false", "0", "no", "n"}:
        return False
    return None


def load_rows(path: Path) -> tuple[list[dict[str, str]], dict[str, str]]:
    raw = path.read_bytes()
    source_meta = {"input_file": path.name, "input_sha256": hashlib.sha256(raw).hexdigest()}
    if path.suffix.lower() == ".zip":
        if source_meta["input_sha256"] != ARTIFACT_SHA256:
            raise ValueError("Phase 346 artifact SHA-256 mismatch")
        with zipfile.ZipFile(io.BytesIO(raw)) as zf:
            csv_bytes = zf.read(MEMBER)
    else:
        csv_bytes = raw
    csv_sha = hashlib.sha256(csv_bytes).hexdigest()
    if csv_sha != EXPECTED_CSV_SHA256:
        raise ValueError("Phase 346 candidate CSV SHA-256 mismatch")
    source_meta["candidate_csv_sha256"] = csv_sha
    rows = list(csv.DictReader(io.StringIO(csv_bytes.decode("utf-8-sig"))))
    return rows, source_meta


def summarize(rows: Iterable[dict[str, str]], source_meta: dict[str, str] | None = None) -> dict:
    all_rows = list(rows)
    pit_rows = [r for r in all_rows if as_bool(r.get("pit_eligible_at_transaction")) is True]
    matched_rows = [r for r in pit_rows if as_bool(r.get("ticker_exact_match")) is True]

    def issuer_key(r: dict[str, str]) -> str:
        return str(r.get("issuer_cik", "")).strip().lstrip("0")

    def accession_key(r: dict[str, str]) -> tuple[str, str]:
        return issuer_key(r), str(r.get("form4_accession", "")).strip()

    def filing_unit_key(r: dict[str, str]) -> tuple[str, str]:
        return issuer_key(r), str(r.get("form4_filing_date", "")).strip()

    def unique_units(source: list[dict[str, str]], key_fn) -> set:
        return {key_fn(r) for r in source if all(key_fn(r))}

    issuer_all = unique_units(pit_rows, lambda r: (issuer_key(r),))
    issuer_matched = unique_units(matched_rows, lambda r: (issuer_key(r),))
    accession_all = unique_units(pit_rows, accession_key)
    accession_matched = unique_units(matched_rows, accession_key)
    filing_all = unique_units(pit_rows, filing_unit_key)
    filing_matched = unique_units(matched_rows, filing_unit_key)

    by_issuer: dict[str, dict] = {}
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for r in matched_rows:
        grouped[issuer_key(r)].append(r)
    for cik, group in sorted(grouped.items()):
        symbols = sorted({str(r.get("form4_symbol", "")).strip() for r in group if str(r.get("form4_symbol", "")).strip()})
        by_issuer[cik] = {
            "symbols": symbols,
            "matched_rows": len(group),
            "matched_accessions": len(unique_units(group, accession_key)),
            "matched_filing_units": len(unique_units(group, filing_unit_key)),
        }

    def rate(n: int, d: int) -> float | None:
        return n / d if d else None

    row_matches = len(matched_rows)
    issuer_matches = len(issuer_matched)
    accession_matches = len(accession_matched)
    filing_matches = len(filing_matched)
    top_issuer_rows = max((v["matched_rows"] for v in by_issuer.values()), default=0)

    return {
        "phase": 439,
        "source_phase": 346,
        "source": {
            "artifact_id": ARTIFACT_ID,
            "artifact_zip_sha256": ARTIFACT_SHA256,
            **(source_meta or {}),
        },
        "sample": {
            "candidate_rows_all": len(all_rows),
            "pit_eligible_rows": len(pit_rows),
            "distinct_issuer_ciks": len(issuer_all),
            "distinct_issuer_accessions": len(accession_all),
            "distinct_issuer_filing_date_units": len(filing_all),
        },
        "exact_ticker_evidence": {
            "matched_transaction_rows": row_matches,
            "row_weighted_rate": rate(row_matches, len(pit_rows)),
            "matched_issuer_ciks": issuer_matches,
            "issuer_weighted_rate": rate(issuer_matches, len(issuer_all)),
            "matched_issuer_accessions": accession_matches,
            "accession_weighted_rate": rate(accession_matches, len(accession_all)),
            "matched_issuer_filing_date_units": filing_matches,
            "filing_unit_weighted_rate": rate(filing_matches, len(filing_all)),
            "matched_rows_by_issuer": by_issuer,
            "largest_issuer_share_of_matched_rows": rate(top_issuer_rows, row_matches),
        },
        "interpretation": {
            "53_of_96_is_row_weighted_not_independent_coverage": True,
            "dominant_issuer": "1427352",
            "dominant_issuer_symbol": "ONTC",
            "dominant_issuer_matched_rows": by_issuer.get("1427352", {}).get("matched_rows", 0),
            "dominant_issuer_share_of_all_pit_rows": rate(
                by_issuer.get("1427352", {}).get("matched_rows", 0), len(pit_rows)
            ),
            "decision": "DO_NOT_USE_ROW_WEIGHTED_53_OF_96_AS_IDENTITY_COVERAGE",
            "alpha_authorized": False,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path, help="Phase 346 artifact ZIP or extracted candidate CSV")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    rows, meta = load_rows(args.input)
    payload = json.dumps(summarize(rows, meta), indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload)


if __name__ == "__main__":
    main()

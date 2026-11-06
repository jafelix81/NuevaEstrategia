#!/usr/bin/env python3
"""Phase 162: inspect the SEC document referenced by a reused 13D/G accession."""
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

from phase161_13dg_previous_accession_semantics_audit import SAMPLE_ROWS as PHASE161_ROWS

PARENT_DOCUMENT = {
    "accession": "0001445546-21-002430",
    "form": "SC 13G",
    "filing_date": "2021-05-10",
    "accepted_et": "2021-05-10 09:06:41",
    "filer_cik": "0001184765",
    "issuer_cik": "0001667919",
    "issuer_name": "First Trust Exchange-Traded Fund VIII",
    "security_class": "FT Cboe Vest U.S. Equity Deep Buffer ETF - August",
    "cusip": "33740F854",
    "event_date": "2021-04-30",
    "index_url": "https://www.sec.gov/Archives/edgar/data/1184765/000144554621002430/0001445546-21-002430-index.html",
    "primary_document_url": "https://www.sec.gov/Archives/edgar/data/1184765/000144554621002430/sc13g_3.txt",
}

# Child rows/URLs are inherited from the Phase 161 targeted official-SEC XML fixture.
# The SEC XML header filer CIK is 0001184765 for each child.
CHILD_ROWS = [{**row, "filer_cik": "0001184765"} for row in PHASE161_ROWS]


def normalize_accession(value: str) -> str | None:
    match = re.fullmatch(r"\s*(\d{1,10})-(\d{2})-(\d{1,6})\s*", str(value or ""))
    if not match:
        return None
    return f"{int(match.group(1)):010d}-{match.group(2)}-{int(match.group(3)):06d}"


def audit(rows: list[dict] | None = None, parent: dict | None = None) -> tuple[list[dict], dict]:
    rows = CHILD_ROWS if rows is None else rows
    parent = PARENT_DOCUMENT if parent is None else parent
    parent_accession = normalize_accession(parent.get("accession", ""))
    parent_issuer = str(parent.get("issuer_cik", "")).zfill(10)
    parent_filer = str(parent.get("filer_cik", "")).zfill(10)
    parent_cusip = str(parent.get("cusip", "")).strip()

    output_rows: list[dict] = []
    invalid_rows = 0
    for raw in rows:
        child = normalize_accession(raw.get("child_accession", ""))
        previous = normalize_accession(raw.get("previous_accession", ""))
        child_issuer = str(raw.get("issuer_cik", "")).strip().zfill(10)
        child_filer = str(raw.get("filer_cik", "")).strip().zfill(10)
        child_cusip = str(raw.get("cusip", "")).strip()
        if not child or not previous or not child_issuer.isdigit() or not child_filer.isdigit() or not child_cusip:
            invalid_rows += 1
            continue

        same_reference = previous == parent_accession
        same_filer = child_filer == parent_filer
        same_issuer = child_issuer == parent_issuer
        same_cusip = child_cusip == parent_cusip
        child_year = 2000 + int(child.split("-")[1])
        parent_year = int(parent["filing_date"][:4])

        if not same_reference:
            status = "REFERENCE_DOES_NOT_MATCH_INSPECTED_PARENT"
        elif not same_filer:
            status = "FILER_MISMATCH"
        elif not same_issuer:
            status = "ISSUER_CIK_MISMATCH"
        elif not same_cusip:
            status = "SAME_ISSUER_CIK_DIFFERENT_CUSIP_UNRESOLVED"
        else:
            status = "ISSUER_CUSIP_CONTINUITY_CANDIDATE_ONLY"

        output_rows.append({
            "child_accession": child,
            "previous_accession": previous,
            "parent_accession": parent_accession,
            "child_filer_cik": child_filer,
            "parent_filer_cik": parent_filer,
            "child_issuer_cik": child_issuer,
            "parent_issuer_cik": parent_issuer,
            "child_cusip": child_cusip,
            "parent_cusip": parent_cusip,
            "same_reference": same_reference,
            "same_filer_cik": same_filer,
            "same_issuer_cik": same_issuer,
            "same_cusip": same_cusip,
            "child_accession_year": child_year,
            "parent_filing_year": parent_year,
            "parent_precedes_child_by_accession_year": parent_year < child_year,
            "status": status,
            "child_source_url": raw.get("source_url", ""),
        })

    valid = output_rows
    same_ref = [r for r in valid if r["same_reference"]]
    same_filer = [r for r in same_ref if r["same_filer_cik"]]
    same_issuer = [r for r in same_ref if r["same_issuer_cik"]]
    same_cusip = [r for r in same_ref if r["same_cusip"]]
    exact = [r for r in same_ref if r["same_issuer_cik"] and r["same_cusip"]]
    same_issuer_diff_cusip = [r for r in same_ref if r["same_issuer_cik"] and not r["same_cusip"]]
    cross_issuer = [r for r in same_ref if not r["same_issuer_cik"]]
    form_family_match = "13G" in str(parent.get("form", "")).upper() and all(
        "13G" in str(r.get("form", "")).upper() for r in valid
    )
    summary = {
        "phase": 162,
        "status": "PREVIOUS_ACCESSION_NOT_PARENT_FOR_TARGETED_CHILD_SET" if same_ref and not exact else "REQUIRES_REVIEW",
        "sample_design": "TARGETED_NON_RANDOM_PUBLIC_SEC_XML_CONTROL_SET_INHERITED_FROM_PHASE161",
        "child_rows": len(rows),
        "valid_child_rows": len(valid),
        "invalid_child_rows": invalid_rows,
        "unique_child_accessions": len({r["child_accession"] for r in valid}),
        "unique_previous_accessions": len({r["previous_accession"] for r in valid}),
        "parent_document_inspected": True,
        "parent_accession": parent_accession,
        "parent_form": parent["form"],
        "parent_is_amendment": str(parent["form"]).upper().endswith("/A"),
        "parent_filing_date": parent["filing_date"],
        "parent_accepted_et": parent["accepted_et"],
        "parent_filer_cik": parent_filer,
        "parent_issuer_cik": parent_issuer,
        "parent_issuer_name": parent["issuer_name"],
        "parent_security_class": parent["security_class"],
        "parent_cusip": parent_cusip,
        "children_matching_parent_reference": len(same_ref),
        "children_matching_parent_filer_cik": len(same_filer),
        "children_matching_parent_issuer_cik": len(same_issuer),
        "children_with_parent_issuer_cik_mismatch": len(cross_issuer),
        "children_matching_parent_cusip": len(same_cusip),
        "children_same_issuer_different_cusip": len(same_issuer_diff_cusip),
        "children_with_exact_issuer_and_cusip_match": len(exact),
        "parent_13g_family_matches_children": form_family_match,
        "all_children_later_than_parent_by_accession_year": bool(valid) and all(
            r["parent_precedes_child_by_accession_year"] for r in valid
        ),
        "interpretation": (
            "The referenced accession is a real initial SC 13G filed by First Trust Portfolios L.P. "
            "for First Trust Exchange-Traded Fund VIII, specifically FT Cboe Vest U.S. Equity Deep Buffer ETF - August "
            "(CUSIP 33740F854). All eight sampled children carry the same filer CIK and repeat this accession, "
            "but four have a different issuer CIK and the four with the same issuer CIK all have a different CUSIP. "
            "No child has exact issuer-CIK plus CUSIP continuity with the referenced filing. The pattern is consistent "
            "with a stale or template-level filer reference being reused, but the exact software/workflow cause is not proven."
        ),
        "decision": (
            "Retain previousAccessionNumber as raw provenance only for this targeted group. Do not use it to link or "
            "backdate any of the eight child ownership states. A different parent must be found through issuer/security "
            "history and the original SEC submission; same filer, same issuer CIK, form-family match or date precedence "
            "alone is insufficient."
        ),
        "source_provenance": (
            "Parent SEC filing-detail index and primary text were inspected on the official SEC archive. Child XML URLs "
            "are inherited from the Phase 161 official-SEC fixture. This repository fixture is manually transcribed; "
            "raw response bodies and per-document SHA-256 hashes are not included."
        ),
        "forward_returns_used": False,
        "final_holdout_used": False,
        "production_changed": False,
        "f80_changed": False,
    }
    return output_rows, summary


def write_outputs(rows: list[dict], summary: dict, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "phase162_13dg_parent_accession_validation_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    fields = [
        "child_accession", "previous_accession", "parent_accession",
        "child_filer_cik", "parent_filer_cik", "child_issuer_cik", "parent_issuer_cik",
        "child_cusip", "parent_cusip", "same_reference", "same_filer_cik",
        "same_issuer_cik", "same_cusip", "child_accession_year", "parent_filing_year",
        "parent_precedes_child_by_accession_year", "status", "child_source_url",
    ]
    with (output_dir / "phase162_13dg_parent_accession_validation.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    rows, summary = audit()
    write_outputs(rows, summary, args.output_dir)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["status"] == "PREVIOUS_ACCESSION_NOT_PARENT_FOR_TARGETED_CHILD_SET" else 2


if __name__ == "__main__":
    raise SystemExit(main())

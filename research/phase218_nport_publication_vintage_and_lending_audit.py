#!/usr/bin/env python3
"""Phase 218 deterministic N-PORT publication-vintage and field-semantics audit.

This validates a curated SEC filing-index manifest and explicit admission controls.
It does not download filings, hash raw XML, or estimate population coverage.
"""
from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from statistics import median

EVIDENCE_PATH = Path(__file__).with_name("phase218_nport_publication_vintage_and_lending_audit.json")


def build_audit(evidence: dict[str, object]) -> dict[str, object]:
    filings = evidence["filing_lag_sample"]["filings"]
    lags: list[int] = []
    accession_seen: set[str] = set()
    acceptance_dates_match = True
    all_forms_nport_p = True

    for filing in filings:
        accession = filing["accession"]
        if accession in accession_seen:
            raise ValueError("duplicate_accession")
        accession_seen.add(accession)
        if filing["form"] != "NPORT-P":
            all_forms_nport_p = False
        report_date = date.fromisoformat(filing["report_date"])
        filing_date = date.fromisoformat(filing["filing_date"])
        lag = (filing_date - report_date).days
        if lag != int(filing["report_to_filing_calendar_days"]):
            raise ValueError("report_to_filing_lag_mismatch")
        if filing["acceptance_et"][:10] != filing["filing_date"]:
            acceptance_dates_match = False
        lags.append(lag)

    summary = {"min": min(lags), "median": median(lags), "max": max(lags)}
    if len(filings) != int(evidence["filing_lag_sample"]["count"]):
        raise ValueError("filing_count_mismatch")
    if summary != evidence["filing_lag_sample"]["lag_calendar_days_summary"]:
        raise ValueError("lag_summary_mismatch")

    return {
        "phase": 218,
        "status": evidence["status"],
        "filing_count": len(filings),
        "all_accessions_unique": len(accession_seen) == len(filings),
        "all_forms_nport_p": all_forms_nport_p,
        "all_acceptance_dates_match_filing_dates": acceptance_dates_match,
        "report_to_filing_calendar_days": summary,
        "filings_within_50_to_60_days": sum(50 <= value <= 60 for value in lags),
        "early_filing_count_below_50_days": sum(value < 50 for value in lags),
        "official_sec_quarters": evidence["official_sec_archive"]["quarter_count"],
        "data_gov_quarters": evidence["data_gov_catalog_comparison"]["resource_count"],
        "data_gov_one_quarter_stale": (
            evidence["official_sec_archive"]["quarter_count"]
            - evidence["data_gov_catalog_comparison"]["resource_count"]
            == 1
        ),
        "raw_submission_sha256_verified": evidence["phase217_reassessment"]["raw_submission_sha256_verified"],
        "raw_primary_xml_sha256_verified": evidence["phase217_reassessment"]["raw_primary_xml_sha256_verified"],
        "first_public_receipt_verified": evidence["phase217_reassessment"]["first_public_receipt_capture_verified"],
        "alpha_test_authorized": evidence["research_decision"]["alpha_test_authorized"],
        "holdout_used": evidence["research_decision"]["holdout_used"],
        "f80_frozen": evidence["research_decision"]["f80_frozen"],
        "decision": "NO_ALPHA_ADMISSION_PENDING_RAW_FILES_PIT_LINEAGE_AND_UNIVERSE_GATES",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--evidence", type=Path, default=EVIDENCE_PATH)
    args = parser.parse_args()
    evidence = json.loads(args.evidence.read_text(encoding="utf-8"))
    result = build_audit(evidence)
    payload = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    print(payload)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Adjudicate the Phase 84 Schedule 13D/A combined tender-offer XML exception.

This is an offline audit of an already captured SEC submission artifact. It does
not make network requests, alter the source artifact, or authorize an economic
or trading test.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any

COMBINED_TENDER_TYPES = {"SC TO-I", "SC TO-I/A", "SC TO-T", "SC TO-T/A"}
MANDATORY_XML_TOKEN = "mandatory_xml"


def normalize_form(value: str | None) -> str:
    token = re.sub(r"\s+", " ", str(value or "").strip().upper())
    token = re.sub(r"^SCHEDULE\s+", "SC ", token)
    return token


def parse_sec_header(raw: str) -> dict[str, Any]:
    match = re.search(r"<SEC-HEADER\b[^>]*>(.*?)</SEC-HEADER>", raw, flags=re.I | re.S)
    if not match:
        raise ValueError("sec_header_block_missing")
    header = match.group(1)

    submission_match = re.search(
        r"(?im)^\s*CONFORMED SUBMISSION TYPE:\s*([^\r\n]+)", header
    )
    submission_type = normalize_form(submission_match.group(1)) if submission_match else ""

    subject_blocks = re.findall(
        r"(?ims)^\s*SUBJECT COMPANY:\s*(.*?)(?=^\s*(?:SUBJECT COMPANY:|FILED BY:)\s*$)",
        header,
    )
    subject_form_types: list[str] = []
    subject_ciks: list[str] = []
    for block in subject_blocks:
        for value in re.findall(r"(?im)^\s*FORM TYPE:\s*([^\r\n]+)", block):
            normalized = normalize_form(value)
            if normalized and normalized not in subject_form_types:
                subject_form_types.append(normalized)
        for value in re.findall(r"(?im)^\s*CENTRAL INDEX KEY:\s*([0-9]{1,10})\s*$", block):
            cik = value.zfill(10)
            if cik not in subject_ciks:
                subject_ciks.append(cik)

    return {
        "conformed_submission_type": submission_type,
        "subject_form_types": subject_form_types,
        "subject_ciks": subject_ciks,
        "subject_block_count": len(subject_blocks),
    }


def is_documented_combined_13d_exception(
    master_index_form: str,
    header: dict[str, Any],
    xml_present: bool,
) -> bool:
    """True only for the SEC-documented combined SC 13D/A + SC TO exception."""
    if xml_present:
        return False
    index_form = normalize_form(master_index_form)
    submission_type = normalize_form(header.get("conformed_submission_type"))
    subject_forms = {normalize_form(x) for x in header.get("subject_form_types", [])}
    return (
        index_form == "SC 13D/A"
        and submission_type in COMBINED_TENDER_TYPES
        and index_form in subject_forms
    )


def parse_bool(value: Any) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "y"}


def audit_artifact(artifact_dir: Path) -> dict[str, Any]:
    artifact_dir = Path(artifact_dir)
    summary_path = artifact_dir / "pilot_summary.json"
    validation_path = artifact_dir / "pilot_header_validation.csv"
    if not summary_path.exists() or not validation_path.exists():
        raise FileNotFoundError(
            "Phase 84 artifact must contain pilot_summary.json and pilot_header_validation.csv"
        )

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    with validation_path.open("r", newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))

    exceptions: list[dict[str, Any]] = []
    missing_xml: list[dict[str, Any]] = []
    missing_raw: list[str] = []
    form_mismatches: list[dict[str, Any]] = []
    mandatory_rows = 0
    mandatory_xml_present = 0
    role_form_matches = 0

    for row in rows:
        raw_rel = str(row.get("raw_file") or "").strip()
        raw_path = artifact_dir / raw_rel
        if not raw_rel or not raw_path.is_file():
            missing_raw.append(str(row.get("accession") or ""))
            header: dict[str, Any] = {}
        else:
            raw = raw_path.read_text(encoding="utf-8", errors="replace")
            try:
                header = parse_sec_header(raw)
            except ValueError:
                header = {}

        index_form = normalize_form(row.get("master_index_form"))
        subject_forms = {normalize_form(x) for x in header.get("subject_form_types", [])}
        form_match = bool(index_form and index_form in subject_forms)
        if form_match:
            role_form_matches += 1
        else:
            form_mismatches.append({
                "accession": row.get("accession", ""),
                "master_index_form": row.get("master_index_form", ""),
                "conformed_submission_type": header.get("conformed_submission_type", ""),
                "subject_form_types": sorted(subject_forms),
            })

        timing_regime = str(row.get("timing_regime") or "")
        if MANDATORY_XML_TOKEN not in timing_regime:
            continue
        mandatory_rows += 1
        xml_present = parse_bool(row.get("xml_present"))
        if xml_present:
            mandatory_xml_present += 1
            continue

        exception = is_documented_combined_13d_exception(
            str(row.get("master_index_form") or ""), header, xml_present
        )
        item = {
            "accession": row.get("accession", ""),
            "master_index_form": row.get("master_index_form", ""),
            "header_form": row.get("header_form", ""),
            "conformed_submission_type": header.get("conformed_submission_type", ""),
            "subject_form_types": header.get("subject_form_types", []),
            "subject_ciks": header.get("subject_ciks", []),
            "raw_file": raw_rel,
        }
        if exception:
            exceptions.append(item)
        else:
            missing_xml.append(item)

    eligible_mandatory_xml_rows = mandatory_rows - len(exceptions)
    xml_coverage = (
        mandatory_xml_present / eligible_mandatory_xml_rows
        if eligible_mandatory_xml_rows else 1.0
    )
    form_rate = role_form_matches / len(rows) if rows else 0.0

    original_checks = dict(summary.get("gate_checks") or {})
    checks = dict(original_checks)
    checks["subject_role_form_concordance_ge_99_5pct"] = form_rate >= 0.995
    checks["mandatory_xml_present_ge_99_5pct"] = xml_coverage >= 0.995 and not missing_xml
    checks["mandatory_xml_present_ge_99_5pct_after_sec_documented_exception"] = (
        xml_coverage >= 0.995 and not missing_xml
    )
    checks["all_sample_raw_submissions_present"] = not missing_raw
    checks["no_unresolved_mandatory_xml_exceptions"] = not missing_xml

    required_original = [
        "all_sample_rows_retrieved",
        "header_parse_ge_99_5pct",
        "accession_form_date_concordance_ge_99_5pct",
        "subject_and_filer_cik_presence_ge_99_5pct",
        "target_subject_index_recall_ge_99_5pct",
        "no_target_subjects_missed_by_index_candidate_set",
        "candidate_roles_resolved_ge_99_5pct",
        "xml_subject_filer_concordance_ge_99_5pct",
        "acceptance_timestamp_valid_ge_99_5pct",
        "raw_hash_and_retrieval_utc_ge_99_5pct",
        "source_http_200_ge_99_5pct",
    ]
    all_checks = all(bool(checks.get(key)) for key in required_original) and all(
        bool(checks.get(key)) for key in (
            "subject_role_form_concordance_ge_99_5pct",
            "mandatory_xml_present_ge_99_5pct_after_sec_documented_exception",
            "all_sample_raw_submissions_present",
            "no_unresolved_mandatory_xml_exceptions",
        )
    )

    return {
        "phase": "601-13dg-combined-tender-offer-xml-exception-adjudication",
        "source_run_id": 41914491120,
        "source_artifact_id": 13364856424,
        "source_artifact_sha256": "b807be9099e1a777c232f6d50b341e8e714585dc4da5fe993e833c2051494b16",
        "sample_rows": len(rows),
        "sample_rows_retrieved": summary.get("sample_rows_retrieved"),
        "fetch_errors": summary.get("fetch_errors"),
        "original_phase84_data_gate": summary.get("data_gate"),
        "adjudicated_data_gate": "PASS" if all_checks else "FAIL",
        "original_mandatory_xml_rows": mandatory_rows,
        "documented_combination_exceptions": len(exceptions),
        "mandatory_xml_rows_after_exception": eligible_mandatory_xml_rows,
        "mandatory_xml_present_rows": mandatory_xml_present,
        "mandatory_xml_coverage_after_exception": round(xml_coverage, 9),
        "subject_role_form_concordance_rows": role_form_matches,
        "subject_role_form_concordance_rate": round(form_rate, 9),
        "form_mismatches_after_role_aware_check": form_mismatches,
        "documented_exceptions": exceptions,
        "unresolved_mandatory_xml_missing": missing_xml,
        "missing_raw_submissions": missing_raw,
        "original_gate_checks": original_checks,
        "adjudicated_gate_checks": checks,
        "economic_test_authorized": False,
        "forward_returns_used": False,
        "production_changes_authorized": False,
        "limitations": [
            "The SEC Filer Manual exception resolves only the combined SC 13D/A + SC TO filing format case; it does not waive XML for standalone Schedule 13D/G filings.",
            "The 319 CIKs are current candidate identifiers, not a historical point-in-time F80 security master or membership ledger.",
            "The deterministic hash-stratified sample is descriptive and has no design-based inferential confidence interval.",
            "This is a data-identity feasibility result, not evidence of informed or predictive behavior.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    result = audit_artifact(args.artifact_dir)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "adjudicated_data_gate": result["adjudicated_data_gate"],
        "sample_rows": result["sample_rows"],
        "documented_combination_exceptions": result["documented_combination_exceptions"],
        "mandatory_xml_rows_after_exception": result["mandatory_xml_rows_after_exception"],
        "mandatory_xml_present_rows": result["mandatory_xml_present_rows"],
        "mandatory_xml_coverage_after_exception": result["mandatory_xml_coverage_after_exception"],
        "subject_role_form_concordance_rate": result["subject_role_form_concordance_rate"],
        "form_mismatches_after_role_aware_check": len(result["form_mismatches_after_role_aware_check"]),
        "unresolved_mandatory_xml_missing": len(result["unresolved_mandatory_xml_missing"]),
        "economic_test_authorized": False,
    }, indent=2))
    return 0 if result["adjudicated_data_gate"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())

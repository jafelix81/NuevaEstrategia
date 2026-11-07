#!/usr/bin/env python3
"""Artifact-only adjudication of the Phase 84 SEC 13D/13G role-aware pilot.

No network requests are made. The input ZIPs are immutable GitHub Actions
artifacts downloaded from Phase 84 and Phase 82.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
from typing import Any

VALID_13DG_FORMS = {"SC 13D", "SC 13D/A", "SC 13G", "SC 13G/A"}


def norm(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip().upper()


def normalize_form(value: Any) -> str:
    form = norm(value)
    if form.startswith("SCHEDULE "):
        form = "SC " + form[len("SCHEDULE "):]
    return form


def is_13dg_form(value: Any) -> bool:
    return normalize_form(value) in VALID_13DG_FORMS


def parse_submission(raw: str) -> tuple[str, list[str]]:
    header_match = re.search(
        r"CONFORMED SUBMISSION TYPE:\s*([^\r\n]+)", raw, flags=re.IGNORECASE
    )
    header_form = normalize_form(header_match.group(1)) if header_match else ""
    document_types = [
        normalize_form(x)
        for x in re.findall(r"<TYPE>\s*([^\r\n<]+)", raw, flags=re.IGNORECASE)
    ]
    return header_form, document_types


def classify_form_relationship(index_form: str, header_form: str, document_types: list[str]) -> str:
    if normalize_form(index_form) == normalize_form(header_form):
        return "match"
    # Quarantine only when the actual SEC submission header and every document
    # identify a non-13D/G filing. A conflicting 13D/G document remains unresolved.
    if not is_13dg_form(header_form) and not any(is_13dg_form(x) for x in document_types):
        return "index_alias_non_13dg"
    return "unresolved_form_conflict"


def parse_bool(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def parse_iso_utc(value: Any) -> datetime | None:
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            return None
        return dt.astimezone(timezone.utc)
    except (TypeError, ValueError):
        return None


def parse_sec_acceptance_utc(raw: str) -> datetime | None:
    match = re.search(r"<ACCEPTANCE-DATETIME>\s*(\d{14})", raw, flags=re.IGNORECASE)
    if not match:
        return None
    try:
        local = datetime.strptime(match.group(1), "%Y%m%d%H%M%S").replace(
            tzinfo=ZoneInfo("America/New_York")
        )
        return local.astimezone(timezone.utc)
    except ValueError:
        return None


def read_phase84(artifact_path: Path) -> tuple[dict[str, Any], list[dict[str, str]], zipfile.ZipFile]:
    zf = zipfile.ZipFile(artifact_path)
    summary = json.loads(zf.read("pilot_summary.json"))
    rows = list(csv.DictReader(io.TextIOWrapper(
        zf.open("pilot_header_validation.csv"), encoding="utf-8-sig", newline=""
    )))
    return summary, rows, zf


def audit_artifacts(phase84_zip: Path, phase82_zip: Path | None = None) -> dict[str, Any]:
    summary, rows, z84 = read_phase84(phase84_zip)
    errors: list[str] = []
    conflict_rows: list[dict[str, Any]] = []
    hash_valid = raw_saved = timestamp_valid = 0
    acceptance_recomputed_match = raw_size_match = http_200 = 0
    xml_subject_match = xml_filer_match = xml_rows = 0

    for row in rows:
        raw_name = row.get("raw_file", "")
        if not raw_name or raw_name not in z84.namelist():
            errors.append(f"missing raw submission: {row.get('accession')}")
            continue
        raw_bytes = z84.read(raw_name)
        raw_saved += 1
        digest = hashlib.sha256(raw_bytes).hexdigest()
        if digest == row.get("source_sha256", "") and parse_bool(row.get("source_sha256_valid")):
            hash_valid += 1
        else:
            errors.append(f"raw hash mismatch: {row.get('accession')}")

        raw_text = raw_bytes.decode("utf-8", errors="replace")
        if str(len(raw_bytes)) == str(row.get("source_bytes", "")) and parse_bool(row.get("raw_submission_saved")):
            raw_size_match += 1
        else:
            errors.append(f"raw size/save metadata mismatch: {row.get('accession')}")

        actual_acceptance = parse_sec_acceptance_utc(raw_text)
        recorded_acceptance = parse_iso_utc(row.get("acceptance_utc"))
        retrieved_at = parse_iso_utc(row.get("retrieved_at_utc"))
        if actual_acceptance is not None and recorded_acceptance is not None and actual_acceptance == recorded_acceptance and retrieved_at is not None:
            acceptance_recomputed_match += 1
        else:
            errors.append(f"acceptance/retrieval timestamp mismatch: {row.get('accession')}")

        actual_header_form, document_types = parse_submission(raw_text)
        recorded_header_form = normalize_form(row.get("header_form", ""))
        if actual_header_form != recorded_header_form:
            errors.append(f"CSV/header form mismatch: {row.get('accession')}")
        relationship = classify_form_relationship(
            row.get("master_index_form", ""), actual_header_form, document_types
        )
        if relationship == "unresolved_form_conflict":
            errors.append(f"unresolved index/header/document form conflict: {row.get('accession')}")
        if relationship != "match":
            conflict_rows.append({
                "accession": row.get("accession"),
                "index_form": normalize_form(row.get("master_index_form", "")),
                "header_form": actual_header_form,
                "document_types": document_types,
                "classification": relationship,
                "sample_stratum": row.get("sample_stratum"),
                "candidate_class": row.get("candidate_class"),
            })

        if row.get("source_http_status") == "200":
            http_200 += 1
        if parse_bool(row.get("acceptance_timestamp_valid")) and parse_bool(row.get("retrieval_timestamp_valid")):
            timestamp_valid += 1
        if parse_bool(row.get("xml_present")):
            xml_rows += 1
            if parse_bool(row.get("xml_subject_matches_header")):
                xml_subject_match += 1
            else:
                errors.append(f"XML subject/header mismatch: {row.get('accession')}")
            if parse_bool(row.get("xml_filer_matches_header")):
                xml_filer_match += 1
            else:
                errors.append(f"XML filer/header mismatch: {row.get('accession')}")

    # The master index is a discovery layer. Mandatory-XML eligibility is
    # evaluated only after the actual SEC submission form has been confirmed.
    mandatory_index_rows = [r for r in rows if "mandatory_xml" in r.get("sample_stratum", "")]
    valid_mandatory_rows = [
        r for r in mandatory_index_rows if is_13dg_form(r.get("header_form", ""))
    ]
    mandatory_xml_present = sum(parse_bool(r.get("xml_present")) for r in valid_mandatory_rows)
    mandatory_xml_missing = len(valid_mandatory_rows) - mandatory_xml_present

    candidate_rows = [r for r in rows if r.get("candidate_class") != "control"]
    role_resolved = [
        r for r in candidate_rows
        if parse_bool(r.get("candidate_role_resolved")) and r.get("candidate_role") in {"subject", "filer"}
    ]
    role_counts = Counter(r.get("candidate_role") for r in candidate_rows)
    unique_rows = [r for r in candidate_rows if r.get("candidate_class") == "unique_candidate"]
    ambiguous_rows = [r for r in candidate_rows if r.get("candidate_class") == "ambiguous"]
    unique_roles = Counter(r.get("candidate_role") for r in unique_rows)
    ambiguous_roles = Counter(r.get("candidate_role") for r in ambiguous_rows)
    subject_rows = [r for r in candidate_rows if r.get("candidate_role") == "subject"]
    subject_index_covered = sum(parse_bool(r.get("subject_target_index_covered")) for r in subject_rows)

    phase82_index_evidence: dict[str, Any] | None = None
    if phase82_zip is not None:
        with zipfile.ZipFile(phase82_zip) as z82:
            idx_name = "raw_master_indexes/master_2026Q2.idx"
            if idx_name in z82.namelist():
                index_text = z82.read(idx_name).decode("latin-1", errors="replace")
                accession = "0001104659-26-057293"
                lines = [line for line in index_text.splitlines() if accession in line]
                phase82_index_evidence = {
                    "accession": accession,
                    "raw_index_row_count": len(lines),
                    "raw_index_rows": lines,
                    "forms": dict(Counter(
                        line.split("|")[2] for line in lines if len(line.split("|")) >= 3
                    )),
                }
            else:
                errors.append(f"missing Phase 82 raw index: {idx_name}")

    form_mismatches = [r for r in rows if not parse_bool(r.get("form_match"))]
    alias_quarantine_count = sum(
        x["classification"] == "index_alias_non_13dg" for x in conflict_rows
    )
    unresolved_conflicts = sum(
        x["classification"] == "unresolved_form_conflict" for x in conflict_rows
    )
    n = len(rows)
    valid_form_rows = n - alias_quarantine_count

    checks = {
        "all_600_raw_submissions_present": raw_saved == n == 600,
        "all_600_raw_sizes_match_metadata": raw_size_match == n,
        "all_600_acceptance_utc_recomputed_from_SEC_header": acceptance_recomputed_match == n,
        "all_600_raw_hashes_recomputed_and_match": hash_valid == n,
        "all_600_http_200": http_200 == n,
        "all_600_acceptance_and_retrieval_timestamps_valid": timestamp_valid == n,
        "all_csv_header_forms_reproduced_from_raw": not any("CSV/header form mismatch" in e for e in errors),
        "all_form_conflicts_explained_or_quarantined": unresolved_conflicts == 0,
        "valid_13dg_form_concordance_100pct_after_quarantine": valid_form_rows == 599 and len(form_mismatches) == alias_quarantine_count == 1,
        "mandatory_xml_100pct_on_actual_13dg_forms": mandatory_xml_missing == 0 and len(valid_mandatory_rows) == 192 and mandatory_xml_present == 192,
        "all_200_present_xml_subject_and_filer_match_header": xml_rows == 200 and xml_subject_match == 200 and xml_filer_match == 200,
        "all_candidate_roles_resolved": len(role_resolved) == len(candidate_rows) == 367,
        "all_sampled_subject_target_candidates_index_covered": subject_index_covered == len(subject_rows) == 224,
    }
    status = "PASS_WITH_INDEX_ALIAS_QUARANTINE" if all(checks.values()) and not errors else "FAIL"

    return {
        "phase": "118-sec-13dg-phase84-artifact-adjudication",
        "status": status,
        "source_artifacts": {
            "phase84_zip": phase84_zip.name,
            "phase82_zip": phase82_zip.name if phase82_zip else None,
            "phase84_sample_rows": n,
        },
        "form_adjudication": {
            "master_index_header_form_mismatches": len(form_mismatches),
            "quarantined_non_13dg_index_aliases": alias_quarantine_count,
            "unresolved_form_conflicts": unresolved_conflicts,
            "valid_13dg_rows_after_quarantine": valid_form_rows,
            "mandatory_xml_index_stratum_rows_before_quarantine": len(mandatory_index_rows),
            "mandatory_xml_actual_13dg_rows_after_quarantine": len(valid_mandatory_rows),
            "mandatory_xml_present": mandatory_xml_present,
            "mandatory_xml_missing": mandatory_xml_missing,
            "conflict_rows": conflict_rows,
            "phase82_raw_index_evidence": phase82_index_evidence,
        },
        "integrity": {
            "raw_submissions_saved": raw_saved,
            "raw_hashes_recomputed_and_matching": hash_valid,
            "http_200": http_200,
            "acceptance_and_retrieval_timestamps_valid": timestamp_valid,
            "acceptance_utc_recomputed_from_raw_header": acceptance_recomputed_match,
            "raw_sizes_match_metadata": raw_size_match,
            "xml_rows": xml_rows,
            "xml_subject_header_matches": xml_subject_match,
            "xml_filer_header_matches": xml_filer_match,
        },
        "role_resolution": {
            "candidate_rows": len(candidate_rows),
            "candidate_roles_resolved": len(role_resolved),
            "subject_role_rows": role_counts.get("subject", 0),
            "filer_only_role_rows": role_counts.get("filer", 0),
            "subject_role_share_sample": role_counts.get("subject", 0) / len(candidate_rows) if candidate_rows else None,
            "filer_only_share_sample": role_counts.get("filer", 0) / len(candidate_rows) if candidate_rows else None,
            "unique_candidate_rows": len(unique_rows),
            "unique_candidate_subject_rows": unique_roles.get("subject", 0),
            "unique_candidate_filer_rows": unique_roles.get("filer", 0),
            "ambiguous_candidate_rows": len(ambiguous_rows),
            "ambiguous_resolved_subject_rows": ambiguous_roles.get("subject", 0),
            "ambiguous_resolved_filer_rows": ambiguous_roles.get("filer", 0),
            "subject_target_index_covered": subject_index_covered,
            "weighted_role_estimate_from_phase84": summary.get("weighted_role_estimate"),
        },
        "gate_checks": checks,
        "errors": errors,
        "forward_returns_used": False,
        "economic_test_authorized": False,
        "production_changes_authorized": False,
        "limitations": [
            "The 600-row pilot is stratified from the candidate population intersecting the current 319 CIK list; it does not establish global subject-issuer recall or historical F80 membership.",
            "The weighted role estimate is descriptive and has no inferential confidence interval; it is not alpha evidence.",
            "SEC-HEADER ACCEPTANCE-DATETIME is not independently verified public dissemination time; apply a conservative next-session knowledge rule.",
            "A role-correct filing panel still requires deterministic reporting-group/amendment lineage and historical issuer-security identity before returns testing.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase84-zip", type=Path, required=True)
    parser.add_argument("--phase82-zip", type=Path)
    parser.add_argument("--output", type=Path, default=Path("phase118_adjudication.json"))
    args = parser.parse_args()
    result = audit_artifacts(args.phase84_zip, args.phase82_zip)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if result["status"] != "PASS_WITH_INDEX_ALIAS_QUARANTINE":
        raise SystemExit(2)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Phase 351 — recover the single unresolved SEC 13D/G parent archive-path candidate.

This is deliberately a one-row recovery. It reads the immutable Phase 349
manifest and the completed Phase 350 artifact, then attempts only the one
explicit parent that returned HTTP 404 through the subject-CIK path. The
manifest's alternate archive-path candidate is unverified until SEC-HEADER
identity, form family and acceptance chronology all validate.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

from research.phase350_sec_13dg_parent_retrieval import (
    build_archive_url,
    normalize_accession,
    normalize_cik,
    parse_sec_header,
    request_submission,
    validate_parent_metadata,
)
from research.sec_user_agent import resolve_sec_user_agent


def read_csv(path: str | Path) -> list[dict]:
    with Path(path).open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def build_recovery_target(prior_rows: list[dict], manifest_rows: list[dict]) -> dict:
    unresolved = [
        row for row in prior_rows
        if str(row.get("retrieval_status") or "").upper() == "NOT_FOUND"
        and str(row.get("http_status") or "") == "404"
    ]
    if len(unresolved) != 1:
        raise ValueError(f"expected_exactly_one_phase350_http_404_target_found_{len(unresolved)}")

    prior = unresolved[0]
    child = str(prior.get("child_accession") or "")
    manifest = [row for row in manifest_rows if row.get("child_accession") == child]
    if len(manifest) != 1:
        raise ValueError("phase349_manifest_child_join_not_unique")
    expected = manifest[0]

    parent_accession = normalize_accession(expected.get("explicit_parent_accession"))
    if parent_accession != normalize_accession(prior.get("parent_accession")):
        raise ValueError("phase350_phase349_parent_accession_mismatch")

    subject_cik = normalize_cik(expected.get("subject_issuer_cik"))
    candidate = normalize_cik(expected.get("parent_archive_path_cik"))
    accession_prefix = normalize_cik(parent_accession.split("-")[0])
    if not parent_accession or not subject_cik or not candidate:
        raise ValueError("missing_parent_subject_or_alternate_path_candidate")
    if candidate != accession_prefix:
        raise ValueError("manifest_alternate_candidate_not_accession_prefix")
    prior_failed_path = normalize_cik(prior.get("parent_archive_path_cik_candidate"))
    if candidate == subject_cik or (prior_failed_path and candidate == prior_failed_path):
        raise ValueError("alternate_path_candidate_not_distinct_from_failed_subject_path")

    return {
        "child_accession": child,
        "parent_accession": parent_accession,
        "subject_issuer_cik": subject_cik,
        "form_family": str(expected.get("form_family") or "").upper(),
        "child_acceptance_utc": str(expected.get("child_acceptance_utc") or ""),
        "alternate_archive_path_cik_candidate": candidate,
        "alternate_path_role": "UNVERIFIED_MANIFEST_CANDIDATE_FROM_ACCESSION_PREFIX",
        "prior_failed_path_cik": prior_failed_path,
        "prior_http_status": 404,
        "immediate_predecessor_claimed": False,
    }


def evaluate_parent_response(raw: bytes, target: dict) -> dict:
    parsed = parse_sec_header(raw.decode("utf-8", errors="replace"))
    expected = {
        "explicit_parent_accession": target["parent_accession"],
        "subject_issuer_cik": target["subject_issuer_cik"],
        "form_family": target["form_family"],
        "child_acceptance_utc": target["child_acceptance_utc"],
    }
    reasons = validate_parent_metadata(parsed, expected)
    return {
        **parsed,
        "accession_match": parsed.get("header_accession") == target["parent_accession"],
        "subject_cik_match": parsed.get("parent_subject_cik") == target["subject_issuer_cik"],
        "form_family_match": parsed.get("parent_form_family") == target["form_family"],
        "acceptance_strictly_earlier": bool(
            parsed.get("parent_acceptance_utc")
            and target.get("child_acceptance_utc")
            and not any(x == "parent_acceptance_not_strictly_earlier" for x in reasons)
            and not any(x in reasons for x in (
                "parent_acceptance_missing", "child_acceptance_missing"
            ))
        ),
        "validation_reasons": ";".join(reasons),
        "reference_validation_status": "VALID_EXPLICIT_REFERENCE" if not reasons else "QUARANTINE",
        "immediate_predecessor_claimed": False,
    }


def recover(prior_csv: str | Path, manifest_csv: str | Path, outdir: str | Path) -> dict:
    prior_rows = read_csv(prior_csv)
    manifest_rows = read_csv(manifest_csv)
    target = build_recovery_target(prior_rows, manifest_rows)
    user_agent, user_agent_source = resolve_sec_user_agent()
    url = build_archive_url(
        target["parent_accession"],
        target["alternate_archive_path_cik_candidate"],
    )
    status, body, error_text, blocked, retryable = request_submission(
        url, user_agent, pause_seconds=0.5, max_retries=1
    )

    out = Path(outdir)
    raw_dir = out / "parents"
    raw_dir.mkdir(parents=True, exist_ok=True)
    record = {
        **target,
        "url": url,
        "http_status": status,
        "raw_bytes": len(body),
        "raw_sha256": "",
        "retrieval_status": "HTTP_ERROR",
        "header_accession": "",
        "parent_form": "",
        "parent_form_family": "",
        "parent_filing_date": "",
        "parent_subject_cik": "",
        "parent_acceptance_utc": "",
        "accession_match": False,
        "subject_cik_match": False,
        "form_family_match": False,
        "acceptance_strictly_earlier": False,
        "reference_validation_status": "QUARANTINE",
        "validation_reasons": error_text,
        "user_agent_source": user_agent_source,
    }

    if status == 200 and body:
        raw_path = raw_dir / f"{target['parent_accession'].replace('-', '')}.txt"
        raw_path.write_bytes(body)
        record["raw_sha256"] = hashlib.sha256(body).hexdigest()
        record["retrieval_status"] = "HTTP_200"
        try:
            record.update(evaluate_parent_response(body, target))
        except Exception as exc:
            record["retrieval_status"] = "HEADER_PARSE_FAILED"
            record["validation_reasons"] = f"header_parse_error:{type(exc).__name__}:{exc}"
    elif status == 404:
        record["retrieval_status"] = "NOT_FOUND"
        record["validation_reasons"] = "alternate_archive_path_candidate_returned_http_404"
    elif blocked:
        record["retrieval_status"] = "BLOCKED_SEC_ACCESS"
    elif retryable:
        record["retrieval_status"] = "RETRYABLE_TRANSPORT_OR_RATE_LIMIT"

    out.mkdir(parents=True, exist_ok=True)
    with (out / "phase351_parent_404_recovery.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = list(record)
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerow(record)

    valid = record["reference_validation_status"] == "VALID_EXPLICIT_REFERENCE"
    summary = {
        "phase": 351,
        "status": "RECOVERED_VALID_EXPLICIT_REFERENCE" if valid else record["retrieval_status"],
        "target_references": 1,
        "requests_attempted": 1,
        "http_status_counts": {str(status): 1},
        "raw_parent_documents_saved": int(bool(record["raw_sha256"])),
        "valid_explicit_reference_rows": int(valid),
        "quarantined_or_unvalidated_rows": int(not valid),
        "user_agent_source": user_agent_source,
        "alternate_archive_path_candidate": target["alternate_archive_path_cik_candidate"],
        "alternate_path_verified_by_sec_header": valid,
        "immediate_predecessor_inference_performed": False,
        "sec_first_publication_timestamp_available": False,
        "strict_pit_admitted": False,
        "alpha_test_authorized": False,
        "f80_frozen": True,
    }
    (out / "phase351_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prior-results", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--outdir", type=Path, default=Path("phase351_output"))
    args = parser.parse_args()
    recover(args.prior_results, args.manifest, args.outdir)


if __name__ == "__main__":
    main()

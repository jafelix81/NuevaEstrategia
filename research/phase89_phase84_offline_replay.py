#!/usr/bin/env python3
"""Offline replay of the Phase 84 SEC 13D/13G artifact; performs no network requests."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from datetime import datetime
from pathlib import Path

from research.phase73_sec_submission_text_extractor import normalize_cik
from research.phase74_13dg_global_subject_audit import parse_pilot_record
from research.phase84_13dg_role_aware_identity_audit import (
    acceptance_to_utc, candidate_role_resolved, mandatory_xml_expected,
    target_role_flags, weighted_role_estimate,
)


def load_csv(path):
    with Path(path).open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def parse_json(value, default):
    if isinstance(value, (list, dict)):
        return value
    try:
        return json.loads(value) if str(value or "").strip() else default
    except (TypeError, ValueError):
        return default


def as_bool(value):
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "y"}


def expected_mandatory_xml_accessions(sample_rows, parsed_by_accession):
    """Use actual SEC-HEADER form; fall back to index form only if retrieval failed."""
    expected = set()
    for sample in sample_rows:
        accession = sample["accession"]
        parsed = parsed_by_accession.get(accession)
        if parsed is not None:
            form = parsed.get("header_form", "")
            filing_date = parsed.get("header_filing_date", "")
        else:
            form = sample.get("form", "")
            filing_date = sample.get("filing_date", "")
        if mandatory_xml_expected(form, filing_date):
            expected.add(accession)
    return expected


def run(args):
    artifact_dir = Path(args.artifact_dir)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    manifest = load_csv(artifact_dir / "sample_manifest.csv")
    prior_rows = load_csv(artifact_dir / "pilot_header_validation.csv")
    prior_by_accession = {r["accession"]: r for r in prior_rows}
    prior_summary = json.loads((artifact_dir / "pilot_summary.json").read_text(encoding="utf-8"))
    target_ciks = {
        normalize_cik(r.get("cik", ""))
        for r in load_csv(args.target_cik_file)
        if normalize_cik(r.get("cik", ""))
    }
    if not manifest or not target_ciks:
        raise RuntimeError("Missing Phase 84 manifest or target CIK input")

    parsed_rows, errors, consistency_errors = [], [], []
    raw_dir = artifact_dir / "raw_submissions"
    json_fields = ("master_index_ciks", "archive_path_ciks", "all_candidate_ciks")
    compare_fields = (
        "header_accession", "accession_match", "header_form", "form_match",
        "header_filing_date", "filing_date_match", "subject_cik", "filer_cik",
        "candidate_role", "xml_present", "xml_subject_cik", "xml_filer_cik",
        "xml_subject_matches_header", "xml_filer_matches_header", "xml_form_matches_header",
    )

    for sample in manifest:
        accession = sample["accession"]
        prior = prior_by_accession.get(accession, {})
        raw_path = raw_dir / f"{accession}.txt"
        if not raw_path.is_file():
            errors.append({"accession": accession, "error": "raw_submission_missing"})
            continue
        raw = raw_path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        row = dict(sample)
        for field in json_fields:
            row[field] = parse_json(row.get(field), [])
        try:
            parsed = parse_pilot_record(row, raw)
        except Exception as exc:
            errors.append({"accession": accession, "error": repr(exc)})
            continue

        for field in (
            "sample_stratum", "candidate_class", "form_family", "is_amendment",
            "timing_regime", "population_stratum_n", "phase83_sample_n",
            "phase83_subject_target_n", "phase83_filer_only_n",
            "phase84_sample_stratum_n",
        ):
            parsed[field] = row.get(field)
        parsed.update(target_role_flags(
            parsed, target_ciks, row.get("candidate_class") != "control"
        ))
        parsed["candidate_role_resolved"] = candidate_role_resolved(parsed)
        parsed["acceptance_utc"] = acceptance_to_utc(parsed.get("acceptance_datetime", ""))
        parsed["acceptance_timestamp_valid"] = bool(parsed["acceptance_utc"])

        retrieved = prior.get("retrieved_at_utc", "")
        try:
            datetime.fromisoformat(retrieved)
            retrieval_valid = True
        except (TypeError, ValueError):
            retrieval_valid = False
        prior_digest = prior.get("source_sha256", "")
        try:
            prior_bytes = int(float(prior.get("source_bytes") or 0))
        except (TypeError, ValueError):
            prior_bytes = 0
        try:
            http_status = int(float(prior.get("source_http_status") or 0))
        except (TypeError, ValueError):
            http_status = 0

        parsed.update({
            "retrieved_at_utc": retrieved,
            "retrieval_timestamp_valid": retrieval_valid,
            "source_http_status": http_status,
            "source_content_type": prior.get("source_content_type", ""),
            "source_url": prior.get("source_url", ""),
            "resolved_archive_path_cik": prior.get("resolved_archive_path_cik", ""),
            "archive_path_attempt_errors_json": prior.get("archive_path_attempt_errors_json", "[]"),
            "source_bytes": len(raw),
            "source_sha256": digest,
            "source_sha256_valid": bool(len(prior_digest) == 64 and digest == prior_digest),
            "raw_file": f"raw_submissions/{accession}.txt",
            "raw_submission_saved": bool(len(raw) == prior_bytes and len(raw) > 0),
        })

        for field in compare_fields:
            old = prior.get(field, "")
            new = parsed.get(field, "")
            if field in {
                "accession_match", "form_match", "filing_date_match",
                "xml_present", "xml_subject_matches_header",
                "xml_filer_matches_header", "xml_form_matches_header",
            }:
                equal = as_bool(old) == as_bool(new)
            else:
                equal = str(old or "") == str(new or "")
            if not equal:
                consistency_errors.append({
                    "accession": accession, "field": field,
                    "artifact_value": old, "replay_value": new,
                })
        parsed["replay_consistent"] = not any(
            e["accession"] == accession for e in consistency_errors
        )
        parsed_rows.append(parsed)

    parsed_by_accession = {r["accession"]: r for r in parsed_rows}
    expected_xml_accessions = expected_mandatory_xml_accessions(manifest, parsed_by_accession)
    present_xml_accessions = {
        r["accession"] for r in parsed_rows
        if r["accession"] in expected_xml_accessions and r.get("xml_present") is True
    }
    missing_xml_accessions = sorted(expected_xml_accessions - present_xml_accessions)

    n_sample, n = len(manifest), len(parsed_rows)
    candidate_rows = [r for r in parsed_rows if r.get("candidate_target_hit")]
    unique_rows = [r for r in candidate_rows if r.get("candidate_class") == "unique_candidate"]
    ambiguous_rows = [r for r in candidate_rows if r.get("candidate_class") == "ambiguous"]
    target_subject_rows = [r for r in parsed_rows if r.get("subject_target_hit")]
    xml_rows = [r for r in parsed_rows if r.get("xml_present") is True]

    def rate(rows, field, denominator=None):
        denom = denominator if denominator is not None else len(rows)
        return sum(bool(r.get(field)) for r in rows) / denom if denom else 0.0

    header_rate = sum(bool(r.get("header_accession")) for r in parsed_rows) / n_sample if n_sample else 0.0
    accession_rate = rate(parsed_rows, "accession_match", n_sample)
    form_rate = rate(parsed_rows, "form_match", n_sample)
    date_rate = rate(parsed_rows, "filing_date_match", n_sample)
    subject_cik_rate = sum(bool(r.get("subject_cik")) for r in parsed_rows) / n_sample if n_sample else 0.0
    filer_cik_rate = sum(bool(r.get("filer_cik")) for r in parsed_rows) / n_sample if n_sample else 0.0
    target_index_recall = rate(target_subject_rows, "subject_target_index_covered")
    candidate_role_rate = rate(candidate_rows, "candidate_role_resolved")
    xml_subject_rate = rate(xml_rows, "xml_subject_matches_header")
    xml_filer_rate = rate(xml_rows, "xml_filer_matches_header")
    xml_required_rate = len(present_xml_accessions) / len(expected_xml_accessions) if expected_xml_accessions else 0.0
    acceptance_rate = rate(parsed_rows, "acceptance_timestamp_valid", n_sample)
    raw_integrity_rate = sum(
        bool(r.get("raw_submission_saved") and r.get("source_sha256_valid") and r.get("retrieval_timestamp_valid"))
        for r in parsed_rows
    ) / n_sample if n_sample else 0.0
    http_200_rate = sum(r.get("source_http_status") == 200 for r in parsed_rows) / n_sample if n_sample else 0.0
    replay_consistency_rate = sum(bool(r.get("replay_consistent")) for r in parsed_rows) / n_sample if n_sample else 0.0

    filer_only_false_positives = sum(bool(r.get("filer_only_target_hit")) for r in candidate_rows)
    unresolved_rows = sum(not bool(r.get("candidate_role_resolved")) for r in candidate_rows)
    subject_candidate_misses = sum(bool(r.get("subject_target_candidate_missed")) for r in parsed_rows)

    weighted_source = prior_summary.get("weighted_role_estimate", {})
    population = Counter()
    phase83_roles = {}
    for item in weighted_source.get("strata", []):
        key = item["sample_stratum"]
        population[key] = int(item["population_n"])
        phase83_roles[key] = {
            "n83": int(item["phase83_n"]),
            "subject_target_n": int(item["phase83_subject_target_n"]),
            "filer_only_n": int(item["phase83_filer_only_n"]),
        }
    weighted = weighted_role_estimate(parsed_rows, population, phase83_roles)

    gate_checks = {
        "all_sample_rows_retrieved": n == n_sample and not errors,
        "header_parse_ge_99_5pct": header_rate >= 0.995,
        "accession_form_date_concordance_ge_99_5pct": min(accession_rate, form_rate, date_rate) >= 0.995,
        "subject_and_filer_cik_presence_ge_99_5pct": subject_cik_rate >= 0.995 and filer_cik_rate >= 0.995,
        "target_subject_index_recall_ge_99_5pct": bool(target_subject_rows) and target_index_recall >= 0.995,
        "no_target_subjects_missed_by_index_candidate_set": subject_candidate_misses == 0,
        "candidate_roles_resolved_ge_99_5pct": bool(candidate_rows) and candidate_role_rate >= 0.995,
        "mandatory_xml_present_ge_99_5pct": bool(expected_xml_accessions) and xml_required_rate >= 0.995,
        "xml_subject_filer_concordance_ge_99_5pct": bool(xml_rows) and min(xml_subject_rate, xml_filer_rate) >= 0.995,
        "acceptance_timestamp_valid_ge_99_5pct": acceptance_rate >= 0.995,
        "raw_hash_and_retrieval_utc_ge_99_5pct": raw_integrity_rate >= 0.995,
        "source_http_200_ge_99_5pct": http_200_rate >= 0.995,
        "offline_replay_matches_original_parse_ge_99_5pct": replay_consistency_rate >= 0.995,
    }
    summary = {
        "phase": "89-phase84-offline-artifact-replay",
        "status": "COMPLETE" if n == n_sample else "PARTIAL",
        "source_run_id": args.source_run_id,
        "source_artifact_id": args.source_artifact_id,
        "sample_rows_requested": n_sample,
        "sample_rows_replayed": n,
        "raw_replay_errors": errors,
        "replay_consistency_errors": consistency_errors[:100],
        "replay_consistency_error_count": len(consistency_errors),
        "replay_consistency_rate": replay_consistency_rate,
        "target_cik_count": len(target_ciks),
        "candidate_rows": len(candidate_rows),
        "unique_candidate_rows": len(unique_rows),
        "ambiguous_candidate_rows": len(ambiguous_rows),
        "target_subject_rows": len(target_subject_rows),
        "target_subject_index_recall": target_index_recall,
        "target_subject_candidate_misses": subject_candidate_misses,
        "unique_candidate_subject_role_rate": rate(unique_rows, "subject_target_hit"),
        "ambiguous_candidate_subject_role_rate": rate(ambiguous_rows, "subject_target_hit"),
        "filer_only_candidate_false_positives": filer_only_false_positives,
        "filer_only_false_positive_rate": filer_only_false_positives / len(candidate_rows) if candidate_rows else 0.0,
        "unresolved_candidate_rows": unresolved_rows,
        "header_parse_rate": header_rate,
        "accession_concordance": accession_rate,
        "form_concordance": form_rate,
        "filing_date_concordance": date_rate,
        "subject_cik_presence": subject_cik_rate,
        "filer_cik_presence": filer_cik_rate,
        "xml_rows": len(xml_rows),
        "xml_subject_header_concordance": xml_subject_rate,
        "xml_filer_header_concordance": xml_filer_rate,
        "mandatory_xml_rows": len(expected_xml_accessions),
        "mandatory_xml_present_rows": len(present_xml_accessions),
        "mandatory_xml_missing_accessions": missing_xml_accessions,
        "mandatory_xml_presence_rate": xml_required_rate,
        "acceptance_timestamp_valid_rate": acceptance_rate,
        "raw_hash_and_retrieval_utc_rate": raw_integrity_rate,
        "source_http_200_rate": http_200_rate,
        "weighted_role_estimate": weighted,
        "gate_checks": gate_checks,
        "data_gate": "PASS" if all(gate_checks.values()) else "FAIL",
        "original_run_conclusion": "failure caused by XML denominator counting one SC TO-T/A tender-offer filing as mandatory Schedule 13D/G XML",
        "forward_returns_used": False,
        "economic_test_authorized": False,
        "production_changes_authorized": False,
        "knowledge_time_rule": "SEC-HEADER ACCEPTANCE-DATETIME interpreted as America/New_York and converted to UTC; economic testing must use a conservative next-session availability rule unless dissemination time is independently verified.",
        "limitations": [
            "The 319 CIKs are current candidate identifiers, not historical F80 security lineage or PIT membership.",
            "Index/path candidates must be role-resolved; filer-only candidates are not subject-issuer events.",
            "The weighted estimate is descriptive and has no inferential confidence interval.",
            "No event normalization, forward-return test, alpha inference, feature tuning or production change is authorized.",
        ],
    }
    (outdir / "phase89_replay_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    with (outdir / "replayed_rows.csv").open("w", newline="", encoding="utf-8") as handle:
        if parsed_rows:
            fields = list(dict.fromkeys(k for r in parsed_rows for k in r))
            writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            for row in parsed_rows:
                writer.writerow({
                    k: json.dumps(v, sort_keys=True) if isinstance(v, (list, dict)) else v
                    for k, v in row.items()
                })
    print(json.dumps(summary, indent=2), flush=True)
    if summary["data_gate"] != "PASS":
        raise SystemExit(2)
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--target-cik-file", type=Path, required=True)
    parser.add_argument("--outdir", type=Path, default=Path("phase89_phase84_offline_replay"))
    parser.add_argument("--source-run-id", default="41914491120")
    parser.add_argument("--source-artifact-id", default="13364856424")
    run(parser.parse_args())


if __name__ == "__main__":
    main()

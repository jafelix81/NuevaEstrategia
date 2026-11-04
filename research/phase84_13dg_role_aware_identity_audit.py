#!/usr/bin/env python3
"""Role-aware, disjoint SEC 13D/13G identity validation using the frozen Phase 82 index."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from research.phase73_sec_submission_text_extractor import normalize_cik
from research.phase74_13dg_global_subject_audit import (
    SecClient, normalize_form, parse_pilot_record, submission_url_candidates, timing_regime,
)

JSON_FIELDS = (
    "master_index_ciks", "master_index_names", "archive_path_ciks",
    "candidate_identity_ciks", "master_candidate_ciks", "path_candidate_ciks",
    "all_candidate_ciks", "filenames",
)


def parse_bool(value):
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "y"}


def parse_json_field(value, default):
    if isinstance(value, (list, dict)):
        return value
    if not str(value or "").strip():
        return default
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return default


def load_csv(path):
    with Path(path).open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = list(dict.fromkeys(k for row in rows for k in row))
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            clean = {
                key: json.dumps(value, sort_keys=True) if isinstance(value, (list, dict)) else value
                for key, value in row.items()
            }
            writer.writerow(clean)


def acceptance_to_utc(value):
    raw = str(value or "").strip()
    if not re.fullmatch(r"\d{14}", raw):
        return ""
    local = datetime.strptime(raw, "%Y%m%d%H%M%S").replace(
        tzinfo=ZoneInfo("America/New_York")
    )
    return local.astimezone(timezone.utc).isoformat()


def candidate_role_resolved(row):
    candidates = row.get("all_candidate_ciks") or []
    unresolved = row.get("unresolved_candidate_ciks") or []
    if not candidates:
        return True
    return not unresolved and row.get("candidate_role") in {"subject", "filer", "ambiguous_subject"}


def mandatory_xml_expected(header_form, filing_date):
    """Use the actual SEC-HEADER form/date, not only the master-index family."""
    form = normalize_form(header_form)
    if form not in {"SC 13D", "SC 13D/A", "SC 13G", "SC 13G/A"}:
        return False
    family = "13D" if "13D" in form else "13G"
    return timing_regime(family, filing_date).endswith("mandatory_xml")


def target_role_flags(parsed, target_ciks, candidate_target):
    subject = normalize_cik(parsed.get("subject_cik", ""))
    filer = normalize_cik(parsed.get("filer_cik", ""))
    subject_target = bool(subject and subject in target_ciks)
    filer_target = bool(filer and filer in target_ciks)
    return {
        "subject_target_hit": subject_target,
        "filer_target_hit": filer_target,
        "candidate_target_hit": bool(candidate_target),
        "filer_only_target_hit": bool(candidate_target and filer_target and not subject_target),
        "both_subject_and_filer_target_hit": bool(candidate_target and subject_target and filer_target),
        "subject_target_index_covered": bool(
            subject_target and (
                parsed.get("subject_in_master_index_ciks")
                or parsed.get("subject_in_archive_path_ciks")
            )
        ),
        "subject_target_candidate_missed": bool(subject_target and not candidate_target),
    }


def build_manifest(candidate_index_file, phase83_accessions_file, phase83_roles_file, limit=600):
    source_rows = load_csv(candidate_index_file)
    phase83_accessions = {
        row["accession"] for row in load_csv(phase83_accessions_file)
    }
    phase83_roles = {
        row["sample_stratum"]: row for row in load_csv(phase83_roles_file)
    }

    population = Counter()
    strata = defaultdict(list)
    for source in source_rows:
        row = dict(source)
        for field in JSON_FIELDS:
            row[field] = parse_json_field(
                row.get(field), {} if field == "master_index_names" else []
            )
        row["is_amendment"] = parse_bool(row.get("is_amendment"))
        row["timing_regime"] = timing_regime(
            row.get("form_family", ""), row.get("filing_date", "")
        )
        stratum = "|".join((
            str(row.get("form_family", "")),
            str(bool(row["is_amendment"])),
            row["timing_regime"],
            str(row.get("candidate_class", "")),
        ))
        row["sample_stratum"] = stratum
        population[stratum] += 1
        if row["accession"] in phase83_accessions:
            continue
        row["phase84_sample_hash"] = hashlib.sha256(
            f"phase84|{row['accession']}|{stratum}".encode()
        ).hexdigest()
        strata[stratum].append(row)

    for values in strata.values():
        values.sort(key=lambda row: row["phase84_sample_hash"])

    selected = []
    offsets = {key: 0 for key in strata}
    for key in sorted(strata):
        offsets[key] = 0
    ordered_keys = sorted(strata)
    while len(selected) < limit:
        progressed = False
        for key in ordered_keys:
            pos = offsets[key]
            if pos < len(strata[key]) and len(selected) < limit:
                selected.append(dict(strata[key][pos]))
                offsets[key] += 1
                progressed = True
        if not progressed:
            break

    sample_counts = Counter(row["sample_stratum"] for row in selected)
    for row in selected:
        role = phase83_roles.get(row["sample_stratum"], {})
        row["population_stratum_n"] = population[row["sample_stratum"]]
        row["phase83_sample_n"] = int(role.get("n83") or 0)
        row["phase83_subject_target_n"] = int(role.get("subject_target_n") or 0)
        row["phase83_filer_only_n"] = int(role.get("filer_only_n") or 0)
        row["phase83_unresolved_n"] = int(role.get("unresolved_n") or 0)
        row["phase84_sample_stratum_n"] = sample_counts[row["sample_stratum"]]
        row["phase83_overlap_excluded"] = True

    if len(selected) != limit:
        raise RuntimeError(f"Expected {limit} disjoint sample rows, got {len(selected)}")
    if len({row["accession"] for row in selected}) != len(selected):
        raise RuntimeError("Duplicate accessions in Phase 84 sample")
    if any(row["accession"] in phase83_accessions for row in selected):
        raise RuntimeError("Phase 84 sample overlaps Phase 83")
    return selected, population, phase83_roles


def weighted_role_estimate(sample_rows, population, phase83_roles):
    by_stratum = defaultdict(list)
    for row in sample_rows:
        by_stratum[row["sample_stratum"]].append(row)
    candidate_population = 0
    estimated_subject = 0.0
    estimated_filer_only = 0.0
    strata_report = []
    for key, population_n in sorted(population.items()):
        class_name = key.split("|")[-1]
        rows = by_stratum.get(key, [])
        prior = phase83_roles.get(key, {})
        n83 = int(prior.get("n83") or 0)
        y83_subject = int(prior.get("subject_target_n") or 0)
        y83_filer = int(prior.get("filer_only_n") or 0)
        n84 = len(rows)
        y84_subject = sum(bool(row.get("subject_target_hit")) for row in rows)
        y84_filer = sum(bool(row.get("filer_only_target_hit")) for row in rows)
        combined_n = n83 + n84
        if class_name != "control":
            candidate_population += population_n
            if combined_n:
                estimated_subject += population_n * (y83_subject + y84_subject) / combined_n
                estimated_filer_only += population_n * (y83_filer + y84_filer) / combined_n
        strata_report.append({
            "sample_stratum": key,
            "candidate_class": class_name,
            "population_n": population_n,
            "phase83_n": n83,
            "phase84_n": n84,
            "combined_sample_n": combined_n,
            "combined_subject_target_n": y83_subject + y84_subject,
            "combined_filer_only_n": y83_filer + y84_filer,
        })
    return {
        "method": "post-stratified descriptive estimate; form family × amendment × timing regime × candidate class",
        "phase83_and_phase84_disjoint": True,
        "candidate_population_n": candidate_population,
        "estimated_subject_target_accessions": estimated_subject,
        "estimated_filer_only_false_positives": estimated_filer_only,
        "estimated_subject_share_of_candidate_population": (
            estimated_subject / candidate_population if candidate_population else None
        ),
        "estimated_filer_only_share_of_candidate_population": (
            estimated_filer_only / candidate_population if candidate_population else None
        ),
        "inferential_confidence_interval": None,
        "caveat": "Deterministic hash-stratified sample; descriptive feasibility estimate only, not alpha evidence.",
        "strata": strata_report,
    }


def run(args):
    outdir = Path(args.outdir)
    raw_dir = outdir / "raw_submissions"
    raw_dir.mkdir(parents=True, exist_ok=True)
    target_ciks = {
        normalize_cik(row.get("cik", ""))
        for row in load_csv(args.target_cik_file)
        if normalize_cik(row.get("cik", ""))
    }
    if not target_ciks:
        raise ValueError("Target CIK input is empty")

    sample, population, phase83_roles = build_manifest(
        args.candidate_index_file, args.phase83_accessions_file,
        args.phase83_roles_file, args.sample_limit,
    )
    write_csv(outdir / "sample_manifest.csv", sample)

    client = SecClient(sleep_seconds=args.sleep_seconds, max_retries=5, timeout=60)
    filing_rows, fetch_errors = [], []
    for index, row in enumerate(sample, start=1):
        resolved = None
        path_errors = []
        for archive_cik, url in submission_url_candidates(row):
            try:
                response = client.get_response(url)
                resolved = (archive_cik, url, response)
                break
            except Exception as exc:
                path_errors.append({
                    "archive_cik": archive_cik, "url": url, "error": repr(exc)
                })
        if resolved is None:
            fetch_errors.append({
                "accession": row["accession"],
                "sample_stratum": row["sample_stratum"],
                "path_errors": path_errors,
            })
            continue

        archive_cik, url, response = resolved
        raw = response.content
        parsed = parse_pilot_record(row, raw)
        retrieved = datetime.now(timezone.utc).isoformat()
        digest = hashlib.sha256(raw).hexdigest()
        raw_name = f"{row['accession']}.txt"
        raw_path = raw_dir / raw_name
        raw_path.write_bytes(raw)

        parsed["all_candidate_ciks"] = row["all_candidate_ciks"]
        parsed.update({
            "sample_stratum": row["sample_stratum"],
            "candidate_class": row["candidate_class"],
            "form_family": row["form_family"],
            "is_amendment": row["is_amendment"],
            "timing_regime": row["timing_regime"],
            "population_stratum_n": row["population_stratum_n"],
            "phase83_sample_n": row["phase83_sample_n"],
            "phase83_subject_target_n": row["phase83_subject_target_n"],
            "phase83_filer_only_n": row["phase83_filer_only_n"],
            "phase84_sample_stratum_n": row["phase84_sample_stratum_n"],
        })
        parsed.update(target_role_flags(
            parsed, target_ciks, row.get("candidate_class") != "control"
        ))
        acceptance_utc = acceptance_to_utc(parsed.get("acceptance_datetime", ""))
        parsed.update({
            "candidate_role_resolved": candidate_role_resolved(parsed),
            "acceptance_utc": acceptance_utc,
            "acceptance_timestamp_valid": bool(acceptance_utc),
            "retrieved_at_utc": retrieved,
            "retrieval_timestamp_valid": bool(datetime.fromisoformat(retrieved)),
            "source_url": url,
            "resolved_archive_path_cik": archive_cik,
            "source_http_status": response.status_code,
            "source_content_type": response.headers.get("Content-Type", ""),
            "source_bytes": len(raw),
            "source_sha256": digest,
            "source_sha256_valid": bool(re.fullmatch(r"[0-9a-f]{64}", digest)),
            "raw_file": f"raw_submissions/{raw_name}",
            "raw_submission_saved": raw_path.exists() and raw_path.stat().st_size == len(raw),
            "archive_path_attempt_errors_json": path_errors,
        })
        filing_rows.append(parsed)
        if index % 50 == 0:
            print(json.dumps({
                "progress": index, "sample": len(sample),
                "retrieved": len(filing_rows), "errors": len(fetch_errors),
                "sec_requests": client.request_count,
            }), flush=True)

    n_sample = len(sample)
    n = len(filing_rows)
    candidate_rows = [r for r in filing_rows if r["candidate_target_hit"]]
    unique_rows = [r for r in candidate_rows if r["candidate_class"] == "unique_candidate"]
    ambiguous_rows = [r for r in candidate_rows if r["candidate_class"] == "ambiguous"]
    target_subject_rows = [r for r in filing_rows if r["subject_target_hit"]]
    xml_rows = [r for r in filing_rows if r.get("xml_present") is True]
    parsed_by_accession = {r["accession"]: r for r in filing_rows}
    xml_required_accessions = set()
    for sample_row in sample:
        accession = sample_row["accession"]
        parsed = parsed_by_accession.get(accession)
        if parsed is not None:
            expected = mandatory_xml_expected(
                parsed.get("header_form", ""), parsed.get("header_filing_date", "")
            )
        else:
            # A failed retrieval remains in the denominator under its index-form expectation.
            expected = mandatory_xml_expected(
                sample_row.get("form", ""), sample_row.get("filing_date", "")
            )
        if expected:
            xml_required_accessions.add(accession)
    xml_required_rows = [
        r for r in filing_rows if r["accession"] in xml_required_accessions
    ]
    xml_required_fetched = [
        r for r in xml_required_rows if r.get("xml_present") is True
    ]
    xml_required_missing_accessions = sorted(
        xml_required_accessions - {r["accession"] for r in xml_required_fetched}
    )

    def rate(rows, field, denominator=None):
        denom = denominator if denominator is not None else len(rows)
        return sum(bool(row.get(field)) for row in rows) / denom if denom else 0.0

    header_parse_rate = sum(bool(r.get("header_accession")) for r in filing_rows) / n_sample if n_sample else 0.0
    accession_rate = rate(filing_rows, "accession_match", n_sample)
    form_rate = rate(filing_rows, "form_match", n_sample)
    date_rate = rate(filing_rows, "filing_date_match", n_sample)
    target_index_recall = rate(target_subject_rows, "subject_target_index_covered")
    candidate_role_rate = rate(candidate_rows, "candidate_role_resolved")
    xml_subject_rate = rate(xml_rows, "xml_subject_matches_header")
    xml_filer_rate = rate(xml_rows, "xml_filer_matches_header")
    xml_required_rate = len(xml_required_fetched) / len(xml_required_accessions) if xml_required_accessions else 0.0
    acceptance_rate = rate(filing_rows, "acceptance_timestamp_valid", n_sample)
    raw_integrity_rate = sum(
        bool(r.get("raw_submission_saved") and r.get("source_sha256_valid") and r.get("retrieval_timestamp_valid"))
        for r in filing_rows
    ) / n_sample if n_sample else 0.0
    http_200_rate = sum(r.get("source_http_status") == 200 for r in filing_rows) / n_sample if n_sample else 0.0

    unique_subject_rate = rate(unique_rows, "subject_target_hit")
    ambiguous_subject_rate = rate(ambiguous_rows, "subject_target_hit")
    filer_only_false_positives = sum(bool(r.get("filer_only_target_hit")) for r in candidate_rows)
    unresolved_rows = sum(not bool(r.get("candidate_role_resolved")) for r in candidate_rows)
    subject_candidate_misses = sum(bool(r.get("subject_target_candidate_missed")) for r in filing_rows)

    weighted = weighted_role_estimate(filing_rows, population, phase83_roles)
    gate_checks = {
        "all_sample_rows_retrieved": n == n_sample and not fetch_errors,
        "header_parse_ge_99_5pct": header_parse_rate >= 0.995,
        "accession_form_date_concordance_ge_99_5pct": min(accession_rate, form_rate, date_rate) >= 0.995,
        "subject_and_filer_cik_presence_ge_99_5pct": (
            rate(filing_rows, "subject_cik", n_sample) >= 0.995
            and rate(filing_rows, "filer_cik", n_sample) >= 0.995
        ),
        "target_subject_index_recall_ge_99_5pct": bool(target_subject_rows) and target_index_recall >= 0.995,
        "no_target_subjects_missed_by_index_candidate_set": subject_candidate_misses == 0,
        "candidate_roles_resolved_ge_99_5pct": bool(candidate_rows) and candidate_role_rate >= 0.995,
        "mandatory_xml_present_ge_99_5pct": bool(xml_required_rows) and xml_required_rate >= 0.995,
        "xml_subject_filer_concordance_ge_99_5pct": bool(xml_rows) and min(xml_subject_rate, xml_filer_rate) >= 0.995,
        "acceptance_timestamp_valid_ge_99_5pct": acceptance_rate >= 0.995,
        "raw_hash_and_retrieval_utc_ge_99_5pct": raw_integrity_rate >= 0.995,
        "source_http_200_ge_99_5pct": http_200_rate >= 0.995,
    }
    summary = {
        "phase": "84-13dg-role-aware-identity-validation",
        "status": "COMPLETE" if n == n_sample else "PARTIAL",
        "sample_rows_requested": n_sample,
        "sample_rows_retrieved": n,
        "fetch_errors": len(fetch_errors),
        "sec_request_count": client.request_count,
        "target_cik_count": len(target_ciks),
        "candidate_rows": len(candidate_rows),
        "unique_candidate_rows": len(unique_rows),
        "ambiguous_candidate_rows": len(ambiguous_rows),
        "target_subject_rows": len(target_subject_rows),
        "target_subject_index_recall": target_index_recall,
        "target_subject_candidate_misses": subject_candidate_misses,
        "unique_candidate_subject_role_rate": unique_subject_rate,
        "ambiguous_candidate_subject_role_rate": ambiguous_subject_rate,
        "filer_only_candidate_false_positives": filer_only_false_positives,
        "filer_only_false_positive_rate": (
            filer_only_false_positives / len(candidate_rows) if candidate_rows else 0.0
        ),
        "unresolved_candidate_rows": unresolved_rows,
        "header_parse_rate": header_parse_rate,
        "accession_concordance": accession_rate,
        "form_concordance": form_rate,
        "filing_date_concordance": date_rate,
        "subject_cik_presence": rate(filing_rows, "subject_cik", n_sample),
        "filer_cik_presence": rate(filing_rows, "filer_cik", n_sample),
        "xml_rows": len(xml_rows),
        "xml_subject_header_concordance": xml_subject_rate,
        "xml_filer_header_concordance": xml_filer_rate,
        "mandatory_xml_rows": len(xml_required_accessions),
        "mandatory_xml_present_rows": len(xml_required_fetched),
        "mandatory_xml_missing_accessions": xml_required_missing_accessions,
        "mandatory_xml_presence_rate": xml_required_rate,
        "acceptance_timestamp_valid_rate": acceptance_rate,
        "raw_hash_and_retrieval_utc_rate": raw_integrity_rate,
        "source_http_200_rate": http_200_rate,
        "raw_submission_files_saved": sum(bool(r.get("raw_submission_saved")) for r in filing_rows),
        "weighted_role_estimate": weighted,
        "gate_checks": gate_checks,
        "data_gate": "PASS" if all(gate_checks.values()) else "FAIL",
        "forward_returns_used": False,
        "economic_test_authorized": False,
        "production_changes_authorized": False,
        "knowledge_time_rule": "SEC-HEADER ACCEPTANCE-DATETIME interpreted as America/New_York and converted to UTC; economic testing must apply a conservative next-session availability rule unless public dissemination time is independently verified.",
        "limitations": [
            "Current 319 CIK candidates are not historical F80 security lineage or a PIT membership ledger.",
            "Header subject/filer roles resolve candidate false positives but do not establish informed or predictive behavior.",
            "The weighted role estimate is descriptive; deterministic hash sampling does not provide a formal inferential confidence interval.",
            "No forward returns, alpha inference, feature tuning or production changes are authorized.",
        ],
    }

    write_csv(outdir / "pilot_header_validation.csv", filing_rows)
    write_csv(outdir / "pilot_errors.csv", fetch_errors)
    (outdir / "pilot_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    (outdir / "summary.json").write_text(json.dumps({
        "phase84": summary,
        "phase83_sample_accessions_excluded": len(load_csv(args.phase83_accessions_file)),
        "phase82_index_snapshot": "run 41892370262 / artifact 13353118959",
    }, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2), flush=True)
    if summary["data_gate"] != "PASS":
        raise SystemExit(2)
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-index-file", type=Path, required=True)
    parser.add_argument("--target-cik-file", type=Path, required=True)
    parser.add_argument("--phase83-accessions-file", type=Path, required=True)
    parser.add_argument("--phase83-roles-file", type=Path, required=True)
    parser.add_argument("--sample-limit", type=int, default=600)
    parser.add_argument("--outdir", type=Path, default=Path("phase84_13dg_role_aware_identity"))
    parser.add_argument("--sleep-seconds", type=float, default=0.8)
    run(parser.parse_args())


if __name__ == "__main__":
    main()

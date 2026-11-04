#!/usr/bin/env python3
"""Offline event-semantics audit of the Phase 84 13D/13G raw-submission sample."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from datetime import date, datetime
import statistics
from pathlib import Path

from research.phase72_13dg_structured_xml_parser import parse_schedule13_xml
from research.phase73_sec_submission_text_extractor import extract_primary_doc_xml, normalize_cik
from research.phase74_13dg_global_subject_audit import (
    normalize_accession, normalize_form, parse_pilot_record,
)
from research.phase84_13dg_role_aware_identity_audit import (
    acceptance_to_utc, mandatory_xml_expected,
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


def event_lag_days(event_date, filing_date):
    def parse_date(value):
        value = str(value or "").strip()
        for fmt in ("%Y-%m-%d", "%m/%d/%Y"):
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                pass
        return None
    event = parse_date(event_date)
    filing = parse_date(filing_date)
    if event is None or filing is None:
        return None
    return (filing - event).days


def previous_accession_field_status(raw):
    text = raw.decode("utf-8-sig", errors="replace") if isinstance(raw, bytes) else str(raw)
    tag = r"(?:[A-Za-z0-9_.-]+:)?previousAccessionNumber"
    match = re.search(rf"<{tag}\b[^>]*>(.*?)</{tag}\s*>", text, re.I | re.S)
    if match:
        return "field_nonempty" if match.group(1).strip() else "field_empty"
    if re.search(rf"<{tag}\b[^>]*/>", text, re.I | re.S):
        return "field_empty"
    return "field_absent"


def count_element_occurrences(raw, element_name):
    text = raw.decode("utf-8-sig", errors="replace") if isinstance(raw, bytes) else str(raw)
    tag = re.escape(element_name)
    return len(re.findall(rf"<(?:[A-Za-z0-9_.-]+:)?{tag}\b", text, re.I))


def lag_summary(records):
    values = [r["event_date_lag_days"] for r in records if r.get("event_date_lag_days") is not None]
    if not values:
        return {"n": 0, "min": None, "median": None, "max": None}
    return {
        "n": len(values),
        "min": min(values),
        "median": statistics.median(values),
        "max": max(values),
    }


def classify_predecessor(current, previous_accession, all_by_accession):
    previous = normalize_accession(previous_accession)
    is_amendment = bool(current.get("is_amendment"))
    if not previous:
        return "amendment_missing_predecessor" if is_amendment else "original_no_predecessor"
    if not re.fullmatch(r"\d{10}-\d{2}-\d{6}", previous):
        return "predecessor_invalid_format"
    prior = all_by_accession.get(previous)
    if prior is None:
        return "predecessor_outside_sample"
    if prior.get("subject_cik") != current.get("subject_cik"):
        return "predecessor_subject_mismatch"
    if prior.get("form_family") != current.get("form_family"):
        return "predecessor_family_mismatch"
    if not prior.get("filing_date") or not current.get("filing_date") or prior["filing_date"] >= current["filing_date"]:
        return "predecessor_not_earlier"
    return "predecessor_in_sample_consistent"


def run(args):
    artifact_dir = Path(args.artifact_dir)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    manifest = load_csv(artifact_dir / "sample_manifest.csv")
    prior_rows = load_csv(artifact_dir / "pilot_header_validation.csv")
    prior_by_accession = {r["accession"]: r for r in prior_rows}
    raw_dir = artifact_dir / "raw_submissions"

    base_rows = []
    raw_errors = []
    for sample in manifest:
        accession = sample["accession"]
        prior = prior_by_accession.get(accession, {})
        raw_path = raw_dir / f"{accession}.txt"
        if not raw_path.is_file():
            raw_errors.append({"accession": accession, "error": "raw_submission_missing"})
            continue
        raw = raw_path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if digest != prior.get("source_sha256", ""):
            raw_errors.append({"accession": accession, "error": "raw_sha256_mismatch"})
            continue
        row = dict(sample)
        for field in ("all_candidate_ciks", "master_index_ciks", "archive_path_ciks"):
            row[field] = parse_json(row.get(field), [])
        try:
            header = parse_pilot_record(row, raw)
        except Exception as exc:
            raw_errors.append({"accession": accession, "error": repr(exc)})
            continue
        family = "13D" if "13D" in header.get("header_form", "") else (
            "13G" if "13G" in header.get("header_form", "") else ""
        )
        retrieved = prior.get("retrieved_at_utc", "")
        base_rows.append({
            "accession": accession,
            "index_form": normalize_form(sample.get("form", "")),
            "header_form": header.get("header_form", ""),
            "form_family": family,
            "form_match": bool(header.get("form_match")),
            "filing_date": header.get("header_filing_date", ""),
            "subject_cik": normalize_cik(header.get("subject_cik", "")),
            "filer_cik": normalize_cik(header.get("filer_cik", "")),
            "acceptance_datetime": header.get("acceptance_datetime", ""),
            "acceptance_utc": acceptance_to_utc(header.get("acceptance_datetime", "")),
            "acceptance_timestamp_valid": bool(acceptance_to_utc(header.get("acceptance_datetime", ""))),
            "is_amendment": header.get("header_form", "").endswith("/A"),
            "xml_present_in_phase84": bool(header.get("xml_present")),
            "raw_sha256_valid": True,
            "retrieved_at_utc": retrieved,
            "source_http_status": int(float(prior.get("source_http_status") or 0)),
            "sample_stratum": sample.get("sample_stratum", ""),
        })

    all_by_accession = {r["accession"]: r for r in base_rows}
    xml_records = []
    for base in base_rows:
        accession = base["accession"]
        raw = (raw_dir / f"{accession}.txt").read_bytes()
        try:
            extracted = extract_primary_doc_xml(raw)
            parsed = parse_schedule13_xml(extracted["xml_bytes"])
        except Exception as exc:
            if base["xml_present_in_phase84"]:
                raw_errors.append({"accession": accession, "error": f"xml_replay_failed:{exc!r}"})
            continue

        xml_family = parsed.get("form_family", "")
        xml_submission_type = normalize_form(parsed.get("submission_type", ""))
        header_subject_match = bool(parsed.get("issuer_cik") and parsed.get("issuer_cik") == base["subject_cik"])
        header_filer_match = bool(parsed.get("filer_cik_xml") and parsed.get("filer_cik_xml") == base["filer_cik"])
        header_form_match = bool(xml_submission_type and xml_submission_type == base["header_form"])
        persons = parsed.get("reporting_persons") or []
        person_status = Counter(p.get("person_cik_status", "") for p in persons)
        cik_element_counts = {
            tag: count_element_occurrences(raw, tag)
            for tag in ("reportingPersonCIK", "reportingPersonNoCIK", "reportingCik", "reportingCikNotPresentInEdgarFlag")
        }
        person_ciks = [p.get("person_cik") for p in persons if p.get("person_cik")]
        previous = parsed.get("previous_accession_number", "")
        event_date = parsed.get("event_date", "")
        lag = event_lag_days(event_date, base["filing_date"])
        record = {
            **base,
            "xml_parse_success": True,
            "xml_form_family": xml_family,
            "xml_submission_type": parsed.get("submission_type", ""),
            "xml_subject_cik": parsed.get("issuer_cik", ""),
            "xml_filer_cik": parsed.get("filer_cik_xml", ""),
            "xml_subject_header_match": header_subject_match,
            "xml_filer_header_match": header_filer_match,
            "xml_form_header_match": header_form_match,
            "event_date": event_date,
            "event_date_lag_days": lag,
            "event_date_missing": not bool(event_date),
            "event_date_after_filing": lag is not None and lag < 0,
            "amendment_number": parsed.get("amendment_number", ""),
            "previous_accession_number": normalize_accession(previous),
            "previous_accession_format_valid": not previous or bool(normalize_accession(previous)),
            "previous_accession_field_status": previous_accession_field_status(raw),
            "predecessor_status": "",
            "reporting_person_count": len(persons),
            "reporting_person_cik_count": len(person_ciks),
            "reporting_person_cik_unique_count": len(set(person_ciks)),
            "reporting_person_cik_status_counts": dict(person_status),
            "reporting_cik_element_counts": cik_element_counts,
            "reporting_persons": persons,
            "cusips": parsed.get("cusips", []),
            "rule_designations": parsed.get("rule_designations", []),
            "purpose_text_present": bool(parsed.get("purpose_text")),
            "group_members_narrative_present": bool(parsed.get("group_members_narrative")),
            "filing_person_name_narrative": parsed.get("filing_person_name_narrative", ""),
            "lineage_status_parser": parsed.get("lineage_status", ""),
        }
        xml_records.append(record)

    xml_by_accession = {r["accession"]: r for r in xml_records}
    for record in xml_records:
        record["predecessor_status"] = classify_predecessor(
            record, record.get("previous_accession_number", ""), all_by_accession
        )

    prior_xml_accessions = {
        r["accession"] for r in prior_rows
        if str(r.get("xml_present", "")).strip().lower() == "true"
    }
    mandatory_accessions = {
        r["accession"] for r in base_rows
        if mandatory_xml_expected(r.get("header_form", ""), r.get("filing_date", ""))
    }
    mandatory_present = mandatory_accessions & set(xml_by_accession)
    n_xml_expected = len(prior_xml_accessions)
    n_xml_parsed = len(xml_records)
    identity_subject = sum(bool(r["xml_subject_header_match"]) for r in xml_records)
    identity_filer = sum(bool(r["xml_filer_header_match"]) for r in xml_records)
    identity_form = sum(bool(r["xml_form_header_match"]) for r in xml_records)
    acceptance_valid = sum(bool(r["acceptance_timestamp_valid"]) for r in base_rows)
    hash_valid = sum(bool(r["raw_sha256_valid"]) for r in base_rows)

    amendments = [r for r in xml_records if r["is_amendment"]]
    originals = [r for r in xml_records if not r["is_amendment"]]
    predecessor_counts = Counter(r["predecessor_status"] for r in xml_records)
    person_status_counts = Counter()
    person_counts = []
    for record in xml_records:
        person_counts.append(record["reporting_person_count"])
        person_status_counts.update(record["reporting_person_cik_status_counts"])

    event_lags = [r["event_date_lag_days"] for r in xml_records if r["event_date_lag_days"] is not None]
    family_counts = Counter(r["form_family"] for r in xml_records)
    amendment_missing_by_family = {
        family: sum(not bool(r.get("previous_accession_number")) for r in amendments if r["form_family"] == family)
        for family in ("13D", "13G")
    }
    amendment_total_by_family = {
        family: sum(1 for r in amendments if r["form_family"] == family)
        for family in ("13D", "13G")
    }
    amendment_field_status_counts = Counter(
        r.get("previous_accession_field_status", "") for r in amendments
    )
    amendment_field_status_by_family = {
        family: dict(Counter(r.get("previous_accession_field_status", "") for r in amendments if r["form_family"] == family))
        for family in ("13D", "13G")
    }
    person_status_by_family = {}
    person_count_by_family = {}
    cik_elements_by_family = {}
    for family in ("13D", "13G"):
        family_records = [r for r in xml_records if r["form_family"] == family]
        family_persons = [p for r in family_records for p in r["reporting_persons"]]
        person_status_by_family[family] = dict(Counter(p.get("person_cik_status", "") for p in family_persons))
        family_counts_persons = [len(r["reporting_persons"]) for r in family_records]
        person_count_by_family[family] = {
            "filings": len(family_records),
            "reporting_persons": len(family_persons),
            "mean_per_filing": sum(family_counts_persons) / len(family_counts_persons) if family_counts_persons else 0.0,
            "max_per_filing": max(family_counts_persons) if family_counts_persons else 0,
        }
        cik_elements_by_family[family] = dict(Counter(
            tag
            for r in family_records
            for tag, count in r["reporting_cik_element_counts"].items()
            for _ in range(count)
        ))
    event_lag_by_family = {
        family: lag_summary([r for r in xml_records if r["form_family"] == family])
        for family in ("13D", "13G")
    }
    event_lag_by_amendment = {
        str(flag): lag_summary([r for r in xml_records if r["is_amendment"] == flag])
        for flag in (False, True)
    }
    summary = {
        "phase": "90-13dg-event-semantics-pilot",
        "status": "COMPLETE" if len(base_rows) == len(manifest) else "PARTIAL",
        "source_run_id": args.source_run_id,
        "sample_rows_requested": len(manifest),
        "sample_rows_replayed": len(base_rows),
        "raw_integrity_errors": raw_errors,
        "xml_rows_expected_from_phase84": n_xml_expected,
        "xml_rows_reparsed": n_xml_parsed,
        "xml_parse_coverage": n_xml_parsed / n_xml_expected if n_xml_expected else 0.0,
        "mandatory_xml_rows": len(mandatory_accessions),
        "mandatory_xml_present": len(mandatory_present),
        "mandatory_xml_missing_accessions": sorted(mandatory_accessions - mandatory_present),
        "xml_subject_header_concordance": identity_subject / n_xml_parsed if n_xml_parsed else 0.0,
        "xml_filer_header_concordance": identity_filer / n_xml_parsed if n_xml_parsed else 0.0,
        "xml_form_header_concordance": identity_form / n_xml_parsed if n_xml_parsed else 0.0,
        "acceptance_timestamp_valid_rate": acceptance_valid / len(base_rows) if base_rows else 0.0,
        "raw_sha256_valid_rate": hash_valid / len(base_rows) if base_rows else 0.0,
        "form_family_counts": dict(family_counts),
        "amendments_with_xml": len(amendments),
        "originals_with_xml": len(originals),
        "amendments_with_predecessor": sum(bool(r.get("previous_accession_number")) for r in amendments),
        "amendments_missing_predecessor": sum(not bool(r.get("previous_accession_number")) for r in amendments),
        "amendments_missing_predecessor_by_family": amendment_missing_by_family,
        "amendments_total_by_family": amendment_total_by_family,
        "amendment_previous_accession_field_status_counts": dict(amendment_field_status_counts),
        "amendment_previous_accession_field_status_by_family": amendment_field_status_by_family,
        "predecessor_status_counts": dict(predecessor_counts),
        "reporting_person_total": sum(person_counts),
        "reporting_person_count_by_family": person_count_by_family,
        "reporting_person_cik_status_by_family": person_status_by_family,
        "reporting_cik_element_occurrences_by_family": cik_elements_by_family,
        "reporting_person_count_mean": sum(person_counts) / len(person_counts) if person_counts else 0.0,
        "reporting_person_count_max": max(person_counts) if person_counts else 0,
        "reporting_person_cik_status_counts": dict(person_status_counts),
        "event_date_present_rows": sum(not r["event_date_missing"] for r in xml_records),
        "event_date_missing_rows": sum(bool(r["event_date_missing"]) for r in xml_records),
        "event_date_after_filing_rows": sum(bool(r["event_date_after_filing"]) for r in xml_records),
        "event_date_lag_days_min": min(event_lags) if event_lags else None,
        "event_date_lag_days_median": statistics.median(event_lags) if event_lags else None,
        "event_date_lag_days_max": max(event_lags) if event_lags else None,
        "event_date_lag_by_family": event_lag_by_family,
        "event_date_lag_by_amendment": event_lag_by_amendment,
        "purpose_text_present_13d": sum(bool(r["purpose_text_present"]) for r in xml_records if r["form_family"] == "13D"),
        "rule_designations_present_13g": sum(bool(r["rule_designations"]) for r in xml_records if r["form_family"] == "13G"),
        "gate_checks": {
            "all_600_raw_rows_replayed": len(base_rows) == len(manifest) and not raw_errors,
            "all_phase84_xml_rows_reparsed": n_xml_parsed == n_xml_expected,
            "mandatory_xml_coverage_100pct": len(mandatory_present) == len(mandatory_accessions),
            "xml_subject_header_100pct": n_xml_parsed > 0 and identity_subject == n_xml_parsed,
            "xml_filer_header_100pct": n_xml_parsed > 0 and identity_filer == n_xml_parsed,
            "xml_form_header_100pct": n_xml_parsed > 0 and identity_form == n_xml_parsed,
            "acceptance_timestamps_99_5pct": bool(base_rows) and acceptance_valid / len(base_rows) >= 0.995,
            "raw_sha256_99_5pct": bool(base_rows) and hash_valid / len(base_rows) >= 0.995,
        },
        "data_gate": "PASS" if (
            len(base_rows) == len(manifest) and not raw_errors
            and n_xml_parsed == n_xml_expected
            and len(mandatory_present) == len(mandatory_accessions)
            and n_xml_parsed > 0 and identity_subject == identity_filer == identity_form == n_xml_parsed
            and bool(base_rows) and acceptance_valid / len(base_rows) >= 0.995
            and hash_valid / len(base_rows) >= 0.995
        ) else "FAIL",
        "knowledge_time_rule": "SEC-HEADER ACCEPTANCE-DATETIME converted from America/New_York to UTC; event_date is a reported event field, never the signal availability timestamp.",
        "forward_returns_used": False,
        "economic_test_authorized": False,
        "production_changes_authorized": False,
        "limitations": [
            "Only 200 structured-XML filings from the 600-filing stratified sample are parsed; legacy pre-XML filings need a separate HTML/TXT normalization design.",
            "A predecessor not present in this small sample is not a failed link; it is classified as outside_sample.",
            "Event dates may be corrected in amendments and are not treated as contemporaneous knowledge dates.",
            "The 319 CIKs remain current candidates, not historical F80 security lineage or active-universe membership.",
            "No forward returns or predictive hypothesis are tested.",
        ],
    }

    (outdir / "phase90_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    with (outdir / "phase90_event_records.jsonl").open("w", encoding="utf-8") as handle:
        for record in xml_records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
    with (outdir / "phase90_event_records.csv").open("w", newline="", encoding="utf-8") as handle:
        if xml_records:
            fields = list(dict.fromkeys(k for r in xml_records for k in r if k != "reporting_persons"))
            writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            for record in xml_records:
                writer.writerow({
                    k: json.dumps(v, sort_keys=True) if isinstance(v, (list, dict)) else v
                    for k, v in record.items() if k != "reporting_persons"
                })
    print(json.dumps(summary, indent=2), flush=True)
    if summary["data_gate"] != "PASS":
        raise SystemExit(2)
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--outdir", type=Path, default=Path("phase90_13dg_event_semantics"))
    parser.add_argument("--source-run-id", default="41914491120")
    run(parser.parse_args())


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Offline audit of Schedule 13G first-person CIK semantics and rule-regime filing lags.

No SEC network requests, forward returns, feature construction, or alpha tests.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import statistics
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path

from research.phase72_13dg_structured_xml_parser import parse_schedule13_xml
from research.phase73_sec_submission_text_extractor import extract_primary_doc_xml, normalize_cik
from research.phase74_13dg_global_subject_audit import parse_pilot_record
from research.phase84_13dg_role_aware_identity_audit import acceptance_to_utc


def parse_json(value, default):
    if isinstance(value, (list, dict)):
        return value
    try:
        return json.loads(value) if str(value or "").strip() else default
    except (TypeError, ValueError):
        return default


def parse_date(value):
    value = str(value or "").strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            pass
    return None


def normalize_name(value):
    return re.sub(r"[^A-Z0-9]", "", str(value or "").upper())


def expected_timing_regime(family, filing_date):
    d = parse_date(filing_date)
    if d is None:
        return "unknown_date"
    if family == "13D":
        if d < date(2024, 2, 5):
            return "13d_legacy_deadline"
        if d < date(2024, 12, 18):
            return "13d_revised_deadline_pre_xml"
        return "13d_mandatory_xml"
    if family == "13G":
        if d < date(2024, 9, 30):
            return "13g_legacy_deadline"
        if d < date(2024, 12, 18):
            return "13g_revised_deadline_pre_xml"
        return "13g_mandatory_xml"
    return "unknown_family"


def parse_sample_stratum(value):
    parts = str(value or "").split("|")
    if len(parts) != 4:
        return {"family": "", "is_amendment": None, "timing_regime": "", "candidate_class": ""}
    raw_bool = parts[1].strip().lower()
    flag = True if raw_bool == "true" else False if raw_bool == "false" else None
    return {
        "family": parts[0].strip(),
        "is_amendment": flag,
        "timing_regime": parts[2].strip(),
        "candidate_class": parts[3].strip(),
    }


def classify_13g_person_identity(person, person_index, filer_cik, filer_name):
    """Return conservative identity class; never silently promote a filer CIK to a person CIK."""
    explicit = normalize_cik(person.get("person_cik", ""))
    no_cik_flag = str(person.get("person_no_cik_flag", "") or "").strip().upper()
    if explicit:
        return {"identity_status": "explicit_reporting_person_cik",
                "candidate_person_cik": explicit, "identity_resolved": True}
    if no_cik_flag == "Y":
        return {"identity_status": "declared_no_reporting_person_cik",
                "candidate_person_cik": "", "identity_resolved": True}
    if no_cik_flag == "N":
        return {"identity_status": "cik_expected_but_missing",
                "candidate_person_cik": "", "identity_resolved": False}
    if person_index == 0:
        same_name = bool(normalize_name(filer_name) and
                         normalize_name(filer_name) == normalize_name(person.get("name", "")))
        if same_name and normalize_cik(filer_cik):
            return {"identity_status": "first_person_filer_cik_candidate_name_match",
                    "candidate_person_cik": normalize_cik(filer_cik), "identity_resolved": False}
        return {"identity_status": "first_person_filer_cik_unverified",
                "candidate_person_cik": "", "identity_resolved": False}
    return {"identity_status": "additional_person_cik_unresolved",
            "candidate_person_cik": "", "identity_resolved": False}


def percentile(values, p):
    ordered = sorted(float(x) for x in values)
    if not ordered:
        return None
    if len(ordered) == 1:
        return ordered[0]
    pos = (len(ordered) - 1) * p
    lo, hi = int(pos), min(int(pos) + 1, len(ordered) - 1)
    weight = pos - lo
    return ordered[lo] * (1 - weight) + ordered[hi] * weight


def lag_stats(values):
    clean = [int(x) for x in values if x is not None]
    if not clean:
        return {"n": 0, "min": None, "p25": None, "median": None,
                "p75": None, "max": None, "pct_le_5": None,
                "pct_le_10": None, "pct_gt_45": None}
    return {
        "n": len(clean), "min": min(clean), "p25": percentile(clean, .25),
        "median": statistics.median(clean), "p75": percentile(clean, .75),
        "max": max(clean), "pct_le_5": sum(x <= 5 for x in clean) / len(clean),
        "pct_le_10": sum(x <= 10 for x in clean) / len(clean),
        "pct_gt_45": sum(x > 45 for x in clean) / len(clean),
    }


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
            writer.writerow({k: json.dumps(v, ensure_ascii=False, sort_keys=True)
                             if isinstance(v, (list, dict, tuple, set)) else v
                             for k, v in row.items()})


def run(args):
    artifact = Path(args.artifact_dir)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    manifest = load_csv(artifact / "sample_manifest.csv")
    header_rows = load_csv(artifact / "pilot_header_validation.csv")
    header_by_accession = {r.get("accession", ""): r for r in header_rows}
    raw_dir = artifact / "raw_submissions"
    errors, filing_rows, person_rows = [], [], []

    for sample in manifest:
        accession = sample.get("accession", "")
        prior = header_by_accession.get(accession, {})
        raw_path = raw_dir / f"{accession}.txt"
        if not raw_path.is_file():
            errors.append({"accession": accession, "error": "raw_submission_missing"})
            continue
        raw = raw_path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if digest != prior.get("source_sha256", ""):
            errors.append({"accession": accession, "error": "raw_sha256_mismatch"})
            continue
        row = dict(sample)
        for field in ("all_candidate_ciks", "master_index_ciks", "archive_path_ciks"):
            row[field] = parse_json(row.get(field), [])
        try:
            header = parse_pilot_record(row, raw)
        except Exception as exc:
            errors.append({"accession": accession, "error": f"header_parse:{exc!r}"})
            continue
        form = str(header.get("header_form", "")).upper()
        family = "13D" if "13D" in form else ("13G" if "13G" in form else "")
        if not family:
            continue
        try:
            extracted = extract_primary_doc_xml(raw)
            parsed = parse_schedule13_xml(extracted["xml_bytes"])
        except Exception as exc:
            errors.append({"accession": accession, "error": f"xml_parse:{exc!r}"})
            continue
        if parsed.get("form_family") != family:
            errors.append({"accession": accession, "error": "xml_header_family_mismatch"})
            continue

        filing_date = header.get("header_filing_date", "")
        event_date = parsed.get("event_date", "")
        event_dt, filing_dt = parse_date(event_date), parse_date(filing_date)
        lag = (filing_dt - event_dt).days if event_dt and filing_dt else None
        stratum = parse_sample_stratum(sample.get("sample_stratum", ""))
        regime = expected_timing_regime(family, filing_date)
        if stratum["family"] and stratum["family"] != family:
            errors.append({"accession": accession, "error": "sample_stratum_family_mismatch"})
        if stratum["timing_regime"] and stratum["timing_regime"] != regime:
            errors.append({"accession": accession, "error": "sample_stratum_regime_mismatch"})
        is_amendment = bool(form.endswith("/A"))
        if stratum["is_amendment"] is not None and stratum["is_amendment"] != is_amendment:
            errors.append({"accession": accession, "error": "sample_stratum_amendment_mismatch"})

        filer_cik = normalize_cik(header.get("filer_cik", ""))
        xml_filer_cik = normalize_cik(parsed.get("filer_cik_xml", ""))
        if not filer_cik or filer_cik != xml_filer_cik:
            errors.append({"accession": accession, "error": "xml_header_filer_cik_mismatch"})
        persons = parsed.get("reporting_persons") or []
        rule_designations = parsed.get("rule_designations") or []
        acceptance_utc = acceptance_to_utc(header.get("acceptance_datetime", ""))
        filing_rows.append({
            "accession": accession, "family": family, "form": form,
            "filing_date": filing_date, "event_date": event_date,
            "event_date_lag_days": lag, "is_amendment": is_amendment,
            "timing_regime": regime, "sample_candidate_class": stratum["candidate_class"],
            "rule_designations": rule_designations,
            "subject_cik": normalize_cik(header.get("subject_cik", "")),
            "filer_cik": filer_cik, "filer_name": header.get("filer_name", ""),
            "xml_subject_cik": normalize_cik(parsed.get("issuer_cik", "")),
            "xml_filer_cik": xml_filer_cik,
            "acceptance_datetime_et": header.get("acceptance_datetime", ""),
            "acceptance_utc": acceptance_utc,
            "reporting_person_count": len(persons),
            "xml_previous_accession": parsed.get("previous_accession_number", ""),
            "raw_sha256": digest,
        })
        for idx, person in enumerate(persons):
            if family == "13G":
                identity = classify_13g_person_identity(person, idx, filer_cik, header.get("filer_name", ""))
            else:
                pcik = normalize_cik(person.get("person_cik", ""))
                status = person.get("person_cik_status", "")
                identity = {
                    "identity_status": "explicit_reporting_person_cik" if pcik else status,
                    "candidate_person_cik": pcik,
                    "identity_resolved": bool(pcik or status == "declared_no_cik"),
                }
            person_rows.append({
                "accession": accession, "family": family, "filing_date": filing_date,
                "subject_cik": normalize_cik(header.get("subject_cik", "")),
                "filer_cik": filer_cik, "filer_name": header.get("filer_name", ""),
                "person_index": idx, "person_name": person.get("name", ""),
                "person_explicit_cik": normalize_cik(person.get("person_cik", "")),
                "person_no_cik_flag": person.get("person_no_cik_flag", ""),
                **identity,
                "is_first_reporting_person": idx == 0,
                "member_of_group": person.get("member_of_group", ""),
                "type_codes": person.get("type_codes", []),
                "aggregate_amount_owned": person.get("aggregate_amount_owned", ""),
                "percent_of_class": person.get("percent_of_class", ""),
            })

    if errors:
        # Any integrity/identity parse error fails closed; ordinary non-13D/G index rows are skipped.
        summary_status = "FAIL"
    else:
        summary_status = "COMPLETE"

    lag_groups = defaultdict(list)
    for row in filing_rows:
        rules = row["rule_designations"] or ["not_tagged"]
        rule_key = ";".join(sorted(str(x) for x in rules))
        key = (row["family"], row["timing_regime"], str(row["is_amendment"]),
               rule_key, row["sample_candidate_class"])
        lag_groups[key].append(row["event_date_lag_days"])
    lag_rows = []
    for key, values in sorted(lag_groups.items()):
        family, regime, amendment, rule_key, candidate_class = key
        lag_rows.append({
            "family": family, "timing_regime": regime, "is_amendment": amendment,
            "rule_designations": rule_key, "sample_candidate_class": candidate_class,
            **lag_stats(values),
        })

    status_counts = Counter(r["identity_status"] for r in person_rows if r["family"] == "13G")
    first_13g = [r for r in person_rows if r["family"] == "13G" and r["is_first_reporting_person"]]
    first_name_matches = sum(r["identity_status"] == "first_person_filer_cik_candidate_name_match" for r in first_13g)
    summary = {
        "phase": "91-13dg-implicit-cik-and-rule-regime-audit",
        "status": summary_status,
        "raw_submissions_requested": len(manifest),
        "filings_parsed": len(filing_rows),
        "xml_reporting_person_rows": len(person_rows),
        "errors": errors,
        "family_counts": dict(Counter(r["family"] for r in filing_rows)),
        "13g_reporting_person_identity_status_counts": dict(status_counts),
        "13g_first_reporting_person_count": len(first_13g),
        "13g_first_person_filer_name_exact_match_count": first_name_matches,
        "13g_first_person_filer_name_exact_match_rate": first_name_matches / len(first_13g) if first_13g else None,
        "13g_first_person_cik_candidate_count": status_counts.get("first_person_filer_cik_candidate_name_match", 0),
        "13g_additional_person_unresolved_count": status_counts.get("additional_person_cik_unresolved", 0),
        "lag_group_count": len(lag_rows),
        "lag_groups": lag_rows,
        "interpretation": {
            "first_person_filer_cik": "Candidate only when SEC-HEADER FILED BY name exactly matches the first reporting-person name after conservative punctuation/case normalization. This is not promoted to a verified CIK without an independent entity check.",
            "additional_reporting_persons": "Require explicit reportingCik or an explicit no-CIK flag; do not inherit the submission filer CIK.",
            "event_date_lag": "Descriptive filing-minus-reported-event calendar days only. It is not the public-knowledge timestamp and not a predictive feature.",
            "sample_design": "The pilot is stratified by candidate class and timing regime. Reported group medians are unweighted sample diagnostics, not population estimates; no confidence intervals are claimed.",
        },
        "knowledge_time_rule": "SEC-HEADER ACCEPTANCE-DATETIME converted from America/New_York to UTC; next-session availability is required for any future economic test.",
        "forward_returns_used": False,
        "economic_test_authorized": False,
        "production_changes_authorized": False,
    }
    (outdir / "phase91_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    write_csv(outdir / "phase91_filing_lag_strata.csv", lag_rows)
    write_csv(outdir / "phase91_reporting_person_identity.csv", person_rows)
    print(json.dumps(summary, indent=2), flush=True)
    if summary_status != "COMPLETE" or len(filing_rows) != 200:
        raise SystemExit(2)
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--outdir", type=Path, default=Path("phase91_13dg_audit"))
    run(parser.parse_args())


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Offline manifest for 44 explicit SEC 13D/G predecessor references outside the Phase 84 sample."""
from __future__ import annotations
import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path

ZERO_CUSIP = "000000000"
TARGET_STATUS = "explicit_predecessor_outside_600_header_sample"


def normalize_accession(value):
    digits = re.sub(r"\D", "", str(value or ""))
    if len(digits) != 18:
        return ""
    return f"{digits[:10]}-{digits[10:12]}-{digits[12:]}"


def normalize_cik(value):
    digits = re.sub(r"\D", "", str(value or ""))
    return digits.zfill(10) if digits and len(digits) <= 10 else digits


def parse_json_list(value):
    if isinstance(value, list):
        return value
    try:
        parsed = json.loads(str(value or ""))
        return parsed if isinstance(parsed, list) else []
    except (TypeError, ValueError):
        return []


def cusip_checksum_valid(value):
    cusip = re.sub(r"\s+, "", str(value or "")).upper()
    if not re.fullmatch(r"[A-Z0-9*@#]{9}", cusip) or not cusip[-1].isdigit():
        return False
    total = 0
    for index, char in enumerate(cusip[:8]):
        if char.isdigit():
            number = int(char)
        elif "A" <= char <= "Z":
            number = ord(char) - 55
        else:
            number = {"*": 36, "@": 37, "#": 38}.get(char, -1)
        if number < 0:
            return False
        if index % 2:
            number *= 2
        total += number // 10 + number % 10
    return (10 - total % 10) % 10 == int(cusip[-1])


def child_cusip_status(cusips):
    normalized = sorted(set(re.sub(r"\s+, "", str(x or "")).upper() for x in cusips if str(x or "").strip()))
    if len(normalized) != 1:
        return "", "MISSING_OR_MULTIPLE"
    cusip = normalized[0]
    if cusip == ZERO_CUSIP:
        return cusip, "ZERO_SENTINEL"
    if not cusip_checksum_valid(cusip):
        return cusip, "INVALID_CHECKSUM"
    return cusip, "VALID_NONZERO"


def load_csv(path):
    with Path(path).open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_json(path, payload):
    Path(path).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_manifest(lineage_rows, event_rows, phase84_header_rows, phase93_summary, expected_target_count=44):
    if not lineage_rows or len(lineage_rows) != len(event_rows):
        raise ValueError("Phase 93 lineage/event row counts are empty or inconsistent")
    if phase93_summary.get("filings_reparsed") != len(lineage_rows):
        raise ValueError("Phase 93 reparse count does not match lineage rows")
    if phase93_summary.get("raw_sha256_and_xml_identity_errors"):
        raise ValueError("Phase 93 source integrity errors are nonzero")
    declared = phase93_summary.get("amendment_lineage_status_counts", {}).get(TARGET_STATUS)
    if declared != expected_target_count:
        raise ValueError("Phase 93 summary target count differs from the requested manifest count")

    events = {}
    for row in event_rows:
        accession = normalize_accession(row.get("accession"))
        if not accession or accession in events:
            raise ValueError("Missing or duplicate Phase 93 event accession")
        events[accession] = row
    header_accessions = {
        normalize_accession(row.get("accession"))
        for row in phase84_header_rows
        if normalize_accession(row.get("accession"))
    }

    targets = [row for row in lineage_rows if row.get("lineage_status") == TARGET_STATUS]
    if len(targets) != expected_target_count:
        raise ValueError(f"Expected {expected_target_count} explicit out-of-sample parents; found {len(targets)}")

    records = []
    seen_children, seen_parents = set(), set()
    family_counts, cusip_status_counts, tag_counts = Counter(), Counter(), Counter()
    for line in targets:
        child_accession = normalize_accession(line.get("accession"))
        parent_accession = normalize_accession(line.get("xml_previous_accession"))
        if not child_accession or not parent_accession or child_accession == parent_accession:
            raise ValueError("Invalid child/parent accession reference")
        if child_accession in seen_children or parent_accession in seen_parents:
            raise ValueError("Duplicate child or explicit parent accession")
        seen_children.add(child_accession)
        seen_parents.add(parent_accession)
        if parent_accession in header_accessions:
            raise ValueError("Target parent unexpectedly appears in the Phase 84 header sample")

        event = events.get(child_accession)
        if event is None:
            raise ValueError(f"Missing event row for child {child_accession}")
        subject = normalize_cik(line.get("subject_cik"))
        event_subject = normalize_cik(event.get("subject_cik"))
        family = str(line.get("family", "")).upper()
        if not subject or subject != event_subject:
            raise ValueError(f"Child subject CIK mismatch for {child_accession}")
        if family not in {"13D", "13G"} or family != str(event.get("family", "")).upper():
            raise ValueError(f"Child form-family mismatch for {child_accession}")
        if normalize_accession(event.get("xml_previous_accession")) != parent_accession:
            raise ValueError(f"Explicit previousAccessionNumber mismatch for {child_accession}")

        child_filer_cik = normalize_cik(line.get("filer_cik"))
        child_path_cik = normalize_cik(child_accession.split("-")[0])
        parent_path_cik = normalize_cik(parent_accession.split("-")[0])
        cusips = parse_json_list(event.get("cusips"))
        child_cusip, cusip_status = child_cusip_status(cusips)
        person_ciks = parse_json_list(event.get("explicit_person_ciks"))
        person_names = parse_json_list(event.get("person_names"))
        tags = parse_json_list(event.get("event_mechanism_tags"))
        phrases = parse_json_list(event.get("matched_event_phrases"))
        try:
            person_count = int(event.get("reporting_person_count") or 0)
        except (TypeError, ValueError):
            person_count = 0

        family_counts[family] += 1
        cusip_status_counts[cusip_status] += 1
        tag_counts.update(str(tag) for tag in tags)
        records.append({
            "child_accession": child_accession,
            "explicit_parent_accession": parent_accession,
            "subject_issuer_cik": subject,
            "child_filer_cik": child_filer_cik,
            "child_accession_path_cik": child_path_cik,
            "parent_archive_path_cik": parent_path_cik,
            "parent_path_cik_role": "ARCHIVE_PATH_ONLY_NOT_ISSUER_IDENTITY",
            "parent_prefix_matches_child_accession_prefix": parent_path_cik == child_path_cik,
            "parent_prefix_matches_child_filer_cik": bool(child_filer_cik) and parent_path_cik == child_filer_cik,
            "form_family": family,
            "child_filing_date": str(line.get("filing_date", "")),
            "child_acceptance_utc": str(line.get("acceptance_utc", "")),
            "child_cusip": child_cusip,
            "child_cusip_status": cusip_status,
            "explicit_reporting_person_ciks": json.dumps(person_ciks, separators=(",", ":")),
            "reporting_person_names": json.dumps(person_names, separators=(",", ":")),
            "reporting_person_count": person_count,
            "event_mechanism_tags": json.dumps(tags, separators=(",", ":")),
            "matched_event_phrases": json.dumps(phrases, separators=(",", ":")),
            "parent_document_retrieval_status": "NOT_RETRIEVED",
            "immediate_predecessor_claimed": False,
        })

    records.sort(key=lambda row: row["child_accession"])
    summary = {
        "phase": "349-13dg-explicit-predecessor-target-manifest",
        "status": "COMPLETE_TARGET_MANIFEST_ONLY",
        "source_phase93_filings": len(lineage_rows),
        "phase84_header_sample_rows": len(phase84_header_rows),
        "target_references": len(records),
        "unique_parent_accessions": len(seen_parents),
        "unique_subject_issuer_ciks": len({x["subject_issuer_cik"] for x in records}),
        "unique_child_filer_ciks": len({x["child_filer_cik"] for x in records if x["child_filer_cik"]}),
        "unique_parent_archive_path_ciks": len({x["parent_archive_path_cik"] for x in records}),
        "parent_prefix_matches_child_accession_prefix": sum(x["parent_prefix_matches_child_accession_prefix"] for x in records),
        "parent_prefix_differs_from_child_accession_prefix": sum(not x["parent_prefix_matches_child_accession_prefix"] for x in records),
        "parent_prefix_matches_child_filer_cik": sum(x["parent_prefix_matches_child_filer_cik"] for x in records),
        "family_counts": dict(sorted(family_counts.items())),
        "child_cusip_status_counts": dict(sorted(cusip_status_counts.items())),
        "explicit_person_cik_coverage_rows": sum(bool(parse_json_list(x["explicit_reporting_person_ciks"])) for x in records),
        "person_name_coverage_rows": sum(bool(parse_json_list(x["reporting_person_names"])) for x in records),
        "reporting_person_rows_total": sum(x["reporting_person_count"] for x in records),
        "event_mechanism_tag_counts_nonexclusive": dict(sorted(tag_counts.items())),
        "activist_control_tag_rows": sum("activist_or_control_action" in parse_json_list(x["event_mechanism_tags"]) for x in records),
        "aggregated_client_adviser_tag_rows": sum("aggregated_client_or_adviser_holdings" in parse_json_list(x["event_mechanism_tags"]) for x in records),
        "unclassified_narrative_rows": sum("unclassified_narrative" in parse_json_list(x["event_mechanism_tags"]) for x in records),
        "parent_documents_retrieved": 0,
        "new_sec_requests_made": False,
        "immediate_predecessor_inference_performed": False,
        "strict_pit_admitted": False,
        "alpha_test_authorized": False,
        "f80_frozen": True,
    }
    return summary, records


def run(args):
    phase84 = Path(args.phase84_artifact_dir)
    phase93 = Path(args.phase93_artifact_dir)
    lineage = load_csv(phase93 / "phase93_amendment_lineage_audit.csv")
    events = load_csv(phase93 / "phase93_event_mechanism_audit.csv")
    headers = load_csv(phase84 / "pilot_header_validation.csv")
    source_summary = json.loads((phase93 / "phase93_summary.json").read_text(encoding="utf-8"))
    summary, records = build_manifest(lineage, events, headers, source_summary, expected_target_count=44)

    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    fields = list(records[0])
    with (out / "phase349_predecessor_target_manifest.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)
    write_json(out / "phase349_summary.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase84-artifact-dir", type=Path, required=True)
    parser.add_argument("--phase93-artifact-dir", type=Path, required=True)
    parser.add_argument("--outdir", type=Path, default=Path("phase349_output"))
    run(parser.parse_args())


if __name__ == "__main__":
    main()

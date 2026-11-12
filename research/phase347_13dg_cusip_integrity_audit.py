#!/usr/bin/env python3
"""Offline CUSIP integrity and subject-issuer consistency audit for Phase 93."""
from __future__ import annotations
import argparse, csv, json, re
from collections import Counter, defaultdict
from pathlib import Path

ZERO_CUSIP = "000000000"
ALLOWED = re.compile(r"^[A-Z0-9*@#]{9}$")

def parse_json_list(value):
    if isinstance(value, list):
        return value
    try:
        parsed = json.loads(str(value or ""))
        return parsed if isinstance(parsed, list) else []
    except (TypeError, ValueError):
        return []

def normalize_cik(value):
    digits = re.sub(r"\\D", "", str(value or ""))
    return digits.zfill(10) if digits and len(digits) <= 10 else digits

def normalize_cusip(value):
    return re.sub(r"\\s+", "", str(value or "")).upper()

def cusip_checksum_valid(value):
    cusip = normalize_cusip(value)
    if not ALLOWED.fullmatch(cusip) or not cusip[-1].isdigit():
        return False
    total = 0
    for index, char in enumerate(cusip[:8]):
        if char.isdigit():
            number = int(char)
        elif "A" <= char <= "Z":
            number = ord(char) - 55
        elif char == "*":
            number = 36
        elif char == "@":
            number = 37
        elif char == "#":
            number = 38
        else:
            return False
        if index % 2:
            number *= 2
        total += number // 10 + number % 10
    return (10 - total % 10) % 10 == int(cusip[-1])

def is_valid_security_cusip(value):
    cusip = normalize_cusip(value)
    return cusip != ZERO_CUSIP and cusip_checksum_valid(cusip)

def load_csv(path):
    with Path(path).open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))

def audit_rows(rows, phase93_summary=None):
    if not rows:
        raise ValueError("Phase 93 event-mechanism input is empty")
    accessions = [str(row.get("accession", "")).strip() for row in rows]
    if any(not x for x in accessions) or len(set(accessions)) != len(accessions):
        raise ValueError("Missing or duplicate accession")
    details, invalid_rows, zero_rows, checksum_bad = [], [], [], []
    cusip_subjects, cusip_accessions, issuer_cusips = defaultdict(set), defaultdict(list), defaultdict(set)
    family_counts, amendment_counts, tag_counts = Counter(), Counter(), Counter()
    for row in rows:
        accession = str(row["accession"]).strip()
        family = str(row.get("family", "")).strip().upper()
        if family not in {"13D", "13G"}:
            raise ValueError(f"Unexpected family for {accession}: {family}")
        subject = normalize_cik(row.get("subject_cik", ""))
        if len(subject) != 10:
            raise ValueError(f"Invalid subject CIK for {accession}")
        cusips = [normalize_cusip(x) for x in parse_json_list(row.get("cusips")) if normalize_cusip(x)]
        if len(cusips) != 1:
            invalid_rows.append({"accession": accession, "reason": "missing_cusip" if not cusips else "multiple_cusips"})
        cusip = cusips[0] if cusips else ""
        checksum = bool(cusip and cusip_checksum_valid(cusip))
        zero = cusip == ZERO_CUSIP
        valid = bool(cusip and is_valid_security_cusip(cusip))
        if zero:
            zero_rows.append(accession)
        if cusip and not checksum:
            checksum_bad.append({"accession": accession, "cusip": cusip})
        if cusip:
            cusip_subjects[cusip].add(subject)
            cusip_accessions[cusip].append(accession)
        if valid:
            issuer_cusips[subject].add(cusip)
        amendment = str(row.get("is_amendment", "")).strip().lower() in {"true", "1", "yes", "y"}
        family_counts[family] += 1
        amendment_counts["amendment" if amendment else "initial"] += 1
        for tag in parse_json_list(row.get("event_mechanism_tags")):
            tag_counts[str(tag)] += 1
        details.append({
            "accession": accession, "family": family, "is_amendment": amendment,
            "subject_cik": subject, "cusip": cusip, "cusip_count": len(cusips),
            "checksum_valid": checksum, "zero_sentinel": zero,
            "valid_security_cusip": valid, "cusip_subject_collision": False,
        })
    raw_nonzero = {x for x in cusip_subjects if x and x != ZERO_CUSIP}
    valid_nonzero = {x for x in raw_nonzero if cusip_checksum_valid(x)}
    collisions = {x: sorted(cusip_subjects[x]) for x in sorted(valid_nonzero) if len(cusip_subjects[x]) > 1}
    repeated = {x: v for x, v in cusip_accessions.items() if x != ZERO_CUSIP and len(v) > 1}
    multi_issuer = {cik: sorted(xs) for cik, xs in sorted(issuer_cusips.items()) if len(xs) > 1}
    for detail in details:
        detail["cusip_subject_collision"] = detail["cusip"] in collisions
    phase93_errors = (phase93_summary or {}).get("raw_sha256_and_xml_identity_errors", []) or []
    if phase93_summary is not None:
        if phase93_summary.get("filings_reparsed") != len(rows) or phase93_errors:
            raise ValueError("Phase 93 source integrity gate failed")
    valid_rows = sum(x["valid_security_cusip"] for x in details)
    checksum_rows = sum(x["checksum_valid"] for x in details)
    summary = {
        "phase": "347-13dg-cusip-integrity-and-subject-consistency",
        "status": "COMPLETE", "input_filings": len(rows),
        "unique_accessions": len(set(accessions)),
        "unique_subject_ciks": len({x["subject_cik"] for x in details}),
        "cusip_field_present_rows": sum(bool(x["cusip"]) for x in details),
        "exactly_one_cusip_rows": sum(x["cusip_count"] == 1 for x in details),
        "filing_cusip_cardinality_errors": len(invalid_rows),
        "cusip_checksum_valid_rows_including_zero_sentinel": checksum_rows,
        "valid_nonzero_security_cusip_rows": valid_rows,
        "all_zero_sentinel_rows": len(zero_rows),
        "all_zero_sentinel_subject_ciks": sorted(cusip_subjects.get(ZERO_CUSIP, set())),
        "checksum_invalid_nonzero_rows": len(checksum_bad),
        "checksum_invalid_nonzero_cusips": checksum_bad,
        "unique_nonzero_cusips": len(raw_nonzero),
        "unique_checksum_valid_nonzero_cusips": len(valid_nonzero),
        "repeated_nonzero_cusip_groups": len(repeated),
        "repeated_nonzero_extra_filing_rows": sum(len(v)-1 for v in repeated.values()),
        "nonzero_cusips_with_multiple_subject_ciks": len(collisions),
        "nonzero_cusip_subject_collisions": collisions,
        "subject_ciks_with_multiple_nonzero_cusips": len(multi_issuer),
        "maximum_nonzero_cusips_for_one_subject_cik": max((len(v) for v in multi_issuer.values()), default=0),
        "subject_ciks_with_multiple_cusips": multi_issuer,
        "family_counts": dict(sorted(family_counts.items())),
        "amendment_counts": dict(sorted(amendment_counts.items())),
        "valid_cusip_rows_by_family": {f: sum(x["family"] == f and x["valid_security_cusip"] for x in details) for f in ("13D", "13G")},
        "valid_cusip_rows_by_initial_amendment": {g: sum(x["is_amendment"] == (g == "amendment") and x["valid_security_cusip"] for x in details) for g in ("initial", "amendment")},
        "event_mechanism_tag_counts_nonexclusive": dict(sorted(tag_counts.items())),
        "phase93_raw_and_xml_identity_errors": len(phase93_errors),
        "forward_returns_used": False, "alpha_test_authorized": False,
        "strict_pit_admitted": False, "production_changes_authorized": False,
    }
    return summary, details

def run(args):
    source = Path(args.phase93_artifact_dir)
    rows = load_csv(source / "phase93_event_mechanism_audit.csv")
    source_summary = json.loads((source / "phase93_summary.json").read_text(encoding="utf-8"))
    summary, details = audit_rows(rows, source_summary)
    out = Path(args.outdir); out.mkdir(parents=True, exist_ok=True)
    with (out / "phase347_cusip_filing_audit.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(details[0])); writer.writeheader(); writer.writerows(details)
    (out / "phase347_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return summary

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase93-artifact-dir", type=Path, required=True)
    parser.add_argument("--outdir", type=Path, default=Path("phase347_audit"))
    run(parser.parse_args())

if __name__ == "__main__":
    main()

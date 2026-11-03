"""Audit a deterministic candidate link from 13G submission filer to one reporting person.

This creates candidate links only; it never mutates the source reporting-person CIKs
or infers an economic group. It is an identity-feasibility audit, not an alpha test.
"""
from __future__ import annotations
import argparse
import csv
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

LEGAL_SUFFIXES = {
    "INC", "INCORPORATED", "CORP", "CORPORATION", "CO", "COMPANY",
    "LLC", "LP", "L P", "LTD", "LIMITED", "PLC", "LLP", "L L P",
    "NA", "N A", "SA", "AG", "NV",
}


def tokens(name):
    value = unicodedata.normalize("NFKD", str(name or ""))
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    parts = re.findall(r"[A-Z0-9]+", value.upper())
    while parts and (parts[0] == "THE" or parts[-1] in LEGAL_SUFFIXES):
        if parts[0] == "THE":
            parts = parts[1:]
        elif parts[-1] in LEGAL_SUFFIXES:
            parts = parts[:-1]
    return tuple(parts)


def canonical_name(name, person_types):
    parts = tokens(name)
    if not parts:
        return tuple()
    # SEC CIK display names for natural persons can be surname-first.
    if "IN" in (person_types or []):
        return tuple(sorted(parts))
    return parts


def match_filer_to_reporting_person(people, filer_name, filer_cik):
    if not filer_name or not filer_cik:
        return {"status": "missing_filer_identity", "matches": []}
    filer_key_entity = canonical_name(filer_name, [])
    if not filer_key_entity:
        return {"status": "empty_filer_name", "matches": []}
    matches = []
    for i, person in enumerate(people or []):
        types = person.get("types") or []
        person_key = canonical_name(person.get("name"), types)
        # The filer may be an individual, so compare using the person's type
        # only after deriving the corresponding canonical filer key.
        filer_key = canonical_name(filer_name, types)
        if person_key and person_key == filer_key:
            matches.append({"index": i, "name": person.get("name")})
    if len(matches) == 1:
        return {
            "status": "unique_exact_normalized_name_match",
            "matches": matches,
            "candidate_reporting_person_cik": filer_cik,
            "candidate_source": "submission_filer_cik_via_unique_master_index_name_match",
        }
    if len(matches) > 1:
        return {"status": "ambiguous_multiple_reporting_person_matches", "matches": matches}
    return {"status": "no_exact_normalized_name_match", "matches": []}


def load_rows(path):
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def audit_rows(rows, quarter):
    detail = []
    for row in rows:
        try:
            people = json.loads(row.get("reporting_persons_json") or "[]")
        except Exception:
            people = []
        match = match_filer_to_reporting_person(
            people,
            row.get("submission_filer_name_from_master_pair"),
            row.get("submission_filer_cik"),
        )
        detail.append({
            "quarter": quarter,
            "accession": row.get("accession"),
            "form": row.get("form"),
            "sample": (
                "target_subject" if row.get("subject_is_target_candidate") == "True"
                else "non_target_validation" if row.get("validation_sample_non_target") == "True"
                else "other"
            ),
            "subject_issuer_cik": row.get("subject_issuer_cik"),
            "subject_issuer_name": row.get("subject_issuer_name"),
            "submission_filer_cik": row.get("submission_filer_cik"),
            "submission_filer_name": row.get("submission_filer_name_from_master_pair"),
            "reporting_person_count": len(people),
            "explicit_reporting_person_cik_count": sum(bool(p.get("cik")) for p in people),
            "crosswalk_status": match["status"],
            "matched_reporting_person_index": (
                match["matches"][0]["index"] if len(match["matches"]) == 1 else ""
            ),
            "matched_reporting_person_name": (
                match["matches"][0]["name"] if len(match["matches"]) == 1 else ""
            ),
            "candidate_reporting_person_cik": match.get("candidate_reporting_person_cik", ""),
            "candidate_source": match.get("candidate_source", ""),
            "previous_accession": row.get("previous_accession") or "",
            "amendment_no": row.get("amendment_no") or "",
            "event_date_raw": row.get("event_date_raw") or "",
            "filing_date": row.get("filing_date") or "",
        })
    return detail


def summarize(detail, quarter):
    summaries = []
    for sample in ("target_subject", "non_target_validation"):
        for family in ("13D", "13G"):
            subset = [
                x for x in detail
                if x["quarter"] == quarter and x["sample"] == sample
                and family in (x["form"] or "")
            ]
            if not subset:
                continue
            forms = Counter(x["form"] for x in subset)
            amendments = [x for x in subset if (x["form"] or "").endswith("/A")]
            status = Counter(x["crosswalk_status"] for x in subset)
            people_total = sum(int(x["reporting_person_count"] or 0) for x in subset)
            explicit_ciks = sum(int(x["explicit_reporting_person_cik_count"] or 0) for x in subset)
            single = [x for x in subset if int(x["reporting_person_count"] or 0) == 1]
            single_unique = sum(x["crosswalk_status"] == "unique_exact_normalized_name_match" for x in single)
            summaries.append({
                "quarter": quarter,
                "sample": sample,
                "family": family,
                "filings": len(subset),
                "unique_subject_ciks": len({x["subject_issuer_cik"] for x in subset if x["subject_issuer_cik"]}),
                "form_counts": dict(forms),
                "reporting_persons": people_total,
                "explicit_reporting_person_ciks": explicit_ciks,
                "explicit_reporting_person_cik_coverage": explicit_ciks / people_total if people_total else None,
                "unique_filer_to_person_matches": status["unique_exact_normalized_name_match"],
                "unique_match_rate": status["unique_exact_normalized_name_match"] / len(subset),
                "ambiguous_matches": status["ambiguous_multiple_reporting_person_matches"],
                "no_exact_match": status["no_exact_normalized_name_match"],
                "single_person_filings": len(single),
                "single_person_unique_match_rate": single_unique / len(single) if single else None,
                "amendments": len(amendments),
                "amendments_with_previous_accession": sum(bool(x["previous_accession"]) for x in amendments),
                "amendments_missing_previous_accession": sum(not bool(x["previous_accession"]) for x in amendments),
                "amendments_with_amendment_no": sum(bool(x["amendment_no"]) for x in amendments),
                "group_status": "NOT_INFERRED",
            })
    return summaries


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="phase35_global_subject_census_xml_pilot")
    ap.add_argument("--quarters", default="2025Q2,2025Q3")
    ap.add_argument("--output", default="phase35_global_subject_census_xml_pilot")
    args = ap.parse_args()
    root = Path(args.root)
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    all_detail, all_summary = [], []
    for quarter in [x.strip() for x in args.quarters.split(",") if x.strip()]:
        qdir = root / quarter
        global_path = qdir / "global_subject_census_xml.csv"
        subject_path = qdir / "target_subject_filings_xml.csv"
        if not global_path.exists() or not subject_path.exists():
            raise FileNotFoundError(f"Missing census outputs for {quarter}: {qdir}")
        global_rows = load_rows(global_path)
        subject_rows = load_rows(subject_path)
        target_detail = audit_rows(subject_rows, quarter)
        non_target_rows = [
            row for row in global_rows if row.get("validation_sample_non_target") == "True"
        ]
        validation_detail = audit_rows(non_target_rows, quarter)
        detail = target_detail + validation_detail
        all_detail.extend(detail)
        all_summary.extend(summarize(detail, quarter))
    if not all_detail:
        raise RuntimeError("No identity crosswalk rows were audited")
    detail_path = output / "reporting_person_crosswalk_detail.csv"
    with detail_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(all_detail[0].keys()))
        writer.writeheader()
        writer.writerows(all_detail)
    summary = {
        "status": "IDENTITY_CANDIDATE_AUDIT_COMPLETE",
        "quarters": [x.strip() for x in args.quarters.split(",") if x.strip()],
        "normalization": {
            "unicode": "NFKD accent removal",
            "case_and_punctuation": "uppercase alphanumeric tokens",
            "legal_suffixes_removed": sorted(LEGAL_SUFFIXES),
            "leading_the_removed": True,
            "individual_name_order": "token-order invariant only when type IN is present",
            "entity_name_order": "preserved",
            "acceptance": "exact canonical key and exactly one reporting-person match",
        },
        "interpretation": (
            "Candidate filer-to-person identity coverage only; not measured precision, "
            "not group identity, and not a beneficial-ownership event. Source CIK fields "
            "are never overwritten. No forward returns are used."
        ),
        "results": all_summary,
        "forward_returns_used": False,
        "economic_group_status": "NOT_TESTED",
    }
    (output / "reporting_person_crosswalk_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()

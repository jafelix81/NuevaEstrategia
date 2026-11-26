#!/usr/bin/env python3
"""Phase 352 — offline SEC 13D/G parent identity and security continuity audit."""
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
from pathlib import Path


def read_csv(path: str | Path) -> list[dict]:
    with Path(path).open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def normalize_cik(value: object) -> str:
    digits = re.sub(r"\D", "", str(value or ""))
    return digits.lstrip("0") or ("0" if digits else "")


def normalize_name(value: object) -> str:
    return re.sub(r"[^A-Z0-9]", "", html.unescape(str(value or "")).upper())


def parse_json_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(x) for x in value]
    try:
        parsed = json.loads(str(value or "[]"))
    except (TypeError, json.JSONDecodeError):
        return []
    return [str(x) for x in parsed] if isinstance(parsed, list) else []


def extract_header_fields(raw: str) -> dict:
    match = re.search(r"<SEC-HEADER>(.*?)</SEC-HEADER>", raw, re.I | re.S)
    if not match:
        return {}
    header = match.group(1)
    subject = re.search(r"SUBJECT COMPANY:\s*(.*?)(?=FILED BY:)", header, re.I | re.S)
    filed = re.search(r"FILED BY:\s*(.*?)(?=(?:REPORTING-OWNER:|SUBJECT COMPANY:|$))", header, re.I | re.S)

    def field(pattern: str, block: str | None) -> str:
        if not block:
            return ""
        found = re.search(pattern, block, re.I | re.M)
        return found.group(1).strip() if found else ""

    subject_block = subject.group(1) if subject else ""
    filed_block = filed.group(1) if filed else ""
    return {
        "parent_subject_name": field(r"COMPANY CONFORMED NAME\s*:\s*([^\r\n]+)", subject_block),
        "parent_subject_cik": normalize_cik(field(r"CENTRAL INDEX KEY\s*:\s*(\d{1,10})", subject_block)),
        "parent_filed_by_name": field(r"COMPANY CONFORMED NAME\s*:\s*([^\r\n]+)", filed_block),
        "parent_filed_by_cik": normalize_cik(field(r"CENTRAL INDEX KEY\s*:\s*(\d{1,10})", filed_block)),
    }


def extract_primary_cusips(raw: str) -> list[str]:
    xml_values = re.findall(r"<issuerCUSIP>\s*([^<\s]+)\s*</issuerCUSIP>", raw, re.I)
    if xml_values:
        values = xml_values
    else:
        clean = html.unescape(re.sub(r"<[^>]+>", " ", raw))
        clean = re.sub(r"\s+", " ", clean)
        values = re.findall(
            r"\bCUSIP(?:\s+(?:NO\.?|NUMBER))?\s*[:#]?\s*([0-9A-Z]{6}\s*[0-9A-Z]{3})\b",
            clean,
            re.I,
        )
    return sorted({re.sub(r"\s+", "", value).upper() for value in values
                   if re.fullmatch(r"[0-9A-Z\s]{9,15}", re.sub(r"\s+", "", value).upper())})


def extract_structured_reporting_person_names(raw: str) -> list[str]:
    values = re.findall(r"<reportingPersonName>\s*(.*?)\s*</reportingPersonName>", raw, re.I | re.S)
    names = {
        normalize_name(re.sub(r"<[^>]+>", " ", html.unescape(value)))
        for value in values
    }
    return sorted(name for name in names if name)


def cusip_status(child_cusip: object, parent_cusips: list[str], parent_retrieved: bool = True) -> str:
    child = re.sub(r"\s+", "", str(child_cusip or "")).upper()
    if not parent_retrieved:
        return "UNRESOLVED_PARENT_NOT_RETRIEVED"
    if not child or child == "000000000" or not re.fullmatch(r"[0-9A-Z]{9}", child):
        return "CHILD_CUSIP_INVALID"
    if not parent_cusips:
        return "PARENT_CUSIP_MISSING"
    return "MATCH" if child in parent_cusips else "MISMATCH"


def cik_overlap(parent_filed_by_cik: object, child_reporting_ciks: list[str]) -> str:
    child = {normalize_cik(x) for x in child_reporting_ciks if normalize_cik(x)}
    if not child:
        return "CHILD_REPORTING_PERSON_CIK_UNAVAILABLE"
    return "OVERLAP" if normalize_cik(parent_filed_by_cik) in child else "NO_OVERLAP"


def name_overlap(parent_names: list[str], child_names: list[str]) -> str:
    parent = {normalize_name(x) for x in parent_names if normalize_name(x)}
    child = {normalize_name(x) for x in child_names if normalize_name(x)}
    if not parent or not child:
        return "NAME_SET_UNAVAILABLE"
    if parent & child:
        return "EXACT_OVERLAP"
    if any(a in b or b in a for a in parent for b in child):
        return "SUBSTRING_CANDIDATE"
    return "NO_OVERLAP"


def run(manifest_path: str | Path, parent_results_path: str | Path,
        parents_dir: str | Path, outdir: str | Path) -> dict:
    manifest_rows = read_csv(manifest_path)
    parent_rows = read_csv(parent_results_path)
    manifest_by_child = {row.get("child_accession"): row for row in manifest_rows}
    out_rows = []
    for prior in parent_rows:
        child = str(prior.get("child_accession") or "")
        manifest = manifest_by_child.get(child, {})
        parent_acc = str(prior.get("parent_accession") or "")
        if str(prior.get("retrieval_status") or "").upper() != "HTTP_200":
            out_rows.append({
                "child_accession": child,
                "parent_accession": parent_acc,
                "identity_status": "UNRESOLVED_PARENT_NOT_RETRIEVED",
                "cusip_continuity_status": "UNRESOLVED_PARENT_NOT_RETRIEVED",
                "parent_reporting_person_names": "[]",
                "structured_parent_reporting_person_name_overlap": "NOT_TESTED",
                "parent_filed_by_cik_child_reporting_person_overlap": "NOT_TESTED",
                "parent_filed_by_name_child_reporting_person_overlap": "NOT_TESTED",
            })
            continue

        raw_path = Path(parents_dir) / f"{re.sub(r'[^0-9]', '', parent_acc)}.txt"
        if not raw_path.exists():
            raise FileNotFoundError(f"missing raw parent submission for {parent_acc}")
        raw_bytes = raw_path.read_bytes()
        raw = raw_bytes.decode("utf-8", errors="replace")
        header = extract_header_fields(raw)
        parent_cusips = extract_primary_cusips(raw)
        parent_rp_names = extract_structured_reporting_person_names(raw)
        child_ciks = parse_json_list(manifest.get("explicit_reporting_person_ciks"))
        child_names = parse_json_list(manifest.get("reporting_person_names"))
        child_cusip = manifest.get("child_cusip", "")
        child_issuer_cik = normalize_cik(manifest.get("subject_issuer_cik"))
        expected_family = str(manifest.get("form_family") or "").upper()
        actual_family = str(prior.get("parent_form_family") or "").upper()
        parent_acceptance = str(prior.get("parent_acceptance_utc") or "")
        child_acceptance = str(manifest.get("child_acceptance_utc") or "")
        identity_ok = (
            header.get("parent_subject_cik") == child_issuer_cik
            and actual_family == expected_family
            and bool(parent_acceptance and child_acceptance and parent_acceptance < child_acceptance)
        )
        parent_cik = normalize_cik(header.get("parent_filed_by_cik"))
        prefix_cik = normalize_cik(parent_acc.split("-")[0])
        structured_overlap = name_overlap(parent_rp_names, child_names)
        filed_by_name_proxy = name_overlap(
            [header.get("parent_filed_by_name", "")], child_names
        )
        out_rows.append({
            "child_accession": child,
            "parent_accession": parent_acc,
            "parent_subject_name": header.get("parent_subject_name", ""),
            "parent_subject_cik": header.get("parent_subject_cik", ""),
            "child_subject_cik": child_issuer_cik,
            "parent_filed_by_name": header.get("parent_filed_by_name", ""),
            "parent_filed_by_cik": parent_cik,
            "parent_filed_by_cik_equals_accession_prefix": bool(parent_cik and parent_cik == prefix_cik),
            "child_reporting_person_ciks": json.dumps(child_ciks),
            "child_reporting_person_names": json.dumps(child_names),
            "parent_structured_reporting_person_names": json.dumps(parent_rp_names),
            "structured_parent_reporting_person_name_overlap": structured_overlap,
            "parent_filed_by_cik_child_reporting_person_overlap": cik_overlap(parent_cik, child_ciks),
            "parent_filed_by_name_child_reporting_person_overlap": filed_by_name_proxy,
            "child_cusip": child_cusip,
            "parent_primary_cusips": json.dumps(parent_cusips),
            "cusip_continuity_status": cusip_status(child_cusip, parent_cusips),
            "parent_acceptance_utc": parent_acceptance,
            "child_acceptance_utc": child_acceptance,
            "parent_form_family": actual_family,
            "child_form_family": expected_family,
            "identity_status": "PASS" if identity_ok else "QUARANTINE",
            "parent_raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
            "reporting_person_identity_note": "structured reportingPersonName is preferred; FILED BY is only a submitter proxy",
        })

    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    fields = sorted({key for row in out_rows for key in row})
    with (out / "phase352_parent_identity_security_crosswalk.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(out_rows)

    valid = [r for r in out_rows if r.get("identity_status") == "PASS"]
    retrieved = [r for r in valid if r.get("cusip_continuity_status") != "UNRESOLVED_PARENT_NOT_RETRIEVED"]
    cusip_counts = {}
    for status in ["MATCH", "MISMATCH", "PARENT_CUSIP_MISSING", "CHILD_CUSIP_INVALID", "UNRESOLVED_PARENT_NOT_RETRIEVED"]:
        cusip_counts[status] = sum(r.get("cusip_continuity_status") == status for r in out_rows)
    structured = [r for r in retrieved if r.get("structured_parent_reporting_person_name_overlap") != "NAME_SET_UNAVAILABLE"]
    child_cik_available = [r for r in retrieved if r.get("parent_filed_by_cik_child_reporting_person_overlap") != "CHILD_REPORTING_PERSON_CIK_UNAVAILABLE"]
    summary = {
        "phase": 352,
        "parent_rows_total": len(out_rows),
        "parent_rows_retrieved": len(retrieved),
        "identity_pass_rows": len(valid),
        "cusip_continuity_counts": cusip_counts,
        "structured_parent_reporting_person_name_rows": len(structured),
        "structured_parent_reporting_person_name_exact_or_substring_overlap_rows": sum(
            r.get("structured_parent_reporting_person_name_overlap") in {"EXACT_OVERLAP", "SUBSTRING_CANDIDATE"}
            for r in structured
        ),
        "child_reporting_person_cik_rows_available": len(child_cik_available),
        "parent_filed_by_cik_overlap_rows": sum(
            r.get("parent_filed_by_cik_child_reporting_person_overlap") == "OVERLAP"
            for r in child_cik_available
        ),
        "parent_filed_by_name_exact_overlap_rows": sum(
            r.get("parent_filed_by_name_child_reporting_person_overlap") == "EXACT_OVERLAP"
            for r in retrieved
        ),
        "parent_filed_by_name_substring_candidate_rows": sum(
            r.get("parent_filed_by_name_child_reporting_person_overlap") == "SUBSTRING_CANDIDATE"
            for r in retrieved
        ),
        "filed_by_is_submitter_proxy_not_reporting_person_ground_truth": True,
        "cusip_match_is_security_continuity_evidence_not_proof_of_same_economic_exposure": True,
        "strict_pit_admitted": False,
        "alpha_test_authorized": False,
        "f80_frozen": True,
    }
    (out / "phase352_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--parent-results", required=True, type=Path)
    parser.add_argument("--parents-dir", required=True, type=Path)
    parser.add_argument("--outdir", type=Path, default=Path("phase352_output"))
    args = parser.parse_args()
    run(args.manifest, args.parent_results, args.parents_dir, args.outdir)


if __name__ == "__main__":
    main()

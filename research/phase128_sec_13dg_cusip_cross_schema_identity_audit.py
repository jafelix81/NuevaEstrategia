#!/usr/bin/env python3
"""Artifact-only SEC 13D/G CUSIP cross-schema identity and legacy parser feasibility audit."""
from __future__ import annotations
import argparse, csv, hashlib, json, re
from collections import Counter, defaultdict
from pathlib import Path

from research.phase126_sec_13dg_body_issuer_identity_audit import (
    extract_cover_issuer_name, extract_xml_issuer_identity, normalize_name, norm_cik
)

EXPECTED_PHASE124_RUN_ID = 42073725379
EXPECTED_PHASE124_ARTIFACT_ID = 13436764625
EXPECTED_PHASE127_RUN_ID = 42079517644
EXPECTED_PHASE127_ARTIFACT_ID = 13438903901
EXPECTED_PHASE127_ARTIFACT_SHA256 = "b80d15d736ba6c45f4f3c5dd569604175e221414b31a28fd58a62010a805c166"
CROSS_SCHEMA_ANCHORS = {"90290N109", "G38644103"}
LEGACY_HEADER_CONFLICT_ANCHOR = "81752R100"


def read_csv(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def unique(values):
    return sorted({value for value in values if value not in (None, "")})


def source_mix(sources):
    sources = set(sources)
    if {"LEGACY_HTML_EXACT_TOKEN", "13DG_XML"}.issubset(sources):
        return "CROSS_SCHEMA"
    if "LEGACY_HTML_EXACT_TOKEN" in sources:
        return "LEGACY_ONLY"
    if "13DG_XML" in sources:
        return "XML_ONLY"
    return "UNKNOWN"


def cross_schema_identity_match(legacy_rows, xml_rows):
    if not legacy_rows or not xml_rows:
        return False
    legacy_ciks = unique(norm_cik(row.get("header_subject_cik")) for row in legacy_rows)
    xml_ciks = unique(norm_cik(row.get("xml_issuer_cik")) for row in xml_rows)
    legacy_names = unique(normalize_name(row.get("body_issuer_name")) for row in legacy_rows)
    xml_names = unique(normalize_name(row.get("xml_issuer_name")) for row in xml_rows)
    return (
        len(legacy_ciks) == 1 and legacy_ciks == xml_ciks
        and len(legacy_names) == 1 and legacy_names == xml_names
    )


def same_body_name_different_header_cik(rows):
    names = unique(normalize_name(row.get("body_issuer_name")) for row in rows)
    ciks = unique(norm_cik(row.get("header_subject_cik")) for row in rows)
    return len(names) == 1 and len(ciks) > 1


def is_obvious_body_name_contamination(value):
    value = str(value or "").strip()
    if not value or not re.search(r"[A-Za-z]", value):
        return True
    patterns = (
        r"[-_]{8,}",
        r"SECURITIES\s*&\s*EXCHANGE|SECURITIES\s+AND\s+EXCHANGE",
        r"\b1934\b|AMENDMENTS?\s+THERETO|\b13[DG]/A\b",
        r"EDGARWIZ|CONVERTED\s+BY",
        r"\bDC\s+20549\b|HOURS\s+PER\s+RESPONSE|REFERENCE\s+IS\s+MADE\s+TO\s+PAGE",
        r"^UNDER\s+THE\b|^COMMISSION$",
    )
    return any(re.search(pattern, value, flags=re.I) for pattern in patterns)


def audit(phase124_dir: Path, phase127_dir: Path, output_dir: Path):
    s124 = json.loads((phase124_dir / "phase124_global_13dg_summary.json").read_text(encoding="utf-8"))
    s127 = json.loads((phase127_dir / "phase127_sec_13dg_xml_cusip_summary.json").read_text(encoding="utf-8"))
    rows124 = read_csv(phase124_dir / "phase124_global_13dg_submission_audit.csv")
    rows127 = read_csv(phase127_dir / "phase127_sec_13dg_xml_cusip_audit.csv")
    manifest = read_csv(phase124_dir / "phase124_global_stratified_sample_manifest.csv")
    errors = []
    if len(rows124) != 600 or len(manifest) != 600 or len(rows127) != 599:
        errors.append({"error": "unexpected source artifact row counts", "phase124_rows": len(rows124), "manifest_rows": len(manifest), "phase127_rows": len(rows127)})
    if s127.get("status") != "PASS_ARTIFACT_ONLY_XML_CUSIP_SCHEMA_CORRECTION":
        errors.append({"error": "Phase 127 source artifact status is not PASS", "status": s127.get("status")})
    if s127.get("source_phase124_run_id") != EXPECTED_PHASE124_RUN_ID or s127.get("source_phase124_artifact_id") != EXPECTED_PHASE124_ARTIFACT_ID:
        errors.append({"error": "Phase 127 source artifact lineage mismatch"})
    if s124.get("sampled_index_rows_resolved") != 600 or s124.get("download_or_mirror_failures") != 0:
        errors.append({"error": "Phase 124 sample retrieval gate failed"})

    phase124_by_accession = {row["accession"]: row for row in rows124}
    cusip_by_accession = {row["accession"]: row for row in rows127}
    raw_cache = {}
    alias_rows = []
    actual_rows = []
    raw_verified = 0
    for row in rows124:
        accession = row["accession"]
        raw_path = phase124_dir / (row.get("raw_file") or "")
        if not raw_path.is_file():
            errors.append({"accession": accession, "error": "raw submission file missing"})
            continue
        body = raw_path.read_bytes()
        digest = hashlib.sha256(body).hexdigest()
        if digest != row.get("raw_sha256"):
            errors.append({"accession": accession, "error": "Phase 124 raw SHA-256 mismatch"})
            continue
        raw_verified += 1
        raw = body.decode("utf-8", errors="replace")
        raw_cache[accession] = raw
        if row.get("download_status") == "INDEX_ALIAS_NON_13DG":
            alias_rows.append(accession)
            continue
        c = cusip_by_accession.get(accession)
        if c is None or c.get("raw_sha256") != digest:
            errors.append({"accession": accession, "error": "Phase 127 CUSIP row/hash missing or inconsistent"})
            continue
        actual_rows.append({
            "accession": accession,
            "quarter": row.get("quarter"),
            "family": row.get("family"),
            "source": c.get("cusip_source"),
            "cusip": c.get("cusip"),
            "cusip_status": c.get("cusip_status"),
            "header_subject_cik": norm_cik(row.get("subject_cik")),
            "header_subject_name": row.get("subject_name"),
            "header_filer_cik": norm_cik(row.get("filer_cik")),
            "raw": raw,
        })
    if raw_verified != 600 or len(alias_rows) != 1 or len(actual_rows) != 599:
        errors.append({"error": "raw/sample reconciliation failed", "raw_verified": raw_verified, "aliases": len(alias_rows), "actual_rows": len(actual_rows)})

    valid_rows = [row for row in actual_rows if row["cusip_status"] == "UNIQUE_CHECKSUM_VALID" and row["cusip"]]
    groups = defaultdict(list)
    for row in valid_rows:
        groups[row["cusip"]].append(row)
    repeated = {cusip: rows for cusip, rows in groups.items() if len(rows) > 1}

    group_rows = []
    for cusip, rows in sorted(repeated.items()):
        mix = source_mix(row["source"] for row in rows)
        legacy_rows = [row for row in rows if row["source"] == "LEGACY_HTML_EXACT_TOKEN"]
        xml_rows = [row for row in rows if row["source"] == "13DG_XML"]
        for row in legacy_rows:
            row["body_issuer_name"] = extract_cover_issuer_name(row["raw"]) if cusip in CROSS_SCHEMA_ANCHORS | {LEGACY_HEADER_CONFLICT_ANCHOR} else None
        for row in xml_rows:
            if cusip in CROSS_SCHEMA_ANCHORS:
                row["xml_issuer_name"], row["xml_issuer_cik"] = extract_xml_issuer_identity(row["raw"])
            else:
                row["xml_issuer_name"], row["xml_issuer_cik"] = None, None
        cross_match = cross_schema_identity_match(legacy_rows, xml_rows) if mix == "CROSS_SCHEMA" else False
        body_cik_conflict = same_body_name_different_header_cik(legacy_rows) if cusip == LEGACY_HEADER_CONFLICT_ANCHOR else False
        group_rows.append({
            "cusip": cusip,
            "filing_count": len(rows),
            "source_mix": mix,
            "quarters": json.dumps(unique(row["quarter"] for row in rows)),
            "accessions": json.dumps(unique(row["accession"] for row in rows)),
            "header_subject_ciks": json.dumps(unique(row["header_subject_cik"] for row in rows)),
            "header_subject_names": json.dumps(unique(row["header_subject_name"] for row in rows)),
            "legacy_body_issuer_names": json.dumps(unique(row.get("body_issuer_name") for row in legacy_rows)),
            "xml_issuer_names": json.dumps(unique(row.get("xml_issuer_name") for row in xml_rows)),
            "xml_issuer_ciks": json.dumps(unique(row.get("xml_issuer_cik") for row in xml_rows)),
            "cross_schema_identity_match": cross_match,
            "same_body_name_different_header_subject_cik": body_cik_conflict,
        })

    mix_counts = Counter(row["source_mix"] for row in group_rows)
    cross_groups = [row for row in group_rows if row["source_mix"] == "CROSS_SCHEMA"]
    cross_matches = [row for row in cross_groups if row["cross_schema_identity_match"]]
    conflict_groups = [row for row in group_rows if row["same_body_name_different_header_subject_cik"]]

    # Probe the current legacy cover-name heuristic on all 497 legacy rows.
    # This is a parser-quality diagnostic only; candidates are not promoted as issuer identities.
    legacy_probe = []
    for row in actual_rows:
        if row["source"] != "LEGACY_HTML_EXACT_TOKEN":
            continue
        name = extract_cover_issuer_name(row["raw"])
        legacy_probe.append({
            "accession": row["accession"],
            "body_issuer_name": name,
            "obvious_contamination": is_obvious_body_name_contamination(name) if name else False,
        })
    candidate_rows = [row for row in legacy_probe if row["body_issuer_name"]]
    contaminated_rows = [row for row in candidate_rows if row["obvious_contamination"]]
    clean_unvalidated_rows = [row for row in candidate_rows if not row["obvious_contamination"]]

    cross_schema_cusips = sorted(row["cusip"] for row in cross_groups)
    expected_cross = sorted(CROSS_SCHEMA_ANCHORS)
    if len(groups) != 553:
        errors.append({"error": "unique valid CUSIP group count changed", "actual": len(groups), "expected": 553})
    if len(repeated) != 18 or dict(mix_counts) != {"LEGACY_ONLY": 14, "XML_ONLY": 2, "CROSS_SCHEMA": 2}:
        errors.append({"error": "repeated CUSIP source-mix counts changed", "repeated_groups": len(repeated), "mix_counts": dict(mix_counts)})
    if cross_schema_cusips != expected_cross or len(cross_matches) != 2:
        errors.append({"error": "cross-schema identity anchors did not reconcile", "cross_schema_cusips": cross_schema_cusips, "matches": len(cross_matches)})
    if len(conflict_groups) != 1 or conflict_groups[0]["cusip"] != LEGACY_HEADER_CONFLICT_ANCHOR:
        errors.append({"error": "legacy header-CIK conflict anchor did not reconcile", "conflict_groups": [row["cusip"] for row in conflict_groups]})

    output_dir.mkdir(parents=True, exist_ok=True)
    if group_rows:
        with (output_dir / "phase128_sec_13dg_cusip_repeated_groups.csv").open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(group_rows[0].keys()))
            writer.writeheader()
            writer.writerows(group_rows)
    summary = {
        "phase": "128-sec-13dg-cusip-cross-schema-identity-feasibility",
        "status": "PASS_CUSIP_CROSS_SCHEMA_IDENTITY_FEASIBILITY" if not errors else "INCOMPLETE",
        "source_phase124_run_id": EXPECTED_PHASE124_RUN_ID,
        "source_phase124_artifact_id": EXPECTED_PHASE124_ARTIFACT_ID,
        "source_phase127_run_id": EXPECTED_PHASE127_RUN_ID,
        "source_phase127_artifact_id": EXPECTED_PHASE127_ARTIFACT_ID,
        "source_phase127_artifact_sha256": EXPECTED_PHASE127_ARTIFACT_SHA256,
        "sampled_index_rows": len(rows124),
        "actual_13dg_rows": len(actual_rows),
        "index_alias_rows_quarantined": len(alias_rows),
        "raw_sha256_verified": raw_verified,
        "errors": errors,
        "legacy_html_rows": len([row for row in actual_rows if row["source"] == "LEGACY_HTML_EXACT_TOKEN"]),
        "xml_rows": len([row for row in actual_rows if row["source"] == "13DG_XML"]),
        "unique_valid_cusips": len(groups),
        "repeated_cusip_groups": len(repeated),
        "repeated_group_source_mix_counts": dict(mix_counts),
        "cross_schema_cusip_groups": len(cross_groups),
        "cross_schema_identity_matches": len(cross_matches),
        "cross_schema_cusips": cross_schema_cusips,
        "cross_schema_coverage_of_unique_valid_cusips": len(cross_groups) / len(groups) if groups else None,
        "legacy_header_cik_conflict_groups_with_same_body_name": len(conflict_groups),
        "legacy_header_cik_conflict_details": conflict_groups,
        "cross_schema_identity_details": cross_matches,
        "legacy_body_name_parser_probe": {
            "rows": len(legacy_probe),
            "candidate_rows": len(candidate_rows),
            "candidate_rate": len(candidate_rows) / len(legacy_probe) if legacy_probe else None,
            "obvious_contamination_rows": len(contaminated_rows),
            "remaining_unvalidated_candidate_rows": len(clean_unvalidated_rows),
            "no_candidate_rows": len(legacy_probe) - len(candidate_rows),
            "promoted_as_identity_source": False,
        },
        "interpretation": [
            "Only two CUSIPs in this 599-filing sample bridge legacy HTML and structured XML; both have matching subject/issuer CIKs and issuer names across the two schemas.",
            "The 81752R100 Seritage group has the same body issuer name across two legacy filings but different SEC-HEADER subject CIKs, confirming a concrete legacy header-role exception.",
            "Internal cross-schema CUSIP overlap is too sparse to provide a historical security master: it covers only two of 553 unique checksum-valid CUSIPs.",
            "The legacy cover-name heuristic has apparent candidate yield but obvious separator/boilerplate contamination; remaining candidates are unvalidated and are not promoted.",
        ],
        "limitations": [
            "The sample is hash-stratified from the SEC filing index, not a historical eligible-security universe; repeated CUSIP frequency and cross-schema overlap are not population estimates.",
            "CUSIP is not permanent and cannot alone handle share classes, ADRs, reorganizations, splits, successors or delistings.",
            "Only two cross-schema links are available in this sample; this is insufficient for broad historical issuer/security identity mapping.",
            "The body-name parser probe is exploratory; obvious contamination is flagged, but remaining candidates have not been manually validated.",
            "No public dissemination-time proof, reporting-person/group normalization, forward-return test or alpha test was performed.",
        ],
    }
    (output_dir / "phase128_sec_13dg_cusip_cross_schema_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    if summary["status"] != "PASS_CUSIP_CROSS_SCHEMA_IDENTITY_FEASIBILITY":
        raise SystemExit(2)
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase124-dir", type=Path, required=True)
    parser.add_argument("--phase127-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    audit(args.phase124_dir, args.phase127_dir, args.output_dir)


if __name__ == "__main__":
    main()

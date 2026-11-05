#!/usr/bin/env python3
"""Artifact-only body-first issuer identity adjudication for the Phase 124 13D/G sample."""
from __future__ import annotations
import argparse, csv, hashlib, json, re
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path
import xml.etree.ElementTree as ET

from research.phase125_sec_13dg_exact_cusip_audit import (
    primary_document_text, parse_header, form_family, normalize_form
)

EXPECTED_PHASE124_RUN_ID = 42073725379
EXPECTED_PHASE124_ARTIFACT_ID = 13436764625
EXPECTED_PHASE125_RUN_ID = 42077788015
EXPECTED_PHASE125_ARTIFACT_ID = 13437963766
EXPECTED_PHASE125_ARTIFACT_DIGEST = "sha256:eda7a26b256c087a469b0ae7c213114673e1180458b76867b8c7ce7b99262cc7"

MANUAL_CASES = {
    "0001549575-20-000008": {
        "subject_cik": "1549575", "filer_cik": "1549575",
        "subject_name": "Dalal Street, LLC", "filer_name": "Dalal Street, LLC",
        "body_issuer_name": "Seritage Growth Properties", "cusip": "81752R100",
        "note": "SEC-HEADER SUBJECT COMPANY and FILED BY both identify Dalal Street, LLC; the 13G cover page identifies Seritage Growth Properties."
    },
    "0001903596-22-000671": {
        "subject_cik": "1626837", "filer_cik": "1945609",
        "subject_name": "American Community Capital, LP.", "filer_name": "Igwealor Frank I",
        "body_issuer_name": "Nano Mobile Healthcare, Inc.", "cusip": "63010B200",
        "note": "SEC-HEADER subject company differs from the issuer named on the 13D cover page."
    },
    "0001172661-24-001310": {
        "subject_cik": "1578987", "filer_cik": "1837915",
        "subject_name": "ArrowMark Financial Corp.", "filer_name": "ArrowMark Colorado Holdings LLC",
        "body_issuer_name": "StoneCastle Financial Corp.", "cusip": "861780104",
        "note": "SEC-HEADER subject company differs from the issuer named on the 13G cover page."
    },
}
SERITAGE_ANCHOR = "0001193125-21-208169"


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def norm_cik(value):
    digits = re.sub(r"\D", "", str(value or ""))
    return digits.lstrip("0") or "0" if digits else None


def normalize_cik(value):
    return norm_cik(value)


def normalize_name(value):
    value = re.sub(r"[^A-Z0-9 ]", " ", str(value or "").upper())
    return re.sub(r"\s+", " ", value).strip()


def clean_issuer_candidate(value):
    value = re.sub(r"^\s*\d+\s*\)\s*\*?\s*", "", str(value or ""))
    value = re.sub(r"^\s*\d+\s*\(a\)\s*[-:]?\s*", "", value, flags=re.I)
    value = re.sub(r"^\s*(?:INITIAL\s+FILING|FINAL\s+AMENDMENT)\s+", "", value, flags=re.I)
    value = re.sub(r"\s*\(the\s+[" + '"' + r"“]?Issuer[" + '"' + r"”]?\)\.?$", "", value, flags=re.I)
    value = re.sub(r"\s+", " ", value).strip(" :()")
    boilerplate = (
        r"FORMERLY\b|UNDER\s+THE\s+SECURITIES|ACT\s+OF\s+1934|AMENDMENT\s+NO|"
        r"SCHEDULE\s+13[DG]|SECURITIES\s+AND\s+EXCHANGE|WASHINGTON|UNITED\s+STATES|"
        r"INFORMATION\s+TO\s+BE\s+INCLUDED|TO\s+§|§\s*240|FILED\s+PURSUANT|PURSUANT\s+TO|"
        r"TO\s+RULE|RULE\s+13D|CHECK\s+THE\s+APPROPRIATE|THE\s+REMAINDER|ANNUAL\s+FILING|"
        r"INITIAL\s+FILING|FINAL\s+AMENDMENT|TITLE\s+OF\s+CLASS|CUSIP|DATE\s+OF\s+EVENT|"
        r"NAME\s+OF\s+ISSUER|SEE\s+COVER\s+PAGE|SEC\s+USE\s+ONLY"
    )
    if not value or len(value) > 120 or re.search(boilerplate, value, flags=re.I):
        return None
    return value


class BlockTextParser(HTMLParser):
    BLOCKS = {
        "address", "article", "br", "center", "div", "dl", "dt", "dd", "h1", "h2", "h3",
        "hr", "li", "ol", "p", "pre", "table", "tbody", "td", "th", "tr", "ul"
    }
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
    def handle_starttag(self, tag, attrs):
        if tag.lower() in self.BLOCKS:
            self.parts.append("\n")
    def handle_endtag(self, tag):
        if tag.lower() in self.BLOCKS:
            self.parts.append("\n")
    def handle_data(self, data):
        self.parts.append(data)


def extract_cover_issuer_name(raw):
    parser = BlockTextParser()
    parser.feed(primary_document_text(raw))
    lines = [re.sub(r"\s+", " ", x).strip() for x in "".join(parser.parts).splitlines()]
    lines = [x for x in lines if x][:100]

    # Publisher-style layouts place the issuer name after the label, sometimes split across blocks.
    for i in range(len(lines)):
        combo = " ".join(lines[i:i + 2])
        m = re.search(
            r"NAME\s+OF\s+ISSUER\s*:\s*(.{1,160}?)(?=\s+(?:TITLE\s+OF\s+CLASS|CUSIP|DATE\s+OF\s+EVENT)|$)",
            combo, flags=re.I
        )
        if m:
            candidate = clean_issuer_candidate(m.group(1))
            if candidate:
                return candidate

    # Standard cover pages place the issuer name immediately before the parenthesized label.
    label_idx = next((i for i, line in enumerate(lines) if re.search(r"NAME\s+OF\s+ISSUER", line, flags=re.I)), None)
    if label_idx is None:
        return None
    line = lines[label_idx]
    m = re.search(r"NAME\s+OF\s+ISSUER", line, flags=re.I)
    before = clean_issuer_candidate(line[:m.start()])
    if before:
        return before
    after = clean_issuer_candidate(line[m.end():])
    if after:
        return after

    candidates = []
    for j in range(label_idx - 1, max(-1, label_idx - 7), -1):
        candidate = clean_issuer_candidate(lines[j])
        if candidate:
            candidates.append(candidate)
        if len(candidates) >= 2:
            break
    return " ".join(reversed(candidates)) if candidates else None


def extract_xml_issuer_identity(raw):
    for block in re.findall(r"<XML>(.*?)</XML>", raw, flags=re.I | re.S):
        if "edgarSubmission" not in block:
            continue
        try:
            root = ET.fromstring(block.strip())
        except ET.ParseError:
            continue
        issuer_name = issuer_cik = None
        for node in root.iter():
            local = node.tag.split("}")[-1].lower()
            if local == "issuername":
                issuer_name = (node.text or "").strip() or None
            elif local == "issuercik":
                issuer_cik = norm_cik(node.text)
        return issuer_name, issuer_cik
    return None, None


def audit(phase124_dir: Path, phase125_dir: Path, output_dir: Path):
    s124 = json.loads((phase124_dir / "phase124_global_13dg_summary.json").read_text(encoding="utf-8"))
    s125 = json.loads((phase125_dir / "phase125_sec_13dg_exact_cusip_summary.json").read_text(encoding="utf-8"))
    rows124 = read_csv(phase124_dir / "phase124_global_13dg_submission_audit.csv")
    rows125 = read_csv(phase125_dir / "phase125_sec_13dg_exact_cusip_audit.csv")
    manifest = read_csv(phase124_dir / "phase124_global_stratified_sample_manifest.csv")
    if len(rows124) != 600 or len(manifest) != 600 or len(rows125) != 599:
        raise ValueError("Phase 124/125 artifact row counts do not match the expected sample")
    if s124.get("sampled_index_rows_resolved") != 600 or s124.get("download_or_mirror_failures") != 0:
        raise ValueError("Phase 124 sample has unresolved retrieval failures")
    if s125.get("status") != "PASS_ARTIFACT_ONLY_CUSIP_AUDIT" or s125.get("source_phase124_run_id") != EXPECTED_PHASE124_RUN_ID:
        raise ValueError("Phase 125 source audit is not the expected passing artifact")

    cusip_by_accession = {r["accession"]: r for r in rows125}
    output_rows, errors, alias_rows = [], [], []
    manual_accessions = set(MANUAL_CASES) | {SERITAGE_ANCHOR}
    xml_matches = 0
    xml_rows = 0
    for row in rows124:
        accession = row["accession"]
        raw_path = phase124_dir / (row.get("raw_file") or "")
        if not raw_path.is_file():
            errors.append({"accession": accession, "error": "raw file missing"})
            continue
        body = raw_path.read_bytes()
        digest = hashlib.sha256(body).hexdigest()
        if digest != row.get("raw_sha256"):
            errors.append({"accession": accession, "error": "raw SHA-256 mismatch"})
            continue
        raw = body.decode("utf-8", errors="replace")
        header = parse_header(raw)
        if header.get("accession") != accession or header.get("filed_date") != row.get("filing_date_index"):
            errors.append({"accession": accession, "error": "SEC header accession/date mismatch"})
            continue

        if row.get("download_status") == "INDEX_ALIAS_NON_13DG":
            alias_rows.append(accession)
            continue

        c = cusip_by_accession.get(accession)
        if c is None or c.get("raw_sha256") != digest:
            errors.append({"accession": accession, "error": "Phase 125 CUSIP row/hash missing or inconsistent"})
            continue
        subject_cik = norm_cik(row.get("subject_cik"))
        filer_cik = norm_cik(row.get("filer_cik"))
        is_xml = str(row.get("xml_present", "")).lower() in {"true", "1"}
        xml_name = xml_cik = None
        if is_xml:
            xml_rows += 1
            xml_name, xml_cik = extract_xml_issuer_identity(raw)
            if xml_cik and xml_cik == subject_cik:
                xml_matches += 1
            else:
                errors.append({"accession": accession, "error": "XML issuerCik does not match SEC-HEADER subject CIK", "xml_issuer_cik": xml_cik, "header_subject_cik": subject_cik})

        body_name = None
        scope = "XML_STRUCTURED_ISSUER" if is_xml else "NOT_ADJUDICATED_LEGACY"
        if accession in manual_accessions and not is_xml:
            body_name = extract_cover_issuer_name(raw)
            scope = "HAND_ADJUDICATED_LEGACY_COVER_PAGE"

        output_rows.append({
            "accession": accession, "family": row["family"], "filing_date": header.get("filed_date"),
            "header_subject_cik": subject_cik, "header_subject_name": row.get("subject_name"),
            "header_filer_cik": filer_cik, "header_filer_name": row.get("filer_name"),
            "body_issuer_name": body_name, "xml_issuer_name": xml_name, "xml_issuer_cik": xml_cik,
            "xml_issuer_cik_matches_header": (xml_cik == subject_cik) if xml_cik else None,
            "cusip": c.get("cusip"), "cusip_status": c.get("cusip_status"),
            "subject_equals_filer": subject_cik == filer_cik,
            "identity_audit_scope": scope, "raw_sha256": digest,
        })

    by_accession = {r["accession"]: r for r in output_rows}
    confirmed = []
    for accession, expected in MANUAL_CASES.items():
        row = by_accession.get(accession)
        if row is None:
            errors.append({"accession": accession, "error": "manual case missing"})
            continue
        checks = {
            "subject_cik": row["header_subject_cik"] == expected["subject_cik"],
            "filer_cik": row["header_filer_cik"] == expected["filer_cik"],
            "subject_name": normalize_name(row["header_subject_name"]) == normalize_name(expected["subject_name"]),
            "filer_name": normalize_name(row["header_filer_name"]) == normalize_name(expected["filer_name"]),
            "body_issuer_name": normalize_name(row["body_issuer_name"]) == normalize_name(expected["body_issuer_name"]),
            "cusip": row["cusip"] == expected["cusip"],
            "cusip_valid": row["cusip_status"] == "UNIQUE_CHECKSUM_VALID",
        }
        if not all(checks.values()):
            errors.append({"accession": accession, "error": "manual case assertion failed", "checks": checks, "row": row})
        confirmed.append({
            "accession": accession, **expected, "checks": checks,
            "subject_equals_filer": row["subject_equals_filer"],
        })

    anchor = by_accession.get(SERITAGE_ANCHOR)
    if anchor is None:
        errors.append({"accession": SERITAGE_ANCHOR, "error": "Seritage cross-filing anchor missing"})
    else:
        anchor_checks = {
            "subject_cik": anchor["header_subject_cik"] == "1628063",
            "subject_name": normalize_name(anchor["header_subject_name"]) == normalize_name("Seritage Growth Properties"),
            "body_issuer_name": normalize_name(anchor["body_issuer_name"]) == normalize_name("Seritage Growth Properties"),
            "cusip": anchor["cusip"] == "81752R100",
            "cusip_valid": anchor["cusip_status"] == "UNIQUE_CHECKSUM_VALID",
        }
        if not all(anchor_checks.values()):
            errors.append({"accession": SERITAGE_ANCHOR, "error": "Seritage anchor assertion failed", "checks": anchor_checks, "row": anchor})

    seritage_rows = [r for r in output_rows if r["cusip"] == "81752R100"]
    seritage_subject_ciks = {r["header_subject_cik"] for r in seritage_rows}
    seritage_body_names = {normalize_name(r["body_issuer_name"]) for r in seritage_rows if r["body_issuer_name"]}
    cross_cik_conflict = (
        len(seritage_rows) == 2 and seritage_subject_ciks == {"1549575", "1628063"}
        and seritage_body_names == {normalize_name("Seritage Growth Properties")}
    )
    if not cross_cik_conflict:
        errors.append({
            "error": "CUSIP 81752R100 did not reproduce the expected cross-header-CIK/body-name conflict",
            "rows": seritage_rows,
        })

    output_dir.mkdir(parents=True, exist_ok=True)
    fields = list(output_rows[0].keys()) if output_rows else []
    with (output_dir / "phase126_sec_13dg_body_issuer_identity_audit.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(output_rows)

    summary = {
        "phase": "126-sec-13dg-body-first-issuer-identity-audit",
        "status": "PASS_BODY_FIRST_IDENTITY_AUDIT_WITH_LEGACY_HEADER_EXCEPTIONS" if not errors and len(output_rows) == 599 and len(alias_rows) == 1 and xml_matches == 102 else "INCOMPLETE",
        "source_phase124_run_id": EXPECTED_PHASE124_RUN_ID,
        "source_phase124_artifact_id": EXPECTED_PHASE124_ARTIFACT_ID,
        "source_phase125_run_id": EXPECTED_PHASE125_RUN_ID,
        "source_phase125_artifact_id": EXPECTED_PHASE125_ARTIFACT_ID,
        "source_phase125_artifact_digest": EXPECTED_PHASE125_ARTIFACT_DIGEST,
        "sampled_index_rows": len(rows124), "actual_13dg_rows": len(output_rows),
        "index_alias_rows_quarantined": len(alias_rows),
        "raw_sha256_and_accession_date_checks": len(output_rows) + len(alias_rows) - len(errors),
        "errors": errors,
        "legacy_rows": len([r for r in output_rows if r["identity_audit_scope"] != "XML_STRUCTURED_ISSUER"]),
        "xml_rows": xml_rows, "xml_issuer_cik_header_matches": xml_matches,
        "header_subject_cik_present_rows": sum(bool(r["header_subject_cik"]) for r in output_rows),
        "header_subject_equals_filer_rows": sum(r["subject_equals_filer"] for r in output_rows),
        "confirmed_legacy_header_body_issuer_mismatches": confirmed,
        "seritage_cusip_cross_filing": {
            "cusip": "81752R100", "filings": [r["accession"] for r in seritage_rows],
            "distinct_header_subject_ciks": sorted(seritage_subject_ciks),
            "body_issuer_names": sorted(seritage_body_names),
            "same_body_issuer_different_header_subject_cik": cross_cik_conflict,
        },
        "interpretation": [
            "SEC-HEADER SUBJECT COMPANY CIK is not a reliable issuer CIK for every legacy HTML 13D/G filing.",
            "The 81752R100 Seritage cross-filing is especially probative: two filings carry different header subject CIKs but the same body issuer name and cover-page CUSIP.",
            "The three hand-adjudicated legacy examples are concrete exceptions, not a statistically estimated global mismatch rate.",
            "Structured XML issuerCik matched SEC-HEADER subject CIK in all 102 XML rows in this sample; this does not prove universal correctness outside the sample.",
            "For legacy 13D/G, use body cover-page issuer name plus effective-dated CUSIP/security mapping; do not treat header subject CIK presence as issuer-universe coverage."
        ],
        "limitations": [
            "Only four legacy cover pages were hand-adjudicated in this phase; no broad automated body-issuer parser was promoted.",
            "CUSIP is not permanent and requires effective-dated corporate-action, share-class and delisting-aware security mapping.",
            "The sample is a hash-stratified filing-index sample, not a historical tradable-security universe; no inferential confidence interval is claimed.",
            "No forward returns, features, alpha tests, vendor purchases, or production changes were performed."
        ],
    }
    (output_dir / "phase126_sec_13dg_body_issuer_identity_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    if summary["status"] != "PASS_BODY_FIRST_IDENTITY_AUDIT_WITH_LEGACY_HEADER_EXCEPTIONS":
        raise SystemExit(2)
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase124-dir", type=Path, required=True)
    parser.add_argument("--phase125-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    audit(args.phase124_dir, args.phase125_dir, args.output_dir)


if __name__ == "__main__":
    main()

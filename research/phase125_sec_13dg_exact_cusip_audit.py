#!/usr/bin/env python3
"""Artifact-only exact-token CUSIP identity audit for the Phase 124 SEC 13D/G sample."""
from __future__ import annotations
import argparse, csv, hashlib, json, re
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
import xml.etree.ElementTree as ET

EXPECTED_PHASE124_RUN_ID = 42073725379
EXPECTED_PHASE124_ARTIFACT_ID = 13436764625
EXPECTED_PHASE124_ARTIFACT_DIGEST = "sha256:85f69e083b5af65731c9bcfe24e8c75821fc0f2c2476bfa8ba573e2e884570dc"
SAMPLE_SIZE = 600

def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def normalize_form(value):
    form = re.sub(r"\s+", " ", str(value or "")).strip().upper()
    return "SC " + form[len("SCHEDULE "):] if form.startswith("SCHEDULE ") else form

def form_family(value):
    form = normalize_form(value)
    if form in {"SC 13D", "SC 13D/A"}: return "13D"
    if form in {"SC 13G", "SC 13G/A"}: return "13G"
    return None

def parse_header(raw):
    m = re.search(r"<SEC-HEADER>(.*?)</SEC-HEADER>", raw, flags=re.I | re.S)
    header = m.group(1) if m else raw[:100000]
    def one(pattern):
        x = re.search(pattern, header, flags=re.I | re.S)
        return x.group(1).strip() if x else None
    filed = one(r"FILED AS OF DATE\s*:\s*(\d{8})")
    return {
        "accession": one(r"ACCESSION NUMBER\s*:\s*([0-9-]{20})"),
        "form": normalize_form(one(r"CONFORMED SUBMISSION TYPE\s*:\s*([^\r\n]+)")),
        "filed_date": f"{filed[:4]}-{filed[4:6]}-{filed[6:8]}" if filed else None,
    }

def document_types(raw):
    return [normalize_form(x) for x in re.findall(r"<TYPE>\s*([^\r\n<]+)", raw, flags=re.I)]

def classify_submission(index_form, raw, expected_accession, expected_filed_date):
    header, docs = parse_header(raw), document_types(raw)
    if header["accession"] != expected_accession or header["filed_date"] != expected_filed_date:
        return "INVALID_IDENTITY", header, docs
    indexed_family, header_family = form_family(index_form), form_family(header["form"])
    if indexed_family in {"13D", "13G"} and indexed_family == header_family:
        return "VALID_13DG", header, docs
    if header_family is None and not any(form_family(x) for x in docs):
        return "INDEX_ALIAS_NON_13DG", header, docs
    return "UNRESOLVED_FORM_CONFLICT", header, docs

class SimpleTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
    def handle_data(self, data):
        value = re.sub(r"\s+", " ", data).strip()
        if value: self.parts.append(value)

def primary_document_text(raw):
    docs = re.findall(r"<DOCUMENT>(.*?)</DOCUMENT>", raw, flags=re.I | re.S)
    for doc in docs:
        m = re.search(r"<TYPE>\s*([^\r\n<]+)", doc, flags=re.I)
        if m and form_family(m.group(1)):
            body = re.search(r"<TEXT>(.*?)</TEXT>", doc, flags=re.I | re.S)
            return body.group(1) if body else doc
    return raw

def normalize_cusip(value):
    value = re.sub(r"[^A-Z0-9]", "", str(value or "").upper())
    if not re.fullmatch(r"[A-Z0-9]{8}\d", value) or value == "000000000":
        return None
    return value

def extract_legacy_cusips(raw):
    parser = SimpleTextExtractor()
    parser.feed(primary_document_text(raw))
    text = " ".join(parser.parts)
    values = []
    patterns = (
        r"\bCUSIP\b(?:\s+(?:NO\.?|NUMBER))?\s*[:#.]?\s*([A-Z0-9]{8}\d)(?![A-Z0-9])",
        r"(?<![A-Z0-9])([A-Z0-9]{8}\d)(?![A-Z0-9])\s*\(CUSIP\s+(?:NUMBER|NO\.?)",
    )
    for pattern in patterns:
        for match in re.finditer(pattern, text, flags=re.I):
            value = normalize_cusip(match.group(1))
            if value and value not in values: values.append(value)
    return values

def extract_xml_cusip(raw):
    for block in re.findall(r"<XML>(.*?)</XML>", raw, flags=re.I | re.S):
        if "edgarSubmission" not in block: continue
        try: root = ET.fromstring(block.strip())
        except ET.ParseError: continue
        for node in root.iter():
            if node.tag.split("}")[-1].lower() == "issuercusip":
                return True, (node.text or "").strip() or None
        return True, None
    return False, None

def cusip_check_digit(value):
    cusip = normalize_cusip(value)
    if not cusip: return False
    total = 0
    for i, char in enumerate(cusip[:8]):
        if char.isdigit(): number = int(char)
        elif "A" <= char <= "Z": number = ord(char) - ord("A") + 10
        else: return False
        product = number * (2 if i % 2 else 1)
        total += product // 10 + product % 10
    return str((10 - total % 10) % 10) == cusip[-1]

def cusip_status(candidates):
    if not candidates: return "MISSING", None, None
    if len(candidates) > 1: return "AMBIGUOUS", None, None
    value = candidates[0]
    valid = cusip_check_digit(value)
    return ("UNIQUE_CHECKSUM_VALID" if valid else "UNIQUE_CHECKSUM_INVALID"), value, valid

def weighted_rate(rows, predicate):
    denominator = sum(float(r["sample_weight"]) for r in rows)
    if denominator <= 0: return None
    return sum(float(r["sample_weight"]) for r in rows if predicate(r)) / denominator

def audit(input_dir, output_dir):
    source_summary = json.loads((input_dir / "phase124_global_13dg_summary.json").read_text(encoding="utf-8"))
    source_rows = read_csv(input_dir / "phase124_global_13dg_submission_audit.csv")
    manifest = read_csv(input_dir / "phase124_global_stratified_sample_manifest.csv")
    if len(manifest) != SAMPLE_SIZE or len({r["accession"] for r in manifest}) != SAMPLE_SIZE:
        raise ValueError("Phase 124 manifest is not 600 unique accessions")
    if len(source_rows) != SAMPLE_SIZE or len({r["accession"] for r in source_rows}) != SAMPLE_SIZE:
        raise ValueError("Phase 124 result is not 600 unique accession rows")
    if source_summary.get("sampled_index_rows_resolved") != SAMPLE_SIZE or source_summary.get("download_or_mirror_failures") != 0:
        raise ValueError("Phase 124 source artifact is not fully resolved")

    manifest_by_accession = {r["accession"]: r for r in manifest}
    results, aliases, errors = [], [], []
    for row in source_rows:
        accession = row["accession"]
        sample = manifest_by_accession.get(accession)
        if sample is None:
            errors.append({"accession": accession, "error": "not in sample manifest"}); continue
        raw_rel = row.get("raw_file") or ""
        raw_path = input_dir / raw_rel
        if not raw_rel or not raw_path.is_file():
            errors.append({"accession": accession, "error": "raw submission missing"}); continue
        body = raw_path.read_bytes()
        digest = hashlib.sha256(body).hexdigest()
        if digest != row.get("raw_sha256"):
            errors.append({"accession": accession, "error": "raw SHA-256 mismatch"}); continue
        raw = body.decode("utf-8", errors="replace")
        classification, header, docs = classify_submission(
            sample.get("form") or row.get("index_form") or row.get("family") or "",
            raw, accession, sample.get("filing_date") or row.get("filing_date_index") or ""
        )
        if classification == "INDEX_ALIAS_NON_13DG":
            aliases.append({
                "accession": accession, "index_form": sample.get("form"),
                "header_form": header.get("form"), "document_types": docs,
                "sample_weight": float(row["sample_weight"]),
            })
            if row.get("download_status") != "INDEX_ALIAS_NON_13DG":
                errors.append({"accession": accession, "error": "alias status differs from Phase 124"})
            continue
        if classification != "VALID_13DG":
            errors.append({"accession": accession, "error": classification, "header": header, "document_types": docs})
            continue
        if row.get("download_status") not in ("", None):
            errors.append({"accession": accession, "error": "Phase 124 status conflicts with valid filing"})
            continue

        xml_present, xml_raw = extract_xml_cusip(raw)
        if xml_present:
            candidate = normalize_cusip(xml_raw)
            candidates = [candidate] if candidate else []
            source = "13DG_XML"
            format_invalid = bool(xml_raw and candidate is None)
        else:
            candidates = extract_legacy_cusips(raw)
            source = "LEGACY_HTML_EXACT_TOKEN"
            xml_raw = None
            format_invalid = False
        status, cusip, checksum_valid = cusip_status(candidates)
        if format_invalid: status = "INVALID_XML_CUSIP_FORMAT"
        results.append({
            "accession": accession, "quarter": row["quarter"], "family": row["family"],
            "index_form": sample.get("form"), "form": header.get("form"),
            "filing_date": header.get("filed_date"), "xml_present": xml_present,
            "cusip_source": source, "xml_cusip_raw": xml_raw,
            "cusip_candidates": json.dumps(candidates), "cusip_candidate_count": len(candidates),
            "cusip": cusip, "cusip_status": status, "cusip_checksum_valid": checksum_valid,
            "sample_weight": float(row["sample_weight"]), "sample_stratum": row["sample_stratum"],
            "raw_sha256": digest,
        })

    legacy = [r for r in results if r["cusip_source"] == "LEGACY_HTML_EXACT_TOKEN"]
    xml = [r for r in results if r["cusip_source"] == "13DG_XML"]
    status_counts = Counter(r["cusip_status"] for r in results)
    alias_weight = sum(float(r["sample_weight"]) for r in aliases)
    total_index_weight = sum(float(r["sample_weight"]) for r in source_rows)
    output_dir.mkdir(parents=True, exist_ok=True)
    fields = list(results[0].keys()) if results else []
    with (output_dir / "phase125_sec_13dg_exact_cusip_audit.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields); writer.writeheader(); writer.writerows(results)

    summary = {
        "phase": "125-sec-13dg-exact-cusip-identity-audit",
        "status": "PASS_ARTIFACT_ONLY_CUSIP_AUDIT" if not errors and len(results) == 599 and len(aliases) == 1 else "INCOMPLETE",
        "source_phase124_run_id": EXPECTED_PHASE124_RUN_ID,
        "source_phase124_artifact_id": EXPECTED_PHASE124_ARTIFACT_ID,
        "source_phase124_artifact_digest": EXPECTED_PHASE124_ARTIFACT_DIGEST,
        "source_phase124_summary_status": source_summary.get("status"),
        "sampled_index_rows": len(source_rows), "actual_13dg_rows": len(results),
        "index_alias_rows_quarantined": len(aliases),
        "raw_files_sha256_verified": len(results) + len(aliases) - len(errors),
        "raw_hash_or_identity_errors": errors,
        "legacy_html_rows": len(legacy), "xml_rows": len(xml),
        "cusip_status_counts": dict(status_counts),
        "legacy_exact_candidate_rows": sum(r["cusip_candidate_count"] > 0 for r in legacy),
        "legacy_unique_checksum_valid_rows": sum(r["cusip_status"] == "UNIQUE_CHECKSUM_VALID" for r in legacy),
        "legacy_ambiguous_rows": sum(r["cusip_status"] == "AMBIGUOUS" for r in legacy),
        "legacy_unique_checksum_invalid_rows": sum(r["cusip_status"] == "UNIQUE_CHECKSUM_INVALID" for r in legacy),
        "legacy_missing_rows": sum(r["cusip_status"] == "MISSING" for r in legacy),
        "xml_cusip_present_rows": sum(r["cusip_candidate_count"] > 0 for r in xml),
        "xml_unique_checksum_valid_rows": sum(r["cusip_status"] == "UNIQUE_CHECKSUM_VALID" for r in xml),
        "xml_unique_checksum_invalid_rows": sum(r["cusip_status"] == "UNIQUE_CHECKSUM_INVALID" for r in xml),
        "xml_missing_or_invalid_format_rows": sum(r["cusip_status"] in {"MISSING", "INVALID_XML_CUSIP_FORMAT"} for r in xml),
        "unique_checksum_valid_rows": sum(r["cusip_status"] == "UNIQUE_CHECKSUM_VALID" for r in results),
        "weighted_legacy_unique_checksum_valid_rate": weighted_rate(legacy, lambda r: r["cusip_status"] == "UNIQUE_CHECKSUM_VALID"),
        "weighted_xml_unique_checksum_valid_rate": weighted_rate(xml, lambda r: r["cusip_status"] == "UNIQUE_CHECKSUM_VALID"),
        "weighted_all_unique_checksum_valid_rate": weighted_rate(results, lambda r: r["cusip_status"] == "UNIQUE_CHECKSUM_VALID"),
        "weighted_index_alias_rate": alias_weight / total_index_weight if total_index_weight else None,
        "nonempty_strata": source_summary.get("nonempty_strata"),
        "eligible_index_population": source_summary.get("eligible_population_after_exclusions"),
        "limitations": [
            "CUSIP checksum validity is a syntactic quality check, not proof that the filing's identifier is correct or maps to the intended traded security.",
            "CUSIP is not a permanent security identifier; effective-dated corporate-action, share-class and issuer mapping is still required.",
            "Legacy extraction accepts only exact nine-character tokens adjacent to a CUSIP label; ambiguous multi-CUSIP filings are quarantined and unusual layouts may be missed.",
            "The hash-stratified sample is drawn from the 2016Q1-2026Q3 filing-index population, not a historical active/inactive eligible-security universe; no formal inferential confidence interval is claimed.",
            "No legacy reporting-person/ownership parser was validated, and no forward returns, features, alpha tests, vendor purchases or production changes were performed."
        ],
    }
    (output_dir / "phase125_sec_13dg_exact_cusip_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    if summary["status"] != "PASS_ARTIFACT_ONLY_CUSIP_AUDIT":
        raise SystemExit(2)
    return summary

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    audit(args.input_dir, args.output_dir)

if __name__ == "__main__":
    main()

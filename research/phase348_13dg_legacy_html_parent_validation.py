#!/usr/bin/env python3
"""Offline validation of legacy-HTML SEC 13D/G predecessor records in Phase 84."""
from __future__ import annotations
import argparse, csv, hashlib, html, json, re
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ZERO = "000000000"

def normalize_accession(value):
    digits = re.sub(r"\D", "", str(value or ""))
    if len(digits) != 18:
        return ""
    return f"{digits[:10]}-{digits[10:12]}-{digits[12:]}"

def normalize_cik(value):
    digits = re.sub(r"\D", "", str(value or ""))
    return digits.zfill(10) if digits and len(digits) <= 10 else digits

def normalize_cusip(value):
    return re.sub(r"\s+", "", str(value or "")).upper()

def cusip_checksum_valid(value):
    cusip = normalize_cusip(value)
    if not re.fullmatch(r"[A-Z0-9*@#]{9}", cusip) or not cusip[-1].isdigit():
        return False
    total = 0
    for i, ch in enumerate(cusip[:8]):
        n = int(ch) if ch.isdigit() else (ord(ch)-55 if "A" <= ch <= "Z" else {"*":36,"@":37,"#":38}.get(ch,-1))
        if n < 0:
            return False
        if i % 2:
            n *= 2
        total += n // 10 + n % 10
    return (10-total%10)%10 == int(cusip[-1])

def parse_acceptance_et(value):
    raw = str(value or "").strip()
    if not re.fullmatch(r"\d{14}", raw):
        return ""
    local = datetime.strptime(raw, "%Y%m%d%H%M%S").replace(tzinfo=ZoneInfo("America/New_York"))
    return local.astimezone(timezone.utc).isoformat()

def parse_legacy_submission(raw):
    text = raw.decode("utf-8", "ignore") if isinstance(raw, bytes) else str(raw)
    hm = re.search(r"<SEC-HEADER>(.*?)</SEC-HEADER>", text, re.I | re.S)
    if not hm:
        raise ValueError("missing SEC-HEADER")
    header = hm.group(1)
    def capture(pattern):
        m = re.search(pattern, header, re.I | re.S)
        return m.group(1).strip() if m else ""
    accession = normalize_accession(capture(r"ACCESSION NUMBER:\s*([0-9-]{20})"))
    form = capture(r"CONFORMED SUBMISSION TYPE:\s*([A-Z0-9 /-]+)")
    filed_raw = capture(r"FILED AS OF DATE:\s*(\d{8})")
    acceptance_raw = capture(r"<ACCEPTANCE-DATETIME>\s*(\d{14})")
    subject_match = re.search(r"SUBJECT COMPANY:\s*(.*?)FILED BY:", header, re.I | re.S)
    subject_block = subject_match.group(1) if subject_match else ""
    cik_match = re.search(r"CENTRAL INDEX KEY:\s*(\d{6,10})", subject_block, re.I)
    name_match = re.search(r"COMPANY CONFORMED NAME:\s*(.*?)\s+CENTRAL INDEX KEY:", subject_block, re.I | re.S)
    subject_cik = normalize_cik(cik_match.group(1)) if cik_match else ""
    subject_name = re.sub(r"\s+", " ", name_match.group(1)).strip() if name_match else ""
    docs = re.findall(r"<DOCUMENT>(.*?)</DOCUMENT>", text, re.I | re.S)
    if not docs:
        raise ValueError("missing DOCUMENT block")
    primary = docs[0]
    type_match = re.search(r"<TYPE>\s*([^\r\n<]+)", primary, re.I)
    file_match = re.search(r"<FILENAME>\s*([^\r\n<]+)", primary, re.I)
    body_match = re.search(r"<TEXT>(.*?)</TEXT>", primary, re.I | re.S)
    body = body_match.group(1) if body_match else primary
    plain = html.unescape(re.sub(r"<[^>]+>", " ", body))
    plain = re.sub(r"\s+", " ", plain)
    found = []
    patterns = (
        r"([A-Z0-9*@#]{9})\s*\(\s*CUSIP\s+Number\s*\)",
        r"CUSIP\s+(?:NO\.?|Number)\s*:?\s*([A-Z0-9*@#]{9})",
    )
    for pattern in patterns:
        found.extend(re.findall(pattern, plain, re.I))
    cusips = sorted(set(normalize_cusip(x) for x in found))
    return {
        "accession": accession, "form": re.sub(r"\s+", " ", form).upper(),
        "filing_date": f"{filed_raw[:4]}-{filed_raw[4:6]}-{filed_raw[6:]}" if len(filed_raw)==8 else "",
        "acceptance_utc": parse_acceptance_et(acceptance_raw),
        "subject_cik": subject_cik, "subject_name": subject_name,
        "primary_doc_type": type_match.group(1).strip().upper() if type_match else "",
        "primary_filename": file_match.group(1).strip() if file_match else "",
        "primary_cusips": cusips, "acceptance_raw_et": acceptance_raw,
    }

def load_csv(path):
    with Path(path).open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def validate_parent(child, parent, header_row, parsed):
    reasons = []
    if parsed["accession"] != parent:
        reasons.append("parent_accession_mismatch")
    parent_form = parsed["form"]
    parent_family = "13D" if "13D" in parent_form else ("13G" if "13G" in parent_form else "")
    if parent_family != str(child.get("family","")).upper():
        reasons.append("parent_form_family_mismatch")
    if parsed["subject_cik"] != normalize_cik(child.get("subject_cik","")):
        reasons.append("parent_subject_cik_mismatch")
    if not parsed["acceptance_utc"] or not child.get("acceptance_utc"):
        reasons.append("missing_acceptance_timestamp")
    else:
        if datetime.fromisoformat(parsed["acceptance_utc"]) >= datetime.fromisoformat(str(child["acceptance_utc"]).replace("Z","+00:00")):
            reasons.append("parent_not_strictly_earlier")
    if not parsed["filing_date"] or parsed["filing_date"] >= str(child.get("filing_date","")):
        reasons.append("parent_filing_date_not_earlier")
    child_cusips = json.loads(child.get("cusips") or "[]")
    child_cusips = sorted(set(normalize_cusip(x) for x in child_cusips))
    if len(parsed["primary_cusips"]) != 1 or parsed["primary_cusips"] != child_cusips:
        reasons.append("parent_child_cusip_not_exact_single_match")
    elif not cusip_checksum_valid(parsed["primary_cusips"][0]) or parsed["primary_cusips"][0] == ZERO:
        reasons.append("parent_child_cusip_invalid")
    if normalize_accession(header_row.get("accession","")) != parent:
        reasons.append("phase84_header_accession_mismatch")
    if normalize_cik(header_row.get("subject_cik","")) != parsed["subject_cik"]:
        reasons.append("phase84_header_subject_mismatch")
    if str(header_row.get("header_form","")).upper() != parent_form:
        reasons.append("phase84_header_form_mismatch")
    if str(header_row.get("acceptance_utc","")) != parsed["acceptance_utc"]:
        reasons.append("phase84_header_acceptance_mismatch")
    return reasons

def run(args):
    p84, p93 = Path(args.phase84_artifact_dir), Path(args.phase93_artifact_dir)
    headers = {normalize_accession(x.get("accession","")): x for x in load_csv(p84/"pilot_header_validation.csv")}
    lineage = load_csv(p93/"phase93_amendment_lineage_audit.csv")
    events = {normalize_accession(x.get("accession","")): x for x in load_csv(p93/"phase93_event_mechanism_audit.csv")}
    targets = [x for x in lineage if x.get("lineage_status") == "explicit_predecessor_header_sample_consistent_xml_unavailable"]
    if len(targets) != 2:
        raise ValueError(f"Expected two header-sample legacy parents, found {len(targets)}")
    results = []
    for child_lineage in targets:
        child_acc = normalize_accession(child_lineage["accession"])
        parent_acc = normalize_accession(child_lineage["xml_previous_accession"])
        child, header = events[child_acc], headers.get(parent_acc)
        if not header:
            raise ValueError(f"Parent not in Phase 84 header sample: {parent_acc}")
        raw_path = p84 / (header.get("raw_file") or f"raw_submissions/{parent_acc}.txt")
        if not raw_path.is_file():
            raise ValueError(f"Parent raw submission missing: {parent_acc}")
        raw = raw_path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if digest != header.get("source_sha256") or str(header.get("source_sha256_valid","")).lower() != "true":
            raise ValueError(f"Parent raw hash mismatch: {parent_acc}")
        parsed = parse_legacy_submission(raw)
        reasons = validate_parent(child, parent_acc, header, parsed)
        results.append({
            "child_accession": child_acc, "parent_accession": parent_acc,
            "subject_cik": parsed["subject_cik"], "family": child_lineage["family"],
            "parent_form": parsed["form"], "parent_filing_date": parsed["filing_date"],
            "parent_acceptance_utc": parsed["acceptance_utc"],
            "child_filing_date": child_lineage["filing_date"],
            "child_acceptance_utc": child_lineage["acceptance_utc"],
            "parent_cusip": parsed["primary_cusips"][0] if len(parsed["primary_cusips"])==1 else "",
            "child_cusip": json.loads(child.get("cusips") or "[]")[0],
            "parent_primary_filename": parsed["primary_filename"],
            "legacy_html": parsed["primary_filename"].lower().endswith((".htm",".html")),
            "raw_sha256": digest, "validation_reasons": reasons,
            "explicit_reference_validated": not reasons,
            "immediate_predecessor_claimed": False,
        })
    summary = {
        "phase": "348-13dg-legacy-html-explicit-predecessor-validation",
        "status": "COMPLETE", "target_references": len(results),
        "verified_legacy_html_parents": sum(x["explicit_reference_validated"] for x in results),
        "failed_parent_validations": sum(not x["explicit_reference_validated"] for x in results),
        "all_parents_legacy_html": all(x["legacy_html"] for x in results),
        "all_parent_child_cusips_match": all(x["parent_cusip"] == x["child_cusip"] for x in results),
        "all_parent_acceptances_strictly_earlier": all(datetime.fromisoformat(x["parent_acceptance_utc"]) < datetime.fromisoformat(x["child_acceptance_utc"]) for x in results),
        "all_subject_ciks_match": all(bool(x["subject_cik"]) for x in results),
        "explicit_predecessor_refs_outside_600_header_sample_remaining": 44,
        "immediate_predecessor_inference_performed": False,
        "new_sec_requests_made": False, "alpha_test_authorized": False,
        "strict_pit_admitted": False, "f80_frozen": True,
    }
    out = Path(args.outdir); out.mkdir(parents=True, exist_ok=True)
    with (out/"phase348_legacy_html_parent_validation.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(results[0]));w.writeheader();w.writerows(results)
    (out/"phase348_summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"summary":summary,"records":results},indent=2))
    if summary["failed_parent_validations"]:
        raise SystemExit(2)
    return summary

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--phase84-artifact-dir",required=True,type=Path)
    p.add_argument("--phase93-artifact-dir",required=True,type=Path)
    p.add_argument("--outdir",default="phase348_output",type=Path)
    run(p.parse_args())

if __name__=="__main__":
    main()

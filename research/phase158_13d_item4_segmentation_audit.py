#!/usr/bin/env python3
"""Phase 158: SEC Schedule 13D Item 4 segmentation and amendment-contamination audit.

This is a deterministic extraction/feasibility audit only. It does not classify
investor intent, create a predictive feature, or treat an amendment as a new trade.
"""
from __future__ import annotations
import argparse, csv, hashlib, html, json, re, statistics
from pathlib import Path
from html.parser import HTMLParser

P124_RUN = 42073725379
P124_ARTIFACT = 13436764625
P124_CSV_SHA = "be2c592c6c26d9f1ea49bda5d29d20e944004b2e2f4a3c3f4fe1f732319c55d5"
P157_RUN = 42224436013
P157_ARTIFACT = 13504962007
P157_CSV_SHA = "154b628436d6c438e54bb953f7d77b0a82f89b5c19373e9f1b642a5140f20072"
P157_ZIP_SHA = "c7c46e51ddda8ac85b60763a337e5cd2273f5af0c522d91f862bdb668791ce4a"

class BlockText(HTMLParser):
    BLOCKS = {"address","article","br","center","div","dl","dt","dd","h1","h2","h3","hr","li","ol","p","pre","table","tbody","td","th","tr","ul"}
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

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def read_csv(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def primary_document(raw: str):
    found = []
    for doc in re.findall(r"<DOCUMENT>(.*?)</DOCUMENT>", raw, re.I | re.S):
        m = re.search(r"<TYPE>\s*([^\r\n<]+)", doc, re.I)
        if not m:
            continue
        form = re.sub(r"\s+", " ", m.group(1)).strip().upper()
        if form not in {"SC 13D", "SC 13D/A"}:
            continue
        x = re.search(r"<TEXT>(.*?)</TEXT>", doc, re.I | re.S)
        body = x.group(1) if x else doc
        if not re.match(r"\s*<PDF>", body, re.I):
            found.append(body)
    if not found:
        raise ValueError("readable primary SC 13D document missing")
    found.sort(key=lambda x: ("<HTML" in x[:2000].upper(), len(re.sub(r"<[^>]+>", " ", x))), reverse=True)
    return found[0]

def text_lines(raw: str):
    parser = BlockText()
    parser.feed(primary_document(raw))
    s = html.unescape("".join(parser.parts)).replace("\xa0", " ").replace("\u200b", " ").replace("\ufeff", " ")
    return [re.sub(r"\s+", " ", x).strip() for x in s.splitlines() if re.sub(r"\s+", " ", x).strip()]

def find_item4_start(lines, max_scan_lines=2500):
    # Search the complete primary document, not only the first 1,000 extracted lines.
    for i in range(min(len(lines), max_scan_lines)):
        window = " ".join(lines[i:i+5])
        if re.search(r"\bITEM\s*4\b", lines[i], re.I) and re.search(r"PURPOSE\s+OF\s+TRANSACTION", window, re.I):
            return i
    return None

def next_item_boundary(lines, start):
    # Accept the next numbered Schedule 13D item (5–9), including standalone
    # headings and common inline heading labels. Do not stop on narrative mentions.
    for i in range(start + 1, len(lines)):
        s = lines[i].strip()
        if re.fullmatch(r"(?i)ITEM\s*[5-9]\s*[.)]?", s):
            m = re.match(r"(?i)ITEM\s*([5-9])", s)
            return i, f"ITEM{m.group(1)}"
        m = re.match(r"(?i)^ITEM\s*([5-9])\s*[.)]\s*(?:INTEREST|SOURCE|CONTRACTS|MATERIAL|OTHER|EXHIBITS|ARRANGEMENTS|SECURITIES|PURPOSE|TRANSACTIONS|GENERAL)\b", s)
        if m:
            return i, f"ITEM{m.group(1)}"
    return None, None

PAGE_NOISE = re.compile(
    r"(?i)^(?:PURPOSE\s+OF\s+TRANSACTION\.?|CUSIP(?:\s+NO\.?)?\s+.*|"
    r"SCHEDULE\s+13D(?:/A)?|PAGE\s+\d+(?:\s+OF\s+\d+(?:\s+PAGES?)?)?|\d{1,3})$"
)

def clean_section(lines):
    kept = []
    for line in lines:
        line = re.sub(r"\s+", " ", line).strip()
        if not line or PAGE_NOISE.fullmatch(line):
            continue
        kept.append(line)
    return "\n".join(kept).strip()

def audit(phase124_dir, phase157_dir, outdir):
    p124 = Path(phase124_dir)
    p157 = Path(phase157_dir)
    b124 = (p124 / "phase124_global_13dg_submission_audit.csv").read_bytes()
    b157 = (p157 / "phase157_legacy_13dg_html_field_audit.csv").read_bytes()
    if sha(b124) != P124_CSV_SHA:
        raise ValueError("Phase 124 immutable CSV hash mismatch")
    if sha(b157) != P157_CSV_SHA:
        raise ValueError("Phase 157 immutable CSV hash mismatch")
    s157 = json.loads((p157 / "phase157_legacy_13dg_html_summary.json").read_text())
    if s157.get("status") != "COMPLETED_LEGACY_HTML_PIT_FEASIBILITY_AUDIT":
        raise ValueError("Phase 157 source summary status mismatch")
    src = s157.get("sources", {})
    if src.get("phase124_run_id") != P124_RUN or src.get("phase124_artifact_id") != P124_ARTIFACT:
        raise ValueError("Phase 157 source lineage mismatch")
    if src.get("phase124_csv_sha256") != P124_CSV_SHA or src.get("legacy_html_filings") != 497:
        raise ValueError("Phase 157 source dimensions/hash mismatch")

    rows124 = read_csv(p124 / "phase124_global_13dg_submission_audit.csv")
    rows157 = read_csv(p157 / "phase157_legacy_13dg_html_field_audit.csv")
    if len(rows124) != 600 or len({r["accession"] for r in rows124}) != 600 or len(rows157) != 497:
        raise ValueError("immutable source dimensions changed")
    p157_by = {r["accession"]: r for r in rows157}
    if len(p157_by) != 497:
        raise ValueError("Phase 157 accession uniqueness failure")

    out = []
    raw_verified = 0
    errors = []
    for r in rows124:
        raw_path = p124 / (r.get("raw_file") or "")
        if not raw_path.is_file():
            errors.append({"accession": r["accession"], "error": "raw submission missing"})
            continue
        raw_bytes = raw_path.read_bytes()
        digest = sha(raw_bytes)
        if digest != r.get("raw_sha256"):
            errors.append({"accession": r["accession"], "error": "raw submission hash mismatch"})
            continue
        raw_verified += 1
        if r.get("is_index_alias", "").lower() == "true" or r.get("xml_present", "").lower() == "true" or r.get("family", "").upper() != "13D":
            continue
        cross = p157_by.get(r["accession"])
        if not cross or cross.get("raw_sha256") != digest or cross.get("family") != "13D":
            errors.append({"accession": r["accession"], "error": "Phase 157 accession/hash join mismatch"})
            continue

        lines = text_lines(raw_bytes.decode("utf-8", "replace"))
        start = find_item4_start(lines)
        amendment = r.get("is_amendment", "").lower() == "true"
        base = {
            "accession": r["accession"],
            "quarter": r.get("quarter"),
            "is_amendment": amendment,
            "filing_date": r.get("filing_date_header"),
            "acceptance_datetime_et": r.get("acceptance_datetime"),
            "sample_weight": float(r.get("sample_weight") or 0),
            "raw_sha256": digest,
            "phase157_item4_flag": cross.get("item4_purpose_section_present", "").lower() == "true",
            "phase157_item4_chars": int(float(cross.get("item4_purpose_chars") or 0)),
        }
        if start is None:
            out.append({**base, "status": "NO_ITEM4_HEADING", "heading_line_1based": None, "boundary_line_1based": None,
                        "boundary_item": None, "section_chars": 0, "section_lines": 0, "section_sha256": None,
                        "no_material_change_only": False, "filing_role": "AMENDMENT_STATE_UPDATE" if amendment else "INITIAL_DISCLOSURE"})
            continue
        end, boundary = next_item_boundary(lines, start)
        if end is None:
            out.append({**base, "status": "NO_NEXT_ITEM_BOUNDARY", "heading_line_1based": start + 1, "boundary_line_1based": None,
                        "boundary_item": None, "section_chars": 0, "section_lines": 0, "section_sha256": None,
                        "no_material_change_only": False, "filing_role": "AMENDMENT_STATE_UPDATE" if amendment else "INITIAL_DISCLOSURE"})
            continue
        cleaned = clean_section(lines[start+1:end])
        no_change = bool(re.fullmatch(r"(?is)no material changes?\.?", cleaned))
        out.append({**base, "status": "EXTRACTED", "heading_line_1based": start + 1, "boundary_line_1based": end + 1,
                    "boundary_item": boundary, "section_chars": len(cleaned), "section_lines": len(cleaned.splitlines()) if cleaned else 0,
                    "section_sha256": sha(cleaned.encode("utf-8")) if cleaned else None,
                    "no_material_change_only": no_change,
                    "filing_role": "AMENDMENT_STATE_UPDATE" if amendment else "INITIAL_DISCLOSURE"})

    if raw_verified != 600 or len(out) != 180 or errors:
        raise ValueError(f"source reconciliation failed: raw={raw_verified}, 13D legacy={len(out)}, errors={errors[:3]}")
    if len({r["accession"] for r in out}) != 180:
        raise ValueError("13D legacy accession uniqueness failure")

    p157_true = sum(r["phase157_item4_flag"] for r in out)
    new_found = sum(r["status"] == "EXTRACTED" for r in out)
    recovered = [r for r in out if r["status"] == "EXTRACTED" and not r["phase157_item4_flag"]]
    missed = [r for r in out if r["status"] != "EXTRACTED" and r["phase157_item4_flag"]]
    if p157_true != 116 or new_found != 117 or len(recovered) != 1 or len(missed) != 0:
        raise ValueError(f"Phase 157 reconciliation changed: p157={p157_true}, new={new_found}, recovered={len(recovered)}, missed={len(missed)}")
    late = [r for r in recovered if (r["heading_line_1based"] or 0) > 1000]
    if len(late) != 1 or late[0]["accession"] != "0001140361-18-032832":
        raise ValueError("expected late Item 4 recovery not reproduced")

    extracted = [r for r in out if r["status"] == "EXTRACTED"]
    by_role = {}
    for amendment, label in ((False, "INITIAL"), (True, "AMENDMENT")):
        group = [r for r in out if r["is_amendment"] == amendment]
        segs = [r for r in group if r["status"] == "EXTRACTED"]
        lengths = [r["section_chars"] for r in segs]
        by_role[label] = {
            "filings": len(group),
            "item4_extracted": len(segs),
            "item4_coverage": round(len(segs)/len(group), 6) if group else None,
            "median_clean_chars": statistics.median(lengths) if lengths else None,
            "p75_clean_chars": round(statistics.quantiles(lengths, n=4, method="inclusive")[2], 2) if len(lengths) >= 2 else (lengths[0] if lengths else None),
            "max_clean_chars": max(lengths) if lengths else None,
            "no_material_change_only": sum(r["no_material_change_only"] for r in segs),
        }
    boundary_counts = {}
    for r in extracted:
        boundary_counts[r["boundary_item"]] = boundary_counts.get(r["boundary_item"], 0) + 1
    summary = {
        "phase": 158,
        "status": "COMPLETED_ITEM4_SEGMENTATION_AND_AMENDMENT_CONTAMINATION_AUDIT",
        "sources": {
            "phase124_run_id": P124_RUN, "phase124_artifact_id": P124_ARTIFACT, "phase124_csv_sha256": sha(b124),
            "phase157_run_id": P157_RUN, "phase157_artifact_id": P157_ARTIFACT, "phase157_csv_sha256": sha(b157),
            "phase157_artifact_zip_sha256": P157_ZIP_SHA,
            "phase124_index_rows": len(rows124), "raw_submission_hashes_verified": raw_verified,
            "phase157_legacy_html_rows": len(rows157), "legacy_13d_rows": len(out)
        },
        "phase157_reconciliation": {
            "prior_item4_flagged": p157_true, "new_item4_sections_extracted": new_found,
            "additional_section_recovered": len(recovered), "prior_flag_not_reproduced": len(missed),
            "recovered_accessions": [r["accession"] for r in recovered],
            "recovered_heading_lines": [r["heading_line_1based"] for r in recovered],
            "reason": "Phase 157 scanned only the first 1,000 extracted text lines; one valid Item 4 heading appears at line 1,317."
        },
        "by_filing_role": by_role,
        "boundary_item_counts": boundary_counts,
        "combined": {
            "item4_extracted": new_found,
            "item4_coverage": round(new_found/len(out), 6),
            "no_item4_heading": sum(r["status"] == "NO_ITEM4_HEADING" for r in out),
            "no_next_item_boundary": sum(r["status"] == "NO_NEXT_ITEM_BOUNDARY" for r in out),
            "amendment_sections_are_state_updates": sum(r["is_amendment"] for r in extracted),
            "initial_sections": sum(not r["is_amendment"] for r in extracted),
            "no_material_change_only": sum(r["no_material_change_only"] for r in extracted),
            "all_amendments_blocked_from_independent_event_count": True
        },
        "decision": {
            "use": "section-level content extraction feasibility only",
            "intent_classification": "NOT_PERFORMED_NO_GOLD_LABELS",
            "amendments": "state updates; never count as independent trades/events without confirmed parent lineage and line-level diff",
            "text_features": "no predictive features or keyword-based sentiment/activism labels created",
            "economic_testing": "NOT_AUTHORIZED_IDENTITY_AND_UNIVERSE_GATES_REMAIN_OPEN",
            "final_holdout_used": False,
            "f80_modified": False
        }
    }
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    with (outdir / "phase158_13d_item4_segments.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(out[0]))
        writer.writeheader()
        writer.writerows(out)
    (outdir / "phase158_13d_item4_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    return summary

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase124-dir", required=True)
    ap.add_argument("--phase157-dir", required=True)
    ap.add_argument("--output-dir", required=True)
    a = ap.parse_args()
    print(json.dumps(audit(a.phase124_dir, a.phase157_dir, a.output_dir), indent=2, sort_keys=True))

if __name__ == "__main__":
    main()

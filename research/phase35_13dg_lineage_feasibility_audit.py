#!/usr/bin/env python3
"""Conservative 13D/13G amendment-lineage audit; never assigns inferred edges."""
import argparse, csv, json, re, unicodedata
from collections import Counter
from pathlib import Path

def norm_name(value):
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(c for c in value if not unicodedata.combining(c)).upper()
    tokens = re.findall(r"[A-Z0-9]+", value)
    suffixes = {"INC","INCORPORATED","CORP","CORPORATION","CO","COMPANY","LLC","LP","LTD","LIMITED","PLC","LLP","NA","SA","AG","NV"}
    while tokens and (tokens[0] == "THE" or tokens[-1] in suffixes):
        if tokens[0] == "THE": tokens = tokens[1:]
        else: tokens = tokens[:-1]
    return " ".join(tokens)

def family(form):
    return "13D" if "13D" in (form or "").upper() else "13G"

def classify_candidate_count(n):
    if n == 0: return "zero_in_panel_candidates"
    if n == 1: return "one_in_panel_candidate_unassigned"
    return "multiple_in_panel_candidates_ambiguous"

def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def load_panel(roots):
    rows, details, quarters = {}, {}, set()
    for root in map(Path, roots):
        detail = root / "reporting_person_crosswalk_detail.csv"
        if detail.exists():
            for d in read_csv(detail):
                if d.get("sample") == "target_subject": details[d["accession"]] = d
        for qdir in root.glob("20*Q*"):
            path = qdir / "target_subject_filings_xml.csv"
            if not path.exists(): continue
            quarters.add(qdir.name)
            for r in read_csv(path):
                if r["accession"] in rows: raise ValueError("Duplicate accession: " + r["accession"])
                rows[r["accession"]] = r
    return list(rows.values()), details, sorted(quarters)

def person_name(row, details):
    d = details.get(row["accession"], {})
    if d.get("crosswalk_status") != "unique_exact_normalized_name_match": return None
    return norm_name(d.get("matched_reporting_person_name", "")) or None

def cusips(row):
    try: return set(json.loads(row.get("subject_issuer_cusips") or "[]"))
    except json.JSONDecodeError: return set()

def audit(rows, details, quarters):
    by_acc = {r["accession"]: r for r in rows}
    out = {"quarters": quarters, "target_subject_accessions": len(rows), "by_family": {}, "economic_tests": False}
    for fam in ("13D", "13G"):
        fr = [r for r in rows if family(r.get("form")) == fam]
        amendments = [r for r in fr if r.get("form", "").upper().endswith("/A")]
        with_ptr = [r for r in amendments if r.get("previous_accession")]
        no_ptr = [r for r in amendments if not r.get("previous_accession")]
        in_panel = []
        outside = 0
        for r in with_ptr:
            p = by_acc.get(r["previous_accession"])
            if p is None: outside += 1
            else: in_panel.append((r,p))
        checks = []
        for r,p in in_panel:
            rn, pn = person_name(r, details), person_name(p, details)
            overlap = bool(cusips(r) & cusips(p))
            prior = []
            if rn and overlap:
                prior = [x for x in fr if x["subject_issuer_cik"] == r["subject_issuer_cik"]
                         and person_name(x, details) == rn and x["filing_date"] < r["filing_date"]
                         and bool(cusips(x) & cusips(r))]
            latest = max(prior, key=lambda x:(x["filing_date"],x["accession"])) if prior else None
            checks.append({
                "same_subject": r["subject_issuer_cik"] == p["subject_issuer_cik"],
                "same_family": family(r["form"]) == family(p["form"]),
                "same_person": bool(rn and pn and rn == pn),
                "cusip_overlap": overlap,
                "comparable_person_cusip": bool(rn and pn and rn == pn and overlap),
                "same_day": r["filing_date"] == p["filing_date"],
                "latest_match": bool(latest and latest["accession"] == p["accession"]),
                "older_reference": bool(latest and latest["accession"] != p["accession"] and p["filing_date"] < r["filing_date"]),
            })
        missing = Counter()
        for r in no_ptr:
            rn, cs = person_name(r, details), cusips(r)
            if not rn or not cs:
                missing["unmatched_person_or_missing_cusip"] += 1
                continue
            candidates = [x for x in fr if x["subject_issuer_cik"] == r["subject_issuer_cik"]
                          and person_name(x, details) == rn and x["filing_date"] < r["filing_date"]
                          and bool(cusips(x) & cs)]
            missing[classify_candidate_count(len(candidates))] += 1
        comparable = sum(x["comparable_person_cusip"] for x in checks)
        out["by_family"][fam] = {
            "filings": len(fr), "amendments": len(amendments),
            "amendments_with_previous_accession": len(with_ptr),
            "previous_accession_coverage": len(with_ptr)/len(amendments) if amendments else None,
            "amendments_without_previous_accession": len(no_ptr),
            "referenced_accession_found_in_panel": len(in_panel),
            "referenced_accession_outside_panel": outside,
            "same_subject": sum(x["same_subject"] for x in checks),
            "same_family": sum(x["same_family"] for x in checks),
            "same_matched_person_name": sum(x["same_person"] for x in checks),
            "cusip_overlap": sum(x["cusip_overlap"] for x in checks),
            "comparable_person_cusip": comparable,
            "pointer_is_latest_candidate": sum(x["comparable_person_cusip"] and x["latest_match"] for x in checks),
            "pointer_references_older_candidate": sum(x["comparable_person_cusip"] and x["older_reference"] for x in checks),
            "same_day_order_unresolved": sum(x["comparable_person_cusip"] and x["same_day"] for x in checks),
            "missing_pointer_candidate_classes": dict(missing),
        }
    return out

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--roots", nargs="+", required=True)
    p.add_argument("--out", required=True)
    a = p.parse_args()
    rows, details, quarters = load_panel(a.roots)
    result = audit(rows, details, quarters)
    result["method"] = {
        "identity": "unique exact-normalized filer-to-reporting-person name match only; not group identity",
        "previousAccessionNumber": "explicit prior-filing reference; not assumed to be the immediate prior amendment",
        "missing_pointer": "unique earlier same-subject/person/CUSIP candidates are counted but never assigned",
        "left_censoring": "bounded four-quarter panel; no candidate does not mean no historical predecessor",
        "knowledge_date": "filing_date only; event_date is not used as KnowledgeDate",
        "forward_returns": False
    }
    Path(a.out).write_text(json.dumps(result, indent=2), encoding="utf-8")

if __name__ == "__main__": main()

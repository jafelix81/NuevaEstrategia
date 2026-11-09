#!/usr/bin/env python3
"""Phase 214: independent DOM cross-parser verification of Phase 213."""
from __future__ import annotations
import argparse, csv, hashlib, json, re
from collections import Counter
from datetime import date
from pathlib import Path
from statistics import median
from phase213_13dg_legacy_event_date_recovery import (
    ARTIFACT_SHA256, CSV_NAME, CSV_SHA256, DATE_PATTERNS, EVENT_LABEL,
    extract_event, family, is_true, parse_date, primary_document, validate_header,
)

def extract_event_bs4(body):
    from bs4 import BeautifulSoup
    visible = BeautifulSoup(body, "lxml").get_text(" ", strip=True)
    labels = list(EVENT_LABEL.finditer(visible))
    if not labels:
        return None, "NO_LABEL", None
    candidates = []
    for label in labels:
        left, right = max(0, label.start() - 220), min(len(visible), label.end() + 220)
        for pattern in DATE_PATTERNS:
            for match in pattern.finditer(visible[left:right]):
                parsed = parse_date(match.group(0))
                if not parsed:
                    continue
                start, end = left + match.start(), left + match.end()
                distance = start - label.start() if start >= label.start() else label.start() - end
                side = 0 if end <= label.start() else 1
                candidates.append((distance, side, start, parsed, match.group(0)))
    if not candidates:
        return None, "LABEL_NO_DATE", None
    candidates.sort(key=lambda item: item[:3])
    chosen = candidates[0]
    return chosen[3], "HTML_LABEL_NEAREST_DATE", {"distance_chars": chosen[0]}

def audit(input_dir: Path, zip_path: Path | None = None):
    zip_sha = hashlib.sha256(zip_path.read_bytes()).hexdigest() if zip_path else None
    if zip_sha is not None and zip_sha != ARTIFACT_SHA256:
        raise ValueError(f"Phase 124 ZIP hash mismatch: {zip_sha}")
    csv_path = input_dir / CSV_NAME
    csv_sha = hashlib.sha256(csv_path.read_bytes()).hexdigest()
    if csv_sha != CSV_SHA256:
        raise ValueError(f"Phase 124 CSV hash mismatch: {csv_sha}")
    with csv_path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 600:
        raise ValueError(f"Expected 600 rows, got {len(rows)}")
    raw_ok = header_ok = primary_ok = xml_ok = 0
    html_n = html_parsed = no_label = label_no_date = 0
    distances, conflicts, actual = [], [], []
    for row in rows:
        raw_bytes = (input_dir / row["raw_file"]).read_bytes()
        if hashlib.sha256(raw_bytes).hexdigest() != row["raw_sha256"]:
            raise ValueError(f"Raw SHA-256 mismatch: {row['accession']}")
        raw_ok += 1
        raw = raw_bytes.decode("latin1")
        validate_header(raw, row)
        header_ok += 1
        if is_true(row.get("is_index_alias")):
            if family(row.get("form")):
                raise ValueError(f"Index alias unexpectedly classified as 13D/G: {row['accession']}")
            continue
        if family(row.get("form")) not in {"13D", "13G"}:
            raise ValueError(f"Unexpected form: {row['accession']}")
        primary = primary_document(raw)
        if primary is None or family(primary[0]) != family(row["form"]):
            raise ValueError(f"Primary document/form mismatch: {row['accession']}")
        primary_ok += 1
        actual.append(row)
        body = primary[1]
        if is_true(row.get("xml_present")):
            parsed, _method = extract_event(body)
            expected = parse_date(row.get("event_date")) if row.get("event_date") else None
            if parsed is None or parsed != expected:
                raise ValueError(f"Structured XML event-date mismatch: {row['accession']}")
            xml_ok += 1
        else:
            html_n += 1
            ref_date, ref_method = extract_event(body)
            dom_date, dom_method, diag = extract_event_bs4(body)
            if ref_date != dom_date or ref_method != dom_method:
                conflicts.append(row["accession"])
            if dom_method == "HTML_LABEL_NEAREST_DATE":
                html_parsed += 1
                distances.append(diag["distance_chars"])
            elif dom_method == "NO_LABEL":
                no_label += 1
            elif dom_method == "LABEL_NO_DATE":
                label_no_date += 1
    if (len(actual), primary_ok, xml_ok, html_n) != (599, 599, 102, 497):
        raise ValueError("Unexpected actual/primary/XML/HTML counts")
    if conflicts:
        raise ValueError(f"Cross-parser conflicts: {conflicts[:10]}")
    parsed_total = xml_ok + html_parsed
    family_summary = {}
    for fam in ("13D", "13G"):
        group = [r for r in actual if family(r["form"]) == fam]
        parsed = []
        for r in group:
            if is_true(r.get("xml_present")):
                d = parse_date(r.get("event_date")) if r.get("event_date") else None
            else:
                raw = (input_dir / r["raw_file"]).read_bytes().decode("latin1")
                body = primary_document(raw)[1]
                d, _m, _diag = extract_event_bs4(body)
            if d:
                parsed.append((r, d))
        total_w = sum(float(r["sample_weight"]) for r in group)
        parsed_w = sum(float(r["sample_weight"]) for r, _ in parsed)
        qend_w = sum(float(r["sample_weight"]) for r, d in parsed if (d.month, d.day) in {(3,31),(6,30),(9,30),(12,31)})
        lags = [(date.fromisoformat(r["filing_date_header"]) - d).days for r, d in parsed]
        family_summary[fam] = {
            "n":len(group),"parsed_n":len(parsed),
            "coverage_sample_weighted_pct":round(100*parsed_w/total_w,4),
            "quarter_end_weighted_pct_within_parsed":round(100*qend_w/parsed_w,4),
            "median_filing_minus_event_days":median(lags),
            "max_filing_minus_event_days":max(lags),
            "over_30_days_n":sum(x>30 for x in lags),
            "over_90_days_n":sum(x>90 for x in lags),
            "over_365_days_n":sum(x>365 for x in lags),
        }
    ordered = sorted(distances)
    result = {
        "phase":214,"status":"PASS_INDEPENDENT_DOM_CROSS_PARSER_REPLICATION",
        "source":{"phase124_run_id":42073725379,"phase124_artifact_id":13436764625,
                  "phase124_artifact_zip_sha256":ARTIFACT_SHA256,
                  "phase124_artifact_zip_sha256_verified":zip_sha==ARTIFACT_SHA256 if zip_sha else None,
                  "phase124_csv_sha256":csv_sha},
        "integrity":{"source_rows":len(rows),"index_aliases_quarantined":1,
                     "raw_submission_sha256_verified":raw_ok,
                     "sec_header_accession_acceptance_filing_date_verified":header_ok,
                     "actual_primary_13dg_documents_verified":primary_ok,
                     "structured_xml_event_dates_reproduced":xml_ok},
        "legacy_html_cross_parser":{"rows":html_n,"same_date_and_status_outcomes":html_n-len(conflicts),
            "parsed_dates":html_parsed,"no_label":no_label,"label_without_unambiguous_date":label_no_date,
            "conflicts":len(conflicts),"reference_engine":"Python html.parser / Phase 213",
            "independent_engine":"BeautifulSoup 4.14.3 + lxml 6.1.1",
            "nearest_label_distance_chars":{"n":len(ordered),"min":min(ordered),"median":median(ordered),
                "p90":ordered[int((len(ordered)-1)*0.90)],"max":max(ordered)}},
        "combined_event_date_recovery":{"actual_submissions":len(actual),"parsed_event_dates":parsed_total,
            "parsed_unweighted_pct":round(100*parsed_total/len(actual),4),
            "unresolved":len(actual)-parsed_total,"by_family":family_summary},
        "interpretation_limits":[
            "Cross-parser agreement validates implementation reproducibility, not legal or economic meaning.",
            "Both engines use the same conservative label and nearest-date rule; no independent gold-standard labels exist.",
            "Event date is not public-knowledge time; preserve SEC-header ACCEPTANCE-DATETIME and use next full regular session conservatively.",
            "No issuer/security crosswalk, amendment-state reconstruction, returns, alpha, bootstrap/LOO or OOS test."
        ],
        "alpha_test_performed":False,"forward_returns_used":False,"final_holdout_used":False,
        "production_changed":False,"f80_changed":False
    }
    return result

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--input-dir",type=Path,required=True)
    parser.add_argument("--output-json",type=Path,required=True)
    parser.add_argument("--zip-path",type=Path,default=None)
    args=parser.parse_args()
    result=audit(args.input_dir,args.zip_path)
    args.output_json.parent.mkdir(parents=True,exist_ok=True)
    args.output_json.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2))

if __name__=="__main__":
    main()

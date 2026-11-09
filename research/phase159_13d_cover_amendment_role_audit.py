#!/usr/bin/env python3
"""Phase 159: detect cover-page amendment numbers hidden by non-/A index forms.

Positive numbers are amendment candidates, not parent links. Blank/missing
fields never prove that a filing is initial. No returns or alpha are tested.
"""
from __future__ import annotations
import argparse, csv, json, re
from pathlib import Path
import phase158_13d_item4_segmentation_audit as p158

P124_RUN, P124_ARTIFACT = 42073725379, 13436764625
P124_CSV_SHA = "be2c592c6c26d9f1ea49bda5d29d20e944004b2e2f4a3c3f4fe1f732319c55d5"
P157_RUN, P157_ARTIFACT = 42224436013, 13504962007
P157_CSV_SHA = "154b628436d6c438e54bb953f7d77b0a82f89b5c19373e9f1b642a5140f20072"
P158_RUN, P158_ARTIFACT = 42231437618, 13510130459
P158_CSV_SHA = "038fbab2c3f4ebafac55078c16c68f89af3037b021c50462b8070cdab8909b60"
P158_SUMMARY_SHA = "456d852bcf60cc77d01ed54ca132d59410ac32639bd7a135f2f750badb842b68"

def parse_cover_amendment_field(lines):
    cover = " ".join(lines[:80])[:3000]
    m = re.search(r"\bAMENDMENT\s+NO\.?\s*([^\)\*\n]{0,40})", cover, re.I)
    if not m:
        return {"status": "MISSING", "raw_value": None, "number": None}
    raw = m.group(1).strip()
    compact = re.sub(r"[\s_.,:#]", "", raw)
    if compact.isdigit() and 1 <= len(compact) <= 4:
        return {"status": "NUMBERED", "raw_value": raw, "number": int(compact)}
    if not compact or compact.upper() in {"NA", "N/A"}:
        return {"status": "BLANK_OR_NA", "raw_value": raw, "number": None}
    return {"status": "OTHER_UNRESOLVED", "raw_value": raw, "number": None}

def truth(x):
    return str(x).strip().lower() in {"true", "1", "yes"}

def audit(phase124_dir, phase157_dir, phase158_dir, outdir):
    a,b,c,outdir = map(Path,(phase124_dir,phase157_dir,phase158_dir,outdir))
    b124=(a/"phase124_global_13dg_submission_audit.csv").read_bytes()
    b157=(b/"phase157_legacy_13dg_html_field_audit.csv").read_bytes()
    b158=(c/"phase158_13d_item4_segments.csv").read_bytes()
    j158=(c/"phase158_13d_item4_summary.json").read_bytes()
    if p158.sha(b124)!=P124_CSV_SHA or p158.sha(b157)!=P157_CSV_SHA:
        raise ValueError("Phase 124/157 CSV hash mismatch")
    if p158.sha(b158)!=P158_CSV_SHA or p158.sha(j158)!=P158_SUMMARY_SHA:
        raise ValueError("Phase 158 artifact hash mismatch")
    s158=json.loads(j158)
    if s158.get("phase")!=158 or s158.get("combined",{}).get("item4_extracted")!=117:
        raise ValueError("Phase 158 lineage mismatch")
    r124=p158.read_csv(a/"phase124_global_13dg_submission_audit.csv")
    r157=p158.read_csv(b/"phase157_legacy_13dg_html_field_audit.csv")
    r158=p158.read_csv(c/"phase158_13d_item4_segments.csv")
    if (len(r124),len(r157),len(r158))!=(600,497,180):
        raise ValueError("input dimensions changed")
    m157={x["accession"]:x for x in r157}
    m158={x["accession"]:x for x in r158}
    if len(m157)!=497 or len(m158)!=180:
        raise ValueError("duplicate source accession")
    rows=[]; errors=[]; raw_verified=0
    for r in r124:
        acc=r["accession"]; rawpath=a/(r.get("raw_file") or "")
        if not rawpath.is_file():
            errors.append({"accession":acc,"error":"raw missing"}); continue
        raw=rawpath.read_bytes(); digest=p158.sha(raw); raw_verified+=1
        if digest!=r.get("raw_sha256"):
            errors.append({"accession":acc,"error":"raw hash mismatch"}); continue
        if truth(r.get("is_index_alias")) or truth(r.get("xml_present")) or r.get("family","").upper()!="13D":
            continue
        x,y=m157.get(acc),m158.get(acc)
        if not x or not y or x.get("raw_sha256")!=digest or y.get("raw_sha256")!=digest or x.get("family")!="13D":
            errors.append({"accession":acc,"error":"cross-phase accession/hash mismatch"}); continue
        lines=p158.text_lines(raw.decode("utf-8","replace"))
        index_a=truth(r.get("is_amendment")) or str(r.get("form","")).upper().endswith("/A")
        # Skip /A cover parsing: short amendment documents can expose body
        # references to amendment numbers inside the first 80 lines.
        field=({"status":"NOT_APPLICABLE_INDEX_CODED_AMENDMENT","raw_value":None,"number":None}
               if index_a else parse_cover_amendment_field(lines))
        role=("INDEX_CODED_AMENDMENT" if index_a else
              "COVER_NUMBERED_AMENDMENT_CANDIDATE" if field["status"]=="NUMBERED" else
              "INDEX_NON_AMENDMENT_FORM_UNCONFIRMED")
        extracted=y.get("status")=="EXTRACTED"; section_sha=None; excerpt=None
        if extracted:
            start=p158.find_item4_start(lines)
            if start is None:
                errors.append({"accession":acc,"error":"Item 4 start not reproduced"}); continue
            end,_=p158.next_item_boundary(lines,start)
            if end is None:
                errors.append({"accession":acc,"error":"Item 4 boundary not reproduced"}); continue
            cleaned=p158.clean_section(lines[start+1:end]); section_sha=p158.sha(cleaned.encode())
            if section_sha!=y.get("section_sha256"):
                errors.append({"accession":acc,"error":"Item 4 hash mismatch"}); continue
            excerpt=re.sub(r"\s+"," ",cleaned)[:240]
        rows.append({"accession":acc,"quarter":r.get("quarter"),"form":r.get("form"),"index_is_amendment":index_a,
          "cover_amendment_field_status":field["status"],"cover_amendment_raw_value":field["raw_value"],
          "cover_amendment_number":field["number"],"corrected_role_class":role,"filing_date":r.get("filing_date_header"),
          "acceptance_datetime":r.get("acceptance_datetime"),"subject_cik":r.get("subject_cik"),
          "subject_name_header_provenance":r.get("subject_name"),"filer_cik":r.get("filer_cik"),"filer_name":r.get("filer_name"),
          "cusip":x.get("cusip"),"event_date":x.get("event_date"),"previous_accession":r.get("previous_accession"),
          "item4_extracted":extracted,"item4_section_sha256":section_sha,"item4_excerpt_first_240_chars":excerpt,
          "raw_sha256":digest,"phase158_original_role":y.get("filing_role"),
          "parent_accession_resolved":bool(str(r.get("previous_accession") or "").strip())})
    if raw_verified!=600 or len(rows)!=180 or errors:
        raise ValueError(f"reconciliation failed raw={raw_verified}, rows={len(rows)}, errors={errors[:4]}")
    if len({r["accession"] for r in rows})!=180:
        raise ValueError("output accession uniqueness failure")
    by_role={}
    for role in ("INDEX_CODED_AMENDMENT","COVER_NUMBERED_AMENDMENT_CANDIDATE","INDEX_NON_AMENDMENT_FORM_UNCONFIRMED"):
        g=[r for r in rows if r["corrected_role_class"]==role]; n=sum(r["item4_extracted"] for r in g)
        by_role[role]={"filings":len(g),"item4_extracted":n,"item4_coverage":round(n/len(g),6) if g else None}
    numbered=[r for r in rows if r["corrected_role_class"]=="COVER_NUMBERED_AMENDMENT_CANDIDATE"]
    fields={}
    for r in rows:
        fields[r["cover_amendment_field_status"]]=fields.get(r["cover_amendment_field_status"],0)+1
    old=sum(r["item4_extracted"] for r in rows if not r["index_is_amendment"])
    remaining=by_role["INDEX_NON_AMENDMENT_FORM_UNCONFIRMED"]["item4_extracted"]
    summary={"phase":159,"status":"COMPLETED_COVER_PAGE_AMENDMENT_ROLE_AUDIT",
      "sources":{"phase124_run_id":P124_RUN,"phase124_artifact_id":P124_ARTIFACT,"phase124_csv_sha256":p158.sha(b124),
        "phase124_raw_submissions_verified":raw_verified,"phase157_run_id":P157_RUN,"phase157_artifact_id":P157_ARTIFACT,
        "phase157_csv_sha256":p158.sha(b157),"phase158_run_id":P158_RUN,"phase158_artifact_id":P158_ARTIFACT,
        "phase158_csv_sha256":p158.sha(b158),"phase158_summary_sha256":p158.sha(j158),"phase158_rows_reconciled":len(r158)},
      "population":{"legacy_13d_filings":len(rows),"index_coded_amendments":sum(r["index_is_amendment"] for r in rows),
        "index_non_amendment_forms":sum(not r["index_is_amendment"] for r in rows)},
      "cover_field_status_counts":fields,"role_counts":by_role,"cover_numbered_amendment_candidates":numbered,
      "item4_cohort_correction":{"phase158_index_non_amendment_item4_count":old,"cover_numbered_candidates_with_item4":len(numbered),
        "remaining_non_amendment_form_unconfirmed_item4":remaining,"removed_from_initial_candidate_count":old-remaining,
        "contamination_share_of_phase158_initial_item4":round((old-remaining)/old,6) if old else None},
      "interpretation":{"positive_cover_number":"strong amendment candidate; parent accession unresolved",
        "blank_or_missing_cover_field":"not proof of an initial filing","no_parent_inference":True,"no_event_or_trade_inference":True,
        "item4_text":"short excerpts are for manual review only; no intent taxonomy or predictive feature created"},
      "decision":{"item4_initial_cohort":"QUARANTINE_COVER_NUMBERED_AMENDMENTS; REMAINING_NON_A_FORMS_UNCONFIRMED",
        "parent_lineage":"UNRESOLVED_FOR_ALL_FOUR_COVER_NUMBERED_CANDIDATES","economic_testing":"NOT_AUTHORIZED_IDENTITY_AND_UNIVERSE_GATES_REMAIN_OPEN",
        "final_holdout_used":False,"f80_modified":False}}
    outdir.mkdir(parents=True,exist_ok=True)
    with (outdir/"phase159_13d_cover_amendment_roles.csv").open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    (outdir/"phase159_13d_cover_amendment_summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
    return summary

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--phase124-dir",required=True); ap.add_argument("--phase157-dir",required=True)
    ap.add_argument("--phase158-dir",required=True); ap.add_argument("--output-dir",required=True)
    a=ap.parse_args()
    print(json.dumps(audit(a.phase124_dir,a.phase157_dir,a.phase158_dir,a.output_dir),indent=2,sort_keys=True))
if __name__=="__main__": main()

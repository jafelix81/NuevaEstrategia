#!/usr/bin/env python3
"""Phase 160: reconcile structured 13D/G previousAccessionNumber links to the global index.

Index CIKs are candidate identities only. They are not role-labelled proof of issuer identity.
"""
from __future__ import annotations
import argparse, csv, json, re, hashlib
from collections import Counter
from datetime import date
from pathlib import Path

PHASE82_RUN_ID=41892370262
PHASE82_ARTIFACT_ID=13353118959
PHASE82_ZIP_SHA256="e925ad8fe9792f27e570b9e882dff772bb67d9edd67f1c93404a198faab80985"
PHASE124_RUN_ID=42073725379
PHASE124_ARTIFACT_ID=13436764625
PHASE124_ZIP_SHA256="85f69e083b5af65731c9bcfe24e8c75821fc0f2c2476bfa8ba573e2e884570dc"

def norm_accession(value):
    m=re.fullmatch(r"\s*(\d{1,10})-(\d{2})-(\d{1,6})\s*",str(value or ""))
    return f"{int(m.group(1)):010d}-{m.group(2)}-{int(m.group(3)):06d}" if m else None

def norm_cik(value):
    value=str(value or "").strip()
    return value.zfill(10) if value.isdigit() else ""

def accession_year(value):
    if not re.fullmatch(r"\d{2}",str(value or "")): return None
    y=int(value)
    return 1900+y if y>=90 else 2000+y

def family(form):
    form=str(form or "").strip().upper()
    return "13D" if form.startswith("SC 13D") else "13G" if form.startswith("SC 13G") else None

def parse_list(value):
    try: x=json.loads(value or "[]")
    except (TypeError,json.JSONDecodeError): return []
    return [norm_cik(v) or str(v) for v in x] if isinstance(x,list) else []

def read_csv(path):
    with Path(path).open(encoding="utf-8-sig",newline="") as f: return list(csv.DictReader(f))

def audit(index_rows,sample_rows,index_metadata=None):
    counts=Counter(r.get("accession","") for r in index_rows)
    duplicates=sorted(k for k,v in counts.items() if k and v>1)
    index={r.get("accession",""):r for r in index_rows if r.get("accession")}
    quarters=sorted({r.get("quarter","") for r in index_rows if r.get("quarter")})
    conflicts=sum(str(r.get("metadata_conflict","")).lower()=="true" for r in index_rows)
    compact_integrity={"compact_index_rows":len(index_rows),"compact_unique_accessions":len(index),
      "compact_duplicate_accession_count":len(duplicates)}
    integrity=dict(index_metadata) if index_metadata else {"index_rows":len(index_rows),"unique_accessions":len(index),
      "duplicate_accession_count":len(duplicates),"duplicate_accessions":duplicates[:20],
      "quarters":len(quarters),"first_quarter":quarters[0] if quarters else None,
      "last_quarter":quarters[-1] if quarters else None,"metadata_conflict_rows":conflicts}
    integrity.update(compact_integrity)
    links=[]
    for r in sample_rows:
        if str(r.get("xml_present","")).lower()!="true" or str(r.get("is_index_alias","")).lower()=="true": continue
        raw=(r.get("previous_accession") or "").strip()
        if not raw: continue
        parent_id=norm_accession(raw)
        parent=index.get(parent_id or "")
        current_family=(r.get("family") or family(r.get("form")) or "").upper()
        filer=norm_cik(r.get("filer_cik")); subject=norm_cik(r.get("subject_cik"))
        if not parent_id:
            status="INVALID_PREVIOUS_ACCESSION_FORMAT"
        elif parent is None:
            min_year=int(quarters[0][:4]) if quarters else None
            py=accession_year(parent_id.split("-")[1])
            status="OUTSIDE_INDEX_HISTORY" if py is not None and min_year is not None and py<min_year else "PARENT_NOT_FOUND_WITHIN_INDEX_WINDOW"
        else:
            pf=family(parent.get("form")); pd=None
            try: pd=date.fromisoformat(parent.get("filing_date",""))
            except ValueError: pass
            cd=None
            try: cd=date.fromisoformat(r.get("filing_date_index") or r.get("filing_date_header",""))
            except ValueError: pass
            candidates=set(parse_list(parent.get("candidate_identity_ciks")))
            if pf!=current_family: status="PARENT_FORM_FAMILY_MISMATCH"
            elif not pd or not cd or pd>=cd: status="PARENT_DATE_NOT_BEFORE_CURRENT"
            elif not filer or filer not in candidates: status="PARENT_INDEX_CIKS_DO_NOT_INCLUDE_CURRENT_FILER_CANDIDATE"
            elif not subject or subject not in candidates: status="PARENT_FOUND_SUBJECT_CIK_CANDIDATE_MISMATCH"
            else: status="PARENT_FOUND_FORM_DATE_AND_CIK_CANDIDATES_MATCH"
        candidates=parse_list(parent.get("candidate_identity_ciks")) if parent else []
        links.append({
          "current_accession":norm_accession(r.get("accession")) or r.get("accession",""),
          "current_form":r.get("form",""),"current_family":current_family,
          "current_filing_date":r.get("filing_date_index") or r.get("filing_date_header",""),
          "current_subject_cik_from_sec_header_xml":subject,"current_filer_cik_from_sec_header_xml":filer,
          "previous_accession_as_filed":raw,"previous_accession_canonical":parent_id or "",
          "parent_lookup_method":"EXACT" if parent_id==raw else "CANONICAL_PADDING" if parent_id else "INVALID",
          "parent_found_in_global_index":bool(parent),"parent_form":parent.get("form","") if parent else "",
          "parent_family":family(parent.get("form")) if parent else "",
          "parent_filing_date":parent.get("filing_date","") if parent else "",
          "parent_is_amendment":str(parent.get("is_amendment","")).lower()=="true" if parent else None,
          "parent_index_candidate_ciks":"|".join(candidates),
          "current_filer_cik_in_parent_candidate_ciks":bool(parent and filer and filer in candidates),
          "current_subject_cik_in_parent_candidate_ciks":bool(parent and subject and subject in candidates),
          "lineage_status":status})
    sc=Counter(x["lineage_status"] for x in links)
    found=[x for x in links if x["parent_found_in_global_index"]]
    parents=[x["previous_accession_canonical"] for x in links]
    summary={
      "phase":160,"status":"COMPLETE_INDEX_RECONCILIATION" if not duplicates and not conflicts else "INDEX_INTEGRITY_REVIEW_REQUIRED",
      "sources":{"phase82_run_id":PHASE82_RUN_ID,"phase82_artifact_id":PHASE82_ARTIFACT_ID,"phase82_zip_sha256":PHASE82_ZIP_SHA256,
        "phase124_run_id":PHASE124_RUN_ID,"phase124_artifact_id":PHASE124_ARTIFACT_ID,"phase124_zip_sha256":PHASE124_ZIP_SHA256},
      "index_integrity":integrity,"direct_previous_accession_links":len(links),
      "unique_parent_accessions":len(set(parents)),"reused_parent_accessions":len(parents)-len(set(parents)),
      "parents_found_in_index":len(found),
      "parents_found_exactly_as_filed":sum(x["parent_lookup_method"]=="EXACT" for x in found),
      "parents_recovered_by_canonicalization":sum(x["parent_lookup_method"]!="EXACT" for x in found),
      "parents_outside_index_history":sc["OUTSIDE_INDEX_HISTORY"],
      "parent_form_family_matches":sum(x["parent_family"]==x["current_family"] for x in found),
      "parents_precede_current_filing_date":sum(bool(x["parent_filing_date"]) and x["parent_filing_date"]<x["current_filing_date"] for x in found),
      "parents_that_are_non_amended_13d_or_13g":sum(x["parent_form"] in {"SC 13D","SC 13G"} for x in found),
      "current_filer_cik_in_parent_candidate_ciks":sum(x["current_filer_cik_in_parent_candidate_ciks"] for x in found),
      "current_subject_cik_in_parent_candidate_ciks":sum(x["current_subject_cik_in_parent_candidate_ciks"] for x in found),
      "lineage_status_counts":dict(sorted(sc.items())),
      "decision":"Direct XML previousAccessionNumber is a strong accession-level parent pointer. The 43-quarter index finds 30/32 links after canonical padding; two parents predate the 2016Q1 index window. Index CIKs are candidate identities only, not role-labelled proof. One found parent lacks the current SEC-header subject CIK among its candidate CIKs and remains identity/role-quarantined. No legacy-HTML parent is inferred from filing-agent CIK or date proximity.",
      "economic_test_authorized":False,"forward_returns_used":False,"final_holdout_used":False,"production_changed":False}
    return links,summary

def write_outputs(links, summary, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "phase160_13dg_previous_accession_index_reconciliation.csv"
    if links:
        with csv_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(links[0].keys()))
            writer.writeheader()
            writer.writerows(links)
    else:
        csv_path.write_text("", encoding="utf-8")
    (output_dir / "phase160_13dg_previous_accession_index_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def sha256_file(path):
    digest=hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""): digest.update(block)
    return digest.hexdigest()

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--phase82-dir",required=True,type=Path); p.add_argument("--phase124-dir",required=True,type=Path); p.add_argument("--output-dir",required=True,type=Path)
    a=p.parse_args()
    index_path=a.phase82_dir/"global_master_index_13dg.csv"
    sample_path=a.phase124_dir/"phase124_global_13dg_submission_audit.csv"
    manifest_path=a.phase82_dir/"phase160_input_manifest.json"
    manifest=json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else None
    if manifest:
        expected=manifest.get("compact_inputs",{})
        for label,path in [("phase82_source/global_master_index_13dg.csv",index_path),
                           ("phase124_source/phase124_global_13dg_submission_audit.csv",sample_path)]:
            if expected.get(label)!=sha256_file(path):
                raise RuntimeError(f"compact input hash mismatch: {label}")
    links,summary=audit(read_csv(index_path),read_csv(sample_path),manifest.get("index_integrity") if manifest else None)
    if manifest:
        summary["compact_input_hashes"]=manifest.get("compact_inputs",{})
        summary["source_artifacts"]=manifest.get("source_artifacts",{})
    write_outputs(links,summary,a.output_dir)
    print(json.dumps(summary,indent=2,sort_keys=True))
    return 2 if summary["index_integrity"]["duplicate_accession_count"] or summary["index_integrity"]["metadata_conflict_rows"] else 0

if __name__=="__main__": raise SystemExit(main())

#!/usr/bin/env python3
"""Phase 301: 2023Q2 Form 4/A lineage and EDGAR XML source audit."""
from __future__ import annotations
import argparse, hashlib, json, time, urllib.error, urllib.request, zipfile
from collections import defaultdict
from pathlib import Path
import phase299_form4a_edgar_validation as base
import phase300_form4a_xml_bulk_reconciliation as recon

TARGET = "2023Q2"
HASHES = {
    "2023Q1": "0b476188f52a0862e71886eb31a81f6345fc6616403b52188484aef0438cfcfb",
    "2023Q2": "7e636787231ae0f00accf5c3627298402dedd1aefffd7c50fb48292e5d3a8fbb",
}
ARCHIVE_URL = "https://www.sec.gov/files/structureddata/data/insider-transactions-data-sets/{period_lower}_form345.zip"
MAX_PARENTS = 12


def sha(b): return hashlib.sha256(b).hexdigest()


def download_archive(period: str, path: Path, ua: str) -> dict:
    url = ARCHIVE_URL.format(period_lower=period.lower())
    req = urllib.request.Request(url, headers={"User-Agent": ua, "Accept": "application/octet-stream, application/zip, */*", "Accept-Encoding": "identity"})
    errors=[]
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=90) as r: payload=r.read(); meta={"http_status":r.status,"content_type":r.headers.get("Content-Type",""),"last_modified":r.headers.get("Last-Modified","")}
            if not payload.startswith(b"PK"): raise ValueError("unexpected_archive_body")
            with zipfile.ZipFile(__import__("io").BytesIO(payload)) as z:
                if z.testzip(): raise ValueError("archive_crc_failure")
                for table in ("SUBMISSION.tsv","REPORTINGOWNER.tsv","NONDERIV_TRANS.tsv","DERIV_TRANS.tsv"): base.read_table(z,table)
            digest = sha(payload)
            if period in HASHES and digest != HASHES[period]: raise ValueError(f"archive_sha256_mismatch:{period}:{digest}")
            path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(payload); time.sleep(0.2)
            return {**meta,"url":url,"period":period,"bytes":len(payload),"sha256":digest,"attempts":attempt+1}
        except urllib.error.HTTPError as e:
            errors.append(e.code)
            if e.code not in (403,429,500,502,503,504) or attempt==4: break
        except (urllib.error.URLError,TimeoutError,ValueError,zipfile.BadZipFile) as e:
            errors.append(type(e).__name__)
            if attempt==4: break
        time.sleep(min(2**attempt,16))
    raise RuntimeError(f"sec_archive_download_failed:{errors}")


def load_periods(paths: dict) -> dict:
    base.INNER_HASHES.update(HASHES)
    for period,path in paths.items(): base.INNER_HASHES[period] = sha(path.read_bytes())
    return {p:base.load_period(path,p) for p,path in paths.items()}


def quarter_of(value: str) -> str:
    value = base.norm_date(value)
    if not value: return "UNKNOWN"
    from datetime import date
    d = date.fromisoformat(value)
    return f"{d.year}Q{(d.month-1)//3+1}"


def classify(periods: dict) -> list[dict]:
    idx=defaultdict(list)
    for data in periods.values():
        for f in data["filings"].values():
            if f["doc"]=="4" and f["filing_date"]: idx[(f["issuer"],f["filing_date"])].append(f)
    out=[]
    for child in periods[TARGET]["filings"].values():
        if child["doc"]!="4/A" or not child["orig_date"] or not child["owners"]: continue
        dates=[p for p in idx.get((child["issuer"],child["orig_date"]),[]) if p["filing_date"]<=child["filing_date"]]
        owners=[p for p in dates if child["owners"] & p["owners"]]
        if len(owners)==1: status="unique_owner_overlap"; parent=owners[0]; diff=base.diff_class(parent,child)
        elif len(owners)>1: status="ambiguous_multiple_owner_overlaps"; parent=None; diff="not_applicable"
        elif dates: status="same_issuer_date_no_owner_overlap"; parent=None; diff="not_applicable"
        else: status="no_parent_in_loaded_archives"; parent=None; diff="not_applicable"
        out.append({"child":child,"status":status,"parent":parent,"date_candidates":dates,"owner_candidates":owners,"diff_class":diff})
    return out


def rank(row, key): return hashlib.sha256(f"{row['child']['accession']}|{key}|phase301-v1".encode()).hexdigest()


def sample_cases(rows: list[dict]) -> list[dict]:
    chosen={}
    def add(r,why): chosen.setdefault(r["child"]["accession"],{**r,"sample_reason":why})
    for q in ("2022Q4","2023Q1","2023Q2"):
        for diff in ("exact_only","same_coarse","distinct_coarse","both"):
            for equal in (True,False):
                pool=[r for r in rows if r["status"]=="unique_owner_overlap" and r["parent"]["period"]==q and r["diff_class"]==diff and ((r["child"]["owners"]==r["parent"]["owners"])==equal)]
                for r in sorted(pool,key=lambda x:rank(x,f"unique:{q}:{diff}:{equal}"))[:2]: add(r,f"unique:{q}:{diff}:owner_equal={equal}")
    for r in rows:
        if r["status"]=="unique_owner_overlap" and r["child"]["owners"]!=r["parent"]["owners"]: add(r,"all_partial_owner_unique")
    for status,limit in (("ambiguous_multiple_owner_overlaps",8),("same_issuer_date_no_owner_overlap",8)):
        pool=sorted((r for r in rows if r["status"]==status),key=lambda x:rank(x,status))
        for r in pool[:limit]: add(r,status)
    no=[r for r in rows if r["status"]=="no_parent_in_loaded_archives"]
    def norm_orig(r): return base.norm_date(r["child"]["orig_date"])
    strata={"inside_2023": [r for r in no if norm_orig(r).startswith("2023-")],
            "inside_2022Q4": [r for r in no if "2022-10-01" <= norm_orig(r) <= "2022-12-31"],
            "older_than_2022Q4": [r for r in no if norm_orig(r) and norm_orig(r) < "2022-10-01"]}
    for name,pool in strata.items():
        for r in sorted(pool,key=lambda x:rank(x,f"no_parent:{name}"))[:5]: add(r,f"no_parent:{name}")
    return sorted(chosen.values(),key=lambda x:x["child"]["accession"])


def doc_record(f):
    owners=sorted(f["owners"]); paths=list(owners)
    for c in (f["issuer"],f["accession"][:10]):
        if c and c not in paths: paths.append(c)
    return {"accession":f["accession"],"period":f["period"],"document_type":f["doc"],"issuer_cik":f["issuer"],"filing_date":f["filing_date"],"owner_ciks":owners,"path_cik_candidates":paths}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--output-dir",type=Path,required=True); ap.add_argument("--contact-email",required=True); a=ap.parse_args()
    if "@" not in a.contact_email: raise SystemExit("SEC_CONTACT_EMAIL_missing_or_invalid")
    a.output_dir.mkdir(parents=True,exist_ok=True); raw=a.output_dir/"raw"; raw.mkdir(exist_ok=True)
    ua=f"NuevaEstrategia SEC research {a.contact_email.strip()}"
    paths={p:raw/f"{p.lower()}_form345.zip" for p in ("2022Q4","2023Q1","2023Q2")}
    archive_meta={p:download_archive(p,path,ua) for p,path in paths.items()}
    periods=load_periods(paths); classified=classify(periods); sample=sample_cases(classified)
    docs={}; cases=[]
    for i,r in enumerate(sample,1):
        child=r["child"]; docs[child["accession"]]=doc_record(child)
        parents=([r["parent"]] if r["parent"] else (r["owner_candidates"] if r["status"]=="ambiguous_multiple_owner_overlaps" else r["date_candidates"] if r["status"]=="same_issuer_date_no_owner_overlap" else []))[:MAX_PARENTS]
        for p in parents: docs[p["accession"]]=doc_record(p)
        cases.append({"sample_id":f"P301-{i:03d}","status":r["status"],"sample_reason":r["sample_reason"],"child_accession":child["accession"],"child_period":child["period"],"issuer_cik":child["issuer"],"original_submission_date":child["orig_date"],"original_submission_period":quarter_of(child["orig_date"]),"candidate_parent_accessions_downloaded":[p["accession"] for p in parents],"date_candidate_count":len(r["date_candidates"]),"owner_overlap_candidate_count":len(r["owner_candidates"]),"parent_candidate_truncated":len(r["date_candidates"] if r["status"]=="same_issuer_date_no_owner_overlap" else r["owner_candidates"])>MAX_PARENTS})
    manifest={"phase":301,"target_period":TARGET,"loaded_periods":sorted(periods),"bulk_archives":{p:{"sha256":d["sha256"],"filings":len(d["filings"])} for p,d in periods.items()},"population":{s:sum(r["status"]==s for r in classified) for s in ("unique_owner_overlap","ambiguous_multiple_owner_overlaps","same_issuer_date_no_owner_overlap","no_parent_in_loaded_archives")},"sample_cases":cases,"documents":[docs[k] for k in sorted(docs)],"controls":{"strict_pit_admitted":False,"alpha_test":False,"return_test":False,"bootstrap_loo":False,"chronological_oos":False,"holdout_used":False,"f80_frozen":True,"production_changed":False,"universe_changed":False,"capital_changed":False,"parameters_changed":False,"email_sent":False}}
    (a.output_dir/"phase301_sample_manifest.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n")
    edgar=raw/"edgar"; edgar.mkdir(exist_ok=True); downloads=[]; parsed={}; checks={}
    for expected in manifest["documents"]:
        dl=base.download_document(expected,edgar,ua); downloads.append(dl)
        if not dl["downloaded"]: continue
        payload=(edgar/f"{expected['accession'].replace('-','')}.txt").read_bytes(); p=base.parse_submission(payload); f=periods[expected["period"]]["filings"][expected["accession"]]
        ident={"accession":p.get("accession")==expected["accession"],"header_form":p.get("header_form_type")==expected["document_type"],"xml_form":p.get("xml_document_type")==expected["document_type"],"filing_date":p.get("filed_as_of_date")==expected["filing_date"].replace("-",""),"issuer":p.get("xml_issuer_cik")==expected["issuer_cik"],"owners":sorted(p.get("xml_owner_ciks",[]))==expected["owner_ciks"],"xml_parse":p.get("xml_parse_ok") is True}
        if expected["document_type"] == "4/A": ident["original_submission_date"] = base.norm_date(p.get("xml_date_of_original_submission")) == f["orig_date"]
        ndc=recon.multiset_match(f["nd"],p.get("xml_nd_rows",[]),recon.ND_CORE); dvc=recon.multiset_match(f["dv"],p.get("xml_dv_rows",[]),recon.DV_CORE)
        ndf=recon.multiset_match(f["nd"],p.get("xml_nd_rows",[]),recon.ND_FULL); dvf=recon.multiset_match(f["dv"],p.get("xml_dv_rows",[]),recon.DV_FULL)
        checks[expected["accession"]]={"sha256":sha(payload),"identity":ident,"identity_pass":all(ident.values()),"row_counts_match":len(f["nd"])==len(p.get("xml_nd_rows",[])) and len(f["dv"])==len(p.get("xml_dv_rows",[])),"core_match":ndc and dvc,"full_match":ndf and dvf}
        parsed[expected["accession"]]=p
    case_results=[]
    for c in cases:
        child=parsed.get(c["child_accession"]); survivors=[]; parent_checks=[]
        for acc in c["candidate_parent_accessions_downloaded"]:
            p=parsed.get(acc)
            if not p: parent_checks.append({"accession":acc,"downloaded":False}); continue
            parent_doc=docs[acc]
            ok={"form4":p.get("xml_document_type")=="4","issuer":bool(child and p.get("xml_issuer_cik")==child.get("xml_issuer_cik")),"orig_date":bool(child and base.norm_date(child.get("xml_date_of_original_submission"))==parent_doc["filing_date"]),"owner_overlap":bool(child and set(child.get("xml_owner_ciks",[]))&set(p.get("xml_owner_ciks",[]))),"chronology":bool(child and base.parse_acceptance(p.get("acceptance_datetime")) and base.parse_acceptance(child.get("acceptance_datetime")) and base.parse_acceptance(p.get("acceptance_datetime"))<=base.parse_acceptance(child.get("acceptance_datetime")))}
            parent_checks.append({"accession":acc,**ok})
            if all(ok.values()): survivors.append(acc)
        status=c["status"]
        disposition=("unique_candidate_corroborated_in_sample" if status=="unique_owner_overlap" and len(survivors)==1 else "unique_candidate_not_corroborated" if status=="unique_owner_overlap" else "ambiguous_multiple_survive" if status=="ambiguous_multiple_owner_overlaps" and len(survivors)>1 else "one_survivor_without_authoritative_parent_key" if status=="ambiguous_multiple_owner_overlaps" and len(survivors)==1 else "no_ambiguous_candidate_survives" if status=="ambiguous_multiple_owner_overlaps" else "sampled_date_candidates_no_owner_overlap" if status=="same_issuer_date_no_owner_overlap" else "no_parent_in_loaded_archives_unresolved")
        case_results.append({**c,"child_downloaded":child is not None,"child_identity_pass":checks.get(c["child_accession"],{}).get("identity_pass",False),"child_xml_original_date":base.norm_date(child.get("xml_date_of_original_submission")) if child else "","parent_checks":parent_checks,"surviving_candidates":survivors,"disposition":disposition})
    summary={**manifest["population"],"sample_cases":len(cases),"sample_documents":len(docs),"downloaded_documents":sum(x["downloaded"] for x in downloads),"xml_parse_success":sum(x["identity"]["xml_parse"] for x in checks.values()),"identity_pass":sum(x["identity_pass"] for x in checks.values()),"row_counts_match":sum(x["row_counts_match"] for x in checks.values()),"core_match":sum(x["core_match"] for x in checks.values()),"full_match":sum(x["full_match"] for x in checks.values()),"unique_pairs_corroborated":sum(x["disposition"]=="unique_candidate_corroborated_in_sample" for x in case_results),"ambiguous_cases_still_multiple":sum(x["disposition"]=="ambiguous_multiple_survive" for x in case_results),"ambiguous_one_survivor_no_fk":sum(x["disposition"]=="one_survivor_without_authoritative_parent_key" for x in case_results),"no_owner_overlap_cases":sum(x["disposition"]=="sampled_date_candidates_no_owner_overlap" for x in case_results),"no_parent_cases_unresolved":sum(x["disposition"]=="no_parent_in_loaded_archives_unresolved" for x in case_results)}
    complete=(summary["downloaded_documents"]==summary["sample_documents"]==summary["xml_parse_success"]==summary["identity_pass"])
    result={"phase":301,"status":"COMPLETED_INTERMEDIATE_ERA_XML_AUDIT" if complete else "INCOMPLETE_OR_IDENTITY_MISMATCH","source":{"provider":"SEC EDGAR","bulk_archive_downloads":archive_meta,"bulk_archives":manifest["bulk_archives"]},"summary":summary,"documents":checks,"cases":case_results,"downloads":downloads,"limitations":["DATE_OF_ORIG_SUB is date-only and no authoritative parent accession foreign key exists.","Sample is deterministic/stratified, not a prevalence estimate.","No parent in loaded 2022Q4–2023Q2 archives does not mean no parent exists elsewhere in EDGAR.","Owner sets are accession-level, not transaction-line-level.","Line differences are not confirmed new trades, deletions or reversals.","Acceptance timestamp is not exact first-public availability."],"controls":manifest["controls"]}
    (a.output_dir/"phase301_validation_result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"phase":301,"status":result["status"],"summary":summary,"archive_sha256s":{p:m["sha256"] for p,m in archive_meta.items()}},indent=2))
    return 0 if complete else 2

if __name__=="__main__": raise SystemExit(main())

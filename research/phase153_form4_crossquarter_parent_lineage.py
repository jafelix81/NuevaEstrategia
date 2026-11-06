#!/usr/bin/env python3
"""Phase 153: cross-quarter SEC Form 4/A parent-candidate and line-diff audit.

This creates conservative candidates, never authoritative parent links.
"""
from __future__ import annotations
import argparse, csv, hashlib, io, json, re, zipfile
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

PERIOD_FILES = {
    "2011Q4": "2011q4_form345.zip",
    "2012Q1": "2012q1_form345.zip",
    "2026Q2": "2026q2_form345.zip",
    "2026Q3": "2026q3_form345.zip",
}
TARGETS = ("2012Q1", "2026Q3")
NUMERIC = {"TRANS_SHARES","TRANS_PRICEPERSHARE","SHRS_OWND_FOLWNG_TRANS","VALU_OWND_FOLWNG_TRANS",
           "CONV_EXERCISE_PRICE","TRANS_TOTAL_VALUE","UNDLYNG_SEC_SHARES","UNDLYNG_SEC_VALUE"}
ND_EXACT = ("SECURITY_TITLE","TRANS_DATE","DEEMED_EXECUTION_DATE","TRANS_FORM_TYPE","TRANS_CODE",
            "EQUITY_SWAP_INVOLVED","TRANS_TIMELINESS","TRANS_SHARES","TRANS_PRICEPERSHARE",
            "TRANS_ACQUIRED_DISP_CD","SHRS_OWND_FOLWNG_TRANS","DIRECT_INDIRECT_OWNERSHIP","NATURE_OF_OWNERSHIP")
DV_EXACT = ("SECURITY_TITLE","TRANS_DATE","DEEMED_EXECUTION_DATE","TRANS_FORM_TYPE","TRANS_CODE",
            "EQUITY_SWAP_INVOLVED","TRANS_TIMELINESS","TRANS_SHARES","TRANS_TOTAL_VALUE","TRANS_PRICEPERSHARE",
            "TRANS_ACQUIRED_DISP_CD","EXCERCISE_DATE","EXPIRATION_DATE","CONV_EXERCISE_PRICE",
            "UNDLYNG_SEC_TITLE","UNDLYNG_SEC_SHARES","SHRS_OWND_FOLWNG_TRANS",
            "DIRECT_INDIRECT_OWNERSHIP","NATURE_OF_OWNERSHIP")
ND_COARSE = ("SECURITY_TITLE","TRANS_DATE","TRANS_FORM_TYPE","TRANS_CODE")
DV_COARSE = ("SECURITY_TITLE","TRANS_DATE","TRANS_FORM_TYPE","TRANS_CODE","UNDLYNG_SEC_TITLE")
ACC_RE = re.compile(r"^\d{10}-\d{2}-\d{6}$")

def date_norm(x):
    s=(x or "").strip()
    if not s: return ""
    for fmt in ("%d-%b-%Y","%Y-%m-%d","%m/%d/%Y"):
        try: return datetime.strptime(s.upper(),fmt).date().isoformat()
        except ValueError: pass
    return s.upper()

def cik_norm(x):
    s=(x or "").strip()
    return s.zfill(10) if s.isdigit() and len(s)<=10 else ""

def val_norm(field,x):
    s=(x or "").strip()
    if not s: return ""
    if field in NUMERIC:
        try:
            from decimal import Decimal
            d=Decimal(s.replace(",",""))
            if d.is_finite(): return format(d.normalize(),"f")
        except Exception: pass
    return " ".join(s.upper().split())

def read_table(z,suffix):
    names=[n for n in z.namelist() if n.upper().endswith(suffix.upper())]
    if len(names)!=1: raise ValueError(f"Expected one {suffix}; got {names}")
    return list(csv.DictReader(io.StringIO(z.read(names[0]).decode("utf-8-sig")),delimiter="\t"))

def load_period(path,period):
    raw=path.read_bytes()
    if not zipfile.is_zipfile(io.BytesIO(raw)): raise ValueError(f"Invalid ZIP: {path}")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        sub=read_table(z,"SUBMISSION.tsv"); owners=read_table(z,"REPORTINGOWNER.tsv")
        nd=read_table(z,"NONDERIV_TRANS.tsv"); dv=read_table(z,"DERIV_TRANS.tsv")
    filings={}
    for r in sub:
        doc=(r.get("DOCUMENT_TYPE") or "").strip().upper()
        if doc not in {"4","4/A"}: continue
        acc=(r.get("ACCESSION_NUMBER") or "").strip()
        issuer=cik_norm(r.get("ISSUERCIK"))
        if not ACC_RE.fullmatch(acc) or not issuer: raise ValueError(f"Invalid accession/issuer: {acc}")
        filings[acc]={"accession":acc,"period":period,"doc":doc,"issuer":issuer,
                      "filing_date":date_norm(r.get("FILING_DATE")),
                      "orig_date":date_norm(r.get("DATE_OF_ORIG_SUB")),
                      "owners":set(),"nd":[],"dv":[]}
    for r in owners:
        a=(r.get("ACCESSION_NUMBER") or "").strip()
        if a in filings and cik_norm(r.get("RPTOWNERCIK")): filings[a]["owners"].add(cik_norm(r.get("RPTOWNERCIK")))
    for rows,key in ((nd,"nd"),(dv,"dv")):
        for r in rows:
            a=(r.get("ACCESSION_NUMBER") or "").strip()
            if a in filings: filings[a][key].append(r)
    return {"sha256":hashlib.sha256(raw).hexdigest(),"filings":filings}

def signature(row,fields):
    return tuple(val_norm(f,row.get(f)) for f in fields)

def diff_rows(parent,child,exact_fields,coarse_fields):
    p_exact=Counter(signature(r,exact_fields) for r in parent)
    c_exact=Counter(signature(r,exact_fields) for r in child)
    repeated=sum((p_exact & c_exact).values())
    p_coarse=Counter(signature(r,coarse_fields) for r in parent)
    c_coarse=Counter(signature(r,coarse_fields) for r in child)
    exact_coarse=Counter()
    p_left=p_exact.copy()
    for r in child:
        sig=signature(r,exact_fields)
        if p_left[sig]>0:
            exact_coarse[signature(r,coarse_fields)]+=1
            p_left[sig]-=1
    p_coarse-=exact_coarse
    c_coarse-=exact_coarse
    modified=sum((p_coarse & c_coarse).values())
    return {"parent_rows":len(parent),"amendment_rows":len(child),
            "exact_repeated_candidate_rows":repeated,
            "possible_modified_candidate_rows":modified,
            "added_candidate_rows":sum(c_coarse.values())-modified,
            "parent_rows_not_repeated_in_amendment":sum(p_coarse.values())-modified,
            "classification_candidate_only":True}

def candidate_index(periods):
    idx=defaultdict(list)
    for data in periods.values():
        for f in data["filings"].values():
            if f["doc"]=="4" and f["filing_date"]:
                idx[(f["issuer"],f["filing_date"])].append(f)
    return idx

def candidates(child,idx):
    if not child["orig_date"] or not child["owners"]: return []
    out=[]
    for p in idx.get((child["issuer"],child["orig_date"]),[]):
        if p["accession"]==child["accession"] or p["filing_date"]>child["filing_date"]: continue
        shared=child["owners"] & p["owners"]
        if not shared: continue
        out.append({"filing":p,"shared":len(shared),"owner_sets_equal":child["owners"]==p["owners"]})
    return sorted(out,key=lambda x:x["filing"]["accession"])

def audit(periods):
    idx=candidate_index(periods); out={}
    eton_child="0001437749-26-029308"; eton_parent="0001437749-26-029196"; eton=None
    for target in TARGETS:
        amendments=[f for f in periods[target]["filings"].values() if f["doc"]=="4/A"]
        counts=Counter(); nd_tot=Counter(); dv_tot=Counter(); examples=[]
        for child in amendments:
            cand=candidates(child,idx)
            if not cand:
                counts["no_candidate_in_two_quarter_window"]+=1; continue
            if len(cand)>1:
                counts["ambiguous_candidates"]+=1; continue
            p=cand[0]["filing"]; counts["unique_candidate_parent"]+=1
            counts["unique_same_quarter_candidate" if p["period"]==target else "unique_adjacent_quarter_candidate"]+=1
            counts["unique_exact_owner_set" if cand[0]["owner_sets_equal"] else "unique_partial_owner_overlap"]+=1
            n=diff_rows(p["nd"],child["nd"],ND_EXACT,ND_COARSE)
            d=diff_rows(p["dv"],child["dv"],DV_EXACT,DV_COARSE)
            nd_tot.update({k:v for k,v in n.items() if isinstance(v,int)})
            dv_tot.update({k:v for k,v in d.items() if isinstance(v,int)})
            if child["accession"]==eton_child:
                eton={"candidate_parent_accessions":[p["accession"]],"expected_parent_accession":eton_parent,
                      "nonderivative":n,"derivative":d}
            if len(examples)<10:
                examples.append({"amendment_accession":child["accession"],"candidate_parent_accession":p["accession"],
                                 "parent_period":p["period"],"filing_date":child["filing_date"],
                                 "date_of_orig_sub":child["orig_date"],"shared_owner_count":cand[0]["shared"],
                                 "owner_sets_equal":cand[0]["owner_sets_equal"]})
        n=len(amendments)
        out[target]={"amendments":n,"unique_candidate_parent":counts["unique_candidate_parent"],
                     "unique_same_quarter_candidate":counts["unique_same_quarter_candidate"],
                     "unique_adjacent_quarter_candidate":counts["unique_adjacent_quarter_candidate"],
                     "ambiguous_candidates":counts["ambiguous_candidates"],
                     "no_candidate_in_two_quarter_window":counts["no_candidate_in_two_quarter_window"],
                     "unique_exact_owner_set":counts["unique_exact_owner_set"],
                     "unique_partial_owner_overlap":counts["unique_partial_owner_overlap"],
                     "candidate_coverage_pct":round(100*counts["unique_candidate_parent"]/n,4) if n else None,
                     "line_diff_totals_candidate_only":{"table_i_nonderivative":dict(nd_tot),
                                                          "table_ii_derivative":dict(dv_tot)},
                     "first_ten_unique_candidate_examples":examples}
    if not eton or eton["candidate_parent_accessions"] != [eton_parent]:
        raise ValueError(f"ETON known-parent regression failed: {eton}")
    if (eton["nonderivative"]["exact_repeated_candidate_rows"],eton["nonderivative"]["added_candidate_rows"])!=(4,1):
        raise ValueError(f"ETON Table I regression failed: {eton}")
    if (eton["derivative"]["exact_repeated_candidate_rows"],eton["derivative"]["added_candidate_rows"])!=(1,1):
        raise ValueError(f"ETON Table II regression failed: {eton}")
    return {"phase":153,"status":"COMPLETED_CROSS_QUARTER_CANDIDATE_AUDIT",
            "source":{"provider":"SEC","phase39_artifact_run_id":40606706518,"phase39_artifact_id":12781850078,
                      "phase39_outer_sha256":"203d7b1d2e29c999da318456af72e621cb30ef9a470d8f1610d088f9bebecb66",
                      "periods":{k:{"sha256":v["sha256"],"form4_and_4a_filings":len(v["filings"])} for k,v in sorted(periods.items())}},
            "method":{"candidate_rule":"same issuer CIK + DATE_OF_ORIG_SUB equals original Form 4 FILING_DATE + shared reporting-owner CIK + parent not after amendment",
                      "parent_type":"original Form 4 only; Form 4/A excluded as parent",
                      "search_window":"target quarter plus immediately preceding quarter",
                      "line_diff":"multiset exact transaction-fact signature followed by coarse signature for possible modification; footnote references and row surrogate keys excluded",
                      "limitations":["candidate is not an authoritative SEC parent-accession foreign key",
                                    "reporting-owner linkage remains accession-level; no line-to-owner attribution",
                                    "possible modified/additional lines require document-level adjudication",
                                    "parent rows absent from amendment are not called deleted",
                                    "originals older than the immediately preceding quarter remain outside the search window"]},
            "periods":out,"verified_eton_regression":eton,"alpha_test":False,"final_holdout_used":False,
            "f80_modified":False,
            "decision":"Adjacent-quarter search improves candidate-lineage coverage measurement but does not establish confirmed parent links. Quarantine ambiguous and unmatched amendments; no Form 4/A event-flow or alpha use until accession-level adjudication."}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input-dir",type=Path,required=True)
    p.add_argument("--adjacent-dir",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args(); periods={}
    for period,filename in PERIOD_FILES.items():
        folder=a.input_dir if period in {"2012Q1","2026Q3"} else a.adjacent_dir
        path=folder/filename
        if not path.is_file(): raise SystemExit(f"Missing source ZIP: {path}")
        periods[period]=load_period(path,period)
    result=audit(periods); a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"phase":153,"periods":{k:{x:v[x] for x in ("amendments","unique_candidate_parent","unique_same_quarter_candidate","unique_adjacent_quarter_candidate","ambiguous_candidates","no_candidate_in_two_quarter_window","candidate_coverage_pct")} for k,v in result["periods"].items()},"verified_eton_regression":result["verified_eton_regression"]},indent=2))

if __name__=="__main__": main()

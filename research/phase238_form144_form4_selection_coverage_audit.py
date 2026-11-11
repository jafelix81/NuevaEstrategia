#!/usr/bin/env python3
"""Phase 238: reverse Form 144/Form 4 linkage and selection audit; no return test."""
import argparse, csv, hashlib, io, json, random, re, zipfile
from collections import Counter, defaultdict
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

H144 = "7a54ee09e8d4520e1ec14cf22f2c0d1c62d077798b14d3db596826e3360a3659"
H4 = "a4e6a681cfcfa43a3d9e4ca9cfec1fd26a59d0a01eac7e9f7b5a0122092c90f3"
CUTOFF = date(2026, 9, 24)
SNAPSHOT_END = date(2026, 9, 30)

def sha(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for b in iter(lambda:f.read(1<<20),b""): h.update(b)
    return h.hexdigest()

def cik(x): return str(x or "").strip().lstrip("0") or ("0" if x else "")
def name(x): return re.sub(r"[^A-Z0-9]","",str(x or "").upper())
def cls(x): return re.sub(r"[^A-Z0-9]","",str(x or "").upper())
def family(x):
    x=cls(x)
    for c in "ABCD":
        if "CLASS"+c in x: return "CLASS_"+c
    for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        if "SERIES"+c in x: return "SERIES_"+c
    if "PREFERRED" in x:return "PREFERRED"
    if "ORDINARY" in x:return "ORDINARY"
    if "DEPOSITARY" in x or x.startswith("ADS"):return "DEPOSITARY"
    if "COMMON" in x or "COMMSTOCK" in x:return "COMMON"
    return "OTHER:"+x if x else "UNKNOWN"
def iso(x):
    try:return date.fromisoformat(str(x or "").strip()[:10])
    except:return None
def secdate(x):
    try:return datetime.strptime(str(x or "").strip().upper(),"%d-%b-%Y").date()
    except:return None
def dec(x):
    try:return Decimal(str(x or "").strip().replace(",",""))
    except:return None
def flag(x):
    x=str(x or "").strip().lower()
    return True if x in ("1","true") else False if x in ("0","false") else None
def tsv(z,n):
    with z.open(n) as f:
        yield from csv.DictReader(io.TextIOWrapper(f,encoding="utf-8-sig",newline=""),delimiter="\t")

def load144(path):
    with open(path,encoding="utf-8-sig",newline="") as f: rows=list(csv.DictReader(f))
    panel=[r for r in rows if str(r.get("include_as_issuer_event","")).lower()=="true"]
    ciks={cik(r.get("xml_issuer_cik")) for r in panel if cik(r.get("xml_issuer_cik"))}
    q3=[r for r in panel if r.get("quarter")=="2026Q3" and r.get("form")=="144"]
    byacc=defaultdict(list); latest={}
    for r in q3:
        a=r.get("accession",""); ic=cik(r.get("xml_issuer_cik")); seller=name(r.get("seller_name"))
        if not a or not ic or not seller: continue
        try: items=json.loads(r.get("sale_tranches_json") or "[]")
        except: items=[]
        for t in items:
            d=iso(t.get("approx_sale_date_iso")); u=dec(t.get("units_numeric"))
            if d is None or u is None or u<=0: continue
            byacc[a].append({"accession":a,"idx":str(t.get("sale_tranche_index","")),
                "issuer":ic,"seller":seller,"date":d,"units":u,
                "family":family(t.get("security_class"))})
            latest[a]=max(latest.get(a,d),d)
    eligible={a for a,d in latest.items() if d<=CUTOFF}
    tr=[t for a in eligible for t in byacc[a]]
    return {"rows":len(rows),"ciks":ciks,"q3":len(q3),"eligible":eligible,"tranches":tr,
            "notices":len(eligible),"excluded":len(q3)-len(eligible)}

def load4(path,ciks):
    with zipfile.ZipFile(path) as z:
        subs=list(tsv(z,"SUBMISSION.tsv")); owners=list(tsv(z,"REPORTINGOWNER.tsv"))
        tx=list(tsv(z,"NONDERIV_TRANS.tsv"))
    sm={r["ACCESSION_NUMBER"]:r for r in subs if r.get("ACCESSION_NUMBER")}
    om=defaultdict(dict); roles={}
    for r in owners:
        a=r.get("ACCESSION_NUMBER",""); oc=cik(r.get("RPTOWNERCIK"))
        if a and oc: om[a][oc]=r.get("RPTOWNERNAME",""); roles[a]=r.get("RPTOWNER_RELATIONSHIP","")
    seen=set(); blocks={}; fdates=[secdate(r.get("FILING_DATE")) for r in subs]
    for r in tx:
        a=r.get("ACCESSION_NUMBER",""); sk=r.get("NONDERIV_TRANS_SK",""); key=(a,sk)
        if key in seen:continue
        seen.add(key); s=sm.get(a)
        if not s or s.get("DOCUMENT_TYPE")!="4" or r.get("TRANS_FORM_TYPE")!="4":continue
        if r.get("TRANS_CODE")!="S" or r.get("TRANS_ACQUIRED_DISP_CD")!="D":continue
        if r.get("TRANS_TIMELINESS")=="L" or len(om.get(a,{}))!=1:continue
        ic=cik(s.get("ISSUERCIK"))
        if ic not in ciks:continue
        owner=name(next(iter(om[a].values()))); td=secdate(r.get("TRANS_DATE")); fd=secdate(s.get("FILING_DATE"))
        sh=dec(r.get("TRANS_SHARES"))
        if not ic or not owner or td is None or fd is None or sh is None or sh<=0:continue
        lag=(fd-td).days
        if lag<0 or lag>4:continue
        b=blocks.setdefault((a,td),{"accession":a,"date":td,"issuer":ic,"owner":owner,
            "shares":Decimal(0),"titles":set(),"plan":flag(s.get("AFF10B5ONE")),
            "role":roles.get(a,"")})
        b["shares"]+=sh
        if r.get("SECURITY_TITLE"):b["titles"].add(r["SECURITY_TITLE"])
    for b in blocks.values():
        titles=sorted(b["titles"]); b["family"]=family(titles[0]) if len(titles)==1 else "MULTI_OR_UNKNOWN"
    maxfd=max((d for d in fdates if d),default=None)
    if maxfd!=SNAPSHOT_END:raise ValueError(f"unexpected Form 4 snapshot end: {maxfd}")
    return {"submissions":len(subs),"tx_rows":len(tx),"duplicate_tx_keys":len(tx)-len(seen),
            "max_filing_date":maxfd.isoformat(),"blocks":list(blocks.values()),
            "issuers":len({b["issuer"] for b in blocks.values()})}

def edges(tr,bs,lo,hi):
    ix=defaultdict(list)
    for b in bs:ix[(b["issuer"],b["owner"])].append(b)
    return [(t,b,(b["date"]-t["date"]).days) for t in tr for b in ix.get((t["issuer"],t["seller"]),[])
            if lo<=(b["date"]-t["date"]).days<=hi]
def unique(es):
    tc=Counter((t["accession"],t["idx"]) for t,b,g in es)
    bc=Counter((b["accession"],b["date"]) for t,b,g in es)
    return [e for e in es if tc[(e[0]["accession"],e[0]["idx"])]==1 and bc[(e[1]["accession"],e[1]["date"])]==1]
def exact_first(tr,bs):
    ee=[e for e in edges(tr,bs,0,0) if e[0]["units"]==e[1]["shares"]]
    eu=unique(ee)
    rt={(t["accession"],t["idx"]) for t,b,g in ee}; rb={(b["accession"],b["date"]) for t,b,g in ee}
    remt=[t for t in tr if (t["accession"],t["idx"]) not in rt]
    remb=[b for b in bs if (b["accession"],b["date"]) not in rb]
    fe=edges(remt,remb,0,2); fu=unique(fe)
    return ee,eu,fe,fu,len({(t["accession"],t["idx"]) for t,b,g in ee})-len({(t["accession"],t["idx"]) for t,b,g in eu}),len({(b["accession"],b["date"]) for t,b,g in ee})-len({(b["accession"],b["date"]) for t,b,g in eu})

def wilson(k,n):
    if not n:return None
    z=1.96;p=k/n;d=1+z*z/n;c=(p+z*z/(2*n))/d;h=z*((p*(1-p)/n+z*z/(4*n*n))**.5)/d
    return [c-h,c+h]
def conditional(bs,fields,reps,seed):
    strata=defaultdict(list)
    for b in bs:strata[tuple(b[f] for f in fields)].append(b)
    mixed=[v for v in strata.values() if any(x["plan"] is True for x in v) and any(x["plan"] is False for x in v)]
    py=[x["matched"] for g in mixed for x in g if x["plan"] is True]
    ny=[x["matched"] for g in mixed for x in g if x["plan"] is False]
    if not py or not ny:return {"mixed_strata":len(mixed),"status":"INSUFFICIENT"}
    obs=sum(py)/len(py)-sum(ny)/len(ny); total=sum(x["matched"] for g in mixed for x in g)
    rng=random.Random(seed); extreme=0
    for _ in range(reps):
        selected=0
        for g in mixed:
            nplan=sum(x["plan"] is True for x in g)
            selected_ix=set(rng.sample(range(len(g)),nplan))
            selected+=sum(i in selected_ix for i,x in enumerate(g) if x["matched"])
        stat=selected/len(py)-(total-selected)/len(ny)
        extreme+=abs(stat)>=abs(obs)-1e-15
    return {"strata":list(fields),"mixed_strata":len(mixed),"blocks":sum(map(len,mixed)),
        "plan_n":len(py),"nonplan_n":len(ny),"observed_difference":obs,"permutations":reps,
        "seed":seed,"p_two_sided_plus_one":(extreme+1)/(reps+1),
        "null":"plan labels exchangeable within strata; diagnostic, not causal"}

def median(x):
    x=sorted(x); n=len(x)
    return None if not n else x[n//2] if n%2 else (x[n//2-1]+x[n//2])/2

def audit(f144_path,f4_path,reps=20000,seed=238):
    h144,h4=sha(f144_path),sha(f4_path)
    if h144!=H144 or h4!=H4:raise ValueError("immutable input SHA-256 mismatch")
    a=load144(f144_path); f=load4(f4_path,a["ciks"]); bs=f["blocks"]
    ee,eu,fe,fu,ambt,ambb=exact_first(a["tranches"],bs); matches=eu+fu
    mkeys={(b["accession"],b["date"]) for t,b,g in matches}
    for b in bs:
        b["matched"]=(b["accession"],b["date"]) in mkeys
        if b["plan"] is None:raise ValueError("unknown AFF10B5ONE flag")
    pt=[b for b in bs if b["plan"] is True]; pn=[b for b in bs if b["plan"] is False]
    mt=sum(b["matched"] for b in pt); mn=sum(b["matched"] for b in pn)
    class_agree=sum(t["family"]==b["family"] and t["family"] not in ("UNKNOWN","MULTI_OR_UNKNOWN") for t,b,g in eu)
    roles={}
    for role in sorted({b["role"] or "UNKNOWN" for b in bs}):
        g=[b for b in bs if (b["role"] or "UNKNOWN")==role]; p=[b for b in g if b["plan"]]; n=[b for b in g if not b["plan"]]
        roles[role]={"blocks":len(g),"matched":sum(b["matched"] for b in g),"rate":sum(b["matched"] for b in g)/len(g),
            "plan_n":len(p),"plan_rate":sum(b["matched"] for b in p)/len(p) if p else None,
            "nonplan_n":len(n),"nonplan_rate":sum(b["matched"] for b in n)/len(n) if n else None}
    bins=[("<=1000",None,1000),("1001_5000",1000,5000),("5001_10000",5000,10000),
          ("10001_50000",10000,50000),("50001_100000",50000,100000),(">100000",100000,None)]
    size={}
    for label,lo,hi in bins:
        g=[b for b in bs if (lo is None or b["shares"]>lo) and (hi is None or b["shares"]<=hi)]
        size[label]={"blocks":len(g),"matched":sum(b["matched"] for b in g),"rate":sum(b["matched"] for b in g)/len(g) if g else None}
    return {
      "phase":238,"status":"FORM144_FORM4_CAPTURE_IS_SELECTIVE;_PLAN_FLAG_GAP_NOT_ROBUST_WITHIN_ISSUER_ROLE",
      "inputs":{"form144":{"run_id":41959603351,"artifact_id":13385365595,"sha256":h144},
        "form4":{"run_id":40606706518,"artifact_id":12781850078,"sha256":h4,"snapshot_end":f["max_filing_date"]}},
      "sample":{"form144_panel_rows":a["rows"],"form144_panel_issuer_ciks":len(a["ciks"]),
        "form144_q3_original_notices":a["q3"],"form144_eligible_notices":a["notices"],
        "form144_eligible_tranches":len(a["tranches"]),"form144_excluded_notices":a["excluded"],
        "form4_submissions":f["submissions"],"form4_nonderivative_rows":f["tx_rows"],
        "form4_duplicate_transaction_keys":f["duplicate_tx_keys"],"form4_eligible_sale_blocks":len(bs),
        "form4_panel_issuers":f["issuers"],"unknown_plan_flags":sum(b["plan"] is None for b in bs)},
      "linkage":{"exact_edges":len(ee),"exact_unique":len(eu),"ambiguous_exact_tranches":ambt,
        "ambiguous_exact_blocks":ambb,"fallback_edges":len(fe),"fallback_unique":len(fu),
        "fallback_gap_counts":dict(Counter(str(g) for t,b,g in fu)),
        "total_links":len(matches),"matched_notices":len({t["accession"] for t,b,g in matches}),
        "matched_form4_blocks":len(mkeys),"unmatched_form4_blocks":len(bs)-len(mkeys),
        "matched_issuers":len({t["issuer"] for t,b,g in matches}),
        "form4_block_linkage_rate":len(mkeys)/len(bs),
        "class_family_agree":class_agree,"class_family_total_exact":len(eu),
        "class_family_agreement_rate":class_agree/len(eu) if eu else None},
      "plan_flag":{"true":{"n":len(pt),"matched":mt,"rate":mt/len(pt),"wilson95":wilson(mt,len(pt))},
        "false":{"n":len(pn),"matched":mn,"rate":mn/len(pn),"wilson95":wilson(mn,len(pn))},
        "unadjusted_difference":mt/len(pt)-mn/len(pn),
        "within_issuer":conditional(bs,("issuer",),reps,seed),
        "within_issuer_role":conditional(bs,("issuer","role"),reps,seed+1),
        "role_descriptive":roles},
      "share_size":{"matched_median_shares":float(median([b["shares"] for b in bs if b["matched"]])),
        "unmatched_median_shares":float(median([b["shares"] for b in bs if not b["matched"]])),
        "bins":size},
      "decision":{"form144_is_census":"REJECTED","feature_admitted":False,"alpha_test_authorized":False,
        "strict_pit_admitted":False,"holdout_used":False,"legacy_holdout":"CONSUMED_NOT_PRISTINE",
        "f80_frozen":True,"production_changed":False,"universe_changed":False}
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--form144-csv",required=True);p.add_argument("--form4-zip",required=True)
    p.add_argument("--output",required=True);p.add_argument("--permutations",type=int,default=20000)
    p.add_argument("--seed",type=int,default=238);a=p.parse_args()
    r=audit(a.form144_csv,a.form4_zip,a.permutations,a.seed)
    Path(a.output).parent.mkdir(parents=True,exist_ok=True)
    Path(a.output).write_text(json.dumps(r,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(r,indent=2,sort_keys=True))
if __name__=="__main__":main()

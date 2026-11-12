#!/usr/bin/env python3
"""Phase 338: broad stratified SEC Form 4 issuer-identity coverage audit."""
from __future__ import annotations
import argparse,csv,hashlib,io,json,os,zipfile
from collections import Counter,defaultdict
from datetime import date,datetime,timezone
from pathlib import Path
from research.phase325_form4_issuer_symbol_full_census_audit import SOURCE_ARTIFACT_SHA256,classify_symbol
from research.phase328_sec_collision_prior_filing_xbrl_pilot import SECClient,retrieve_filing_facts,select_prior_periodic_filing,summarize_facts
from research.phase333_symbol_class_binding_audit import build_context_associations,extract_symbol_fact_rows,extract_title_fact_rows

PHASE=338
CENSUS_SHA=SOURCE_ARTIFACT_SHA256
COLLISION_SHA="6d7930230a60036931857520df07b28087720d54ae9d3bee8f4b1cfe2fbcefa3"
QUARTERS={"2006Q1":71679,"2012Q1":63678,"2023Q1":63844,"2023Q2":51791,"2025Q3":32127,"2026Q3":34148}
MAX_AGE=365; TARGET=12; VERSION="phase338-v1-sha256-stratified-issuer-quarter"

def digest(b):return hashlib.sha256(b).hexdigest()
def read_source(path,expected,suffix):
    raw=Path(path).read_bytes()
    if digest(raw)!=expected:raise ValueError("source_artifact_hash_mismatch:"+Path(path).name)
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names=[n for n in z.namelist() if n.endswith(suffix)]
        if len(names)!=1:raise ValueError("source_member_not_unique:"+suffix)
        return list(csv.DictReader(io.StringIO(z.read(names[0]).decode("utf-8-sig"))))

def owners(r):
    try:n=int(r.get("reporting_owner_count") or 0)
    except (TypeError,ValueError):n=0
    return "MULTI" if n>1 else "SINGLE" if n==1 else "UNKNOWN"
def stratum(r):
    if r.get("index_status")!="MATCHED_ON_FILED_DATE":return "INDEX_EXCEPTION"
    cls,_=classify_symbol(r.get("ticker_as_filed"))
    return ("SINGLE_TOKEN_MULTI_OWNER" if owners(r)=="MULTI" else "SINGLE_TOKEN_SINGLE_OWNER") if cls=="SINGLE_TOKEN" else cls

def one_accession_per_issuer_quarter(rows):
    grouped=defaultdict(list)
    for r in rows:grouped[(r["quarter"],r["issuer_cik"])].append(r)
    out={}
    for key,items in grouped.items():
        pool=[r for r in items if r.get("index_status")!="MATCHED_ON_FILED_DATE"] or items
        out[key]=min(pool,key=lambda r:hashlib.sha256(f"{VERSION}|issuer-row|{key[0]}|{key[1]}|{r['accession']}".encode()).hexdigest())
    return out

def build_sample(census,collisions):
    if len(census)!=sum(QUARTERS.values()) or dict(Counter(r["quarter"] for r in census))!=QUARTERS:raise ValueError("census_coverage_mismatch")
    if len({r["accession"] for r in census})!=len(census):raise ValueError("duplicate_accession")
    excluded=sorted({str(r[k]).lstrip("0") or "0" for r in collisions for k in ("issuer_cik_a","issuer_cik_b")})
    if len(collisions)!=28 or len(excluded)!=56:raise ValueError("collision_exclusion_mismatch")
    eligible=[]
    for src in census:
        r=dict(src);r["issuer_cik"]=str(r["issuer_cik"]).lstrip("0") or "0"
        if r["issuer_cik"] in excluded or r["form_type"] not in {"4","4/A"}:continue
        eligible.append(r)
    frame=one_accession_per_issuer_quarter(eligible)
    pools=defaultdict(lambda:defaultdict(list))
    for (q,cik),r0 in frame.items():
        r=dict(r0);st=stratum(r);r["sample_stratum"]=st
        r["selection_hash"]=hashlib.sha256("|".join((VERSION,q,st,cik,r["accession"])).encode()).hexdigest()
        r["issuer_cik"]=cik;pools[q][st].append(r)
    records=[];strata=[]
    for q in sorted(QUARTERS):
        p=pools[q];exception=bool(p.get("INDEX_EXCEPTION"))
        quotas={"SINGLE_TOKEN_SINGLE_OWNER":5 if exception else 6,"SINGLE_TOKEN_MULTI_OWNER":2,"MISSING_OR_PLACEHOLDER":1,"MULTI_OR_FREEFORM":1,"OTHER_NONCANONICAL":1,"EXCHANGE_PREFIXED_SINGLE":1}
        if exception:quotas["INDEX_EXCEPTION"]=1
        chosen=[]
        for st,n in quotas.items():
            pop=sorted(p.get(st,[]),key=lambda x:x["selection_hash"])
            if len(pop)<n:raise ValueError(f"small_stratum:{q}:{st}")
            chosen+=pop[:n];strata.append({"quarter":q,"stratum":st,"population_issuer_quarter_units":len(pop),"sample_issuer_quarter_units":n,"inclusion_probability":n/len(pop),"design_weight":len(pop)/n})
        if len(chosen)!=TARGET or len({r["issuer_cik"] for r in chosen})!=TARGET:raise ValueError("quarter_sample_invalid:"+q)
        w={x["stratum"]:x["design_weight"] for x in strata if x["quarter"]==q}
        pn={x["stratum"]:x["population_issuer_quarter_units"] for x in strata if x["quarter"]==q}
        sn={x["stratum"]:x["sample_issuer_quarter_units"] for x in strata if x["quarter"]==q}
        for r in chosen:
            cls,cand=classify_symbol(r.get("ticker_as_filed"));st=r["sample_stratum"]
            records.append({"quarter":q,"accession":r["accession"],"form_type":r["form_type"],"filing_date":r["filing_date"],"issuer_cik":r["issuer_cik"],"issuer_name":r.get("issuer_name",""),"ticker_as_filed":r.get("ticker_as_filed",""),"symbol_class":cls,"candidate_symbol":cand or "","reporting_owner_count":int(r.get("reporting_owner_count") or 0),"index_status":r.get("index_status",""),"observed_index_date":r.get("observed_index_date",""),"sample_stratum":st,"population_issuer_quarter_units":pn[st],"sample_issuer_quarter_units":sn[st],"inclusion_probability":sn[st]/pn[st],"design_weight":w[st],"selection_hash":r["selection_hash"]})
    records.sort(key=lambda x:(x["quarter"],x["sample_stratum"],x["selection_hash"]))
    if len(records)!=72 or len({r["issuer_cik"] for r in records})!=72 or any(r["issuer_cik"] in excluded for r in records):raise ValueError("sample_identity_integrity_failure")
    return {"phase":PHASE,"selection_version":VERSION,"source":{"phase321_run_id":43177940904,"phase321_artifact_id":13925636412,"phase321_artifact_sha256":CENSUS_SHA,"phase325_run_id":43196055022,"phase325_artifact_id":13931894766,"phase325_artifact_sha256":COLLISION_SHA},"frame":{"source_accessions":len(census),"source_quarters":QUARTERS,"eligible_issuer_quarter_units_after_collision_exclusion":len(frame),"excluded_collision_pairs":28,"excluded_collision_issuer_ciks":56,"excluded_issuer_ciks":excluded,"selected_issuer_quarter_units":72,"selected_unique_issuer_ciks":72,"sampled_quarters":sorted(QUARTERS),"per_quarter_target":TARGET},"sampling_design":{"unit":"one hash-selected accession per issuer CIK and quarter","selection":"deterministic SHA-256 within issuer-quarter and predeclared symbol/owner/index strata","strata":strata,"weights":"population issuer-quarter units divided by sampled units per quarter-stratum","collision_exclusion":"all 56 CIKs in Phase 325 purposive collision panel","survivorship_control":"historical SEC Form 4/4-A issuer frame; no current-active filter"},"records":records,"controls":{"f80_frozen":True,"strict_pit_admitted":False,"security_master_admitted":False,"universe_coverage_admitted":False,"alpha_test_run":False,"return_test_run":False,"bootstrap_loo_run":False,"chronological_oos_run":False,"holdout_used":False,"production_changed":False,"universe_changed":False,"capital_changed":False,"parameters_changed":False,"data_purchased":False,"vendor_contacted":False},"availability_interpretation":{"clock":"SEC daily-index and Submissions filing dates; date-level only","first_public_timestamp_observed":False,"filing_date_is_first_public_timestamp":False,"same_day_anchor_allowed":False,"prior_periodic_must_be_strictly_pre_event":True,"maximum_anchor_age_days":MAX_AGE,"strict_pit_admitted":False,"return_backtest_authorized":False}}

def anchor_status(filing,event):
    if not filing:return "NO_PRIOR_PERIODIC_FILING",None
    try:age=(date.fromisoformat(event)-date.fromisoformat(filing["filingDate"])).days
    except (ValueError,KeyError):return "INVALID_DATE",None
    if age<=0:return "INVALID_NONPRE_EVENT_ANCHOR",age
    if age>MAX_AGE:return "STALE_PRIOR_PERIODIC_FILING",age
    return "FRESH_PRIOR_PERIODIC_FILING",age

def compare_candidate(index_status,candidate,symbols,no_symbol):
    if index_status!="MATCHED_ON_FILED_DATE":return "INDEX_DATE_EXCEPTION_NOT_COMPARABLE"
    if not candidate:return "CANDIDATE_SYMBOL_UNAVAILABLE"
    if len(symbols)==1 and symbols[0]==candidate:return "MATCH_SINGLE_SYMBOL"
    if candidate in symbols:return "MATCH_AMONG_MULTIPLE_SYMBOLS"
    if symbols:return "MISMATCH"
    return "EXPLICIT_NO_SYMBOL" if no_symbol else "TRADING_SYMBOL_FACT_MISSING"

def weighted_rate(rows,pred,den=None):
    use=[r for r in rows if den is None or den(r)];total=sum(float(r["design_weight"]) for r in use);pos=sum(float(r["design_weight"]) for r in use if pred(r))
    return {"sample_n":len(use),"weighted_population_units":round(total,6),"weighted_positive_units":round(pos,6),"weighted_rate_pct":round(100*pos/total,4) if total else None,"unweighted_sample_rate_pct":round(100*sum(bool(pred(r)) for r in use)/len(use),4) if use else None}

def run_audit(manifest_path,outdir,email):
    m=json.loads(Path(manifest_path).read_text());rows=m["records"];out=Path(outdir);out.mkdir(parents=True,exist_ok=True)
    if not email or "@" not in email:raise RuntimeError("BLOCKED_MISSING_SEC_CONTACT_EMAIL")
    client=SECClient(email);cache={};obs=[]
    for i,s in enumerate(rows,1):
        row={**s,"submissions_status":"NOT_REQUESTED","submissions_http_status":0,"anchor_status":"NOT_TESTED","anchor_age_calendar_days":None,"selected_filing_accession":"","selected_filing_form":"","selected_filing_date":"","selection_source":"","document_status":"NOT_TESTED","document_sha256":"","document_bytes":0,"trading_symbols":[],"symbol_fact_count":0,"symbol_facts_with_class_axis":0,"symbol_facts_with_listing_axis":0,"direct_class_binding":False,"direct_listing_binding":False,"symbol_match_status":"NOT_TESTED","context_associations":[]}
        cik=s["issuer_cik"]
        if cik not in cache:
            raw,status,err,_=client.get(f"https://data.sec.gov/submissions/CIK{cik.zfill(10)}.json",max_bytes=20_000_000)
            if raw is None:row.update(submissions_status=err or f"HTTP_{status}",submissions_http_status=status,anchor_status="SUBMISSIONS_UNAVAILABLE",symbol_match_status="NOT_TESTED");obs.append(row);continue
            try:cache[cik]=json.loads(raw)
            except ValueError:row.update(submissions_status="JSON_PARSE_ERROR",submissions_http_status=status,anchor_status="SUBMISSIONS_PARSE_ERROR",symbol_match_status="NOT_TESTED");obs.append(row);continue
            row.update(submissions_status="OK",submissions_http_status=status)
        else:row.update(submissions_status="CACHED_OK",submissions_http_status=200)
        filing,source=select_prior_periodic_filing(cache[cik],s["filing_date"],client);ast,age=anchor_status(filing,s["filing_date"])
        row.update(anchor_status=ast,anchor_age_calendar_days=age,selection_source=source)
        if filing:row.update(selected_filing_accession=filing.get("accessionNumber",""),selected_filing_form=filing.get("form",""),selected_filing_date=filing.get("filingDate",""))
        if ast!="FRESH_PRIOR_PERIODIC_FILING":row["symbol_match_status"]="NOT_TESTED_NO_FRESH_ANCHOR";obs.append(row);continue
        facts,doc=retrieve_filing_facts(client,cik,filing);sf=extract_symbol_fact_rows(facts);tf=extract_title_fact_rows(facts);syms=sorted({x["symbol"] for x in sf})
        no_symbol=any(f.get("name")=="NoTradingSymbolFlag" and str(f.get("value") or "").strip().lower() in {"true","1"} for f in facts)
        cc=sum(bool(x.get("class_axis_members")) for x in sf);lc=sum(bool(x.get("listing_axis_members")) for x in sf);sm=summarize_facts(facts,s.get("candidate_symbol") or "")
        row.update(document_status=doc.get("document_status",""),document_sha256=doc.get("document_sha256",""),document_bytes=doc.get("document_bytes",0),trading_symbols=syms,symbol_fact_count=len(sf),symbol_facts_with_class_axis=cc,symbol_facts_with_listing_axis=lc,direct_class_binding=cc>0,direct_listing_binding=lc>0,symbol_match_status=compare_candidate(s["index_status"],s.get("candidate_symbol") or "",syms,no_symbol),context_associations=build_context_associations(sf,tf),document_class_axis_members_any_fact=sm.get("class_axis_members",[]),document_listing_axis_members_any_fact=sm.get("listing_axis_members",[]),document_has_no_trading_symbol_flag=no_symbol)
        obs.append(row);print(f"PHASE338_PROGRESS={i}/72 {ast} {doc.get('document_status','')} symbols={len(syms)}")
    ac=Counter(x["anchor_status"] for x in obs);dc=Counter(x["document_status"] for x in obs);mc=Counter(x["symbol_match_status"] for x in obs)
    coverage={"issuer_identity_submissions_resolved":weighted_rate(obs,lambda r:r["submissions_status"] in {"OK","CACHED_OK"}),"fresh_prior_periodic_anchor":weighted_rate(obs,lambda r:r["anchor_status"]=="FRESH_PRIOR_PERIODIC_FILING"),"periodic_document_retrieved_and_hashed":weighted_rate(obs,lambda r:len(r.get("document_sha256",""))==64),"trading_symbol_fact_present":weighted_rate(obs,lambda r:r["symbol_fact_count"]>0),"direct_symbol_class_binding":weighted_rate(obs,lambda r:r["direct_class_binding"]),"direct_symbol_listing_binding":weighted_rate(obs,lambda r:r["direct_listing_binding"]),"candidate_symbol_match_among_comparable":weighted_rate(obs,lambda r:r["symbol_match_status"] in {"MATCH_SINGLE_SYMBOL","MATCH_AMONG_MULTIPLE_SYMBOLS"},lambda r:r["symbol_match_status"] in {"MATCH_SINGLE_SYMBOL","MATCH_AMONG_MULTIPLE_SYMBOLS","MISMATCH"}),"direct_class_binding_conditional_on_symbol_fact":weighted_rate(obs,lambda r:r["direct_class_binding"],lambda r:r["symbol_fact_count"]>0),"direct_listing_binding_conditional_on_symbol_fact":weighted_rate(obs,lambda r:r["direct_listing_binding"],lambda r:r["symbol_fact_count"]>0),"permanent_security_identity_admitted":weighted_rate(obs,lambda r:False)}
    result={"phase":PHASE,"status":"COMPLETED_WITH_EXPLICIT_COVERAGE_AND_IDENTITY_QUARANTINES","generated_at_utc":datetime.now(timezone.utc).isoformat(),"sample_manifest_sha256":digest(Path(manifest_path).read_bytes()),"source":m["source"],"sample_frame":m["frame"],"summary":{"sample_issuer_quarter_units":len(obs),"unique_issuer_ciks":len({x["issuer_cik"] for x in obs}),"submissions_resolved":sum(x["submissions_status"] in {"OK","CACHED_OK"} for x in obs),"submissions_unavailable_units":ac["SUBMISSIONS_UNAVAILABLE"]+ac["SUBMISSIONS_PARSE_ERROR"],"fresh_anchor_units":ac["FRESH_PRIOR_PERIODIC_FILING"],"stale_anchor_units":ac["STALE_PRIOR_PERIODIC_FILING"],"no_prior_periodic_units":ac["NO_PRIOR_PERIODIC_FILING"],"invalid_anchor_units":ac["INVALID_NONPRE_EVENT_ANCHOR"]+ac["INVALID_DATE"],"fresh_documents_retrieved_and_hashed":sum(x["anchor_status"]=="FRESH_PRIOR_PERIODIC_FILING" and len(x["document_sha256"])==64 for x in obs),"fresh_documents_with_trading_symbol_facts":sum(x["anchor_status"]=="FRESH_PRIOR_PERIODIC_FILING" and x["symbol_fact_count"]>0 for x in obs),"fresh_documents_with_direct_class_binding":sum(x["anchor_status"]=="FRESH_PRIOR_PERIODIC_FILING" and x["direct_class_binding"] for x in obs),"fresh_documents_with_direct_listing_binding":sum(x["anchor_status"]=="FRESH_PRIOR_PERIODIC_FILING" and x["direct_listing_binding"] for x in obs),"anchor_status_counts":dict(sorted(ac.items())),"document_status_counts":dict(sorted(dc.items())),"symbol_match_status_counts":dict(sorted(mc.items()))},"coverage":coverage,"observations":obs,"controls":m["controls"],"interpretation":{"issuer_identity_primary_key":"issuer_cik","ticker_is_permanent_security_key":False,"class_binding_requires_symbol_fact_own_context_class_axis":True,"listing_binding_requires_symbol_fact_own_context_listing_axis":True,"document_level_axis_cooccurrence_is_not_direct_binding":True,"security_identity_admitted":False,"first_public_timestamp_observed":False,"filing_date_is_first_public_timestamp":False,"strict_pit_admitted":False,"sample_is_purposive_collision_panel":False,"sample_excludes_phase325_collision_issuers":True,"sample_is_full_historical_trading_universe":False,"weighted_rates_are_descriptive_not_alpha":True}}
    (out/"phase338_broad_identity_audit.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    (out/"phase338_sample_manifest.json").write_text(json.dumps(m,indent=2,sort_keys=True)+"\n")
    write_csv(out/"phase338_issuer_observations.csv",obs)
    write_csv(out/"phase338_context_associations.csv",[{"accession":x["accession"],"issuer_cik":x["issuer_cik"],**a} for x in obs for a in x.get("context_associations",[])])
    print("PHASE338_STATUS="+result["status"]);print("PHASE338_SUMMARY="+json.dumps(result["summary"],sort_keys=True));print("PHASE338_COVERAGE="+json.dumps(coverage,sort_keys=True));return result

def write_csv(path,rows):
    if not rows:path.write_text("");return
    fields=list(dict.fromkeys(k for r in rows for k in r))
    with path.open("w",newline="",encoding="utf-8-sig") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore");w.writeheader()
        for r in rows:w.writerow({k:json.dumps(v,ensure_ascii=False,sort_keys=True) if isinstance(v,(dict,list)) else v for k,v in r.items()})

def main():
    p=argparse.ArgumentParser();p.add_argument("--census-zip",type=Path,default=Path("phase321_source.zip"));p.add_argument("--collision-zip",type=Path,default=Path("phase325_source.zip"));p.add_argument("--sample-manifest",type=Path,default=Path("phase338_output/phase338_sample_manifest.json"));p.add_argument("--output-dir",type=Path,default=Path("phase338_output"));p.add_argument("--build-sample-only",action="store_true");a=p.parse_args()
    if a.build_sample_only:
        c=read_source(a.census_zip,CENSUS_SHA,"phase321_bulk_daily_index_census.csv");x=read_source(a.collision_zip,COLLISION_SHA,"phase325_same_day_symbol_collisions.csv");m=build_sample(c,x);a.sample_manifest.parent.mkdir(parents=True,exist_ok=True);a.sample_manifest.write_text(json.dumps(m,indent=2,sort_keys=True)+"\n");print("PHASE338_SAMPLE_MANIFEST_SHA256="+digest(a.sample_manifest.read_bytes()));return
    run_audit(a.sample_manifest,a.output_dir,os.environ.get("SEC_CONTACT_EMAIL",""))

if __name__=="__main__":main()

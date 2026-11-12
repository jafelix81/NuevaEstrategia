#!/usr/bin/env python3
"""Phase 338: broad, stratified SEC Form 4 issuer-identity coverage audit.

A fixed 72-unit sample is drawn from six historical Phase 321 Form 4/4-A
census quarters, excluding all 56 issuer CIKs in the purposive Phase 325
collision panel. Each issuer-quarter contributes one hash-selected accession.
The latest supported periodic filing strictly before that filing is inspected
for direct TradingSymbol/class/listing XBRL-context evidence.

Identity feasibility only: no permanent security master, strict-PIT admission,
market signal, return test, or production change. FilingDate is not first-public time.
"""
from __future__ import annotations
import argparse, csv, hashlib, io, json, os, zipfile
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from pathlib import Path
from research.phase325_form4_issuer_symbol_full_census_audit import SOURCE_ARTIFACT_SHA256, classify_symbol
from research.phase328_sec_collision_prior_filing_xbrl_pilot import SECClient, retrieve_filing_facts, select_prior_periodic_filing, summarize_facts
from research.phase333_symbol_class_binding_audit import build_context_associations, extract_symbol_fact_rows, extract_title_fact_rows

PHASE = 338
CENSUS_SHA = SOURCE_ARTIFACT_SHA256
COLLISION_SHA = "6d7930230a60036931857520df07b28087720d54ae9d3bee8f4b1cfe2fbcefa3"
QUARTERS = {"2006Q1":71679,"2012Q1":63678,"2023Q1":63844,"2023Q2":51791,"2025Q3":32127,"2026Q3":34148}
TOTAL = sum(QUARTERS.values())
MAX_AGE = 365
PER_QUARTER = 12
VERSION = "phase338-v1-sha256-stratified-issuer-quarter"

def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def read_zip_csv(path: Path, expected_sha: str, suffix: str):
    raw = path.read_bytes(); digest = sha256(raw)
    if digest != expected_sha: raise ValueError(f"source_zip_sha256_mismatch:{path.name}:{digest}")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names = [n for n in z.namelist() if n.endswith(suffix)]
        if len(names) != 1: raise ValueError(f"expected_one_source_member:{suffix}:{names}")
        rows = list(csv.DictReader(io.StringIO(z.read(names[0]).decode("utf-8-sig"))))
    return rows, digest

def owner_group(row):
    try: n = int(row.get("reporting_owner_count") or 0)
    except (TypeError, ValueError): n = 0
    return "MULTI" if n > 1 else ("SINGLE" if n == 1 else "UNKNOWN")

def stratum(row):
    if row.get("index_status") != "MATCHED_ON_FILED_DATE": return "INDEX_EXCEPTION"
    cls, _ = classify_symbol(row.get("ticker_as_filed"))
    if cls == "SINGLE_TOKEN": return "SINGLE_TOKEN_MULTI_OWNER" if owner_group(row) == "MULTI" else "SINGLE_TOKEN_SINGLE_OWNER"
    return cls

def one_accession_per_issuer_quarter(rows):
    grouped = defaultdict(list)
    for r in rows: grouped[(str(r["quarter"]), str(r["issuer_cik"]))].append(r)
    out = {}
    for key, candidates in grouped.items():
        # Preserve an issuer-quarter index exception if one exists; otherwise
        # select an accession uniformly by deterministic hash, never by recency.
        pool = [r for r in candidates if r.get("index_status") != "MATCHED_ON_FILED_DATE"] or candidates
        out[key] = min(pool, key=lambda r: hashlib.sha256(
            f"{VERSION}|issuer-row|{key[0]}|{key[1]}|{r.get('accession','')}".encode()).hexdigest())
    return out

def build_sample(census_rows, collision_rows, census_sha=CENSUS_SHA, collision_sha=COLLISION_SHA):
    if len(census_rows) != TOTAL: raise ValueError(f"census_row_count_mismatch:{len(census_rows)}")
    if dict(Counter(str(r.get("quarter") or "") for r in census_rows)) != QUARTERS: raise ValueError("census_quarter_counts_mismatch")
    accessions = [str(r.get("accession") or "") for r in census_rows]
    if any(not x for x in accessions) or len(set(accessions)) != len(accessions): raise ValueError("missing_or_duplicate_census_accession")
    excluded = sorted({str(r.get(k) or "").lstrip("0") or "0" for r in collision_rows for k in ("issuer_cik_a","issuer_cik_b")})
    if len(collision_rows) != 28 or len(excluded) != 56: raise ValueError("collision_exclusion_population_mismatch")
    excluded_set = set(excluded); eligible = []
    for source in census_rows:
        r = dict(source); r["issuer_cik"] = str(r.get("issuer_cik") or "").lstrip("0") or "0"
        if r["issuer_cik"] in excluded_set or r.get("form_type") not in {"4","4/A"}: continue
        try: date.fromisoformat(r.get("filing_date") or "")
        except ValueError: continue
        eligible.append(r)
    issuer_quarter = one_accession_per_issuer_quarter(eligible)
    pools = defaultdict(lambda: defaultdict(list))
    for (q,cik), source in issuer_quarter.items():
        r = dict(source); r["sample_stratum"] = stratum(r)
        r["selection_hash"] = hashlib.sha256("|".join((VERSION,q,r["sample_stratum"],cik,r["accession"])).encode()).hexdigest()
        r["issuer_cik"] = cik; pools[q][r["sample_stratum"]].append(r)
    samples=[]; stratum_rows=[]
    for q in sorted(QUARTERS):
        strata=pools[q]; has_exception=bool(strata.get("INDEX_EXCEPTION"))
        quotas={"SINGLE_TOKEN_SINGLE_OWNER":5 if has_exception else 6,"SINGLE_TOKEN_MULTI_OWNER":2,
                "MISSING_OR_PLACEHOLDER":1,"MULTI_OR_FREEFORM":1,"OTHER_NONCANONICAL":1,"EXCHANGE_PREFIXED_SINGLE":1}
        if has_exception: quotas["INDEX_EXCEPTION"]=1
        chosen=[]
        for name,n in quotas.items():
            population=sorted(strata.get(name,[]),key=lambda r:r["selection_hash"])
            if len(population)<n: raise ValueError(f"stratum_too_small:{q}:{name}:{len(population)}<{n}")
            selected=population[:n]; chosen.extend(selected)
            stratum_rows.append({"quarter":q,"stratum":name,"population_issuer_quarter_units":len(population),
                                 "sample_issuer_quarter_units":n,"inclusion_probability":n/len(population),
                                 "design_weight":len(population)/n})
        if len(chosen)!=PER_QUARTER or len({r["issuer_cik"] for r in chosen})!=PER_QUARTER: raise ValueError(f"quarter_sample_invalid:{q}")
        w={x["stratum"]:x["design_weight"] for x in stratum_rows if x["quarter"]==q}
        pn={x["stratum"]:x["population_issuer_quarter_units"] for x in stratum_rows if x["quarter"]==q}
        sn={x["stratum"]:x["sample_issuer_quarter_units"] for x in stratum_rows if x["quarter"]==q}
        for r in chosen:
            cls,candidate=classify_symbol(r.get("ticker_as_filed")); st=r["sample_stratum"]
            samples.append({"quarter":q,"accession":r["accession"],"form_type":r["form_type"],"filing_date":r["filing_date"],
                "issuer_cik":r["issuer_cik"],"issuer_name":r.get("issuer_name",""),"ticker_as_filed":r.get("ticker_as_filed",""),
                "symbol_class":cls,"candidate_symbol":candidate or "","reporting_owner_count":int(r.get("reporting_owner_count") or 0),
                "multiple_reporting_owners":owner_group(r)=="MULTI","index_status":r.get("index_status",""),
                "observed_index_date":r.get("observed_index_date",""),"index_row_count":int(r.get("index_row_count") or 0),
                "sample_stratum":st,"population_issuer_quarter_units":pn[st],"sample_issuer_quarter_units":sn[st],
                "inclusion_probability":sn[st]/pn[st],"design_weight":w[st],"selection_hash":r["selection_hash"]})
    samples.sort(key=lambda r:(r["quarter"],r["sample_stratum"],r["selection_hash"]))
    if len(samples)!=72 or len({r["issuer_cik"] for r in samples})!=72: raise ValueError("sample_size_or_unique_issuer_failure")
    if any(r["issuer_cik"] in excluded_set for r in samples): raise ValueError("collision_issuer_leakage")
    return {"phase":PHASE,"selection_version":VERSION,
        "source":{"phase321_run_id":43177940904,"phase321_artifact_id":13925636412,"phase321_artifact_sha256":census_sha,
                  "phase325_run_id":43196055022,"phase325_artifact_id":13931894766,"phase325_artifact_sha256":collision_sha},
        "frame":{"source_accessions":len(census_rows),"source_quarters":QUARTERS,"eligible_issuer_quarter_units_after_collision_exclusion":len(issuer_quarter),
                 "excluded_collision_pairs":28,"excluded_collision_issuer_ciks":56,"excluded_issuer_ciks":excluded,
                 "selected_issuer_quarter_units":len(samples),"selected_unique_issuer_ciks":len({r["issuer_cik"] for r in samples}),
                 "sampled_quarters":sorted(QUARTERS),"per_quarter_target":PER_QUARTER},
        "sampling_design":{"unit":"one hash-selected Form 4/4-A accession per issuer CIK per sampled quarter; repeated CIKs across quarters retained as clusters",
            "within_issuer_accession_selection":"minimum SHA-256 of version|issuer-row|quarter|CIK|accession; not latest filing and not return-dependent",
            "issuer_sample_selection":"minimum SHA-256 within predeclared symbol/owner/index-status strata",
            "strata":stratum_rows,"weights":"population issuer-quarter units / sampled units within each quarter-stratum",
            "collision_exclusion":"all 56 issuer CIKs in the purposive Phase 325 same-day collision panel excluded",
            "survivorship_control":"historical SEC Form 4/4-A issuer frame; no current-active filter or current ticker list"},
        "records":samples,
        "controls":{"f80_frozen":True,"strict_pit_admitted":False,"security_master_admitted":False,"universe_coverage_admitted":False,
            "alpha_test_run":False,"return_test_run":False,"bootstrap_loo_run":False,"chronological_oos_run":False,"holdout_used":False,
            "production_changed":False,"universe_changed":False,"capital_changed":False,"parameters_changed":False,"data_purchased":False,"vendor_contacted":False},
        "availability_interpretation":{"sample_reference_clock":"SEC bulk daily-index filing date and SEC Submissions filingDate; date-level only",
            "first_public_timestamp_observed":False,"filing_date_is_first_public_timestamp":False,"same_day_periodic_anchor_allowed":False,
            "prior_periodic_filing_must_be_strictly_before_sample_filing_date":True,"maximum_anchor_age_calendar_days":MAX_AGE,
            "strict_pit_admission":False,"return_backtest_authorized":False}}

def build_sample_manifest(census_zip,collision_zip,output_path):
    a,ah=read_zip_csv(Path(census_zip),CENSUS_SHA,"phase321_bulk_daily_index_census.csv")
    b,bh=read_zip_csv(Path(collision_zip),COLLISION_SHA,"phase325_same_day_symbol_collisions.csv")
    m=build_sample(a,b,ah,bh); Path(output_path).parent.mkdir(parents=True,exist_ok=True)
    Path(output_path).write_text(json.dumps(m,indent=2,sort_keys=True)+"\n",encoding="utf-8"); return m

def anchor_status(filing,sample_date):
    if not filing:return "NO_PRIOR_PERIODIC_FILING",None
    try: age=(date.fromisoformat(sample_date)-date.fromisoformat(str(filing.get("filingDate") or ""))).days
    except ValueError:return "INVALID_DATE",None
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

def weighted_rate(rows,predicate,denominator=None):
    use=[r for r in rows if denominator is None or denominator(r)]
    total=sum(float(r["design_weight"]) for r in use); pos=sum(float(r["design_weight"]) for r in use if predicate(r))
    return {"sample_n":len(use),"weighted_population_units":round(total,6),"weighted_positive_units":round(pos,6),
            "weighted_rate_pct":round(100*pos/total,4) if total else None,
            "unweighted_sample_rate_pct":round(100*sum(bool(predicate(r)) for r in use)/len(use),4) if use else None}

def run_audit(manifest_path,output_dir,email):
    manifest=json.loads(Path(manifest_path).read_text(encoding="utf-8")); records=manifest.get("records",[])
    if manifest.get("phase")!=PHASE or len(records)!=72:raise ValueError("phase338_manifest_invalid")
    out=Path(output_dir);out.mkdir(parents=True,exist_ok=True)
    if not email or "@" not in email:
        result={"phase":PHASE,"status":"BLOCKED_MISSING_SEC_CONTACT_EMAIL","sample_manifest_sha256":sha256(Path(manifest_path).read_bytes()),
                "summary":{"sample_issuer_quarter_units":len(records)},"observations":[],"controls":manifest["controls"]}
        (out/"phase338_broad_identity_audit.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n");return result
    client=SECClient(email);cache={};obs=[]
    for i,s in enumerate(records,1):
        cik=s["issuer_cik"]
        row={**{k:s.get(k) for k in ("quarter","accession","form_type","filing_date","issuer_cik","issuer_name","ticker_as_filed","symbol_class","candidate_symbol","reporting_owner_count","index_status","observed_index_date","sample_stratum","population_issuer_quarter_units","sample_issuer_quarter_units","inclusion_probability","design_weight","selection_hash")},
            "submissions_http_status":0,"submissions_status":"NOT_REQUESTED","selected_filing_accession":"","selected_filing_form":"","selected_filing_date":"","selected_report_date":"","selection_source":"",
            "anchor_age_calendar_days":None,"anchor_status":"NOT_TESTED","document_status":"NOT_TESTED","document_sha256":"","document_bytes":0,
            "document_http_status":0,"index_http_status":0,"trading_symbols":[],"symbol_fact_count":0,"symbol_facts_with_class_axis":0,
            "symbol_facts_with_listing_axis":0,"all_symbol_facts_have_direct_class_axis":False,"all_symbol_facts_have_direct_listing_axis":False,
            "same_context_security_titles":[],"symbol_match_status":"NOT_TESTED","direct_class_binding":False,"direct_listing_binding":False,"context_associations":[]}
        if cik not in cache:
            raw,status,err,_=client.get(f"https://data.sec.gov/submissions/CIK{cik.zfill(10)}.json",max_bytes=20_000_000)
            if raw is None:
                obs.append({**row,"submissions_http_status":status,"submissions_status":err or f"HTTP_{status}","anchor_status":"SUBMISSIONS_UNAVAILABLE","symbol_match_status":"NOT_TESTED"})
                print(f"PHASE338_PROGRESS={i}/72 SUBMISSIONS_UNAVAILABLE");continue
            try:cache[cik]=json.loads(raw)
            except ValueError:
                obs.append({**row,"submissions_http_status":status,"submissions_status":"SUBMISSIONS_JSON_PARSE_ERROR","anchor_status":"SUBMISSIONS_PARSE_ERROR","symbol_match_status":"NOT_TESTED"})
                print(f"PHASE338_PROGRESS={i}/72 SUBMISSIONS_PARSE_ERROR");continue
            status_label="OK";http=status
        else:status_label="CACHED_OK";http=200
        filing,source=select_prior_periodic_filing(cache[cik],s["filing_date"],client)
        astatus,age=anchor_status(filing,s["filing_date"])
        row.update({"submissions_http_status":http,"submissions_status":status_label,"selection_source":source,"anchor_status":astatus,"anchor_age_calendar_days":age})
        if filing:row.update({"selected_filing_accession":filing.get("accessionNumber",""),"selected_filing_form":filing.get("form",""),
                              "selected_filing_date":filing.get("filingDate",""),"selected_report_date":filing.get("reportDate","")})
        if astatus!="FRESH_PRIOR_PERIODIC_FILING":
            row["symbol_match_status"]="NOT_TESTED_NO_FRESH_ANCHOR";obs.append(row);print(f"PHASE338_PROGRESS={i}/72 {astatus}");continue
        facts,doc=retrieve_filing_facts(client,cik,filing);sf=extract_symbol_fact_rows(facts);tf=extract_title_fact_rows(facts)
        assoc=build_context_associations(sf,tf);symbols=sorted({x["symbol"] for x in sf})
        no_symbol=any(f.get("name")=="NoTradingSymbolFlag" and str(f.get("value") or "").strip().lower() in {"true","1"} for f in facts)
        cc=sum(bool(x.get("class_axis_members")) for x in sf);lc=sum(bool(x.get("listing_axis_members")) for x in sf);sm=summarize_facts(facts,s.get("candidate_symbol") or "")
        row.update({"document_status":doc.get("document_status",""),"document_sha256":doc.get("document_sha256",""),"document_bytes":doc.get("document_bytes",0),
            "document_http_status":doc.get("document_http_status",0),"index_http_status":doc.get("index_http_status",0),"trading_symbols":symbols,
            "symbol_fact_count":len(sf),"symbol_facts_with_class_axis":cc,"symbol_facts_with_listing_axis":lc,
            "all_symbol_facts_have_direct_class_axis":bool(sf) and cc==len(sf),"all_symbol_facts_have_direct_listing_axis":bool(sf) and lc==len(sf),
            "same_context_security_titles":sorted({t["value"] for t in tf if any(a["context_ref"]==t["context_ref"] for a in sf)}),
            "symbol_match_status":compare_candidate(s["index_status"],s.get("candidate_symbol") or "",symbols,no_symbol),
            "direct_class_binding":cc>0,"direct_listing_binding":lc>0,"context_associations":assoc,
            "document_class_axis_members_any_fact":sm.get("class_axis_members",[]),"document_listing_axis_members_any_fact":sm.get("listing_axis_members",[]),
            "document_has_no_trading_symbol_flag":no_symbol})
        obs.append(row);print(f"PHASE338_PROGRESS={i}/72 {astatus} {doc.get('document_status','')} SYMBOLS={len(symbols)}")
    ac=Counter(x.get("anchor_status","UNKNOWN") for x in obs);dc=Counter(x.get("document_status","UNKNOWN") for x in obs);mc=Counter(x.get("symbol_match_status","UNKNOWN") for x in obs)
    coverage={
        "issuer_identity_submissions_resolved":weighted_rate(obs,lambda r:r.get("submissions_status") in {"OK","CACHED_OK"}),
        "fresh_prior_periodic_anchor":weighted_rate(obs,lambda r:r.get("anchor_status")=="FRESH_PRIOR_PERIODIC_FILING"),
        "periodic_document_retrieved_and_hashed":weighted_rate(obs,lambda r:len(str(r.get("document_sha256") or ""))==64),
        "trading_symbol_fact_present":weighted_rate(obs,lambda r:int(r.get("symbol_fact_count") or 0)>0),
        "direct_symbol_class_binding":weighted_rate(obs,lambda r:bool(r.get("direct_class_binding")),
        "direct_symbol_listing_binding":weighted_rate(obs,lambda r:bool(r.get("direct_listing_binding")),
        "candidate_symbol_match_among_comparable":weighted_rate(obs,lambda r:r.get("symbol_match_status") in {"MATCH_SINGLE_SYMBOL","MATCH_AMONG_MULTIPLE_SYMBOLS"},lambda r:r.get("symbol_match_status") in {"MATCH_SINGLE_SYMBOL","MATCH_AMONG_MULTIPLE_SYMBOLS","MISMATCH"}),
        "direct_class_binding_conditional_on_symbol_fact":weighted_rate(obs,lambda r:bool(r.get("direct_class_binding")),lambda r:int(r.get("symbol_fact_count") or 0)>0),
        "direct_listing_binding_conditional_on_symbol_fact":weighted_rate(obs,lambda r:bool(r.get("direct_listing_binding")),lambda r:int(r.get("symbol_fact_count") or 0)>0),
        "permanent_security_identity_admitted":weighted_rate(obs,lambda r:False)}
    def grouped_coverage(key):
        result={}
        for label in sorted({x[key] for x in obs}):
            sub=[x for x in obs if x[key]==label]
            result[label]={"sample_n":len(sub),"anchor_status_counts":dict(sorted(Counter(x.get("anchor_status","UNKNOWN") for x in sub).items())),
                "trading_symbol_fact":weighted_rate(sub,lambda r:int(r.get("symbol_fact_count") or 0)>0),
                "direct_class_binding":weighted_rate(sub,lambda r:bool(r.get("direct_class_binding")),
                "direct_listing_binding":weighted_rate(sub,lambda r:bool(r.get("direct_listing_binding"))}
        return result
    result={"phase":PHASE,"status":"COMPLETED_WITH_EXPLICIT_COVERAGE_AND_IDENTITY_QUARANTINES","generated_at_utc":datetime.now(timezone.utc).isoformat(),
        "sample_manifest_sha256":sha256(Path(manifest_path).read_bytes()),"source":manifest["source"],"sample_frame":manifest["frame"],
        "summary":{"sample_issuer_quarter_units":len(obs),"unique_issuer_ciks":len({x["issuer_cik"] for x in obs}),
            "issuer_ciks_repeated_across_quarters":len(obs)-len({x["issuer_cik"] for x in obs}),
            "submissions_resolved":sum(x.get("submissions_status") in {"OK","CACHED_OK"} for x in obs),
            "fresh_anchor_units":ac["FRESH_PRIOR_PERIODIC_FILING"],"stale_anchor_units":ac["STALE_PRIOR_PERIODIC_FILING"],
            "no_prior_periodic_units":ac["NO_PRIOR_PERIODIC_FILING"],"invalid_anchor_units":ac["INVALID_NONPRE_EVENT_ANCHOR"]+ac["INVALID_DATE"],
            "submissions_unavailable_units":ac["SUBMISSIONS_UNAVAILABLE"]+ac["SUBMISSIONS_PARSE_ERROR"],
            "fresh_documents_retrieved_and_hashed":sum(x.get("anchor_status")=="FRESH_PRIOR_PERIODIC_FILING" and len(str(x.get("document_sha256") or ""))==64 for x in obs),
            "fresh_documents_with_trading_symbol_facts":sum(x.get("anchor_status")=="FRESH_PRIOR_PERIODIC_FILING" and int(x.get("symbol_fact_count") or 0)>0 for x in obs),
            "fresh_documents_with_direct_class_binding":sum(x.get("anchor_status")=="FRESH_PRIOR_PERIODIC_FILING" and bool(x.get("direct_class_binding")) for x in obs),
            "fresh_documents_with_direct_listing_binding":sum(x.get("anchor_status")=="FRESH_PRIOR_PERIODIC_FILING" and bool(x.get("direct_listing_binding")) for x in obs),
            "symbol_match_status_counts":dict(sorted(mc.items())),"anchor_status_counts":dict(sorted(ac.items())),"document_status_counts":dict(sorted(dc.items()))},
        "coverage":coverage,"coverage_by_quarter":grouped_coverage("quarter"),"coverage_by_stratum":grouped_coverage("sample_stratum"),"observations":obs,
        "controls":{"f80_frozen":True,"strict_pit_admitted":False,"security_master_admitted":False,"universe_coverage_admitted":False,
            "alpha_test_run":False,"return_test_run":False,"bootstrap_loo_run":False,"chronological_oos_run":False,"holdout_used":False,
            "production_changed":False,"universe_changed":False,"capital_changed":False,"parameters_changed":False,"data_purchased":False,"vendor_contacted":False},
        "interpretation":{"issuer_identity_primary_key":"issuer_cik","ticker_is_permanent_security_key":False,
            "class_binding_requires_trading_symbol_fact_own_context_class_axis":True,"listing_binding_requires_trading_symbol_fact_own_context_listing_axis":True,
            "document_level_axis_cooccurrence_is_not_direct_binding":True,"security_identity_admitted":False,"permanent_security_identifier_observed":False,
            "first_public_timestamp_observed":False,"filing_date_is_first_public_timestamp":False,"strict_pit_admitted":False,
            "sample_is_purposive_collision_panel":False,"sample_is_continuous_quarterly_panel":False,"sample_excludes_phase325_collision_issuers":True,
            "sample_is_survivorship_aware_within_sec_form4_issuer_frame":True,"sample_is_full_historical_trading_universe":False,
            "weighted_rates_are_descriptive_issuer_quarter_estimates_not_alpha":True}}
    (out/"phase338_broad_identity_audit.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    (out/"phase338_sample_manifest.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    write_csv(out/"phase338_issuer_observations.csv",obs)
    write_csv(out/"phase338_context_associations.csv",[{"accession":x["accession"],"issuer_cik":x["issuer_cik"],**a} for x in obs for a in x.get("context_associations",[])])
    print("PHASE338_STATUS="+result["status"]);print("PHASE338_SUMMARY="+json.dumps(result["summary"],sort_keys=True));print("PHASE338_COVERAGE="+json.dumps(coverage,sort_keys=True))
    return result

def write_csv(path,rows):
    if not rows:path.write_text("",encoding="utf-8");return
    fields=list(dict.fromkeys(k for r in rows for k in r))
    with path.open("w",newline="",encoding="utf-8-sig") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore");w.writeheader()
        for r in rows:w.writerow({k:json.dumps(v,ensure_ascii=False,sort_keys=True) if isinstance(v,(dict,list)) else v for k,v in r.items()})

def main():
    p=argparse.ArgumentParser();p.add_argument("--census-zip",type=Path,default=Path("phase321_source.zip"));p.add_argument("--collision-zip",type=Path,default=Path("phase325_source.zip"))
    p.add_argument("--sample-manifest",type=Path,default=Path("phase338_output/phase338_sample_manifest.json"));p.add_argument("--output-dir",type=Path,default=Path("phase338_output"));p.add_argument("--build-sample-only",action="store_true");a=p.parse_args()
    if a.build_sample_only:
        build_sample_manifest(a.census_zip,a.collision_zip,a.sample_manifest);print("PHASE338_SAMPLE_MANIFEST_SHA256="+sha256(a.sample_manifest.read_bytes()));return
    run_audit(a.sample_manifest,a.output_dir,os.environ.get("SEC_CONTACT_EMAIL",""))

if __name__=="__main__":main()

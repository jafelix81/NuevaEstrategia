#!/usr/bin/env python3
"""Phase 339: SEC SecurityExchangeName, Security12bTitle and symbol-context audit."""
from __future__ import annotations
import argparse, csv, hashlib, json, os
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

PHASE338_AUDIT_SHA256 = "0bcd8f355bd697d804296caeffd67fd69ff6aa593b8a5643535ad2f0224027a8"
PHASE338_MANIFEST_SHA256 = "9cca7f3eb027776dff89a4b44a0b234386ead708d758051a2b5e604f6d43736a"
PHASE338_RUN_ID = 43236684291
PHASE338_ARTIFACT_ID = 13953101909
PHASE338_ARTIFACT_SHA256 = "30b6a5b6753b24e8bd5d810d4193396249ed3f64de259e2fb8ef9513e29ecf92"

def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def norm_text(value: str) -> str:
    return " ".join(str(value or "").split())

def norm_symbol(value: str) -> str:
    return "".join(norm_text(value).upper().split())

def axis_members(fact: dict, token: str) -> list[str]:
    return sorted({
        str(d.get("dimension","")) + "=" + str(d.get("member",""))
        for d in (fact.get("dimensions") or [])
        if token in str(d.get("dimension",""))
    })

def find_primary_document_in_payload(payload: dict, accession: str) -> dict | None:
    from research.phase328_sec_collision_prior_filing_xbrl_pilot import _parallel_rows
    recent=payload.get("filings",{}).get("recent",{}) if isinstance(payload,dict) else {}
    for row in _parallel_rows(recent):
        if row.get("accessionNumber")==accession:
            return row
    return None

def find_filing_row(client, cik: str, accession: str, filing_date: str) -> tuple[dict | None, str, int]:
    url=f"https://data.sec.gov/submissions/CIK{str(cik).zfill(10)}.json"
    raw,status,err,_=client.get(url,max_bytes=20_000_000)
    if raw is None:
        return None,err or f"SUBMISSIONS_HTTP_{status}",status
    try:
        payload=json.loads(raw)
    except ValueError:
        return None,"SUBMISSIONS_JSON_PARSE_ERROR",status
    row=find_primary_document_in_payload(payload,accession)
    if row and row.get("primaryDocument"):
        return row,"RECENT",status
    files=payload.get("filings",{}).get("files",[]) or []
    candidates=[]
    for shard in files:
        start=str(shard.get("filingFrom") or "")
        end=str(shard.get("filingTo") or "")
        if start and start<=filing_date and (not end or filing_date<=end):
            candidates.append(shard)
    for shard in sorted(candidates,key=lambda x:str(x.get("filingTo") or ""),reverse=True):
        name=str(shard.get("name") or "")
        if not name: continue
        shard_raw,shard_status,shard_err,_=client.get(f"https://data.sec.gov/submissions/{name}",max_bytes=20_000_000)
        if shard_raw is None: continue
        try:
            shard_payload=json.loads(shard_raw)
        except ValueError:
            continue
        row=find_primary_document_in_payload(shard_payload,accession)
        if row and row.get("primaryDocument"):
            return row,f"SHARD:{name}",shard_status
    return None,"ACCESSION_NOT_FOUND_IN_SUBMISSIONS",status

def extract_context_rows(facts: list[dict]) -> tuple[list[dict], list[dict], list[dict]]:
    symbols=[]; exchanges=[]; titles=[]
    for fact in facts:
        name=fact.get("name")
        value=norm_text(fact.get("value",""))
        if not value: continue
        base={
            "context_ref":str(fact.get("context_ref") or ""),
            "dimensions":fact.get("dimensions") or [],
            "class_axis_members":axis_members(fact,"StatementClassOfStockAxis")+axis_members(fact,"ClassesOfShareCapitalAxis"),
            "listing_axis_members":axis_members(fact,"EntityListingsExchangeAxis"),
        }
        if name=="TradingSymbol":
            symbol=norm_symbol(value)
            if symbol:
                symbols.append({**base,"symbol":symbol})
        elif name=="SecurityExchangeName":
            exchanges.append({**base,"exchange_name":value})
        elif name in {"Security12bTitle","Security12gTitle"}:
            titles.append({**base,"title_name":name,"title":value})
    return symbols,exchanges,titles

def build_title_exchange_associations(titles: list[dict], exchanges: list[dict]) -> list[dict]:
    by_context=defaultdict(list)
    for ex in exchanges:
        if ex.get("context_ref"):
            by_context[ex["context_ref"]].append(ex)
    out=[]
    for title in titles:
        if title.get("title_name")!="Security12bTitle" or not title.get("context_ref"):
            continue
        same=by_context.get(title["context_ref"],[])
        out.append({
            "title_context_ref":title["context_ref"],
            "security_12b_title":title["title"],
            "same_context_exchange_values":sorted({x["exchange_name"] for x in same}),
            "same_context_exchange_fact_count":len(same),
            "title_class_axis_members":title.get("class_axis_members",[]),
            "title_listing_axis_members":title.get("listing_axis_members",[]),
            "exchange_listing_axis_members":sorted({m for x in same for m in x.get("listing_axis_members",[])}),
            "has_required_same_context_exchange":bool(same),
        })
    return out

def build_symbol_exchange_associations(symbols: list[dict], exchanges: list[dict], titles: list[dict]) -> list[dict]:
    exchange_by_context=defaultdict(list); title12b_by_context=defaultdict(list)
    for ex in exchanges:
        if ex.get("context_ref"): exchange_by_context[ex["context_ref"]].append(ex)
    for title in titles:
        if title.get("title_name")=="Security12bTitle" and title.get("context_ref"):
            title12b_by_context[title["context_ref"]].append(title)
    all_exchange_values=sorted({x["exchange_name"] for x in exchanges})
    out=[]
    for sym in symbols:
        ctx=sym.get("context_ref","")
        same_ex=exchange_by_context.get(ctx,[]) if ctx else []
        same_title=title12b_by_context.get(ctx,[]) if ctx else []
        ex_values=sorted({x["exchange_name"] for x in same_ex})
        title_values=sorted({x["title"] for x in same_title})
        if sym.get("listing_axis_members"):
            status="MULTI_LISTING_AXIS_ON_SYMBOL_CONTEXT"
        elif same_title and same_ex:
            status="SYMBOL_12B_TITLE_AND_EXCHANGE_SAME_CONTEXT"
        elif same_title:
            status="SYMBOL_12B_TITLE_SAME_CONTEXT_NO_EXCHANGE_FACT"
        elif same_ex:
            status="SYMBOL_EXCHANGE_SAME_CONTEXT_WITHOUT_12B_TITLE"
        elif all_exchange_values:
            status="DOCUMENT_LEVEL_EXCHANGE_ONLY_NOT_LINKED"
        else:
            status="NO_EXCHANGE_EVIDENCE"
        out.append({
            "symbol":sym["symbol"],"symbol_context_ref":ctx,
            "symbol_class_axis_members":sym.get("class_axis_members",[]),
            "symbol_listing_axis_members":sym.get("listing_axis_members",[]),
            "same_context_security_12b_titles":title_values,
            "same_context_exchange_values":ex_values,
            "same_context_exchange_fact_count":len(same_ex),
            "has_symbol_12b_title_exchange_same_context":bool(same_title and same_ex),
            "association_status":status,
        })
    return out

def weighted_rate(rows: list[dict], predicate, denominator=None) -> dict:
    use=[r for r in rows if denominator is None or denominator(r)]
    total=sum(float(r.get("design_weight") or 0) for r in use)
    positive=sum(float(r.get("design_weight") or 0) for r in use if predicate(r))
    return {
        "sample_n":len(use),"weighted_population_units":round(total,6),
        "weighted_positive_units":round(positive,6),
        "weighted_rate_pct":round(100*positive/total,4) if total else None,
        "unweighted_sample_rate_pct":round(100*sum(bool(predicate(r)) for r in use)/len(use),4) if use else None,
    }

def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("",encoding="utf-8"); return
    fields=list(dict.fromkeys(k for row in rows for k in row))
    with path.open("w",newline="",encoding="utf-8-sig") as f:
        writer=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k:json.dumps(v,ensure_ascii=False,sort_keys=True) if isinstance(v,(list,dict)) else v for k,v in row.items()})

def run_audit(audit_path: Path, output_dir: Path, email: str) -> dict:
    raw=audit_path.read_bytes()
    if sha256_bytes(raw)!=PHASE338_AUDIT_SHA256:
        raise ValueError("phase338_audit_json_hash_mismatch")
    source=json.loads(raw.decode("utf-8"))
    if source.get("phase")!=338 or source.get("status")!="COMPLETED_WITH_EXPLICIT_COVERAGE_AND_IDENTITY_QUARANTINES":
        raise ValueError("phase338_source_status_or_phase_mismatch")
    if source.get("sample_manifest_sha256")!=PHASE338_MANIFEST_SHA256:
        raise ValueError("phase338_sample_manifest_hash_mismatch")
    rows=[x for x in source.get("observations",[]) if x.get("document_status")=="XBRL_INSTANCE_PARSED"]
    if len(rows)!=42 or len({x.get("selected_filing_accession") for x in rows})!=42:
        raise ValueError("phase338_xbrl_source_denominator_mismatch")
    if not email or "@" not in email:
        raise RuntimeError("BLOCKED_MISSING_SEC_CONTACT_EMAIL")
    from research.phase328_sec_collision_prior_filing_xbrl_pilot import SECClient, retrieve_filing_facts
    client=SECClient(email); output_dir.mkdir(parents=True,exist_ok=True)
    documents=[]; associations=[]; exchange_rows=[]; title_exchange_rows=[]
    for i,row in enumerate(rows,1):
        accession=row["selected_filing_accession"]
        filing,lookup_status,submissions_status=find_filing_row(client,row["issuer_cik"],accession,row["selected_filing_date"])
        if not filing or str(filing.get("filingDate") or "")!=row["selected_filing_date"] or str(filing.get("form") or "")!=row["selected_filing_form"]:
            documents.append({
                "sample_accession":row["accession"],"issuer_cik":row["issuer_cik"],
                "selected_filing_accession":accession,"selected_filing_date":row["selected_filing_date"],
                "expected_sha256":row["document_sha256"],"actual_sha256":"",
                "primary_document_lookup_status":lookup_status,"submissions_http_status":submissions_status,
                "document_status":"PRIMARY_DOCUMENT_LOOKUP_FAILED","hash_match":False,
                "quarantine_reason":"PRIMARY_DOCUMENT_NOT_RECONCILED_TO_PHASE338_FILING",
                "design_weight":row["design_weight"],
            })
            print(f"PHASE339_PROGRESS={i}/42 PRIMARY_DOCUMENT_QUARANTINE")
            continue
        facts,meta=retrieve_filing_facts(client,row["issuer_cik"],filing)
        expected=row["document_sha256"]; actual=str(meta.get("document_sha256") or "")
        hash_ok=bool(expected) and actual==expected and meta.get("document_status")=="XBRL_INSTANCE_PARSED"
        if not hash_ok:
            documents.append({
                "sample_accession":row["accession"],"issuer_cik":row["issuer_cik"],
                "selected_filing_accession":accession,"selected_filing_date":row["selected_filing_date"],
                "expected_sha256":expected,"actual_sha256":actual,
                "primary_document_lookup_status":lookup_status,"primary_document":filing.get("primaryDocument",""),
                "document_status":meta.get("document_status",""),"document_name":meta.get("document_name",""),
                "index_http_status":meta.get("index_http_status",0),"document_http_status":meta.get("document_http_status",0),
                "index_error":meta.get("index_error",""),"hash_match":False,
                "quarantine_reason":"SOURCE_INSTANCE_NOT_REPRODUCED_BYTE_FOR_BYTE","design_weight":row["design_weight"],
            })
            print(f"PHASE339_PROGRESS={i}/42 HASH_QUARANTINE")
            continue
        symbols,exchanges,titles=extract_context_rows(facts)
        assoc=build_symbol_exchange_associations(symbols,exchanges,titles)
        title_assoc=build_title_exchange_associations(titles,exchanges)
        for a in assoc:
            a.update({"sample_accession":row["accession"],"issuer_cik":row["issuer_cik"],
                "selected_filing_accession":accession,"selected_filing_date":row["selected_filing_date"],
                "design_weight":row["design_weight"]})
            associations.append(a)
        for a in title_assoc:
            a.update({"sample_accession":row["accession"],"issuer_cik":row["issuer_cik"],
                "selected_filing_accession":accession,"selected_filing_date":row["selected_filing_date"],
                "design_weight":row["design_weight"]})
            title_exchange_rows.append(a)
        for ex in exchanges:
            exchange_rows.append({"sample_accession":row["accession"],"issuer_cik":row["issuer_cik"],
                "selected_filing_accession":accession,"selected_filing_date":row["selected_filing_date"],
                "exchange_name":ex["exchange_name"],"context_ref":ex["context_ref"],
                "class_axis_members":ex["class_axis_members"],"listing_axis_members":ex["listing_axis_members"],
                "design_weight":row["design_weight"]})
        title_exchange=sum(x["has_required_same_context_exchange"] for x in title_assoc)
        symbol_title_exchange=sum(x["has_symbol_12b_title_exchange_same_context"] for x in assoc)
        direct_axis=sum(bool(x["symbol_listing_axis_members"]) for x in assoc)
        doc={
            "sample_accession":row["accession"],"issuer_cik":row["issuer_cik"],
            "selected_filing_accession":accession,"selected_filing_date":row["selected_filing_date"],
            "expected_sha256":expected,"actual_sha256":actual,"primary_document":filing.get("primaryDocument",""),
            "primary_document_lookup_status":lookup_status,"document_status":meta.get("document_status",""),
            "document_name":meta.get("document_name",""),"document_bytes":meta.get("document_bytes",0),
            "hash_match":True,"trading_symbol_fact_count":len(symbols),
            "unique_trading_symbols":sorted({x["symbol"] for x in symbols}),
            "security_12b_title_fact_count":sum(x["title_name"]=="Security12bTitle" for x in titles),
            "security_12g_title_fact_count":sum(x["title_name"]=="Security12gTitle" for x in titles),
            "security_exchange_name_fact_count":len(exchanges),
            "unique_exchange_names":sorted({x["exchange_name"] for x in exchanges}),
            "title_12b_exchange_same_context_pair_count":title_exchange,
            "symbol_12b_title_exchange_same_context_count":symbol_title_exchange,
            "symbol_facts_with_listing_axis":direct_axis,
            "document_has_exchange_fact":bool(exchanges),
            "has_12b_title_exchange_same_context":title_exchange>0,
            "has_symbol_12b_title_exchange_same_context":symbol_title_exchange>0,
            "has_document_level_exchange_only":bool(exchanges) and title_exchange==0,
            "design_weight":row["design_weight"],
        }
        documents.append(doc)
        print(f"PHASE339_PROGRESS={i}/42 HASH_OK symbols={len(symbols)} titles12b={doc['security_12b_title_fact_count']} exchanges={len(exchanges)} title_exchange={title_exchange} symbol_title_exchange={symbol_title_exchange} listing_axis={direct_axis}")
    verified=[x for x in documents if x.get("hash_match")]
    if len(documents)!=42: raise ValueError("phase339_document_count_mismatch")
    summary={
        "phase338_xbrl_documents_expected":42,"documents_reprocessed":len(documents),
        "hash_verified_documents":len(verified),"hash_mismatch_or_unavailable_documents":len(documents)-len(verified),
        "documents_with_trading_symbol_facts":sum(x.get("trading_symbol_fact_count",0)>0 for x in verified),
        "documents_with_security_12b_title_facts":sum(x.get("security_12b_title_fact_count",0)>0 for x in verified),
        "documents_with_security_exchange_name_facts":sum(x.get("security_exchange_name_fact_count",0)>0 for x in verified),
        "documents_with_12b_title_exchange_same_context":sum(x.get("has_12b_title_exchange_same_context",False) for x in verified),
        "documents_with_symbol_12b_title_exchange_same_context":sum(x.get("has_symbol_12b_title_exchange_same_context",False) for x in verified),
        "documents_with_document_level_exchange_only":sum(x.get("has_document_level_exchange_only",False) for x in verified),
        "documents_without_exchange_name_facts":sum(not x.get("document_has_exchange_fact",False) for x in verified),
        "trading_symbol_fact_rows":sum(x.get("trading_symbol_fact_count",0) for x in verified),
        "security_12b_title_fact_rows":sum(x.get("security_12b_title_fact_count",0) for x in verified),
        "security_12g_title_fact_rows":sum(x.get("security_12g_title_fact_count",0) for x in verified),
        "security_exchange_name_fact_rows":sum(x.get("security_exchange_name_fact_count",0) for x in verified),
        "title_12b_exchange_same_context_pair_rows":sum(x.get("title_12b_exchange_same_context_pair_count",0) for x in verified),
        "symbol_facts_with_12b_title_exchange_same_context":sum(x.get("symbol_12b_title_exchange_same_context_count",0) for x in verified),
        "symbol_facts_with_listing_axis":sum(x.get("symbol_facts_with_listing_axis",0) for x in verified),
        "unique_exchange_names":sorted({e["exchange_name"] for e in exchange_rows}),
    }
    coverage={
        "exchange_name_fact_document_coverage_among_verified_xbrl":weighted_rate(verified,lambda r:r.get("document_has_exchange_fact",False)),
        "12b_title_exchange_same_context_coverage_among_verified_xbrl":weighted_rate(verified,lambda r:r.get("has_12b_title_exchange_same_context",False)),
        "symbol_12b_title_exchange_same_context_coverage_among_symbol_bearing_xbrl":weighted_rate(verified,lambda r:r.get("has_symbol_12b_title_exchange_same_context",False),lambda r:r.get("trading_symbol_fact_count",0)>0),
        "direct_listing_axis_document_coverage_among_symbol_bearing_xbrl":weighted_rate(verified,lambda r:r.get("symbol_facts_with_listing_axis",0)>0,lambda r:r.get("trading_symbol_fact_count",0)>0),
    }
    controls={"f80_frozen":True,"strict_pit_admitted":False,"security_master_admitted":False,
        "listing_security_mapping_admitted":False,"universe_coverage_admitted":False,
        "alpha_test_run":False,"return_test_run":False,"bootstrap_loo_run":False,
        "chronological_oos_run":False,"holdout_used":False,"production_changed":False,
        "universe_changed":False,"capital_changed":False,"parameters_changed":False,
        "data_purchased":False,"vendor_contacted":False}
    result={
        "phase":339,"status":"COMPLETED_WITH_EXPLICIT_SOURCE_QUARANTINES" if len(verified)!=42 else "COMPLETED_HASH_VERIFIED_IDENTITY_DIAGNOSTIC",
        "generated_at_utc":datetime.now(timezone.utc).isoformat(),
        "source":{"phase338_run_id":PHASE338_RUN_ID,"phase338_artifact_id":PHASE338_ARTIFACT_ID,
            "phase338_artifact_sha256":PHASE338_ARTIFACT_SHA256,"phase338_audit_json_sha256":PHASE338_AUDIT_SHA256,
            "phase338_sample_manifest_sha256":PHASE338_MANIFEST_SHA256},
        "summary":summary,"coverage":coverage,"documents":documents,
        "symbol_exchange_contexts":associations,"title_exchange_contexts":title_exchange_rows,
        "security_exchange_facts":exchange_rows,
        "interpretation":{
            "security_exchange_name_must_be_paired_with_security_12b_title_in_same_context":True,
            "symbol_to_12b_security_exchange_link_requires_symbol_title_and_exchange_in_same_context":True,
            "security_12g_title_does_not_require_national_exchange_name":True,
            "entity_listings_exchange_axis_is_multi_listing_evidence_not_required_for_single_listing":True,
            "security_exchange_name_values_cover_edgar_national_exchanges_not_all_venues":True,
            "document_level_cooccurrence_is_not_symbol_security_mapping":True,
            "effective_dated_listing_history_established":False,"first_public_timestamp_observed":False,
            "strict_pit_admitted":False,"security_identity_admitted":False,"universe_coverage_admitted":False},
        "controls":controls}
    (output_dir/"phase339_security_exchange_audit.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    write_csv(output_dir/"phase339_document_summary.csv",documents)
    write_csv(output_dir/"phase339_symbol_exchange_contexts.csv",associations)
    write_csv(output_dir/"phase339_title_exchange_contexts.csv",title_exchange_rows)
    write_csv(output_dir/"phase339_security_exchange_facts.csv",exchange_rows)
    print("PHASE339_STATUS="+result["status"])
    print("PHASE339_SUMMARY="+json.dumps(summary,sort_keys=True))
    print("PHASE339_COVERAGE="+json.dumps(coverage,sort_keys=True))
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--audit-json",type=Path,default=Path("phase338_source/phase338_broad_identity_audit.json"))
    p.add_argument("--output-dir",type=Path,default=Path("phase339_output"))
    p.add_argument("--email",default=os.environ.get("SEC_CONTACT_EMAIL",""))
    a=p.parse_args()
    run_audit(a.audit_json,a.output_dir,a.email)

if __name__=="__main__":main()

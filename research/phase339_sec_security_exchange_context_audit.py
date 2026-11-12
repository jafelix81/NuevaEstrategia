#!/usr/bin/env python3
"""Phase 339: recover SecurityExchangeName and test same-context symbol linkage."""
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

def build_symbol_exchange_associations(symbols: list[dict], exchanges: list[dict]) -> list[dict]:
    by_context=defaultdict(list)
    for ex in exchanges:
        if ex.get("context_ref"):
            by_context[ex["context_ref"]].append(ex)
    all_exchange_values=sorted({x["exchange_name"] for x in exchanges})
    out=[]
    for sym in symbols:
        same=by_context.get(sym.get("context_ref",""),[]) if sym.get("context_ref") else []
        values=sorted({x["exchange_name"] for x in same})
        if sym.get("listing_axis_members"):
            status="DIRECT_LISTING_AXIS_ON_SYMBOL_CONTEXT"
        elif values:
            status="SAME_CONTEXT_EXCHANGE_NAME_ONLY_NOT_SECURITY_IDENTITY"
        elif all_exchange_values:
            status="DOCUMENT_LEVEL_EXCHANGE_ONLY_NOT_LINKED"
        else:
            status="NO_EXCHANGE_EVIDENCE"
        out.append({
            "symbol":sym["symbol"],
            "symbol_context_ref":sym.get("context_ref",""),
            "symbol_class_axis_members":sym.get("class_axis_members",[]),
            "symbol_listing_axis_members":sym.get("listing_axis_members",[]),
            "same_context_exchange_values":values,
            "same_context_exchange_fact_count":len(same),
            "same_context_exchange_fact_listing_axis_members":sorted({m for x in same for m in x.get("listing_axis_members",[])}),
            "same_context_exchange_fact_class_axis_members":sorted({m for x in same for m in x.get("class_axis_members",[])}),
            "association_status":status,
        })
    return out

def weighted_rate(rows: list[dict], predicate, denominator=None) -> dict:
    use=[r for r in rows if denominator is None or denominator(r)]
    total=sum(float(r.get("design_weight") or 0) for r in use)
    positive=sum(float(r.get("design_weight") or 0) for r in use if predicate(r))
    return {
        "sample_n":len(use),
        "weighted_population_units":round(total,6),
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
    client=SECClient(email)
    output_dir.mkdir(parents=True,exist_ok=True)
    documents=[]; associations=[]; exchange_rows=[]
    for i,row in enumerate(rows,1):
        filing={"accessionNumber":row["selected_filing_accession"],"primaryDocument":""}
        facts,meta=retrieve_filing_facts(client,row["issuer_cik"],filing)
        expected=row["document_sha256"]
        actual=str(meta.get("document_sha256") or "")
        hash_ok=bool(expected) and actual==expected and meta.get("document_status")=="XBRL_INSTANCE_PARSED"
        if not hash_ok:
            documents.append({
                "sample_accession":row["accession"],"issuer_cik":row["issuer_cik"],
                "selected_filing_accession":row["selected_filing_accession"],
                "selected_filing_date":row["selected_filing_date"],
                "expected_sha256":expected,"actual_sha256":actual,
                "document_status":meta.get("document_status",""),
                "document_name":meta.get("document_name",""),
                "hash_match":False,"quarantine_reason":"SOURCE_INSTANCE_NOT_REPRODUCED_BYTE_FOR_BYTE",
                "design_weight":row["design_weight"],
            })
            print(f"PHASE339_PROGRESS={i}/42 HASH_QUARANTINE")
            continue
        symbols,exchanges,titles=extract_context_rows(facts)
        assoc=build_symbol_exchange_associations(symbols,exchanges)
        same_context_titles=defaultdict(list)
        for t in titles:
            if t.get("context_ref"): same_context_titles[t["context_ref"]].append(t["title"])
        for a in assoc:
            a["same_context_security_titles"]=sorted(set(same_context_titles.get(a["symbol_context_ref"],[])))
            a.update({
                "sample_accession":row["accession"],"issuer_cik":row["issuer_cik"],
                "selected_filing_accession":row["selected_filing_accession"],
                "selected_filing_date":row["selected_filing_date"],
                "design_weight":row["design_weight"],
            })
            associations.append(a)
        for ex in exchanges:
            exchange_rows.append({
                "sample_accession":row["accession"],"issuer_cik":row["issuer_cik"],
                "selected_filing_accession":row["selected_filing_accession"],
                "selected_filing_date":row["selected_filing_date"],
                "exchange_name":ex["exchange_name"],"context_ref":ex["context_ref"],
                "class_axis_members":ex["class_axis_members"],
                "listing_axis_members":ex["listing_axis_members"],
                "design_weight":row["design_weight"],
            })
        direct=sum(a["association_status"]=="DIRECT_LISTING_AXIS_ON_SYMBOL_CONTEXT" for a in assoc)
        same=sum(a["association_status"]=="SAME_CONTEXT_EXCHANGE_NAME_ONLY_NOT_SECURITY_IDENTITY" for a in assoc)
        doc={
            "sample_accession":row["accession"],"issuer_cik":row["issuer_cik"],
            "selected_filing_accession":row["selected_filing_accession"],
            "selected_filing_date":row["selected_filing_date"],
            "expected_sha256":expected,"actual_sha256":actual,
            "document_status":meta.get("document_status",""),
            "document_name":meta.get("document_name",""),
            "document_bytes":meta.get("document_bytes",0),"hash_match":True,
            "trading_symbol_fact_count":len(symbols),
            "unique_trading_symbols":sorted({x["symbol"] for x in symbols}),
            "security_exchange_name_fact_count":len(exchanges),
            "unique_exchange_names":sorted({x["exchange_name"] for x in exchanges}),
            "symbol_facts_with_same_context_exchange_name":same,
            "symbol_facts_with_direct_listing_axis":direct,
            "document_has_exchange_fact":bool(exchanges),
            "has_same_context_symbol_exchange_pair":same>0 or direct>0,
            "has_document_level_exchange_only":bool(exchanges) and not (same>0 or direct>0),
            "design_weight":row["design_weight"],
        }
        documents.append(doc)
        print(f"PHASE339_PROGRESS={i}/42 HASH_OK symbols={len(symbols)} exchanges={len(exchanges)} same_context={same} listing_axis={direct}")
    verified=[x for x in documents if x.get("hash_match")]
    if len(documents)!=42: raise ValueError("phase339_document_count_mismatch")
    summary={
        "phase338_xbrl_documents_expected":42,
        "documents_reprocessed":len(documents),
        "hash_verified_documents":len(verified),
        "hash_mismatch_or_unavailable_documents":len(documents)-len(verified),
        "documents_with_trading_symbol_facts":sum(x.get("trading_symbol_fact_count",0)>0 for x in verified),
        "documents_with_security_exchange_name_facts":sum(x.get("security_exchange_name_fact_count",0)>0 for x in verified),
        "documents_with_same_context_symbol_exchange_evidence":sum(x.get("has_same_context_symbol_exchange_pair",False) for x in verified),
        "documents_with_document_level_exchange_only":sum(x.get("has_document_level_exchange_only",False) for x in verified),
        "documents_without_exchange_name_facts":sum(not x.get("document_has_exchange_fact",False) for x in verified),
        "trading_symbol_fact_rows":sum(x.get("trading_symbol_fact_count",0) for x in verified),
        "security_exchange_name_fact_rows":sum(x.get("security_exchange_name_fact_count",0) for x in verified),
        "symbol_facts_with_same_context_exchange_name":sum(x.get("symbol_facts_with_same_context_exchange_name",0) for x in verified),
        "symbol_facts_with_direct_listing_axis":sum(x.get("symbol_facts_with_direct_listing_axis",0) for x in verified),
        "unique_exchange_names":sorted({e["exchange_name"] for e in exchange_rows}),
    }
    coverage={
        "exchange_name_fact_document_coverage_among_verified_xbrl":weighted_rate(verified,lambda r:r.get("document_has_exchange_fact",False)),
        "same_context_symbol_exchange_document_coverage_among_symbol_bearing_xbrl":weighted_rate(verified,lambda r:r.get("has_same_context_symbol_exchange_pair",False),lambda r:r.get("trading_symbol_fact_count",0)>0),
        "document_level_exchange_only_coverage_among_exchange_bearing_xbrl":weighted_rate(verified,lambda r:r.get("has_document_level_exchange_only",False),lambda r:r.get("document_has_exchange_fact",False)),
        "direct_listing_axis_document_coverage_among_symbol_bearing_xbrl":weighted_rate(verified,lambda r:r.get("symbol_facts_with_direct_listing_axis",0)>0,lambda r:r.get("trading_symbol_fact_count",0)>0),
    }
    controls={
        "f80_frozen":True,"strict_pit_admitted":False,"security_master_admitted":False,
        "listing_security_mapping_admitted":False,"universe_coverage_admitted":False,
        "alpha_test_run":False,"return_test_run":False,"bootstrap_loo_run":False,
        "chronological_oos_run":False,"holdout_used":False,"production_changed":False,
        "universe_changed":False,"capital_changed":False,"parameters_changed":False,
        "data_purchased":False,"vendor_contacted":False,
    }
    result={
        "phase":339,
        "status":"COMPLETED_WITH_EXPLICIT_SOURCE_QUARANTINES" if len(verified)!=42 else "COMPLETED_HASH_VERIFIED_IDENTITY_DIAGNOSTIC",
        "generated_at_utc":datetime.now(timezone.utc).isoformat(),
        "source":{
            "phase338_run_id":PHASE338_RUN_ID,"phase338_artifact_id":PHASE338_ARTIFACT_ID,
            "phase338_artifact_sha256":PHASE338_ARTIFACT_SHA256,
            "phase338_audit_json_sha256":PHASE338_AUDIT_SHA256,
            "phase338_sample_manifest_sha256":PHASE338_MANIFEST_SHA256,
        },
        "summary":summary,"coverage":coverage,"documents":documents,
        "symbol_exchange_contexts":associations,"security_exchange_facts":exchange_rows,
        "interpretation":{
            "security_exchange_name_is_not_automatically_a_security_listing":True,
            "same_context_exchange_name_is_contextual_evidence_not_a_security_master_mapping":True,
            "direct_listing_binding_requires_entity_listings_exchange_axis_on_symbol_fact_context":True,
            "document_level_cooccurrence_is_not_symbol_exchange_binding":True,
            "effective_dated_listing_history_established":False,
            "first_public_timestamp_observed":False,
            "strict_pit_admitted":False,
            "security_identity_admitted":False,
            "universe_coverage_admitted":False,
        },
        "controls":controls,
    }
    (output_dir/"phase339_security_exchange_audit.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    write_csv(output_dir/"phase339_document_summary.csv",documents)
    write_csv(output_dir/"phase339_symbol_exchange_contexts.csv",associations)
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

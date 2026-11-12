#!/usr/bin/env python3
"""Phase 340: verify that the Phase 338 identity anchor predates each Form 4 transaction."""
from __future__ import annotations
import argparse,csv,hashlib,json,os,re
from collections import Counter,defaultdict
from datetime import date,datetime,timezone
from pathlib import Path
import xml.etree.ElementTree as ET

P338_ARTIFACT_ID=13953101909
P338_ARTIFACT_SHA="30b6a5b6753b24e8bd5d810d4193396249ed3f64de259e2fb8ef9513e29ecf92"
P338_JSON_SHA="0bcd8f355bd697d804296caeffd67fd69ff6aa593b8a5643535ad2f0224027a8"
P338_MANIFEST_SHA="9cca7f3eb027776dff89a4b44a0b234386ead708d758051a2b5e604f6d43736a"
P339_ARTIFACT_ID=13959007527
P339_ARTIFACT_SHA="186bd582c8cd0ffff73cda16c7331e5a2bd34e413b6aba3715b5fac430a0a66f"
P339_JSON_SHA="4560b26f6cb37db8a3cf499207643026aab7e4e309ef8c7cf496b9e02d2d9e15"

def sha256_bytes(raw): return hashlib.sha256(raw).hexdigest()
def norm_title(value): return " ".join(re.sub(r"[^A-Z0-9]+"," ",str(value or "").upper()).split())
def parse_date(value):
    value=str(value or "").strip()
    try:return date.fromisoformat(value)
    except ValueError:return None

def anchor_relation(anchor_date,transaction_date):
    a=parse_date(anchor_date);t=parse_date(transaction_date)
    if not a or not t:return "MISSING_DATE"
    if a<t:return "ANCHOR_STRICTLY_PRE_TRANSACTION"
    if a==t:return "ANCHOR_SAME_DATE_NOT_STRICTLY_PRIOR"
    return "ANCHOR_AFTER_TRANSACTION_LOOKAHEAD"

def exact_title_matches(issuer_cik,title,mapping):
    key=(str(issuer_cik),norm_title(title))
    return sorted(set(mapping.get(key,[])))

def build_title_map(phase339):
    out=defaultdict(list)
    for row in phase339.get("symbol_exchange_contexts",[]):
        cik=str(row.get("issuer_cik") or "")
        for title in row.get("same_context_security_12b_titles",[]):
            n=norm_title(title)
            if cik and n:out[(cik,n)].append(row.get("symbol",""))
    return {k:sorted(set(v)) for k,v in out.items()}

def parse_ownership_root(raw):
    text=raw.decode("latin-1",errors="replace")
    docs=re.findall(r"<DOCUMENT>\s*(.*?)\s*</DOCUMENT>",text,flags=re.I|re.S)
    candidates=[]
    for doc in docs:
        typ=re.search(r"<TYPE>\s*([^\s<]+)",doc,flags=re.I)
        body=re.search(r"<TEXT>\s*(.*?)\s*</TEXT>",doc,flags=re.I|re.S)
        if not body:continue
        content=body.group(1).strip()
        xm=re.search(r"<XML>\s*(.*?)\s*</XML>",content,flags=re.I|re.S)
        content=xm.group(1).strip() if xm else content
        if (typ and typ.group(1).upper() in {"4","4/A"}) or "ownershipdocument" in content.lower():
            candidates.append(content)
    if not candidates:candidates=[text]
    for candidate in candidates:
        m=re.search(r"<ownershipDocument\b[\s\S]*?</ownershipDocument\s*>",candidate,flags=re.I)
        try:
            root=ET.fromstring((m.group(0) if m else candidate).encode("utf-8",errors="replace"))
            if root.tag.rsplit("}",1)[-1].split(":")[-1].lower()=="ownershipdocument":return root
        except ET.ParseError:pass
    return None

def extract_transaction_rows(raw,expected_issuer):
    from research.phase326_form4_collision_security_title_audit import descendants,value_of,parse_ownership_xml
    root=parse_ownership_root(raw)
    summary=parse_ownership_xml(raw)
    if root is None or summary.get("xml_status")!="PARSED":
        return summary,[]
    issuer_nodes=descendants(root,"issuer")
    issuer=issuer_nodes[0] if issuer_nodes else None
    xml_issuer=str(summary.get("xml_issuer_cik") or "")
    rows=[]
    for kind,tag in (("NON_DERIVATIVE","nonDerivativeTransaction"),("DERIVATIVE","derivativeTransaction")):
        for index,tx in enumerate(descendants(root,tag),1):
            rows.append({
                "transaction_kind":kind,"transaction_index":index,
                "transaction_date":value_of(tx,"transactionDate"),
                "security_title":value_of(tx,"securityTitle"),
                "underlying_security_title":value_of(tx,"underlyingSecurityTitle"),
                "transaction_code":value_of(tx,"transactionCode").upper(),
                "acquired_disposed":value_of(tx,"transactionAcquiredDisposedCode").upper(),
                "shares":value_of(tx,"transactionShares"),
                "price_per_share":value_of(tx,"transactionPricePerShare"),
                "underlying_shares":value_of(tx,"underlyingSecurityShares"),
                "underlying_price_per_share":value_of(tx,"underlyingSecurityPricePerShare"),
                "direct_or_indirect":value_of(tx,"directOrIndirectOwnership").upper(),
            })
    return {**summary,"xml_issuer_cik":xml_issuer,"issuer_matches_expected":xml_issuer==str(expected_issuer)},rows

def fetch_submission(client,row):
    from research.phase320_sec_bulk_daily_index_join import normalize_accession,normalize_cik
    from research.phase326_form4_collision_security_title_audit import path_ciks_for,submission_urls_for,parse_filing_header,parse_ownership_xml
    accession=normalize_accession(row["accession"]);issuer=normalize_cik(row["issuer_cik"])
    errors=[]
    for path_cik in path_ciks_for(accession,issuer,[]):
        for route,url in submission_urls_for(accession,path_cik):
            raw,status,err,headers=client.get(url,max_bytes=30_000_000)
            if raw is None:
                errors.append({"path_cik":path_cik,"route":route,"status":status,"error":err or ""});continue
            h=parse_filing_header(raw)
            header_ok=(normalize_accession(h.get("accession"))==accession and
                str(h.get("form_type") or "").upper()==str(row["form_type"]).upper() and
                str(h.get("filed_date") or "")==str(row["filing_date"]))
            if not header_ok:
                errors.append({"path_cik":path_cik,"route":route,"status":status,"error":"HEADER_IDENTITY_MISMATCH"});continue
            x= parse_ownership_xml(raw)
            if x.get("xml_status")!="PARSED" or str(x.get("xml_issuer_cik") or "")!=issuer:
                errors.append({"path_cik":path_cik,"route":route,"status":status,"error":"XML_ISSUER_IDENTITY_MISMATCH"});continue
            return raw,{"path_cik":path_cik,"route":route,"http_status":status,
                "header_cik":h.get("cik",""),"acceptance_datetime_et":h.get("acceptance_datetime_et",""),
                "submission_sha256":sha256_bytes(raw),"submission_bytes":len(raw),
                "xml_issuer_cik":x.get("xml_issuer_cik"),"xml_owner_ciks":x.get("xml_owner_ciks",[]),
                "xml_issuer_symbol":x.get("xml_issuer_symbol",""),"prior_route_errors":errors}
    return None,{"retrieval_status":"FAILED","prior_route_errors":errors}

def write_csv(path,rows):
    if not rows:path.write_text("",encoding="utf-8");return
    fields=list(dict.fromkeys(k for r in rows for k in r))
    with path.open("w",newline="",encoding="utf-8-sig") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore");w.writeheader()
        for r in rows:
            w.writerow({k:json.dumps(v,ensure_ascii=False,sort_keys=True) if isinstance(v,(list,dict)) else v for k,v in r.items()})

def run(audit_path,manifest_path,phase339_path,outdir,email):
    raw338=audit_path.read_bytes();rawm=manifest_path.read_bytes();raw339=phase339_path.read_bytes()
    if sha256_bytes(raw338)!=P338_JSON_SHA or sha256_bytes(rawm)!=P338_MANIFEST_SHA or sha256_bytes(raw339)!=P339_JSON_SHA:
        raise ValueError("pinned_source_json_hash_mismatch")
    p338=json.loads(raw338);manifest=json.loads(rawm);p339=json.loads(raw339)
    if p338.get("phase")!=338 or p339.get("phase")!=339 or manifest.get("phase")!=338:raise ValueError("source_phase_mismatch")
    if len(p338.get("observations",[]))!=72 or len(manifest.get("records",[]))!=72:raise ValueError("phase338_sample_denominator_mismatch")
    if p339.get("summary",{}).get("hash_verified_documents")!=42:raise ValueError("phase339_source_not_hash_verified")
    if not email or "@" not in email:raise RuntimeError("BLOCKED_MISSING_SEC_CONTACT_EMAIL")
    from research.phase328_sec_collision_prior_filing_xbrl_pilot import SECClient
    client=SECClient(email);title_map=build_title_map(p339);outdir.mkdir(parents=True,exist_ok=True)
    rawdir=outdir/"raw_submissions";rawdir.mkdir(exist_ok=True)
    mapping={x["accession"]:x for x in p338["observations"]}
    docs=[];transactions=[];errors=[]
    for i,row in enumerate(p338["observations"],1):
        raw,meta=fetch_submission(client,row)
        if raw is None:
            docs.append({"accession":row["accession"],"issuer_cik":row["issuer_cik"],"form_type":row["form_type"],
                "filing_date":row["filing_date"],"selected_filing_accession":row["selected_filing_accession"],
                "selected_filing_date":row["selected_filing_date"],"retrieval_status":"FAILED",
                "transaction_rows":0,"design_weight":row["design_weight"],"prior_route_errors":meta.get("prior_route_errors",[])})
            errors.append(row["accession"]);print(f"PHASE340_PROGRESS={i}/72 RETRIEVAL_FAILED");continue
        (rawdir/(row["accession"].replace("-","")+".txt")).write_bytes(raw)
        summary,txrows=extract_transaction_rows(raw,row["issuer_cik"])
        anchor=row.get("selected_filing_date","")
        for tx in txrows:
            relation=anchor_relation(anchor,tx.get("transaction_date"))
            title=tx.get("security_title","");under=tx.get("underlying_security_title","")
            matches=exact_title_matches(row["issuer_cik"],title,title_map)
            underlying_matches=exact_title_matches(row["issuer_cik"],under,title_map)
            tx.update({
                "accession":row["accession"],"issuer_cik":row["issuer_cik"],
                "form_type":row["form_type"],"filing_date":row["filing_date"],
                "selected_filing_accession":row["selected_filing_accession"],
                "selected_filing_date":anchor,"anchor_vs_transaction":relation,
                "anchor_predates_transaction":relation=="ANCHOR_STRICTLY_PRE_TRANSACTION",
                "security_title_normalized":norm_title(title),
                "exact_symbol_matches":matches,
                "exact_title_match_status":"EXACT_ONE_SYMBOL" if len(matches)==1 else "AMBIGUOUS_MULTIPLE_SYMBOLS" if len(matches)>1 else "NO_EXACT_TITLE_MATCH",
                "exact_mapped_symbol":matches[0] if len(matches)==1 else "",
                "underlying_exact_symbol_matches":underlying_matches,
                "underlying_title_match_status":"EXACT_ONE_SYMBOL" if len(underlying_matches)==1 else "AMBIGUOUS_MULTIPLE_SYMBOLS" if len(underlying_matches)>1 else "NO_EXACT_TITLE_MATCH",
                "underlying_exact_mapped_symbol":underlying_matches[0] if len(underlying_matches)==1 else "",
                "pit_identity_candidate":relation=="ANCHOR_STRICTLY_PRE_TRANSACTION" and len(matches)==1,
                "design_weight":row["design_weight"],
            })
            transactions.append(tx)
        dates=[parse_date(x.get("transaction_date")) for x in txrows]
        valid_dates=[x for x in dates if x]
        relations=[anchor_relation(anchor,x.isoformat() if x else "") for x in valid_dates]
        docs.append({
            "accession":row["accession"],"issuer_cik":row["issuer_cik"],"form_type":row["form_type"],
            "filing_date":row["filing_date"],"selected_filing_accession":row["selected_filing_accession"],
            "selected_filing_date":anchor,"anchor_age_calendar_days":row.get("anchor_age_calendar_days"),
            "retrieval_status":"RETRIEVED","submission_sha256":meta["submission_sha256"],
            "submission_bytes":meta["submission_bytes"],"path_cik":meta["path_cik"],"path_route":meta["route"],
            "header_cik":meta["header_cik"],"acceptance_datetime_et":meta["acceptance_datetime_et"],
            "xml_issuer_cik":meta["xml_issuer_cik"],"xml_issuer_matches":summary.get("issuer_matches_expected",False),
            "xml_owner_cik_count":len(meta.get("xml_owner_ciks",[])),"expected_reporting_owner_count":row.get("reporting_owner_count"),
            "xml_issuer_symbol":meta.get("xml_issuer_symbol",""),
            "non_derivative_count":summary.get("non_derivative_count",0),"derivative_count":summary.get("derivative_count",0),
            "transaction_rows":len(txrows),"transaction_rows_with_date":len(valid_dates),
            "transaction_rows_missing_date":len(txrows)-len(valid_dates),
            "transaction_rows_anchor_precedes":sum(x=="ANCHOR_STRICTLY_PRE_TRANSACTION" for x in relations),
            "transaction_rows_same_date_as_anchor":sum(x=="ANCHOR_SAME_DATE_NOT_STRICTLY_PRIOR" for x in relations),
            "transaction_rows_anchor_after":sum(x=="ANCHOR_AFTER_TRANSACTION_LOOKAHEAD" for x in relations),
            "all_transactions_have_dates":bool(txrows) and len(valid_dates)==len(txrows),
            "anchor_predates_all_transaction_dates":bool(txrows) and len(valid_dates)==len(txrows) and all(x=="ANCHOR_STRICTLY_PRE_TRANSACTION" for x in relations),
            "design_weight":row["design_weight"],
        })
        print(f"PHASE340_PROGRESS={i}/72 RETRIEVED tx={len(txrows)} pre={sum(x=='ANCHOR_STRICTLY_PRE_TRANSACTION' for x in relations)} same={sum(x=='ANCHOR_SAME_DATE_NOT_STRICTLY_PRIOR' for x in relations)} after={sum(x=='ANCHOR_AFTER_TRANSACTION_LOOKAHEAD' for x in relations)}")
    retrieved=[x for x in docs if x.get("retrieval_status")=="RETRIEVED"]
    dated=[x for x in transactions if parse_date(x.get("transaction_date"))]
    summary={
        "sample_accessions_expected":72,"accessions_retrieved":len(retrieved),"accession_retrieval_failures":len(docs)-len(retrieved),
        "form4_accessions":sum(x.get("form_type")=="4" for x in docs),"form4a_accessions":sum(x.get("form_type")=="4/A" for x in docs),
        "transaction_rows":len(transactions),"transaction_rows_with_date":len(dated),
        "transaction_rows_missing_date":len(transactions)-len(dated),
        "transaction_rows_anchor_precedes":sum(x.get("anchor_vs_transaction")=="ANCHOR_STRICTLY_PRE_TRANSACTION" for x in dated),
        "transaction_rows_same_date_as_anchor":sum(x.get("anchor_vs_transaction")=="ANCHOR_SAME_DATE_NOT_STRICTLY_PRIOR" for x in dated),
        "transaction_rows_anchor_after":sum(x.get("anchor_vs_transaction")=="ANCHOR_AFTER_TRANSACTION_LOOKAHEAD" for x in dated),
        "accessions_anchor_predates_all_transactions":sum(x.get("anchor_predates_all_transaction_dates",False) for x in retrieved),
        "accessions_with_any_anchor_after_transaction":sum(x.get("transaction_rows_anchor_after",0)>0 or x.get("transaction_rows_same_date_as_anchor",0)>0 for x in retrieved),
        "transactions_with_exact_security_title_to_symbol_match":sum(x.get("exact_title_match_status")=="EXACT_ONE_SYMBOL" for x in transactions),
        "transactions_with_ambiguous_exact_title_match":sum(x.get("exact_title_match_status")=="AMBIGUOUS_MULTIPLE_SYMBOLS" for x in transactions),
        "transactions_without_exact_security_title_match":sum(x.get("exact_title_match_status")=="NO_EXACT_TITLE_MATCH" for x in transactions),
        "transactions_pit_identity_candidates":sum(x.get("pit_identity_candidate",False) for x in transactions),
        "unique_transaction_codes":sorted({x.get("transaction_code","") for x in transactions if x.get("transaction_code")}),
    }
    coverage={
        "accession_retrieval_coverage":len(retrieved)/72*100,
        "accessions_anchor_predates_all_transactions_pct":100*summary["accessions_anchor_predates_all_transactions"]/len(retrieved) if retrieved else None,
        "transaction_rows_anchor_predates_pct":100*summary["transaction_rows_anchor_precedes"]/len(dated) if dated else None,
        "exact_title_match_pct":100*summary["transactions_with_exact_security_title_to_symbol_match"]/len(transactions) if transactions else None,
        "pit_identity_candidate_pct":100*summary["transactions_pit_identity_candidates"]/len(transactions) if transactions else None,
    }
    controls={"f80_frozen":True,"strict_pit_admitted":False,"security_master_admitted":False,
        "transaction_level_security_mapping_admitted":False,"event_study_admitted":False,"alpha_test_run":False,
        "return_test_run":False,"bootstrap_loo_run":False,"chronological_oos_run":False,"holdout_used":False,
        "production_changed":False,"universe_changed":False,"capital_changed":False,"parameters_changed":False,
        "data_purchased":False,"vendor_contacted":False}
    result={"phase":340,"status":"COMPLETED_WITH_EXPLICIT_RETRIEVAL_QUARANTINES" if len(retrieved)!=72 else "COMPLETED_TRANSACTION_DATE_PIT_DIAGNOSTIC",
        "generated_at_utc":datetime.now(timezone.utc).isoformat(),
        "sources":{"phase338_artifact_id":P338_ARTIFACT_ID,"phase338_artifact_sha256":P338_ARTIFACT_SHA,
            "phase338_audit_json_sha256":P338_JSON_SHA,"phase338_manifest_sha256":P338_MANIFEST_SHA,
            "phase339_artifact_id":P339_ARTIFACT_ID,"phase339_artifact_sha256":P339_ARTIFACT_SHA,
            "phase339_audit_json_sha256":P339_JSON_SHA},
        "summary":summary,"coverage":coverage,"accessions":docs,"transactions":transactions,
        "interpretation":{"anchor_before_form4_filing_date_is_not_enough":True,
            "transaction_date_is_required_for_pre_transaction_identity_anchor":True,
            "exact_security_title_match_is_conservative_not_complete":True,
            "no_fuzzy_title_mapping_admitted":True,"acceptance_datetime_is_not_first_public_receipt":True,
            "strict_pit_admitted":False,"event_study_admitted":False},
        "controls":controls}
    (outdir/"phase340_transaction_date_anchor_audit.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    write_csv(outdir/"phase340_accession_summary.csv",docs)
    write_csv(outdir/"phase340_transaction_rows.csv",transactions)
    (outdir/"phase340_retrieval_failures.json").write_text(json.dumps(errors,indent=2)+"\n",encoding="utf-8")
    print("PHASE340_STATUS="+result["status"]);print("PHASE340_SUMMARY="+json.dumps(summary,sort_keys=True));print("PHASE340_COVERAGE="+json.dumps(coverage,sort_keys=True))
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--audit-json",type=Path,default=Path("phase338_source/phase338_broad_identity_audit.json"))
    p.add_argument("--manifest",type=Path,default=Path("phase338_source/phase338_sample_manifest.json"))
    p.add_argument("--phase339-json",type=Path,default=Path("phase339_source/phase339_security_exchange_audit.json"))
    p.add_argument("--output-dir",type=Path,default=Path("phase340_output"))
    p.add_argument("--email",default=os.environ.get("SEC_CONTACT_EMAIL",""))
    a=p.parse_args();run(a.audit_json,a.manifest,a.phase339_json,a.output_dir,a.email)

if __name__=="__main__":main()

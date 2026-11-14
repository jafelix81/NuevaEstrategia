#!/usr/bin/env python3
"""Full 14-quarter SEC Form 144/A parent-identity census; no returns or signals."""
from __future__ import annotations
import argparse, csv, gzip, hashlib, json, random, re, threading, time, xml.etree.ElementTree as ET
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

SEC_ARCHIVES="https://www.sec.gov/Archives/edgar/data"
SEC_UA="NuevaEstrategia quantitative research jose.felix@felixsarmiento.com"
SEC_INTERVAL=0.20
_last_sec_request=0.0
_sec_lock=threading.Lock()

def norm_cik(value):
    if value in (None,""): return None
    digits=re.sub(r"\D","",str(value))
    return digits.zfill(10) if digits else None

def normalize_form(value):
    value=" ".join(str(value or "").upper().split()).replace("FORM ","")
    if "144/A" in value: return "144/A"
    return "144" if re.search(r"(^|[^A-Z0-9])144([^A-Z0-9]|$)",value) else None

def fetch_bytes(url,sec=True,timeout=60,retries=6):
    global _last_sec_request
    last_error=None
    for attempt in range(retries):
        if sec:
            with _sec_lock:
                wait=SEC_INTERVAL-(time.monotonic()-_last_sec_request)
                if wait>0: time.sleep(wait)
                _last_sec_request=time.monotonic()
        request=Request(url,headers={"User-Agent":SEC_UA,"Accept-Encoding":"gzip, deflate",
            "Accept":"application/json,text/html,application/xml,*/*"})
        try:
            with urlopen(request,timeout=timeout) as response:
                raw=response.read()
                if response.headers.get("Content-Encoding","").lower()=="gzip" or raw[:2]==b"\x1f\x8b":
                    raw=gzip.decompress(raw)
                return raw
        except HTTPError as error:
            last_error=error
            if error.code==404: raise
            if error.code not in (403,408,429,500,502,503,504): raise
            retry_after=error.headers.get("Retry-After") if error.headers else None
            try: delay=float(retry_after) if retry_after else min(45,2**attempt)
            except (TypeError,ValueError): delay=min(45,2**attempt)
            time.sleep(delay+random.uniform(0.1,0.6))
        except (URLError,TimeoutError,OSError) as error:
            last_error=error; time.sleep(min(30,2**attempt)+random.uniform(0.1,0.6))
    raise RuntimeError("GET failed after retries: {}: {}".format(url,last_error))

def parse_master_index(raw):
    if isinstance(raw,bytes): raw=raw.decode("latin-1","replace")
    lines=raw.lstrip("\ufeff").splitlines()
    header=None
    for i,line in enumerate(lines):
        if line.strip().lower().startswith("cik|company name|form type|date filed|filename"):
            header=i; break
    if header is None: raise ValueError("SEC master.idx header not found")
    grouped={}
    for line in lines[header+1:]:
        if not line.strip() or line.startswith("---"): continue
        parts=line.split("|",4)
        if len(parts)!=5: continue
        master_cik,company,raw_form,filed,filename=[x.strip() for x in parts]
        form=normalize_form(raw_form)
        if form not in ("144","144/A"): continue
        m=re.search(r"(\d{10}-\d{2}-\d{6})\.txt$",filename,re.I)
        if not m: continue
        acc=m.group(1)
        path_match=re.search(r"/data/(\d+)/",filename,re.I)
        item=grouped.setdefault(acc,{"accession":acc,"entities":{},"paths":set(),"forms":set(),"dates":set()})
        item["entities"][norm_cik(master_cik)]=company
        if path_match: item["paths"].add(norm_cik(path_match.group(1)))
        item["forms"].add(form); item["dates"].add(filed)
    out=[]
    for acc,item in grouped.items():
        paths=sorted(item["paths"]); forms=sorted(item["forms"]); dates=sorted(item["dates"])
        out.append({"accession":acc,"form":forms[0] if len(forms)==1 else None,
            "filing_date":dates[0] if len(dates)==1 else None,
            "master_index_ciks":sorted(item["entities"]),
            "archive_path_cik":paths[0] if len(paths)==1 else None,
            "metadata_conflict":len(forms)!=1 or len(dates)!=1 or len(paths)>1})
    return sorted(out,key=lambda x:(x.get("filing_date") or "",x["accession"]))

def local_name(tag): return tag.rsplit("}",1)[-1].lower()

def descendants(root,name):
    wanted=name.lower()
    return [x for x in root.iter() if local_name(x.tag)==wanted]

def first_text(root,name):
    for x in descendants(root,name):
        if x.text and x.text.strip(): return x.text.strip()
    return None

def all_text(root,name):
    return [x.text.strip() for x in descendants(root,name) if x.text and x.text.strip()]

def parse_form144_xml(raw):
    if isinstance(raw,bytes): raw=raw.decode("utf-8","replace")
    root=ET.fromstring(raw)
    if local_name(root.tag)!="edgarsubmission": raise ValueError("Unexpected Form 144 XML root")
    submission=normalize_form(first_text(root,"submissionType"))
    if submission not in ("144","144/A"): raise ValueError("Unexpected Form 144 submissionType")
    filers=descendants(root,"filerCredentials")
    filer=norm_cik(first_text(filers[0],"cik")) if filers else norm_cik(first_text(root,"cik"))
    return {"submission_type":submission,"filer_cik":filer,
        "previous_accession":first_text(root,"previousAccessionNumber"),
        "issuer_cik":norm_cik(first_text(root,"issuerCik")),"issuer_name":first_text(root,"issuerName"),
        "seller_name":first_text(root,"nameOfPersonForWhoseAccountTheSecuritiesAreToBeSold"),
        "remarks":all_text(root,"remarks")}

def parse_number(value):
    if value in (None,""): return None
    try: return Decimal(re.sub(r"[$, ]","",str(value).strip()))
    except (InvalidOperation,TypeError,ValueError): return None

def parse_date(value):
    value=str(value or "").strip()
    for fmt in ("%m/%d/%Y","%Y-%m-%d"):
        try: return datetime.strptime(value,fmt).date().isoformat()
        except ValueError: pass
    return None

def extract_sale_tranches(root):
    nodes=[x for x in root.iter() if local_name(x.tag)=="securitiesinformation"]
    result=[]
    for i,node in enumerate(nodes,1):
        result.append({"sale_tranche_index":i,"security_class":first_text(node,"securitiesClassTitle"),
            "units_numeric":parse_number(first_text(node,"noOfUnitsSold")),
            "value_numeric":parse_number(first_text(node,"aggregateMarketValue")),
            "outstanding_numeric":parse_number(first_text(node,"noOfUnitsOutstanding")),
            "approx_sale_date_iso":parse_date(first_text(node,"approxSaleDate")),
            "exchange":first_text(node,"securitiesExchangeName"),
            "broker_or_market_maker":first_text(node,"name")})
    return result

QUARTERS=("2023Q2,2023Q3,2023Q4,2024Q1,2024Q2,2024Q3,2024Q4,2025Q1,2025Q2,2025Q3,2025Q4,2026Q1,2026Q2,2026Q3")
START_DATE="2023-04-13"
EXPECTED_CHILDREN=609
EXPECTED_INDEX=56167
EXPECTED_CANDIDATE_CIKS=290
MANIFEST=Path(__file__).with_name("PHASE401_FORM144_CANDIDATE_CIK_MANIFEST_2026-11-14.json")
PHASE400=Path(__file__).with_name("PHASE400_FORM144_EXTERNAL_PARENT_IDENTITY_SUMMARY_2026-11-14.json")

def accession(value):
    digits=re.sub(r"\D","",str(value or ""))
    return f"{digits[:10]}-{digits[10:12]}-{digits[12:]}" if len(digits)==18 else None

def quarter(token):
    m=re.fullmatch(r"(20\d{2})Q([1-4])",token)
    if not m: raise ValueError("Invalid quarter: "+token)
    return int(m.group(1)),int(m.group(2))

def norm_text(value): return re.sub(r"[^A-Z0-9]+","",str(value or "").upper())

def num(value):
    if value in (None,""): return None
    try: d=Decimal(str(value).replace(",","").strip())
    except (InvalidOperation,TypeError,ValueError): return str(value).strip()
    return str(int(d)) if d==d.to_integral_value() else format(d.normalize(),"f")

def date_iso(value):
    value=str(value or "").strip()
    for fmt in ("%m/%d/%Y","%Y-%m-%d"):
        try: return datetime.strptime(value,fmt).date().isoformat()
        except ValueError: pass
    return value or None

def tranche_sig(items):
    rows=[]
    for x in items or []:
        rows.append({"class":norm_text(x.get("security_class")),"units":num(x.get("units_numeric")),
            "value":num(x.get("value_numeric")),"outstanding":num(x.get("outstanding_numeric")),
            "approx_sale_date":x.get("approx_sale_date_iso"),"exchange":norm_text(x.get("exchange")),
            "broker":norm_text(x.get("broker_or_market_maker"))})
    return sorted(rows,key=lambda x:json.dumps(x,sort_keys=True))

def tranche_payload_changed(child,parent):
    if len(child or [])!=len(parent or []): return True
    for left,right in zip(child or [],parent or []):
        for key in ("class","units","value","outstanding","approx_sale_date","exchange","broker"):
            a,b=left.get(key),right.get(key)
            if a not in (None,"") and b not in (None,"") and a!=b: return True
    return False

def load_index(tokens):
    by_acc,counts,duplicates={},{},[]
    for token in tokens:
        year,qtr=quarter(token)
        url=f"https://www.sec.gov/Archives/edgar/full-index/{year}/QTR{qtr}/master.idx"
        rows=parse_master_index(fetch_bytes(url,sec=True,timeout=90,retries=5))
        rows=[r for r in rows if r.get("form") in ("144","144/A")]
        counts[token]={"accessions":len(rows),"form_144":sum(r.get("form")=="144" for r in rows),
                       "form_144a":sum(r.get("form")=="144/A" for r in rows)}
        for r in rows:
            acc=accession(r.get("accession"))
            if not acc: duplicates.append({"quarter":token,"accession":r.get("accession"),"reason":"invalid"}); continue
            if acc in by_acc: duplicates.append({"quarter":token,"accession":acc,"reason":"duplicate"}); continue
            item=dict(r); item.update({"accession":acc,"year":year,"quarter":qtr}); by_acc[acc]=item
    return by_acc,counts,duplicates

def xml_urls(row):
    ciks={norm_cik(x) for x in (row.get("master_index_ciks") or [])}
    if row.get("archive_path_cik"): ciks.add(norm_cik(row["archive_path_cik"]))
    acc_path=row["accession"].replace("-","")
    return [f"{SEC_ARCHIVES}/{int(cik)}/{acc_path}/primary_doc.xml" for cik in sorted(x for x in ciks if x)]

def fetch_doc(row):
    errors=[]
    for url in xml_urls(row):
        try:
            raw=fetch_bytes(url,sec=True,timeout=45,retries=4)
            parsed=parse_form144_xml(raw); root=ET.fromstring(raw)
            pair=set(row.get("master_index_ciks") or [])
            return {"ok":True,"parsed":parsed,"tranches":tranche_sig(extract_sale_tranches(root)),
                "url":url,"sha256":hashlib.sha256(raw).hexdigest(),
                "form_matches_index":parsed.get("submission_type")==row.get("form"),
                "issuer_in_pair":norm_cik(parsed.get("issuer_cik")) in pair,
                "filer_in_pair":norm_cik(parsed.get("filer_cik")) in pair}
        except Exception as e: errors.append(type(e).__name__+":"+str(e)[:160])
    return {"ok":False,"error":";".join(errors[-4:]) or "XML_NOT_FOUND"}

def load_phase400_parents():
    if not PHASE400.exists(): return {}
    data=json.loads(PHASE400.read_text(encoding="utf-8"))
    return {accession(p.get("parent",{}).get("accession")):p.get("parent",{})
            for p in data.get("pairs",[]) if accession(p.get("parent",{}).get("accession"))}

def curated_parent(p):
    return {"ok":True,"parsed":{"submission_type":"144","issuer_cik":norm_cik(p.get("issuer_cik")),
        "issuer_name":p.get("issuer_name"),"filer_cik":norm_cik(p.get("filer_cik")),
        "seller_name":p.get("seller"),"remarks":[]},"tranches":[{
        "class":norm_text(p.get("security_class")),"units":num(p.get("units_to_be_sold")),
        "value":num(p.get("aggregate_market_value_usd")),"outstanding":num(p.get("units_outstanding_raw")),
        "approx_sale_date":date_iso(p.get("approximate_sale_date")),"exchange":norm_text(p.get("exchange")),
        "broker":None}],"url":p.get("xml_url"),"sha256":None,"form_matches_index":None,
        "issuer_in_pair":None,"filer_in_pair":None,"curated_phase400_fallback":True}

def compare(child,parent,child_row,parent_row,candidates,parent_source):
    c,p=child["parsed"],parent["parsed"]
    cc,pc=norm_cik(c.get("issuer_cik")),norm_cik(p.get("issuer_cik"))
    child_cand=bool(cc and cc in candidates); parent_cand=bool(pc and pc in candidates)
    changed=bool(cc and pc and cc!=pc)
    if child_cand and not parent_cand: transition="parent_noncandidate_to_child_candidate"
    elif parent_cand and not child_cand: transition="parent_candidate_to_child_noncandidate"
    elif parent_cand and child_cand and changed: transition="candidate_to_candidate_cik_change"
    elif parent_cand and child_cand: transition="candidate_stable"
    elif changed: transition="noncandidate_to_noncandidate_cik_change"
    else: transition="noncandidate_stable_or_unresolved"
    remarks=" ".join(c.get("remarks") or [])
    explicit=bool(changed and re.search(r"(issuer|cik|sec file number).{0,80}(correct|change)|correct.{0,80}(issuer|cik|sec file number)",remarks,re.I))
    cd=child_row.get("filing_date") or ""; pd=(parent_row or {}).get("filing_date") or ""
    return {"child_accession":child_row["accession"],"parent_accession":accession(c.get("previous_accession")),
        "child_filing_date":cd,"parent_filing_date":pd or None,
        "parent_child_date_order_ok":None if not cd or not pd else pd<=cd,
        "child_form":c.get("submission_type"),"parent_form":p.get("submission_type"),
        "parent_source":parent_source,"parent_in_14q_census":parent_row is not None,
        "child_issuer_cik":cc,"parent_issuer_cik":pc,"issuer_cik_changed":changed,
        "child_issuer_name":c.get("issuer_name") or "","parent_issuer_name":p.get("issuer_name") or "",
        "issuer_name_changed":norm_text(c.get("issuer_name"))!=norm_text(p.get("issuer_name")),
        "child_filer_cik":norm_cik(c.get("filer_cik")),"parent_filer_cik":norm_cik(p.get("filer_cik")),
        "filer_cik_changed":norm_cik(c.get("filer_cik"))!=norm_cik(p.get("filer_cik")),
        "child_seller":c.get("seller_name") or "","parent_seller":p.get("seller_name") or "",
        "seller_changed":norm_text(c.get("seller_name"))!=norm_text(p.get("seller_name")),
        "child_issuer_is_candidate":child_cand,"parent_issuer_is_candidate":parent_cand,
        "candidate_membership_transition":transition,"remarks_explicit_identity_correction":explicit,
        "child_tranches_json":json.dumps(child.get("tranches") or [],sort_keys=True),
        "parent_tranches_json":json.dumps(parent.get("tranches") or [],sort_keys=True),
        "sale_tranches_changed":tranche_payload_changed(child.get("tranches") or [],parent.get("tranches") or []),
        "child_xml_url":child.get("url"),"parent_xml_url":parent.get("url"),
        "child_xml_sha256":child.get("sha256"),"parent_xml_sha256":parent.get("sha256"),
        "child_xml_form_matches_index":child.get("form_matches_index"),
        "parent_xml_form_matches_index":parent.get("form_matches_index"),
        "child_xml_pair_concordant":bool(child.get("issuer_in_pair") and child.get("filer_in_pair")),
        "parent_xml_pair_concordant":None if parent.get("issuer_in_pair") is None else bool(parent.get("issuer_in_pair") and parent.get("filer_in_pair")),
        "curated_parent_fallback":bool(parent.get("curated_phase400_fallback"))}

def write_csv(path,rows):
    if not rows: path.write_text("\n",encoding="utf-8"); return
    fields=list(dict.fromkeys(k for r in rows for k in r))
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore"); w.writeheader(); w.writerows(rows)

def audit(manifest,workers=5,output=Path("phase401_form144a_full_parent_identity_census")):
    candidates=set(manifest.get("candidate_ciks") or [])
    if len(candidates)!=EXPECTED_CANDIDATE_CIKS or any(not re.fullmatch(r"\d{10}",x) for x in candidates):
        raise ValueError("Phase 67 candidate CIK manifest integrity failure")
    index,quarter_counts,duplicates=load_index([x for x in QUARTERS.split(",") if x])
    children=sorted((r for r in index.values() if r.get("form")=="144/A" and r.get("filing_date") and r["filing_date"]>=START_DATE),
                    key=lambda r:(r.get("filing_date") or "",r["accession"]))
    child_results,child_errors={},[]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures={pool.submit(fetch_doc,r):r for r in children}
        for future in as_completed(futures):
            row=futures[future]; result=future.result(); child_results[row["accession"]]=result
            if not result.get("ok"): child_errors.append({"accession":row["accession"],"error":result.get("error")})
    parent_accs=sorted({accession(x["parsed"].get("previous_accession")) for x in child_results.values()
                        if x.get("ok") and accession(x["parsed"].get("previous_accession"))})
    phase400=load_phase400_parents()
    parent_rows={a:index[a] for a in parent_accs if a in index}
    parent_results,parent_errors={},[]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures={pool.submit(fetch_doc,r):a for a,r in parent_rows.items() if a not in child_results}
        for future in as_completed(futures):
            a=futures[future]; result=future.result(); parent_results[a]=result
            if not result.get("ok"): parent_errors.append({"accession":a,"error":result.get("error")})
    pairs,unresolved=[],[]; links=0
    for row in children:
        child=child_results.get(row["accession"],{})
        if not child.get("ok"): unresolved.append({"child_accession":row["accession"],"status":"child_xml_unresolved"}); continue
        parent_acc=accession(child["parsed"].get("previous_accession"))
        if not parent_acc: unresolved.append({"child_accession":row["accession"],"status":"missing_previous_accession"}); continue
        links+=1; parent_row=index.get(parent_acc)
        if parent_acc in child_results and child_results[parent_acc].get("ok"):
            parent,source=child_results[parent_acc],"same_census_child_cache"
        elif parent_results.get(parent_acc,{}).get("ok"):
            parent,source=parent_results[parent_acc],"master_index"
        elif parent_acc not in index and parent_acc in phase400:
            parent,source=curated_parent(phase400[parent_acc]),"phase400_curated_parent"
        else:
            unresolved.append({"child_accession":row["accession"],"parent_accession":parent_acc,"status":"parent_xml_unresolved"}); continue
        item=compare(child,parent,row,parent_row,candidates,source); pairs.append(item)
        if not item["child_xml_form_matches_index"]: unresolved.append({"child_accession":row["accession"],"status":"child_form_index_mismatch"})
        if parent_row and not item["parent_xml_form_matches_index"]: unresolved.append({"child_accession":row["accession"],"parent_accession":parent_acc,"status":"parent_form_index_mismatch"})
    transitions=Counter(x["candidate_membership_transition"] for x in pairs)
    child_ok=[x for x in child_results.values() if x.get("ok")]
    parent_pair_rows=[x for x in pairs if x.get("parent_xml_pair_concordant") is not None]
    child_form_rate=sum(bool(x.get("form_matches_index")) for x in child_ok)/len(child_ok) if child_ok else None
    child_pair_rate=sum(bool(x.get("issuer_in_pair") and x.get("filer_in_pair")) for x in child_ok)/len(child_ok) if child_ok else None
    parent_pair_rate=sum(bool(x.get("parent_xml_pair_concordant")) for x in parent_pair_rows)/len(parent_pair_rows) if parent_pair_rows else None
    parent_form_rows=[x for x in pairs if x.get("parent_xml_form_matches_index") is not None]
    parent_form_rate=sum(bool(x["parent_xml_form_matches_index"]) for x in parent_form_rows)/len(parent_form_rows) if parent_form_rows else None
    parent_link_rate=len(pairs)/links if links else None
    child_candidate=sum(norm_cik(x["parsed"].get("issuer_cik")) in candidates for x in child_ok)
    gates={"index_census_matches_phase67_56167":len(index)==EXPECTED_INDEX,
        "child_census_matches_phase67_609":len(children)==EXPECTED_CHILDREN,
        "every_parsed_child_has_explicit_previous_accession":links==len(child_ok),
        "child_xml_fetch_rate_ge_99_5pct":bool(children) and len(child_ok)/len(children)>=.995,
        "child_xml_form_match_rate_ge_99_5pct":child_form_rate is not None and child_form_rate>=.995,
        "child_xml_pair_concordance_ge_99_5pct":child_pair_rate is not None and child_pair_rate>=.995,
        "parent_link_resolution_rate_ge_99_5pct":parent_link_rate is not None and parent_link_rate>=.995,
        "parent_xml_form_match_rate_ge_99_5pct":parent_form_rate is None or parent_form_rate>=.995,
        "parent_xml_pair_concordance_ge_99_5pct":parent_pair_rate is None or parent_pair_rate>=.995,
        "no_parent_child_date_inversions":not any(x.get("parent_child_date_order_ok") is False for x in pairs),
        "no_duplicate_index_accessions":len(duplicates)==0,
        "historical_f80_identity_gate":False,"economic_test_authorized":False}
    summary={"phase":401,"audit_date_utc":datetime.now(timezone.utc).isoformat(),
        "source":"SEC master.idx + primary_doc.xml; exact Phase 67 candidate CIK snapshot; Phase 400 curated parent fallback only for known parent outside 14-quarter index.",
        "candidate_manifest":{"artifact_id":manifest.get("source_artifact_id"),"artifact_sha256":manifest.get("source_artifact_sha256"),"candidate_ciks":len(candidates)},
        "index_census":{"quarters":[{"quarter":q,**v} for q,v in quarter_counts.items()],"unique_accessions":len(index),
            "expected_unique_accessions":EXPECTED_INDEX,"child_144a_accessions":len(children),"expected_child_144a_accessions":EXPECTED_CHILDREN,"duplicate_accession_rows":len(duplicates)},
        "child_xml":{"attempted":len(children),"parsed":len(child_ok),"errors":len(child_errors),"form_match_rate":child_form_rate,
            "pair_concordance_rate":child_pair_rate,"child_links_with_previous_accession":links,
            "child_issuer_ciks_in_phase67_candidate_set":child_candidate,"child_issuer_ciks_outside_phase67_candidate_set":len(child_ok)-child_candidate,
            "unique_parent_accessions":len(parent_accs)},
        "parent_xml":{"parents_in_index":len(parent_rows),"parents_fetched_not_reused_from_child_cache":sum(x.get("ok") for x in parent_results.values()),
            "fetch_errors":len(parent_errors),"resolved_parent_links":len(pairs),"parent_link_resolution_rate":parent_link_rate,
            "phase400_curated_parent_fallbacks":sum(x["curated_parent_fallback"] for x in pairs),
            "form_match_rate":parent_form_rate,"pair_concordance_rate":parent_pair_rate,"unresolved_links":len(unresolved)},
        "identity_changes":{"issuer_cik_changes":sum(x["issuer_cik_changed"] for x in pairs),
            "explicit_identity_correction_remarks":sum(x["remarks_explicit_identity_correction"] for x in pairs),
            "issuer_name_changes":sum(x["issuer_name_changed"] for x in pairs),"filer_cik_changes":sum(x["filer_cik_changed"] for x in pairs),
            "seller_name_changes":sum(x["seller_changed"] for x in pairs),"sale_tranche_payload_changes":sum(x["sale_tranches_changed"] for x in pairs),
            "candidate_membership_transitions":dict(transitions)},
        "quality_gates":gates,
        "data_integrity_gate":"PASS" if all(v for k,v in gates.items() if k not in ("historical_f80_identity_gate","economic_test_authorized")) else "FAIL_OR_INCOMPLETE",
        "decision":{"144a_is_version_update_not_new_sale":True,"corrected_identity_may_be_backdated":False,
            "noOfUnitsOutstanding_feature":"KILLED; raw version comparison only","forward_returns_used":False,
            "alpha_oos_bootstrap_loo_holdout_used":False,"f80_changed":False},
        "unresolved_status_counts":dict(Counter(x["status"] for x in unresolved))}
    out=Path(output); out.mkdir(parents=True,exist_ok=True)
    (out/"summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    write_csv(out/"all_amendment_parent_pairs.csv",pairs); write_csv(out/"unresolved_parent_links.csv",unresolved)
    write_csv(out/"child_xml_errors.csv",child_errors); write_csv(out/"parent_xml_errors.csv",parent_errors)
    write_csv(out/"duplicate_index_rows.csv",duplicates)
    print(json.dumps(summary,indent=2,sort_keys=True),flush=True)
    return summary

def main():
    p=argparse.ArgumentParser(); p.add_argument("--workers",type=int,default=5)
    p.add_argument("--output",type=Path,default=Path("phase401_form144a_full_parent_identity_census"))
    p.add_argument("--manifest",type=Path,default=MANIFEST); args=p.parse_args()
    manifest=json.loads(args.manifest.read_text(encoding="utf-8"))
    summary=audit(manifest,workers=args.workers,output=args.output)
    failed=[k for k,v in summary["quality_gates"].items() if not v and k not in ("historical_f80_identity_gate","economic_test_authorized")]
    if failed: raise SystemExit("Phase 401 gates failed: "+", ".join(failed))

if __name__=="__main__": main()

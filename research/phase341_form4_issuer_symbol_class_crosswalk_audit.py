from __future__ import annotations
import argparse,csv,hashlib,json,re,xml.etree.ElementTree as ET
from collections import Counter,defaultdict
from datetime import date
from pathlib import Path
EXCHANGES={"NYSE","NASDAQ","NYSE AMERICAN","NYSEAMERICAN","NYSE ARCA","NYSEARCA","AMEX","ARCA","BATS","OTC"}
def sha(b):return hashlib.sha256(b).hexdigest()
def norm(s):return re.sub(r"\s+"," ",re.sub(r"[^A-Z0-9]+"," ",(s or "").upper())).strip()
def parse_symbol(raw):
 s=(raw or "").strip().upper(); ex=""
 if not s:return "","MISSING",""
 if ":" in s:
  p=s.split(":")
  if len(p)!=2:return "","MULTI_OR_MALFORMED",""
  ex=re.sub(r"\s+"," ",p[0].strip())
  if ex not in EXCHANGES:return "","UNKNOWN_EXCHANGE_PREFIX",ex
  s=p[1].strip()
 if len(s)>1 and (s[0],s[-1]) in {('"','"'),("'","'"),("(",")"),("[","]")}:s=s[1:-1].strip()
 if s in {"","N/A","NA","NONE","NAN","-","NOT APPLICABLE"}:return "","PLACEHOLDER",ex
 if any(c in s for c in [",",";","/"," ","\t","\n","\\"]):return "","MULTI_OR_MALFORMED",ex
 if not re.fullmatch(r"[A-Z0-9]+(?:[.-][A-Z0-9]+)*",s):return "","MALFORMED",ex
 return s,"SINGLE_TOKEN",ex
def cls(s):
 u=(s or "").upper(); c=tuple(re.findall(r"\bCLASS\s+([A-Z0-9]+)\b",u)); q=tuple(re.findall(r"\bSERIES\s+([A-Z0-9]+(?:-[A-Z0-9]+)?)\b",u))
 if not u.strip():k="UNKNOWN"
 elif "WARRANT" in u:k="WARRANT"
 elif "PREFERRED" in u or "PREFERENCE" in u:k="PREFERRED"
 elif "DEPOSITARY" in u or re.search(r"\bADS\b",u):k="DEPOSITARY"
 elif any(x in u for x in ("DEBENTURE","SENIOR NOTE","SUBORDINATED NOTE","NOTES DUE","NOTE DUE","BOND")):k="DEBT"
 elif "CORPORATE UNIT" in u:k="CORPORATE_UNIT"
 elif "BENEFICIAL INTEREST" in u:k="BENEFICIAL_INTEREST"
 elif "ORDINARY" in u:k="ORDINARY_SHARES"
 elif "COMMON" in u:k="COMMON_STOCK"
 elif "OPTION" in u or "RIGHT TO BUY" in u:k="OPTION"
 else:k="OTHER"
 return k,c,q
def match_title(a,b):
 if not norm(a) or not norm(b):return False,"MISSING_TITLE",""
 if norm(a)==norm(b):return True,"EXACT_TITLE",cls(a)[0]
 x,y=cls(a),cls(b)
 if x[0]!=y[0]:return False,"INSTRUMENT_CLASS_MISMATCH",x[0]
 if x[0] in {"UNKNOWN","OTHER","OPTION","CORPORATE_UNIT","DEBT","WARRANT"}:return False,"NON_COMMON_CLASS_REQUIRES_EXACT_TITLE",x[0]
 if x[1:]!=y[1:]:return False,"CLASS_OR_SERIES_TOKEN_MISMATCH",x[0]
 return True,"CONTROLLED_SAME_INSTRUMENT_CLASS",x[0]
def val(root,path):
 e=root.find(path)
 if e is None:return ""
 v=e.find("value");return (v.text or "").strip() if v is not None else (e.text or "").strip()
def raw_meta(b):
 m=re.search(r"<XML>\s*(.*?)\s*</XML>",b.decode("utf-8","replace"),re.I|re.S)
 if not m:raise ValueError("missing ownership XML")
 r=ET.fromstring(m.group(1)); owners=[]
 for o in r.findall("reportingOwner"):
  rel=o.find("reportingOwnerRelationship")
  def rv(k):
   e=rel.find(k) if rel is not None else None;return (e.text or "").strip() if e is not None else ""
  owners.append({"name":val(o,"reportingOwnerId/rptOwnerName"),"director":rv("isDirector"),"officer":rv("isOfficer"),"title":rv("officerTitle")})
 fns={e.attrib.get("id",""):" ".join("".join(e.itertext()).split()) for e in r.findall("footnotes/footnote")}; rows={}
 for table,k,node in (("nonDerivativeTable","NON_DERIVATIVE","nonDerivativeTransaction"),("derivativeTable","DERIVATIVE","derivativeTransaction")):
  p=r.find(table)
  if p is None:continue
  for i,e in enumerate(p.findall(node),1):
   ids=[x.attrib.get("id","") for x in e.findall(".//footnoteId")]
   rows[(k,i)]={"title":val(e,"securityTitle"),"date":val(e,"transactionDate"),"code":val(e,"transactionCoding/transactionCode"),"direct":val(e,"ownershipNature/directOrIndirectOwnership"),"nature":val(e,"ownershipNature/natureOfOwnership"),"footnotes":[fns.get(x,"") for x in ids if x]}
 return {"cik":val(r,"issuer/issuerCik").lstrip("0"),"symbol":val(r,"issuer/issuerTradingSymbol"),"aff":val(r,"aff10b5One"),"owners":owners,"rows":rows}
def csvout(path,rows):
 if not rows:path.write_text("");return
 fields=list(dict.fromkeys(k for r in rows for k in r))
 with path.open("w",newline="",encoding="utf-8-sig") as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
  for r in rows:w.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v for k,v in r.items()})
def run(p340dir,p339dir,out):
 p=json.loads((p340dir/"phase340_transaction_date_anchor_audit.json").read_text());q=json.loads((p339dir/"phase339_security_exchange_audit.json").read_text())
 if p.get("phase")!=340 or p["summary"].get("accessions_retrieved")!=72 or p["summary"].get("transaction_rows")!=122:raise ValueError("Phase340 contract")
 if q.get("phase")!=339 or q["summary"].get("hash_verified_documents")!=42:raise ValueError("Phase339 contract")
 idx=defaultdict(list)
 for c in q["symbol_exchange_contexts"]:
  if c.get("association_status")=="SYMBOL_12B_TITLE_AND_EXCHANGE_SAME_CONTEXT" and c.get("has_symbol_12b_title_exchange_same_context"):idx[(str(c["issuer_cik"]).lstrip("0"),c["symbol"].strip().upper())].append(c)
 ar=[];meta={}
 for d in p["accessions"]:
  a=d["accession"];b=(p340dir/"raw_submissions"/(a.replace("-","")+".txt")).read_bytes()
  if sha(b)!=d["submission_sha256"]:raise ValueError("raw hash mismatch "+a)
  m=raw_meta(b);cik=str(d["issuer_cik"]).lstrip("0")
  if m["cik"]!=cik:raise ValueError("issuer CIK mismatch "+a)
  tok,st,ex=parse_symbol(m["symbol"]);dt,_,_=parse_symbol(str(d.get("xml_issuer_symbol","")))
  if tok and dt and tok!=dt:raise ValueError("Phase340 symbol mismatch "+a)
  cs=idx.get((cik,tok),[]) if tok else []; titles=sorted({t for x in cs for t in x.get("same_context_security_12b_titles",[])}); exch=sorted({x for z in cs for x in z.get("same_context_exchange_values",[])})
  unique=len(cs)==1 and len(titles)==1
  ar.append({"accession":a,"issuer_cik":cik,"filing_date":d.get("filing_date",""),"selected_filing_date":d.get("selected_filing_date",""),"anchor_age_calendar_days":d.get("anchor_age_calendar_days"),"design_weight":d.get("design_weight",1),"raw_sha256":sha(b),"issuer_symbol_raw":m["symbol"],"symbol_token":tok,"symbol_parse_status":st,"exchange_prefix":ex,"context_count":len(cs),"candidate_xbrl_titles":titles,"exchange_values":exch,"unique_symbol_crosswalk":unique,"aff10b5one":m["aff"],"owner_count":len(m["owners"]),"owners":m["owners"],"acceptance_datetime_et":d.get("acceptance_datetime_et","")})
  meta[a]={**m,"token":tok,"status":st,"contexts":cs,"titles":titles,"exchanges":exch,"unique":unique,"doc":d}
 tr=[]
 for t in p["transactions"]:
  a=t["accession"];m=meta[a];k=t["transaction_kind"];i=int(t.get("transaction_index") or 0);rm=m["rows"].get((k,i),{})
  for f,g in (("security_title","title"),("transaction_date","date"),("transaction_code","code"),("direct_or_indirect","direct")):
   if str(t.get(f,"") or "")!=str(rm.get(g,"") or ""):raise ValueError(f"raw XML mismatch {a} {k} {i} {f}")
  der=k=="DERIVATIVE";field="underlying_security_title" if der else "security_title";title=t.get(field,"");matches=[]
  if m["unique"]:
   for x in m["contexts"][0].get("same_context_security_12b_titles",[]):
    ok,method,ic=match_title(title,x);matches.append((x,ok,method,ic))
  good=[x for x in matches if x[1]];cm=len(good)==1;txanchor=bool(t.get("anchor_predates_transaction"))
  try:prefile=bool(t.get("selected_filing_date") and date.fromisoformat(t["selected_filing_date"])<date.fromisoformat(t["filing_date"]))
  except ValueError:prefile=False
  age=m["doc"].get("anchor_age_calendar_days");fresh=age is not None and 0<int(age)<=365;eventgate=prefile and fresh
  txid=m["unique"] and cm and txanchor and not der;ev=m["unique"] and cm and eventgate and not der;txunder=m["unique"] and cm and txanchor and der;evunder=m["unique"] and cm and eventgate and der
  try:lag=(date.fromisoformat(t["filing_date"])-date.fromisoformat(t["transaction_date"])).days
  except (ValueError,TypeError):lag=None
  foot=rm.get("footnotes",[]);nature=rm.get("nature","");plan=bool(re.search(r"401\s*\(?K\)?|PLAN|TRUST|SUBSIDIARY|WIFE|SPOUSE|CHILD|PRIVATE PLACEMENT|PRIVATE PURCHASE",nature+" "+" ".join(foot),re.I))
  if t.get("transaction_code")!="P":screen="NOT_CODE_P"
  elif not ev:screen="EVENT_TIME_IDENTITY_OR_FRESH_ANCHOR_NOT_ADMITTED"
  elif t.get("direct_or_indirect")!="D":screen="INDIRECT_OWNERSHIP"
  elif len(m["owners"])!=1:screen="OWNER_ATTRIBUTION_AMBIGUOUS"
  elif m["aff"]!="0":screen="10B5_ONE_TRUE_OR_UNKNOWN"
  elif plan:screen="PLAN_TRUST_PRIVATE_OR_RELATED_ACCOUNT"
  else:screen="P_CODE_CANDIDATE_NOT_CONFIRMED_OPEN_MARKET"
  r=dict(t);r.update({"issuer_symbol_raw":m["symbol"],"symbol_token":m["token"],"symbol_parse_status":m["status"],"unique_symbol_crosswalk":m["unique"],"candidate_xbrl_titles":m["titles"],"exchange_values":m["exchanges"],"identity_title_field":field,"identity_title_used":title,"title_match_status":good[0][2] if cm else (matches[0][2] if len(matches)==1 else "NO_UNIQUE_COMPATIBLE_TITLE"),"matched_xbrl_title":good[0][0] if cm else "","instrument_class":good[0][3] if cm else "","anchor_pre_transaction":txanchor,"anchor_pre_filing":prefile,"anchor_fresh_le_365d":fresh,"event_time_anchor_gate":eventgate,"transaction_to_filing_lag_days":lag,"provisional_transaction_date_identity":bool(txid),"provisional_transaction_date_underlying":bool(txunder),"provisional_event_time_identity":bool(ev),"provisional_event_time_underlying":bool(evunder),"aff10b5one":m["aff"],"owner_count":len(m["owners"]),"owner_role":m["owners"][0] if len(m["owners"])==1 else {},"nature_of_ownership":nature,"transaction_footnotes":foot,"purchase_screen_status":screen});tr.append(r)
 mapped=[x for x in ar if x["unique_symbol_crosswalk"]];txid=[x for x in tr if x["provisional_transaction_date_identity"]];ev=[x for x in tr if x["provisional_event_time_identity"]];tu=[x for x in tr if x["provisional_transaction_date_underlying"]];eu=[x for x in tr if x["provisional_event_time_underlying"]];ep=[x for x in ev if x.get("transaction_code")=="P"];ap=[x for x in tr if x.get("transaction_code")=="P"]
 byyear={}
 for x in ar:
  y=x["filing_date"][:4];z=byyear.setdefault(y,{"sample":0,"symbol_crosswalk":0,"event_time_identity":0,"transaction_date_identity":0});z["sample"]+=1;z["symbol_crosswalk"]+=int(x["unique_symbol_crosswalk"]);z["event_time_identity"]+=int(x["accession"] in {r["accession"] for r in ev});z["transaction_date_identity"]+=int(x["accession"] in {r["accession"] for r in txid})
 lags=sorted(x["transaction_to_filing_lag_days"] for x in ev if x["transaction_to_filing_lag_days"] is not None);w=sum(float(x.get("design_weight",1) or 1) for x in ar);mw=sum(float(x.get("design_weight",1) or 1) for x in mapped);ea={x["accession"] for x in ev};ta={x["accession"] for x in txid};ew=sum(float(x.get("design_weight",1) or 1) for x in ar if x["accession"] in ea);tw=sum(float(x.get("design_weight",1) or 1) for x in ar if x["accession"] in ta)
 s={"accessions":72,"raw_submissions_hash_verified":len(ar),"symbol_context_rows":len(q["symbol_exchange_contexts"]),"unique_issuer_symbol_crosswalk_accessions":len(mapped),"single_token_symbols":sum(x["symbol_parse_status"]=="SINGLE_TOKEN" for x in ar),"multi_malformed_symbols":sum(x["symbol_parse_status"] in {"MULTI_OR_MALFORMED","MALFORMED","UNKNOWN_EXCHANGE_PREFIX"} for x in ar),"placeholder_missing_symbols":sum(x["symbol_parse_status"] in {"PLACEHOLDER","MISSING"} for x in ar),"transaction_rows":len(tr),"transaction_date_equity_identity_rows":len(txid),"transaction_date_equity_identity_accessions":len(ta),"transaction_date_derivative_underlying_rows":len(tu),"transaction_date_derivative_underlying_accessions":len({x["accession"] for x in tu}),"event_time_equity_identity_rows":len(ev),"event_time_equity_identity_accessions":len(ea),"event_time_derivative_underlying_rows":len(eu),"event_time_derivative_underlying_accessions":len({x["accession"] for x in eu}),"event_time_codes":dict(sorted(Counter(x.get("transaction_code","") for x in ev).items())),"event_time_title_match_methods":dict(sorted(Counter(x.get("title_match_status","") for x in ev).items())),"event_time_instrument_classes":dict(sorted(Counter(x.get("instrument_class","") for x in ev).items())),"event_time_lag_median_days":lags[len(lags)//2] if lags else None,"event_time_lag_max_days":max(lags) if lags else None,"all_code_p_rows":len(ap),"all_code_p_accessions":len({x["accession"] for x in ap}),"all_code_p_direct_rows":sum(x.get("direct_or_indirect")=="D" for x in ap),"all_code_p_indirect_rows":sum(x.get("direct_or_indirect")=="I" for x in ap),"event_time_code_p_rows":len(ep),"event_time_code_p_accessions":len({x["accession"] for x in ep}),"event_time_code_p_indirect_rows":sum(x.get("direct_or_indirect")=="I" for x in ep),"event_time_code_p_direct_rows":sum(x.get("direct_or_indirect")=="D" for x in ep),"unmapped_direct_code_p_rows":sum(x.get("direct_or_indirect")=="D" for x in ap)-sum(x.get("direct_or_indirect")=="D" for x in ep),"unmapped_code_p_rows":len(ap)-len(ep),"event_time_only_after_transaction_anchor_rows":sum(not x.get("anchor_pre_transaction") for x in ev),"confirmed_discretionary_open_market_purchase_rows":0,"crosswalk_by_year":byyear}
 cov={"symbol_crosswalk_unweighted_pct":100*len(mapped)/72,"symbol_crosswalk_design_weighted_pct":100*mw/w,"event_time_identity_accessions_unweighted_pct":100*len(ea)/72,"event_time_identity_accessions_design_weighted_pct":100*ew/w,"transaction_date_identity_accessions_unweighted_pct":100*len(ta)/72,"transaction_date_identity_accessions_design_weighted_pct":100*tw/w,"event_time_identity_rows_unweighted_pct":100*len(ev)/len(tr)}
 controls={k:False for k in ("strict_pit_admitted","security_master_admitted","transaction_level_security_mapping_admitted","event_study_admitted","alpha_test_run","return_test_run","bootstrap_loo_run","chronological_oos_run","holdout_used","production_changed","universe_changed","capital_changed","parameters_changed","data_purchased","vendor_contacted")};controls["f80_frozen"]=True
 result={"phase":341,"status":"COMPLETED_ISSUER_SYMBOL_CLASS_CROSSWALK_DIAGNOSTIC","sources":{"phase340_artifact_id":13959807159,"phase340_artifact_sha256":"246fc82c5fa6c9fdb6071a58ad5675e7892bbc389fcb5798e3cc2e27f55c78f5","phase340_json_sha256":"d0382a656cdfc8937a4d5749cf4e1281a0a1f642c93b3d73b7f7d4c4f3a1a731","phase339_artifact_id":13959007527,"phase339_artifact_sha256":"186bd582c8cd0ffff73cda16c7331e5a2bd34e413b6aba3715b5fac430a0a66f","phase339_json_sha256":"4560b26f6cb37db8a3cf499207643026aab7e4e309ef8c7cf496b9e02d2d9e15"},"summary":s,"coverage":cov,"accessions":ar,"transactions":tr,"controls":controls,"interpretation":{"issuer_trading_symbol_is_issuer_level_not_transaction_specific":True,"issuer_symbol_is_in_form4_filed_after_transaction_but_available_at_disclosure":True,"event_time_and_transaction_date_identity_are_distinct_gates":True,"event_time_gate_requires_fresh_prior_anchor_before_form4_filing":True,"no_fuzzy_ticker_mapping":True,"common_ordinary_beneficial_interest_preferred_debt_and_ads_kept_separate":True,"class_and_series_tokens_must_match":True,"derivative_underlying_is_separate":True,"code_p_means_open_market_or_private_not_proven_open_market":True,"crosswalk_candidates_are_not_strict_pit_or_effective_dated_security_admission":True}}
 out.mkdir(parents=True,exist_ok=True);(out/"phase341_issuer_symbol_class_crosswalk_audit.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n");csvout(out/"phase341_accession_crosswalk.csv",ar);csvout(out/"phase341_transaction_crosswalk.csv",tr)
 print("PHASE341_STATUS="+result["status"]);print("PHASE341_SUMMARY="+json.dumps(s,sort_keys=True));print("PHASE341_COVERAGE="+json.dumps(cov,sort_keys=True));return result
def main():
 p=argparse.ArgumentParser();p.add_argument("--phase340-dir",type=Path,default=Path("phase340_source"));p.add_argument("--phase339-dir",type=Path,default=Path("phase339_source"));p.add_argument("--output-dir",type=Path,default=Path("phase341_output"));a=p.parse_args();run(a.phase340_dir,a.phase339_dir,a.output_dir)
if __name__=="__main__":main()

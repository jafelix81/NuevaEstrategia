"""Phase 253 normalized SEC registered-security XBRL context and Form 144 join contract."""
import argparse, csv, hashlib, json, re, zipfile
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path

ZIP_SHA = "f84644200a8925c6fc190a823ca0dcd6b40c7bee127a8d2740a5ea67cae56519"
CSV_SHA = "7a54ee09e8d4520e1ec14cf22f2c0d1c62d077798b14d3db596826e3360a3659"
CLASS_AXES = {"statementclassofstockaxis", "classesofsharecapitalaxis"}
LISTING_AXIS = "entitylistingsexchangeaxis"

def norm(x):
    return " ".join(str(x or "").casefold().split())

def companyfacts_can_supply_context(c):
    return not bool(c.get("dimensions") or [])

def _vals(f, k):
    x=f.get(k, [])
    return [] if x is None else [str(v) for v in (x if isinstance(x,list) else [x])]

def validate_context(c):
    f=c.get("facts") or {}; dims=c.get("dimensions") or []
    t12b=_vals(f,"dei:Security12bTitle"); t12g=_vals(f,"dei:Security12gTitle")
    ex=_vals(f,"dei:SecurityExchangeName"); sy=_vals(f,"dei:TradingSymbol")
    no=_vals(f,"dei:NoTradingSymbolFlag")
    def bad(s): return {"status":s,"context_id":c.get("context_id")}
    if len(t12b)>1 or len(t12g)>1: return bad("CONFLICTING_SECURITY_TITLE_FACTS")
    if t12b and t12g: return bad("CONFLICTING_12B_12G_TITLE_TYPES")
    if max(len(ex),len(sy),len(no))>1: return bad("DUPLICATE_CONTEXT_FACT_VALUES")
    if sy and no: return bad("TRADING_SYMBOL_NO_SYMBOL_FLAG_CONFLICT")
    if no and norm(no[0]) not in {"true","1"}: return bad("INVALID_NO_TRADING_SYMBOL_FLAG")
    kind="12B" if t12b else ("12G" if t12g else None)
    title=t12b[0] if t12b else (t12g[0] if t12g else None)
    if not title: return bad("NO_REGISTERED_SECURITY_TITLE_FACTS")
    classes=[]; listings=[]; adr=False; kept=[]
    for d in dims:
        a=str(d.get("axis","")); m=str(d.get("member",""))
        la=a.split(":")[-1].casefold(); lm=m.split(":")[-1].casefold()
        kept.append({"axis":a,"member":m})
        if la in CLASS_AXES: classes.append((a,m))
        if la==LISTING_AXIS: listings.append((a,m))
        adr |= lm=="adrmember"
    if len(classes)>1: return bad("MULTIPLE_CLASS_AXIS_MEMBERS_IN_ONE_CONTEXT")
    if len(listings)>1: return bad("MULTIPLE_LISTING_AXIS_MEMBERS_IN_ONE_CONTEXT")
    if kind=="12B" and not ex and not adr: return bad("MISSING_12B_EXCHANGE_IN_SAME_CONTEXT")
    if sy: ss="HAS_TRADING_SYMBOL"; symbol=sy[0].strip()
    elif no: ss="EXPLICIT_NO_TRADING_SYMBOL"; symbol=None
    else: ss="TRADING_SYMBOL_UNKNOWN"; symbol=None
    if classes: scope="EXACT_CLASS_MEMBER"; ca,cm=classes[0]
    elif not kept: scope="UNDIMENSIONED_REGISTERED_SECURITY"; ca=cm=None
    else: scope="OTHER_DIMENSIONS_PRESERVED_CLASS_SCOPE_UNKNOWN"; ca=cm=None
    la,lm=listings[0] if listings else (None,None)
    return {"status":"VALID_NORMALIZED_CONTEXT","context_id":c.get("context_id"),
            "title_kind":kind,"security_title":title,"symbol":symbol,"symbol_status":ss,
            "exchange":ex[0].strip() if ex else None,"exchange_status":
            "PRESENT_IN_SAME_CONTEXT" if ex else ("ADR_EXCEPTION" if adr else "UNKNOWN"),
            "class_scope":scope,"class_axis":ca,"class_member":cm,
            "listing_axis":la,"listing_member":lm,"dimensions":kept}

def resolve_form144_class(label, contexts):
    target=norm(label)
    xs=[x for x in contexts if x.get("status")=="VALID_NORMALIZED_CONTEXT"
        and x.get("symbol_status")=="HAS_TRADING_SYMBOL" and norm(x.get("security_title"))==target]
    if not xs: return {"status":"NO_EXACT_CLASS_TITLE_MATCH","symbols":[]}
    classes={(x.get("class_axis"),x.get("class_member"),norm(x.get("security_title"))) for x in xs}
    symbols=sorted({x["symbol"] for x in xs if x.get("symbol")})
    if len(classes)>1 or len(symbols)>1:
        return {"status":"AMBIGUOUS_CLASS_OR_SYMBOL","symbols":symbols,"candidate_contexts":len(xs)}
    listings={(x.get("listing_axis"),x.get("listing_member"),x.get("exchange")) for x in xs}
    if len(listings)>1:
        return {"status":"MULTIPLE_LISTINGS_SAME_CLASS","symbols":symbols,
                "listings":[{"axis":a,"member":m,"exchange":e} for a,m,e in sorted(listings,key=str)]}
    return {"status":"UNIQUE_CLASS_LISTING","symbols":symbols,"candidate_contexts":len(xs)}

def select_prior_vintage(filings, event_date):
    try: event=date.fromisoformat(str(event_date)[:10])
    except (TypeError,ValueError): return {"status":"INVALID_EVENT_DATE"}
    eligible=[]
    for f in filings:
        try: d=date.fromisoformat(str(f.get("filing_date"))[:10])
        except (TypeError,ValueError): continue
        if d<event and f.get("accession"): eligible.append((d,f))
    if not eligible: return {"status":"NO_STRICTLY_PRIOR_VINTAGE"}
    latest=max(d for d,_ in eligible); same=[f for d,f in eligible if d==latest]
    if len(same)==1:
        f=same[0]; return {"status":"SELECTED_STRICTLY_PRIOR_VINTAGE","accession":f["accession"],"filing_date":latest.isoformat(),"form":f.get("form")}
    parsed=[]
    for f in same:
        try: t=datetime.fromisoformat(f["acceptance_datetime"].replace("Z","+00:00"))
        except (KeyError,TypeError,ValueError): return {"status":"SAME_DAY_VINTAGE_TIE_UNKNOWN"}
        if t.tzinfo is None: return {"status":"SAME_DAY_VINTAGE_TIE_UNKNOWN"}
        parsed.append((t,f))
    parsed.sort(key=lambda x:x[0])
    if parsed[-1][0]==parsed[-2][0]: return {"status":"SAME_DAY_VINTAGE_TIE_UNKNOWN"}
    f=parsed[-1][1]
    return {"status":"SELECTED_STRICTLY_PRIOR_VINTAGE","accession":f["accession"],"filing_date":latest.isoformat(),"form":f.get("form"),"acceptance_order_used":True}

def audit_phase69(zip_path):
    b=Path(zip_path).read_bytes()
    if hashlib.sha256(b).hexdigest()!=ZIP_SHA: raise ValueError("PHASE69_ARCHIVE_HASH_MISMATCH")
    with zipfile.ZipFile(zip_path) as z:
        raw=z.read("expanded_issuer_event_raw.csv")
        if hashlib.sha256(raw).hexdigest()!=CSV_SHA: raise ValueError("PHASE69_CSV_HASH_MISMATCH")
        rows=list(csv.DictReader(raw.decode("utf-8-sig").splitlines()))
        summary=json.loads(z.read("summary.json"))
    issuers=defaultdict(set); raw_issuers=defaultdict(set); rc=Counter(); nc=Counter(); common=Counter(); explicit=set(); tranches=0
    for r in rows:
        if r.get("form")!="144": continue
        cik=str(r.get("xml_issuer_cik","")).lstrip("0")
        for t in json.loads(r.get("sale_tranches_json") or "[]"):
            tranches+=1; label=" ".join(str(t.get("security_class","")).split())
            if not label: continue
            rc[label]+=1; n=norm(label); nc[n]+=1; issuers[cik].add(n); raw_issuers[cik].add(label)
            if label=="Common": common[cik]+=1
            if re.search(r"\bclass\s+[A-Z]\b",label,re.I): explicit.add(cik)
    rd=Counter(map(len,raw_issuers.values())); nd=Counter(map(len,issuers.values()))
    multi={c for c,v in raw_issuers.items() if len(v)>1}
    return {"phase":253,"status":"FORM144_CLASS_IDENTITY_SOURCE_CONDITIONAL_NO_PIT_NO_ALPHA",
      "source":{"run_id":41959603351,"artifact_id":13385365595,"zip_sha256":ZIP_SHA,"csv_sha256":CSV_SHA,
                "issuer_event_rows":len(rows),"original_144_rows":sum(r.get("form")=="144" for r in rows)},
      "panel":{"issuer_ciks":len(issuers),"current_universe_tickers":summary.get("current_universe_tickers"),
        "sale_tranches":tranches,"distinct_raw_security_class_labels":len(rc),
        "distinct_case_whitespace_normalized_labels":len(nc),
        "issuers_with_multiple_raw_labels":sum(v for k,v in rd.items() if k>1),
        "issuers_with_multiple_normalized_labels":sum(v for k,v in nd.items() if k>1),
        "raw_label_diversity_distribution":{str(k):v for k,v in sorted(rd.items())},
        "normalized_label_diversity_distribution":{str(k):v for k,v in sorted(nd.items())},
        "explicit_class_letter_issuers":len(explicit),"exact_common_label_tranches":rc["Common"],
        "exact_common_tranches_in_multi_raw_label_issuers":sum(common[c] for c in multi),
        "exact_common_tranches_in_explicit_class_issuers":sum(common[c] for c in explicit)},
      "admission":{"raw_ixbrl_parser_validated":False,"cover_page_fallback_validated":False,
        "coverage_across_289_issuers_measured":False,"exact_class_join_measured":False,
        "strict_pit":False,"alpha":False,"returns_tested":False,"holdout_used":False,"f80_frozen":True}}

if __name__=="__main__":
    p=argparse.ArgumentParser(); p.add_argument("--artifact-zip",required=True); p.add_argument("--output",required=True); a=p.parse_args()
    r=audit_phase69(a.artifact_zip); Path(a.output).write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
    print(r["status"],r["panel"]["issuer_ciks"],r["panel"]["sale_tranches"],r["panel"]["distinct_raw_security_class_labels"])

#!/usr/bin/env python3
"""Phase 252: immutable SEC Form 144 panel semantics audit; no returns or alpha."""
import argparse, csv, hashlib, json, re, zipfile
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path

ZIP_SHA = "f84644200a8925c6fc190a823ca0dcd6b40c7bee127a8d2740a5ea67cae56519"
CSV_SHA = "7a54ee09e8d4520e1ec14cf22f2c0d1c62d077798b14d3db596826e3360a3659"
CSV_MEMBER = "expanded_issuer_event_raw.csv"

def d(v):
    if not isinstance(v, str) or not v.strip(): return None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y"):
        try: return datetime.strptime(v.strip(), fmt).date()
        except ValueError: pass
    return None

def dates(v):
    if not isinstance(v, str): return []
    out=[]
    for token in re.findall(r"\b\d{1,2}/\d{1,2}/\d{4}\b|\b\d{4}-\d{2}-\d{2}\b", v):
        x=d(token)
        if x: out.append(x)
    return out

def jlist(v):
    try:
        x=json.loads(v or "[]")
        return x if isinstance(x,list) else []
    except (TypeError,ValueError): return []

def ticker_maps(rows):
    c2t, t2c=defaultdict(set), defaultdict(set)
    for r in rows:
        t=(r.get("ticker") or "").strip().upper()
        for cik in (r.get("ciks") or "").split(";"):
            k=cik.strip().lstrip("0")
            if t and k: c2t[k].add(t); t2c[t].add(k)
    return c2t,t2c

def resolve_issuer_ticker_candidates(xml_issuer_cik, c2t):
    ts=sorted(c2t.get(str(xml_issuer_cik or "").strip().lstrip("0"),set()))
    status="UNIQUE_CURRENT_TICKER" if len(ts)==1 else ("AMBIGUOUS_CURRENT_TICKER_MAP" if ts else "NO_CURRENT_TICKER_MAP")
    return {"status":status,"tickers":ts}

def resolve_zillow_class_ticker(xml_issuer_cik, security_class, filing_date):
    # SEC Form 10-K states Class A=ZG and Class C=Z since 2015-08-17.
    if str(xml_issuer_cik or "").strip().lstrip("0") != "1617640":
        return None
    if not filing_date or filing_date < date(2015, 8, 17):
        return None
    label = " ".join(str(security_class or "").lower().split())
    if "class a" in label: return "ZG"
    if "class c" in label: return "Z"
    return None

def sale_date_relation(filing_date, approximate_sale_date):
    if not filing_date or not approximate_sale_date: return "UNKNOWN"
    if filing_date==approximate_sale_date: return "SAME_DAY"
    return "BEFORE_FILING" if approximate_sale_date<filing_date else "AFTER_FILING"

def proposed_notional_to_adv20(notional, adv20):
    try: n,a=float(notional),float(adv20)
    except (TypeError,ValueError): return None
    return n/a if n>0 and a>0 else None

def audit_rows(rows, ticker_rows, universe_n=335):
    c2t,t2c=ticker_maps(ticker_rows)
    originals=[r for r in rows if r.get("form")=="144"]
    amendments=[r for r in rows if r.get("form")=="144/A"]
    by_acc={r.get("accession"):r for r in originals}
    issuers={str(r.get("xml_issuer_cik","")).lstrip("0") for r in rows if r.get("xml_issuer_cik")}
    plan_all=plan_orig=kw_all=kw_orig=plan_kw_false=plan_kw_false_orig=kw_no_plan=kw_no_plan_orig=0
    plan_tokens=plan_invalid=plan_future=0; plan_lags=[]
    notice_all=notice_orig=0; sale_rel=Counter(); sale_rel_orig=Counter()
    tranches=tranches_orig=units_missing=value_missing=units_zero=value_zero=0
    past_n=past_future=0
    acc_groups=Counter(); tranche_groups=Counter()
    candidate_multi=Counter(); candidate_mismatch=0
    raw_classes=defaultdict(set); zillow_classes=Counter(); zillow_tickers=Counter()
    for r in rows:
        form=r.get("form",""); fd=d(r.get("filing_date"))
        issuer=str(r.get("xml_issuer_cik","")).lstrip("0")
        plan_text=(r.get("plan_adoption_dates") or "").strip()
        has_plan=bool(plan_text); kw=str(r.get("mentions_10b5_1","")).lower()=="true"
        if has_plan:
            plan_all+=1; ds=dates(plan_text); plan_tokens+=len(ds)
            if not ds: plan_invalid+=1
            if fd:
                plan_lags.extend((fd-x).days for x in ds)
                plan_future+=sum((fd-x).days<0 for x in ds)
        if kw: kw_all+=1
        if has_plan and not kw: plan_kw_false+=1
        if kw and not has_plan: kw_no_plan+=1
        if form=="144":
            if has_plan: plan_orig+=1
            if kw: kw_orig+=1
            if has_plan and not kw: plan_kw_false_orig+=1
            if kw and not has_plan: kw_no_plan_orig+=1
            acc_groups[(issuer,(r.get("seller_name") or "").strip().lower(),r.get("filing_date",""))]+=1
        nd=d(r.get("notice_date"))
        if fd and nd and fd!=nd:
            notice_all+=1
            if form=="144": notice_orig+=1
        cand=[x.strip().upper() for x in (r.get("candidate_tickers") or "").split(";") if x.strip()]
        if len(cand)>1: candidate_multi[";".join(cand)]+=1
        for t in cand:
            if t2c.get(t) and issuer not in t2c[t]:
                candidate_mismatch+=1; break
        for tr in jlist(r.get("sale_tranches_json")):
            tranches+=1
            if form=="144":
                tranches_orig+=1
                tranche_groups[(issuer,(r.get("seller_name") or "").strip().lower(),r.get("filing_date",""))]+=1
            sd=d(tr.get("approx_sale_date_iso")) or d(tr.get("approx_sale_date"))
            rel=sale_date_relation(fd,sd)
            sale_rel[rel]+=1
            if form=="144": sale_rel_orig[rel]+=1
            try: u=float(tr.get("units_numeric"))
            except (TypeError,ValueError): u=None
            try: v=float(tr.get("value_numeric"))
            except (TypeError,ValueError): v=None
            units_missing+=u is None; value_missing+=v is None
            units_zero+=u==0 if u is not None else False
            value_zero+=v==0 if v is not None else False
            cl=" ".join(str(tr.get("security_class","")).lower().split())
            if cl: raw_classes[issuer].add(cl)
            if issuer=="1617640":
                zillow_classes[cl or "UNKNOWN"]+=1
                mapped=resolve_zillow_class_ticker(issuer,cl,fd)
                zillow_tickers[mapped or "AMBIGUOUS"]+=1
        for ps in jlist(r.get("past_sales_json")):
            past_n+=1
            pd=d(ps.get("sale_date_iso")) or d(ps.get("sale_date"))
            past_future+=bool(fd and pd and pd>fd)
    linked=same=adds=removes=changes=unmatched=0
    for a in amendments:
        o=by_acc.get((a.get("previous_accession_normalized") or "").strip())
        if not o: unmatched+=1; continue
        linked+=1; old=(o.get("plan_adoption_dates") or "").strip(); new=(a.get("plan_adoption_dates") or "").strip()
        if old==new: same+=1
        elif not old and new: adds+=1
        elif old and not new: removes+=1
        else: changes+=1
    map_counts=Counter(); map_examples={}
    for cik in issuers:
        ts=sorted(c2t.get(cik,set()))
        status="UNIQUE" if len(ts)==1 else ("AMBIGUOUS" if ts else "UNMAPPED")
        map_counts[status]+=1
        if status!="UNIQUE": map_examples[cik]=ts
    return {
      "phase":252,"status":"REAL_ARTIFACT_SEMANTICS_AUDIT_PASS_NO_PIT_NO_ALPHA",
      "panel":{"rows":len(rows),"unique_accessions":len({r.get("accession") for r in rows}),
        "date_min":min(d(r.get("filing_date")) for r in rows if d(r.get("filing_date"))).isoformat(),
        "date_max":max(d(r.get("filing_date")) for r in rows if d(r.get("filing_date"))).isoformat(),
        "original_144":len(originals),"144a":len(amendments),"issuer_ciks_with_events":len(issuers),
        "current_universe_tickers":universe_n,"issuer_cik_current_ticker_map":{"unique":map_counts["UNIQUE"],
        "ambiguous":map_counts["AMBIGUOUS"],"unmapped":map_counts["UNMAPPED"],"examples":map_examples,
        "effective_dated":False},"candidate_ticker_multi_rows":sum(candidate_multi.values()),
        "candidate_ticker_combinations":dict(candidate_multi),"candidate_ticker_cross_cik_mismatch_rows":candidate_mismatch,
        "raw_security_class_strings":len({x for s in raw_classes.values() for x in s}),
        "issuers_with_multiple_raw_class_strings":sum(len(s)>1 for s in raw_classes.values()),
        "zillow_effective_dated_class_crosswalk":{"issuer_cik":"0001617640","valid_from":"2015-08-17",
          "source":"SEC 10-K: Class A=ZG; Class C=Z","tranches_by_raw_class":dict(zillow_classes),
          "tranches_mapped_by_ticker":dict(zillow_tickers),"ambiguous_tranches":zillow_tickers["AMBIGUOUS"]}},
      "plan_dates":{"all_forms_present":plan_all,"original_144_present":plan_orig,
        "keyword_true_all":kw_all,"keyword_true_original_144":kw_orig,
        "plan_present_keyword_false_all":plan_kw_false,"plan_present_keyword_false_original":plan_kw_false_orig,
        "keyword_true_without_plan_all":kw_no_plan,"keyword_true_without_plan_original":kw_no_plan_orig,
        "date_tokens":plan_tokens,"nonempty_unparseable":plan_invalid,
        "median_days_before_filing":sorted(plan_lags)[len(plan_lags)//2] if plan_lags else None,
        "future_to_filing":plan_future},
      "amendments":{"linked_to_original":linked,"unmatched_previous_accession":unmatched,
        "same_plan_date_text":same,"added_plan_date":adds,"removed_plan_date":removes,"changed_plan_date":changes},
      "dates":{"notice_mismatch_all":notice_all,"notice_mismatch_original":notice_orig,
        "sale_tranches_all":tranches,"sale_tranches_original":tranches_orig,
        "approx_sale_date_all":dict(sale_rel),"approx_sale_date_original":dict(sale_rel_orig),
        "past_sales_rows":past_n,"past_sales_after_filing":past_future},
      "proposed_notional":{"missing_units":units_missing,"zero_units":units_zero,
        "missing_aggregate_market_value":value_missing,"zero_aggregate_market_value":value_zero,
        "candidate":"sum(aggregate_market_value) / trailing 20-session average daily dollar volume",
        "meaning":"proposed notional in ADV-days; not float pressure or completed sales","computed":False},
      "repeats":{"original_accessions_beyond_first_in_issuer_seller_day_groups":sum(n-1 for n in acc_groups.values() if n>1),
        "original_tranches_beyond_first_in_issuer_seller_day_groups":sum(n-1 for n in tranche_groups.values() if n>1)},
      "admission":{"pre_2023_04_13_history_complete":False,"absence_is_zero":False,
        "strict_pit":False,"alpha":False,"returns_tested":False,"bootstrap_loo_oos":False,
        "holdout_used":False,"f80_frozen":True,"production_universe_capital_changed":False}
    }

def audit_archive(path):
    raw=Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=ZIP_SHA: raise ValueError("ARCHIVE_HASH_MISMATCH")
    with zipfile.ZipFile(path) as z:
        csv_bytes=z.read(CSV_MEMBER)
        if hashlib.sha256(csv_bytes).hexdigest()!=CSV_SHA: raise ValueError("CSV_HASH_MISMATCH")
        rows=list(csv.DictReader(csv_bytes.decode("utf-8-sig").splitlines()))
        tickers=list(csv.DictReader(z.read("ticker_mapping.csv").decode("utf-8-sig").splitlines()))
        summary=json.loads(z.read("summary.json"))
    if len(rows)!=21634 or summary.get("expanded_issuer_event_rows")!=21634 or summary.get("current_universe_tickers")!=335:
        raise ValueError("PANEL_CONTRACT_MISMATCH")
    result=audit_rows(rows,tickers,335)
    result["source"]={"run_id":41959603351,"artifact_id":13385365595,"zip_sha256":ZIP_SHA,
      "csv_sha256":CSV_SHA,"csv_rows":len(rows),"ticker_mapping_rows":len(tickers),"source_status":summary.get("status")}
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--artifact-zip",required=True); p.add_argument("--output",required=True)
    a=p.parse_args(); result=audit_archive(a.artifact_zip)
    Path(a.output).write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"phase":252,"status":result["status"],"rows":result["panel"]["rows"],
      "originals":result["panel"]["original_144"],"amendments":result["panel"]["144a"],
      "plan_date_keyword_non_equivalence":result["plan_dates"]["plan_present_keyword_false_all"],
      "amendment_plan_date_changes":result["amendments"]["added_plan_date"]+result["amendments"]["removed_plan_date"]+result["amendments"]["changed_plan_date"],
      "zillow_mapped_tranches":result["panel"]["zillow_effective_dated_class_crosswalk"]["tranches_mapped_by_ticker"],
      "zillow_ambiguous_tranches":result["panel"]["zillow_effective_dated_class_crosswalk"]["ambiguous_tranches"],
      "strict_pit":False,"alpha":False},sort_keys=True))

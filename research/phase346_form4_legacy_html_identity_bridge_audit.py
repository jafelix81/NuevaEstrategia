#!/usr/bin/env python3
"""Phase 346: fail-closed legacy SEC HTML bridge audit for Form 4 identity."""
from __future__ import annotations
import argparse, csv, hashlib, html, json, re
from collections import Counter, defaultdict
from datetime import date
from html.parser import HTMLParser
from pathlib import Path

PERIODS = ("2006Q1", "2012Q1")
EXPECTED_ROWS = {"2006Q1": 10, "2012Q1": 102}
EXCHANGES = ("NASDAQ National Market", "NASDAQ Capital Market", "NASDAQ",
             "New York Stock Exchange", "NYSE", "Toronto Stock Exchange",
             "American Stock Exchange", "NYSE American", "OTC Bulletin Board",
             "OTC Markets", "OTC Pink", "OTCQB", "OTCQX")

def clean(s):
    return re.sub(r"\s+", " ", str(s).replace("\xa0", " ")).strip()

def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", html.unescape(str(s)).replace("\xa0", " ").lower()).strip()

def family(value):
    s = norm(value)
    if not s or s in {"none", "n a", "not applicable"}: return ""
    q = ""
    m = re.search(r"\bseries\s+([a-z0-9]+)\b", s)
    if m: q = "SERIES_" + m.group(1).upper() + "_"
    else:
        m = re.search(r"\bclass\s+([a-z0-9]+)\b", s)
        if m: q = "CLASS_" + m.group(1).upper() + "_"
    if "depositary share" in s or "depositary receipt" in s or re.search(r"\bads\b", s): base = "DEPOSITARY"
    elif "preferred" in s: base = "PREFERRED"
    elif "warrant" in s: base = "WARRANT"
    elif "unit" in s: base = "UNIT"
    elif any(x in s for x in ("note", "debenture", "bond")): base = "DEBT"
    elif "common stock" in s: base = "COMMON_STOCK"
    elif "common share" in s: base = "COMMON_SHARES"
    elif "ordinary share" in s or "ordinary stock" in s: base = "ORDINARY_SHARES"
    else: return "OTHER:" + re.sub(r"\s+", "_", s[:80]).upper()
    return q + base

class Parser(HTMLParser):
    BLOCK = {"p","div","br","li","tr","td","th","h1","h2","h3","h4","section","article","hr"}
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.text=[]; self.tables=[]; self.stack=[]; self.ignore=0
    def handle_starttag(self, tag, attrs):
        t=tag.lower()
        if t in {"script","style","noscript"}: self.ignore += 1
        if self.ignore: return
        if t in self.BLOCK: self.text.append(" ")
        if t=="table": self.stack.append({"rows":[],"row":None,"cell":None})
        elif self.stack and t=="tr":
            c=self.stack[-1]
            if c["row"] is not None: c["rows"].append(c["row"])
            c["row"]=[]
        elif self.stack and t in {"td","th"}: self.stack[-1]["cell"]=[]
        elif self.stack and t=="br" and self.stack[-1]["cell"] is not None: self.stack[-1]["cell"].append(" ")
    def handle_endtag(self, tag):
        t=tag.lower()
        if t in {"script","style","noscript"} and self.ignore:
            self.ignore-=1; return
        if self.ignore: return
        if self.stack and t in {"td","th"}:
            c=self.stack[-1]
            if c["cell"] is not None and c["row"] is not None:
                c["row"].append(clean("".join(c["cell"]))); c["cell"]=None
        elif self.stack and t=="tr":
            c=self.stack[-1]
            if c["row"] is not None: c["rows"].append(c["row"]); c["row"]=None
        elif t=="table" and self.stack:
            c=self.stack.pop()
            if c["row"] is not None: c["rows"].append(c["row"])
            self.tables.append(c["rows"])
        if t in self.BLOCK: self.text.append(" ")
    def handle_data(self, data):
        if self.ignore: return
        self.text.append(data)
        if self.stack and self.stack[-1]["cell"] is not None: self.stack[-1]["cell"].append(data)

def class_exchange_rows(tables):
    out=[]
    for ti, table in enumerate(tables):
        for ri, row in enumerate(table):
            cells=[norm(x) for x in row]
            tii=next((i for i,x in enumerate(cells) if "title of each class" in x or x=="title of class"),None)
            eii=next((i for i,x in enumerate(cells) if ("name of each exchange" in x or "name of exchange" in x) and "registered" in x),None)
            if tii is None or eii is None: continue
            vals=table[ri+1] if ri+1<len(table) else []
            title=vals[tii] if tii<len(vals) else ""
            exchange=vals[eii] if eii<len(vals) else ""
            out.append({"table_index":ti,"header_row":ri,"title":title,"exchange":exchange,
                        "class_family":family(title),"raw_header":row,"raw_value_row":vals})
    return out

def section_text(text, letter):
    p=rf"securities registered pursuant to section 12\s*\({letter}\)[^:]*:\s*(.*?)"
    ends=r"securities registered pursuant to section 12\s*\([bg]\)|indicate by check ?mark|applicable only to|$"
    m=re.search(p+r"(?="+ends+r")",text,re.I)
    return clean(m.group(1))[:500] if m else ""

def ticker_mentions(text):
    pats=(r"\b(?:new\s+)?(?:ticker|trading)\s+symbol(?:\s+of)?\s+(?:is\s+)?[\"'“‘]?([A-Z][A-Z0-9.\-]{0,9})",
          r"\bunder\s+the\s+symbol\s+[\"'“‘]?([A-Z][A-Z0-9.\-]{0,9})")
    found={}
    for pat in pats:
        for m in re.finditer(pat,text,re.I):
            sym=m.group(1).upper().rstrip(".,;:)")
            if not sym or sym in {"THE","OUR","AND","FOR","ON"}: continue
            sn=clean(text[max(0,m.start()-220):min(len(text),m.end()+100)])
            ok=re.search(r"\bour\s+(?:(?:common|ordinary)\s+)?(?:stock|shares)\b|\bour\s+(?:new\s+)?(?:ticker|trading)\s+symbol\b|\b(?:corporation|company|inc\.?|issuer)\s+trades\s+on\b",sn,re.I)
            if ok: found[(sym,sn)]={"symbol":sym,"snippet":sn}
    return list(found.values())

def exchange_prose(text):
    out={}
    stock=re.compile(r"\b(?:common|ordinary)\s+(?:stock|shares)\b",re.I)
    direct=re.compile(r"\b(?:traded|trades|listed|reported|as reported|closing sale price|closing price|market price|principal established foreign public trading market)\b",re.I)
    conditional=re.compile(r"\b(?:if|would|could|may|might|likely|potentially|delisted|delisting|hypothetical)\b",re.I)
    for term in EXCHANGES:
        for m in re.finditer(re.escape(term),text,re.I):
            left=max(text.rfind(".",max(0,m.start()-500),m.start()),text.rfind(";",max(0,m.start()-500),m.start()))
            rs=[x for x in (text.find(".",m.end(),min(len(text),m.end()+500)),text.find(";",m.end(),min(len(text),m.end()+500))) if x>=0]
            right=min(rs) if rs else min(len(text),m.end()+500)
            sentence=clean(text[left+1:right])
            if stock.search(sentence) and direct.search(sentence) and not conditional.search(sentence):
                sn=clean(text[max(0,m.start()-220):min(len(text),m.end()+220)])
                out[(term.upper(),sn)]={"exchange_term":term,"snippet":sn}
    return list(out.values())

def parse_doc(raw):
    p=Parser(); p.feed(raw.decode("utf-8","replace"))
    text=clean("".join(p.text))
    return {"text":text,"class_exchange_rows":class_exchange_rows(p.tables),
            "ticker_mentions":ticker_mentions(text),"exchange_prose":exchange_prose(text),
            "section12b_text":section_text(text,"b"),"section12g_text":section_text(text,"g")}

def accession_url(url):
    m=re.search(r"/([0-9]{18})/[^/]+$",url or "")
    if not m: return None
    d=m.group(1); return d[:10]+"-"+d[10:12]+"-"+d[12:]

def parse_date(s):
    try: return date.fromisoformat(str(s)[:10])
    except (TypeError,ValueError): return None

def temporal(row):
    a=parse_date(row.get("anchor_filing_date","")); t=parse_date(row.get("transaction_date",""))
    if not row.get("anchor_accession") or not a: return "NO_ANCHOR",False
    if not t: return "TRANSACTION_DATE_UNPARSEABLE",False
    age=(t-a).days
    if age<0: return "ANCHOR_AFTER_TRANSACTION",False
    if age==0: return "ANCHOR_SAME_DAY_AS_TRANSACTION",False
    if age>365: return "ANCHOR_STALE_OVER_365D",False
    return "PRETRANSACTION_FRESH_ANCHOR",True

def classify(group, parsed):
    syms=sorted(group["symbols"]); titles=sorted(group["titles"])
    fams=sorted({family(x) for x in titles if family(x)})
    mentions=parsed["ticker_mentions"]; mentioned=sorted({x["symbol"] for x in mentions})
    exact=sorted(set(syms)&set(mentioned)); mismatch=sorted(set(mentioned)-set(syms))
    compatible=[x for x in parsed["class_exchange_rows"] if x["class_family"] and x["class_family"] in fams]
    usable=[x for x in compatible if x["exchange"].strip() and norm(x["exchange"]) not in {"none","n a","not applicable"}]
    if len(usable)==1 and len(fams)==1: table_status="UNIQUE_CLASS_FAMILY_EXCHANGE_ROW"
    elif len(usable)>1: table_status="MULTIPLE_COMPATIBLE_CLASS_EXCHANGE_ROWS"
    elif parsed["class_exchange_rows"]: table_status="CLASS_EXCHANGE_TABLE_PRESENT_BUT_NO_USABLE_MATCH"
    else: table_status="NO_SAME_ROW_CLASS_EXCHANGE_TABLE"
    s12=family(parsed["section12g_text"]); s12match=bool(s12 and s12 in fams)
    ex=sorted({x["exchange_term"] for x in parsed["exchange_prose"]})
    if len(exact)==1 and len(syms)==1:
        grade=("TICKER_CLASS_AND_EXCHANGE_CORROBORATED" if table_status=="UNIQUE_CLASS_FAMILY_EXCHANGE_ROW"
               else "TICKER_AND_SECTION12G_CLASS_CORROBORATED" if s12match
               else "TICKER_AND_EXCHANGE_PROSE_CORROBORATED" if ex else "TICKER_PROSE_ONLY")
    elif mentioned and not exact: grade="ISSUER_TICKER_MISMATCH"
    elif table_status=="UNIQUE_CLASS_FAMILY_EXCHANGE_ROW": grade="CLASS_EXCHANGE_ROW_TICKER_NOT_DIRECTLY_LINKED"
    elif ex: grade="EXCHANGE_PROSE_ONLY"
    elif s12match: grade="SECTION12G_CLASS_ONLY"
    else: grade="NO_DIRECT_LEGACY_BRIDGE"
    return {"form4_symbols":syms,"form4_security_titles":titles,"form4_class_families":fams,
            "ticker_mentions":mentions,"ticker_mention_symbols":mentioned,"ticker_exact_matches":exact,
            "ticker_mismatches":mismatch,"class_exchange_rows":parsed["class_exchange_rows"],
            "class_exchange_match_rows":compatible,"class_exchange_table_status":table_status,
            "section12b_text":parsed["section12b_text"],"section12g_text":parsed["section12g_text"],
            "section12g_class_match":s12match,"exchange_prose":parsed["exchange_prose"],
            "exchange_prose_terms":ex,"evidence_grade":grade}

def write_csv(path, rows):
    if not rows: path.write_text("",encoding="utf-8"); return
    fields=list(dict.fromkeys(k for r in rows for k in r))
    with path.open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore"); w.writeheader()
        for r in rows:
            w.writerow({k:json.dumps(v,ensure_ascii=False,sort_keys=True) if isinstance(v,(dict,list)) else v for k,v in r.items()})

def run(input_dir:Path, output_dir:Path):
    summary_path=input_dir/"phase345_output"/"phase345_multiquarter_identity_summary.json"
    if not summary_path.is_file(): raise FileNotFoundError("phase345_summary_missing")
    summary=json.loads(summary_path.read_text(encoding="utf-8"))
    if summary.get("phase")!=345 or summary.get("status")!="COMPLETED_MULTIQUARTER_FORM4_IDENTITY_AUDIT":
        raise ValueError("phase345_artifact_contract_invalid")
    output_dir.mkdir(parents=True,exist_ok=True)
    anchors=[]; candidates=[]; period_summaries=[]
    for period in PERIODS:
        base=input_dir/"phase345_output"/period/"identity_audit"
        rows_path=base/f"phase345_{period}_candidate_rows.csv"
        manifest_path=base/"sec_response_manifest.json"
        if not rows_path.is_file() or not manifest_path.is_file(): raise FileNotFoundError(f"phase345_period_input_missing:{period}")
        with rows_path.open("r",encoding="utf-8-sig",newline="") as f: rows=list(csv.DictReader(f))
        if len(rows)!=EXPECTED_ROWS[period]: raise ValueError(f"candidate_row_count_mismatch:{period}:{len(rows)}")
        manifest=json.loads(manifest_path.read_text(encoding="utf-8"))
        mmap=defaultdict(list)
        for item in manifest:
            acc=accession_url(item.get("url",""))
            if acc and item.get("artifact_file"): mmap[acc].append(item)
        groups={}
        for r in rows:
            a=r.get("anchor_accession","").strip()
            if not a: continue
            digits=re.sub(r"\D","",a); acc=digits[:10]+"-"+digits[10:12]+"-"+digits[12:]
            key=(r.get("issuer_cik",""),acc)
            g=groups.setdefault(key,{"period":period,"issuer_cik":r.get("issuer_cik",""),"anchor_accession":acc,
                "anchor_form":r.get("anchor_form",""),"anchor_filing_date":r.get("anchor_filing_date",""),
                "sha":r.get("anchor_document_sha256",""),"symbols":set(),"titles":set(),"form4_accessions":set(),"rows":[]})
            if r.get("form4_symbol_token"): g["symbols"].add(r["form4_symbol_token"].strip().upper())
            if r.get("security_title"): g["titles"].add(r["security_title"].strip())
            g["form4_accessions"].add(r.get("accession","")); g["rows"].append(r)
        anchored={id(r) for g in groups.values() for r in g["rows"]}
        for r in rows:
            if id(r) in anchored: continue
            candidates.append({"period":period,"issuer_cik":r.get("issuer_cik",""),"form4_accession":r.get("accession",""),
                "form4_filing_date":r.get("filing_date",""),"transaction_date":r.get("transaction_date",""),
                "form4_symbol":r.get("form4_symbol_token",""),"form4_security_title":r.get("security_title",""),
                "anchor_accession":"","anchor_form":"","anchor_filing_date":"","anchor_sha256":"",
                "temporal_status":"NO_ANCHOR","pit_eligible_at_transaction":False,"ticker_mentions":[],
                "ticker_exact_match":False,"ticker_mismatch_symbols":[],"class_exchange_rows":[],
                "class_exchange_table_status":"NOT_TESTED_NO_ANCHOR","section12g_text":"",
                "section12g_class_match":False,"exchange_prose_terms":[],"row_evidence_grade":"NO_ANCHOR"})
        for g in groups.values():
            items=[x for x in mmap.get(g["anchor_accession"],[]) if int(x.get("http_status",0))==200
                   and x.get("sha256")==g["sha"] and x.get("artifact_file")]
            if len(items)!=1: raise ValueError(f"anchor_manifest_hash_match_count_not_one:{period}:{g['anchor_accession']}:{len(items)}")
            item=items[0]; raw_path=base/item["artifact_file"]
            if not raw_path.is_file(): raise FileNotFoundError(f"anchor_raw_file_missing:{period}:{item['artifact_file']}")
            raw=raw_path.read_bytes(); digest=hashlib.sha256(raw).hexdigest()
            if digest!=g["sha"]: raise ValueError(f"anchor_raw_sha256_mismatch:{period}:{g['anchor_accession']}")
            ev=classify(g,parse_doc(raw)); pitrows=0; tc=Counter()
            for r in g["rows"]:
                ts,pit=temporal(r); tc[ts]+=1; pitrows+=int(pit)
                sym=r.get("form4_symbol_token","").strip().upper()
                exact=bool(sym and sym in ev["ticker_mention_symbols"])
                mismatch=sorted(set(ev["ticker_mention_symbols"])-({sym} if sym else set()))
                grade=ts if not pit else ev["evidence_grade"]
                if pit and ev["evidence_grade"]=="ISSUER_TICKER_MISMATCH": grade="QUARANTINE_ISSUER_TICKER_MISMATCH"
                elif pit and exact and ev["class_exchange_table_status"]=="UNIQUE_CLASS_FAMILY_EXCHANGE_ROW": grade="PIT_TICKER_CLASS_EXCHANGE_CONFIRMED"
                elif pit and exact and ev["section12g_class_match"]: grade="PIT_TICKER_AND_SECTION12G_CLASS_CONFIRMED"
                elif pit and exact and ev["exchange_prose_terms"]: grade="PIT_TICKER_AND_EXCHANGE_PROSE_CONFIRMED"
                elif pit and exact: grade="PIT_TICKER_PROSE_ONLY"
                candidates.append({"period":period,"issuer_cik":g["issuer_cik"],"form4_accession":r.get("accession",""),
                    "form4_filing_date":r.get("filing_date",""),"transaction_date":r.get("transaction_date",""),
                    "form4_symbol":sym,"form4_security_title":r.get("security_title",""),"anchor_accession":g["anchor_accession"],
                    "anchor_form":g["anchor_form"],"anchor_filing_date":g["anchor_filing_date"],"anchor_sha256":digest,
                    "temporal_status":ts,"pit_eligible_at_transaction":pit,"ticker_mentions":ev["ticker_mentions"],
                    "ticker_exact_match":exact,"ticker_mismatch_symbols":mismatch,"class_exchange_rows":ev["class_exchange_rows"],
                    "class_exchange_table_status":ev["class_exchange_table_status"],"section12g_text":ev["section12g_text"],
                    "section12g_class_match":ev["section12g_class_match"],"exchange_prose_terms":ev["exchange_prose_terms"],
                    "row_evidence_grade":grade})
            anchors.append({"period":period,"issuer_cik":g["issuer_cik"],"anchor_accession":g["anchor_accession"],
                "anchor_form":g["anchor_form"],"anchor_filing_date":g["anchor_filing_date"],"anchor_sha256":digest,
                "manifest_url":item.get("url",""),"manifest_http_status":item.get("http_status",0),
                "raw_document_bytes":len(raw),"form4_accessions":sorted(g["form4_accessions"]),
                "candidate_rows":len(g["rows"]),"pit_eligible_candidate_rows":pitrows,
                "temporal_status_counts":dict(tc),**ev})
        pr=[x for x in candidates if x["period"]==period]; ar=[x for x in anchors if x["period"]==period]
        period_summaries.append({"period":period,"candidate_rows":len(rows),"selected_anchor_groups":len(groups),
            "raw_anchor_documents_hash_verified":len(ar),"pretransaction_fresh_candidate_rows":sum(x["pit_eligible_at_transaction"] for x in pr),
            "post_or_same_day_candidate_rows":sum(x["temporal_status"] in {"ANCHOR_AFTER_TRANSACTION","ANCHOR_SAME_DAY_AS_TRANSACTION"} for x in pr),
            "stale_candidate_rows":sum(x["temporal_status"]=="ANCHOR_STALE_OVER_365D" for x in pr),
            "no_anchor_candidate_rows":sum(x["temporal_status"]=="NO_ANCHOR" for x in pr),
            "rows_with_exact_ticker_prose_match":sum(x["ticker_exact_match"] for x in pr if x["pit_eligible_at_transaction"]),
            "rows_quarantined_ticker_mismatch":sum(x["row_evidence_grade"]=="QUARANTINE_ISSUER_TICKER_MISMATCH" for x in pr),
            "anchor_groups_with_same_row_class_exchange_table":sum(x["class_exchange_table_status"]=="UNIQUE_CLASS_FAMILY_EXCHANGE_ROW" for x in ar),
            "anchor_groups_with_usable_same_row_class_exchange_and_pit":sum(x["pit_eligible_candidate_rows"]>0 and x["class_exchange_table_status"]=="UNIQUE_CLASS_FAMILY_EXCHANGE_ROW" for x in ar),
            "evidence_grade_anchor_counts":dict(sorted(Counter(x["evidence_grade"] for x in ar).items()))})
    totals={k:sum(x[k] for x in period_summaries) for k in (
        "candidate_rows","selected_anchor_groups","raw_anchor_documents_hash_verified","pretransaction_fresh_candidate_rows",
        "rows_with_exact_ticker_prose_match","rows_quarantined_ticker_mismatch",
        "anchor_groups_with_same_row_class_exchange_table","anchor_groups_with_usable_same_row_class_exchange_and_pit")}
    result={"phase":346,"status":"COMPLETED_LEGACY_FORM4_HTML_IDENTITY_BRIDGE_AUDIT","source_phase":345,
        "source_periods":list(PERIODS),"periods":period_summaries,"totals":totals,
        "anchor_results":anchors,"candidate_results":candidates,
        "controls":{"phase345_raw_source_hashes_verified":True,"no_sec_refetch":True,"no_fuzzy_ticker_inference":True,
            "no_exchange_inference_from_missing_fields":True,"same_day_and_post_transaction_anchors_excluded":True,
            "stale_anchors_over_365d_excluded":True,"no_returns_or_alpha_test":True,"no_bootstrap_or_loo":True,
            "no_oos_or_holdout_access":True,"f80_frozen":True,"production_changed":False,"universe_changed":False,
            "capital_changed":False,"parameters_changed":False,"data_purchased":False,"vendor_contacted":False},
        "decision":{"universal_legacy_html_bridge_admitted":False,
            "reason":"Legacy HTML evidence is heterogeneous; exact class/exchange rows and issuer-specific ticker prose cover only a subset, and one pre-event ticker mismatch was found. Keep evidence grades separate and require effective-dated security-master corroboration.",
            "insider_event_study_authorized":False}}
    (output_dir/"phase346_legacy_html_identity_bridge_audit.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    write_csv(output_dir/"phase346_anchor_evidence.csv",anchors)
    write_csv(output_dir/"phase346_candidate_evidence.csv",candidates)
    print("PHASE346_STATUS="+result["status"])
    print("PHASE346_TOTALS="+json.dumps(totals,sort_keys=True))
    for x in period_summaries: print("PHASE346_PERIOD="+json.dumps(x,sort_keys=True))
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input-dir",type=Path,required=True); p.add_argument("--output-dir",type=Path,required=True)
    a=p.parse_args(); run(a.input_dir,a.output_dir)
if __name__=="__main__": main()

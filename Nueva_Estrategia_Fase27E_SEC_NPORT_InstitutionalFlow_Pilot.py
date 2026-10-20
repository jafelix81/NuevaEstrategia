import ast, csv, io, json, os, re, tempfile, zipfile
from collections import defaultdict
from datetime import datetime, timezone
from urllib.request import Request, urlopen

BASE_SOURCE = "Nueva_Estrategia_Fase0_Descubrimiento.py"
OUT = "nueva_estrategia_phase27e_sec_nport"
os.makedirs(OUT, exist_ok=True)
HEADERS = {"User-Agent": "NuevaEstrategia research research@example.com", "Accept-Encoding": "gzip, deflate"}
DATASETS = {
    "2021Q4": "https://www.sec.gov/files/dera/data/form-n-port-data-sets/2021q4_nport.zip",
    "2022Q4": "https://www.sec.gov/files/dera/data/form-n-port-data-sets/2022q4_nport.zip",
}

def universe():
    tree = ast.parse(open(BASE_SOURCE, encoding="utf-8").read())
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == "DEFAULT_UNIVERSE":
                    u = sorted(set(str(x).strip().upper() for x in ast.literal_eval(node.value)))
                    if len(u) != 335: raise RuntimeError(f"Expected frozen 335 universe, got {len(u)}")
                    return set(u)
    raise RuntimeError("DEFAULT_UNIVERSE not found")
UNIVERSE = universe()

def download(url, path):
    with urlopen(Request(url, headers=HEADERS), timeout=300) as r, open(path, "wb") as f:
        while True:
            b = r.read(1024*1024)
            if not b: break
            f.write(b)

def member(z, stem):
    for n in z.namelist():
        b=os.path.basename(n).lower()
        if b==stem.lower() or b.startswith(stem.lower()+"."): return n
    raise RuntimeError(f"Missing {stem}")

def read_tsv(z, m):
    with z.open(m) as raw:
        return list(csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8-sig", errors="replace", newline=""), delimiter="\t"))

def norm(x): return re.sub(r"[^A-Z0-9.\-]", "", (x or "").strip().upper())

def parse_date(x):
    for fmt in ("%d-%b-%Y", "%Y-%m-%d"):
        try: return datetime.strptime(x, fmt).date()
        except: pass
    return None

def period_snapshot(period):
    path=os.path.join(tempfile.gettempdir(), period+"_nport27e.zip")
    download(DATASETS[period], path)
    try:
        with zipfile.ZipFile(path) as z:
            sub=read_tsv(z, member(z,"SUBMISSION"))
            info=read_tsv(z, member(z,"FUND_REPORTED_INFO"))
            hold=read_tsv(z, member(z,"FUND_REPORTED_HOLDING"))
            ids=read_tsv(z, member(z,"IDENTIFIERS"))
        sub_by={r.get("ACCESSION_NUMBER",""):r for r in sub}
        series_by={r.get("ACCESSION_NUMBER",""):r.get("SERIES_ID","") for r in info}
        report_by={}
        for a,r in sub_by.items():
            d=parse_date(r.get("REPORT_DATE", ""))
            if d: report_by[a]=d
        latest=max(report_by.values())
        # Authoritative filing per series/report date: latest filing date, including amendments.
        candidates=defaultdict(list)
        for a,d in report_by.items():
            if d==latest and series_by.get(a): candidates[series_by[a]].append(a)
        selected={}
        for s, accs in candidates.items():
            selected[s]=max(accs, key=lambda a: parse_date(sub_by[a].get("FILING_DATE", "")) or datetime.min.date())
        selected_acc=set(selected.values())
        ids_by_hold=defaultdict(list)
        for r in ids: ids_by_hold[r.get("HOLDING_ID","")].append(r)
        rows=[]
        filing_dates=[]
        for a in selected_acc:
            fd=parse_date(sub_by[a].get("FILING_DATE", ""))
            if fd: filing_dates.append(fd)
        signal_date=max(filing_dates) if filing_dates else None
        for h in hold:
            a=h.get("ACCESSION_NUMBER","")
            if a not in selected_acc: continue
            ticker=set()
            for i in ids_by_hold.get(h.get("HOLDING_ID",""),[]):
                t=norm(i.get("IDENTIFIER_TICKER"))
                if t in UNIVERSE: ticker.add(t)
            if len(ticker)!=1: continue
            # Restrict to ordinary common equity and long positions; this is a conservative pilot definition.
            title=(h.get("ISSUER_TITLE") or "").upper()
            payoff=(h.get("PAYOFF_PROFILE") or "").upper()
            if "COMMON STOCK" not in title or payoff not in ("", "LONG"): continue
            try: value=float(h.get("CURRENCY_VALUE") or 0.0)
            except: continue
            if value < 0: continue
            rows.append((next(iter(ticker)), series_by[a], value, a, h.get("ISSUER_CUSIP","")))
        # One fund-series/ticker can have multiple CUSIPs; sum them rather than choosing a survivorship-prone bridge.
        agg=defaultdict(float)
        for t,s,v,_,_ in rows: agg[(t,s)]+=v
        by_ticker=defaultdict(float)
        for (t,_),v in agg.items(): by_ticker[t]+=v
        return {"period":period,"report_date":latest.isoformat(),"signal_date":signal_date.isoformat() if signal_date else None,"series_selected":len(selected),"holding_rows_used":len(rows),"ticker_count":len(by_ticker),"by_series_ticker":{f"{t}|{s}":v for (t,s),v in agg.items()},"by_ticker":dict(by_ticker)}
    finally:
        try: os.remove(path)
        except OSError: pass

def compare(prev, cur):
    a=prev["by_series_ticker"]; b=cur["by_series_ticker"]
    keys=set(a)|set(b)
    out=[]
    for k in keys:
        t=k.split("|",1)[0]; pv=a.get(k,0.0); cv=b.get(k,0.0)
        if pv==0 and cv==0: continue
        delta=cv-pv
        out.append({"ticker":t,"series_key":k,"prior_value":pv,"current_value":cv,"delta_value":delta,"pct_change":(delta/pv if pv else None)})
    by=defaultdict(list)
    for r in out: by[r["ticker"]].append(r)
    sig=[]
    for t,rs in by.items():
        prior=sum(r["prior_value"] for r in rs); current=sum(r["current_value"] for r in rs); delta=current-prior
        up=sum(1 for r in rs if r["delta_value"]>0); down=sum(1 for r in rs if r["delta_value"]<0)
        sig.append({"ticker":t,"prior_value":prior,"current_value":current,"delta_value":delta,"pct_change":delta/prior if prior else None,"fund_breadth_net":up-down,"funds_up":up,"funds_down":down,"funds_observed":len(rs)})
    return sorted(sig,key=lambda x:(x["pct_change"] is not None,x["pct_change"] or 0),reverse=True)

def main():
    p1=period_snapshot("2021Q4"); p2=period_snapshot("2022Q4")
    signals=compare(p1,p2)
    payload={"phase":"27E","purpose":"PIT construction pilot for institutional fund position changes; no production change.","knowledge_rule":"Signal date is the latest filing date among authoritative quarter-end reports used; returns, when tested later, must begin strictly after this date.","amendment_rule":"For each series/report period, latest filing date wins; NPORT-P/A therefore replaces prior version.","security_rule":"Frozen 335 universe; ticker only selects universe membership, all CUSIPs for the ticker are aggregated rather than forcing a single historical CUSIP.","holding_rule":"COMMON STOCK only, long/blank payoff profile, nonnegative USD value.","periods":[p1,p2],"signals":signals,"audit_timestamp_utc":datetime.now(timezone.utc).isoformat()}
    with open(os.path.join(OUT,"phase27e_pilot_2021Q4_2022Q4.json"),"w",encoding="utf-8") as f: json.dump(payload,f,indent=2)
    print(json.dumps({"phase":"27E","report_dates":[p1["report_date"],p2["report_date"]],"signal_date":p2["signal_date"],"ticker_count":len(signals),"status":"COMPLETE"},indent=2))
if __name__=="__main__": main()

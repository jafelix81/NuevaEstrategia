#!/usr/bin/env python3
"""Inspect Cboe Option EOD Summary sample for OPRA schema and ticker coverage."""
from __future__ import annotations
import ast,csv,gzip,hashlib,io,json,re,zipfile
from datetime import datetime,timezone
from pathlib import Path
from urllib.error import HTTPError,URLError
from urllib.request import Request,urlopen

BASE_SOURCE="Nueva_Estrategia_Fase0_Descubrimiento.py"
SAMPLE_URL="https://datashop.cboe.com/download/sample/217"
USER_AGENT="Mozilla/5.0 (compatible; NuevaEstrategiaResearch/1.0; jose.felix@felixsarmiento.com)"
OUT_DIR=Path("phase55_cboe_option_eod_summary_feasibility")
BASE_FIELDS=("underlying_symbol","quote_date","root","expiration","strike","option_type","open","high","low","close","trade_volume","bid_size_1545","bid_1545","ask_size_1545","ask_1545","bid_size_eod","bid_eod","ask_size_eod","ask_eod","vwap","open_interest")
CALC_FIELDS=("active_underlying_price_1545","implied_volatility_1545","delta_1545","gamma_1545","theta_1545","vega_1545","rho_1545")

def fetch_bytes(url):
    req=Request(url,headers={"User-Agent":USER_AGENT,"Accept":"application/zip,application/octet-stream,*/*","Accept-Encoding":"gzip, deflate"})
    with urlopen(req,timeout=120) as response:
        raw=response.read()
        if response.headers.get("Content-Encoding","").lower()=="gzip" or raw[:2]==b"\x1f\x8b":
            raw=gzip.decompress(raw)
        return raw,response.status,response.headers.get("Content-Type",""),response.headers.get("Last-Modified","")

def load_universe():
    tree=ast.parse(Path(BASE_SOURCE).read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node,ast.Assign):
            for target in node.targets:
                if isinstance(target,ast.Name) and target.id=="DEFAULT_UNIVERSE":
                    values=sorted({str(v).strip().upper() for v in ast.literal_eval(node.value)})
                    if len(values)!=335:raise RuntimeError("Expected 335 tickers, got {}".format(len(values)))
                    return set(values)
    raise RuntimeError("DEFAULT_UNIVERSE not found")

def norm(value):
    return re.sub(r"[^a-z0-9]","",str(value or "").lower())

def parse_csv(raw):
    text=raw.decode("utf-8-sig","replace")
    lines=[line for line in text.splitlines() if line.strip()]
    if not lines:return {"headers":[],"rows":[],"prefix":text[:300]}
    header_idx=0
    for i,line in enumerate(lines[:20]):
        low=line.lower()
        if "underlying_symbol" in low and "quote_date" in low:
            header_idx=i;break
    sample="\n".join(lines[header_idx:header_idx+10])
    try:dialect=csv.Sniffer().sniff(sample,delimiters=",\t|;")
    except csv.Error:dialect=csv.excel
    reader=csv.DictReader(lines[header_idx:],dialect=dialect)
    return {"headers":reader.fieldnames or [],"rows":[r for r in reader if r and any(v not in (None,"") for v in r.values())],"prefix":"\n".join(lines[:3])[:300]}

def extract_zip_csvs(raw):
    out=[]
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        for name in archive.namelist():
            if name.lower().endswith(".csv"):
                out.append((name,archive.read(name)))
            elif name.lower().endswith(".zip"):
                out.extend((name+"!"+sub,data) for sub,data in extract_zip_csvs(archive.read(name)))
    return out

def field_stats(headers,rows,field):
    lookup={norm(h):h for h in headers}
    actual=lookup.get(norm(field))
    if not actual:return {"present":False,"nonnull_rate":0.0}
    n=sum(1 for row in rows if row.get(actual) not in (None,""))
    return {"present":True,"nonnull_rate":n/len(rows) if rows else 0.0}

def to_num(value):
    try:return float(str(value).replace(",","")) if value not in (None,"") else None
    except ValueError:return None

def inspect_file(name,raw,universe):
    parsed=parse_csv(raw);headers=parsed["headers"];rows=parsed["rows"]
    lookup={norm(h):h for h in headers}
    under_col=lookup.get("underlyingsymbol")
    underlyings=sorted({str(row.get(under_col,"")).strip().upper() for row in rows if under_col and row.get(under_col)})
    targets=sorted(set(underlyings).intersection(universe))
    quote_col=lookup.get("quotedate")
    option_col=lookup.get("optiontype")
    root_col=lookup.get("root")
    expiry_col=lookup.get("expiration")
    iv_col=lookup.get("impliedvolatility1545")
    oi_col=lookup.get("openinterest")
    vol_col=lookup.get("tradevolume")
    call_put=Counter(str(row.get(option_col,"")).strip().upper() for row in rows if option_col)
    expiries=sorted({str(row.get(expiry_col,"")).strip() for row in rows if expiry_col and row.get(expiry_col)})
    roots=sorted({str(row.get(root_col,"")).strip() for row in rows if root_col and row.get(root_col)})
    iv_values=[to_num(row.get(iv_col)) for row in rows if iv_col]
    iv_values=[v for v in iv_values if v is not None]
    oi_values=[to_num(row.get(oi_col)) for row in rows if oi_col]
    oi_values=[v for v in oi_values if v is not None]
    vol_values=[to_num(row.get(vol_col)) for row in rows if vol_col]
    vol_values=[v for v in vol_values if v is not None]
    return {
        "member":name,"file_type":"OPTION_EOD" if quote_col else "UNKNOWN",
        "bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest(),
        "row_count":len(rows),"header_count":len(headers),"headers":headers,
        "quote_dates":sorted({str(row.get(quote_col,"")) for row in rows if quote_col}),
        "unique_underlyings":len(underlyings),"target_ticker_count":len(targets),
        "target_universe_coverage":len(targets)/len(universe),
        "target_tickers_observed":targets,"unique_option_roots":len(roots),
        "unique_expirations":len(expiries),"option_type_counts":dict(call_put),
        "iv_nonnull_rows":len(iv_values),"iv_nonnull_rate":len(iv_values)/len(rows) if rows else 0.0,
        "open_interest_nonnull_rows":len(oi_values),"open_interest_nonnull_rate":len(oi_values)/len(rows) if rows else 0.0,
        "trade_volume_nonnull_rows":len(vol_values),"trade_volume_nonnull_rate":len(vol_values)/len(rows) if rows else 0.0,
        "total_trade_volume_sample":sum(vol_values) if vol_values else None,
        "total_open_interest_sample":sum(oi_values) if oi_values else None,
        "base_field_coverage":{field:field_stats(headers,rows,field) for field in BASE_FIELDS},
        "calc_field_coverage":{field:field_stats(headers,rows,field) for field in CALC_FIELDS},
        "sample_rows":rows[:5],"text_prefix":parsed["prefix"],
    }

def main():
    OUT_DIR.mkdir(parents=True,exist_ok=True)
    universe=load_universe()
    raw,status,content_type,last_modified=fetch_bytes(SAMPLE_URL)
    (OUT_DIR/"option_eod_sample.zip").write_bytes(raw)
    if raw[:2]!=b"PK":raise RuntimeError("Option EOD sample response is not ZIP: {!r}".format(raw[:300]))
    members=extract_zip_csvs(raw)
    files=[inspect_file(name,data,universe) for name,data in members]
    eod=[item for item in files if item["file_type"]=="OPTION_EOD"]
    base_pass=[]
    calc_pass=[]
    for item in eod:
        base_pass.append(item["row_count"]>0 and item["target_universe_coverage"]>=0.70 and all(v["present"] and v["nonnull_rate"]>=0.95 for v in item["base_field_coverage"].values()))
        calc_pass.append(all(v["present"] and v["nonnull_rate"]>=0.95 for v in item["calc_field_coverage"].values()))
    summary={
        "phase":"55_Cboe_Option_EOD_Summary_sample_feasibility",
        "status":"COMPLETE","sample_url":SAMPLE_URL,"http_status":status,
        "content_type":content_type,"last_modified_header":last_modified,
        "zip_bytes":len(raw),"zip_sha256":hashlib.sha256(raw).hexdigest(),
        "zip_members":[name for name,_ in members],"parsed_csv_files":len(files),
        "option_eod_files":len(eod),"frozen_universe_size":len(universe),
        "file_summaries":files,"option_eod_summaries":eod,
        "base_schema_gate":"PASS" if eod and all(base_pass) else "FAIL_OR_PARTIAL",
        "base_schema_gate_by_file":base_pass,
        "calcs_gate":"PASS" if eod and all(calc_pass) else "NOT_IN_SAMPLE_OR_FAIL",
        "calcs_gate_by_file":calc_pass,
        "historical_availability":"Cboe product page states January 2012 to present; sample is not a full historical coverage audit.",
        "pit_delivery":"Daily files; conservative KnowledgeDate should be next trading session unless historical delivery timestamp can be evidenced.",
        "economic_interpretation":"Full OPRA option NBBO/OHLC/volume/OI with optional 15:45 IV and Greeks; no participant capacity, buy/sell or open/close classification. Pair with Open-Close EOD for a complementary hypothesis.",
        "licensing":"Historical/subscription purchase supports all symbols or pick-symbol selection. Exact quote for 335 symbols and Calcs option must be confirmed in DataShop.",
        "forward_returns_used":False,
        "audit_timestamp_utc":datetime.now(timezone.utc).isoformat(),
    }
    (OUT_DIR/"summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    with (OUT_DIR/"sample_rows.json").open("w",encoding="utf-8") as handle:
        json.dump([{"member":item["member"],"sample_rows":item["sample_rows"]} for item in files],handle,indent=2)
    print(json.dumps(summary,indent=2),flush=True)
    if summary["base_schema_gate"]!="PASS":raise RuntimeError("Option EOD base schema gate failed")

if __name__=="__main__":main()

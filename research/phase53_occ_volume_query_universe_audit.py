#!/usr/bin/env python3
"""OCC Volume Query full-expiry, full-universe coverage audit.

The OCC Volume Query reports quantity by underlying, option root, account type,
call/put, exchange and series/contract date. It has no buy/sell aggressor side.
"""
from __future__ import annotations
import ast,csv,gzip,hashlib,json,re,time
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path
from urllib.error import HTTPError,URLError
from urllib.parse import urlencode
from urllib.request import Request,urlopen

BASE_SOURCE="Nueva_Estrategia_Fase0_Descubrimiento.py"
OCC_BASE="https://marketdata.theocc.com"
VOLUME_URL=OCC_BASE+"/volume-query"
USER_AGENT="Mozilla/5.0 (compatible; NuevaEstrategiaResearch/1.0; jose.felix@felixsarmiento.com)"
DATES=("2025-01-03","2026-11-02")
BOUNDARY_DATE="2024-01-03"
BOUNDARY_SYMBOLS=("AAPL","NVDA","TSLA")
OUT_DIR=Path("phase53_occ_volume_query_universe_audit")
REQUIRED=("quantity","underlying","symbol","actype","porc","exchange","actdate","contractdate")

def fetch_bytes(url,retries=5):
    last=None
    for attempt in range(retries):
        req=Request(url,headers={"User-Agent":USER_AGENT,"Accept":"text/csv,text/plain,*/*","Accept-Encoding":"gzip, deflate"})
        try:
            with urlopen(req,timeout=60) as response:
                raw=response.read()
                if response.headers.get("Content-Encoding","").lower()=="gzip" or raw[:2]==b"\x1f\x8b":
                    raw=gzip.decompress(raw)
                return raw,response.status,response.headers.get("Content-Type",""),response.headers.get("Last-Modified","")
        except HTTPError as error:
            last="HTTP{}".format(error.code)
            if error.code not in (408,429,500,502,503,504): raise
            time.sleep(min(20,2**attempt))
        except (URLError,TimeoutError,OSError) as error:
            last="{}:{}".format(type(error).__name__,error);time.sleep(min(20,2**attempt))
    raise RuntimeError("OCC Volume Query failed: {}".format(last))

def load_universe():
    tree=ast.parse(Path(BASE_SOURCE).read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node,ast.Assign):
            for target in node.targets:
                if isinstance(target,ast.Name) and target.id=="DEFAULT_UNIVERSE":
                    values=sorted({str(v).strip().upper() for v in ast.literal_eval(node.value)})
                    if len(values)!=335:raise RuntimeError("Expected 335 tickers, got {}".format(len(values)))
                    return values
    raise RuntimeError("DEFAULT_UNIVERSE not found")

def norm(value):
    return re.sub(r"[^a-z0-9]","",str(value or "").lower())

def parse_csv(raw):
    text=raw.decode("utf-8-sig","replace") if isinstance(raw,bytes) else str(raw)
    lines=[line for line in text.splitlines() if line.strip()]
    if not lines:return {"headers":[],"rows":[],"prefix":text[:300]}
    header_idx=0
    for i,line in enumerate(lines[:15]):
        low=line.lower()
        if "quantity" in low and "underlying" in low and "actype" in low:
            header_idx=i;break
    sample="\n".join(lines[header_idx:header_idx+10])
    try:dialect=csv.Sniffer().sniff(sample,delimiters=",\t|;")
    except csv.Error:dialect=csv.excel
    reader=csv.DictReader(lines[header_idx:],dialect=dialect)
    rows=[r for r in reader if r and any(v not in (None,"") for v in r.values())]
    return {"headers":reader.fieldnames or [],"rows":rows,"prefix":"\n".join(lines[:3])[:300]}

def volume_url(day,symbol):
    ymd=day.replace("-","")
    params={"reportDate":ymd,"format":"csv","volumeQueryType":"O","symbolType":"U","symbol":symbol,"reportType":"D","accountType":"ALL","productKind":"OSTK","porc":"BOTH"}
    # Deliberately omit contractDt: including it restricts the query to that series/contract date.
    return VOLUME_URL+"?"+urlencode(params)

def boundary_url(day,symbol):
    return volume_url(day,symbol)

def to_int(value):
    try:return int(float(str(value).replace(",",""))) if value not in (None,"") else None
    except ValueError:return None

def inspect_response(raw,requested_ticker,day):
    parsed=parse_csv(raw)
    lookup={norm(h):h for h in parsed["headers"]}
    missing=[field for field in REQUIRED if norm(field) not in lookup]
    rows=parsed["rows"]
    valid=[]
    for row in rows:
        normalized={norm(k):v for k,v in row.items()}
        quantity=to_int(normalized.get("quantity"))
        underlying=str(normalized.get("underlying") or "").strip().upper()
        actype=str(normalized.get("actype") or "").strip().upper()
        porc=str(normalized.get("porc") or "").strip().upper()
        actdate=str(normalized.get("actdate") or "").strip()
        if quantity is not None and underlying and actype in {"C","F","M"} and porc in {"C","P"}:
            valid.append((quantity,underlying,actype,porc,actdate))
    account_types=sorted({item[2] for item in valid})
    put_call=sorted({item[3] for item in valid})
    underlyings=sorted({item[1] for item in valid})
    quantities_by_type={}
    for code in ("C","F","M"):
        quantities_by_type[code]=sum(item[0] for item in valid if item[2]==code)
    quantities_by_type_and_side={}
    for code in ("C","F","M"):
        for side in ("C","P"):
            quantities_by_type_and_side[code+"_"+side]=sum(item[0] for item in valid if item[2]==code and item[3]==side)
    actdate_matches=sum(1 for item in valid if item[4]==datetime.strptime(day,"%Y-%m-%d").strftime("%m/%d/%Y"))
    return {
        "headers":parsed["headers"],"rows":rows,"row_count":len(rows),"valid_rows":len(valid),
        "schema_valid":not missing and len(valid)==len(rows) and len(rows)>0,
        "missing_required_fields":missing,"underlyings":underlyings,
        "requested_ticker_present":requested_ticker in underlyings,
        "account_types":account_types,"put_call_values":put_call,
        "quantities_by_account_type":quantities_by_type,
        "quantities_by_account_type_put_call":quantities_by_type_and_side,
        "activity_date_match_rate":actdate_matches/len(valid) if valid else 0.0,
        "contract_dates":sorted({str((row.get(lookup.get("contractdate")) or "")).strip() for row in rows if lookup.get("contractdate")}),
        "prefix":parsed["prefix"],
    }

def main():
    OUT_DIR.mkdir(parents=True,exist_ok=True)
    tickers=load_universe()
    pair_rows=[]; errors=[]; sample_rows=[]
    for day in DATES:
        for i,ticker in enumerate(tickers,1):
            url=volume_url(day,ticker)
            try:
                raw,status,content_type,last_modified=fetch_bytes(url)
                inspected=inspect_response(raw,ticker,day)
                pair_rows.append({
                    "date":day,"ticker":ticker,"url":url,"http_status":status,
                    "content_type":content_type,"last_modified_header":last_modified,
                    "bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest(),
                    "row_count":inspected["row_count"],"valid_rows":inspected["valid_rows"],
                    "schema_valid":inspected["schema_valid"],
                    "requested_ticker_present":inspected["requested_ticker_present"],
                    "account_types":";".join(inspected["account_types"]),
                    "put_call_values":";".join(inspected["put_call_values"]),
                    "activity_date_match_rate":inspected["activity_date_match_rate"],
                    "contract_date_count":len(inspected["contract_dates"]),
                    "quantity_customer":inspected["quantities_by_account_type"]["C"],
                    "quantity_firm":inspected["quantities_by_account_type"]["F"],
                    "quantity_market_maker":inspected["quantities_by_account_type"]["M"],
                    "missing_required_fields":";".join(inspected["missing_required_fields"]),
                    "response_prefix":inspected["prefix"],
                })
                for row in inspected["rows"][:10]:
                    sample_rows.append({"date":day,"requested_ticker":ticker,**row})
            except Exception as error:
                errors.append({"date":day,"ticker":ticker,"url":url,"error":str(error)})
                pair_rows.append({"date":day,"ticker":ticker,"url":url,"schema_valid":False,"row_count":0,"error":str(error)})
            if i%50==0:
                print(json.dumps({"stage":"UNIVERSE_PROGRESS","date":day,"processed":i,"total":len(tickers)}),flush=True)
            time.sleep(0.2)

    boundary=[]
    for ticker in BOUNDARY_SYMBOLS:
        url=boundary_url(BOUNDARY_DATE,ticker)
        try:
            raw,status,content_type,last_modified=fetch_bytes(url)
            parsed=parse_csv(raw)
            boundary.append({"date":BOUNDARY_DATE,"ticker":ticker,"http_status":status,"bytes":len(raw),"headers":parsed["headers"],"row_count":len(parsed["rows"]),"prefix":parsed["prefix"]})
        except Exception as error:
            boundary.append({"date":BOUNDARY_DATE,"ticker":ticker,"error":str(error)})
        time.sleep(0.2)

    by_date={}
    for day in DATES:
        rows=[row for row in pair_rows if row["date"]==day]
        valid=[row for row in rows if row.get("schema_valid")]
        covered=[row for row in valid if row.get("requested_ticker_present")]
        by_date[day]={
            "ticker_queries":len(rows),"schema_valid_queries":len(valid),
            "schema_valid_rate":len(valid)/len(rows) if rows else 0.0,
            "tickers_with_rows":len(covered),"ticker_coverage":len(covered)/len(tickers),
            "mean_rows_per_valid_ticker":sum(row["row_count"] for row in valid)/len(valid) if valid else 0.0,
            "account_type_presence":{code:sum(code in row.get("account_types","").split(";") for row in valid) for code in ("C","F","M")},
            "mean_activity_date_match_rate":sum(row.get("activity_date_match_rate",0) for row in valid)/len(valid) if valid else 0.0,
        }
    coverage_pass=all(by_date[day]["ticker_coverage"]>=0.70 and by_date[day]["schema_valid_rate"]>=0.95 for day in DATES)
    summary={
        "phase":"53B_OCC_volume_query_full_expiry_universe_audit",
        "status":"COMPLETE",
        "frozen_universe_size":len(tickers),
        "dates":list(DATES),
        "by_date":by_date,
        "boundary_2024_probes":boundary,
        "total_ticker_date_queries":len(pair_rows),
        "schema_valid_ticker_date_queries":sum(bool(row.get("schema_valid")) for row in pair_rows),
        "errors":errors[:100],
        "volume_query_data_gate":"PASS" if coverage_pass else "FAIL",
        "historical_depth_gate":"FAIL_FOR_LONG_OOS",
        "documented_retention":"OCC Volume Query UI states data available for past 24 months; 2024-01-03 probe tests the boundary.",
        "pit_publication_timestamp":"NOT_VERIFIED",
        "pit_rule":"Do not use reportDate as KnowledgeDate; OCC does not provide a historical publication timestamp in the reviewed docs. If retained for a later test, use a conservative next-session availability rule.",
        "economic_interpretation":"Volume is reported by account type and call/put, exchange, underlying/root and series/contract date. It does not disclose buy/sell aggressor side, open/close status, strike-level position changes or actual OI.",
        "contract_date_filter":"Omitted intentionally to include all series/contract dates; the prior pilot passed contractDt=reportDate and therefore sampled only that date's series (mostly 0DTE).",
        "forward_returns_used":False,
        "audit_timestamp_utc":datetime.now(timezone.utc).isoformat(),
    }
    with (OUT_DIR/"ticker_date_coverage.csv").open("w",newline="",encoding="utf-8") as handle:
        fields=list(pair_rows[0].keys()) if pair_rows else ["date","ticker","schema_valid"]
        writer=csv.DictWriter(handle,fieldnames=fields,extrasaction="ignore");writer.writeheader();writer.writerows(pair_rows)
    with (OUT_DIR/"volume_query_sample_rows.csv").open("w",newline="",encoding="utf-8") as handle:
        fields=list(sample_rows[0].keys()) if sample_rows else ["date","requested_ticker"]
        writer=csv.DictWriter(handle,fieldnames=fields,extrasaction="ignore");writer.writeheader();writer.writerows(sample_rows)
    (OUT_DIR/"summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    print(json.dumps(summary,indent=2),flush=True)

if __name__=="__main__":
    main()

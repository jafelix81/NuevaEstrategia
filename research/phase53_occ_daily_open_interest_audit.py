#!/usr/bin/env python3
"""OCC daily open-interest and account-type volume feasibility audit.

Public-source data audit only. Open interest is not trade direction, and this
script performs no forward-return or alpha test.
"""
from __future__ import annotations
import ast, csv, gzip, hashlib, json, re, time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE_SOURCE = "Nueva_Estrategia_Fase0_Descubrimiento.py"
OCC_BASE = "https://marketdata.theocc.com"
OCC_OI_URL = OCC_BASE + "/daily-open-interest"
OCC_VOLUME_URL = OCC_BASE + "/volume-query"
USER_AGENT = "Mozilla/5.0 (compatible; NuevaEstrategiaResearch/1.0; jose.felix@felixsarmiento.com)"
SAMPLE_DATES = ("2018-01-03","2020-01-03","2022-01-03","2023-04-14","2024-01-03","2025-01-03","2026-01-05","2026-11-02")
VOLUME_DATES = ("2024-01-03","2025-01-03","2026-11-02")
VOLUME_SYMBOLS = ("AAPL","NVDA","TSLA")
ACCOUNT_TYPES = ("C","F","M")
OUT_DIR = Path("phase53_occ_daily_open_interest_audit")

def decode_body(raw, content_encoding=""):
    if (content_encoding or "").lower() == "gzip" or raw[:2] == b"\x1f\x8b":
        return gzip.decompress(raw)
    return raw

def fetch_url(url, retries=4, timeout=60):
    last_error = None
    for attempt in range(retries):
        request = Request(url, headers={"User-Agent":USER_AGENT,"Accept":"text/csv,text/plain,application/octet-stream,*/*","Accept-Encoding":"gzip, deflate"})
        try:
            with urlopen(request, timeout=timeout) as response:
                return decode_body(response.read(), response.headers.get("Content-Encoding","")), response.status, response.headers.get("Content-Type",""), response.headers.get("Last-Modified","")
        except HTTPError as error:
            last_error = "HTTP{}".format(error.code)
            if error.code not in (408,429,500,502,503,504):
                raise
            time.sleep(min(20,2**attempt))
        except (URLError,TimeoutError,OSError) as error:
            last_error = "{}:{}".format(type(error).__name__,error)
            time.sleep(min(15,2**attempt))
    raise RuntimeError("OCC request failed after retries: {}".format(last_error))

def load_universe():
    tree = ast.parse(Path(BASE_SOURCE).read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node,ast.Assign):
            for target in node.targets:
                if isinstance(target,ast.Name) and target.id=="DEFAULT_UNIVERSE":
                    values=sorted({str(value).strip().upper() for value in ast.literal_eval(node.value)})
                    if len(values)!=335: raise RuntimeError("Expected 335 frozen tickers, got {}".format(len(values)))
                    return values
    raise RuntimeError("DEFAULT_UNIVERSE not found")

def norm_col(value):
    return re.sub(r"[^a-z0-9]","",str(value or "").lower())

def parse_osi_root(value):
    text=str(value or "").strip().upper()
    match=re.match(r"^(.{1,6})\d{6}[CP]\d{8}$",text)
    return match.group(1).strip() if match else None

def normalize_ticker(value):
    text=str(value or "").strip().upper()
    return text.replace("/",".") if text else None

def parse_csv_payload(raw):
    text=raw.decode("utf-8-sig","replace") if isinstance(raw,bytes) else str(raw)
    lines=[line for line in text.splitlines() if line.strip()]
    if not lines: return {"header":[],"rows":[],"delimiter":None,"text_prefix":text[:500]}
    header_index=None
    for index,line in enumerate(lines[:30]):
        lowered=line.lower()
        if ("open interest" in lowered or "openinterest" in lowered or "volume" in lowered) and any(d in line for d in (",","\t","|",";")):
            header_index=index; break
    if header_index is None:
        try: dialect=csv.Sniffer().sniff("\n".join(lines[:10]),delimiters=",\t|;")
        except csv.Error: dialect=csv.excel
        header_index=0
    sample="\n".join(lines[header_index:header_index+10])
    try: dialect=csv.Sniffer().sniff(sample,delimiters=",\t|;")
    except csv.Error: dialect=csv.excel
    reader=csv.DictReader(lines[header_index:],dialect=dialect)
    rows=[row for row in reader if row and any(value not in (None,"") for value in row.values())]
    return {"header":reader.fieldnames or [],"rows":rows,"delimiter":dialect.delimiter,"text_prefix":"\n".join(lines[:3])[:500]}

def find_column(headers,candidates):
    by_normalized={norm_col(header):header for header in headers}
    for candidate in candidates:
        if norm_col(candidate) in by_normalized: return by_normalized[norm_col(candidate)]
    return None

def extract_contract_rows(parsed):
    headers,rows=parsed["header"],parsed["rows"]
    underlying_col=find_column(headers,("Underlying","Underlying Symbol","UnderlyingSymbol","Underlying Ticker"))
    symbol_col=find_column(headers,("Option Symbol","OptionSymbol","Contract Symbol","Symbol","OSI Symbol"))
    oi_col=find_column(headers,("Open Interest","OpenInterest","OI","Open Int"))
    volume_col=find_column(headers,("Volume","Contracts","Contract Volume","Total Volume"))
    expiry_col=find_column(headers,("Expiration","Expiry","Expiration Date"))
    strike_col=find_column(headers,("Strike","Strike Price"))
    type_col=find_column(headers,("Put/Call","Put or Call","Option Type","Call Put","Type"))
    output=[]
    for row in rows:
        raw_underlying=row.get(underlying_col) if underlying_col else None
        raw_symbol=row.get(symbol_col) if symbol_col else None
        underlying=normalize_ticker(raw_underlying) if raw_underlying else parse_osi_root(raw_symbol)
        oi_raw=row.get(oi_col) if oi_col else None
        try: oi=int(float(str(oi_raw).replace(",",""))) if oi_raw not in (None,"") else None
        except ValueError: oi=None
        volume_raw=row.get(volume_col) if volume_col else None
        try: volume=int(float(str(volume_raw).replace(",",""))) if volume_raw not in (None,"") else None
        except ValueError: volume=None
        output.append({"underlying":underlying,"option_symbol":raw_symbol,"open_interest":oi,"volume":volume,"expiration":row.get(expiry_col) if expiry_col else None,"strike":row.get(strike_col) if strike_col else None,"put_call":row.get(type_col) if type_col else None})
    return {"underlying_column":underlying_col,"symbol_column":symbol_col,"open_interest_column":oi_col,"volume_column":volume_col,"rows":output}

def report_date(value):
    return datetime.strptime(value,"%Y-%m-%d").strftime("%m/%d/%Y")

def occ_oi_url(day):
    return OCC_OI_URL+"?"+urlencode({"reportDate":report_date(day),"action":"download","format":"csv"})

def occ_volume_url(day,symbol,account_type):
    yyyymmdd=day.replace("-","")
    return OCC_VOLUME_URL+"?"+urlencode({"reportDate":yyyymmdd,"format":"csv","volumeQueryType":"O","symbolType":"U","symbol":symbol,"reportType":"D","accountType":account_type,"productKind":"OSTK","porc":"BOTH","contractDt":yyyymmdd})

def main():
    OUT_DIR.mkdir(parents=True,exist_ok=True)
    universe=set(load_universe())
    oi_summaries,oi_rows,oi_errors=[],[],[]
    for day in SAMPLE_DATES:
        url=occ_oi_url(day)
        try:
            raw,status,content_type,last_modified=fetch_url(url)
            parsed=parse_csv_payload(raw); extracted=extract_contract_rows(parsed); contracts=extracted["rows"]
            underlyings=sorted({row["underlying"] for row in contracts if row["underlying"]})
            target=sorted(universe.intersection(underlyings))
            valid_oi=[row["open_interest"] for row in contracts if row["open_interest"] is not None]
            oi_summaries.append({"report_date":day,"url":url,"http_status":status,"content_type":content_type,"last_modified_header":last_modified,"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest(),"header":parsed["header"],"delimiter":parsed["delimiter"],"contract_rows":len(contracts),"unique_underlyings":len(underlyings),"frozen_universe_underlying_count":len(target),"frozen_universe_coverage":len(target)/len(universe),"target_tickers_observed":target,"open_interest_nonnull_rows":len(valid_oi),"total_open_interest":sum(valid_oi) if valid_oi else None,"underlying_column":extracted["underlying_column"],"option_symbol_column":extracted["symbol_column"],"open_interest_column":extracted["open_interest_column"],"volume_column":extracted["volume_column"],"text_prefix":parsed["text_prefix"]})
            for contract in contracts[:30]: oi_rows.append({"report_date":day,**contract})
        except Exception as error:
            oi_errors.append({"report_date":day,"url":url,"error":str(error)})
            oi_summaries.append({"report_date":day,"url":url,"error":str(error),"contract_rows":0,"frozen_universe_coverage":0.0})
        time.sleep(0.2)

    volume_summaries,volume_rows,volume_errors=[],[],[]
    for day in VOLUME_DATES:
        for symbol in VOLUME_SYMBOLS:
            for account_type in ACCOUNT_TYPES:
                url=occ_volume_url(day,symbol,account_type)
                try:
                    raw,status,content_type,last_modified=fetch_url(url)
                    parsed=parse_csv_payload(raw)
                    volume_summaries.append({"report_date":day,"symbol":symbol,"account_type":account_type,"url":url,"http_status":status,"content_type":content_type,"last_modified_header":last_modified,"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest(),"header":parsed["header"],"row_count":len(parsed["rows"]),"delimiter":parsed["delimiter"],"text_prefix":parsed["text_prefix"]})
                    for item in parsed["rows"][:20]: volume_rows.append({"report_date":day,"symbol":symbol,"account_type":account_type,**item})
                except Exception as error:
                    volume_errors.append({"report_date":day,"symbol":symbol,"account_type":account_type,"url":url,"error":str(error)})
                    volume_summaries.append({"report_date":day,"symbol":symbol,"account_type":account_type,"row_count":0,"error":str(error)})
                time.sleep(0.2)

    successful_oi=[row for row in oi_summaries if row.get("contract_rows",0)>0 and row.get("open_interest_nonnull_rows",0)>0]
    coverage_values=[row["frozen_universe_coverage"] for row in successful_oi]
    earliest=min((row["report_date"] for row in successful_oi),default=None)
    latest=max((row["report_date"] for row in successful_oi),default=None)
    recent_volume=[row for row in volume_summaries if row["report_date"] in ("2025-01-03","2026-11-02")]
    older_volume=[row for row in volume_summaries if row["report_date"]=="2024-01-03"]
    recent_nonempty=sum(row.get("row_count",0)>0 for row in recent_volume)
    recent_rate=recent_nonempty/len(recent_volume) if recent_volume else 0.0
    older_nonempty=sum(row.get("row_count",0)>0 for row in older_volume)
    history_years=0.0
    if earliest and latest:
        history_years=(datetime.strptime(latest,"%Y-%m-%d")-datetime.strptime(earliest,"%Y-%m-%d")).days/365.25
    min_coverage=min(coverage_values) if coverage_values else 0.0
    gates={"at_least_6_of_8_oi_dates_have_contract_data":len(successful_oi)>=6,"oi_history_spans_at_least_3_years":history_years>=3.0,"minimum_successful_date_universe_coverage_at_least_70pct":min_coverage>=0.70,"recent_volume_query_nonempty_rate_at_least_80pct":recent_rate>=0.80}
    summary={"phase":"53_OCC_daily_open_interest_feasibility","status":"COMPLETE","data_gate":"PASS" if all(gates.values()) else "FAIL_OR_PARTIAL","frozen_universe_size":len(universe),"oi_sample_dates":list(SAMPLE_DATES),"oi_successful_dates":len(successful_oi),"oi_earliest_available_sample":earliest,"oi_latest_available_sample":latest,"oi_sample_history_span_years":history_years,"oi_minimum_successful_date_universe_coverage":min_coverage,"oi_mean_successful_date_universe_coverage":sum(coverage_values)/len(coverage_values) if coverage_values else 0.0,"oi_by_date":oi_summaries,"oi_errors":oi_errors,"volume_query_probes":len(volume_summaries),"volume_query_recent_probes":len(recent_volume),"volume_query_recent_nonempty_probes":recent_nonempty,"volume_query_recent_nonempty_rate":recent_rate,"volume_query_older_2024_nonempty_probes":older_nonempty,"volume_query_by_probe":volume_summaries,"volume_query_errors":volume_errors,"gate_checks":gates,"pit_publication_timestamp":"NOT_VERIFIED","pit_rule":"Do not use reportDate as KnowledgeDate. OCC's public Daily Open Interest page documents the download endpoint but not a reproducible historical publication timestamp. Keep conditional until release timing is evidenced; any later test must use a conservative next-session rule.","economic_interpretation":"Daily OI is outstanding contract inventory, not buyer/seller direction, trade initiation, or proof of informed positioning. Volume by account type does not disclose buy/sell side. Treat any combination as a hypothesis.","historical_universe_limitation":"Coverage is measured against the current frozen 335-name list, not a point-in-time active/delisted universe.","forward_returns_used":False,"audit_timestamp_utc":datetime.now(timezone.utc).isoformat()}

    with (OUT_DIR/"oi_date_summary.csv").open("w",newline="",encoding="utf-8") as handle:
        fields=["report_date","http_status","bytes","contract_rows","unique_underlyings","frozen_universe_underlying_count","frozen_universe_coverage","open_interest_nonnull_rows","total_open_interest","open_interest_column","underlying_column","option_symbol_column","content_type","last_modified_header","sha256","error"]
        writer=csv.DictWriter(handle,fieldnames=fields,extrasaction="ignore"); writer.writeheader(); writer.writerows(oi_summaries)
    with (OUT_DIR/"oi_sample_contracts.csv").open("w",newline="",encoding="utf-8") as handle:
        fields=list(oi_rows[0].keys()) if oi_rows else ["report_date","underlying","option_symbol","open_interest","volume"]
        writer=csv.DictWriter(handle,fieldnames=fields,extrasaction="ignore"); writer.writeheader(); writer.writerows(oi_rows)
    with (OUT_DIR/"volume_query_summary.csv").open("w",newline="",encoding="utf-8") as handle:
        fields=["report_date","symbol","account_type","http_status","bytes","row_count","content_type","last_modified_header","sha256","error"]
        writer=csv.DictWriter(handle,fieldnames=fields,extrasaction="ignore"); writer.writeheader(); writer.writerows(volume_summaries)
    with (OUT_DIR/"volume_query_sample_rows.csv").open("w",newline="",encoding="utf-8") as handle:
        fields=list(volume_rows[0].keys()) if volume_rows else ["report_date","symbol","account_type"]
        writer=csv.DictWriter(handle,fieldnames=fields,extrasaction="ignore"); writer.writeheader(); writer.writerows(volume_rows)
    (OUT_DIR/"summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    print(json.dumps(summary,indent=2),flush=True)

if __name__=="__main__":
    main()

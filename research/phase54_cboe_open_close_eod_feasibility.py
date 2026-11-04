#!/usr/bin/env python3
"""Inspect Cboe Open-Close EOD sample for schema and coverage feasibility."""
from __future__ import annotations
import ast, csv, gzip, hashlib, io, json, re, time, zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE_SOURCE="Nueva_Estrategia_Fase0_Descubrimiento.py"
SAMPLE_URL="https://datashop.cboe.com/download/sample/218"
USER_AGENT="Mozilla/5.0 (compatible; NuevaEstrategiaResearch/1.0; jose.felix@felixsarmiento.com)"
OUT_DIR=Path("phase54_cboe_open_close_eod_feasibility")
KEY_FIELDS=("quote_date","underlying_symbol","expiration_date","strike_price","call_put_flag","total_exchange_vol","open_interest","previous_open_interest","firm_open_buy_vol","firm_open_sell_vol","mm_buy_vol","mm_sell_vol","cust_lt_100_open_buy_vol","cust_lt_100_open_sell_vol","procust_lt_100_open_buy_vol","procust_lt_100_open_sell_vol")

def fetch_bytes(url,retries=4):
    last=None
    for attempt in range(retries):
        req=Request(url,headers={"User-Agent":USER_AGENT,"Accept":"application/zip,application/octet-stream,*/*","Accept-Encoding":"gzip, deflate"})
        try:
            with urlopen(req,timeout=90) as response:
                raw=response.read()
                if (response.headers.get("Content-Encoding","").lower()=="gzip" or raw[:2]==b"\x1f\x8b"):
                    raw=gzip.decompress(raw)
                return raw,response.status,response.headers.get("Content-Type",""),response.headers.get("Last-Modified","")
        except HTTPError as error:
            last="HTTP{}".format(error.code)
            if error.code not in (408,429,500,502,503,504): raise
            time.sleep(2**attempt)
        except (URLError,TimeoutError,OSError) as error:
            last="{}:{}".format(type(error).__name__,error); time.sleep(2**attempt)
    raise RuntimeError("sample download failed: {}".format(last))

def load_universe():
    tree=ast.parse(Path(BASE_SOURCE).read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node,ast.Assign):
            for target in node.targets:
                if isinstance(target,ast.Name) and target.id=="DEFAULT_UNIVERSE":
                    values=sorted({str(v).strip().upper() for v in ast.literal_eval(node.value)})
                    if len(values)!=335: raise RuntimeError("Expected 335 tickers, got {}".format(len(values)))
                    return set(values)
    raise RuntimeError("DEFAULT_UNIVERSE not found")

def norm(value):
    return re.sub(r"[^a-z0-9]","",str(value or "").lower())

def parse_csv_bytes(raw):
    text=raw.decode("utf-8-sig","replace") if isinstance(raw,bytes) else str(raw)
    lines=[line for line in text.splitlines() if line.strip()]
    if not lines: return {"headers":[],"rows":[],"text_prefix":text[:300]}
    header_idx=0
    for i,line in enumerate(lines[:20]):
        low=line.lower()
        if "underlying_symbol" in low or ("quote_date" in low and "open_interest" in low):
            header_idx=i; break
    sample="\n".join(lines[header_idx:header_idx+10])
    try: dialect=csv.Sniffer().sniff(sample,delimiters=",\t|;")
    except csv.Error: dialect=csv.excel
    reader=csv.DictReader(lines[header_idx:],dialect=dialect)
    return {"headers":reader.fieldnames or [],"rows":[r for r in reader if r and any(v not in (None,"") for v in r.values())],"text_prefix":"\n".join(lines[:3])[:300]}

def extract_zip_csvs(raw):
    output=[]
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        members=[name for name in archive.namelist() if name.lower().endswith(".csv")]
        nested=[name for name in archive.namelist() if name.lower().endswith(".zip")]
        for name in members:
            output.append((name,archive.read(name)))
        for name in nested:
            output.extend((name+"!"+subname,data) for subname,data in extract_zip_csvs(archive.read(name)))
    return output

def field_coverage(headers,rows,field):
    lookup={norm(h):h for h in headers}
    key=norm(field)
    if key not in lookup: return {"present":False,"nonnull_rate":0.0}
    actual=lookup[key]
    count=sum(1 for row in rows if row.get(actual) not in (None,""))
    return {"present":True,"nonnull_rate":count/len(rows) if rows else 0.0}

def to_num(value):
    try: return float(str(value).replace(",","")) if value not in (None,"") else None
    except ValueError: return None

def inspect_file(name,raw,universe):
    parsed=parse_csv_bytes(raw)
    headers,rows=parsed["headers"],parsed["rows"]
    normalized={norm(h):h for h in headers}
    underlying_col=normalized.get("underlyingsymbol")
    industry_col=normalized.get("totalindustryvol")
    exchange_col=normalized.get("totalexchangevol")
    underlying_values=sorted({str(row.get(underlying_col,"")).strip().upper() for row in rows if underlying_col and row.get(underlying_col)})
    target=sorted(set(underlying_values).intersection(universe))
    shares=[]
    if industry_col and exchange_col:
        for row in rows:
            industry=to_num(row.get(industry_col)); exchange=to_num(row.get(exchange_col))
            if industry and industry>0 and exchange is not None:
                shares.append(exchange/industry)
    participant_fields=[h for h in headers if re.search(r"(firm|bd_|mm_|cust_|procust_).*(open|close).*(buy|sell).*vol",h,re.I)]
    participant_nonzero=0
    for row in rows:
        if any((to_num(row.get(field)) or 0)>0 for field in participant_fields):
            participant_nonzero+=1
    return {
        "member":name,
        "bytes":len(raw),
        "sha256":hashlib.sha256(raw).hexdigest(),
        "row_count":len(rows),
        "headers":headers,
        "header_count":len(headers),
        "quote_dates":sorted({str(row.get(normalized.get("quotedate"),"")) for row in rows if normalized.get("quotedate")}),
        "unique_underlyings":len(underlying_values),
        "target_tickers_observed":target,
        "target_ticker_count":len(target),
        "target_universe_coverage":len(target)/len(universe),
        "participant_fields_present":participant_fields,
        "participant_nonzero_rows":participant_nonzero,
        "participant_nonzero_rate":participant_nonzero/len(rows) if rows else 0.0,
        "market_share_proxy_rows":len(shares),
        "market_share_proxy_median":sorted(shares)[len(shares)//2] if shares else None,
        "market_share_proxy_p90":sorted(shares)[int(0.9*(len(shares)-1))] if shares else None,
        "field_coverage":{field:field_coverage(headers,rows,field) for field in KEY_FIELDS},
        "text_prefix":parsed["text_prefix"],
        "sample_rows":rows[:5],
    }

def main():
    OUT_DIR.mkdir(parents=True,exist_ok=True)
    universe=load_universe()
    raw,status,content_type,last_modified=fetch_bytes(SAMPLE_URL)
    (OUT_DIR/"cboe_open_close_sample.zip").write_bytes(raw)
    if raw[:2]!=b"PK":
        raise RuntimeError("Sample response is not a ZIP archive; prefix={!r}".format(raw[:300]))
    members=extract_zip_csvs(raw)
    files=[inspect_file(name,data,universe) for name,data in members]
    key_passes=[]
    for item in files:
        rates=item["field_coverage"]
        key_passes.append(
            item["row_count"]>0
            and all(rates[field]["present"] and rates[field]["nonnull_rate"]>=0.95 for field in (
                "quote_date","underlying_symbol","expiration_date","strike_price","call_put_flag",
                "total_exchange_vol","open_interest","firm_open_buy_vol","firm_open_sell_vol",
                "mm_buy_vol","mm_sell_vol","cust_lt_100_open_buy_vol","cust_lt_100_open_sell_vol",
                "procust_lt_100_open_buy_vol","procust_lt_100_open_sell_vol",
            ))
        )
    summary={
        "phase":"54_Cboe_Open_Close_EOD_sample_feasibility",
        "status":"COMPLETE",
        "sample_url":SAMPLE_URL,
        "http_status":status,
        "content_type":content_type,
        "last_modified_header":last_modified,
        "zip_bytes":len(raw),
        "zip_sha256":hashlib.sha256(raw).hexdigest(),
        "zip_members":[name for name,_ in members],
        "parsed_csv_files":len(files),
        "frozen_universe_size":len(universe),
        "file_summaries":files,
        "schema_gate":"PASS" if files and all(key_passes) else "FAIL_OR_PARTIAL",
        "schema_gate_by_file":key_passes,
        "historical_coverage":"DOCUMENTED_NOT_YET_PURCHASED",
        "pit_delivery":"Cboe EOD specification says final subscription files are typically delivered 00:30-01:00 US Eastern next morning; use next trading session as conservative KnowledgeDate.",
        "economic_caution":"Participant categories and buy/sell/open/close fields are observed classifications, not proof of informed trading. Cboe exchanges are only part of OPRA; total_industry_vol is a best-effort third-party value and historical conventions must be audited.",
        "forward_returns_used":False,
        "audit_timestamp_utc":datetime.now(timezone.utc).isoformat(),
    }
    (OUT_DIR/"summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    with (OUT_DIR/"sample_rows.json").open("w",encoding="utf-8") as handle:
        json.dump([{"member":item["member"],"sample_rows":item["sample_rows"]} for item in files],handle,indent=2)
    print(json.dumps(summary,indent=2),flush=True)
    if summary["schema_gate"]!="PASS":
        raise RuntimeError("Cboe Open-Close sample schema gate failed")

if __name__=="__main__":
    main()

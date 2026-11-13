#!/usr/bin/env python3
"""Phase 381: audit alternative daily price providers for Phase 20C's 7 missing symbols.

Provider feasibility only. No prices are persisted; the artifact contains
availability counts, date ranges and cross-provider return-comparison metrics.
"""
from __future__ import annotations
import argparse, json, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timezone
from io import StringIO
from pathlib import Path
import requests
import pandas as pd
import numpy as np

START="2016-10-24"
END_EXCLUSIVE="2026-10-24"
MISSING=("AVB","EA","EQR","LPRO","ROKU","WBD","WBS")
CONTROLS=("AAPL","MSFT","NVDA","SPY")
TICKERS=MISSING+CONTROLS
TIMEOUT=35

def epoch(day):
    return int(datetime.strptime(day,"%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp())

def new_session():
    s=requests.Session()
    s.headers.update({"User-Agent":"Mozilla/5.0 (compatible; NuevaEstrategia/Phase381; research)"})
    return s

def summarize_series(ticker,provider,dates,closes,status,http_status=None,error=None,adj_rows=None):
    valid=[(d,float(v)) for d,v in zip(dates,closes) if v is not None and np.isfinite(float(v)) and float(v)>0]
    valid.sort(key=lambda x:x[0])
    return {
        "ticker":ticker,"provider":provider,"status":status,"http_status":http_status,
        "rows":len(valid),"first_date":valid[0][0] if valid else None,
        "last_date":valid[-1][0] if valid else None,
        "adj_close_rows":adj_rows,"error_class":error,
        "_series":{d:v for d,v in valid},
    }

def fetch_yahoo(ticker,host):
    s=new_session()
    url=f"https://{host}/v8/finance/chart/{ticker}"
    params={"period1":epoch(START),"period2":epoch(END_EXCLUSIVE),"interval":"1d","events":"div,splits"}
    last=None
    for attempt in range(3):
        try:
            r=s.get(url,params=params,timeout=TIMEOUT)
            if r.status_code in (429,500,502,503,504): raise requests.HTTPError(f"HTTP {r.status_code}")
            r.raise_for_status()
            payload=r.json().get("chart",{})
            result=payload.get("result")
            if not result:
                raise ValueError(str(payload.get("error") or "empty chart result")[:160])
            item=result[0]
            timestamps=item.get("timestamp") or []
            quote=(item.get("indicators") or {}).get("quote",[{}])[0]
            closes=quote.get("close") or []
            adj=(item.get("indicators") or {}).get("adjclose",[{}])[0].get("adjclose") or []
            dates=[datetime.fromtimestamp(ts,timezone.utc).date().isoformat() for ts in timestamps]
            out=summarize_series(ticker,f"yahoo_{host}",dates,closes,"ok",r.status_code,
                                 adj_rows=sum(x is not None for x in adj))
            out["_adj_series"]={d:float(v) for d,v in zip(dates,adj) if v is not None and np.isfinite(float(v))}
            return out
        except Exception as exc:
            last=type(exc).__name__
            if attempt<2: time.sleep(2**attempt)
    return summarize_series(ticker,f"yahoo_{host}",[],[],"failed",error=last)

def fetch_stooq(ticker):
    s=new_session()
    url="https://stooq.com/q/d/l/"
    params={"s":ticker.lower()+".us","d1":START.replace("-",""),"d2":END_EXCLUSIVE.replace("-",""),"i":"d"}
    try:
        r=s.get(url,params=params,timeout=TIMEOUT)
        r.raise_for_status()
        frame=pd.read_csv(StringIO(r.text))
        if not {"Date","Close"}.issubset(frame.columns):
            raise ValueError("missing Date/Close columns")
        dates=pd.to_datetime(frame.Date,errors="coerce").dt.strftime("%Y-%m-%d").tolist()
        closes=pd.to_numeric(frame.Close,errors="coerce").tolist()
        return summarize_series(ticker,"stooq",dates,closes,"ok" if len(frame) else "empty",r.status_code)
    except Exception as exc:
        return summarize_series(ticker,"stooq",[],[],"failed",error=type(exc).__name__)

def fetch_nasdaq(ticker):
    s=new_session()
    s.headers.update({"Accept":"application/json, text/plain, */*","Origin":"https://www.nasdaq.com",
                      "Referer":f"https://www.nasdaq.com/market-activity/stocks/{ticker.lower()}/historical"})
    url=f"https://api.nasdaq.com/api/quote/{ticker}/historical"
    params={"assetclass":"stocks","fromdate":"10/24/2016","limit":"5000","todate":"10/24/2026"}
    try:
        r=s.get(url,params=params,timeout=TIMEOUT)
        r.raise_for_status()
        data=r.json().get("data") or {}
        table=data.get("tradesTable") or {}
        rows=table.get("rows") or []
        dates=[];closes=[]
        for row in rows:
            d=row.get("date") or row.get("Date")
            c=row.get("close") or row.get("Close/Last") or row.get("closePrice")
            if d and c is not None:
                dates.append(str(d).strip())
                closes.append(float(str(c).replace("$","").replace(",","")))
        return summarize_series(ticker,"nasdaq",dates,closes,"ok" if rows else "empty",r.status_code)
    except Exception as exc:
        return summarize_series(ticker,"nasdaq",[],[],"failed",error=type(exc).__name__)

def compare_returns(a,b):
    common=sorted(set(a)&set(b))
    if len(common)<30:
        return {"common_dates":len(common),"return_pairs":0,"median_abs_return_diff":None,
                "p95_abs_return_diff":None,"max_abs_return_diff":None,"return_corr":None}
    ra=[];rb=[]
    for d0,d1 in zip(common,common[1:]):
        va0,va1=a[d0],a[d1];vb0,vb1=b[d0],b[d1]
        if min(va0,va1,vb0,vb1)<=0: continue
        ra.append(va1/va0-1);rb.append(vb1/vb0-1)
    if not ra:
        return {"common_dates":len(common),"return_pairs":0,"median_abs_return_diff":None,
                "p95_abs_return_diff":None,"max_abs_return_diff":None,"return_corr":None}
    diff=np.abs(np.asarray(ra)-np.asarray(rb))
    corr=float(np.corrcoef(ra,rb)[0,1]) if np.std(ra)>0 and np.std(rb)>0 else None
    return {"common_dates":len(common),"return_pairs":len(diff),
            "median_abs_return_diff":float(np.median(diff)),
            "p95_abs_return_diff":float(np.quantile(diff,.95)),
            "max_abs_return_diff":float(np.max(diff)),"return_corr":corr}

def public_record(item):
    return {k:v for k,v in item.items() if not k.startswith("_")}

def run():
    tasks=[]
    with ThreadPoolExecutor(max_workers=4) as pool:
        for ticker in TICKERS:
            tasks.extend([
                pool.submit(fetch_yahoo,ticker,"query1.finance.yahoo.com"),
                pool.submit(fetch_yahoo,ticker,"query2.finance.yahoo.com"),
                pool.submit(fetch_stooq,ticker),
                pool.submit(fetch_nasdaq,ticker),
            ])
        results=[f.result() for f in as_completed(tasks)]
    by={(r["ticker"],r["provider"]):r for r in results}
    comparisons=[]
    for ticker in TICKERS:
        yahoo=by.get((ticker,"yahoo_query1.finance.yahoo.com"))
        stooq=by.get((ticker,"stooq"))
        nasdaq=by.get((ticker,"nasdaq"))
        if yahoo and stooq and yahoo["_series"] and stooq["_series"]:
            comparisons.append({"ticker":ticker,"pair":"Yahoo query1 vs Stooq",
                                **compare_returns(yahoo["_series"],stooq["_series"])})
        if stooq and nasdaq and stooq["_series"] and nasdaq["_series"]:
            comparisons.append({"ticker":ticker,"pair":"Stooq vs Nasdaq",
                                **compare_returns(stooq["_series"],nasdaq["_series"])})
    missing_records=[public_record(r) for r in results if r["ticker"] in MISSING]
    control_records=[public_record(r) for r in results if r["ticker"] in CONTROLS]
    coverage={t:{r["provider"]:r["rows"] for r in results if r["ticker"]==t} for t in TICKERS}
    missing_with_alternative=[t for t in MISSING if any(
        by.get((t,p),{}).get("rows",0)>=220 for p in ("stooq","nasdaq","yahoo_query1.finance.yahoo.com","yahoo_query2.finance.yahoo.com"))]
    return {
        "phase":381,"audit_timestamp_utc":datetime.now(timezone.utc).isoformat(),
        "price_window_start":START,"price_window_end_exclusive":END_EXCLUSIVE,
        "missing_tickers":list(MISSING),"control_tickers":list(CONTROLS),
        "provider_coverage_rows":coverage,"missing_ticker_provider_results":missing_records,
        "control_provider_results":control_records,"cross_provider_return_comparisons":comparisons,
        "missing_tickers_with_at_least_220_rows_from_one_alternative":missing_with_alternative,
        "fallback_accepted":False,
        "fallback_acceptance_rule":"Require >=220 rows, date-range completeness appropriate to listing date, and independent-provider return concordance; do not mix providers until validated.",
        "raw_prices_retained":False,"forward_returns_used":False,"alpha_test_authorized":False,
        "holdout_used":False,"f80_changed":False,"production_changed":False,
        "research_disposition":"PROVIDER_FEASIBILITY_AUDIT_ONLY_NO_FALLBACK_ADMITTED",
    }

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",default="phase381_finra_price_provider_fallback_audit")
    args=parser.parse_args()
    out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
    summary=run()
    (out/"summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True),encoding="utf-8")
    print("PHASE381_PRICE_PROVIDER_AUDIT=",summary["research_disposition"])
    print("MISSING_WITH_220_PLUS_ROWS=",summary["missing_tickers_with_at_least_220_rows_from_one_alternative"])
    print("RAW_PRICES_RETAINED=False")
    print("FALLBACK_ACCEPTED=False")
    if summary["raw_prices_retained"] or summary["alpha_test_authorized"] or summary["holdout_used"] or summary["f80_changed"]:
        raise SystemExit("Phase 381 research-only control violated")

if __name__=="__main__":
    main()

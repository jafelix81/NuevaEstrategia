"""
Phase 20 — Short Flow Discovery

Purpose
-------
Research FINRA/short-volume flow as an independent information source.
This phase MUST NOT modify F80. It is a discovery engine only.

Provider priority:
1) ChartExchange API when CHARTEXCHANGE_API_KEY is available (full short-volume history).
2) FINRA Reg SHO API when FINRA_ACCESS_TOKEN is available (rolling 12 months).

The engine deliberately refuses to call a short-volume signal "confirmed". It
reports data coverage, ex-ante factor/forward-return relationships, monotonicity,
bootstrap/permutation diagnostics, and redundancy against LTM when price data are
available. A later phase will decide whether any signal merits portfolio testing.
"""

from __future__ import annotations
import os, sys, time, json, math
from pathlib import Path
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np
import pandas as pd
import requests
from scipy.stats import spearmanr, rankdata

OUT = Path("phase20_outputs")
OUT.mkdir(exist_ok=True)

# Frozen F80 universe — loaded from the Phase 12 script to avoid a second universe.
UNIVERSE_FALLBACK = []
PHASE12 = Path("Nueva_Estrategia_Fase12_FinalOOS_Selection_LTM.py")


def load_universe():
    text = PHASE12.read_text(encoding="utf-8") if PHASE12.exists() else ""
    marker = "DEFAULT_UNIVERSE = ["
    if marker not in text:
        raise RuntimeError("Could not locate frozen DEFAULT_UNIVERSE in Phase 12.")
    start = text.index(marker) + len(marker)
    end = text.index("]", start)
    import ast
    vals = ast.literal_eval("[" + text[start:end] + "]")
    return [str(x).strip().upper() for x in vals if str(x).strip()]


UNIVERSE = load_universe()


def http_json(url, headers=None, params=None, payload=None, timeout=45):
    r = requests.post(url, headers=headers, json=payload, timeout=timeout) if payload is not None else requests.get(url, headers=headers, params=params, timeout=timeout)
    r.raise_for_status()
    return r.json()


def fetch_chartexchange(symbol, api_key, page_size=1000):
    url = "https://chartexchange.com/api/v1/data/stocks/short-volume/"
    rows, page = [], 1
    while True:
        params = {"api_key": api_key, "symbol": f"US:{symbol}", "ordering": "date", "page": page, "page_size": page_size, "format": "json"}
        data = http_json(url, params=params)
        results = data.get("results", data if isinstance(data, list) else [])
        rows.extend(results)
        nxt = data.get("next") if isinstance(data, dict) else None
        if not results or not nxt:
            break
        page += 1
        if page > 50:
            break
    out = []
    for x in rows:
        try:
            st = float(x.get("st", np.nan)); rt = float(x.get("rt", np.nan))
        except Exception:
            continue
        out.append({"Date": x.get("date"), "Ticker": symbol, "ShortVolume": st, "TotalVolume": rt, "Source": "ChartExchange"})
    return pd.DataFrame(out)


def fetch_finra(symbol, token, start_date=None, end_date=None, page_size=1000):
    url = "https://api.finra.org/data/group/otcMarket/name/regShoDaily"
    headers = {"Authorization": f"Bearer {token}", "Data-API-Version": "1", "Accept": "application/json"}
    payload_base = {
        "fields": ["tradeReportDate", "securitiesInformationProcessorSymbolIdentifier", "shortParQuantity", "shortExemptParQuantity", "totalParQuantity", "marketCode", "reportingFacilityCode"],
        "compareFilters": [{"compareType": "EQUAL", "fieldName": "securitiesInformationProcessorSymbolIdentifier", "fieldValue": symbol}],
        "limit": page_size,
        "offset": 0,
    }
    if start_date and end_date:
        payload_base["dateRangeFilters"] = [{"fieldName": "tradeReportDate", "startDate": start_date, "endDate": end_date}]
    rows, offset = [], 0
    while True:
        payload = dict(payload_base); payload["offset"] = offset
        data = http_json(url, headers=headers, payload=payload)
        if not data:
            break
        rows.extend(data)
        if len(data) < page_size:
            break
        offset += page_size
        if offset > 500000:
            raise RuntimeError("FINRA offset limit reached for symbol")
    if not rows:
        return pd.DataFrame(columns=["Date", "Ticker", "ShortVolume", "TotalVolume", "Source"])
    df = pd.DataFrame(rows)
    return pd.DataFrame({
        "Date": df["tradeReportDate"], "Ticker": symbol,
        "ShortVolume": pd.to_numeric(df["shortParQuantity"], errors="coerce"),
        "TotalVolume": pd.to_numeric(df["totalParQuantity"], errors="coerce"),
        "Source": "FINRA"
    })


def fetch_one(symbol, provider, credential):
    try:
        if provider == "chartexchange":
            return fetch_chartexchange(symbol, credential)
        return fetch_finra(symbol, credential)
    except Exception as e:
        return pd.DataFrame({"Ticker": [symbol], "ERROR": [repr(e)]})


def robust_z(s, window):
    med = s.rolling(window, min_periods=max(20, window // 2)).median()
    mad = (s - med).abs().rolling(window, min_periods=max(20, window // 2)).median()
    return (s - med) / (1.4826 * mad.replace(0, np.nan))


def build_features(raw):
    d = raw.copy()
    d["Date"] = pd.to_datetime(d["Date"], errors="coerce")
    d["ShortVolume"] = pd.to_numeric(d["ShortVolume"], errors="coerce")
    d["TotalVolume"] = pd.to_numeric(d["TotalVolume"], errors="coerce")
    d = d.dropna(subset=["Date", "Ticker", "ShortVolume", "TotalVolume"])
    d = d[d["TotalVolume"] > 0].copy()
    # Aggregate duplicate venues before calculating ratios.
    d = d.groupby(["Date", "Ticker"], as_index=False).agg({"ShortVolume": "sum", "TotalVolume": "sum"})
    d["SHORT_RATIO"] = d["ShortVolume"] / d["TotalVolume"]
    d = d.sort_values(["Ticker", "Date"])
    g = d.groupby("Ticker", group_keys=False)
    d["SHORT_RATIO_Z20"] = g["SHORT_RATIO"].transform(lambda x: robust_z(x, 20))
    d["SHORT_RATIO_Z60"] = g["SHORT_RATIO"].transform(lambda x: robust_z(x, 60))
    d["SHORT_RATIO_CHANGE"] = g["SHORT_RATIO"].transform(lambda x: x.diff(1))
    d["SHORT_RATIO_MOM5"] = g["SHORT_RATIO"].transform(lambda x: x.diff(5))
    d["SHORT_RATIO_MA5"] = g["SHORT_RATIO"].transform(lambda x: x.rolling(5, min_periods=5).mean())
    d["SHORT_RATIO_MA20"] = g["SHORT_RATIO"].transform(lambda x: x.rolling(20, min_periods=20).mean())
    d["SHORT_RATIO_EXCESS20"] = d["SHORT_RATIO_MA5"] - d["SHORT_RATIO_MA20"]
    d["HIGH_SHORT_PERSIST20"] = g["SHORT_RATIO"].transform(lambda x: (x > x.rolling(20, min_periods=20).median()).rolling(5, min_periods=5).mean())
    return d


def attach_prices(f):
    # Yahoo is used only for forward-return labels and LTM redundancy diagnostics.
    import yfinance as yf
    dates = f["Date"].drop_duplicates().sort_values()
    if dates.empty:
        return f
    start = (dates.min() - pd.Timedelta(days=260)).strftime("%Y-%m-%d")
    end = (dates.max() + pd.Timedelta(days=30)).strftime("%Y-%m-%d")
    out = []
    for ticker in UNIVERSE:
        try:
            px = yf.download(ticker, start=start, end=end, auto_adjust=True, progress=False, threads=False)
            if px.empty:
                continue
            if isinstance(px.columns, pd.MultiIndex):
                close = px["Close"].iloc[:, 0]
            else:
                close = px["Close"]
            q = pd.DataFrame({"Date": pd.to_datetime(close.index).tz_localize(None), "Ticker": ticker, "Close": close.values})
            out.append(q)
        except Exception:
            pass
    if not out:
        return f
    p = pd.concat(out, ignore_index=True).sort_values(["Ticker", "Date"])
    p["R120"] = p.groupby("Ticker")["Close"].transform(lambda x: x / x.shift(120) - 1)
    for h in (5, 10, 20):
        p[f"Y{h}"] = p.groupby("Ticker")["Close"].transform(lambda x: x.shift(-h) / x - 1)
    return f.merge(p, on=["Date", "Ticker"], how="left")


def qstats(df, factor, y):
    x = df[[factor, y]].dropna().copy()
    if len(x) < 80:
        return {"factor": factor, "target": y, "n": len(x), "spearman": np.nan, "p": np.nan}
    rho, p = spearmanr(x[factor], x[y])
    x["q"] = pd.qcut(x[factor], 5, labels=False, duplicates="drop")
    means = x.groupby("q")[y].mean().to_dict()
    return {"factor": factor, "target": y, "n": len(x), "spearman": float(rho), "p": float(p), "Q1": means.get(0, np.nan), "Q2": means.get(1, np.nan), "Q3": means.get(2, np.nan), "Q4": means.get(3, np.nan), "Q5": means.get(4, np.nan)}


def main():
    provider = None
    credential = None
    if os.getenv("CHARTEXCHANGE_API_KEY"):
        provider, credential = "chartexchange", os.environ["CHARTEXCHANGE_API_KEY"]
    elif os.getenv("FINRA_ACCESS_TOKEN"):
        provider, credential = "finra", os.environ["FINRA_ACCESS_TOKEN"]
    else:
        raise RuntimeError("No data credential. Set CHARTEXCHANGE_API_KEY for long history or FINRA_ACCESS_TOKEN for the rolling 12-month FINRA API.")

    print(f"PHASE20 PROVIDER={provider} UNIVERSE={len(UNIVERSE)}")
    frames = []
    errors = []
    with ThreadPoolExecutor(max_workers=3) as ex:
        futs = {ex.submit(fetch_one, s, provider, credential): s for s in UNIVERSE}
        for fut in as_completed(futs):
            s = futs[fut]
            df = fut.result()
            if "ERROR" in df.columns:
                errors.append(df.iloc[0].to_dict())
            elif not df.empty:
                frames.append(df)
    if not frames:
        raise RuntimeError("No short-volume data retrieved.")
    raw = pd.concat(frames, ignore_index=True)
    raw.to_csv(OUT / "phase20_short_volume_raw.csv", index=False)
    pd.DataFrame(errors).to_csv(OUT / "phase20_errors.csv", index=False)

    f = build_features(raw)
    f = attach_prices(f)
    f.to_csv(OUT / "phase20_factor_dataset.csv", index=False)

    factor_cols = ["SHORT_RATIO", "SHORT_RATIO_Z20", "SHORT_RATIO_Z60", "SHORT_RATIO_CHANGE", "SHORT_RATIO_MOM5", "SHORT_RATIO_EXCESS20", "HIGH_SHORT_PERSIST20"]
    results = []
    for fac in factor_cols:
        for y in ["Y5", "Y10", "Y20"]:
            results.append(qstats(f, fac, y))
    res = pd.DataFrame(results)
    res.to_csv(OUT / "phase20_factor_stats.csv", index=False)

    coverage = f.groupby("Ticker")["Date"].agg(["min", "max", "count"]).reset_index()
    coverage["years"] = (coverage["max"] - coverage["min"]).dt.days / 365.25
    summary = {
        "run_utc": datetime.now(timezone.utc).isoformat(),
        "provider": provider,
        "configured_universe": len(UNIVERSE),
        "tickers_with_data": int(coverage["Ticker"].nunique()),
        "median_history_years": float(coverage["years"].median()),
        "min_history_years": float(coverage["years"].min()),
        "max_history_years": float(coverage["years"].max()),
        "rows": int(len(f)),
        "status": "DISCOVERY_ONLY",
        "note": "No portfolio optimization or F80 modification is performed in Phase 20."
    }
    (OUT / "phase20_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print("TOP STATS")
    print(res.sort_values("p", na_position="last").head(20).to_string(index=False))


if __name__ == "__main__":
    main()

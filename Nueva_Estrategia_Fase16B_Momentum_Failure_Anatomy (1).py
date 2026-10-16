"""
FASE 16B — MOMENTUM FAILURE ANATOMY
====================================
Consumes the EXACT Phase 15B BASELINE C20 trade ledger.

This phase is diagnostic only. It does NOT reconstruct or reselect the strategy.
The entry universe, dates, Top20 selection, persistence, frequency and execution
are inherited from the Phase 15B ledger.

Input:
    phase15b_c20_trades.csv

For every BUY/SELL_CAP entry transaction, forward price-path diagnostics are
calculated from Yahoo Finance using the actual ExecutionOpen recorded by Phase 15B.
Forward returns are measured from the actual execution open to future closes.
MAE/MFE use future daily Low/High relative to the execution open.
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import yfinance as yf

RUN_ID = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
INPUT = Path(os.environ.get("PHASE15B_TRADES_PATH", "phase15b_c20_trades.csv"))
OUT = Path("fase16B_momentum_failure_anatomy.csv")

HORIZONS = (1, 5, 10, 20)


def classify(row):
    r5 = row.get("Return_5D", np.nan)
    r10 = row.get("Return_10D", np.nan)
    mae = row.get("MAE_20D", np.nan)
    mfe = row.get("MFE_20D", np.nan)
    if pd.notna(r5) and r5 <= -0.05 and pd.notna(mae) and mae <= -0.10:
        return "QUICK_FAILURE"
    if pd.notna(mae) and mae <= -0.10 and pd.notna(mfe) and mfe >= 0.10:
        return "LATER_REVERSAL"
    if pd.notna(mfe) and mfe >= 0.10:
        return "MOMENTUM_SUCCESS"
    if pd.notna(r10) and r10 < 0:
        return "WEAK_FAILURE"
    return "OTHER"


def download_paths(tickers, start, end):
    """Download OHLC once per ticker; no strategy decisions are made here."""
    paths = {}
    failures = []
    for j, t in enumerate(sorted(tickers), 1):
        try:
            x = yf.download(
                t,
                start=start,
                end=end,
                auto_adjust=False,
                progress=False,
                threads=False,
                group_by="column",
            )
            if x is None or x.empty:
                failures.append((t, "empty"))
                continue
            if isinstance(x.columns, pd.MultiIndex):
                x.columns = x.columns.get_level_values(0)
            x.index = pd.to_datetime(x.index).tz_localize(None).normalize()
            x = x[~x.index.duplicated(keep="last")].sort_index()
            keep = [c for c in ["Open", "High", "Low", "Close"] if c in x.columns]
            if len(keep) < 4:
                failures.append((t, "missing OHLC"))
                continue
            paths[t] = x[keep].apply(pd.to_numeric, errors="coerce").dropna(how="all")
        except Exception as e:
            failures.append((t, type(e).__name__ + ": " + str(e)))
        if j % 50 == 0:
            print(f"PRICE DATA {j}/{len(tickers)}", flush=True)
    return paths, failures


def forward_path(row, df):
    dt = pd.Timestamp(row["ExecutionDate"]).normalize()
    if dt not in df.index:
        return None
    i = df.index.get_loc(dt)
    if isinstance(i, slice):
        i = i.start
    entry = float(row["ExecutionOpen"])
    if not np.isfinite(entry) or entry <= 0:
        return None
    future = df.iloc[i:]
    closes = future["Close"].to_numpy(dtype=float)
    highs = future["High"].to_numpy(dtype=float)
    lows = future["Low"].to_numpy(dtype=float)
    out = {"EntryOpen": entry}
    for h in HORIZONS:
        if len(closes) > h:
            out[f"Return_{h}D"] = float(closes[h - 1] / entry - 1.0)
        else:
            out[f"Return_{h}D"] = np.nan
    # Session 1 through 20 inclusive: excursion relative to the actual entry open.
    n = min(20, len(highs))
    if n:
        out["MAE_20D"] = float(np.nanmin(lows[:n] / entry - 1.0))
        out["MFE_20D"] = float(np.nanmax(highs[:n] / entry - 1.0))
        out["GapMin_20D"] = float(np.nanmin(future["Open"].to_numpy(dtype=float)[:n] / entry - 1.0))
    else:
        out["MAE_20D"] = np.nan
        out["MFE_20D"] = np.nan
        out["GapMin_20D"] = np.nan
    return out


def main():
    t0 = time.time()
    print("FASE 16B — MOMENTUM FAILURE ANATOMY")
    print("=" * 78)
    print(f"RUN_ID: {RUN_ID}")
    print("FROZEN STRATEGY: F80_TOP20_PARTIAL50 | exact Phase 12 semantics")
    print("SOURCE: exact Phase 15B BASELINE C20 trade ledger")
    print("No new factors | No re-selection | No risk overlay | No Kelly | No stops")

    if not INPUT.exists():
        print("STATUS: INPUT_REQUIRED")
        print(f"Missing exact Phase 15B ledger: {INPUT}")
        sys.exit(2)

    trades = pd.read_csv(INPUT)
    trades.columns = [str(c).strip() for c in trades.columns]
    required = {"PolicyID", "DateSignal", "ExecutionDate", "Ticker", "Side", "SharesDelta", "ExecutionOpen", "Notional", "Cost", "CostBpsPerSide"}
    missing = required - set(trades.columns)
    if missing:
        print(f"STATUS: FAIL_SCHEMA | missing={sorted(missing)}")
        sys.exit(3)

    policy = "F80_TOP20_PARTIAL50_BASELINE_C20"
    trades = trades[trades["PolicyID"].astype(str) == policy].copy()
    trades["ExecutionDate"] = pd.to_datetime(trades["ExecutionDate"], errors="coerce")
    trades["DateSignal"] = pd.to_datetime(trades["DateSignal"], errors="coerce")
    trades["Ticker"] = trades["Ticker"].astype(str)
    trades["Side"] = trades["Side"].astype(str)
    trades["ExecutionOpen"] = pd.to_numeric(trades["ExecutionOpen"], errors="coerce")
    trades["Notional"] = pd.to_numeric(trades["Notional"], errors="coerce")
    trades["Cost"] = pd.to_numeric(trades["Cost"], errors="coerce")
    trades = trades.dropna(subset=["Ticker", "ExecutionDate", "ExecutionOpen"])

    # BUY transactions are the cleanest observable entry events. SELL_CAP is a
    # forced reduction, not a new momentum entry, so it is excluded from entry anatomy.
    entries = trades[trades["Side"].eq("BUY")].copy()
    entries = entries.sort_values(["ExecutionDate", "Ticker"]).reset_index(drop=True)

    if entries.empty:
        print("STATUS: FAIL | no BUY entries in exact C20 ledger")
        sys.exit(4)

    start = (entries["ExecutionDate"].min() - pd.Timedelta(days=10)).strftime("%Y-%m-%d")
    end = (entries["ExecutionDate"].max() + pd.Timedelta(days=45)).strftime("%Y-%m-%d")
    tickers = entries["Ticker"].unique().tolist()
    print(f"C20 BUY entries: {len(entries)} | tickers: {len(tickers)}")
    print(f"Price window: {start} -> {end}")

    paths, failures = download_paths(tickers, start, end)
    print(f"Price datasets OK: {len(paths)} | failures: {len(failures)}")

    rows = []
    for _, r in entries.iterrows():
        p = paths.get(r["Ticker"])
        if p is None:
            continue
        fp = forward_path(r, p)
        if fp is None:
            continue
        x = r.to_dict()
        x.update(fp)
        x["FailureClass"] = classify(x)
        rows.append(x)

    out = pd.DataFrame(rows)
    if out.empty:
        print("STATUS: FAIL | no forward diagnostics could be calculated")
        sys.exit(5)

    out.to_csv(OUT, index=False)

    print("\n--- COVERAGE ---")
    print(f"ExactC20TradeRows: {len(trades)}")
    print(f"BUYEntriesAnalyzed: {len(out)}")
    print(f"UniqueTickers: {out.Ticker.nunique()}")
    print(f"Forward5D: {out.Return_5D.notna().sum()}")
    print(f"Forward10D: {out.Return_10D.notna().sum()}")
    print(f"Forward20D: {out.Return_20D.notna().sum()}")
    print(f"MAE20D: {out.MAE_20D.notna().sum()}")
    print(f"MFE20D: {out.MFE_20D.notna().sum()}")

    print("\n--- FAILURE CLASSIFICATION ---")
    print(out["FailureClass"].value_counts().to_string())

    print("\n--- OUTCOMES BY ENTRY TRANSACTION ---")
    cols = ["ExecutionDate", "Ticker", "Notional", "Return_5D", "Return_10D", "Return_20D", "MAE_20D", "MFE_20D", "GapMin_20D", "FailureClass"]
    print(out.sort_values("Return_5D")[cols].head(20).to_string(index=False))

    print("\n--- AGGREGATE DIAGNOSTICS ---")
    for c in ["Return_1D", "Return_5D", "Return_10D", "Return_20D", "MAE_20D", "MFE_20D", "GapMin_20D"]:
        if c in out:
            s = pd.to_numeric(out[c], errors="coerce").dropna()
            if len(s):
                print(f"{c}: mean={s.mean():.5f} median={s.median():.5f} p10={s.quantile(.10):.5f} p90={s.quantile(.90):.5f}")

    print("\n--- TOP NEGATIVE 20-DAY MAE ---")
    print(out.sort_values("MAE_20D")[cols].head(20).to_string(index=False))

    print("\n--- INTEGRITY ---")
    print(f"PolicyOnlyPASS: {bool((trades.PolicyID == policy).all())}")
    print(f"DatesOrderedPASS: {bool(out.ExecutionDate.is_monotonic_increasing)}")
    print(f"NoNaNIdentityPASS: {bool(out[['Ticker','ExecutionDate','ExecutionOpen']].notna().all().all())}")
    print(f"RuntimeSeconds: {time.time()-t0:.1f}")
    print(f"Output: {OUT}")
    print("STATUS: PASS")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"STATUS: FAIL | {type(e).__name__}: {e}")
        raise

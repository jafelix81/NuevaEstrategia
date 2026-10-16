"""
FASE 16 — MOMENTUM FAILURE ANATOMY — LONG-TERM MOMENTUM
========================================================
Frozen strategy:
    F80_TOP20_PARTIAL50
    Exact Phase 12 semantics
    BASELINE
    Central cost 20 bps

Purpose:
    Purely diagnostic. No reselection, optimization, risk overlay, Kelly,
    stops, or production logic.

For every portfolio position entered by the frozen strategy, calculate:
    - entry signal date / execution date
    - rank at entry
    - LTM composite score at entry
    - forward 1/5/10/20-session returns
    - MFE/MAE over 5/10/20 sessions
    - maximum adverse overnight gap over 20 sessions
    - realized P&L
    - holding duration
    - whether the position was a quick failure, later reversal,
      or successful momentum continuation.

The script is intentionally diagnostic only. It should reuse the exact
Phase 12 engine/output ledger when available rather than reconstructing
strategy decisions differently.

Expected input:
    PHASE12_LEDGER_PATH environment variable pointing to the exact
    Phase 12 trade ledger CSV produced by the frozen strategy.

If the ledger contains the required fields, no market-data download is
needed for the core diagnosis. If future-return fields are absent, the
script will report that they are unavailable rather than inventing them.
"""

import os
import sys
import json
import math
import traceback
from pathlib import Path

import numpy as np
import pandas as pd

RUN_ID = pd.Timestamp.utcnow().strftime("%Y%m%d_%H%M%S")
POLICY = "F80_TOP20_PARTIAL50_BASELINE_C20"
INITIAL_CAPITAL = 1000.0

# Diagnostic definitions — deliberately fixed before seeing results.
HORIZONS = (1, 5, 10, 20)
FAIL_RETURN_5D = -0.05
FAIL_RETURN_10D = -0.08
MAE_20D_FAIL = -0.10
MFE_20D_WIN = 0.10

def locate_ledger():
    candidates = []
    env = os.environ.get("PHASE12_LEDGER_PATH")
    if env:
        candidates.append(Path(env))
    candidates += [
        Path("phase12_trade_ledger.csv"),
        Path("trade_ledger.csv"),
        Path("trades.csv"),
        Path("outputs/phase12_trade_ledger.csv"),
        Path("outputs/trade_ledger.csv"),
    ]
    for p in candidates:
        if p.exists():
            return p
    return None

def norm_cols(df):
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    return df

def pick(df, names):
    for n in names:
        if n in df.columns:
            return n
    return None

def numeric(df, col):
    return pd.to_numeric(df[col], errors="coerce") if col else pd.Series(np.nan, index=df.index)

def classify(row):
    r5 = row.get("Return_5D", np.nan)
    r10 = row.get("Return_10D", np.nan)
    mae = row.get("MAE_20D", np.nan)
    mfe = row.get("MFE_20D", np.nan)
    if pd.notna(r5) and r5 <= FAIL_RETURN_5D and pd.notna(mae) and mae <= MAE_20D_FAIL:
        return "QUICK_FAILURE"
    if pd.notna(mae) and mae <= MAE_20D_FAIL and pd.notna(mfe) and mfe >= MFE_20D_WIN:
        return "LATER_REVERSAL"
    if pd.notna(mfe) and mfe >= MFE_20D_WIN:
        return "MOMENTUM_SUCCESS"
    if pd.notna(r10) and r10 < 0:
        return "WEAK_FAILURE"
    return "OTHER"

def main():
    print("FASE 16 — MOMENTUM FAILURE ANATOMY — LONG-TERM MOMENTUM")
    print("=" * 78)
    print(f"RUN_ID: {RUN_ID}")
    print(f"FROZEN STRATEGY: {POLICY} | exact Phase 12 semantics")
    print("No new factors | No re-selection | No risk overlay | No Kelly | No stops")
    print("Diagnostic attribution only")

    ledger = locate_ledger()
    if ledger is None:
        print("")
        print("STATUS: INPUT_REQUIRED")
        print("No Phase 12 trade ledger CSV was found.")
        print("Set PHASE12_LEDGER_PATH to the exact Phase 12 trade-ledger CSV.")
        sys.exit(2)

    print(f"Ledger: {ledger}")
    df = norm_cols(pd.read_csv(ledger))
    print(f"LedgerRows: {len(df)}")
    print(f"LedgerColumns: {len(df.columns)}")

    policy_col = pick(df, ["PolicyID", "Policy", "RiskPolicy"])
    if policy_col:
        df = df[df[policy_col].astype(str) == POLICY].copy()

    ticker_col = pick(df, ["Ticker", "ticker", "Symbol"])
    signal_col = pick(df, ["DateSignal", "SignalDate", "Signal_Date"])
    exec_col = pick(df, ["ExecutionDate", "EntryDate", "Date"])
    side_col = pick(df, ["Side", "Action"])
    entry_price_col = pick(df, ["EntryPrice", "PriceEntry", "Entry_Price"])
    exit_price_col = pick(df, ["ExitPrice", "PriceExit", "Exit_Price"])
    rank_col = pick(df, ["Rank", "EntryRank", "RankAtEntry", "TargetRank"])
    score_col = pick(df, ["LTMScore", "CompositeScore", "Score", "SignalScore"])

    required = {"Ticker": ticker_col, "ExecutionDate": exec_col}
    missing = [k for k,v in required.items() if v is None]
    if missing:
        print(f"STATUS: INPUT_SCHEMA_INSUFFICIENT | missing={missing}")
        print("Available columns:")
        print(list(df.columns))
        sys.exit(3)

    df["_Ticker"] = df[ticker_col].astype(str)
    df["_EntryDate"] = pd.to_datetime(df[exec_col], errors="coerce")
    if signal_col:
        df["_SignalDate"] = pd.to_datetime(df[signal_col], errors="coerce")
    else:
        df["_SignalDate"] = pd.NaT

    # Normalize optional numerical fields.
    df["_EntryPrice"] = numeric(df, entry_price_col)
    df["_ExitPrice"] = numeric(df, exit_price_col)
    df["_Rank"] = numeric(df, rank_col)
    df["_Score"] = numeric(df, score_col)

    # If the ledger is trade-level and contains explicit entry records, retain
    # entries only. Otherwise preserve all rows and report that classification
    # is limited by the source schema.
    if side_col:
        s = df[side_col].astype(str).str.upper()
        entry_mask = s.str.contains("BUY|ENTRY|ADD", regex=True, na=False)
        if entry_mask.any():
            df = df.loc[entry_mask].copy()

    df = df.dropna(subset=["_Ticker", "_EntryDate"]).sort_values(
        ["_EntryDate", "_Ticker"]
    ).reset_index(drop=True)

    print(f"EntryRowsAnalyzed: {len(df)}")
    print(f"UniqueTickers: {df['_Ticker'].nunique()}")
    print(f"FirstEntryDate: {df['_EntryDate'].min()}")
    print(f"LastEntryDate: {df['_EntryDate'].max()}")

    # Detect whether forward-return / excursion fields already exist.
    # We do not fabricate them.
    aliases = {}
    for h in HORIZONS:
        aliases[f"Return_{h}D"] = pick(df, [
            f"Return_{h}D", f"ForwardReturn{h}", f"Forward_{h}",
            f"Return{h}D", f"R{h}Forward"
        ])
    aliases["MAE_20D"] = pick(df, ["MAE_20D", "MAE20", "MaxAdverseExcursion20"])
    aliases["MFE_20D"] = pick(df, ["MFE_20D", "MFE20", "MaxFavorableExcursion20"])
    aliases["GapMin_20D"] = pick(df, ["GapMin_20D", "MinOvernightGap20", "WorstGap20"])

    for out, src in aliases.items():
        if src:
            df[out] = numeric(df, src)
        else:
            df[out] = np.nan

    available = {k:v for k,v in aliases.items() if v}
    print(f"ForwardFieldsAvailable: {list(available.keys())}")

    # Optional realized P&L.
    pnl_col = pick(df, ["NetPnL", "PnL", "Net_PnL"])
    if pnl_col:
        df["NetPnL"] = numeric(df, pnl_col)
    else:
        df["NetPnL"] = np.nan

    # Holding duration if explicit exit date exists.
    exit_date_col = pick(df, ["ExitDate", "DateExit"])
    if exit_date_col:
        df["HoldingDays"] = (
            pd.to_datetime(df[exit_date_col], errors="coerce") - df["_EntryDate"]
        ).dt.days
    else:
        df["HoldingDays"] = np.nan

    df["FailureClass"] = df.apply(classify, axis=1)

    print("")
    print("--- DATA AVAILABILITY ---")
    for c in ["Return_1D","Return_5D","Return_10D","Return_20D","MAE_20D","MFE_20D","GapMin_20D","NetPnL","HoldingDays"]:
        print(f"{c}: {int(df[c].notna().sum())}/{len(df)}")

    print("")
    print("--- FAILURE ANATOMY ---")
    if df["FailureClass"].notna().any():
        print(df["FailureClass"].value_counts(dropna=False).to_string())

    # Rank/score diagnostics are descriptive only.
    for label, col in [("EntryRank","_Rank"),("LTMScore","_Score")]:
        x = df[col].dropna()
        if len(x):
            print(f"{label}: mean={x.mean():.6f} median={x.median():.6f} "
                  f"p10={x.quantile(.10):.6f} p90={x.quantile(.90):.6f}")

    # Top failures, only when forward metrics exist.
    if df["MAE_20D"].notna().any():
        cols = ["_EntryDate","_Ticker","_Rank","_Score","Return_5D",
                "Return_10D","Return_20D","MAE_20D","MFE_20D",
                "GapMin_20D","NetPnL","FailureClass"]
        cols = [c for c in cols if c in df.columns]
        print("")
        print("--- 20 WORST MAE ENTRIES ---")
        print(df.sort_values("MAE_20D", ascending=True)[cols].head(20).to_string(index=False))

    if df["Return_5D"].notna().any():
        cols = ["_EntryDate","_Ticker","_Rank","_Score","Return_5D",
                "Return_10D","Return_20D","MAE_20D","MFE_20D",
                "GapMin_20D","FailureClass"]
        print("")
        print("--- 20 WORST 5-DAY OUTCOMES ---")
        print(df.sort_values("Return_5D", ascending=True)[cols].head(20).to_string(index=False))

    # Save diagnostic table without changing strategy outputs.
    out = Path("fase16_entry_anatomy.csv")
    df.to_csv(out, index=False)

    print("")
    print("--- INTEGRITY ---")
    print(f"UniqueEntryDates: {df['_EntryDate'].nunique()}")
    print(f"RowsWithTicker: {int(df['_Ticker'].notna().sum())}")
    print(f"NoNaNCoreIdentityPASS: {bool(df['_Ticker'].notna().all() and df['_EntryDate'].notna().all())}")
    print(f"Output: {out}")
    print("")
    if not available:
        print("STATUS: PASS_DIAGNOSTIC_FRAMEWORK | FORWARD_METRICS_NOT_PRESENT_IN_LEDGER")
    else:
        print("STATUS: PASS")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("STATUS: FAIL")
        print(type(e).__name__, str(e))
        traceback.print_exc()
        sys.exit(1)

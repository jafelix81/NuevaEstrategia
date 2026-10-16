"""
FASE 16B — MOMENTUM FAILURE ANATOMY
====================================
Frozen strategy:
    F80_TOP20_PARTIAL50
    Exact Phase 12 semantics
    BASELINE
    Central cost 20 bps

IMPORTANT:
This phase is diagnostic only. It does not select, optimize, or modify
the strategy.

Input:
    PHASE15B_TRADES_PATH
must point to the trade-level CSV exported by the exact Phase 15B engine.

The workflow should first run Phase 15B (the exact frozen engine), export
its C20 trade ledger, and then run this script against that ledger.

Expected trade-level fields (aliases accepted):
    Ticker
    DateSignal / SignalDate
    ExecutionDate / EntryDate
    ExitDate (if available)
    EntryPrice
    ExitPrice
    NetPnL
    OvernightPnL
    IntradayPnL
    TransactionCost
    Rank / EntryRank
    LTMScore / CompositeScore

Optional forward fields are accepted but never fabricated.
"""

import os
import sys
import traceback
from pathlib import Path
import pandas as pd
import numpy as np

RUN_ID = pd.Timestamp.now("UTC").strftime("%Y%m%d_%H%M%S")
POLICY = "F80_TOP20_PARTIAL50_BASELINE_C20"

HORIZONS = (1, 5, 10, 20)
FAIL_RETURN_5D = -0.05
FAIL_RETURN_10D = -0.08
MAE_20D_FAIL = -0.10
MFE_20D_WIN = 0.10

def find_input():
    env = os.environ.get("PHASE15B_TRADES_PATH")
    candidates = []
    if env:
        candidates.append(Path(env))
    candidates += [
        Path("phase15b_c20_trades.csv"),
        Path("phase15b_trades_c20.csv"),
        Path("fase15b_c20_trades.csv"),
        Path("outputs/phase15b_c20_trades.csv"),
        Path("outputs/phase15b_trades_c20.csv"),
    ]
    for p in candidates:
        if p.exists():
            return p
    return None

def pick(df, names):
    for n in names:
        if n in df.columns:
            return n
    return None

def num(df, col):
    if col is None:
        return pd.Series(np.nan, index=df.index)
    return pd.to_numeric(df[col], errors="coerce")

def classify(row):
    r5, r10 = row["Return_5D"], row["Return_10D"]
    mae, mfe = row["MAE_20D"], row["MFE_20D"]
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
    print("FASE 16B — MOMENTUM FAILURE ANATOMY")
    print("=" * 78)
    print(f"RUN_ID: {RUN_ID}")
    print(f"FROZEN STRATEGY: {POLICY} | exact Phase 12 semantics")
    print("No new factors | No re-selection | No risk overlay | No Kelly | No stops")
    print("Diagnostic attribution only")

    src = find_input()
    if src is None:
        print("")
        print("STATUS: INPUT_REQUIRED")
        print("Phase 15B C20 trade ledger not found.")
        print("Set PHASE15B_TRADES_PATH to the trade-level CSV exported by Phase 15B.")
        sys.exit(2)

    print(f"INPUT: {src}")
    df = pd.read_csv(src)
    df.columns = [str(c).strip() for c in df.columns]
    print(f"RowsRead: {len(df)}")
    print(f"ColumnsRead: {len(df.columns)}")

    policy_col = pick(df, ["PolicyID", "Policy", "RiskPolicy"])
    if policy_col:
        df = df[df[policy_col].astype(str) == POLICY].copy()

    ticker = pick(df, ["Ticker", "ticker", "Symbol"])
    entry = pick(df, ["ExecutionDate", "EntryDate", "DateEntry", "Date"])
    signal = pick(df, ["DateSignal", "SignalDate", "Signal_Date"])
    exitd = pick(df, ["ExitDate", "DateExit"])
    side = pick(df, ["Side", "Action"])

    if ticker is None or entry is None:
        print("STATUS: FAIL_SCHEMA")
        print("Required trade identity fields missing.")
        print(list(df.columns))
        sys.exit(3)

    # If the source contains entry and exit rows, retain entry rows.
    if side:
        s = df[side].astype(str).str.upper()
        mask = s.str.contains("BUY|ENTRY|ADD", regex=True, na=False)
        if mask.any():
            df = df.loc[mask].copy()

    df["Ticker"] = df[ticker].astype(str)
    df["EntryDate"] = pd.to_datetime(df[entry], errors="coerce")
    df["SignalDate"] = pd.to_datetime(df[signal], errors="coerce") if signal else pd.NaT
    df["ExitDate"] = pd.to_datetime(df[exitd], errors="coerce") if exitd else pd.NaT

    aliases = {
        "EntryPrice": ["EntryPrice","PriceEntry","Entry_Price"],
        "ExitPrice": ["ExitPrice","PriceExit","Exit_Price"],
        "NetPnL": ["NetPnL","PnL","Net_PnL"],
        "OvernightPnL": ["OvernightPnL","Overnight_PnL"],
        "IntradayPnL": ["IntradayPnL","Intraday_PnL"],
        "TransactionCost": ["TransactionCost","Cost","Transaction_Cost"],
        "Rank": ["Rank","EntryRank","RankAtEntry","TargetRank"],
        "LTMScore": ["LTMScore","CompositeScore","Score","SignalScore"],
        "Return_1D": ["Return_1D","ForwardReturn1","Forward_1D"],
        "Return_5D": ["Return_5D","ForwardReturn5","Forward_5D"],
        "Return_10D": ["Return_10D","ForwardReturn10","Forward_10D"],
        "Return_20D": ["Return_20D","ForwardReturn20","Forward_20D"],
        "MAE_20D": ["MAE_20D","MAE20","MaxAdverseExcursion20"],
        "MFE_20D": ["MFE_20D","MFE20","MaxFavorableExcursion20"],
        "GapMin_20D": ["GapMin_20D","MinOvernightGap20","WorstGap20"],
    }

    for out, names in aliases.items():
        col = pick(df, names)
        df[out] = num(df, col)

    df = df.dropna(subset=["Ticker","EntryDate"]).sort_values(
        ["EntryDate","Ticker"]
    ).reset_index(drop=True)

    if df["ExitDate"].notna().any():
        df["HoldingCalendarDays"] = (df["ExitDate"] - df["EntryDate"]).dt.days
    else:
        df["HoldingCalendarDays"] = np.nan

    df["FailureClass"] = df.apply(classify, axis=1)

    print(f"EntryRowsAnalyzed: {len(df)}")
    print(f"UniqueTickers: {df['Ticker'].nunique()}")
    print(f"FirstEntryDate: {df['EntryDate'].min()}")
    print(f"LastEntryDate: {df['EntryDate'].max()}")

    print("")
    print("--- FIELD COVERAGE ---")
    fields = [
        "EntryPrice","ExitPrice","NetPnL","OvernightPnL","IntradayPnL",
        "TransactionCost","Rank","LTMScore","Return_1D","Return_5D",
        "Return_10D","Return_20D","MAE_20D","MFE_20D","GapMin_20D",
        "HoldingCalendarDays"
    ]
    for c in fields:
        print(f"{c}: {int(df[c].notna().sum())}/{len(df)}")

    print("")
    print("--- FAILURE CLASSIFICATION ---")
    print(df["FailureClass"].value_counts(dropna=False).to_string())

    print("")
    print("--- ENTRY RANK / SCORE ---")
    for label in ["Rank","LTMScore"]:
        x = df[label].dropna()
        if len(x):
            print(
                f"{label}: mean={x.mean():.6f} median={x.median():.6f} "
                f"p10={x.quantile(.10):.6f} p90={x.quantile(.90):.6f}"
            )

    if df["MAE_20D"].notna().any():
        cols = [
            "EntryDate","Ticker","Rank","LTMScore","Return_5D","Return_10D",
            "Return_20D","MAE_20D","MFE_20D","GapMin_20D","NetPnL","FailureClass"
        ]
        print("")
        print("--- WORST 20 MAE ENTRIES ---")
        print(df.sort_values("MAE_20D")[cols].head(20).to_string(index=False))

    if df["Return_5D"].notna().any():
        cols = [
            "EntryDate","Ticker","Rank","LTMScore","Return_5D","Return_10D",
            "Return_20D","MAE_20D","MFE_20D","GapMin_20D","FailureClass"
        ]
        print("")
        print("--- WORST 20 FIVE-DAY OUTCOMES ---")
        print(df.sort_values("Return_5D")[cols].head(20).to_string(index=False))

    if df["NetPnL"].notna().any():
        print("")
        print("--- P&L BY FAILURE CLASS ---")
        print(
            df.groupby("FailureClass", dropna=False)["NetPnL"]
              .agg(["count","sum","mean","median"])
              .sort_values("sum")
              .to_string()
        )

    out = Path("fase16B_entry_anatomy_C20.csv")
    df.to_csv(out, index=False)

    print("")
    print("--- INTEGRITY ---")
    print(f"Rows: {len(df)}")
    print(f"UniqueDates: {df['EntryDate'].nunique()}")
    print(f"UniqueTickers: {df['Ticker'].nunique()}")
    print(f"IdentityPASS: {bool(df['Ticker'].notna().all() and df['EntryDate'].notna().all())}")
    print(f"Output: {out}")

    forward_available = any(df[c].notna().any() for c in
                            ["Return_1D","Return_5D","Return_10D","Return_20D",
                             "MAE_20D","MFE_20D","GapMin_20D"])
    if forward_available:
        print("STATUS: PASS")
    else:
        print("STATUS: PASS_DIAGNOSTIC_LEDGER_ONLY | FORWARD_EXCURSION_FIELDS_NOT_PRESENT")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("STATUS: FAIL")
        print(type(e).__name__, str(e))
        traceback.print_exc()
        sys.exit(1)

#!/usr/bin/env python3
"""Phase 427 — temporal concentration audit of the Phase 426 matched-exposure result.

Reads only the paired daily-return CSV from the Phase 426 GitHub Actions artifact.
No new prices, universe changes, parameter search, or trading simulation occur here.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import binomtest

def hac_se(values: np.ndarray, max_lag: int) -> float:
    x = np.asarray(values, dtype=float)
    x = x[np.isfinite(x)]
    n = len(x)
    if n < max_lag + 5:
        raise ValueError(f"n={n} is too small for requested HAC lag {max_lag}")
    e = x - x.mean()
    lrv = float(np.dot(e, e) / n)
    for lag in range(1, max_lag + 1):
        gamma = float(np.dot(e[lag:], e[:-lag]) / n)
        weight = 1.0 - lag / (max_lag + 1.0)
        lrv += 2.0 * weight * gamma
    return math.sqrt(max(lrv, 0.0) / n)

def safe_float(x):
    return float(x) if np.isfinite(x) else None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="Phase426 paired_exposure_matched_excess_C20.csv")
    ap.add_argument("--output", default="phase427_output/phase427_report.json")
    args = ap.parse_args()

    src = Path(args.input)
    raw = src.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    df = pd.read_csv(src)
    required = {"Date", "DailyReturn_ltm", "DailyReturn_mom", "cycle_id"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"missing required columns: {sorted(missing)}")
    df["Date"] = pd.to_datetime(df["Date"], errors="raise")
    df = df.sort_values("Date").reset_index(drop=True)
    if df["Date"].duplicated().any():
        raise ValueError("duplicate dates")
    if len(df) != 721:
        raise ValueError(f"expected the exact Phase426 OOS window of 721 rows; got {len(df)}")
    if not (df["DailyReturn_ltm"].gt(-1).all() and df["DailyReturn_mom"].gt(-1).all()):
        raise ValueError("daily return <= -100% encountered")

    df["daily_simple_excess"] = df["DailyReturn_mom"] - df["DailyReturn_ltm"]
    df["daily_log_excess"] = np.log1p(df["DailyReturn_mom"]) - np.log1p(df["DailyReturn_ltm"])
    df["year"] = df["Date"].dt.year

    overall_mean = float(df["daily_simple_excess"].mean())
    total_log = float(df["daily_log_excess"].sum())
    relative_multiple = float(math.exp(total_log))
    years = []
    for year, g in df.groupby("year"):
        x = g["daily_simple_excess"].to_numpy(float)
        se20 = hac_se(x, 20)
        se80 = hac_se(x, 80)
        years.append({
            "year": int(year),
            "n": int(len(g)),
            "mean_daily_excess_bps": float(x.mean() * 10000.0),
            "hac20_se_bps": float(se20 * 10000.0),
            "hac20_t": float(x.mean() / se20),
            "hac80_se_bps": float(se80 * 10000.0),
            "hac80_t": float(x.mean() / se80),
            "hac80_ci95_bps": [
                float((x.mean() - 1.96 * se80) * 10000.0),
                float((x.mean() + 1.96 * se80) * 10000.0),
            ],
            "cumulative_log_excess": float(g["daily_log_excess"].sum()),
        })

    cycles = []
    for cycle_id, g in df.groupby("cycle_id", sort=True):
        ltm_mult = float(np.prod(1.0 + g["DailyReturn_ltm"].to_numpy(float)))
        mom_mult = float(np.prod(1.0 + g["DailyReturn_mom"].to_numpy(float)))
        log_excess = float(g["daily_log_excess"].sum())
        cycles.append({
            "cycle_id": int(cycle_id),
            "start": str(g["Date"].min().date()),
            "end": str(g["Date"].max().date()),
            "days": int(len(g)),
            "ltm_multiple": ltm_mult,
            "mom120_multiple": mom_mult,
            "compound_difference": float(mom_mult - ltm_mult),
            "log_excess": log_excess,
            "positive": bool(log_excess > 0.0),
            "boundary_partial": bool(len(g) < 80),
        })
    positive_cycles = sum(c["positive"] for c in cycles)
    sign_p = float(binomtest(positive_cycles, len(cycles), 0.5, alternative="greater").pvalue)
    full_cycles = [c for c in cycles if c["days"] == 80]
    partial_cycles = [c for c in cycles if c["days"] < 80]

    year_map = {x["year"]: x for x in years}
    first_two_log = sum(year_map[y]["cumulative_log_excess"] for y in (2024, 2025) if y in year_map)
    share_2024_25 = first_two_log / total_log if total_log != 0 else None
    share_2026 = year_map[2026]["cumulative_log_excess"] / total_log if 2026 in year_map and total_log != 0 else None

    report = {
        "phase": 427,
        "input_file": src.name,
        "input_sha256": digest,
        "source_artifact_run": 43789923762,
        "source_artifact_id": 14191029663,
        "source_metric": "paired exposure-matched C20 daily portfolio returns; MOM120 minus frozen LTM",
        "date_start": str(df["Date"].min().date()),
        "date_end": str(df["Date"].max().date()),
        "n_daily_observations": int(len(df)),
        "overall": {
            "mean_daily_simple_excess_bps": float(overall_mean * 10000.0),
            "cumulative_log_excess": total_log,
            "relative_wealth_multiple_mom120_over_ltm": relative_multiple,
            "relative_wealth_gain_pct": float((relative_multiple - 1.0) * 100.0),
        },
        "calendar_years": years,
        "cycles": cycles,
        "cycle_summary": {
            "n_cycles": int(len(cycles)),
            "positive_cycles": int(positive_cycles),
            "positive_cycle_fraction": float(positive_cycles / len(cycles)),
            "one_sided_exact_sign_test_p": sign_p,
            "n_full_80_session_cycles": int(len(full_cycles)),
            "positive_full_80_session_cycles": int(sum(c["positive"] for c in full_cycles)),
            "n_boundary_partial_cycles": int(len(partial_cycles)),
            "partial_cycles_all_negative": bool(partial_cycles and all(not c["positive"] for c in partial_cycles)),
        },
        "concentration": {
            "2024_2025_share_of_total_cumulative_log_excess": safe_float(share_2024_25),
            "2026_share_of_total_cumulative_log_excess": safe_float(share_2026),
            "2026_mean_excess_is_statistically_clear_at_hac80": bool(
                year_map.get(2026, {}).get("hac80_ci95_bps", [0, 0])[0] > 0
            ),
        },
        "decision": "PROMISING_BUT_TEMPORALLY_CONCENTRATED_NO_PROMOTION",
        "limitations": [
            "The 2024+ window was already examined in Phase 29/30/426 and is not a fresh holdout.",
            "The 335-name universe and Yahoo price history are not point-in-time or survivorship-free.",
            "Only ten OOS rebalance-cycle fragments are available; the exact sign test is descriptive and cycles are not guaranteed independent.",
            "The two boundary partial cycles are negative; the latest 75-session partial cycle underperformed.",
            "2026 year-to-date paired excess is not statistically distinguishable from zero under HAC lag 80.",
            "MOM120 is a momentum reweighting already contained in the LTM composite, not a Smart Money source.",
        ],
        "no_new_market_data": True,
        "no_parameter_search": True,
        "no_holdout_used": True,
        "f80_changed": False,
        "production_changed": False,
    }
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True, allow_nan=False))
    print("PHASE427_STATUS=PASS")

if __name__ == "__main__":
    main()

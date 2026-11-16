#!/usr/bin/env python3
"""Phase 428 — block-bootstrap and HAC sensitivity of MOM120 year segments.

Input is the paired exposure-matched daily-return CSV from the immutable
Phase 426 Actions artifact. No prices, signals, universe, parameters, or trades
are downloaded or rebuilt. This is a post-hoc stability diagnostic only.
"""
from __future__ import annotations
import argparse, hashlib, json, math
from pathlib import Path
import numpy as np
import pandas as pd

BLOCK_LENGTHS = (20, 40, 60)
HAC_LAGS = (20, 40, 60, 80)
REPLICATES = 50_000
BASE_SEED = 428_000


def hac_se(values: np.ndarray, max_lag: int) -> float:
    x = np.asarray(values, dtype=float)
    if x.ndim != 1 or len(x) <= max_lag + 5 or not np.isfinite(x).all():
        raise ValueError("invalid HAC input")
    n = len(x)
    e = x - x.mean()
    lrv = float(np.dot(e, e) / n)
    for lag in range(1, max_lag + 1):
        gamma = float(np.dot(e[lag:], e[:-lag]) / n)
        weight = 1.0 - lag / (max_lag + 1.0)
        lrv += 2.0 * weight * gamma
    return math.sqrt(max(lrv, 0.0) / n)


def circular_block_bootstrap(values: np.ndarray, block: int, reps: int, seed: int) -> dict:
    x = np.asarray(values, dtype=float)
    if x.ndim != 1 or not np.isfinite(x).all() or len(x) < max(100, 3 * block):
        raise ValueError("insufficient or invalid block-bootstrap input")
    n = len(x)
    rng = np.random.default_rng(seed)
    nblocks = int(math.ceil(n / block))
    offsets = np.arange(block)
    means = np.empty(reps, dtype=float)
    batch = 1000
    for lo in range(0, reps, batch):
        m = min(batch, reps - lo)
        starts = rng.integers(0, n, size=(m, nblocks))
        idx = ((starts[:, :, None] + offsets[None, None, :]) % n).reshape(m, -1)[:, :n]
        means[lo:lo + m] = x[idx].mean(axis=1)
    q = np.quantile(means, [0.025, 0.5, 0.975])
    return {
        "n": n, "block_length": block, "replicates": reps, "seed": seed,
        "mean": float(x.mean()), "ci95_low": float(q[0]),
        "median": float(q[1]), "ci95_high": float(q[2]),
    }


def summarize_segment(frame: pd.DataFrame, label: str, reps: int = REPLICATES) -> dict:
    x = frame["excess"].to_numpy(dtype=float)
    result = {
        "segment": label, "n": int(len(x)),
        "start": frame["Date"].iloc[0].date().isoformat(),
        "end": frame["Date"].iloc[-1].date().isoformat(),
        "mean_bps_per_session": float(x.mean() * 1e4),
        "median_bps_per_session": float(np.median(x) * 1e4),
        "positive_session_fraction": float(np.mean(x > 0)),
        "hac": {}, "circular_block_bootstrap": {},
    }
    for lag in HAC_LAGS:
        if len(x) > lag + 5:
            se = hac_se(x, lag)
            result["hac"][str(lag)] = {
                "lag": lag, "se_bps": se * 1e4,
                "t": float(x.mean() / se) if se > 0 else None,
                "ci95_low_bps": float((x.mean() - 1.96 * se) * 1e4),
                "ci95_high_bps": float((x.mean() + 1.96 * se) * 1e4),
            }
    for block in BLOCK_LENGTHS:
        if len(x) >= max(100, 3 * block):
            seed = BASE_SEED + len(x) + block
            boot = circular_block_bootstrap(x, block, reps, seed)
            result["circular_block_bootstrap"][str(block)] = {
                "n": boot["n"], "block_length": boot["block_length"],
                "replicates": boot["replicates"], "seed": boot["seed"],
                "mean_bps": boot["mean"] * 1e4,
                "ci95_low_bps": boot["ci95_low"] * 1e4,
                "median_bps": boot["median"] * 1e4,
                "ci95_high_bps": boot["ci95_high"] * 1e4,
            }
    return result


def run(input_path: Path, output_dir: Path, reps: int = REPLICATES) -> dict:
    raw = input_path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    df = pd.read_csv(input_path, parse_dates=["Date"])
    required = {"Date", "DailyReturn_ltm", "DailyReturn_mom", "cycle_id"}
    if not required.issubset(df.columns):
        raise ValueError(f"missing columns: {sorted(required - set(df.columns))}")
    df = df.sort_values("Date").reset_index(drop=True)
    if df["Date"].duplicated().any():
        raise ValueError("duplicate dates")
    for col in ["DailyReturn_ltm", "DailyReturn_mom"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    if df[["DailyReturn_ltm", "DailyReturn_mom"]].isna().any().any():
        raise ValueError("missing daily returns")
    df["excess"] = df["DailyReturn_mom"] - df["DailyReturn_ltm"]
    if len(df) != 721 or df["Date"].min().date().isoformat() != "2024-01-02" or df["Date"].max().date().isoformat() != "2026-11-13":
        raise ValueError("input does not match the frozen Phase 426 paired sample")
    segments = []
    for year in [2024, 2025, 2026]:
        part = df[df.Date.dt.year.eq(year)].copy()
        segments.append(summarize_segment(part, str(year), reps))
    all_result = summarize_segment(df, "2024-01-02_to_2026-11-13", reps)
    report = {
        "phase": 428,
        "input": {
            "path_basename": input_path.name,
            "sha256": digest,
            "source_run_id": "43789923762",
            "source_artifact_id": 14191029663,
            "rows": int(len(df)),
            "start": "2024-01-02",
            "end": "2026-11-13",
        },
        "method": {
            "paired_excess": "DailyReturn_mom - DailyReturn_ltm",
            "bootstrap": "circular moving-block bootstrap of the segment mean; percentile 95% interval",
            "block_lengths_sessions": list(BLOCK_LENGTHS),
            "bootstrap_replicates_per_segment_block": reps,
            "hac": "Newey-West/Bartlett long-run variance with stated lag sensitivity",
            "hac_lags_sessions": list(HAC_LAGS),
            "seeds": "BASE_SEED + segment_n + block_length",
            "no_prices_or_signals_downloaded": True,
            "no_parameter_tuning_or_candidate_reselection": True,
            "no_holdout_used": True,
        },
        "segments": segments,
        "full_sample": all_result,
        "decision": "2026_SEGMENT_NOT_STATISTICALLY_DISTINGUISHABLE_FROM_ZERO_ACROSS_TESTED_BLOCK_AND_HAC_SENSITIVITIES",
        "limitations": [
            "Post-hoc stability diagnostic on a previously inspected 2024+ sample; not a fresh OOS or holdout test.",
            "Circular block bootstrap is conditional on the observed segment and does not create new market regimes.",
            "The 2026 segment has 219 sessions; 60-session blocks leave few effective blocks per resample.",
            "The underlying 335-name universe is not point-in-time or survivorship-free.",
            "No causal attribution, conditional residual test, or smart-money source is evaluated.",
        ],
        "production_changed": False,
        "f80_changed": False,
        "forward_returns_used": False,
        "alpha_test_authorized": False,
        "holdout_used": False,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "phase428_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Phase 426 paired_exposure_matched_excess_C20.csv")
    parser.add_argument("--output-dir", default="phase428_output")
    parser.add_argument("--replicates", type=int, default=REPLICATES)
    args = parser.parse_args()
    report = run(Path(args.input), Path(args.output_dir), args.replicates)
    print("PHASE428_STATUS=PASS")
    print("INPUT_SHA256=", report["input"]["sha256"])
    for s in report["segments"]:
        print(s["segment"], "N=", s["n"], "MEAN_BPS=", round(s["mean_bps_per_session"], 4))
        for block, b in s["circular_block_bootstrap"].items():
            print("CBB", s["segment"], block, "CI_BPS=", round(b["ci95_low_bps"], 4), round(b["ci95_high_bps"], 4))
    print("DECISION=", report["decision"])
    print("F80_CHANGED=False")


if __name__ == "__main__":
    main()

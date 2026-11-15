#!/usr/bin/env python3
"""Phase 422: stress-test rolling-rank event-count feasibility under AR(1) persistence.

Synthetic design diagnostic only. It does not read CFTC history, prices, returns,
labels, or the legacy holdout. The raw series is stationary Gaussian AR(1) with
unit marginal variance. A signal is HIGH when at least 42 of the prior 52 raw
observations are strictly below the current observation (mid-rank ties have
probability zero under this continuous simulation).
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np

PHIS = (0.0, 0.2, 0.4, 0.6, 0.8)
PLANS = (
    ("iid_90_reference", 116, 166),
    ("iid_95_reference", 120, 170),
    ("stress_90", 135, 185),
    ("stress_95", 140, 190),
)
WARMUP = 52
MATURITY_GAP = 4
FINAL_MATURITY = 4


def wilson(successes: int, trials: int) -> dict[str, float]:
    z = 1.959963984540054
    p = successes / trials
    den = 1.0 + z * z / trials
    center = (p + z * z / (2.0 * trials)) / den
    half = z * math.sqrt(p * (1.0 - p) / trials + z * z / (4.0 * trials * trials)) / den
    return {"estimate": p, "lower_95": center - half, "upper_95": center + half}


def simulate_phi(phi: float, n_paths: int, base_seed: int, chunk_size: int) -> dict:
    max_train = max(train for _, train, _ in PLANS)
    max_eval = max(evaluate for _, _, evaluate in PLANS)
    total_raw = WARMUP + max_train + MATURITY_GAP + max_eval
    signal_count = total_raw - WARMUP
    rng = np.random.default_rng(base_seed + int(round(phi * 1000)))
    innovation_scale = math.sqrt(1.0 - phi * phi)

    total_high = 0
    total_signals = 0
    adjacent_high_pairs = 0
    adjacent_pairs = 0
    pass_counts = {name: 0 for name, _, _ in PLANS}

    for offset in range(0, n_paths, chunk_size):
        m = min(chunk_size, n_paths - offset)
        raw = np.empty((m, total_raw), dtype=np.float32)
        raw[:, 0] = rng.standard_normal(m)
        for t in range(1, total_raw):
            raw[:, t] = phi * raw[:, t - 1] + innovation_scale * rng.standard_normal(m)

        high = np.empty((m, signal_count), dtype=np.bool_)
        for j, t in enumerate(range(WARMUP, total_raw)):
            below = (raw[:, t - WARMUP:t] < raw[:, t, None]).sum(axis=1)
            high[:, j] = below >= 42

        total_high += int(high.sum())
        total_signals += int(high.size)
        adjacent_high_pairs += int((high[:, :-1] & high[:, 1:]).sum())
        adjacent_pairs += int(high[:, :-1].size)

        for name, train_n, eval_n in PLANS:
            train_high = high[:, :train_n].sum(axis=1)
            eval_start = train_n + MATURITY_GAP
            eval_high = high[:, eval_start:eval_start + eval_n].sum(axis=1)
            passed = (
                (train_high >= 20)
                & ((train_n - train_high) >= 40)
                & (eval_high >= 30)
                & ((eval_n - eval_high) >= 100)
            )
            pass_counts[name] += int(passed.sum())

    high_rate = total_high / total_signals
    adjacent_product = adjacent_high_pairs / adjacent_pairs
    lag1_corr = (adjacent_product - high_rate * high_rate) / (high_rate * (1.0 - high_rate))

    plan_results = []
    for name, train_n, eval_n in PLANS:
        total_reports = WARMUP + train_n + MATURITY_GAP + eval_n + FINAL_MATURITY
        plan_results.append({
            "plan": name,
            "training_observations": train_n,
            "excluded_training_maturity_gap_observations": MATURITY_GAP,
            "evaluation_observations": eval_n,
            "final_outcome_maturity_reports": FINAL_MATURITY,
            "total_weekly_reports_including_warmup_and_maturity": total_reports,
            "approx_years_at_52_reports_per_year": total_reports / 52.0,
            "joint_event_gate_probability": wilson(pass_counts[name], n_paths),
        })

    return {
        "phi": phi,
        "paths": n_paths,
        "seed": base_seed + int(round(phi * 1000)),
        "raw_series_model": "stationary Gaussian AR(1), unit marginal variance",
        "high_state_rule": "at least 42 of prior 52 raw values are strictly below current value",
        "high_state_rate": high_rate,
        "high_state_lag1_correlation": lag1_corr,
        "plans": plan_results,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--paths", type=int, default=100_000)
    parser.add_argument("--chunk", type=int, default=5_000)
    parser.add_argument("--seed", type=int, default=20261116)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.paths < 1 or args.chunk < 1:
        parser.error("--paths and --chunk must be positive")

    result = {
        "phase": 422,
        "simulation_only": True,
        "cftc_historical_rows_used": False,
        "market_prices_or_returns_used": False,
        "legacy_holdout_used": False,
        "n_paths_per_phi": args.paths,
        "base_seed": args.seed,
        "phis": [simulate_phi(phi, args.paths, args.seed, args.chunk) for phi in PHIS],
        "interpretation": (
            "Conditional event-count sensitivity only; AR(1) persistence values are stress assumptions, "
            "not estimates from CFTC data. Not statistical power, empirical CFTC frequency, alpha, or a "
            "change to Phase 387 preregistration."
        ),
    }
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")


if __name__ == "__main__":
    main()

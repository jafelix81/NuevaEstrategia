#!/usr/bin/env python3
"""Phase 421: sensitivity to the four-report outcome-maturity gap.

Synthetic IID continuous inputs only. No CFTC positions, market prices, labels,
or returns are read. The four-report gap is excluded from both event-count
blocks so the simulated joint gate matches the calendar planning convention.
Requires numpy.
"""
from __future__ import annotations

import json
from math import sqrt

import numpy as np

WINDOW = 52
HIGH_RANK_COUNT = 42
N_SIMULATIONS = 200_000
N_POST_WARMUP = 316
SEED = 20261115
CHUNK = 5_000


def wilson(successes: int, trials: int) -> list[float]:
    p = successes / trials
    z = 1.959963984540054
    den = 1 + z * z / trials
    center = (p + z * z / (2 * trials)) / den
    half = z * sqrt(p * (1 - p) / trials + z * z / (4 * trials * trials)) / den
    return [center - half, center + half]


def simulate() -> np.ndarray:
    rng = np.random.default_rng(SEED)
    flags = np.zeros((N_SIMULATIONS, N_POST_WARMUP), dtype=np.uint8)
    done = 0
    while done < N_SIMULATIONS:
        m = min(CHUNK, N_SIMULATIONS - done)
        x = rng.random((m, WINDOW + N_POST_WARMUP))
        block = np.empty((m, N_POST_WARMUP), dtype=np.uint8)
        for t in range(N_POST_WARMUP):
            lower_count = (x[:, t : t + WINDOW] < x[:, t + WINDOW, None]).sum(axis=1)
            block[:, t] = lower_count >= HIGH_RANK_COUNT
        flags[done : done + m] = block
        done += m
    return flags


def block_result(flags: np.ndarray, n_train: int, n_eval: int, gap: int) -> dict:
    eval_start = n_train + gap
    if eval_start + n_eval > flags.shape[1]:
        raise ValueError("requested plan exceeds simulated indicator horizon")
    train = flags[:, :n_train].sum(axis=1)
    evaluation = flags[:, eval_start : eval_start + n_eval].sum(axis=1)
    train_ok = (train >= 20) & ((n_train - train) >= 40)
    evaluation_ok = (evaluation >= 30) & ((n_eval - evaluation) >= 100)
    joint = train_ok & evaluation_ok
    successes = int(joint.sum())
    return {
        "n_train": n_train,
        "maturity_gap_reports_excluded": gap,
        "n_evaluation": n_eval,
        "train_gate_probability": float(train_ok.mean()),
        "evaluation_gate_probability": float(evaluation_ok.mean()),
        "joint_successes": successes,
        "joint_trials": int(len(joint)),
        "joint_probability": float(joint.mean()),
        "joint_wilson_95": wilson(successes, len(joint)),
        "mean_train_high_count": float(train.mean()),
        "mean_evaluation_high_count": float(evaluation.mean()),
    }


def main() -> None:
    flags = simulate()
    marginal = float(flags.mean())
    plans = []
    for n_train, n_eval in ((111, 161), (116, 166), (120, 170)):
        contiguous = block_result(flags, n_train, n_eval, 0)
        row = {"n_train": n_train, "n_evaluation": n_eval, "gap_sensitivity": []}
        for gap in (0, 4, 5):
            result = block_result(flags, n_train, n_eval, gap)
            result["joint_change_vs_no_gap_percentage_points"] = (
                result["joint_probability"] - contiguous["joint_probability"]
            ) * 100
            row["gap_sensitivity"].append(result)
        plans.append(row)

    print(json.dumps({
        "phase": 421,
        "seed": SEED,
        "simulations": N_SIMULATIONS,
        "window": WINDOW,
        "high_rank_count": HIGH_RANK_COUNT,
        "post_warmup_indicators_per_path": N_POST_WARMUP,
        "simulated_marginal_high_probability": marginal,
        "plans": plans,
        "data_policy": "SYNTHETIC_IID_ONLY_NO_CFTC_DATA",
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

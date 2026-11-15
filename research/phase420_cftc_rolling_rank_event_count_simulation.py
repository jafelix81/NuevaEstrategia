#!/usr/bin/env python3
"""Synthetic feasibility simulation for Phase 387's 52-observation rolling rank.

This script uses no CFTC data. It isolates the dependence induced by overlapping
rolling reference windows under IID continuous inputs.
Requires numpy.
"""
from __future__ import annotations

import json
from math import comb, sqrt

import numpy as np

WINDOW = 52
HIGH_RANK_COUNT = 42  # ceil(0.80 * 52); current value is excluded
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


def binomial_tail(n: int, k: int, p: float = 11 / 53) -> float:
    return sum(comb(n, j) * p**j * (1 - p) ** (n - j) for j in range(k, n + 1))


def simulate() -> np.ndarray:
    rng = np.random.default_rng(SEED)
    flags = np.zeros((N_SIMULATIONS, N_POST_WARMUP), dtype=np.uint8)
    done = 0
    while done < N_SIMULATIONS:
        m = min(CHUNK, N_SIMULATIONS - done)
        x = rng.random((m, WINDOW + N_POST_WARMUP))  # float64 continuous reference
        block = np.empty((m, N_POST_WARMUP), dtype=np.uint8)
        for t in range(N_POST_WARMUP):
            lower_count = (x[:, t : t + WINDOW] < x[:, t + WINDOW, None]).sum(axis=1)
            block[:, t] = lower_count >= HIGH_RANK_COUNT
        flags[done : done + m] = block
        done += m
    return flags


def block_result(flags: np.ndarray, n_train: int, n_eval: int) -> dict:
    train = flags[:, :n_train].sum(axis=1)
    evaluation = flags[:, n_train : n_train + n_eval].sum(axis=1)
    train_ok = (train >= 20) & ((n_train - train) >= 40)
    evaluation_ok = (evaluation >= 30) & ((n_eval - evaluation) >= 100)
    joint = train_ok & evaluation_ok
    successes = int(joint.sum())
    return {
        "n_train": n_train,
        "n_evaluation": n_eval,
        "train_probability": float(train_ok.mean()),
        "evaluation_probability": float(evaluation_ok.mean()),
        "joint_successes": successes,
        "joint_trials": int(len(joint)),
        "joint_probability": float(joint.mean()),
        "joint_wilson_95": wilson(successes, len(joint)),
        "binomial_train_high_only": binomial_tail(n_train, 20),
        "binomial_evaluation_high_only": binomial_tail(n_eval, 30),
        "train_nonhigh_gate_failures": int(((n_train - train) < 40).sum()),
        "evaluation_nonhigh_gate_failures": int(((n_eval - evaluation) < 100).sum()),
    }


def main() -> None:
    flags = simulate()
    marginal = float(flags.mean())
    f = flags.astype(np.float64)
    acf = {}
    for lag in (1, 13, 26, 39, 51, 52, 53):
        a, b = f[:, :-lag], f[:, lag:]
        acf[str(lag)] = float(((a - marginal) * (b - marginal)).mean() / (marginal * (1 - marginal)))

    eval150 = flags[:, :150].sum(axis=1)
    eval150_ok = (eval150 >= 30) & ((150 - eval150) >= 100)
    variance150 = float(eval150.var())
    binomial_variance150 = 150 * (11 / 53) * (42 / 53)

    result = {
        "phase": 420,
        "seed": SEED,
        "simulations": N_SIMULATIONS,
        "post_warmup_indicators_per_path": N_POST_WARMUP,
        "window": WINDOW,
        "high_rank_count": HIGH_RANK_COUNT,
        "theoretical_iid_marginal_high_probability": 11 / 53,
        "simulated_marginal_high_probability": marginal,
        "indicator_acf": acf,
        "evaluation_150": {
            "joint_gate_probability": float(eval150_ok.mean()),
            "wilson_95": wilson(int(eval150_ok.sum()), len(eval150_ok)),
            "rolling_count_variance": variance150,
            "independent_binomial_count_variance": binomial_variance150,
            "variance_ratio": variance150 / binomial_variance150,
            "binomial_high_count_gate_probability": binomial_tail(150, 30),
        },
        "consecutive_plans": [
            block_result(flags, 111, 161),
            block_result(flags, 116, 166),
            block_result(flags, 120, 170),
        ],
        "data_policy": "SYNTHETIC_IID_ONLY_NO_CFTC_DATA",
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

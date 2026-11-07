#!/usr/bin/env python3
"""Phase 148 — audit the Phase 29 independent-alpha lab for execution costs and OOS discipline.

This is an artifact-only audit. It does not redownload prices, reselect factors, tune
thresholds, or treat the already inspected 2024+ slice as an untouched holdout.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np

SOURCE_RUN_ID = 40105752275
SOURCE_ARTIFACT_ID = 12565060248
SOURCE_BRANCH = "phase29-independent-alpha-lab"
SOURCE_SHA = "a4fb2a8b4d6d5443605aaf9c04f99184712ce5ce"
SOURCE_ARTIFACT_SHA256 = "85480d28d6d24c8a167c67baee5b3c28c2915e0a3bc3b2eb2f13b490d4167d77"
SOURCE_REPORT_SHA256 = "a935ca2994a1041ad458a76fa203576cdd330e33fc253143879c9491bcc4db65"
SOURCE_INPUT_SHA256 = "dc5516d7c2dcaa308dac21e5b521803bc2159affb53b03d64b65d752aafd528b"

EXPECTED_COUNTS = {
    20: {"discovery": 54, "validation": 36, "final_oos": 33},
    60: {"discovery": 54, "validation": 36, "final_oos": 31},
}
COSTS_BPS_PER_SIDE = (0, 5, 10, 25, 50)
BLOCK_LENGTHS = (1, 3, 6, 9)
BOOTSTRAP_REPS = 20_000
BOOTSTRAP_SEED = 148
SPREAD_COST_MULTIPLIER = 4  # long entry/exit + short entry/exit


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_source(report: dict, report_path: Path) -> None:
    actual_hash = sha256_file(report_path)
    if actual_hash != SOURCE_INPUT_SHA256:
        raise ValueError(f"Phase 148 compact input SHA-256 mismatch: {actual_hash}")
    source = report.get("source", {})
    expected_source = {
        "github_run_id": SOURCE_RUN_ID,
        "artifact_id": SOURCE_ARTIFACT_ID,
        "branch": SOURCE_BRANCH,
        "head_sha": SOURCE_SHA,
        "artifact_sha256": SOURCE_ARTIFACT_SHA256,
        "report_sha256": SOURCE_REPORT_SHA256,
    }
    for key, expected in expected_source.items():
        if source.get(key) != expected:
            raise ValueError(f"Phase 29 source lineage mismatch for {key}")
    if report.get("universe_configured") != 335:
        raise ValueError("Unexpected Phase 29 configured universe")
    if report.get("prices_loaded") != 335 or report.get("data_series") != 334:
        raise ValueError("Unexpected Phase 29 price/data-series counts")
    protocol = report.get("protocol", {})
    if protocol.get("horizons") != [20, 60]:
        raise ValueError("Unexpected Phase 29 horizons")
    if protocol.get("step") != 21 or protocol.get("min_cross_section") != 100:
        raise ValueError("Unexpected Phase 29 sampling protocol")
    if protocol.get("cost_bps_per_side") != 10.0:
        raise ValueError("Unexpected declared Phase 29 cost assumption")
    results = {int(item["horizon"]): item for item in report.get("results", [])}
    if set(results) != {20, 60}:
        raise ValueError("Phase 29 result horizons are incomplete")
    for horizon, stages in EXPECTED_COUNTS.items():
        item = results[horizon]
        if item.get("factor") != "MOM120" or item.get("direction") != 1:
            raise ValueError(f"Unexpected previously selected factor for {horizon}")
        for stage, expected_n in stages.items():
            stage_data = item.get("stages", {}).get(stage, {})
            dates = [str(date) for date in stage_data.get("dates", [])]
            spreads = stage_data.get("spreads", [])
            if len(dates) != expected_n or len(spreads) != expected_n:
                raise ValueError(f"{horizon}/{stage}: expected {expected_n} date/spread pairs")
            if any(not date for date in dates) or len(set(dates)) != len(dates):
                raise ValueError(f"{horizon}/{stage}: missing or duplicate signal dates")
            if dates != sorted(dates):
                raise ValueError(f"{horizon}/{stage}: dates are not chronological")
            if any(not math.isfinite(float(value)) for value in spreads):
                raise ValueError(f"{horizon}/{stage}: non-finite Q10-Q1 spread")
            actual_mean = float(np.mean([float(value) for value in spreads]))
            expected_mean = stage_data.get("mean_d10_d1")
            if expected_mean is None or not math.isclose(
                actual_mean, float(expected_mean), rel_tol=0, abs_tol=1e-10
            ):
                raise ValueError(f"{horizon}/{stage}: aggregate mean does not reconcile")


def circular_block_bootstrap(values, block_length: int, reps: int, seed: int) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    n = len(values)
    if n < 2:
        raise ValueError("At least two observations are required for bootstrap")
    if block_length < 1:
        raise ValueError("Block length must be positive")
    rng = np.random.default_rng(seed)
    blocks_needed = int(math.ceil(n / block_length))
    starts = rng.integers(0, n, size=(reps, blocks_needed))
    offsets = np.arange(block_length)
    indices = (starts[:, :, None] + offsets[None, None, :]) % n
    sampled = values[indices.reshape(reps, -1)[:, :n]]
    return sampled.mean(axis=1)


def leave_one_out_means(values) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    if len(values) < 2:
        raise ValueError("At least two observations are required for LOO")
    return (values.sum() - values) / (len(values) - 1)


def summarize_stage(rows: list[dict], horizon: int, stage: str) -> dict:
    values = np.asarray([float(row["d10_d1"]) for row in rows], dtype=float)
    n = len(values)
    gross_mean = float(values.mean())
    gross_median = float(np.median(values))
    gross_hit_rate = float(np.mean(values > 0))
    loo = leave_one_out_means(values)
    bootstrap_by_block = {}
    bootstrap_means_by_block = {}
    for block in BLOCK_LENGTHS:
        boot = circular_block_bootstrap(
            values,
            block_length=block,
            reps=BOOTSTRAP_REPS,
            seed=BOOTSTRAP_SEED + horizon * 100 + block + len(stage),
        )
        bootstrap_means_by_block[str(block)] = boot
        lo, hi = np.quantile(boot, [0.025, 0.975])
        bootstrap_by_block[str(block)] = {
            "block_length_signal_dates": block,
            "repetitions": BOOTSTRAP_REPS,
            "gross_ci95": [float(lo), float(hi)],
            "gross_probability_mean_gt_zero": float(np.mean(boot > 0)),
        }

    costs = {}
    for cost_bps in COSTS_BPS_PER_SIDE:
        spread_cost = SPREAD_COST_MULTIPLIER * cost_bps / 10_000.0
        net_loo = loo - spread_cost
        costs[str(cost_bps)] = {
            "cost_bps_per_side": cost_bps,
            "round_trip_long_short_spread_cost_bps": SPREAD_COST_MULTIPLIER * cost_bps,
            "net_mean": gross_mean - spread_cost,
            "net_median": gross_median - spread_cost,
            "net_hit_rate": float(np.mean(values - spread_cost > 0)),
            "net_loo_min": float(net_loo.min()),
            "net_loo_max": float(net_loo.max()),
            "net_loo_negative_count": int(np.sum(net_loo < 0)),
            "net_ci95_by_block": {
                block: [
                    bounds["gross_ci95"][0] - spread_cost,
                    bounds["gross_ci95"][1] - spread_cost,
                ]
                for block, bounds in bootstrap_by_block.items()
            },
            "bootstrap_probability_net_mean_gt_zero_by_block": {
                block: bounds["gross_probability_mean_gt_zero"]
                if cost_bps == 0
                else None
                for block, bounds in bootstrap_by_block.items()
            },
        }
        # A bootstrap probability after costs uses the same fixed bootstrap draws.
        for block in BLOCK_LENGTHS:
            boot = bootstrap_means_by_block[str(block)]
            costs[str(cost_bps)]["bootstrap_probability_net_mean_gt_zero_by_block"][str(block)] = float(
                np.mean(boot > spread_cost)
            )

    return {
        "horizon_sessions": horizon,
        "stage": stage,
        "n_signal_dates": n,
        "first_signal_date": str(rows[0]["Date"]),
        "last_signal_date": str(rows[-1]["Date"]),
        "gross_mean": gross_mean,
        "gross_median": gross_median,
        "gross_hit_rate": gross_hit_rate,
        "gross_min": float(values.min()),
        "gross_max": float(values.max()),
        "gross_loo_min": float(loo.min()),
        "gross_loo_max": float(loo.max()),
        "gross_loo_negative_count": int(np.sum(loo < 0)),
        "bootstrap_by_block": bootstrap_by_block,
        "cost_sensitivity": costs,
    }


def run_audit(report_path: Path, output_path: Path) -> dict:
    report = json.loads(report_path.read_text(encoding="utf-8"))
    validate_source(report, report_path)
    results = {int(item["horizon"]): item for item in report["results"]}
    stage_summaries = []
    for horizon in (20, 60):
        for stage in ("discovery", "validation", "final_oos"):
            data = results[horizon]["stages"][stage]
            rows = [
                {"Date": date, "d10_d1": spread}
                for date, spread in zip(data["dates"], data["spreads"])
            ]
            stage_summaries.append(summarize_stage(rows, horizon, stage))

    validation = {}
    for horizon in (20, 60):
        item = next(
            x for x in stage_summaries
            if x["horizon_sessions"] == horizon and x["stage"] == "validation"
        )
        validation[str(horizon)] = {}
        for cost_bps in COSTS_BPS_PER_SIDE:
            cost = item["cost_sensitivity"][str(cost_bps)]
            # Strict screen: positive net mean, positive lower CI at block lengths
            # 3 and 6, and positive leave-one-date-out mean in every deletion.
            ci3 = cost["net_ci95_by_block"]["3"][0]
            ci6 = cost["net_ci95_by_block"]["6"][0]
            loo_min = cost["net_loo_min"]
            validation[str(horizon)][str(cost_bps)] = {
                "net_mean_positive": cost["net_mean"] > 0,
                "block3_ci_lower_positive": ci3 > 0,
                "block6_ci_lower_positive": ci6 > 0,
                "loo_min_positive": loo_min > 0,
                "strict_validation_pass": bool(
                    cost["net_mean"] > 0 and ci3 > 0 and ci6 > 0 and loo_min > 0
                ),
            }

    output = {
        "phase": 148,
        "status": "COMPLETED_ARTIFACT_ONLY_COST_AND_OOS_AUDIT",
        "source": {
            "github_run_id": SOURCE_RUN_ID,
            "artifact_id": SOURCE_ARTIFACT_ID,
            "branch": SOURCE_BRANCH,
            "head_sha": SOURCE_SHA,
            "artifact_sha256": SOURCE_ARTIFACT_SHA256,
            "report_sha256": SOURCE_REPORT_SHA256,
            "compact_input_sha256": sha256_file(report_path),
            "original_run_protocol_cost_bps_per_side_declared_but_not_applied": 10.0,
        },
        "interpretation": {
            "factor": "MOM120",
            "direction": "long momentum",
            "universe_configured": 335,
            "prices_loaded": 335,
            "data_series": 334,
            "signal_step_sessions": 21,
            "cross_section_minimum": 100,
            "long_short_cost_model": "four one-way legs: long entry/exit plus short entry/exit",
            "final_oos_status": "EXPOSED_EXPLORATORY_NOT_AN_UNTOUCHED_HOLDOUT",
            "alpha_promotion": "NOT_APPROVED",
            "f80_comparison": "NOT_PERFORMED",
        },
        "validation_strict_screen": validation,
        "stage_summaries": stage_summaries,
        "limitations": [
            "Phase 29 used a fixed 335-symbol universe; this is not a broad point-in-time universe.",
            "Yahoo Finance auto-adjusted prices do not establish point-in-time security identity, delisted coverage, or historical universe membership.",
            "The declared 10 bps per-side cost was not deducted from Q10-Q1 returns in the original Phase 29 code.",
            "The 10 bps cost is a sensitivity assumption, not an empirically estimated spread/impact/borrow model.",
            "The long-short cost adjustment excludes stock-borrow fees, financing, market impact, taxes, and turnover variation.",
            "The 2024+ final slice was already inspected in the prior Phase 29 report and is therefore exposed exploratory evidence, not a virgin holdout.",
            "The audit has no per-ticker holdings/returns, so extreme date-level spreads cannot be attributed to specific securities.",
            "No comparison against frozen LTM/F80 was included in Phase 29.",
            "No multiple-testing correction across the ten candidate factor families was performed.",
        ],
        "decision": "The 20-session candidate fails net validation at 5 bps per side and above; the 60-session candidate has positive mean net validation but fails the block-bootstrap confidence-interval gate at all tested costs. Neither horizon is promotion-grade. Do not add MOM120 or any Smart Money feature to F80 on this evidence.",
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = run_audit(args.input, args.output)
    print(json.dumps({
        "phase": result["phase"],
        "status": result["status"],
        "source_run_id": result["source"]["github_run_id"],
        "stage_summaries": len(result["stage_summaries"]),
        "validation": result["validation_strict_screen"],
        "decision": result["decision"],
    }, indent=2))


if __name__ == "__main__":
    main()

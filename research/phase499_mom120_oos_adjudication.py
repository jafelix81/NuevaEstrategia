from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import binomtest, t as student_t

PHASE29_ARTIFACT_ID = 12565060248
PHASE30_ARTIFACT_ID = 12581524526
PHASE29_SHA256 = "85480d28d6d24c8a167c67baee5b3c28c2915e0a3bc3b2eb2f13b490d4167d77"
PHASE30_SHA256 = "b57190f1d979bde7bb38cff0c6fa0e294cbfed029c5bc702ab62574bb459bc48"
INITIAL_EQUITY = 1000.0
OOS_START = pd.Timestamp("2024-01-01")
EXPECTED_OOS_DAYS = 706
COSTS_BPS = (10, 20, 50)
BOOTSTRAP_BLOCKS = (20, 80, 160)


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json_member(path: str, member: str) -> dict:
    with zipfile.ZipFile(path) as archive:
        return json.loads(archive.read(member).decode("utf-8"))


def read_csv_member(path: str, member: str) -> pd.DataFrame:
    with zipfile.ZipFile(path) as archive:
        return pd.read_csv(archive.open(member), parse_dates=["Date"])


def validate_ledger(frame: pd.DataFrame, label: str, top_n: int = 20) -> dict:
    required = {
        "Date", "Equity", "DailyReturn", "Cash", "GrossValue",
        "Positions", "Gross",
    }
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"{label}: missing columns {sorted(missing)}")
    if frame.empty:
        raise ValueError(f"{label}: empty ledger")
    if frame["Date"].isna().any() or frame["Date"].duplicated().any():
        raise ValueError(f"{label}: invalid or duplicate dates")
    if not frame["Date"].is_monotonic_increasing:
        raise ValueError(f"{label}: dates are not strictly chronological")

    numeric = ["Equity", "DailyReturn", "Cash", "GrossValue", "Positions", "Gross"]
    for column in numeric:
        values = pd.to_numeric(frame[column], errors="coerce").to_numpy(float)
        if not np.isfinite(values).all():
            raise ValueError(f"{label}: non-finite values in {column}")

    equity = frame["Equity"].to_numpy(float)
    returns = frame["DailyReturn"].to_numpy(float)
    cash = frame["Cash"].to_numpy(float)
    gross_value = frame["GrossValue"].to_numpy(float)
    positions = frame["Positions"].to_numpy(float)
    gross = frame["Gross"].to_numpy(float)

    previous_equity = np.r_[INITIAL_EQUITY, equity[:-1]]
    chain_error = float(np.max(np.abs(returns - (equity / previous_equity - 1.0))))
    balance_error = float(np.max(np.abs(cash + gross_value - equity)))
    if chain_error > 1e-9:
        raise ValueError(f"{label}: daily return/equity chain mismatch {chain_error}")
    if balance_error > 1e-7:
        raise ValueError(f"{label}: cash + gross value != equity ({balance_error})")
    if float(np.min(equity)) <= 0:
        raise ValueError(f"{label}: non-positive equity")
    if float(np.min(cash)) < -1e-8:
        raise ValueError(f"{label}: negative cash")
    if float(np.min(gross)) < -1e-8 or float(np.max(gross)) > 1.0 + 1e-6:
        raise ValueError(f"{label}: gross exposure outside [0, 100%]")
    if float(np.max(positions)) > top_n:
        raise ValueError(f"{label}: position count exceeds Top-{top_n}")

    return {
        "rows": int(len(frame)),
        "start": str(frame["Date"].iloc[0].date()),
        "end": str(frame["Date"].iloc[-1].date()),
        "max_positions": int(np.max(positions)),
        "avg_positions": float(np.mean(positions)),
        "max_gross": float(np.max(gross)),
        "min_cash": float(np.min(cash)),
        "max_return_chain_error": chain_error,
        "max_balance_error": balance_error,
    }


def oos_metrics(frame: pd.DataFrame) -> dict:
    sample = frame.loc[frame["Date"] >= OOS_START].copy()
    if len(sample) != EXPECTED_OOS_DAYS:
        raise ValueError(f"Expected {EXPECTED_OOS_DAYS} OOS days, got {len(sample)}")
    returns = sample["DailyReturn"].to_numpy(float)
    equity = sample["Equity"].to_numpy(float)
    volatility = float(np.std(returns, ddof=1))
    drawdown = equity / np.maximum.accumulate(equity) - 1.0
    return {
        "start": str(sample["Date"].iloc[0].date()),
        "end": str(sample["Date"].iloc[-1].date()),
        "days": int(len(sample)),
        "final_multiple": float(equity[-1] / equity[0]),
        "max_drawdown": float(np.min(drawdown)),
        "sharpe": float(np.mean(returns) / volatility * np.sqrt(252)) if volatility else None,
        "mean_daily_return": float(np.mean(returns)),
        "annualized_volatility": float(volatility * np.sqrt(252)),
        "avg_gross": float(sample["Gross"].mean()),
        "avg_positions": float(sample["Positions"].mean()),
    }


def paired_incremental_summary(
    candidate: pd.Series | np.ndarray,
    baseline: pd.Series | np.ndarray,
    blocks: tuple[int, ...] = BOOTSTRAP_BLOCKS,
    bootstrap_samples: int = 10000,
    seed: int = 30,
) -> dict:
    candidate_values = np.asarray(candidate, dtype=float)
    baseline_values = np.asarray(baseline, dtype=float)
    if candidate_values.shape != baseline_values.shape:
        raise ValueError("Candidate and baseline daily-return arrays must have identical shape")
    if candidate_values.ndim != 1 or candidate_values.size < 2:
        raise ValueError("Paired daily-return sample must be a one-dimensional array of length >= 2")
    if not np.isfinite(candidate_values).all() or not np.isfinite(baseline_values).all():
        raise ValueError("Paired daily returns must be finite")

    difference = candidate_values - baseline_values
    n = int(difference.size)
    positive_n = int(np.sum(difference > 0))
    sign_p = float(binomtest(positive_n, n, 0.5).pvalue)
    sample_std = float(np.std(difference, ddof=1))
    t_stat = float(np.mean(difference) / (sample_std / np.sqrt(n))) if sample_std else 0.0
    t_p = float(2.0 * student_t.sf(abs(t_stat), n - 1)) if sample_std else 1.0
    loo = (float(np.sum(difference)) - difference) / (n - 1)

    intervals = {}
    for block in blocks:
        rng = np.random.default_rng(seed + int(block))
        bootstrap_means = np.empty(bootstrap_samples, dtype=float)
        for iteration in range(bootstrap_samples):
            indices: list[int] = []
            while len(indices) < n:
                start = int(rng.integers(0, n))
                indices.extend(((start + np.arange(block)) % n).tolist())
            bootstrap_means[iteration] = float(np.mean(difference[np.asarray(indices[:n])]))
        lower, median, upper = np.quantile(bootstrap_means, [0.025, 0.5, 0.975])
        intervals[str(block)] = {
            "ci95_low_bps": float(lower * 10000.0),
            "median_bps": float(median * 10000.0),
            "ci95_high_bps": float(upper * 10000.0),
        }

    return {
        "n_daily_observations": n,
        "mean_excess_daily_bps": float(np.mean(difference) * 10000.0),
        "positive_daily_differences": positive_n,
        "sign_test_p_two_sided": sign_p,
        "naive_paired_t_p_two_sided": t_p,
        "loo_mean_min_bps": float(np.min(loo) * 10000.0),
        "loo_mean_max_bps": float(np.max(loo) * 10000.0),
        "loo_positive_fraction": float(np.mean(loo > 0)),
        "block_bootstrap": intervals,
        "bootstrap_samples": int(bootstrap_samples),
    }


def audit(phase29_zip: str, phase30_zip: str) -> dict:
    hash29 = sha256_file(phase29_zip)
    hash30 = sha256_file(phase30_zip)
    if hash29 != PHASE29_SHA256:
        raise ValueError(f"Phase 29 artifact SHA-256 mismatch: {hash29}")
    if hash30 != PHASE30_SHA256:
        raise ValueError(f"Phase 30 artifact SHA-256 mismatch: {hash30}")

    phase29 = read_json_member(phase29_zip, "phase29_report.json")
    phase30 = read_json_member(phase30_zip, "phase30_report.json")

    if phase29.get("universe_configured") != 335 or phase29.get("prices_loaded") != 335:
        raise ValueError("Phase 29 universe/price coverage does not match the audited run")
    if phase30.get("universe_configured") != 335 or phase30.get("prices_loaded") != 335:
        raise ValueError("Phase 30 universe/price coverage does not match the audited run")
    if phase30.get("signal_dates") != 32:
        raise ValueError("Phase 30 signal-date count changed")

    selection = phase29.get("selected_by_horizon", {})
    for horizon in ("20", "60"):
        selected = selection.get(horizon, {})
        if selected.get("factor") != "MOM120" or not selected.get("passes_validation"):
            raise ValueError(f"Phase 29 MOM120 validation gate did not pass for horizon {horizon}")

    protocol = phase30.get("protocol", {})
    expected_protocol = {
        "rebalance_sessions": 80,
        "top_n": 20,
        "partial": 0.5,
        "max_position": 0.2,
        "gross_cap": 1.0,
        "oos_start": "2024-01-01",
        "signal_convention": "close t -> open t+1",
    }
    for key, expected in expected_protocol.items():
        if protocol.get(key) != expected:
            raise ValueError(f"Phase 30 protocol mismatch for {key}: {protocol.get(key)!r}")

    cost_results = {}
    oos_trade_dates = {}
    for cost in COSTS_BPS:
        ltm = read_csv_member(phase30_zip, f"LTM_ledger_C{cost}.csv")
        mom = read_csv_member(phase30_zip, f"MOM120_ledger_C{cost}.csv")
        ltm_validation = validate_ledger(ltm, f"LTM_C{cost}")
        mom_validation = validate_ledger(mom, f"MOM120_C{cost}")
        if not ltm["Date"].equals(mom["Date"]):
            raise ValueError(f"C{cost}: candidate and baseline dates differ")

        ltm_oos = ltm.loc[ltm["Date"] >= OOS_START].reset_index(drop=True)
        mom_oos = mom.loc[mom["Date"] >= OOS_START].reset_index(drop=True)
        if not ltm_oos["Date"].equals(mom_oos["Date"]):
            raise ValueError(f"C{cost}: OOS candidate and baseline dates differ")

        ltm_metrics = oos_metrics(ltm)
        mom_metrics = oos_metrics(mom)
        paired = paired_incremental_summary(mom_oos["DailyReturn"], ltm_oos["DailyReturn"])

        ltm_trades = read_csv_member(phase30_zip, f"LTM_trades_C{cost}.csv")
        mom_trades = read_csv_member(phase30_zip, f"MOM120_trades_C{cost}.csv")
        ltm_trade_dates = int(ltm_trades.loc[ltm_trades["Date"] >= "2024-01-01", "Date"].nunique())
        mom_trade_dates = int(mom_trades.loc[mom_trades["Date"] >= "2024-01-01", "Date"].nunique())
        oos_trade_dates[str(cost)] = {
            "ltm_trade_dates": ltm_trade_dates,
            "mom120_trade_dates": mom_trade_dates,
        }

        cost_results[str(cost)] = {
            "ltm_oos": ltm_metrics,
            "mom120_oos": mom_metrics,
            "relative_final_multiple_difference_pct": float(
                (mom_metrics["final_multiple"] / ltm_metrics["final_multiple"] - 1.0) * 100.0
            ),
            "mean_excess_daily_bps": paired["mean_excess_daily_bps"],
            "paired_incremental": paired,
            "ledger_validation": {
                "ltm": ltm_validation,
                "mom120": mom_validation,
            },
        }

    all_intervals_include_zero = all(
        float(result["paired_incremental"]["block_bootstrap"][str(block)]["ci95_low_bps"]) < 0.0
        and float(result["paired_incremental"]["block_bootstrap"][str(block)]["ci95_high_bps"]) > 0.0
        for result in cost_results.values()
        for block in BOOTSTRAP_BLOCKS
    )

    return {
        "phase": 499,
        "status": "COMPLETED_ARTIFACT_ONLY_ADJUDICATION",
        "method": "immutable Phase 29 and Phase 30 GitHub Actions artifacts; no new market-data requests",
        "artifacts": {
            "phase29": {
                "run_id": 40105752275,
                "artifact_id": PHASE29_ARTIFACT_ID,
                "sha256": hash29,
                "universe_configured": int(phase29["universe_configured"]),
                "prices_loaded": int(phase29["prices_loaded"]),
                "selected_mom120_horizons": {
                    horizon: {
                        "discovery_dates": int(selection[horizon]["discovery"]["dates"]),
                        "validation_dates": int(selection[horizon]["validation"]["dates"]),
                        "validation_passed": bool(selection[horizon]["passes_validation"]),
                        "validation_mean_d10_d1": float(selection[horizon]["validation"]["mean_d10_d1"]),
                        "validation_mean_partial_ic": float(selection[horizon]["validation"]["mean_partial_ic"]),
                    }
                    for horizon in ("20", "60")
                },
            },
            "phase30": {
                "run_id": 40149358003,
                "artifact_id": PHASE30_ARTIFACT_ID,
                "sha256": hash30,
                "universe_configured": int(phase30["universe_configured"]),
                "prices_loaded": int(phase30["prices_loaded"]),
                "signal_dates_total": int(phase30["signal_dates"]),
                "oos_start": protocol["oos_start"],
                "oos_end": "2026-10-23",
                "oos_days": EXPECTED_OOS_DAYS,
                "rebalance_sessions": int(protocol["rebalance_sessions"]),
                "top_n": int(protocol["top_n"]),
                "partial": float(protocol["partial"]),
                "gross_cap": float(protocol["gross_cap"]),
                "costs_bps_per_side": list(COSTS_BPS),
                "oos_trade_dates": oos_trade_dates,
            },
        },
        "oos_by_cost": cost_results,
        "decision": {
            "incremental_oos_edge_demonstrated": False,
            "all_block_bootstrap_intervals_include_zero": bool(all_intervals_include_zero),
            "mom120_standalone_replacement": "REJECT_FOR_PROMOTION_NO_SIGNIFICANT_INCREMENTAL_EDGE",
            "general_momentum_hypothesis": "NOT_KILLED; LTM already contains overlapping long-term momentum information",
            "signal_admitted": False,
            "production_change_authorized": False,
        },
        "limitations": [
            "The 335-name universe is static, not an effective-dated historical constituent panel.",
            "Yahoo Finance history does not supply a reproducible point-in-time security-master or delisted-security return panel for this experiment.",
            "The 706 daily OOS observations contain only eight observed OOS trade/rebalance dates; daily rows are not independent signal decisions.",
            "The result is temporal OOS on a static universe, not strict point-in-time OOS.",
            "Fixed basis-point costs do not model name-specific spread, market impact, borrow, or capacity.",
        ],
        "frozen_controls": {
            "f80_top20_partial50_baseline_c20_changed": False,
            "universe_changed": False,
            "parameters_changed": False,
            "exposure_or_costs_changed": False,
            "holdout_changed": False,
            "production_changed": False,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase29-zip", required=True)
    parser.add_argument("--phase30-zip", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = audit(args.phase29_zip, args.phase30_zip)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

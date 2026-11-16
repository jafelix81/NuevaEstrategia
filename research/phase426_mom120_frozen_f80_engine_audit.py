#!/usr/bin/env python3
"""Phase 426 — MOM120 versus the frozen F80 engine.

This is a research-only, fixed-candidate retest. It imports the exact Phase 11 v4
portfolio state machine and uses the same universe, signal calendar, rebalance
cadence, target construction, PARTIAL50 mechanics, position/gross caps and costs.
The candidate is the already-selected positive cross-sectional R120 rank; no
OOS tuning or candidate reselection occurs here.

Important limits:
- 2024+ was already examined in Phase 29/30, so this is a corrected historical
  diagnostic, NOT a fresh untouched holdout.
- Yahoo historical prices and the frozen 335-name universe are not a PIT
  security-master reconstruction; no investability claim is authorized.
- F80 production/baseline files are imported read-only and never modified.
"""
from __future__ import annotations

import json
import math
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf
from scipy.stats import spearmanr

import Nueva_Estrategia_Fase11_Real1000_LTM_v4 as f11

RUN_ID = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
OUT = Path("phase426_output")
OUT.mkdir(parents=True, exist_ok=True)

START = "2016-01-01"
END = "2026-11-16"  # exclusive; last intended session is 2026-11-14
OOS_START = pd.Timestamp("2024-01-01")
FREQUENCY = 80
TOP_N = 20
REBALANCE = "PARTIAL50"
COSTS = (10.0, 20.0, 50.0)
BOOTSTRAP_REPS = 10000
BLOCK_LENGTHS = (5, 20, 60)
EXPECTED_UNIVERSE = 335
PHASE11_ENGINE_BLOB_SHA = "06dc0ece5dd4a3def6a7e2b603564bfc588c0b27"

def json_safe(value):
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(v) for v in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        return float(value) if np.isfinite(value) else None
    if isinstance(value, (pd.Timestamp,)):
        return value.isoformat()
    return value

def write_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(json_safe(payload), indent=2, sort_keys=True, default=str, allow_nan=False) + "\n",
                    encoding="utf-8")

def safe_float(x):
    return float(x) if x is not None and np.isfinite(x) else None

def ticker_frame(raw: pd.DataFrame, ticker: str) -> pd.DataFrame:
    if raw is None or raw.empty:
        raise ValueError("empty provider response")
    frame = raw
    if isinstance(raw.columns, pd.MultiIndex):
        level0 = set(raw.columns.get_level_values(0))
        level1 = set(raw.columns.get_level_values(1))
        if ticker in level0:
            frame = raw[ticker]
        elif ticker in level1:
            frame = raw.xs(ticker, axis=1, level=1)
        else:
            raise ValueError("ticker absent from returned column levels")
    required = {"Open", "Close"}
    if not required.issubset(set(frame.columns)):
        raise ValueError(f"missing required columns: {sorted(required - set(frame.columns))}")
    frame = frame[["Open", "Close"]].copy()
    feat = f11.build_features(frame)
    dates = pd.to_datetime(feat["Date"], errors="coerce")
    if getattr(dates.dt, "tz", None) is not None:
        dates = dates.dt.tz_convert("America/New_York").dt.tz_localize(None)
    feat["Date"] = dates.dt.normalize()
    feat = feat.dropna(subset=["Date"]).drop_duplicates("Date").sort_values("Date").reset_index(drop=True)
    if len(feat) < 220:
        raise ValueError(f"insufficient daily rows after feature build: {len(feat)}")
    return feat

def download_universe(tickers):
    data = {}
    failures = []
    t0 = time.time()
    for offset in range(0, len(tickers), 40):
        chunk = tickers[offset:offset + 40]
        try:
            raw = yf.download(
                chunk,
                start=START,
                end=END,
                auto_adjust=False,
                actions=False,
                progress=False,
                threads=True,
                group_by="ticker",
            )
        except Exception as exc:
            for ticker in chunk:
                failures.append({"ticker": ticker, "error": f"chunk_download: {exc}"})
            continue
        for ticker in chunk:
            try:
                frame = ticker_frame(raw, ticker)
                data[ticker] = frame
            except Exception as exc:
                failures.append({"ticker": ticker, "error": str(exc)})
        print(f"DOWNLOAD {min(offset + 40, len(tickers))}/{len(tickers)} loaded={len(data)} failed={len(failures)}",
              flush=True)
    return data, failures

def build_mom120_snapshots(ltm_snapshots):
    out = {}
    for dt, snapshot in ltm_snapshots.items():
        if "rank_R120" not in snapshot.columns:
            raise RuntimeError(f"rank_R120 missing at {dt}")
        candidate = snapshot.copy()
        candidate["LTM"] = candidate["rank_R120"].astype(float)
        out[dt] = candidate.sort_values("LTM", ascending=False).reset_index(drop=True)
    return out

def hac_mean_se(values, max_lag=20):
    x = np.asarray(values, dtype=float)
    x = x[np.isfinite(x)]
    n = len(x)
    if n < max_lag + 5:
        return None
    e = x - x.mean()
    gamma0 = float(np.dot(e, e) / n)
    lrv = gamma0
    for lag in range(1, max_lag + 1):
        gamma = float(np.dot(e[lag:], e[:-lag]) / n)
        weight = 1.0 - lag / (max_lag + 1.0)
        lrv += 2.0 * weight * gamma
    return math.sqrt(max(lrv, 0.0) / n)

def circular_block_bootstrap(values, block, reps, seed):
    x = np.asarray(values, dtype=float)
    x = x[np.isfinite(x)]
    n = len(x)
    if n < max(100, block * 3):
        return {"n": n, "status": "INSUFFICIENT"}
    rng = np.random.default_rng(seed)
    means = np.empty(reps, dtype=float)
    nblocks = int(math.ceil(n / block))
    offsets = np.arange(block)
    for b in range(reps):
        starts = rng.integers(0, n, size=nblocks)
        idx = ((starts[:, None] + offsets[None, :]) % n).ravel()[:n]
        means[b] = float(x[idx].mean())
    q = np.quantile(means, [0.025, 0.5, 0.975])
    return {
        "n": n,
        "block_length": block,
        "replicates": reps,
        "mean": float(x.mean()),
        "ci95_low": float(q[0]),
        "median": float(q[1]),
        "ci95_high": float(q[2]),
        "seed": seed,
    }

def oos_metrics(daily: pd.DataFrame, trades: pd.DataFrame):
    x = daily.copy()
    x["Date"] = pd.to_datetime(x["Date"])
    x = x[x["Date"] >= OOS_START].sort_values("Date").reset_index(drop=True)
    if x.empty:
        raise RuntimeError("no OOS observations")
    r = x["DailyReturn"].to_numpy(dtype=float)
    wealth = np.cumprod(1.0 + r)
    dd = wealth / np.maximum.accumulate(wealth) - 1.0
    sd = float(np.std(r, ddof=1)) if len(r) > 1 else float("nan")
    downside = r[r < 0]
    downside_sd = float(np.std(downside, ddof=1)) if len(downside) > 1 else float("nan")
    gross = x["GrossMarketValue"] / x["EquityClose"]
    cash = x["Cash"] / x["EquityClose"]
    pos = x["Positions"]
    tr = trades.copy()
    if not tr.empty:
        tr["ExecutionDate"] = pd.to_datetime(tr["ExecutionDate"])
        tr = tr[tr["ExecutionDate"] >= OOS_START]
        total_notional = float(tr["Notional"].sum())
        total_cost = float(tr["Cost"].sum())
    else:
        total_notional = 0.0
        total_cost = 0.0
    years = len(x) / 252.0
    avg_equity = float(x["EquityClose"].mean())
    return {
        "start": str(x["Date"].iloc[0].date()),
        "end": str(x["Date"].iloc[-1].date()),
        "days": int(len(x)),
        "final_multiple_from_daily_returns": float(wealth[-1]),
        "mean_daily_return": float(np.mean(r)),
        "annualized_volatility": sd * math.sqrt(252.0) if np.isfinite(sd) else None,
        "sharpe_daily": float(np.mean(r) / sd * math.sqrt(252.0)) if sd > 0 else None,
        "sortino_daily": float(np.mean(r) / downside_sd * math.sqrt(252.0)) if downside_sd > 0 else None,
        "max_drawdown": float(np.min(dd)),
        "daily_hit_rate": float(np.mean(r > 0)),
        "average_gross_exposure": float(gross.mean()),
        "maximum_gross_exposure": float(gross.max()),
        "average_cash_weight": float(cash.mean()),
        "average_positions": float(pos.mean()),
        "maximum_positions": int(pos.max()),
        "oos_buy_plus_sell_notional": total_notional,
        "oos_transaction_cost": total_cost,
        "oos_annualized_turnover": (total_notional / max(avg_equity, 1e-12)) / max(years, 1e-12),
        "oos_transaction_cost_over_average_equity": total_cost / max(avg_equity, 1e-12),
    }

def main():
    t0 = time.time()
    tickers = list(dict.fromkeys(str(x).upper().strip() for x in f11.DEFAULT_UNIVERSE))
    if len(tickers) != EXPECTED_UNIVERSE:
        raise RuntimeError(f"frozen universe count mismatch: {len(tickers)} != {EXPECTED_UNIVERSE}")
    if len(set(tickers)) != len(tickers):
        raise RuntimeError("duplicate ticker in frozen universe")

    data, failures = download_universe(tickers)
    coverage = {
        "run_id": RUN_ID,
        "configured_universe": len(tickers),
        "loaded_tickers": len(data),
        "failed_tickers": failures,
        "start": START,
        "end_exclusive": END,
        "auto_adjust": False,
        "point_in_time_security_master": False,
        "complete_universe": len(data) == len(tickers),
    }
    write_json(OUT / "data_coverage.json", coverage)
    if len(data) != len(tickers):
        raise RuntimeError(f"UNIVERSE_INCOMPLETE: loaded {len(data)}/{len(tickers)}; no reduced-universe test permitted")

    calendar = sorted(set(d for frame in data.values() for d in frame["Date"].dropna().tolist()))
    open_maps, close_maps = f11.build_price_maps(data)
    ltm_snapshots = f11.build_snapshots(data, calendar)
    mom_snapshots = build_mom120_snapshots(ltm_snapshots)
    if not ltm_snapshots:
        raise RuntimeError("no valid cross-sectional snapshots")
    if set(ltm_snapshots) != set(mom_snapshots):
        raise RuntimeError("LTM and MOM120 snapshot dates differ")

    scheduled_dates = [
        d for d in calendar[f11.DISCOVERY_DATES + f11.EMBARGO::FREQUENCY]
        if d in ltm_snapshots
    ]
    oos_signal_dates = [d for d in scheduled_dates if pd.Timestamp(d) >= OOS_START]
    if len(oos_signal_dates) < 4:
        raise RuntimeError(f"too few OOS rebalance signals: {len(oos_signal_dates)}")

    overlap_rows = []
    for dt in oos_signal_dates:
        snap = ltm_snapshots[dt]
        ltm_top = set(snap.sort_values("LTM", ascending=False).head(TOP_N)["Ticker"])
        mom_top = set(mom_snapshots[dt].sort_values("LTM", ascending=False).head(TOP_N)["Ticker"])
        corr = spearmanr(snap["LTM"].to_numpy(float), snap["rank_R120"].to_numpy(float)).statistic
        overlap_rows.append({
            "date": str(pd.Timestamp(dt).date()),
            "cross_section_n": int(len(snap)),
            "spearman_ltm_vs_mom120": safe_float(corr),
            "top20_overlap_count": int(len(ltm_top & mom_top)),
            "top20_jaccard": float(len(ltm_top & mom_top) / max(len(ltm_top | mom_top), 1)),
        })
    overlap_df = pd.DataFrame(overlap_rows)
    overlap_df.to_csv(OUT / "oos_signal_overlap.csv", index=False)

    total_policies = len(COSTS) * 2
    policy_no = 0
    results = {}
    daily_by_factor_cost = {}
    trades_by_factor_cost = {}
    checks_by_factor_cost = {}
    all_daily = []
    all_trades = []
    all_checks = []

    for factor, snapshots in (("LTM", ltm_snapshots), ("MOM120", mom_snapshots)):
        for cost in COSTS:
            policy_no += 1
            result, daily_rows, trade_rows, checks = f11.run_policy(
                data,
                calendar,
                snapshots,
                open_maps,
                close_maps,
                FREQUENCY,
                TOP_N,
                REBALANCE,
                cost,
                policy_no,
                total_policies,
            )
            key = f"{factor}_C{int(cost)}"
            daily = pd.DataFrame(daily_rows)
            trades = pd.DataFrame(trade_rows)
            checks_df = pd.DataFrame(checks)
            daily["Factor"] = factor
            daily["CostBpsPerSide"] = cost
            trades["Factor"] = factor
            checks_df["Factor"] = factor
            results[key] = {
                "engine_full_period_diagnostics": result,
                "oos_metrics": oos_metrics(daily, trades),
            }
            daily_by_factor_cost[key] = daily
            trades_by_factor_cost[key] = trades
            checks_by_factor_cost[key] = checks_df
            all_daily.append(daily)
            all_trades.append(trades)
            all_checks.append(checks_df)
            daily.to_csv(OUT / f"{key}_daily.csv", index=False)
            trades.to_csv(OUT / f"{key}_trades.csv", index=False)
            checks_df.to_csv(OUT / f"{key}_checks.csv", index=False)

    paired = {}
    for cost in COSTS:
        key_l = f"LTM_C{int(cost)}"
        key_m = f"MOM120_C{int(cost)}"
        a = daily_by_factor_cost[key_l][["Date", "DailyReturn"]].copy()
        b = daily_by_factor_cost[key_m][["Date", "DailyReturn"]].copy()
        a["Date"] = pd.to_datetime(a["Date"])
        b["Date"] = pd.to_datetime(b["Date"])
        z = a.merge(b, on="Date", suffixes=("_ltm", "_mom"), validate="one_to_one")
        z = z[z["Date"] >= OOS_START].sort_values("Date")
        if len(z) == 0:
            raise RuntimeError("empty paired OOS return series")
        d = (z["DailyReturn_mom"] - z["DailyReturn_ltm"]).to_numpy(float)
        hac_se = hac_mean_se(d, max_lag=20)
        loo = (d.sum() - d) / (len(d) - 1) if len(d) > 1 else np.array([])
        paired[str(int(cost))] = {
            "n": int(len(d)),
            "same_dates": bool(np.array_equal(a["Date"].to_numpy(), b["Date"].to_numpy())),
            "mean_daily_excess_mom120_minus_ltm": float(d.mean()),
            "hac_lag_20_se": safe_float(hac_se),
            "hac_lag_20_t": safe_float(d.mean() / hac_se if hac_se and hac_se > 0 else None),
            "loo_mean_min": safe_float(loo.min()) if len(loo) else None,
            "loo_mean_max": safe_float(loo.max()) if len(loo) else None,
            "positive_loo_fraction": safe_float(np.mean(loo > 0)) if len(loo) else None,
            "positive_excess_day_fraction": float(np.mean(d > 0)),
            "block_bootstrap": {
                str(block): circular_block_bootstrap(
                    d, block, BOOTSTRAP_REPS, seed=426000 + int(cost) * 100 + block
                )
                for block in BLOCK_LENGTHS
            },
        }
        z.assign(excess_daily=d).to_csv(OUT / f"paired_excess_C{int(cost)}.csv", index=False)

    # Strict invariant audit on all six ledgers.
    invariant_rows = []
    for key, daily in daily_by_factor_cost.items():
        d = daily.copy()
        d["Date"] = pd.to_datetime(d["Date"])
        equity = pd.to_numeric(d["EquityClose"], errors="coerce")
        prev = pd.to_numeric(d["PreviousCloseEquity"], errors="coerce")
        expected_return = equity / prev - 1.0
        return_error = (pd.to_numeric(d["DailyReturn"], errors="coerce") - expected_return).abs()
        accounting_error = pd.to_numeric(d["EquityClose"], errors="coerce") - (
            pd.to_numeric(d["Cash"], errors="coerce") + pd.to_numeric(d["GrossMarketValue"], errors="coerce")
        )
        decomposition_error = pd.to_numeric(d["ReturnDecompositionError"], errors="coerce")
        gross = pd.to_numeric(d["GrossMarketValue"], errors="coerce") / pd.to_numeric(d["EquityClose"], errors="coerce")
        trades = trades_by_factor_cost[key]
        if not trades.empty:
            signal_dates = pd.to_datetime(trades["DateSignal"])
            execution_dates = pd.to_datetime(trades["ExecutionDate"])
            no_lookahead = bool((execution_dates > signal_dates).all())
        else:
            no_lookahead = True
        invariant_rows.append({
            "strategy_cost": key,
            "max_daily_return_reconciliation_error": safe_float(return_error.max()),
            "max_accounting_identity_error": safe_float(accounting_error.abs().max()),
            "max_return_decomposition_error": safe_float(decomposition_error.max()),
            "max_gross_exposure": safe_float(gross.max()),
            "max_positions": int(d["Positions"].max()),
            "all_trade_executions_after_signal_close": no_lookahead,
            "all_equity_positive": bool((equity > 0).all()),
            "all_cash_nonnegative": bool((d["Cash"] >= -1e-8).all()),
        })
    invariant_df = pd.DataFrame(invariant_rows)
    invariant_df.to_csv(OUT / "invariant_audit.csv", index=False)

    primary = paired["20"]
    primary_ci = primary["block_bootstrap"]["20"]
    primary_no_increment = (
        primary_ci.get("ci95_low") is not None
        and primary_ci.get("ci95_high") is not None
        and primary_ci["ci95_low"] <= 0 <= primary_ci["ci95_high"]
        and (primary["positive_loo_fraction"] is None or primary["positive_loo_fraction"] < 0.80)
    )

    summary = {
        "phase": 426,
        "run_id": RUN_ID,
        "source_commit": "2d7d163da1988e923bdcc7958daefc33d1a38536",
        "phase11_engine_blob_sha": PHASE11_ENGINE_BLOB_SHA,
        "phase29_candidate": "positive cross-sectional rank of R120 (MOM120), fixed before 2024 OOS",
        "protocol": {
            "universe": "exact Phase 11 v4 DEFAULT_UNIVERSE; no reduced-universe fallback",
            "configured_universe": len(tickers),
            "loaded_universe": len(data),
            "price_source": "Yahoo Finance via yfinance",
            "price_adjustment": "auto_adjust=False, exact frozen Phase 11 v4 convention",
            "start": START,
            "end_exclusive": END,
            "oos_start": str(OOS_START.date()),
            "rebalance_sessions": FREQUENCY,
            "top_n": TOP_N,
            "rebalance": REBALANCE,
            "max_position": f11.MAX_POSITION,
            "gross_cap": f11.GROSS_CAP,
            "initial_capital": f11.INITIAL_CAPITAL,
            "costs_bps_per_side": list(COSTS),
            "signal_convention": "Close(t) signal; next calendar session Open(t+1) execution; daily close valuation",
            "state_machine": "imported without edits from Phase 11 v4 frozen engine",
            "discovery_skip_sessions": f11.DISCOVERY_DATES,
            "embargo_skip_sessions": f11.EMBARGO,
            "signal_calendar_rule": "calendar[DISCOVERY_DATES + EMBARGO :: 80]",
            "holding_period": "variable; no fixed minimum or maximum holding period",
        },
        "data": {
            "configured_tickers": len(tickers),
            "loaded_tickers": len(data),
            "failures": failures,
            "first_session": str(pd.Timestamp(calendar[0]).date()),
            "last_session": str(pd.Timestamp(calendar[-1]).date()),
            "cross_sectional_snapshot_dates": len(ltm_snapshots),
            "oos_signal_dates": len(oos_signal_dates),
            "point_in_time_security_master": False,
            "survivorship_free": False,
        },
        "historical_oos_retest_is_fresh_holdout": False,
        "no_oos_tuning_or_candidate_reselection": True,
        "holdout_used": False,
        "f80_changed": False,
        "production_changed": False,
        "strategy_results": results,
        "signal_overlap": {
            "mean_ltm_mom120_spearman": safe_float(overlap_df["spearman_ltm_vs_mom120"].mean()),
            "mean_top20_overlap_count": safe_float(overlap_df["top20_overlap_count"].mean()),
            "mean_top20_jaccard": safe_float(overlap_df["top20_jaccard"].mean()),
            "oos_signal_dates": len(overlap_df),
        },
        "paired_incremental": paired,
        "invariants": {
            "all_rows_pass": bool(
                (invariant_df["max_daily_return_reconciliation_error"].fillna(np.inf) <= 1e-8).all()
                and (invariant_df["max_accounting_identity_error"].fillna(np.inf) <= 1e-8).all()
                and (invariant_df["max_return_decomposition_error"].fillna(np.inf) <= 1e-8).all()
                and (invariant_df["max_gross_exposure"].fillna(np.inf) <= f11.GROSS_CAP + 1e-7).all()
                and invariant_df["all_trade_executions_after_signal_close"].all()
                and invariant_df["all_equity_positive"].all()
                and invariant_df["all_cash_nonnegative"].all()
            ),
            "max_daily_return_reconciliation_error": safe_float(invariant_df["max_daily_return_reconciliation_error"].max()),
            "max_accounting_identity_error": safe_float(invariant_df["max_accounting_identity_error"].max()),
            "max_return_decomposition_error": safe_float(invariant_df["max_return_decomposition_error"].max()),
            "max_gross_exposure": safe_float(invariant_df["max_gross_exposure"].max()),
            "max_entry_position_weight": safe_float(max(
                results[k]["engine_full_period_diagnostics"]["MaxEntryPositionObserved"]
                for k in results
            )),
        },
        "decision": "NO_INCREMENTAL_PROMOTION" if primary_no_increment else "REQUIRES_FURTHER_REVIEW",
        "decision_rule_note": "This is a diagnostic rule only; a CI crossing zero and weak LOO stability do not prove the true effect is exactly zero.",
        "limitations": [
            "The 2024+ period was already used in Phase 29/30; this is not a fresh untouched holdout.",
            "Yahoo current historical prices and the frozen 335-name universe are not a PIT security-master reconstruction.",
            "No F80 baseline, universe, parameters, capital, exposure, production or holdout was changed.",
            "No Smart Money feature was used; this is an independent-factor comparator audit.",
        ],
        "runtime_seconds": time.time() - t0,
    }
    write_json(OUT / "phase426_report.json", summary)
    print(json.dumps(summary, indent=2, default=str))
    print("PHASE426_STATUS=PASS" if summary["invariants"]["all_rows_pass"] else "PHASE426_STATUS=FAIL")
    if not summary["invariants"]["all_rows_pass"]:
        raise RuntimeError("one or more frozen-engine accounting / no-lookahead invariants failed")

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        write_json(OUT / "failure.json", {
            "phase": 426,
            "run_id": RUN_ID,
            "error": str(exc),
            "traceback": traceback.format_exc(),
        })
        raise

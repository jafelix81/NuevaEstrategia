"""
FASE 12 — FINAL OUT-OF-SAMPLE + PREDEFINED SELECTION — LONG-TERM MOMENTUM

Purpose
-------
Make one final, auditable selection without using the final test period to choose
parameters. The LTM signal and execution engine remain frozen.

Frozen signal
-------------
LTM = average cross-sectional percentile ranks of R100/R120/R140/R160.

Frozen execution
----------------
- Signal known at close t.
- Rebalance at open t+1.
- Fractional shares allowed.
- Initial capital = $1,000.
- Max entry position = 20% of equity.
- Gross exposure <= 100%.
- Persistence buffer = +20 ranks (EXIT20-equivalent).
- Rebalance modes = FULL / PARTIAL50 / PARTIAL25.
- Frequencies = 20 / 40 / 60 / 80 sessions.
- Top-N = 5 / 10 / 15 / 20.
- Costs = 10 / 20 / 50 bps per side.

Critical anti-overfitting rule
------------------------------
The usable signal dates are split chronologically BEFORE selection:
    80% SELECTION / 20% FINAL OOS TEST.

All 144 structural/cost policies are evaluated ONLY on the selection period.
Exactly ONE structural policy is selected using predefined criteria. Its final
OOS result is then evaluated on the untouched final 20% period at 10/20/50 bps.
The final OOS results are NEVER used to change the selection.

Selection criteria (frozen before final OOS)
--------------------------------------------
At 20 bps/side on the selection period:
    CAGR >= 15%
    MaxDD >= -45%
    Sharpe >= 0.85
    Annualized turnover <= 3.5x
    Average cash weight between 25% and 75%

Cost robustness on the selection period:
    50bps CAGR >= 80% of 10bps CAGR
    50bps CAGR > 0

Among eligible structural policies, choose the single policy with the highest
predefined composite score:
    35% Sharpe rank
    25% CAGR rank
    25% drawdown rank (less negative is better)
    15% turnover rank (lower is better)

If no policy passes the frozen eligibility rules, the phase FAILS and NO final
OOS winner is declared.

IMPORTANT
---------
This phase does not introduce Kelly, stop losses, new factors, or production
rules. It is a research gate. A PASS means the frozen strategy survives the
predeclared final OOS test; it does NOT authorize live trading.

Dependency
----------
The exact, already-audited Phase 11 v4 engine is imported for the frozen
universe, feature construction, LTM snapshot construction, and execution
mechanics. No Phase 12 code changes that engine.
"""
from __future__ import annotations

import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

# Reuse the already audited/frozen Phase 11 mechanics.
from Nueva_Estrategia_Fase11_Real1000_LTM_v4 import (
    DEFAULT_UNIVERSE,
    PERIOD,
    DISCOVERY_DATES,
    EMBARGO,
    MIN_CROSS_SECTION,
    WINDOWS,
    INITIAL_CAPITAL,
    MAX_POSITION,
    GROSS_CAP,
    COST_BPS,
    FREQUENCIES,
    TOP_N,
    PERSISTENCE_BUFFER,
    REBALANCES,
    download_universe,
    build_price_maps,
    build_snapshots,
    portfolio_value,
    build_target,
    execute_rebalance,
)

RUN_ID = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
OUTDIR = Path("nueva_estrategia_phase12_final_oos_ltm")
OUTDIR.mkdir(parents=True, exist_ok=True)

TRAIN_FRACTION = 0.80
SELECTION_COST = 20

# Frozen selection thresholds.
MIN_SELECTION_CAGR = 0.15
MIN_SELECTION_SHARPE = 0.85
MAX_SELECTION_DD = -0.45
MAX_SELECTION_TURNOVER = 3.50
MIN_SELECTION_CASH = 0.25
MAX_SELECTION_CASH = 0.75
MIN_COST_ROBUSTNESS_RATIO = 0.80

# Frozen final-test acceptance thresholds. These do not select the winner;
# they only determine whether the selected policy survives the final test.
MIN_TEST_CAGR = 0.15
MIN_TEST_SHARPE = 0.85
MAX_TEST_DD = -0.45
MAX_TEST_TURNOVER = 3.50

GAP_BY_REBALANCE = {"FULL": 1.0, "PARTIAL50": 0.5, "PARTIAL25": 0.25}


def policy_id(f, n, r, c):
    return f"F{f}_TOP{n}_{r}_C{c}"


def signal_dates_for(calendar, snapshots, frequency):
    base = calendar[DISCOVERY_DATES + EMBARGO:]
    return [d for d in base[::frequency] if d in snapshots]


def metric_summary(daily, initial_equity):
    if daily.empty:
        raise RuntimeError("empty daily ledger")
    eq = daily["EquityClose"].astype(float).to_numpy()
    ret = daily["DailyReturn"].dropna().astype(float)
    base = max(float(initial_equity), 1e-12)
    test_eq = eq / base
    running = np.maximum.accumulate(test_eq)
    dd = test_eq / running - 1.0
    years = max(len(daily) / 252.0, 1e-12)
    final = float(eq[-1])
    growth = final / base
    cagr = growth ** (1.0 / years) - 1.0 if growth > 0 else -1.0
    sd = ret.std(ddof=1) if len(ret) > 1 else np.nan
    sharpe = float(ret.mean() / sd * np.sqrt(252)) if sd and np.isfinite(sd) else np.nan
    down = ret[ret < 0]
    dsd = down.std(ddof=1) if len(down) > 1 else np.nan
    sortino = float(ret.mean() / dsd * np.sqrt(252)) if dsd and np.isfinite(dsd) else np.nan
    gains = ret[ret > 0].sum()
    losses = -ret[ret < 0].sum()
    pf = float(gains / losses) if losses > 0 else np.inf
    return {
        "FinalEquity": final,
        "GrowthMultiple": growth,
        "CAGR": cagr,
        "MaxDD": float(dd.min()),
        "Sharpe": sharpe,
        "Sortino": sortino,
        "ProfitFactor": pf,
        "HitRate": float((ret > 0).mean()) if len(ret) else np.nan,
    }


def simulate_policy_window(
    calendar,
    snapshots,
    open_maps,
    close_maps,
    frequency,
    top_n,
    rebalance,
    cost_bps,
    start_index=0,
    end_index=None,
    initial_positions=None,
    initial_cash=INITIAL_CAPITAL,
    initial_last_close=None,
    initial_prev_equity=None,
    previous_signal_dt=None,
    collect_ledger=True,
    heartbeat_label="",
):
    """Run one policy on a bounded chronological window.

    The previous signal can be supplied so the first test-day open can execute
    the rebalance generated at the final selection-period close.
    """
    if end_index is None:
        end_index = len(calendar) - 1
    if end_index < start_index:
        raise RuntimeError("invalid simulation window")

    signal_dates = signal_dates_for(calendar, snapshots, frequency)
    signal_set = set(signal_dates)

    positions = dict(initial_positions or {})
    cash = float(initial_cash)
    last_close = dict(initial_last_close or {})
    prev_equity = float(initial_prev_equity if initial_prev_equity is not None else INITIAL_CAPITAL)

    trade_rows = []
    daily_rows = []
    checks = []
    max_entry_pos_obs = 0.0
    max_marked_pos_obs = 0.0
    stale_marks = 0
    missing_open_trades = 0
    gap = GAP_BY_REBALANCE[rebalance]

    for i in range(start_index, end_index + 1):
        dt = calendar[i]
        opens = open_maps.get(dt, {})
        closes = close_maps.get(dt, {})
        open_marks = dict(last_close)
        open_marks.update(opens)
        equity_before_trade = portfolio_value(positions, open_marks, cash)
        traded_buy = traded_sell = cost = 0.0

        prev_dt = calendar[i - 1] if i > 0 else previous_signal_dt
        if prev_dt in signal_set:
            target, exits = build_target(snapshots[prev_dt], top_n, positions)
            if not opens:
                missing_open_trades += 1
            else:
                positions, cash, traded_buy, traded_sell, cost = execute_rebalance(
                    positions, cash, target, exits, opens, equity_before_trade,
                    gap, cost_bps, prev_dt, dt,
                    policy_id(frequency, top_n, rebalance, cost_bps), trade_rows
                )
                entry_marks = dict(last_close)
                entry_marks.update(opens)
                entry_equity = portfolio_value(positions, entry_marks, cash)
                entry_maxw = max(
                    (sh * entry_marks[t] / max(entry_equity, 1e-12)
                     for t, sh in positions.items() if t in entry_marks),
                    default=0.0,
                )
                max_entry_pos_obs = max(max_entry_pos_obs, entry_maxw)

        post_trade_open_marks = dict(last_close)
        post_trade_open_marks.update(opens)
        post_trade_open_equity = portfolio_value(positions, post_trade_open_marks, cash)

        close_marks = dict(last_close)
        close_marks.update(closes)
        held_missing = [t for t in positions if t not in closes]
        stale_marks += len(held_missing)
        close_equity = portfolio_value(positions, close_marks, cash)
        gross_value = sum(sh * close_marks[t] for t, sh in positions.items() if t in close_marks)
        maxw = max(
            (sh * close_marks[t] / max(close_equity, 1e-12)
             for t, sh in positions.items() if t in close_marks),
            default=0.0,
        )
        max_marked_pos_obs = max(max_marked_pos_obs, maxw)

        identity = cash + gross_value
        accounting_error = abs(identity - close_equity)
        overnight_ret = equity_before_trade / prev_equity - 1.0 if prev_equity > 0 else np.nan
        execution_ret = post_trade_open_equity / equity_before_trade - 1.0 if equity_before_trade > 0 else np.nan
        intraday_ret = close_equity / post_trade_open_equity - 1.0 if post_trade_open_equity > 0 else np.nan
        daily_ret = close_equity / prev_equity - 1.0 if prev_equity > 0 else np.nan
        vals = [overnight_ret, execution_ret, intraday_ret, daily_ret]
        decomp_error = (
            abs((1 + overnight_ret) * (1 + execution_ret) * (1 + intraday_ret) - (1 + daily_ret))
            if all(np.isfinite(x) for x in vals) else np.nan
        )

        checks.append({
            "Date": str(dt.date()),
            "Cash": cash,
            "GrossMarketValue": gross_value,
            "Equity": close_equity,
            "AccountingIdentityError": accounting_error,
            "HeldWithoutFreshClose": len(held_missing),
            "GrossExposure": gross_value / max(close_equity, 1e-12),
            "MaxMarkedPositionWeight": maxw,
            "MaxEntryPositionWeightObservedToDate": max_entry_pos_obs,
        })
        if collect_ledger:
            daily_rows.append({
                "Date": str(dt.date()),
                "PreviousCloseEquity": prev_equity,
                "OpenEquityBeforeTrade": equity_before_trade,
                "EquityAfterOpenExecution": post_trade_open_equity,
                "EquityClose": close_equity,
                "OvernightReturn": overnight_ret,
                "ExecutionReturn": execution_ret,
                "IntradayReturn": intraday_ret,
                "DailyReturn": daily_ret,
                "ReturnDecompositionError": decomp_error,
                "Cash": cash,
                "GrossMarketValue": gross_value,
                "Positions": len(positions),
                "BuyNotional": traded_buy,
                "SellNotional": traded_sell,
                "TransactionCost": cost,
                "FreshCloseMissingCount": len(held_missing),
            })

        prev_equity = close_equity
        last_close.update(closes)

    daily = pd.DataFrame(daily_rows)
    trades = pd.DataFrame(trade_rows)
    checks_df = pd.DataFrame(checks)

    if collect_ledger and daily.empty:
        raise RuntimeError("empty daily ledger")

    if collect_ledger:
        m = metric_summary(daily, initial_prev_equity if initial_prev_equity is not None else INITIAL_CAPITAL)
        avg_equity = max(float(daily["EquityClose"].mean()), 1e-12)
        years = max(len(daily) / 252.0, 1e-12)
        total_buy = float(trades.loc[trades.Side.str.startswith("BUY"), "Notional"].sum()) if not trades.empty else 0.0
        total_sell = float(trades.loc[trades.Side.str.startswith("SELL"), "Notional"].sum()) if not trades.empty else 0.0
        total_cost = float(trades["Cost"].sum()) if not trades.empty else 0.0
        m.update({
            "DailyObservations": len(daily),
            "TotalBuyNotional": total_buy,
            "TotalSellNotional": total_sell,
            "TotalTransactionCost": total_cost,
            "AnnualizedTurnover": ((total_buy + total_sell) / avg_equity) / years,
            "AnnualizedBuyTurnover": (total_buy / avg_equity) / years,
            "AnnualizedSellTurnover": (total_sell / avg_equity) / years,
            "AvgPositions": float(daily["Positions"].mean()),
            "AvgCashWeight": float((daily["Cash"] / daily["EquityClose"]).mean()),
            "AvgGrossExposure": float((daily["GrossMarketValue"] / daily["EquityClose"]).mean()),
            "MaxEntryPositionObserved": max_entry_pos_obs,
            "MaxDailyMarkedPositionObserved": max_marked_pos_obs,
            "MaxAccountingIdentityError": float(checks_df["AccountingIdentityError"].max()),
            "MaxReturnDecompositionError": float(daily["ReturnDecompositionError"].max()),
            "HeldWithoutFreshCloseMarks": int(stale_marks),
            "MissingOpenExecutionDays": int(missing_open_trades),
        })
    else:
        m = {}

    state = {
        "positions": positions,
        "cash": cash,
        "last_close": last_close,
        "equity": prev_equity,
        "last_index": end_index,
    }
    return m, daily, trades, checks_df, state


def selection_score(df):
    """Predeclared rank-based score; no test-period information enters here."""
    x = df.copy()
    x["r_sharpe"] = x["Sharpe_20"].rank(pct=True, method="average")
    x["r_cagr"] = x["CAGR_20"].rank(pct=True, method="average")
    x["r_dd"] = x["MaxDD_20"].rank(pct=True, method="average")
    x["r_turn"] = (-x["Turnover_20"]).rank(pct=True, method="average")
    x["SelectionScore"] = (
        0.35 * x["r_sharpe"]
        + 0.25 * x["r_cagr"]
        + 0.25 * x["r_dd"]
        + 0.15 * x["r_turn"]
    )
    return x.sort_values(["Eligible", "SelectionScore"], ascending=[False, False]).reset_index(drop=True)


def main():
    t0 = time.time()
    print("FASE 12 — FINAL OUT-OF-SAMPLE + PREDEFINED SELECTION — LTM", flush=True)
    print("=" * 78, flush=True)
    print(f"RUN_ID: {RUN_ID}", flush=True)
    print(f"Train/Test split: {TRAIN_FRACTION:.0%}/{1-TRAIN_FRACTION:.0%} by chronological signal dates", flush=True)
    print("Selection criteria are frozen BEFORE final OOS.", flush=True)
    print("No Kelly | No stops | No new factors | No production", flush=True)

    data, failures = download_universe(DEFAULT_UNIVERSE)
    valid = len(data)
    if valid < MIN_CROSS_SECTION:
        raise RuntimeError(f"valid universe too small: {valid}")

    calendar = sorted(set(d for df in data.values() for d in df["Date"].dropna().tolist()))
    open_maps, close_maps = build_price_maps(data)
    snapshots = build_snapshots(data, calendar)
    print(f"Valid tickers: {valid} | Failures: {len(failures)} | Snapshots: {len(snapshots)}", flush=True)

    # The split is made on the scheduled signal stream for each frequency. To
    # ensure a genuinely untouched final period, use one common calendar split
    # based on the 20-session signal stream, then apply the same boundary to all
    # frequencies. This prevents a frequency-specific test selection.
    ref_signals = signal_dates_for(calendar, snapshots, 20)
    if len(ref_signals) < 100:
        raise RuntimeError("reference signal stream too short for final OOS split")
    split_pos = int(math.floor(len(ref_signals) * TRAIN_FRACTION)) - 1
    split_pos = max(1, min(split_pos, len(ref_signals) - 2))
    train_end_dt = ref_signals[split_pos]
    test_start_index = calendar.index(train_end_dt) + 1
    print(f"SELECTION END: {train_end_dt.date()}", flush=True)
    print(f"FINAL OOS START: {calendar[test_start_index].date()}", flush=True)
    print(f"Reference signal dates: {len(ref_signals)} | selection={split_pos+1} | final OOS={len(ref_signals)-(split_pos+1)}", flush=True)

    # ---------- SELECTION PERIOD ----------
    configs = [(f, n, r) for f in FREQUENCIES for n in TOP_N for r in REBALANCES]
    selection_rows = []
    total = len(configs)
    for k, (f, n, r) in enumerate(configs, 1):
        cost_metrics = {}
        try:
            for c in COST_BPS:
                # Run only through the common selection boundary.
                end_idx = calendar.index(train_end_dt)
                m, daily, trades, checks_df, state = simulate_policy_window(
                    calendar, snapshots, open_maps, close_maps,
                    f, n, r, c,
                    start_index=0,
                    end_index=end_idx,
                    collect_ledger=True,
                    heartbeat_label="SELECTION",
                )
                cost_metrics[c] = m

            m10, m20, m50 = cost_metrics[10], cost_metrics[20], cost_metrics[50]
            robust_ratio = (m50["CAGR"] / m10["CAGR"]) if m10["CAGR"] > 0 else -np.inf
            eligible = bool(
                m20["CAGR"] >= MIN_SELECTION_CAGR
                and m20["MaxDD"] >= MAX_SELECTION_DD
                and m20["Sharpe"] >= MIN_SELECTION_SHARPE
                and m20["AnnualizedTurnover"] <= MAX_SELECTION_TURNOVER
                and MIN_SELECTION_CASH <= m20["AvgCashWeight"] <= MAX_SELECTION_CASH
                and m50["CAGR"] > 0
                and robust_ratio >= MIN_COST_ROBUSTNESS_RATIO
            )
            selection_rows.append({
                "FrequencySessions": f,
                "TopN": n,
                "Rebalance": r,
                "PolicyID": policy_id(f, n, r, 20),
                "CAGR_10": m10["CAGR"],
                "CAGR_20": m20["CAGR"],
                "CAGR_50": m50["CAGR"],
                "MaxDD_20": m20["MaxDD"],
                "Sharpe_20": m20["Sharpe"],
                "Sortino_20": m20["Sortino"],
                "Turnover_20": m20["AnnualizedTurnover"],
                "Cash_20": m20["AvgCashWeight"],
                "Gross_20": m20["AvgGrossExposure"],
                "FinalEquity_20": m20["FinalEquity"],
                "Cost_20": m20["TotalTransactionCost"],
                "CostRobustnessRatio_50vs10": robust_ratio,
                "Eligible": eligible,
            })
            print(
                f"SELECTION {k}/{total} | {policy_id(f,n,r,20)} | "
                f"CAGR20={m20['CAGR']:.3f} DD20={m20['MaxDD']:.3f} "
                f"Sharpe20={m20['Sharpe']:.3f} Turn={m20['AnnualizedTurnover']:.2f} "
                f"Eligible={eligible}", flush=True
            )
        except Exception as e:
            selection_rows.append({
                "FrequencySessions": f, "TopN": n, "Rebalance": r,
                "PolicyID": policy_id(f,n,r,20), "Eligible": False,
                "Error": str(e),
            })
            print(f"SELECTION ERROR {k}/{total}: {policy_id(f,n,r,20)} | {e}", flush=True)

    sel = pd.DataFrame(selection_rows)
    sel["Eligible"] = sel["Eligible"].fillna(False).astype(bool)
    eligible_count = int(sel["Eligible"].sum())
    print(f"Eligible structural policies: {eligible_count}/{len(configs)}", flush=True)
    if eligible_count == 0:
        sel.to_csv(OUTDIR / "phase12_selection_results.csv", index=False)
        raise RuntimeError("NO POLICY PASSED THE PREDEFINED SELECTION GATE")

    sel = selection_score(sel[sel["Eligible"]].copy())
    winner = sel.iloc[0].to_dict()
    wf = int(winner["FrequencySessions"])
    wn = int(winner["TopN"])
    wr = str(winner["Rebalance"])
    print(f"SELECTED POLICY: F{wf}_TOP{wn}_{wr}", flush=True)
    print(f"SelectionScore: {winner['SelectionScore']:.6f}", flush=True)

    # Re-run the selected structural policy on selection period at 20 bps to
    # capture the exact state at the OOS boundary. This is still selection data.
    train_end_idx = calendar.index(train_end_dt)
    train20, train_daily, train_trades, train_checks, train_state = simulate_policy_window(
        calendar, snapshots, open_maps, close_maps,
        wf, wn, wr, 20,
        start_index=0,
        end_index=train_end_idx,
        collect_ledger=True,
    )
    train_boundary_equity = train_state["equity"]

    # ---------- FINAL UNTOUCHED OOS ----------
    test_rows = []
    test_daily_all = []
    test_trades_all = []
    test_checks_all = []
    for c in COST_BPS:
        # Recreate the selection-boundary state at each cost. The policy itself
        # is already frozen; costs are not being used to select it.
        train_c, _, _, _, state_c = simulate_policy_window(
            calendar, snapshots, open_maps, close_maps,
            wf, wn, wr, c,
            start_index=0,
            end_index=train_end_idx,
            collect_ledger=True,
        )
        test_m, test_daily, test_trades, test_checks, _ = simulate_policy_window(
            calendar, snapshots, open_maps, close_maps,
            wf, wn, wr, c,
            start_index=test_start_index,
            end_index=len(calendar)-1,
            initial_positions=state_c["positions"],
            initial_cash=state_c["cash"],
            initial_last_close=state_c["last_close"],
            initial_prev_equity=state_c["equity"],
            previous_signal_dt=train_end_dt,
            collect_ledger=True,
        )
        test_m.update({
            "FrequencySessions": wf,
            "TopN": wn,
            "Rebalance": wr,
            "CostBpsPerSide": c,
            "SelectionEnd": str(train_end_dt.date()),
            "FinalOOSStart": str(calendar[test_start_index].date()),
            "InitialOOSCapital": state_c["equity"],
        })
        test_rows.append(test_m)
        if c == 20:
            test_daily_all = test_daily
            test_trades_all = test_trades
            test_checks_all = test_checks
        print(
            f"FINAL OOS C{c}: CAGR={test_m['CAGR']:.3f} DD={test_m['MaxDD']:.3f} "
            f"Sharpe={test_m['Sharpe']:.3f} Turn={test_m['AnnualizedTurnover']:.2f} "
            f"Final=${test_m['FinalEquity']:.2f}", flush=True
        )

    testdf = pd.DataFrame(test_rows)
    t10 = testdf.loc[testdf.CostBpsPerSide == 10].iloc[0]
    t20 = testdf.loc[testdf.CostBpsPerSide == 20].iloc[0]
    t50 = testdf.loc[testdf.CostBpsPerSide == 50].iloc[0]
    test_cost_ratio = float(t50.CAGR / t10.CAGR) if t10.CAGR > 0 else -np.inf

    final_test_pass = bool(
        t20.CAGR >= MIN_TEST_CAGR
        and t20.MaxDD >= MAX_TEST_DD
        and t20.Sharpe >= MIN_TEST_SHARPE
        and t20.AnnualizedTurnover <= MAX_TEST_TURNOVER
        and t50.CAGR > 0
        and test_cost_ratio >= MIN_COST_ROBUSTNESS_RATIO
    )

    # Technical checks across the final OOS run at 20bps.
    accounting_pass = bool(test_checks_all["AccountingIdentityError"].max() <= 1e-8)
    decomp_pass = bool(test_daily_all["ReturnDecompositionError"].max() <= 1e-8)
    gross_pass = bool(testdf["AvgGrossExposure"].max() <= GROSS_CAP + 1e-8)
    entry_pass = bool(testdf["MaxEntryPositionObserved"].max() <= MAX_POSITION + 1e-6)
    positive_pass = bool((testdf["FinalEquity"] > 0).all())
    nan_pass = bool(testdf.notna().all().all())

    checks = {
        "ConfiguredUniverse": len(DEFAULT_UNIVERSE),
        "ValidTickers": valid,
        "Failures": len(failures),
        "Snapshots": len(snapshots),
        "ReferenceSignalDates": len(ref_signals),
        "SelectionSignalDates": split_pos + 1,
        "FinalOOSReferenceSignalDates": len(ref_signals) - (split_pos + 1),
        "SelectionEnd": str(train_end_dt.date()),
        "FinalOOSStart": str(calendar[test_start_index].date()),
        "CandidateStructuralPolicies": len(configs),
        "EligibleStructuralPolicies": eligible_count,
        "SelectedPolicy": f"F{wf}_TOP{wn}_{wr}",
        "SelectionScore": float(winner["SelectionScore"]),
        "SelectionCriteriaFrozen": True,
        "FinalOOSUntouched": True,
        "FinalOOSAcceptancePASS": final_test_pass,
        "AccountingIdentityPASS": accounting_pass,
        "ReturnDecompositionPASS": decomp_pass,
        "GrossExposurePASS": gross_pass,
        "EntryPositionPASS": entry_pass,
        "PositiveFinalEquityPASS": positive_pass,
        "NoNaNCoreMetrics": nan_pass,
        "InitialCapital": INITIAL_CAPITAL,
        "TrainBoundaryEquity20bps": float(train_boundary_equity),
        "FinalOOSCostRobustnessRatio50vs10": test_cost_ratio,
        "RuntimeSeconds": time.time() - t0,
        "STATUS": bool(final_test_pass and accounting_pass and decomp_pass and gross_pass and entry_pass and positive_pass and nan_pass),
    }

    # Persist everything needed for audit/reproducibility.
    sel.to_csv(OUTDIR / "phase12_selection_ranked_eligible.csv", index=False)
    pd.DataFrame(selection_rows).to_csv(OUTDIR / "phase12_selection_all_policies.csv", index=False)
    testdf.to_csv(OUTDIR / "phase12_final_oos_results.csv", index=False)
    test_daily_all.to_csv(OUTDIR / "phase12_final_oos_daily_20bps.csv", index=False)
    test_trades_all.to_csv(OUTDIR / "phase12_final_oos_trades_20bps.csv", index=False)
    test_checks_all.to_csv(OUTDIR / "phase12_final_oos_checks_20bps.csv", index=False)
    pd.DataFrame(failures).to_csv(OUTDIR / "phase12_download_failures.csv", index=False)
    pd.DataFrame([winner]).to_csv(OUTDIR / "phase12_selected_policy.csv", index=False)
    with open(OUTDIR / "phase12_checks.json", "w", encoding="utf-8") as fh:
        json.dump(checks, fh, indent=2, default=lambda x: bool(x) if isinstance(x, (np.bool_,)) else float(x) if isinstance(x, np.floating) else int(x) if isinstance(x, np.integer) else x)
    (OUTDIR / "phase12_status.txt").write_text("PASS\n" if checks["STATUS"] else "FAIL\n", encoding="utf-8")

    print("\n--- SELECTED POLICY ---", flush=True)
    print(f"F{wf}_TOP{wn}_{wr}", flush=True)
    print(f"Selection score: {winner['SelectionScore']:.6f}", flush=True)
    print("\n--- FINAL OOS ---", flush=True)
    print(testdf[["CostBpsPerSide", "CAGR", "MaxDD", "Sharpe", "Sortino", "ProfitFactor", "FinalEquity", "AnnualizedTurnover", "AvgCashWeight", "AvgGrossExposure"]].to_string(index=False), flush=True)
    print("\n--- CHECKS ---", flush=True)
    for k, v in checks.items():
        print(f"{k}: {v}", flush=True)
    print(f"\nSTATUS: {'PASS' if checks['STATUS'] else 'FAIL'}", flush=True)
    return 0 if checks["STATUS"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

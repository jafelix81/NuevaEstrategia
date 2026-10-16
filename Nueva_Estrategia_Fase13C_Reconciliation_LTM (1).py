"""
FASE 13B — OOS STABILITY CORRECTIVE AUDIT — LONG-TERM MOMENTUM

Purpose
-------
Audit the selected Phase 12 policy on the untouched final OOS period without
changing the strategy or selecting new parameters.

FROZEN POLICY
-------------
F80_TOP20_PARTIAL50
- LTM = average rank of R100/R120/R140/R160
- Frequency = 80 sessions
- Top N = 20
- Rebalance = PARTIAL50
- Persistence buffer = +20 ranks
- Initial capital = $1,000
- Max entry position = 20%
- Gross exposure <= 100%
- Baseline cost = 20 bps per side

This phase DOES NOT re-select the strategy. Frequency/buffer variations are
stress diagnostics only. They are not candidates for a new winner.

Diagnostics
-----------
A. Final OOS by year and semester.
B. Daily loss sequences, worst rolling losses, drawdown duration/recovery.
C. Exposure/cash during drawdowns.
D. Concentration: positions and top-1/top-3/top-5 weights.
E. Dependence on top contributors: counterfactual removal of top 3/top 5
   positive contributors from the frozen OOS run.
F. Frequency stress: 60/70/80/90/100 sessions around frozen F80.
G. Persistence-buffer stress: +10/+15/+20/+25/+30 around frozen +20.
H. Monte Carlo block bootstrap of final-OOS daily returns and cycle returns.

IMPORTANT
---------
No parameter is selected from these diagnostics. Phase 13B also corrects the two implementation issues identified after the first Phase 13 run: partial/current-day data and an inert persistence buffer. Phase 13 answers:
"Does the already-selected strategy remain structurally credible, or is its
OOS result concentrated in a small number of periods/names/orderings?"

A PASS here is a research-stability PASS, not authorization for live trading.
"""

from __future__ import annotations

import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from Nueva_Estrategia_Fase11_Real1000_LTM_v4 import (
    DEFAULT_UNIVERSE,
    DISCOVERY_DATES,
    EMBARGO,
    MIN_CROSS_SECTION,
    INITIAL_CAPITAL,
    MAX_POSITION,
    GROSS_CAP,
    download_universe,
    build_price_maps,
    build_snapshots,
    portfolio_value,
    execute_rebalance,
)

RUN_ID = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
OUTDIR = Path("nueva_estrategia_phase13b_oos_stability_ltm")
OUTDIR.mkdir(parents=True, exist_ok=True)

# ---------------- FROZEN PHASE 12 POLICY ----------------
FROZEN_FREQUENCY = 80
FROZEN_TOP_N = 20
FROZEN_REBALANCE = "PARTIAL50"
FROZEN_BUFFER = 20
BASELINE_COST_BPS = 20

TRAIN_FRACTION = 0.80

# Diagnostic stress grids. These DO NOT select a replacement policy.
FREQUENCY_STRESS = [60, 70, 80, 90, 100]
BUFFER_STRESS = [10, 15, 20, 25, 30]

# Fixed Monte Carlo configuration for reproducibility.
MC_SEED = 13013
MC_PATHS = 5000
MC_BLOCK_DAYS = 20

# Conservative descriptive gates for the stability audit.
MIN_SUBPERIODS = 4
MIN_POSITIVE_SUBPERIOD_FRACTION = 0.50
MAX_STRESS_DD = -0.60


def policy_id(freq, top_n, rebalance, cost):
    return f"F{freq}_TOP{top_n}_{rebalance}_C{cost}"


def build_target_corrected(snapshot, top_n, positions, persistence_buffer=20):
    """
    Correct persistence-buffer interpretation for a fixed Top-N portfolio.

    The previous implementation filled all N slots with new Top-N names first,
    which made the persistence buffer inert. Here incumbent positions inside
    Top-N+buffer are protected first; remaining slots are filled by the highest
    ranked candidates. The target remains capped at Top-N names.

    This is an implementation correction only. The frozen Phase 12 policy
    remains F80/TOP20/PARTIAL50/+20; no parameter is re-selected.
    """
    if snapshot is None or snapshot.empty:
        return {}, list(positions.keys())

    g = snapshot.copy()
    g = g.sort_values("LTM", ascending=False).reset_index(drop=True)
    g["Rank"] = np.arange(1, len(g) + 1)

    rank_map = dict(zip(g["Ticker"], g["Rank"]))
    ordered = g["Ticker"].tolist()

    incumbents_protected = [
        t for t in positions
        if t in rank_map and rank_map[t] <= top_n + persistence_buffer
    ]
    incumbents_protected.sort(key=lambda t: rank_map[t])

    # Keep protected incumbents, but never exceed Top-N slots.
    target = incumbents_protected[:top_n]

    # Fill remaining slots with the highest-ranked names not already held.
    for t in ordered:
        if len(target) >= top_n:
            break
        if t not in target:
            target.append(t)

    target_set = set(target)
    exits = [t for t in positions if t not in target_set]

    # Equal-weight target, capped by MAX_POSITION. With Top-N=20 this is
    # 5%, safely below the 20% entry cap.
    if not target:
        return {}, exits

    base_weight = min(1.0 / len(target), MAX_POSITION)
    weights = {t: base_weight for t in target}

    return weights, exits


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
    growth = float(eq[-1] / base)
    cagr = growth ** (1.0 / years) - 1.0 if growth > 0 else -1.0

    sd = ret.std(ddof=1) if len(ret) > 1 else np.nan
    sharpe = float(ret.mean() / sd * np.sqrt(252)) if sd and np.isfinite(sd) else np.nan

    down = ret[ret < 0]
    dsd = down.std(ddof=1) if len(down) > 1 else np.nan
    sortino = float(ret.mean() / dsd * np.sqrt(252)) if dsd and np.isfinite(dsd) else np.nan

    gains = ret[ret > 0].sum()
    losses = -ret[ret < 0].sum()

    return {
        "FinalEquity": float(eq[-1]),
        "GrowthMultiple": growth,
        "CAGR": float(cagr),
        "MaxDD": float(dd.min()),
        "Sharpe": sharpe,
        "Sortino": sortino,
        "ProfitFactor": float(gains / losses) if losses > 0 else np.inf,
        "HitRate": float((ret > 0).mean()) if len(ret) else np.nan,
        "Days": int(len(daily)),
    }


def run_window(
    calendar,
    snapshots,
    open_maps,
    close_maps,
    frequency,
    top_n,
    rebalance,
    cost_bps,
    persistence_buffer,
    start_index,
    end_index,
    initial_positions=None,
    initial_cash=INITIAL_CAPITAL,
    initial_last_close=None,
    initial_prev_equity=None,
    previous_signal_dt=None,
    collect_positions=False,
):
    """Run one chronological window using the already-audited execution engine."""

    if end_index < start_index:
        raise RuntimeError("invalid simulation window")

    signal_dates = signal_dates_for(calendar, snapshots, frequency)
    signal_set = set(signal_dates)

    positions = dict(initial_positions or {})
    cash = float(initial_cash)
    last_close = dict(initial_last_close or {})
    prev_equity = float(
        initial_prev_equity if initial_prev_equity is not None else INITIAL_CAPITAL
    )

    trade_rows = []
    daily_rows = []
    position_rows = []
    check_rows = []

    max_entry_pos = 0.0
    max_marked_pos = 0.0
    stale_marks = 0
    gap = {"FULL": 1.0, "PARTIAL50": 0.5, "PARTIAL25": 0.25}[rebalance]

    pid = policy_id(frequency, top_n, rebalance, cost_bps)
    total_window = end_index - start_index + 1

    for step, i in enumerate(range(start_index, end_index + 1), 1):
        dt = calendar[i]

        if step == 1 or step == total_window or step % 500 == 0:
            print(
                f"SIM {pid} | {step}/{total_window} | date={dt.date()}",
                flush=True,
            )

        opens = open_maps.get(dt, {})
        closes = close_maps.get(dt, {})

        open_marks = dict(last_close)
        open_marks.update(opens)
        equity_before_trade = portfolio_value(positions, open_marks, cash)

        traded_buy = traded_sell = trade_cost = 0.0

        prev_dt = calendar[i - 1] if i > 0 else previous_signal_dt

        if prev_dt in signal_set:
            target, exits = build_target_corrected(
                snapshots[prev_dt],
                top_n,
                positions,
                persistence_buffer=persistence_buffer,
            )

            if opens:
                # Phase 11 execution engine expects `exits` to be a set because
                # it performs set union internally. The corrected target builder
                # returns a deterministic list, so normalize it at this boundary.
                exits = set(exits)

                positions, cash, traded_buy, traded_sell, trade_cost = execute_rebalance(
                    positions,
                    cash,
                    target,
                    exits,
                    opens,
                    equity_before_trade,
                    gap,
                    cost_bps,
                    prev_dt,
                    dt,
                    pid,
                    trade_rows,
                )

        post_open_marks = dict(last_close)
        post_open_marks.update(opens)
        post_open_equity = portfolio_value(positions, post_open_marks, cash)

        close_marks = dict(last_close)
        close_marks.update(closes)

        held_missing = [t for t in positions if t not in closes]
        stale_marks += len(held_missing)

        close_equity = portfolio_value(positions, close_marks, cash)
        gross_value = sum(
            sh * close_marks[t]
            for t, sh in positions.items()
            if t in close_marks
        )

        maxw = max(
            (
                sh * close_marks[t] / max(close_equity, 1e-12)
                for t, sh in positions.items()
                if t in close_marks
            ),
            default=0.0,
        )
        max_marked_pos = max(max_marked_pos, maxw)

        entry_marks = dict(last_close)
        entry_marks.update(opens)
        entry_equity = portfolio_value(positions, entry_marks, cash)

        entry_maxw = max(
            (
                sh * entry_marks[t] / max(entry_equity, 1e-12)
                for t, sh in positions.items()
                if t in entry_marks
            ),
            default=0.0,
        )
        max_entry_pos = max(max_entry_pos, entry_maxw)

        overnight = (
            equity_before_trade / prev_equity - 1.0
            if prev_equity > 0 else np.nan
        )
        execution = (
            post_open_equity / equity_before_trade - 1.0
            if equity_before_trade > 0 else np.nan
        )
        intraday = (
            close_equity / post_open_equity - 1.0
            if post_open_equity > 0 else np.nan
        )
        daily_ret = (
            close_equity / prev_equity - 1.0
            if prev_equity > 0 else np.nan
        )

        vals = [overnight, execution, intraday, daily_ret]
        decomp = (
            abs(
                (1 + overnight)
                * (1 + execution)
                * (1 + intraday)
                - (1 + daily_ret)
            )
            if all(np.isfinite(x) for x in vals)
            else np.nan
        )

        accounting = abs((cash + gross_value) - close_equity)

        daily_rows.append({
            "Date": str(dt.date()),
            "EquityClose": close_equity,
            "PreviousCloseEquity": prev_equity,
            "OpenEquityBeforeTrade": equity_before_trade,
            "EquityAfterOpenExecution": post_open_equity,
            "DailyReturn": daily_ret,
            "OvernightReturn": overnight,
            "ExecutionReturn": execution,
            "IntradayReturn": intraday,
            "ReturnDecompositionError": decomp,
            "Cash": cash,
            "GrossMarketValue": gross_value,
            "CashWeight": cash / max(close_equity, 1e-12),
            "GrossExposure": gross_value / max(close_equity, 1e-12),
            "Positions": len(positions),
            "BuyNotional": traded_buy,
            "SellNotional": traded_sell,
            "TransactionCost": trade_cost,
            "HeldWithoutFreshClose": len(held_missing),
            "MaxMarkedPositionWeight": maxw,
            "MaxEntryPositionWeightObservedToDate": max_entry_pos,
        })

        if collect_positions:
            for t, sh in positions.items():
                if t in close_marks and np.isfinite(close_marks[t]):
                    value = sh * close_marks[t]
                    position_rows.append({
                        "Date": str(dt.date()),
                        "Ticker": t,
                        "Shares": sh,
                        "Close": close_marks[t],
                        "Value": value,
                        "Weight": value / max(close_equity, 1e-12),
                    })

        check_rows.append({
            "Date": str(dt.date()),
            "AccountingIdentityError": accounting,
            "ReturnDecompositionError": decomp,
            "GrossExposure": gross_value / max(close_equity, 1e-12),
            "MaxMarkedPositionWeight": maxw,
            "MaxEntryPositionWeightObservedToDate": max_entry_pos,
            "HeldWithoutFreshClose": len(held_missing),
        })

        prev_equity = close_equity
        last_close.update(closes)

    daily = pd.DataFrame(daily_rows)
    trades = pd.DataFrame(trade_rows)
    positions_df = pd.DataFrame(position_rows)
    checks = pd.DataFrame(check_rows)

    if daily.empty:
        raise RuntimeError("empty daily ledger")

    m = metric_summary(
        daily,
        initial_prev_equity if initial_prev_equity is not None else INITIAL_CAPITAL,
    )

    avg_equity = max(float(daily["EquityClose"].mean()), 1e-12)
    years = max(len(daily) / 252.0, 1e-12)

    if not trades.empty:
        buy_mask = trades["Side"].astype(str).str.startswith("BUY")
        sell_mask = trades["Side"].astype(str).str.startswith("SELL")
        total_buy = float(trades.loc[buy_mask, "Notional"].sum())
        total_sell = float(trades.loc[sell_mask, "Notional"].sum())
        total_cost = float(trades["Cost"].sum())
    else:
        total_buy = total_sell = total_cost = 0.0

    m.update({
        "DailyObservations": len(daily),
        "TotalBuyNotional": total_buy,
        "TotalSellNotional": total_sell,
        "TotalTransactionCost": total_cost,
        "AnnualizedTurnover": (
            ((total_buy + total_sell) / avg_equity) / years
        ),
        "AnnualizedBuyTurnover": (total_buy / avg_equity) / years,
        "AnnualizedSellTurnover": (total_sell / avg_equity) / years,
        "AvgPositions": float(daily["Positions"].mean()),
        "AvgCashWeight": float(daily["CashWeight"].mean()),
        "AvgGrossExposure": float(daily["GrossExposure"].mean()),
        "MaxEntryPositionObserved": float(max_entry_pos),
        "MaxDailyMarkedPositionObserved": float(max_marked_pos),
        "MaxAccountingIdentityError": float(
            checks["AccountingIdentityError"].max()
        ),
        "MaxReturnDecompositionError": float(
            daily["ReturnDecompositionError"].max()
        ),
        "HeldWithoutFreshCloseMarks": int(stale_marks),
    })

    state = {
        "positions": positions,
        "cash": cash,
        "last_close": last_close,
        "equity": prev_equity,
        "last_index": end_index,
    }

    return m, daily, trades, positions_df, checks, state


def last_fully_closed_date(calendar):
    """
    Exclude the current calendar date. Phase 13B must only use fully closed
    daily bars, so a morning run on date D can never consume D's partial bar.
    """
    today_utc = pd.Timestamp.now(tz="UTC").tz_localize(None).normalize()
    eligible = [d for d in calendar if pd.Timestamp(d).normalize() < today_utc]
    if not eligible:
        raise RuntimeError("No fully closed daily date available")
    return max(eligible)


def split_boundary(calendar, snapshots):
    ref = signal_dates_for(calendar, snapshots, 20)
    if len(ref) < 100:
        raise RuntimeError("reference signal stream too short")

    split_pos = int(math.floor(len(ref) * TRAIN_FRACTION)) - 1
    split_pos = max(1, min(split_pos, len(ref) - 2))

    end_dt = ref[split_pos]
    test_start = calendar.index(end_dt) + 1
    return ref, split_pos, end_dt, test_start


def run_oos_policy(
    calendar,
    snapshots,
    open_maps,
    close_maps,
    frequency,
    top_n,
    rebalance,
    cost_bps,
    persistence_buffer,
    train_end_idx,
    test_start_idx,
    train_end_dt,
    collect_positions=False,
):
    train_m, _, _, _, _, state = run_window(
        calendar,
        snapshots,
        open_maps,
        close_maps,
        frequency,
        top_n,
        rebalance,
        cost_bps,
        persistence_buffer,
        0,
        train_end_idx,
        collect_positions=False,
    )

    test_m, test_daily, test_trades, test_positions, test_checks, test_state = run_window(
        calendar,
        snapshots,
        open_maps,
        close_maps,
        frequency,
        top_n,
        rebalance,
        cost_bps,
        persistence_buffer,
        test_start_idx,
        len(calendar) - 1,
        initial_positions=state["positions"],
        initial_cash=state["cash"],
        initial_last_close=state["last_close"],
        initial_prev_equity=state["equity"],
        previous_signal_dt=train_end_dt,
        collect_positions=collect_positions,
    )

    return (
        train_m,
        test_m,
        test_daily,
        test_trades,
        test_positions,
        test_checks,
        state,
        test_state,
    )


def drawdown_analysis(daily):
    x = daily.copy()
    x["Date"] = pd.to_datetime(x["Date"])

    eq = x["EquityClose"].astype(float)
    peak = eq.cummax()
    dd = eq / peak - 1.0
    x["Drawdown"] = dd

    min_i = int(dd.idxmin())
    max_dd = float(dd.min())
    trough_date = x.loc[min_i, "Date"]
    peak_before = float(peak.loc[min_i])

    after = x.loc[min_i:]
    recovery = after[after["EquityClose"] >= peak_before]
    recovery_date = recovery.iloc[0]["Date"] if not recovery.empty else None

    underwater = dd < -1e-12
    runs = []
    start = None

    for i, flag in enumerate(underwater.to_numpy()):
        if flag and start is None:
            start = i
        elif not flag and start is not None:
            runs.append((start, i - 1))
            start = None

    if start is not None:
        runs.append((start, len(x) - 1))

    if runs:
        longest = max(runs, key=lambda ab: ab[1] - ab[0] + 1)
        longest_days = longest[1] - longest[0] + 1
        longest_start = x.iloc[longest[0]]["Date"]
        longest_end = x.iloc[longest[1]]["Date"]
    else:
        longest_days = 0
        longest_start = longest_end = None

    return {
        "MaxDD": max_dd,
        "MaxDDDate": str(trough_date.date()),
        "MaxDDRecoveryDate": (
            str(recovery_date.date()) if recovery_date is not None else None
        ),
        "MaxDDRecoveryDaysFromTrough": (
            int((recovery_date - trough_date).days)
            if recovery_date is not None else None
        ),
        "LongestUnderwaterCalendarDays": int(longest_days),
        "LongestUnderwaterStart": (
            str(longest_start.date()) if longest_start is not None else None
        ),
        "LongestUnderwaterEnd": (
            str(longest_end.date()) if longest_end is not None else None
        ),
        "PeakEquityBeforeMaxDD": peak_before,
        "TroughEquity": float(eq.loc[min_i]),
    }, x


def loss_sequence_analysis(daily):
    r = daily["DailyReturn"].astype(float).to_numpy()
    r = r[np.isfinite(r)]

    roll5 = pd.Series(r).rolling(5).apply(
        lambda a: np.prod(1.0 + a) - 1.0,
        raw=True,
    )
    roll10 = pd.Series(r).rolling(10).apply(
        lambda a: np.prod(1.0 + a) - 1.0,
        raw=True,
    )

    streaks = []
    cur = 0
    for val in r:
        if val < 0:
            cur += 1
        else:
            if cur:
                streaks.append(cur)
            cur = 0

    if cur:
        streaks.append(cur)

    neg = r[r < 0]

    return {
        "WorstDailyReturn": float(np.min(r)),
        "Worst5DayReturn": float(roll5.min()),
        "Worst10DayReturn": float(roll10.min()),
        "MaxConsecutiveNegativeDays": int(max(streaks) if streaks else 0),
        "NegativeDays": int((r < 0).sum()),
        "PositiveDays": int((r > 0).sum()),
        "ZeroDays": int((r == 0).sum()),
        "DailyLossP05": (
            float(np.quantile(neg, 0.05)) if len(neg) else np.nan
        ),
    }


def exposure_drawdown_analysis(daily):
    x = daily.copy()
    eq = x["EquityClose"].astype(float)
    x["Drawdown"] = eq / eq.cummax() - 1.0

    rows = []
    for threshold in [-0.05, -0.10, -0.20, -0.25]:
        g = x[x["Drawdown"] <= threshold]
        rows.append({
            "DrawdownThreshold": threshold,
            "Days": len(g),
            "AvgCashWeight": (
                float(g["CashWeight"].mean()) if not g.empty else np.nan
            ),
            "AvgGrossExposure": (
                float(g["GrossExposure"].mean()) if not g.empty else np.nan
            ),
            "AvgPositions": (
                float(g["Positions"].mean()) if not g.empty else np.nan
            ),
            "AvgDailyReturn": (
                float(g["DailyReturn"].mean()) if not g.empty else np.nan
            ),
        })

    return pd.DataFrame(rows)


def concentration_analysis(positions_df):
    if positions_df.empty:
        return {
            "AvgPositionsFromPositionLedger": np.nan,
            "MaxPositionWeight": np.nan,
            "AvgTop1Weight": np.nan,
            "AvgTop3Weight": np.nan,
            "AvgTop5Weight": np.nan,
            "MaxTop3Weight": np.nan,
            "MaxTop5Weight": np.nan,
        }

    rows = []
    for dt, g in positions_df.groupby("Date"):
        w = np.sort(g["Weight"].astype(float).to_numpy())[::-1]
        rows.append({
            "Date": dt,
            "Positions": len(w),
            "Top1": float(w[:1].sum()),
            "Top3": float(w[:3].sum()),
            "Top5": float(w[:5].sum()),
            "MaxPosition": float(w[0]) if len(w) else 0.0,
        })

    d = pd.DataFrame(rows)

    return {
        "AvgPositionsFromPositionLedger": float(d["Positions"].mean()),
        "MaxPositionWeight": float(d["MaxPosition"].max()),
        "AvgTop1Weight": float(d["Top1"].mean()),
        "AvgTop3Weight": float(d["Top3"].mean()),
        "AvgTop5Weight": float(d["Top5"].mean()),
        "MaxTop3Weight": float(d["Top3"].max()),
        "MaxTop5Weight": float(d["Top5"].max()),
    }


def contributor_analysis(positions_df, close_maps):
    """
    Close-to-close ticker P&L proxy.

    This is deliberately labeled a proxy: it measures dependence of price
    performance on individual names and does not allocate transaction costs to
    individual tickers.
    """
    if positions_df.empty:
        return pd.DataFrame(), {}

    # Phase 11 price maps use normalized pandas Timestamps as keys. Keep the
    # same representation here to avoid a date-vs-Timestamp lookup mismatch.
    pos_map = {
        (pd.Timestamp(row.Date).normalize(), row.Ticker): float(row.Shares)
        for row in positions_df.itertuples()
    }

    dates = sorted(
        pd.Timestamp(x).normalize()
        for x in positions_df["Date"].unique()
    )
    contrib = {}

    for idx in range(1, len(dates)):
        prev = dates[idx - 1]
        curr = dates[idx]

        tickers = {
            t for (d, t) in pos_map.keys()
            if d == prev or d == curr
        }

        for ticker in tickers:
            shares_prev = pos_map.get((prev, ticker), 0.0)
            if shares_prev <= 0:
                continue

            p_prev = close_maps.get(prev, {}).get(ticker)
            p_curr = close_maps.get(curr, {}).get(ticker)

            if (
                p_prev is not None
                and p_curr is not None
                and np.isfinite(p_prev)
                and np.isfinite(p_curr)
            ):
                contrib[ticker] = contrib.get(ticker, 0.0) + (
                    shares_prev * (p_curr - p_prev)
                )

    out = pd.DataFrame(
        [{"Ticker": t, "PricePnLProxy": v} for t, v in contrib.items()]
    )

    if out.empty:
        return out, {}

    out = out.sort_values("PricePnLProxy", ascending=False).reset_index(drop=True)
    out["PositiveContribution"] = out["PricePnLProxy"].clip(lower=0.0)

    positive_total = float(out["PositiveContribution"].sum())

    out["ShareOfPositivePricePnL"] = (
        out["PositiveContribution"] / positive_total
        if positive_total > 0 else 0.0
    )

    meta = {
        "TotalPricePnLProxy": float(out["PricePnLProxy"].sum()),
        "PositivePricePnLProxy": positive_total,
        "Top3PositiveShare": (
            float(out.head(3)["PositiveContribution"].sum() / positive_total)
            if positive_total > 0 else np.nan
        ),
        "Top5PositiveShare": (
            float(out.head(5)["PositiveContribution"].sum() / positive_total)
            if positive_total > 0 else np.nan
        ),
        "Top10PositiveShare": (
            float(out.head(10)["PositiveContribution"].sum() / positive_total)
            if positive_total > 0 else np.nan
        ),
    }

    return out, meta


def counterfactual_remove_contributors(
    contributor_table,
    calendar,
    snapshots,
    open_maps,
    close_maps,
    train_end_idx,
    test_start_idx,
    train_end_dt,
    remove_n,
):
    if contributor_table.empty:
        return None

    removed = contributor_table.head(remove_n)["Ticker"].tolist()
    allowed = set(DEFAULT_UNIVERSE) - set(removed)

    # Keep the frozen LTM values/ranks. We only remove the selected names from
    # the investable universe; this is a concentration stress, not a new model.
    snap_cf = {}
    for dt, g in snapshots.items():
        gg = g[g["Ticker"].isin(allowed)].copy()
        if len(gg) >= MIN_CROSS_SECTION:
            snap_cf[dt] = gg

    open_cf = {
        dt: {t: p for t, p in mp.items() if t in allowed}
        for dt, mp in open_maps.items()
    }
    close_cf = {
        dt: {t: p for t, p in mp.items() if t in allowed}
        for dt, mp in close_maps.items()
    }

    _, _, _, _, _, train_state = run_window(
        calendar,
        snap_cf,
        open_cf,
        close_cf,
        FROZEN_FREQUENCY,
        FROZEN_TOP_N,
        FROZEN_REBALANCE,
        BASELINE_COST_BPS,
        FROZEN_BUFFER,
        0,
        train_end_idx,
        collect_positions=False,
    )

    m, daily, *_ = run_window(
        calendar,
        snap_cf,
        open_cf,
        close_cf,
        FROZEN_FREQUENCY,
        FROZEN_TOP_N,
        FROZEN_REBALANCE,
        BASELINE_COST_BPS,
        FROZEN_BUFFER,
        test_start_idx,
        len(calendar) - 1,
        initial_positions=train_state["positions"],
        initial_cash=train_state["cash"],
        initial_last_close=train_state["last_close"],
        initial_prev_equity=train_state["equity"],
        previous_signal_dt=train_end_dt,
        collect_positions=False,
    )

    m["RemovedN"] = remove_n
    m["RemovedTickers"] = ",".join(removed)
    return m


def cycle_returns(daily, frequency):
    r = daily["DailyReturn"].fillna(0.0).to_numpy()
    rows = []

    for i in range(0, len(r), frequency):
        block = r[i:i + frequency]
        if len(block) == 0:
            continue

        rows.append({
            "Cycle": len(rows) + 1,
            "Days": len(block),
            "CycleReturn": float(np.prod(1.0 + block) - 1.0),
        })

    return pd.DataFrame(rows)


def bootstrap_paths(returns, n_paths, block_len, seed):
    """Circular moving-block bootstrap preserving short-run dependence."""
    r = np.asarray(returns, dtype=float)
    r = r[np.isfinite(r)]

    if len(r) < block_len * 2:
        raise RuntimeError("too few returns for block bootstrap")

    rng = np.random.default_rng(seed)
    n = len(r)
    paths = np.empty((n_paths, n), dtype=float)

    for p in range(n_paths):
        out = np.empty(n, dtype=float)
        j = 0

        while j < n:
            start = int(rng.integers(0, n))
            take = min(block_len, n - j)
            idx = (start + np.arange(take)) % n
            out[j:j + take] = r[idx]
            j += take

        paths[p] = out

    return paths


def monte_carlo_summary(daily, initial_equity):
    r = daily["DailyReturn"].astype(float).to_numpy()
    paths = bootstrap_paths(r, MC_PATHS, MC_BLOCK_DAYS, MC_SEED)

    n = paths.shape[1]
    years = max(n / 252.0, 1e-12)

    terminal = np.prod(1.0 + paths, axis=1)
    cagr = terminal ** (1.0 / years) - 1.0

    curves = np.cumprod(1.0 + paths, axis=1)
    peaks = np.maximum.accumulate(curves, axis=1)
    maxdd = (curves / peaks - 1.0).min(axis=1)

    observed_cagr = (
        (daily["EquityClose"].iloc[-1] / initial_equity)
        ** (1.0 / years) - 1.0
    )

    q = lambda a, p: float(np.quantile(a, p))

    return {
        "Paths": MC_PATHS,
        "BlockDays": MC_BLOCK_DAYS,
        "ObservedCAGR": float(observed_cagr),
        "CAGR_P05": q(cagr, 0.05),
        "CAGR_P25": q(cagr, 0.25),
        "CAGR_Median": q(cagr, 0.50),
        "CAGR_P75": q(cagr, 0.75),
        "CAGR_P95": q(cagr, 0.95),
        "MaxDD_P05": q(maxdd, 0.05),
        "MaxDD_P25": q(maxdd, 0.25),
        "MaxDD_Median": q(maxdd, 0.50),
        "MaxDD_P75": q(maxdd, 0.75),
        "MaxDD_P95": q(maxdd, 0.95),
        "ProbabilityCAGRPositive": float((cagr > 0).mean()),
        "ProbabilityMaxDDWorseThanMinus50": float((maxdd <= -0.50).mean()),
        "ProbabilityMaxDDWorseThanMinus40": float((maxdd <= -0.40).mean()),
    }


def subperiod_report(daily):
    x = daily.copy()
    x["Date"] = pd.to_datetime(x["Date"])
    x["Year"] = x["Date"].dt.year
    x["Half"] = np.where(x["Date"].dt.month <= 6, "H1", "H2")

    rows = []

    for (year, half), g in x.groupby(["Year", "Half"], sort=True):
        m = metric_summary(g, float(g["EquityClose"].iloc[0]))

        rows.append({
            "Period": f"{int(year)}-{half}",
            "Start": str(g["Date"].iloc[0].date()),
            "End": str(g["Date"].iloc[-1].date()),
            "Days": len(g),
            "CAGR": m["CAGR"],
            "MaxDDWithinPeriod": m["MaxDD"],
            "Sharpe": m["Sharpe"],
            "HitRate": m["HitRate"],
            "AvgCashWeight": float(g["CashWeight"].mean()),
            "AvgGrossExposure": float(g["GrossExposure"].mean()),
            "PositivePeriod": bool(m["CAGR"] > 0),
        })

    return pd.DataFrame(rows)


def json_default(x):
    if isinstance(x, (np.bool_, bool)):
        return bool(x)
    if isinstance(x, np.integer):
        return int(x)
    if isinstance(x, np.floating):
        return float(x)
    if isinstance(x, (pd.Timestamp, datetime)):
        return str(x)
    if x is None:
        return None
    try:
        if pd.isna(x):
            return None
    except Exception:
        pass
    return x



# Phase 13C embeds the audited Phase 13B engine directly so the GitHub workflow
# does not depend on a separate Phase 13B .py file being present in the repository.
from Nueva_Estrategia_Fase11_Real1000_LTM_v4 import build_target as phase12_target

RUN_ID = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
OUTDIR = Path("nueva_estrategia_phase13c_reconciliation_ltm")
OUTDIR.mkdir(parents=True, exist_ok=True)
FREQUENCY = 80
TOP_N = 20
REBALANCE = "PARTIAL50"
BUFFER = 20
COSTS = [10, 20, 50]

def metric_row(impl, cost, m):
    return {
        "Implementation": impl,
        "CostBps": int(cost),
        "CAGR": float(m["CAGR"]),
        "MaxDD": float(m["MaxDD"]),
        "Sharpe": float(m["Sharpe"]),
        "Sortino": float(m["Sortino"]),
        "AnnualizedTurnover": float(m["AnnualizedTurnover"]),
        "FinalEquity": float(m["FinalEquity"]),
        "AvgCashWeight": float(m["AvgCashWeight"]),
        "AvgGrossExposure": float(m["AvgGrossExposure"]),
        "MaxEntryPositionObserved": float(m["MaxEntryPositionObserved"]),
        "MaxDailyMarkedPositionObserved": float(m["MaxDailyMarkedPositionObserved"]),
        "MaxAccountingIdentityError": float(m["MaxAccountingIdentityError"]),
        "MaxReturnDecompositionError": float(m["MaxReturnDecompositionError"]),
        "HeldWithoutFreshCloseMarks": int(m["HeldWithoutFreshCloseMarks"]),
    }


def run_impl(label, builder, calendar, snapshots, open_maps, close_maps,
             train_end_idx, test_start_idx, train_end_dt, cost):
    # run_oos_policy resolves build_target_corrected through the p13 module
    # namespace. Temporarily substitute the exact builder for the selected
    # implementation, then restore the corrected builder immediately.
    old_builder = build_target_corrected
    build_target_corrected = builder
    try:
        out = run_oos_policy(
            calendar,
            snapshots,
            open_maps,
            close_maps,
            FREQUENCY,
            TOP_N,
            REBALANCE,
            cost,
            BUFFER,
            train_end_idx,
            test_start_idx,
            train_end_dt,
            collect_positions=False,
        )
    finally:
        build_target_corrected = old_builder

    train_m, test_m, daily, trades, positions, checks, train_state, test_state = out
    return train_m, test_m, daily, trades, positions, checks


def main():
    t0 = time.time()
    print("FASE 13C — RECONCILIACIÓN PHASE 12 vs BUFFER CORREGIDO — LTM", flush=True)
    print("=" * 82, flush=True)
    print(f"RUN_ID: {RUN_ID}", flush=True)
    print("FROZEN POLICY: F80_TOP20_PARTIAL50 | buffer +20", flush=True)
    print("A = exact Phase 12 target semantics | B = corrected +20 semantics", flush=True)
    print("No re-selection | No Kelly | No stops | No new factors | No production", flush=True)

    data, failures = download_universe(DEFAULT_UNIVERSE)
    valid = len(data)
    if valid < MIN_CROSS_SECTION:
        raise RuntimeError(f"valid universe too small: {valid}")

    calendar = sorted(set(
        d for df in data.values() for d in df["Date"].dropna().tolist()
    ))
    closed_cutoff = last_fully_closed_date(calendar)
    calendar = [d for d in calendar if pd.Timestamp(d).normalize() <= closed_cutoff]

    open_maps, close_maps = build_price_maps(data)
    snapshots = build_snapshots(data, calendar)

    ref, split_pos, train_end_dt, test_start_idx = split_boundary(calendar, snapshots)
    train_end_idx = calendar.index(train_end_dt)

    print(
        f"Valid tickers={valid} | failures={len(failures)} | snapshots={len(snapshots)}",
        flush=True,
    )
    print(
        f"LastFullyClosedDate={closed_cutoff.date()} | SelectionEnd={train_end_dt.date()} | "
        f"FinalOOSStart={calendar[test_start_idx].date()}",
        flush=True,
    )
    print(
        f"ReferenceSignalDates={len(ref)} | Selection={split_pos + 1} | "
        f"FinalOOS={len(ref) - split_pos - 1}",
        flush=True,
    )

    rows = []
    reconciliation = []

    for cost in COSTS:
        print(f"\n--- COST {cost} BPS ---", flush=True)
        results = {}
        for label, builder in [
            ("ACTUAL_PHASE12", phase12_target),
            ("CORRECTED_BUFFER20", build_target_corrected),
        ]:
            print(f"Running {label} C{cost}...", flush=True)
            train_m, test_m, daily, trades, positions, checks = run_impl(
                label, builder, calendar, snapshots, open_maps, close_maps,
                train_end_idx, test_start_idx, train_end_dt, cost,
            )
            rows.append(metric_row(label, cost, test_m))
            results[label] = (test_m, daily, trades, positions, checks)
            print(
                f"{label} | CAGR={test_m['CAGR']:.4f} DD={test_m['MaxDD']:.4f} "
                f"Sharpe={test_m['Sharpe']:.4f} Turn={test_m['AnnualizedTurnover']:.4f} "
                f"Final=${test_m['FinalEquity']:.2f} Cash={test_m['AvgCashWeight']:.4f}",
                flush=True,
            )

        a = results["ACTUAL_PHASE12"][0]
        b = results["CORRECTED_BUFFER20"][0]
        reconciliation.append({
            "CostBps": cost,
            "CAGR_AbsDiff": abs(a["CAGR"] - b["CAGR"]),
            "CAGR_RelDiff_vs_A": abs(a["CAGR"] - b["CAGR"]) / max(abs(a["CAGR"]), 1e-12),
            "MaxDD_AbsDiff": abs(a["MaxDD"] - b["MaxDD"]),
            "Sharpe_AbsDiff": abs(a["Sharpe"] - b["Sharpe"]),
            "Turnover_AbsDiff": abs(a["AnnualizedTurnover"] - b["AnnualizedTurnover"]),
            "FinalEquity_AbsDiff": abs(a["FinalEquity"] - b["FinalEquity"]),
            "FinalEquity_RelDiff_vs_A": abs(a["FinalEquity"] - b["FinalEquity"]) / max(abs(a["FinalEquity"]), 1e-12),
        })

        # Save daily ledgers separately so the exact path comparison is auditable.
        results["ACTUAL_PHASE12"][1].to_csv(OUTDIR / f"daily_actual_phase12_c{cost}.csv", index=False)
        results["CORRECTED_BUFFER20"][1].to_csv(OUTDIR / f"daily_corrected_buffer20_c{cost}.csv", index=False)

    metrics = pd.DataFrame(rows)
    diffs = pd.DataFrame(reconciliation)
    metrics.to_csv(OUTDIR / "phase13c_metrics.csv", index=False)
    diffs.to_csv(OUTDIR / "phase13c_reconciliation.csv", index=False)

    # Technical integrity: both implementations/costs completed, no NaN core
    # metrics, accounting identities and return decompositions passed, same cutoff.
    core_cols = ["CAGR", "MaxDD", "Sharpe", "AnnualizedTurnover", "FinalEquity"]
    no_nan = bool(not metrics[core_cols].isna().any().any())
    accounting_ok = bool((metrics["MaxAccountingIdentityError"] <= 1e-8).all())
    decomp_ok = bool((metrics["MaxReturnDecompositionError"] <= 1e-10).all())
    positive_eq = bool((metrics["FinalEquity"] > 0).all())
    coverage_ok = bool(len(metrics) == len(COSTS) * 2)

    # This is intentionally descriptive, not a selection gate. Use a 10%
    # relative CAGR tolerance as a material-difference warning, plus 5pp DD,
    # 0.15 Sharpe or 10% final-equity difference.
    diffs["MaterialDifferenceWarning"] = (
        (diffs["CAGR_RelDiff_vs_A"] > 0.10)
        | (diffs["MaxDD_AbsDiff"] > 0.05)
        | (diffs["Sharpe_AbsDiff"] > 0.15)
        | (diffs["FinalEquity_RelDiff_vs_A"] > 0.10)
    )
    material = bool(diffs["MaterialDifferenceWarning"].any())

    checks = {
        "ConfiguredUniverse": len(DEFAULT_UNIVERSE),
        "ValidTickers": valid,
        "Failures": len(failures),
        "Snapshots": len(snapshots),
        "ReferenceSignalDates": len(ref),
        "SelectionSignalDates": split_pos + 1,
        "FinalOOSReferenceSignalDates": len(ref) - split_pos - 1,
        "SelectionEnd": str(train_end_dt.date()),
        "FinalOOSStart": str(calendar[test_start_idx].date()),
        "LastFullyClosedDate": str(closed_cutoff.date()),
        "FrozenPolicy": "F80_TOP20_PARTIAL50",
        "ActualPhase12Semantics": True,
        "CorrectedBuffer20Semantics": True,
        "BothImplementationsRun": coverage_ok,
        "NoNaNCoreMetrics": no_nan,
        "AccountingIdentityPASS": accounting_ok,
        "ReturnDecompositionPASS": decomp_ok,
        "PositiveFinalEquityPASS": positive_eq,
        "MaterialDifferenceWarning": material,
        "NoReselection": True,
        "TechnicalIntegrityPASS": bool(coverage_ok and no_nan and accounting_ok and decomp_ok and positive_eq),
        "Interpretation": (
            "CORRECTED_IMPLEMENTATION_DIFFERS_MATERIALLY_FROM_PHASE12; "
            "PHASE12_VALIDATES_ONLY_ACTUAL_IMPLEMENTATION"
            if material else
            "CORRECTED_IMPLEMENTATION_IS_CLOSE_TO_PHASE12; PHASE12_RESULT_REMAINS_REPRESENTATIVE"
        ),
        "RuntimeSeconds": time.time() - t0,
    }
    with open(OUTDIR / "phase13c_checks.json", "w", encoding="utf-8") as f:
        json.dump(checks, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 82, flush=True)
    print("RECONCILIATION SUMMARY", flush=True)
    print("=" * 82, flush=True)
    print(metrics.to_string(index=False), flush=True)
    print("\nDIFFERENCES A vs B", flush=True)
    print(diffs.to_string(index=False), flush=True)
    print("\nCHECKS", flush=True)
    for k, v in checks.items():
        print(f"{k}: {v}", flush=True)

    if not checks["TechnicalIntegrityPASS"]:
        raise RuntimeError("Phase 13C technical integrity failed")

    # Do NOT fail the run merely because the corrected implementation differs:
    # the purpose of this phase is to reveal that distinction explicitly.
    print(
        "\nSTATUS: PASS_TECHNICAL_RECONCILIATION | "
        + ("MATERIAL_DIFFERENCE_REQUIRES_NEW_VALIDATION" if material else "NO_MATERIAL_DIFFERENCE"),
        flush=True,
    )


if __name__ == "__main__":
    main()

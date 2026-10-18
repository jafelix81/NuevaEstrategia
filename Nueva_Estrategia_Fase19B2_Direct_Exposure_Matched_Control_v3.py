"""FASE 19B.2 — DIRECT EXPOSURE-MATCHED CONTROL v3
Diagnostic only. Frozen F80_TOP20_PARTIAL50 mechanics.

Purpose: separate stock-selection value from the effect of lower gross exposure.
A) Predictor: frozen F80 with an ex-ante entry filter (MAE10 or QUICK).
B) Control: frozen F80 stock selection, but target gross is directly matched
   to the predictor's realized post-open gross exposure at each OOS rebalance.

Important:
- Full history is simulated to carry the exact portfolio state into OOS.
- Before the OOS boundary, BOTH paths run the frozen baseline F80 policy.
- Factors use only history <= DateSignal.
- The predictor executes its actual filtered target (no scaling).
- The control scales the unfiltered F80 target to match predictor realized
  post-open gross exposure. The scale is solved using only same-open data.
- OOS metrics are computed from the selection-end close through final OOS.
- This phase is diagnostic only; it cannot alter official F80.
"""
from __future__ import annotations
import math, time
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
import pandas as pd

from Nueva_Estrategia_Fase12_FinalOOS_Selection_LTM import (
    DEFAULT_UNIVERSE, DISCOVERY_DATES, EMBARGO,
    INITIAL_CAPITAL, download_universe, build_price_maps, build_snapshots,
    portfolio_value, build_target, execute_rebalance,
)

POLICY = "F80_TOP20_PARTIAL50"
FREQ, TOPN, REBALANCE = 80, 20, "PARTIAL50"
GAP = 0.5
TRAIN_FRACTION = 0.80
TOL = 0.01
FILTERS = {
    "MAE10": [("R120", "HIGHER"), ("VOL20", "HIGHER")],
    "QUICK": [("R120", "HIGHER"), ("DIST_200D", "HIGHER")],
}
OUTDIR = Path("nueva_estrategia_phase19b2_direct_exposure_v3")
OUTDIR.mkdir(exist_ok=True)
RUN_ID = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def signal_dates_for(calendar, snapshots):
    base = calendar[DISCOVERY_DATES + EMBARGO:]
    return [d for d in base[::FREQ] if d in snapshots]


def factor_values(hist, dt):
    h = hist.loc[pd.to_datetime(hist["Date"]).dt.normalize() <= pd.Timestamp(dt).normalize()].copy()
    c = h["Close"].dropna()
    if len(c) < 253:
        return {}
    lr = np.log(c / c.shift(1)).dropna()
    return {
        "R1": c.iloc[-1] / c.iloc[-2] - 1,
        "R120": c.iloc[-1] / c.iloc[-121] - 1,
        "VOL20": lr.tail(20).std(ddof=1) * np.sqrt(252),
        "VOL252": lr.tail(252).std(ddof=1) * np.sqrt(252),
        "DIST_200D": c.iloc[-1] / c.tail(200).mean() - 1,
    }


def build_factor_frame(snapshots, data):
    rows = []
    for dt, snap in snapshots.items():
        tickers = snap["Ticker"].astype(str).tolist()
        for t in tickers:
            if t not in data:
                continue
            f = factor_values(data[t], dt)
            if f:
                rows.append({"DateSignal": dt, "Ticker": t, **f})
    df = pd.DataFrame(rows)
    if df.empty:
        raise RuntimeError("No factor rows")
    for name, comps in FILTERS.items():
        out = pd.Series(np.nan, index=df.index, dtype=float)
        for dt, g in df.groupby("DateSignal", sort=False):
            score = np.zeros(len(g), dtype=float)
            valid = np.ones(len(g), dtype=bool)
            for col, direction in comps:
                r = g[col].rank(pct=True, method="average")
                if direction == "LOWER":
                    r = 1.0 - r
                valid &= r.notna().to_numpy()
                score += r.fillna(0).to_numpy()
            score[~valid] = np.nan
            out.loc[g.index] = score / len(comps)
        df[f"S_{name}"] = out
    return df


def current_weight(ticker, positions, prices, equity):
    if equity <= 0 or ticker not in positions or ticker not in prices:
        return 0.0
    return float(positions[ticker] * prices[ticker] / equity)


def filtered_target(snapshot, scores, predictor, positions, equity, close_prices):
    """Entry-only filter: blocked names cannot receive a NEW allocation.
    Existing holdings remain at their current market weight unless frozen F80
    exit logic says they should be closed.
    """
    base, exits = build_target(snapshot, TOPN, positions)
    if scores.empty or f"S_{predictor}" not in scores.columns:
        return base, exits
    s = scores[f"S_{predictor}"].dropna()
    if s.empty:
        return base, exits
    q80 = float(s.quantile(0.80))
    blocked = set(scores.loc[scores[f"S_{predictor}"] >= q80, "Ticker"].astype(str))
    target = dict(base)
    for t in blocked:
        # Entry-only semantics: preserve an existing holding at its current
        # signal-close weight, but do not allow a new allocation.
        if t in positions and t not in exits:
            target[t] = current_weight(t, positions, close_prices, equity)
        elif t in target and target[t] > 0:
            target[t] = 0.0
    return target, exits


def open_gross(positions, opens, cash):
    eq = portfolio_value(positions, opens, cash)
    gross = sum(sh * opens[t] for t, sh in positions.items() if t in opens)
    return float(gross / max(eq, 1e-12)), float(eq)


def execute_target(positions, cash, target, exits, opens, equity_before,
                   cost_bps, prev_dt, dt, policy_id):
    rows = []
    p, c, buy, sell, cost = execute_rebalance(
        dict(positions), float(cash), dict(target), set(exits), opens,
        equity_before, GAP, cost_bps, prev_dt, dt, policy_id, rows
    )
    g, eq = open_gross(p, opens, c)
    return p, c, buy, sell, cost, g, eq, rows


def solve_alpha_to_gross(positions, cash, target, exits, opens, equity_before,
                         target_gross, cost_bps, prev_dt, dt):
    if not np.isfinite(target_gross) or target_gross <= 0:
        return 0.0

    def realized(alpha):
        *_, g, _, _ = execute_target(
            positions, cash, target, exits, opens, equity_before,
            cost_bps, prev_dt, dt, POLICY + "_CONTROL_TMP"
        ) if alpha == 1.0 else execute_target(
            positions, cash, {k: v * alpha for k, v in target.items()}, exits,
            opens, equity_before, cost_bps, prev_dt, dt, POLICY + "_CONTROL_TMP"
        )
        return g

    # Explicit endpoints. If inherited holdings alone already exceed the
    # desired exposure, alpha=0 is the closest achievable control under the
    # frozen mechanics; do not force sales merely to satisfy the diagnostic.
    g0 = realized(0.0)
    if g0 >= target_gross:
        return 0.0
    g1 = realized(1.0)
    if g1 <= target_gross:
        return 1.0

    lo, hi = 0.0, 1.0
    for _ in range(40):
        mid = (lo + hi) / 2.0
        gm = realized(mid)
        if gm < target_gross:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def oos_metrics(daily, start_equity):
    d = pd.DataFrame(daily).sort_values("Date").reset_index(drop=True)
    if d.empty:
        return {"CAGR": np.nan, "MaxDD": np.nan, "Sharpe": np.nan,
                "FinalEquity": np.nan, "AvgGrossExposure": np.nan,
                "AvgCashWeight": np.nan, "AnnualizedTurnover": np.nan,
                "TotalTransactionCost": 0.0}
    e = pd.concat([pd.Series([float(start_equity)]), d["Equity"].astype(float)], ignore_index=True)
    r = e.pct_change().dropna()
    years = max(len(d) / 252.0, 1 / 252.0)
    dd = e / e.cummax() - 1.0
    return {
        "CAGR": float((e.iloc[-1] / e.iloc[0]) ** (1 / years) - 1),
        "MaxDD": float(dd.min()),
        "Sharpe": float(r.mean() / r.std(ddof=1) * np.sqrt(252)) if r.std(ddof=1) > 0 else np.nan,
        "FinalEquity": float(e.iloc[-1]),
        "AvgGrossExposure": float(d.Gross.mean()),
        "AvgCashWeight": float(d.CashWeight.mean()),
        "AnnualizedTurnover": float((d.BuyNotional + d.SellNotional).sum() / max(d["Equity"].mean(), 1e-12) / years),
        "TotalTransactionCost": float(d.Cost.sum()),
    }


def simulate_pair(calendar, snapshots, open_maps, close_maps, fac, oos_dates,
                  cost_bps, predictor):
    """Run predictor and matched control in parallel from the beginning.
    Before OOS both are exact frozen F80. During OOS the predictor is filtered;
    the control remains unfiltered but is scaled to predictor realized gross.
    """
    sigset = set(oos_dates)
    bydate = {d: g for d, g in fac.groupby("DateSignal")}

    ppos, pcash = {}, float(INITIAL_CAPITAL)
    cpos, ccash = {}, float(INITIAL_CAPITAL)
    plast_close, clast_close = {}, {}
    p_daily, c_daily = [], []
    p_trades, c_trades = [], []
    gaps, scales = [], []
    start_equity_p = start_equity_c = None

    for i, dt in enumerate(calendar):
        opens = open_maps.get(dt, {})
        closes = close_maps.get(dt, {})
        prev_dt = calendar[i - 1] if i > 0 else None

        # Mark before today's open using yesterday's close, then execute the
        # signal from prev_dt at today's open.
        pmark = dict(plast_close); pmark.update(opens)
        cmark = dict(clast_close); cmark.update(opens)
        peq_before = portfolio_value(ppos, pmark, pcash)
        ceq_before = portfolio_value(cpos, cmark, ccash)

        if prev_dt in sigset and opens:
            snap = snapshots[prev_dt]
            sc = bydate.get(prev_dt, pd.DataFrame())

            # Predictor: exact frozen F80 target, with entry-only filter.
            if prev_dt in sigset:
                ptarget, pexits = filtered_target(
                    snap, sc, predictor, ppos, peq_before, plast_close
                )
            else:
                ptarget, pexits = build_target(snap, TOPN, ppos)

            # Execute predictor first; this is a hypothetical same-open
            # observable exposure used only as the matching target for control.
            ppos, pcash, pbuy, psell, pcost, pgross, _peq_open, prows = execute_target(
                ppos, pcash, ptarget, pexits, opens, peq_before,
                cost_bps, prev_dt, dt, f"{POLICY}_{predictor}_PREDICTOR"
            )
            p_trades.extend(prows)

            # Control: exact frozen F80 selection/exit mechanics, scaled so its
            # realized post-open gross exposure matches predictor gross.
            ctarget, cexits = build_target(snap, TOPN, cpos)
            alpha = solve_alpha_to_gross(
                cpos, ccash, ctarget, cexits, opens, ceq_before,
                pgross, cost_bps, prev_dt, dt
            )
            cscaled = {k: v * alpha for k, v in ctarget.items()}
            cpos, ccash, cbuy, csell, ccost, cgross, _ceq_open, crows = execute_target(
                cpos, ccash, cscaled, cexits, opens, ceq_before,
                cost_bps, prev_dt, dt, f"{POLICY}_{predictor}_MATCHED_CONTROL"
            )
            c_trades.extend(crows)
            gaps.append(cgross - pgross)
            scales.append(alpha)

        # End-of-day marks.
        pm = dict(plast_close); pm.update(closes)
        cm = dict(clast_close); cm.update(closes)
        peq = portfolio_value(ppos, pm, pcash)
        ceq = portfolio_value(cpos, cm, ccash)
        pg = sum(sh * pm[t] for t, sh in ppos.items() if t in pm) / max(peq, 1e-12)
        cg = sum(sh * cm[t] for t, sh in cpos.items() if t in cm) / max(ceq, 1e-12)

        if dt == oos_dates[0] if oos_dates else False:
            # This branch is intentionally not used as OOS start equity because
            # the first OOS signal executes at the next open. Start equity is
            # captured at selection-end below.
            pass

        if oos_dates and dt == oos_dates[0]:
            # no-op; the actual baseline start is the previous signal date
            pass

        if oos_dates and dt >= oos_dates[0]:
            p_daily.append({"Date": dt, "Equity": peq, "Gross": pg,
                            "CashWeight": pcash / max(peq, 1e-12),
                            "BuyNotional": pbuy if 'pbuy' in locals() and prev_dt in sigset else 0.0,
                            "SellNotional": psell if 'psell' in locals() and prev_dt in sigset else 0.0,
                            "Cost": pcost if 'pcost' in locals() and prev_dt in sigset else 0.0})
            c_daily.append({"Date": dt, "Equity": ceq, "Gross": cg,
                            "CashWeight": ccash / max(ceq, 1e-12),
                            "BuyNotional": cbuy if 'cbuy' in locals() and prev_dt in sigset else 0.0,
                            "SellNotional": csell if 'csell' in locals() and prev_dt in sigset else 0.0,
                            "Cost": ccost if 'ccost' in locals() and prev_dt in sigset else 0.0})

        if dt == oos_dates[0] if oos_dates else False:
            pass

        plast_close.update(closes)
        clast_close.update(closes)

        # Capture selection-end close separately.
        if oos_dates:
            prev_oos = calendar[calendar.index(oos_dates[0]) - 1]
            if dt == prev_oos:
                start_equity_p = peq
                start_equity_c = ceq

    pm = pd.DataFrame(p_daily)
    cm = pd.DataFrame(c_daily)
    pmet = oos_metrics(pm, start_equity_p if start_equity_p is not None else INITIAL_CAPITAL)
    cmet = oos_metrics(cm, start_equity_c if start_equity_c is not None else INITIAL_CAPITAL)
    return pmet, cmet, pm, cm, gaps, scales


def main():
    t0 = time.time()
    print("FASE 19B.2 — DIRECT EXPOSURE-MATCHED CONTROL v3")
    print(f"RUN_ID: {RUN_ID}")
    print(f"Frozen policy: {POLICY} | diagnostic only | no production change")

    data, failures = download_universe(DEFAULT_UNIVERSE)
    calendar = sorted(set(x for df in data.values() for x in df["Date"].dropna().tolist()))
    open_maps, close_maps = build_price_maps(data)
    snapshots = build_snapshots(data, calendar)
    print(f"Valid={len(data)} failures={len(failures)} snapshots={len(snapshots)}")

    signals = signal_dates_for(calendar, snapshots)
    split = int(math.floor(len(signals) * TRAIN_FRACTION)) - 1
    train_end = signals[split]
    oos_dates = [d for d in signals if d > train_end]
    print(f"SELECTION END={train_end.date()} FINAL OOS START={oos_dates[0].date() if oos_dates else None} OOS signals={len(oos_dates)}")

    fac = build_factor_frame(snapshots, data)
    rows = []
    for pred in ("MAE10", "QUICK"):
        pm, cm, pdaily, cdaily, gaps, scales = simulate_pair(
            calendar, snapshots, open_maps, close_maps, fac, oos_dates, 20, pred
        )
        mean_gap = float(np.mean(gaps)) if gaps else np.nan
        mean_abs_gap = float(np.mean(np.abs(gaps))) if gaps else np.nan
        max_abs_gap = float(np.max(np.abs(gaps))) if gaps else np.nan
        match = bool(np.isfinite(max_abs_gap) and max_abs_gap <= TOL)
        if match:
            conclusion = "PREDICTOR_INCREMENTAL_VALUE_SUPPORTED" if pm["Sharpe"] > cm["Sharpe"] and pm["CAGR"] > cm["CAGR"] else "NO_INCREMENTAL_SELECTION_VALUE_DEMONSTRATED"
        else:
            conclusion = "INCONCLUSIVE_EXPOSURE_MISMATCH"

        rows.append({
            "Control": pred, "CostBpsPerSide": 20,
            "Predictor_CAGR": pm["CAGR"], "Predictor_MaxDD": pm["MaxDD"], "Predictor_Sharpe": pm["Sharpe"],
            "Predictor_FinalEquity": pm["FinalEquity"], "Predictor_AvgGross": pm["AvgGrossExposure"],
            "Control_CAGR": cm["CAGR"], "Control_MaxDD": cm["MaxDD"], "Control_Sharpe": cm["Sharpe"],
            "Control_FinalEquity": cm["FinalEquity"], "Control_AvgGross": cm["AvgGrossExposure"],
            "MeanExposureGap": mean_gap, "MeanAbsExposureGap": mean_abs_gap,
            "MaxAbsExposureGap": max_abs_gap, "ExposureMatchPASS": match,
            "MeanScaleFactor": float(np.mean(scales)) if scales else np.nan,
            "DeltaSharpe": pm["Sharpe"] - cm["Sharpe"],
            "DeltaCAGR": pm["CAGR"] - cm["CAGR"],
            "DeltaMaxDD": pm["MaxDD"] - cm["MaxDD"],
            "AttributionConclusion": conclusion,
        })
        pd.DataFrame(pdaily).to_csv(OUTDIR / f"phase19b2_{pred.lower()}_predictor_oos.csv", index=False)
        pd.DataFrame(cdaily).to_csv(OUTDIR / f"phase19b2_{pred.lower()}_matched_control_oos.csv", index=False)

    out = pd.DataFrame(rows)
    out.to_csv(OUTDIR / "phase19b2_results.csv", index=False)
    print("\n--- C20 DIRECT EXPOSURE-MATCHED ATTRIBUTION ---")
    print(out.to_string(index=False))
    print("\nGate: exposure match requires MAX absolute OOS post-open gross gap <= 1 percentage point.")
    print(f"STATUS: {'PASS_TECHNICAL' if len(out)==2 else 'FAIL'} | runtime={time.time()-t0:.1f}s")

if __name__ == "__main__":
    raise SystemExit(main())

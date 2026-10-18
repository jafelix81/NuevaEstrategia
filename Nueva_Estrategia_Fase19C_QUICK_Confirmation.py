"""FASE 19C — QUICK CONFIRMATION / ROBUSTNESS
Diagnostic only. Frozen official policy remains F80_TOP20_PARTIAL50.

Purpose: confirm whether QUICK has incremental stock-selection value beyond
exposure reduction. No production change, no OOS calibration, no re-selection.
"""
from __future__ import annotations
import math, time
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
import pandas as pd

import Nueva_Estrategia_Fase12_FinalOOS_Selection_LTM as P12

POLICY = "F80_TOP20_PARTIAL50"
FREQ, TOPN, REBALANCE = 80, 20, "PARTIAL50"
GAP = {"FULL":1.0,"PARTIAL50":0.5,"PARTIAL25":0.25}[REBALANCE]
TRAIN_FRACTION = 0.80
TOL = 0.01
BOOTSTRAP_N = 5000
RNG_SEED = 1903
THRESHOLDS = (0.70, 0.80, 0.90)
COSTS = (10, 20, 50)
FILTER_COMPONENTS = [("R120", "HIGHER"), ("DIST_200D", "HIGHER")]
OUTDIR = Path("nueva_estrategia_phase19c_quick_confirmation")
OUTDIR.mkdir(exist_ok=True)
RUN_ID = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def signal_dates_for(calendar, snapshots):
    base = calendar[P12.DISCOVERY_DATES + P12.EMBARGO:]
    return [d for d in base[::FREQ] if d in snapshots]


def factor_values(hist, dt):
    h = hist.loc[pd.to_datetime(hist["Date"]).dt.normalize() <= pd.Timestamp(dt).normalize()].copy()
    c = h["Close"].dropna()
    if len(c) < 253:
        return {}
    lr = np.log(c / c.shift(1)).dropna()
    return {
        "R120": c.iloc[-1] / c.iloc[-121] - 1,
        "DIST_200D": c.iloc[-1] / c.tail(200).mean() - 1,
    }


def build_factor_frame(snapshots, data):
    rows = []
    for dt, snap in snapshots.items():
        for t in snap["Ticker"].astype(str).tolist():
            if t not in data:
                continue
            f = factor_values(data[t], dt)
            if f:
                rows.append({"DateSignal": dt, "Ticker": t, **f})
    df = pd.DataFrame(rows)
    if df.empty:
        raise RuntimeError("No factor rows")
    for dt, g in df.groupby("DateSignal", sort=False):
        score = np.zeros(len(g), float)
        valid = np.ones(len(g), bool)
        for col, direction in FILTER_COMPONENTS:
            r = g[col].rank(pct=True, method="average")
            if direction == "LOWER":
                r = 1 - r
            valid &= r.notna().to_numpy()
            score += r.fillna(0).to_numpy()
        score[~valid] = np.nan
        df.loc[g.index, "S_QUICK"] = score / len(FILTER_COMPONENTS)
    return df


def apply_quick_filter(base_target, score_frame, threshold):
    if score_frame is None or score_frame.empty:
        return base_target.copy()
    col = "S_QUICK"
    q = score_frame[col].quantile(threshold)
    blocked = set(score_frame.loc[score_frame[col] >= q, "Ticker"].astype(str))
    target = base_target.copy()
    for t in list(target.keys()):
        if t in blocked and target[t] > 0:
            target[t] = 0.0
    return target


def gross_from_state(positions, prices, cash):
    eq = P12.portfolio_value(positions, prices, cash)
    gross = sum(sh * prices[t] for t, sh in positions.items() if t in prices)
    return gross / max(eq, 1e-12), eq


def execute_trial(positions, cash, target, exits, opens, eq_before, cost_bps, prev_dt, dt):
    p = dict(positions)
    c = float(cash)
    rows = []
    p, c, buy, sell, cost = P12.execute_rebalance(
        p, c, target, exits, opens, eq_before, GAP, cost_bps,
        prev_dt, dt, POLICY, rows
    )
    g, eq = gross_from_state(p, opens, c)
    return p, c, buy, sell, cost, g, eq, rows


def solve_control_alpha(positions, cash, base_target, exits, opens, eq_before,
                        predictor_gross, cost_bps, prev_dt, dt):
    """Choose alpha so CONTROL post-open gross ~= predictor post-open gross."""
    if predictor_gross <= 0:
        return 0.0
    _, _, _, _, _, g0, _, _ = execute_trial(
        positions, cash, base_target * 0.0, exits, opens, eq_before,
        cost_bps, prev_dt, dt
    )
    if g0 > predictor_gross + 1e-12:
        return 0.0
    _, _, _, _, _, g1, _, _ = execute_trial(
        positions, cash, base_target, exits, opens, eq_before,
        cost_bps, prev_dt, dt
    )
    if g1 <= predictor_gross:
        return 1.0
    lo, hi = 0.0, 1.0
    for _ in range(40):
        mid = (lo + hi) / 2
        _, _, _, _, _, gm, _, _ = execute_trial(
            positions, cash, base_target * mid, exits, opens, eq_before,
            cost_bps, prev_dt, dt
        )
        if gm < predictor_gross:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def run_pair(calendar, snapshots, open_maps, close_maps, fac, oos_dates,
             cost_bps, threshold):
    """Run BASE until OOS, then PREDICTOR and direct-matched CONTROL in parallel."""
    pred = {"positions": {}, "cash": float(P12.INITIAL_CAPITAL), "last": {}}
    ctrl = {"positions": {}, "cash": float(P12.INITIAL_CAPITAL), "last": {}}
    bydate = {d: g for d, g in fac.groupby("DateSignal")}
    sigset = set(oos_dates)
    oos_start = min(oos_dates)
    daily = []
    gaps = []
    scales = []
    trades = {"predictor": [], "control": []}
    for i, dt in enumerate(calendar):
        opens = open_maps.get(dt, {})
        closes = close_maps.get(dt, {})
        prev_dt = calendar[i - 1] if i else None
        is_oos_signal = prev_dt in sigset

        for side in (pred, ctrl):
            mark = dict(side["last"])
            mark.update(opens)
            side["eq_before"] = P12.portfolio_value(side["positions"], mark, side["cash"])

        # Before final OOS both portfolios follow exact frozen F80.
        if is_oos_signal:
            snap = snapshots[prev_dt]
            base_pred, exits_pred = P12.build_target(snap, TOPN, pred["positions"])
            base_ctrl, exits_ctrl = P12.build_target(snap, TOPN, ctrl["positions"])
            sc = bydate.get(prev_dt, pd.DataFrame())
            predictor_target = apply_quick_filter(base_pred, sc, threshold)
            predictor_exits = exits_pred

            if opens:
                # Predictor executes the filtered target exactly.
                pp = predictor_target
                pred_pos, pred_cash, pb, ps, pc, pg, _ = execute_trial(
                    pred["positions"], pred["cash"], pp, predictor_exits,
                    opens, pred["eq_before"], cost_bps, prev_dt, dt
                )
                pred["positions"], pred["cash"] = pred_pos, pred_cash

                # Control retains F80 stock selection, but its scalar target is
                # solved to match the predictor's actual post-open gross.
                alpha = solve_control_alpha(
                    ctrl["positions"], ctrl["cash"], base_ctrl, exits_ctrl,
                    opens, ctrl["eq_before"], pg, cost_bps, prev_dt, dt
                )
                cp = base_ctrl * alpha
                ctrl_pos, ctrl_cash, cb, cs, cc, cg, _ = execute_trial(
                    ctrl["positions"], ctrl["cash"], cp, exits_ctrl,
                    opens, ctrl["eq_before"], cost_bps, prev_dt, dt
                )
                ctrl["positions"], ctrl["cash"] = ctrl_pos, ctrl_cash
                gaps.append(cg - pg)
                scales.append(alpha)
                trades["predictor"].append((dt, pb, ps, pc))
                trades["control"].append((dt, cb, cs, cc))
        else:
            # Exact baseline execution before OOS establishes the same historical
            # state that the official Phase-12 policy would have carried forward.
            snap = snapshots.get(prev_dt) if prev_dt is not None else None
            if snap is not None and opens:
                for side, label in ((pred, "predictor"), (ctrl, "control")):
                    target, exits = P12.build_target(snap, TOPN, side["positions"])
                    side["positions"], side["cash"], b, s, c, _, _ = execute_trial(
                        side["positions"], side["cash"], target, exits, opens,
                        side["eq_before"], cost_bps, prev_dt, dt
                    )

        # Mark close. Record only final OOS period.
        for side in (pred, ctrl):
            cm = dict(side["last"])
            cm.update(closes)
            side["close_eq"] = P12.portfolio_value(side["positions"], cm, side["cash"])
            side["close_gross"] = sum(sh * cm[t] for t, sh in side["positions"].items() if t in cm) / max(side["close_eq"], 1e-12)

        if dt >= oos_start:
            daily.append({
                "Date": dt,
                "PredictorEquity": pred["close_eq"],
                "ControlEquity": ctrl["close_eq"],
                "PredictorGross": pred["close_gross"],
                "ControlGross": ctrl["close_gross"],
            })
        pred["last"].update(closes)
        ctrl["last"].update(closes)

    d = pd.DataFrame(daily).sort_values("Date").reset_index(drop=True)
    if d.empty:
        raise RuntimeError("No OOS daily observations")
    d["PredictorReturn"] = d["PredictorEquity"].pct_change()
    d["ControlReturn"] = d["ControlEquity"].pct_change()
    d["ReturnDiff"] = d["PredictorReturn"] - d["ControlReturn"]
    return d, np.asarray(gaps, float), np.asarray(scales, float), trades


def metrics(equity):
    e = equity.dropna().astype(float)
    r = e.pct_change().dropna()
    if len(e) < 2:
        return {"CAGR": np.nan, "MaxDD": np.nan, "Sharpe": np.nan, "FinalEquity": np.nan}
    years = max(len(e) / 252, 1 / 252)
    dd = e / e.cummax() - 1
    return {
        "CAGR": float((e.iloc[-1] / e.iloc[0]) ** (1 / years) - 1),
        "MaxDD": float(dd.min()),
        "Sharpe": float(r.mean() / r.std(ddof=1) * np.sqrt(252)) if r.std(ddof=1) > 0 else np.nan,
        "FinalEquity": float(e.iloc[-1]),
    }


def paired_bootstrap(diff, n=BOOTSTRAP_N, seed=RNG_SEED):
    x = np.asarray(diff, float)
    x = x[np.isfinite(x)]
    if len(x) == 0:
        return np.nan, np.nan, np.nan, 0
    rng = np.random.default_rng(seed)
    means = rng.choice(x, size=(n, len(x)), replace=True).mean(axis=1)
    return float(x.mean()), float(np.quantile(means, .025)), float(np.quantile(means, .975)), len(x)


def loo_results(d):
    rows = []
    for idx in range(1, len(d)):
        sub = d.drop(index=idx).reset_index(drop=True)
        p = metrics(sub["PredictorEquity"])
        c = metrics(sub["ControlEquity"])
        rows.append({
            "ExcludedDate": d.loc[idx, "Date"],
            "DeltaSharpe": p["Sharpe"] - c["Sharpe"],
            "DeltaCAGR": p["CAGR"] - c["CAGR"],
            "DeltaMaxDD": p["MaxDD"] - c["MaxDD"],
            "DeltaFinal": p["FinalEquity"] - c["FinalEquity"],
        })
    return pd.DataFrame(rows)


def main():
    t0 = time.time()
    print("FASE 19C — QUICK CONFIRMATION / ROBUSTNESS")
    print(f"RUN_ID: {RUN_ID}")
    print(f"Frozen policy: {POLICY} | diagnostic only | no production change")
    print(f"Predeclared costs={COSTS} | thresholds={THRESHOLDS} | bootstrap={BOOTSTRAP_N}")

    data, failures = P12.download_universe(P12.DEFAULT_UNIVERSE)
    calendar = sorted(set(x for df in data.values() for x in df["Date"].dropna().tolist()))
    open_maps, close_maps = P12.build_price_maps(data)
    snapshots = P12.build_snapshots(data, calendar)
    signals = signal_dates_for(calendar, snapshots)
    split = int(math.floor(len(signals) * TRAIN_FRACTION)) - 1
    train_end = signals[split]
    oos_start = calendar[calendar.index(train_end) + 1]
    oos_dates = [d for d in signals if d >= oos_start]
    print(f"Valid={len(data)} failures={len(failures)} snapshots={len(snapshots)}")
    print(f"SELECTION END={train_end.date()} FINAL OOS START={oos_start.date()} OOS signals={len(oos_dates)}")

    fac = build_factor_frame(snapshots, data)
    all_rows = []
    daily_store = {}

    for threshold in THRESHOLDS:
        for cost in COSTS:
            d, gaps, scales, trades = run_pair(
                calendar, snapshots, open_maps, close_maps, fac, oos_dates, cost, threshold
            )
            pm = metrics(d["PredictorEquity"])
            cm = metrics(d["ControlEquity"])
            max_gap = float(np.max(np.abs(gaps))) if len(gaps) else np.nan
            mean_gap = float(np.mean(gaps)) if len(gaps) else np.nan
            mean_abs = float(np.mean(np.abs(gaps))) if len(gaps) else np.nan
            match = bool(np.isfinite(max_gap) and max_gap <= TOL)
            conclusion = "INCONCLUSIVE_EXPOSURE_MISMATCH"
            if match and threshold == .80 and cost == 20:
                conclusion = "CANDIDATE_CONFIRMATION"
            all_rows.append({
                "Threshold": threshold,
                "CostBpsPerSide": cost,
                "Predictor_CAGR": pm["CAGR"],
                "Predictor_MaxDD": pm["MaxDD"],
                "Predictor_Sharpe": pm["Sharpe"],
                "Predictor_FinalEquity": pm["FinalEquity"],
                "Control_CAGR": cm["CAGR"],
                "Control_MaxDD": cm["MaxDD"],
                "Control_Sharpe": cm["Sharpe"],
                "Control_FinalEquity": cm["FinalEquity"],
                "DeltaSharpe": pm["Sharpe"] - cm["Sharpe"],
                "DeltaCAGR": pm["CAGR"] - cm["CAGR"],
                "DeltaMaxDD": pm["MaxDD"] - cm["MaxDD"],
                "DeltaFinalEquity": pm["FinalEquity"] - cm["FinalEquity"],
                "MeanExposureGap": mean_gap,
                "MeanAbsExposureGap": mean_abs,
                "MaxAbsExposureGap": max_gap,
                "ExposureMatchPASS": match,
                "MeanScaleFactor": float(np.mean(scales)) if len(scales) else np.nan,
                "AttributionConclusion": conclusion,
            })
            daily_store[(threshold, cost)] = d
            d.to_csv(OUTDIR / f"phase19c_quick_daily_q{int(threshold*100)}_c{cost}.csv", index=False)

    results = pd.DataFrame(all_rows)
    results.to_csv(OUTDIR / "phase19c_quick_confirmation_results.csv", index=False)

    # C20 paired bootstrap and leave-one-OOS-signal-out are intentionally run
    # only on the frozen primary threshold Q80; no threshold is selected from
    # these diagnostics.
    d20 = daily_store[(.80, 20)]
    boot_mean, boot_lo, boot_hi, n = paired_bootstrap(d20["ReturnDiff"].dropna().to_numpy())
    loo = loo_results(d20)
    loo.to_csv(OUTDIR / "phase19c_quick_c20_leave_one_signal_out.csv", index=False)
    pd.DataFrame([{
        "Threshold": .80, "CostBpsPerSide": 20,
        "MeanDailyReturnDifference": boot_mean,
        "Bootstrap95Low": boot_lo,
        "Bootstrap95High": boot_hi,
        "NReturnDiff": n,
        "BootstrapSeed": RNG_SEED,
        "BootstrapN": BOOTSTRAP_N,
    }]).to_csv(OUTDIR / "phase19c_quick_c20_bootstrap.csv", index=False)

    print("\n--- C20 PRIMARY Q80 ---")
    print(results[(results.Threshold == .80) & (results.CostBpsPerSide == 20)].to_string(index=False))
    print("\n--- COST SENSITIVITY Q80 ---")
    print(results[results.Threshold == .80].to_string(index=False))
    print("\n--- THRESHOLD SENSITIVITY C20 ---")
    print(results[results.CostBpsPerSide == 20].to_string(index=False))
    print("\n--- C20 PAIRED BOOTSTRAP ---")
    print(f"Mean daily return diff={boot_mean:.8f} | 95% CI=[{boot_lo:.8f}, {boot_hi:.8f}] | N={n}")
    print("\n--- C20 LEAVE-ONE-SIGNAL-OUT ---")
    print(loo.to_string(index=False))

    primary = results[(results.Threshold == .80) & (results.CostBpsPerSide == 20)].iloc[0]
    loo_positive = bool((loo["DeltaFinal"] > 0).all()) if not loo.empty else False
    cost_positive = bool((results[results.Threshold == .80]["DeltaFinalEquity"] > 0).all())
    threshold_consistent = bool((results[results.CostBpsPerSide == 20]["DeltaFinalEquity"] > 0).all())
    robust = bool(primary.ExposureMatchPASS and cost_positive and threshold_consistent and loo_positive)
    status = "PASS_CONFIRMATION" if robust else "PASS_RESEARCH_NOT_CONFIRMED"
    print(f"\nGATES: Exposure={primary.ExposureMatchPASS} | CostPositive={cost_positive} | ThresholdPositive={threshold_consistent} | LOOPositive={loo_positive}")
    print(f"STATUS: {status} | runtime={time.time()-t0:.1f}s")


if __name__ == "__main__":
    raise SystemExit(main())

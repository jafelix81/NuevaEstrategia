"""FASE 19E — QUICK INCREMENTAL INFORMATION / RECONCILIATION

Diagnostic only. Frozen official policy remains F80_TOP20_PARTIAL50.

Purpose:
1) Reconcile 19B.2 vs 19C by decomposing what QUICK actually removes from F80.
2) Measure whether QUICK is redundant with the frozen LTM ranking.
3) Test whether blocked F80 names subsequently underperform unblocked F80 names.
4) Test whether QUICK retains information after removing its cross-sectional linear
   component explained by LTM (diagnostic residual score).
5) Do not select a threshold and do not alter production F80.

Important: only six final-OOS rebalance signals exist. This phase is therefore
an attribution/diagnostic, not a confirmation test.
"""
from __future__ import annotations

import math, time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

import Nueva_Estrategia_Fase12_FinalOOS_Selection_LTM as P12

POLICY = "F80_TOP20_PARTIAL50"
FREQ, TOPN = 80, 20
TRAIN_FRACTION = 0.80
THRESHOLD = 0.80
FORWARD_HORIZONS = (5, 10, 20)
OUTDIR = Path("nueva_estrategia_phase19e_quick_reconciliation")
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
    return {
        "R120": float(c.iloc[-1] / c.iloc[-121] - 1.0),
        "DIST_200D": float(c.iloc[-1] / c.tail(200).mean() - 1.0),
    }


def quick_score(df):
    x = df.copy()
    r1 = x["R120"].rank(pct=True, method="average")
    r2 = x["DIST_200D"].rank(pct=True, method="average")
    x["Pct_R120"] = r1
    x["Pct_DIST_200D"] = r2
    x["S_QUICK"] = (r1 + r2) / 2.0
    return x


def forward_return(close_series, signal_dt, horizon):
    s = close_series.loc[pd.to_datetime(close_series.index).normalize() >= pd.Timestamp(signal_dt).normalize()]
    if s.empty:
        return np.nan
    # signal close is t; use t+h trading observation.
    pos = list(s.index).index(s.index[0])
    if pos + horizon >= len(s):
        return np.nan
    p0 = float(s.iloc[0])
    p1 = float(s.iloc[horizon])
    if p0 <= 0:
        return np.nan
    return p1 / p0 - 1.0


def build_future_map(data, dt, horizon):
    out = {}
    for t, df in data.items():
        x = df.copy()
        x["Date"] = pd.to_datetime(x["Date"]).dt.normalize()
        x = x.sort_values("Date")
        c = x.set_index("Date")["Close"].dropna()
        out[t] = forward_return(c, dt, horizon)
    return out


def safe_mean(x):
    a = pd.Series(x).dropna().to_numpy(float)
    return float(a.mean()) if len(a) else np.nan


def safe_median(x):
    a = pd.Series(x).dropna().to_numpy(float)
    return float(np.median(a)) if len(a) else np.nan


def main():
    t0 = time.time()
    print("FASE 19E — QUICK INCREMENTAL INFORMATION / RECONCILIATION")
    print("=" * 78)
    print(f"RUN_ID: {RUN_ID}")
    print(f"Frozen policy: {POLICY} | diagnostic only")
    print(f"QUICK threshold: Q{int(THRESHOLD*100)} | forward horizons={FORWARD_HORIZONS}")

    data, failures = P12.download_universe(P12.DEFAULT_UNIVERSE)
    calendar = sorted(set(d for df in data.values() for d in df["Date"].dropna().tolist()))
    open_maps, close_maps = P12.build_price_maps(data)
    snapshots = P12.build_snapshots(data, calendar)
    signals = signal_dates_for(calendar, snapshots)
    split_pos = int(math.floor(len(signals) * TRAIN_FRACTION)) - 1
    train_end = signals[split_pos]
    oos_dates = [d for d in signals if d > train_end]

    print(f"Valid={len(data)} failures={len(failures)} snapshots={len(snapshots)}")
    print(f"Selection end={train_end.date()} | OOS signals={len(oos_dates)}")

    all_rows = []
    date_summary = []
    ltm_rows = []
    blocked_rows = []
    candidate_rows = []

    for dt in oos_dates:
        snap = snapshots[dt].copy()
        base_target, _ = P12.build_target(snap, TOPN, {})
        f80 = set(base_target.keys())

        rows = []
        for t in snap["Ticker"].astype(str):
            if t not in data:
                continue
            f = factor_values(data[t], dt)
            if not f:
                continue
            ltm = float(snap.loc[snap["Ticker"].astype(str) == t, "LTM"].iloc[0])
            rows.append({"DateSignal": dt, "Ticker": t, "LTM": ltm, **f})
        sc = quick_score(pd.DataFrame(rows))
        qcut = float(sc["S_QUICK"].quantile(THRESHOLD))
        sc["BlockedQ80"] = sc["S_QUICK"] >= qcut
        sc["F80Target"] = sc["Ticker"].isin(f80)
        sc["F80Blocked"] = sc["F80Target"] & sc["BlockedQ80"]
        sc["F80Retained"] = sc["F80Target"] & (~sc["BlockedQ80"])

        # Residualize QUICK against LTM cross-sectionally. This is not a model
        # fit across time; it asks whether QUICK contains information not
        # linearly explained by the already-frozen LTM score on the same date.
        x = sc["LTM"].to_numpy(float)
        y = sc["S_QUICK"].to_numpy(float)
        mask = np.isfinite(x) & np.isfinite(y)
        if mask.sum() >= 5 and np.std(x[mask]) > 0:
            beta = np.cov(x[mask], y[mask], ddof=0)[0,1] / np.var(x[mask])
            alpha = float(y[mask].mean() - beta * x[mask].mean())
            sc["QUICK_LTM_Fitted"] = alpha + beta * sc["LTM"]
            sc["QUICK_Residual"] = sc["S_QUICK"] - sc["QUICK_LTM_Fitted"]
        else:
            beta = np.nan; alpha = np.nan
            sc["QUICK_LTM_Fitted"] = np.nan
            sc["QUICK_Residual"] = np.nan

        rho, rho_p = spearmanr(sc["LTM"], sc["S_QUICK"], nan_policy="omit")
        ltm_rows.append({"DateSignal": dt, "N": len(sc), "Spearman_LTM_QUICK": rho, "SpearmanP": rho_p, "ResidualBeta": beta})

        future_maps = {h: build_future_map(data, dt, h) for h in FORWARD_HORIZONS}
        for h in FORWARD_HORIZONS:
            sc[f"FwdRet_{h}D"] = sc["Ticker"].map(future_maps[h])

        # Store every OOS cross-section for auditability.
        all_rows.append(sc.copy())

        blocked = sc[sc["F80Blocked"]].copy()
        retained = sc[sc["F80Retained"]].copy()
        f80_other = sc[sc["F80Target"] & (~sc["F80Blocked"])].copy()
        nonf80 = sc[~sc["F80Target"]].copy()

        # Candidate alternatives: highest-LTM non-F80 names that are not blocked.
        alternatives = nonf80[~nonf80["BlockedQ80"]].sort_values("LTM", ascending=False).head(len(blocked)).copy()
        alternatives["AlternativeForF80Blocked"] = True
        if len(alternatives):
            candidate_rows.append(alternatives)

        row = {
            "DateSignal": dt,
            "F80N": int(sc["F80Target"].sum()),
            "BlockedF80N": int(sc["F80Blocked"].sum()),
            "RetainedF80N": int(sc["F80Retained"].sum()),
            "BlockedShareF80": float(sc["F80Blocked"].mean() / max(sc["F80Target"].mean(), 1e-12)),
            "LTMMean_Blocked": safe_mean(blocked["LTM"]),
            "LTMMean_Retained": safe_mean(retained["LTM"]),
            "QuickMean_Blocked": safe_mean(blocked["S_QUICK"]),
            "QuickMean_Retained": safe_mean(retained["S_QUICK"]),
            "ResidualMean_Blocked": safe_mean(blocked["QUICK_Residual"]),
            "ResidualMean_Retained": safe_mean(retained["QUICK_Residual"]),
        }
        for h in FORWARD_HORIZONS:
            row[f"Fwd{h}_BlockedMean"] = safe_mean(blocked[f"FwdRet_{h}D"])
            row[f"Fwd{h}_RetainedMean"] = safe_mean(retained[f"FwdRet_{h}D"])
            row[f"Fwd{h}_DeltaBlockedMinusRetained"] = row[f"Fwd{h}_BlockedMean"] - row[f"Fwd{h}_RetainedMean"] if np.isfinite(row[f"Fwd{h}_BlockedMean"]) and np.isfinite(row[f"Fwd{h}_RetainedMean"]) else np.nan
            row[f"Fwd{h}_AltMean"] = safe_mean(alternatives[f"FwdRet_{h}D"]) if len(alternatives) else np.nan
            row[f"Fwd{h}_DeltaBlockedMinusAlt"] = row[f"Fwd{h}_BlockedMean"] - row[f"Fwd{h}_AltMean"] if np.isfinite(row[f"Fwd{h}_BlockedMean"]) and np.isfinite(row[f"Fwd{h}_AltMean"]) else np.nan
        date_summary.append(row)

        blocked2 = blocked.copy()
        blocked2["Group"] = "F80_BLOCKED_Q80"
        retained2 = retained.copy()
        retained2["Group"] = "F80_RETAINED_Q80"
        for xdf in (blocked2, retained2):
            blocked_rows.append(xdf)

        print(f"OOS {dt.date()} | F80={len(f80)} blocked={len(blocked)} retained={len(retained)} | rho(LTM,QUICK)={rho:.3f}")

    cross = pd.concat(all_rows, ignore_index=True)
    summary = pd.DataFrame(date_summary)
    ltm_df = pd.DataFrame(ltm_rows)
    groups = pd.concat(blocked_rows, ignore_index=True) if blocked_rows else pd.DataFrame()
    alternatives_df = pd.concat(candidate_rows, ignore_index=True) if candidate_rows else pd.DataFrame()

    cross.to_csv(OUTDIR / "phase19e_quick_oos_cross_sections.csv", index=False)
    summary.to_csv(OUTDIR / "phase19e_quick_date_summary.csv", index=False)
    ltm_df.to_csv(OUTDIR / "phase19e_quick_ltm_redundancy.csv", index=False)
    groups.to_csv(OUTDIR / "phase19e_quick_blocked_vs_retained.csv", index=False)
    alternatives_df.to_csv(OUTDIR / "phase19e_quick_candidate_alternatives.csv", index=False)

    # Aggregate diagnostics. These are descriptive only.
    print("\n--- 19E RECONCILIATION ---")
    print(summary.to_string(index=False))
    print("\n--- LTM REDUNDANCY ---")
    print(ltm_df.to_string(index=False))
    for h in FORWARD_HORIZONS:
        b = summary[f"Fwd{h}_BlockedMean"]
        r = summary[f"Fwd{h}_RetainedMean"]
        a = summary[f"Fwd{h}_AltMean"]
        print(f"H{h}: blocked mean={safe_mean(b):.6f} | retained mean={safe_mean(r):.6f} | alt mean={safe_mean(a):.6f} | blocked-retained={safe_mean(b-r):.6f} | blocked-alt={safe_mean(b-a):.6f}")

    # Information test using cross-sectional residual score. We report the
    # direction and per-date Spearman association with future returns; no claim
    # of statistical confirmation is made because N=6 dates.
    residual_rows = []
    for dt, g in cross.groupby("DateSignal"):
        for h in FORWARD_HORIZONS:
            x = g["QUICK_Residual"]
            y = g[f"FwdRet_{h}D"]
            m = x.notna() & y.notna()
            if m.sum() >= 20:
                rho, p = spearmanr(x[m], y[m])
                residual_rows.append({"DateSignal": dt, "Horizon": h, "N": int(m.sum()), "SpearmanResidualQuick_FwdRet": rho, "P": p})
    residual = pd.DataFrame(residual_rows)
    residual.to_csv(OUTDIR / "phase19e_quick_residual_predictability.csv", index=False)
    print("\n--- RESIDUAL QUICK PREDICTABILITY ---")
    print(residual.to_string(index=False))

    # Conservative status: QUICK cannot be promoted here. We distinguish
    # redundancy from evidence of incremental value, but only descriptively.
    median_abs_rho = float(ltm_df["Spearman_LTM_QUICK"].abs().median()) if len(ltm_df) else np.nan
    blocked_advantage = {h: safe_mean(summary[f"Fwd{h}_DeltaBlockedMinusRetained"]) for h in FORWARD_HORIZONS}
    residual_by_h = {}
    if not residual.empty:
        for h in FORWARD_HORIZONS:
            vals = residual.loc[residual["Horizon"] == h, "SpearmanResidualQuick_FwdRet"]
            residual_by_h[h] = safe_mean(vals)

    print("\n--- GATE ---")
    print(f"Median |Spearman(LTM, QUICK)| = {median_abs_rho:.4f}")
    print("This phase does NOT select QUICK or alter F80.")
    print("STATUS: DIAGNOSTIC_COMPLETE_REQUIRES_RESEARCH_JUDGMENT")
    print(f"Runtime={time.time()-t0:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

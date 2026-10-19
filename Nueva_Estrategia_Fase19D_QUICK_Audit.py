"""FASE 19D — QUICK IDENTITY / THRESHOLD AUDIT

Diagnostic only. Does not change F80 or select a production rule.

Purpose:
1) Prove whether QUICK actually changes the F80 target on each OOS signal.
2) Compare thresholds 0.00/0.50/0.70/0.80/0.90/1.00.
3) Print candidate universe, F80 top-N target, QUICK scores, blocked names,
   overlap, and target changes per OOS signal.
4) Detect whether Q70/Q80/Q90 being identical is legitimate (no selected
   F80 names in the blocked tail) or a code-path error.
5) Preserve exact Phase-12 selection/execution semantics; no economic re-test.
"""
from __future__ import annotations

import math
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

import Nueva_Estrategia_Fase12_FinalOOS_Selection_LTM as P12

POLICY = "F80_TOP20_PARTIAL50"
FREQ = 80
TOPN = 20
FILTER_COMPONENTS = [("R120", "HIGHER"), ("DIST_200D", "HIGHER")]
THRESHOLDS = (0.00, 0.50, 0.70, 0.80, 0.90, 1.00)
TRAIN_FRACTION = 0.80
OUTDIR = Path("nueva_estrategia_phase19d_quick_audit")
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


def score_snapshot(snap, data, dt):
    rows = []
    for t in snap["Ticker"].astype(str).tolist():
        if t not in data:
            continue
        f = factor_values(data[t], dt)
        if f:
            rows.append({"Ticker": t, **f})
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    score = np.zeros(len(df), float)
    valid = np.ones(len(df), bool)
    for col, direction in FILTER_COMPONENTS:
        r = df[col].rank(pct=True, method="average")
        if direction == "LOWER":
            r = 1.0 - r
        valid &= r.notna().to_numpy()
        df[f"Pct_{col}"] = r
        score += r.fillna(0).to_numpy()
    score[~valid] = np.nan
    df["S_QUICK"] = score / len(FILTER_COMPONENTS)
    df = df.sort_values("S_QUICK", ascending=False).reset_index(drop=True)
    df["QuickRank"] = np.arange(1, len(df) + 1)
    df["QuickPct"] = df["S_QUICK"].rank(pct=True, method="average")
    return df


def main():
    t0 = time.time()
    print("FASE 19D — QUICK IDENTITY / THRESHOLD AUDIT")
    print("=" * 78)
    print(f"RUN_ID: {RUN_ID}")
    print("Frozen policy: F80_TOP20_PARTIAL50 | diagnostic only")
    print(f"Thresholds: {THRESHOLDS}")

    data, failures = P12.download_universe(P12.DEFAULT_UNIVERSE)
    calendar = sorted(set(d for df in data.values() for d in df["Date"].dropna().tolist()))
    snapshots = P12.build_snapshots(data, calendar)
    signals = signal_dates_for(calendar, snapshots)
    split_pos = int(math.floor(len(signals) * TRAIN_FRACTION)) - 1
    train_end = signals[split_pos]
    oos_dates = [d for d in signals if d > train_end]

    print(f"Valid={len(data)} failures={len(failures)} snapshots={len(snapshots)}")
    print(f"Selection end={train_end.date()} | OOS signals={len(oos_dates)}")

    summary_rows = []
    detail_rows = []

    # This audit intentionally uses the exact OOS signal snapshots and computes
    # factors using history <= DateSignal only.
    for dt in oos_dates:
        snap = snapshots[dt]
        base_target, exits = P12.build_target(snap, TOPN, {})
        base_names = list(base_target.keys())
        scored = score_snapshot(snap, data, dt)
        if scored.empty:
            raise RuntimeError(f"No factor rows for OOS signal {dt}")

        print("\n" + "-" * 78)
        print(f"OOS SIGNAL: {dt.date()}")
        print(f"Candidates scored: {len(scored)} | F80 target names: {len(base_names)}")
        print("F80 TARGET:", ", ".join(base_names))

        # Map exact scores for the F80 target.
        smap = scored.set_index("Ticker")["S_QUICK"].to_dict()
        for t in base_names:
            print(f"  {t:8s} S_QUICK={smap.get(t, np.nan):.6f}")

        for threshold in THRESHOLDS:
            if threshold <= 0:
                blocked = set()
            elif threshold >= 1:
                blocked = set(scored.loc[scored["S_QUICK"] >= scored["S_QUICK"].quantile(1.0), "Ticker"].astype(str))
            else:
                q = float(scored["S_QUICK"].quantile(threshold))
                blocked = set(scored.loc[scored["S_QUICK"] >= q, "Ticker"].astype(str))
            overlap = [t for t in base_names if t in blocked]
            filtered = [t for t in base_names if t not in blocked]
            changed = set(filtered) != set(base_names)
            summary_rows.append({
                "DateSignal": dt,
                "Threshold": threshold,
                "CandidateN": len(scored),
                "F80TargetN": len(base_names),
                "BlockedCandidateN": len(blocked),
                "BlockedF80N": len(overlap),
                "FilteredTargetN": len(filtered),
                "FilterChangesF80": changed,
                "F80Target": "|".join(base_names),
                "BlockedF80": "|".join(overlap),
                "FilteredTarget": "|".join(filtered),
            })
            print(f"  Q{int(threshold*100):03d}: blocked candidates={len(blocked):3d} | blocked F80={len(overlap):2d} | changed={changed}")

        # Save the complete scored cross-section for this date.
        scored2 = scored.copy()
        scored2.insert(0, "DateSignal", dt)
        scored2["F80Target"] = scored2["Ticker"].isin(base_names)
        detail_rows.append(scored2)

    summary = pd.DataFrame(summary_rows)
    details = pd.concat(detail_rows, ignore_index=True)
    summary.to_csv(OUTDIR / "phase19d_quick_threshold_summary.csv", index=False)
    details.to_csv(OUTDIR / "phase19d_quick_oos_scored_cross_sections.csv", index=False)

    # Compare filtered targets across thresholds date by date.
    pivot = summary.pivot_table(index="DateSignal", columns="Threshold", values="FilteredTarget", aggfunc="first")
    identical_7090 = []
    for dt in pivot.index:
        vals = [pivot.loc[dt, q] for q in (0.70, 0.80, 0.90) if q in pivot.columns]
        identical_7090.append(len(set(vals)) == 1)
    print("\n--- THRESHOLD IDENTITY ---")
    print(f"Q70/Q80/Q90 identical on all OOS dates: {all(identical_7090)}")
    print(f"Dates where Q70/Q80/Q90 identical: {sum(identical_7090)}/{len(identical_7090)}")

    # Extreme thresholds are diagnostic: Q0 blocks nothing; Q100 blocks only
    # names tied at the maximum score. If Q0 and Q100 produce identical F80
    # targets on every date, the filter is not touching F80 at all.
    q0 = summary[summary["Threshold"] == 0.0].set_index("DateSignal")
    q100 = summary[summary["Threshold"] == 1.0].set_index("DateSignal")
    extreme_same = [q0.loc[d, "FilteredTarget"] == q100.loc[d, "FilteredTarget"] for d in q0.index]
    print(f"Q0 vs Q100 identical on all OOS dates: {all(extreme_same)}")

    # Aggregate interpretation gate.
    total_oos = len(oos_dates)
    any_change_80 = int((summary[summary.Threshold == .80]["FilterChangesF80"]).sum())
    any_change_90 = int((summary[summary.Threshold == .90]["FilterChangesF80"]).sum())
    any_change_100 = int((summary[summary.Threshold == 1.00]["FilterChangesF80"]).sum())
    print("\n--- GATE ---")
    print(f"Q80 changed F80 on {any_change_80}/{total_oos} OOS signals")
    print(f"Q90 changed F80 on {any_change_90}/{total_oos} OOS signals")
    print(f"Q100 changed F80 on {any_change_100}/{total_oos} OOS signals")
    if any_change_80 == 0 and any_change_100 == 0:
        status = "FILTER_NOT_TOUCHING_F80"
    elif any_change_80 == 0:
        status = "Q80_NO_EFFECT_BUT_EXTREME_TEST_CHANGES"
    else:
        status = "FILTER_IDENTITY_CONFIRMED_REQUIRES_19E_RECONCILIATION"
    print(f"STATUS: {status}")
    print(f"Runtime={time.time()-t0:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""
FASE 13C — RECONCILIACIÓN PHASE 12 vs BUFFER CORREGIDO — LTM

Purpose
-------
Resolve the methodological discrepancy discovered in Phase 13B without
re-selecting the strategy.

Two implementations of the frozen policy F80_TOP20_PARTIAL50 are run on the
same data, same final-OOS boundary and same execution engine:

A) ACTUAL_PHASE12
   Exact Phase 11/Phase 12 target-builder semantics. The persistence buffer is
   effectively inert when Top-N is completely filled by the current Top-N.

B) CORRECTED_BUFFER20
   Corrected +20 rank persistence semantics: incumbents inside Top-N+20 are
   protected first, then remaining slots are filled by the highest-ranked
   candidates.

Both are evaluated only through the last fully closed daily bar. No current-day
partial bar is allowed. No parameter is selected from this comparison.

Interpretation rule
-------------------
If A and B are close, Phase 12's final-OOS validation remains economically
representative despite the implementation clarification. If they differ
materially, Phase 12 must be treated as validating A only and the corrected
implementation requires its own untouched final-OOS validation/re-selection.
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

import Nueva_Estrategia_Fase13B_CorrectiveAudit_LTM_v2 as p13
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
    old_builder = p13.build_target_corrected
    p13.build_target_corrected = builder
    try:
        out = p13.run_oos_policy(
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
        p13.build_target_corrected = old_builder

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

    data, failures = p13.download_universe(p13.DEFAULT_UNIVERSE)
    valid = len(data)
    if valid < p13.MIN_CROSS_SECTION:
        raise RuntimeError(f"valid universe too small: {valid}")

    calendar = sorted(set(
        d for df in data.values() for d in df["Date"].dropna().tolist()
    ))
    closed_cutoff = p13.last_fully_closed_date(calendar)
    calendar = [d for d in calendar if pd.Timestamp(d).normalize() <= closed_cutoff]

    open_maps, close_maps = p13.build_price_maps(data)
    snapshots = p13.build_snapshots(data, calendar)

    ref, split_pos, train_end_dt, test_start_idx = p13.split_boundary(calendar, snapshots)
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
            ("CORRECTED_BUFFER20", p13.build_target_corrected),
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
        "ConfiguredUniverse": len(p13.DEFAULT_UNIVERSE),
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

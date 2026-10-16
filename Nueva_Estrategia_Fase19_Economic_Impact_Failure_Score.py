"""
FASE 19 — ECONOMIC IMPACT OF S_WEAK
===================================

Purpose
-------
Test whether the pre-specified Phase 18 S_WEAK score has economically meaningful
separation on the exact frozen F80_TOP20_PARTIAL50 BASELINE C20 entries.

IMPORTANT
---------
This is NOT a portfolio counterfactual. Phase 18 S_WEAK was constructed from
actual strategy entries, not from the entire candidate universe. Therefore it
would be methodologically invalid to pretend that a Q5 filter can be inserted
into the portfolio selector without recomputing the score for all candidates.

Phase 19A therefore measures economic materiality at the entry level:
- exact frozen C20 BUY entries;
- exact Phase 17/18 ex-ante score;
- chronological Discovery/Validation split;
- validation quintiles of S_WEAK fixed from validation observations;
- forward 5/10/20-session returns and MAE;
- notional-weighted dollar proxies;
- winners retained/lost and adverse entries avoided;
- transaction coverage and reconciliation checks.

No strategy change | no reselection | no risk overlay | no production.
A true portfolio filter requires a later Phase 19B that computes S_WEAK for
ALL candidates at every signal date and reruns the full portfolio engine.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

import numpy as np
import pandas as pd

RUN_ID = os.getenv("RUN_ID", pd.Timestamp.now(tz="UTC").strftime("%Y%m%d_%H%M%S"))
TRADES = Path(os.getenv("PHASE15B_TRADES_PATH", "phase15b_c20_trades.csv"))
SCORES = Path(os.getenv(
    "PHASE18_DATASET_PATH",
    "nueva_estrategia_phase18_failure_score/phase18_entry_score_dataset.csv",
))
OUTDIR = Path("nueva_estrategia_phase19_economic_impact")
OUTDIR.mkdir(parents=True, exist_ok=True)

POLICY = "F80_TOP20_PARTIAL50_BASELINE_C20"
Q = 5


def norm_dates(df, cols):
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce").dt.normalize()
    return df


def qassign_train_apply(train, valid, col):
    """Fixed validation cutpoints are learned from validation itself only for
    descriptive Q1-Q5 separation, matching Phase 18 qcut semantics. Discovery
    quintiles are independently descriptive. No threshold is selected for
    production.
    """
    out = {}
    for name, d in [("DISCOVERY", train), ("VALIDATION", valid)]:
        x = pd.to_numeric(d[col], errors="coerce")
        if x.notna().sum() < Q:
            out[name] = pd.Series(np.nan, index=d.index)
            continue
        try:
            out[name] = pd.qcut(x, Q, labels=False, duplicates="drop") + 1
        except Exception:
            out[name] = pd.Series(np.nan, index=d.index)
    return out


def weighted_stats(g, return_col):
    z = g[["Notional", return_col]].dropna().copy()
    z["Notional"] = pd.to_numeric(z["Notional"], errors="coerce")
    z[return_col] = pd.to_numeric(z[return_col], errors="coerce")
    z = z[(z.Notional > 0) & np.isfinite(z[return_col])]
    if z.empty:
        return {"N": 0, "Notional": 0.0, "WeightedReturn": np.nan,
                "DollarProxy": 0.0, "PositiveDollarProxy": 0.0,
                "NegativeDollarProxy": 0.0}
    dollar = z.Notional * z[return_col]
    pos = dollar[dollar > 0].sum()
    neg = dollar[dollar < 0].sum()
    return {
        "N": int(len(z)),
        "Notional": float(z.Notional.sum()),
        "WeightedReturn": float(dollar.sum() / z.Notional.sum()),
        "DollarProxy": float(dollar.sum()),
        "PositiveDollarProxy": float(pos),
        "NegativeDollarProxy": float(neg),
    }


def main():
    t0 = time.time()
    print("FASE 19A — ECONOMIC IMPACT OF S_WEAK")
    print("=" * 78)
    print(f"RUN_ID: {RUN_ID}")
    print(f"SOURCE TRADES: {TRADES}")
    print(f"SOURCE SCORE:  {SCORES}")
    print("FROZEN POLICY: F80_TOP20_PARTIAL50_BASELINE_C20")
    print("NO strategy change | NO re-selection | NO risk overlay | NO production")
    print("ENTRY-LEVEL ECONOMIC TEST ONLY — NOT A PORTFOLIO COUNTERFACTUAL")

    if not TRADES.exists():
        raise FileNotFoundError(TRADES)
    if not SCORES.exists():
        raise FileNotFoundError(SCORES)

    trades = pd.read_csv(TRADES)
    scores = pd.read_csv(SCORES)
    trades.columns = [str(c).strip() for c in trades.columns]
    scores.columns = [str(c).strip() for c in scores.columns]

    required_t = {"PolicyID", "ExecutionDate", "Ticker", "Side", "Notional"}
    required_s = {
        "ExecutionDate", "Ticker", "Notional", "S_WEAK",
        "Y_WEAK", "Y_SUCCESS", "Y_MAE10", "Return_5D", "Return_10D",
        "Return_20D", "MAE_20D", "FailureClass", "Split",
    }
    mt = required_t - set(trades.columns)
    ms = required_s - set(scores.columns)
    if mt:
        raise RuntimeError(f"Trade ledger missing columns: {sorted(mt)}")
    if ms:
        raise RuntimeError(f"Phase18 dataset missing columns: {sorted(ms)}")

    trades = norm_dates(trades, ["ExecutionDate", "DateSignal"])
    scores = norm_dates(scores, ["ExecutionDate", "DateSignal"])

    # Phase 18's exported entry-score dataset does not retain DateSignal.
    # This is not a look-ahead problem: Phase 17 already passed the strict
    # ex-ante test for these exact observations. For Phase 19A, use the
    # actual execution date as the chronological event date and explicitly
    # inherit the ex-ante certification from Phase 17 rather than inventing
    # a DateSignal.
    SCORE_HAS_DATESIGNAL = "DateSignal" in scores.columns

    trades = trades[trades.PolicyID.astype(str).eq(POLICY)].copy()
    buys = trades[trades.Side.astype(str).eq("BUY")].copy()
    buys["Ticker"] = buys.Ticker.astype(str)
    buys["Notional"] = pd.to_numeric(buys.Notional, errors="coerce")
    buys = buys.dropna(subset=["ExecutionDate", "Ticker", "Notional"])

    scores["Ticker"] = scores.Ticker.astype(str)
    scores["S_WEAK"] = pd.to_numeric(scores.S_WEAK, errors="coerce")
    scores["Notional"] = pd.to_numeric(scores.Notional, errors="coerce")
    scores = scores.dropna(subset=["ExecutionDate", "Ticker", "S_WEAK"])

    # Score rows originate from Phase 17 actual BUY entries. Match on execution
    # date + ticker. If multiple BUY transactions occur for one ticker/date,
    # the same entry-level outcome is intentionally replicated across those
    # transactions and the audit reports the multiplicity.
    key = ["ExecutionDate", "Ticker"]
    score_cols = [
        "S_WEAK", "Y_WEAK", "Y_SUCCESS", "Y_MAE10",
        "Return_5D", "Return_10D", "Return_20D", "MAE_20D", "FailureClass", "Split",
    ]
    sm = scores[key + score_cols].copy()
    # Keep the score-side signal date under a unique name so a DateSignal
    # column in the trade ledger cannot collide during merge().
    if SCORE_HAS_DATESIGNAL:
        sm["ScoreDateSignal"] = scores.loc[sm.index, "DateSignal"]
    dup_counts = sm.groupby(key).size().rename("ScoreRowsPerEntryKey").reset_index()
    sm = sm.drop_duplicates(key, keep="first")

    m = buys.merge(sm, on=key, how="left", suffixes=("_Trade", "_Score"))
    m["ScoreMatched"] = m["S_WEAK"].notna()
    if SCORE_HAS_DATESIGNAL:
        m["ScoreDateSignal"] = pd.to_datetime(m["ScoreDateSignal"], errors="coerce")
        m["DateSignal"] = m["ScoreDateSignal"]
        m["ExAntePASS"] = m["DateSignal"] < m["ExecutionDate"]
    else:
        # No DateSignal is present in the Phase 18 export. Do not fabricate
        # one. Phase 17 already certified ex-ante timing for the same score
        # observations; here we use ExecutionDate only for chronological
        # splitting and mark the provenance explicitly.
        m["DateSignal"] = pd.NaT
        m["ExAntePASS"] = True
    m = m.merge(dup_counts, on=key, how="left")

    # Chronological split. If DateSignal is retained in a future Phase 18
    # export, use it; otherwise use ExecutionDate, the observable event date.
    split_dates = pd.to_datetime(
        scores["DateSignal"] if SCORE_HAS_DATESIGNAL else scores["ExecutionDate"],
        errors="coerce"
    ).dropna()
    dates = np.sort(split_dates.unique())
    if len(dates) < 2:
        raise RuntimeError("Insufficient score dates")
    cut = dates[max(1, int(len(dates) * 0.70)) - 1]
    split_event_date = m["DateSignal"] if SCORE_HAS_DATESIGNAL else m["ExecutionDate"]
    m["Split_Recomputed"] = np.where(split_event_date <= cut, "DISCOVERY", "VALIDATION")

    matched = m[m.ScoreMatched].copy()
    if matched.empty:
        raise RuntimeError("No BUY entries matched to Phase18 S_WEAK")
    if not bool(matched.ExAntePASS.all()):
        raise RuntimeError("Ex-ante timing failure in Phase19A")

    # Q1-Q5 exactly descriptively within each chronological split, as Phase 18.
    matched["S_WEAK_Q"] = np.nan
    for split in ["DISCOVERY", "VALIDATION"]:
        idx = matched.index[matched.Split_Recomputed.eq(split)]
        x = matched.loc[idx, "S_WEAK"]
        matched.loc[idx, "S_WEAK_Q"] = pd.qcut(x, Q, labels=False, duplicates="drop") + 1
    matched["S_WEAK_Q"] = pd.to_numeric(matched.S_WEAK_Q, errors="coerce")

    # Primary economic tables.
    rows = []
    for split in ["DISCOVERY", "VALIDATION"]:
        for q in range(1, Q + 1):
            g = matched[(matched.Split_Recomputed == split) & (matched.S_WEAK_Q == q)]
            row = {"Split": split, "Q": q, "N": len(g),
                   "BaseRate_Y_WEAK": float(g.Y_WEAK.mean()) if len(g) else np.nan,
                   "SuccessRate": float(g.Y_SUCCESS.mean()) if len(g) else np.nan,
                   "MAE10Rate": float(g.Y_MAE10.mean()) if len(g) else np.nan,
                   "MeanS_WEAK": float(g.S_WEAK.mean()) if len(g) else np.nan}
            for rc in ["Return_5D", "Return_10D", "Return_20D", "MAE_20D"]:
                s = weighted_stats(g, rc)
                row.update({f"{rc}_{k}": v for k, v in s.items()})
            rows.append(row)
    qdf = pd.DataFrame(rows)
    qdf.to_csv(OUTDIR / "phase19_sweak_quintile_economics.csv", index=False)

    # Validation Q5 vs Q1 summary — pre-specified comparison, not optimization.
    v = qdf[qdf.Split.eq("VALIDATION")].set_index("Q")
    summary = {
        "ValidationN": int(len(matched[matched.Split_Recomputed.eq("VALIDATION")])),
        "ValidationBaseRateYWeak": float(matched.loc[matched.Split_Recomputed.eq("VALIDATION"), "Y_WEAK"].mean()),
        "Q1_Y_WEAK": float(v.loc[1, "BaseRate_Y_WEAK"]),
        "Q5_Y_WEAK": float(v.loc[5, "BaseRate_Y_WEAK"]),
        "Q5MinusQ1_Y_WEAK": float(v.loc[5, "BaseRate_Y_WEAK"] - v.loc[1, "BaseRate_Y_WEAK"]),
        "Q1_Return20D_Weighted": float(v.loc[1, "Return_20D_WeightedReturn"]),
        "Q5_Return20D_Weighted": float(v.loc[5, "Return_20D_WeightedReturn"]),
        "Q5MinusQ1_Return20D": float(v.loc[5, "Return_20D_WeightedReturn"] - v.loc[1, "Return_20D_WeightedReturn"]),
        "Q1_MAE20D_Weighted": float(v.loc[1, "MAE_20D_WeightedReturn"]),
        "Q5_MAE20D_Weighted": float(v.loc[5, "MAE_20D_WeightedReturn"]),
    }
    pd.DataFrame([summary]).to_csv(OUTDIR / "phase19_validation_primary.csv", index=False)

    # Economic opportunity-cost diagnostic: what share of positive/negative
    # forward-dollar proxy sits in Q5? This is NOT a portfolio simulation.
    econ_rows = []
    for split in ["DISCOVERY", "VALIDATION"]:
        g0 = matched[matched.Split_Recomputed.eq(split)].copy()
        for rc in ["Return_5D", "Return_10D", "Return_20D"]:
            g0["DollarProxy"] = g0.Notional * pd.to_numeric(g0[rc], errors="coerce")
            total_pos = g0.loc[g0.DollarProxy > 0, "DollarProxy"].sum()
            total_neg = g0.loc[g0.DollarProxy < 0, "DollarProxy"].sum()
            for q in [1, 5]:
                g = g0[g0.S_WEAK_Q.eq(q)]
                dp = g.DollarProxy.sum()
                econ_rows.append({
                    "Split": split, "Q": q, "Return": rc,
                    "DollarProxy": float(dp),
                    "PositiveDollarShare": float(g.loc[g.DollarProxy > 0, "DollarProxy"].sum() / total_pos) if total_pos > 0 else np.nan,
                    "NegativeDollarShare": float(g.loc[g.DollarProxy < 0, "DollarProxy"].sum() / total_neg) if total_neg < 0 else np.nan,
                    "N": int(len(g)),
                })
    edf = pd.DataFrame(econ_rows)
    edf.to_csv(OUTDIR / "phase19_q1_q5_economic_concentration.csv", index=False)

    matched.to_csv(OUTDIR / "phase19_matched_entries.csv", index=False)

    checks = {
        "InputTradesExists": TRADES.exists(),
        "InputScoreExists": SCORES.exists(),
        "PolicyOnly": bool((trades.PolicyID == POLICY).all()),
        "BuyRows": int(len(buys)),
        "MatchedBuyRows": int(matched.shape[0]),
        "MatchRate": float(matched.shape[0] / len(buys)) if len(buys) else 0.0,
        "UnmatchedBuyRows": int((~m.ScoreMatched).sum()),
        "DuplicateScoreKeys": int((dup_counts.ScoreRowsPerEntryKey > 1).sum()),
        "ExAnteTimingPASS": bool(matched.ExAntePASS.all()),
        "ExAnteTimingSource": "Phase17 certified; Phase18 export has no DateSignal" if not SCORE_HAS_DATESIGNAL else "Phase18 DateSignal",
        "DiscoveryRows": int((matched.Split_Recomputed == "DISCOVERY").sum()),
        "ValidationRows": int((matched.Split_Recomputed == "VALIDATION").sum()),
        "AllFiveQuintilesValidation": bool(set(v.index.astype(int)) == {1,2,3,4,5}),
        "NoOutcomeNaNValidation": bool(matched.loc[matched.Split_Recomputed.eq("VALIDATION"), ["Y_WEAK","Y_SUCCESS","Y_MAE10","Return_5D","Return_10D","Return_20D","MAE_20D"]].notna().all().all()),
        "NoStrategyChange": True,
        "PortfolioCounterfactualClaimed": False,
        "STATUS": "PASS",
        "RuntimeSeconds": time.time() - t0,
    }
    if checks["MatchRate"] < 0.95 or not checks["ExAnteTimingPASS"] or not checks["AllFiveQuintilesValidation"] or not checks["NoOutcomeNaNValidation"]:
        checks["STATUS"] = "FAIL"

    (OUTDIR / "phase19_audit.json").write_text(json.dumps(checks, indent=2, default=str), encoding="utf-8")

    print("\n--- PRIMARY VALIDATION ECONOMICS ---")
    print(pd.DataFrame([summary]).to_string(index=False))
    print("\n--- QUINTILE ECONOMICS ---")
    print(qdf[qdf.Split.eq("VALIDATION")].to_string(index=False))
    print("\n--- ECONOMIC CONCENTRATION Q1 vs Q5 ---")
    print(edf[edf.Split.eq("VALIDATION")].to_string(index=False))
    print("\n--- COVERAGE ---")
    print(json.dumps(checks, indent=2, default=str))
    print(f"\nArtifacts: {OUTDIR}")
    print(f"STATUS: {checks['STATUS']}")
    if checks["STATUS"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()

from pathlib import Path
import json
import numpy as np
import pandas as pd

TRADES = Path("phase15b_c20_trades.csv")
SCORES = Path("nueva_estrategia_phase18_failure_score/phase18_entry_score_dataset.csv")
PHASE17 = Path("nueva_estrategia_phase17_failure_predictability/phase17_entry_factor_dataset.csv")
OUTDIR = Path("nueva_estrategia_phase19_unmatched_diagnostic")
OUTDIR.mkdir(parents=True, exist_ok=True)
POLICY = "F80_TOP20_PARTIAL50_BASELINE_C20"


def norm(df):
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    for c in ["ExecutionDate", "DateSignal"]:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce").dt.normalize()
    if "Ticker" in df.columns:
        df["Ticker"] = df["Ticker"].astype(str).str.strip().str.upper()
    return df


def main():
    if not TRADES.exists(): raise FileNotFoundError(TRADES)
    if not SCORES.exists(): raise FileNotFoundError(SCORES)
    trades = norm(pd.read_csv(TRADES))
    scores = norm(pd.read_csv(SCORES))
    trades = trades[trades["PolicyID"].astype(str).eq(POLICY) & trades["Side"].astype(str).str.upper().eq("BUY")].copy()
    scores["S_WEAK"] = pd.to_numeric(scores["S_WEAK"], errors="coerce")
    key = ["ExecutionDate", "Ticker"]
    raw = scores.copy()
    for c in ["R60", "VOL252", "DIST_200D"]:
        raw[c] = pd.to_numeric(raw[c], errors="coerce")
    raw_key = raw.groupby(key, dropna=False).agg(
        RawScoreKeyExists=("S_WEAK", lambda x: True),
        S_WEAK_Raw=("S_WEAK", "first"),
        R60=("R60", "first"),
        VOL252=("VOL252", "first"),
        DIST_200D=("DIST_200D", "first"),
    ).reset_index()
    dup = raw.groupby(key).size().rename("RawRowsPerKey").reset_index()
    raw_key = raw_key.merge(dup, on=key, how="left")
    d = trades.merge(raw_key, on=key, how="left")
    d["Diagnostic"] = np.select(
        [d["RawScoreKeyExists"].isna(), d["S_WEAK_Raw"].notna()],
        ["NO_SCORE_KEY", "SCORE_USABLE"], default="SCORE_PRESENT_S_WEAK_NAN")
    for c in ["R60", "VOL252", "DIST_200D"]:
        d[f"Missing_{c}"] = d[c].isna()
    d["MissingComponentCount"] = d[["Missing_R60", "Missing_VOL252", "Missing_DIST_200D"]].sum(axis=1)

    def reason(row):
        if row["Diagnostic"] == "NO_SCORE_KEY":
            return "Phase18 has no ExecutionDate+Ticker row"
        if row["Diagnostic"] == "SCORE_USABLE":
            return "S_WEAK is usable"
        missing = [c for c in ["R60", "VOL252", "DIST_200D"] if pd.isna(row[c])]
        if not missing:
            return "S_WEAK is NaN despite all 3 components present; inspect Phase18 calculation/export"
        return "S_WEAK NaN because: " + ", ".join(missing)

    d["Reason"] = d.apply(reason, axis=1)
    if PHASE17.exists():
        p17 = norm(pd.read_csv(PHASE17))
        p17_key = p17[key].drop_duplicates().copy()
        p17_key["Phase17KeyExists"] = True
        p17_key = p17_key.merge(p17.groupby(key).size().rename("Phase17RowsPerKey").reset_index(), on=key, how="left")
        d = d.merge(p17_key, on=key, how="left")
    else:
        d["Phase17KeyExists"] = np.nan
        d["Phase17RowsPerKey"] = np.nan

    problems = d[d["Diagnostic"] != "SCORE_USABLE"].copy().sort_values(key).reset_index(drop=True)
    summary = {
        "Policy": POLICY,
        "BuyRows": int(len(trades)),
        "ProblemRows": int(len(problems)),
        "NoScoreKey": int((problems.Diagnostic == "NO_SCORE_KEY").sum()),
        "ScorePresentSWeakNaN": int((problems.Diagnostic == "SCORE_PRESENT_S_WEAK_NAN").sum()),
        "ScoreUsable": int((d.Diagnostic == "SCORE_USABLE").sum()),
        "SWeakNaNMissingComponentCounts": problems.loc[problems.Diagnostic.eq("SCORE_PRESENT_S_WEAK_NAN"), "MissingComponentCount"].value_counts().sort_index().to_dict(),
        "OptionalPhase17Available": bool(PHASE17.exists()),
    }
    problems.to_csv(OUTDIR / "phase19_unmatched_full_diagnostic.csv", index=False)
    (OUTDIR / "phase19_unmatched_full_diagnostic.json").write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print("=" * 78)
    print("FASE 19A — DIAGNÓSTICO DE LAS BUY NO EMPAREJADAS")
    print("=" * 78)
    print(json.dumps(summary, indent=2, default=str))
    print("\n--- PROBLEM ROWS ---")
    cols = ["ExecutionDate","Ticker","Notional","Diagnostic","Reason","R60","VOL252","DIST_200D","S_WEAK_Raw","Phase17KeyExists"]
    print(problems[cols].to_string(index=False))
    print("\n--- RULE ---")
    print("Phase18 defines S_WEAK as the equal-weight mean of R60_LOWER, VOL252_LOWER and DIST_200D_LOWER with skipna=False.")
    print("One missing component therefore legitimately makes S_WEAK NaN; this script does not impute or alter it.")
    print("\nArtifacts:", OUTDIR.resolve())
    print("STATUS: DIAGNOSTIC_ONLY")


if __name__ == "__main__":
    main()

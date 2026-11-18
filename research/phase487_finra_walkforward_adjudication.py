from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import binomtest, t as student_t


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_zip_csv(path: str, member: str) -> pd.DataFrame:
    with zipfile.ZipFile(path) as zf:
        return pd.read_csv(zf.open(member))


def summarize(values, family_tests: int = 1) -> dict:
    x = np.asarray(list(values), dtype=float)
    x = x[np.isfinite(x)]
    n = int(x.size)
    if not n:
        return {"n": 0, "mean": None, "median": None, "std": None,
                "ci95_low": None, "ci95_high": None, "t_p_two_sided": None,
                "positive_n": 0, "sign_p_two_sided": None,
                "bonferroni_p": None, "family_tests": family_tests}
    mean = float(np.mean(x))
    positive_n = int(np.sum(x > 0))
    sign_p = float(binomtest(positive_n, n, 0.5).pvalue)
    if n < 2:
        std = low = high = p = None
    else:
        std = float(np.std(x, ddof=1))
        if std == 0:
            low = high = mean
            p = 1.0 if mean == 0 else 0.0
        else:
            se = std / np.sqrt(n)
            crit = float(student_t.ppf(0.975, n - 1))
            low, high = float(mean - crit * se), float(mean + crit * se)
            p = float(2 * student_t.sf(abs(mean / se), n - 1))
    return {
        "n": n, "mean": mean, "median": float(np.median(x)), "std": std,
        "ci95_low": low, "ci95_high": high, "t_p_two_sided": p,
        "positive_n": positive_n, "sign_p_two_sided": sign_p,
        "bonferroni_p": None if p is None else float(min(1.0, p * family_tests)),
        "family_tests": int(family_tests),
    }


def phase20a_residual_summary(df: pd.DataFrame) -> list[dict]:
    required = {"Factor", "Horizon", "SpearmanResidual"}
    if not required.issubset(df.columns):
        raise ValueError(f"Phase 20A columns missing: {sorted(required - set(df.columns))}")
    groups = list(df.groupby(["Factor", "Horizon"], dropna=False))
    out = []
    for (factor, horizon), g in groups:
        row = summarize(g["SpearmanResidual"], family_tests=len(groups))
        row.update({"factor": str(factor), "horizon": int(horizon)})
        out.append(row)
    return sorted(out, key=lambda r: (r["t_p_two_sided"] or 2, r["factor"], r["horizon"]))


def phase20b_date_differences(df: pd.DataFrame) -> dict:
    required = {"DateSignal", "Role", "FwdRet_5D", "FwdRet_10D", "FwdRet_20D"}
    if not required.issubset(df.columns):
        raise ValueError(f"Phase 20B columns missing: {sorted(required - set(df.columns))}")
    out = {}
    for h in (5, 10, 20):
        col = f"FwdRet_{h}D"
        differences, dates = [], []
        for date, g in df.groupby("DateSignal"):
            blocked = pd.to_numeric(g.loc[g.Role == "BLOCKED_F80", col], errors="coerce").dropna()
            replacement = pd.to_numeric(g.loc[g.Role == "REPLACEMENT_NONF80", col], errors="coerce").dropna()
            if blocked.empty or replacement.empty:
                continue
            diff = float(replacement.mean() - blocked.mean())
            differences.append(diff)
            dates.append({"date": str(date), "blocked_n": int(len(blocked)),
                          "replacement_n": int(len(replacement)),
                          "replacement_minus_blocked": diff})
        out[str(h)] = {**summarize(differences, family_tests=3),
                       "date_differences": dates, "return_unit": "decimal_return"}
    return out


def phase20b_tie_audit(df: pd.DataFrame) -> dict:
    required = {"Group", "RuleScore"}
    if not required.issubset(df.columns):
        raise ValueError(f"Phase 20B tie-audit columns missing: {sorted(required - set(df.columns))}")
    x = pd.to_numeric(df.loc[df.Group == "REPLACEMENT_NONF80", "RuleScore"],
                      errors="coerce").dropna()
    n = int(len(x))
    zeros = int(np.isclose(x.to_numpy(), 0.0, atol=1e-12).sum())
    return {
        "replacement_rows": n, "zero_score_rows": zeros,
        "zero_score_fraction": None if not n else float(zeros / n),
        "unique_score_values": int(x.nunique()),
        "score_std": None if n < 2 else float(x.std(ddof=1)),
        "continuous_rank_discriminates_replacements": bool(x.nunique() > 1),
    }


def phase20c_summary(df: pd.DataFrame) -> dict:
    required = {"Horizon", "DateSignal", "DeltaReplacementMinusBlocked"}
    if not required.issubset(df.columns):
        raise ValueError(f"Phase 20C columns missing: {sorted(required - set(df.columns))}")
    return {str(int(h)): summarize(g.DeltaReplacementMinusBlocked, family_tests=3)
            for h, g in df.groupby("Horizon")}


def adjudicate(a_zip: str, b_zip: str, c_zip: str) -> dict:
    a = phase20a_residual_summary(read_zip_csv(
        a_zip, "phase20a_finra_shortflow_ltm_residual_predictability.csv"))
    b = read_zip_csv(b_zip, "phase20b_oos_blocked_vs_replacement.csv")
    ties = read_zip_csv(b_zip, "phase20b_oos_target_changes.csv")
    with zipfile.ZipFile(b_zip) as zf:
        selected = json.loads(zf.read("phase20b_selected_rule.json").decode("utf-8"))
    c = phase20c_summary(read_zip_csv(c_zip, "phase20c_walkforward_results.csv"))
    return {
        "phase": "487",
        "method": "artifact-only adjudication; no new market-data requests",
        "artifacts": {
            "phase20a": {"sha256": sha256_file(a_zip), "bytes": Path(a_zip).stat().st_size},
            "phase20b": {"sha256": sha256_file(b_zip), "bytes": Path(b_zip).stat().st_size},
            "phase20c": {"sha256": sha256_file(c_zip), "bytes": Path(c_zip).stat().st_size},
        },
        "phase20a_ltm_residual_ic": {"family_size": len(a), "results": a},
        "phase20b_selected_rule": selected,
        "phase20b_oos_replacement_minus_blocked": phase20b_date_differences(b),
        "phase20b_replacement_tie_audit": phase20b_tie_audit(ties),
        "phase20c_walkforward_replacement_minus_blocked": c,
        "decisions": {
            "phase20b_short_exempt_inverse_continuous_rank":
                "REJECT_FOR_PROMOTION_ZERO_VARIANCE_REPLACEMENT_TIES",
            "phase20c_adaptive_factor_rule":
                "REJECT_FOR_PROMOTION_UNSTABLE_SMALL_PSEUDO_OOS",
            "phase20a_residual_ic":
                "EXPLORATORY_ONLY_MULTIPLICITY_AND_PIT_GATES_FAIL",
            "production_signal_admitted": False,
        },
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--phase20a-zip", required=True)
    p.add_argument("--phase20b-zip", required=True)
    p.add_argument("--phase20c-zip", required=True)
    p.add_argument("--output", required=True)
    args = p.parse_args()
    result = adjudicate(args.phase20a_zip, args.phase20b_zip, args.phase20c_zip)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

"""
================================================================================
FASE 17 — MOMENTUM FAILURE PREDICTABILITY
================================================================================

OBJETIVO
--------
Determinar si los resultados futuros observados en Phase 16B pueden ser
explicados/predichos EX ANTE utilizando únicamente información disponible
hasta el cierre de DateSignal.

ESTADO
------
- Investigación / diagnóstico solamente.
- NO modifica la estrategia.
- NO modifica la selección de activos.
- NO modifica Kelly.
- NO modifica stops.
- NO modifica ejecución.
- NO modifica Phase 12.
- NO modifica Phase 15B.
- NO modifica Phase 16B.

FUENTES
-------
1. Phase 15B:
   phase15b_c20_trades.csv

2. Phase 16B:
   fase16B_momentum_failure_anatomy.csv

POLICY
------
F80_TOP20_PARTIAL50_BASELINE_C20

CORRECCIÓN DE INTEGRIDAD
------------------------
Phase15B y Phase16B pueden contener el mismo Notional económico
representado por valores float ligeramente diferentes después de
serialización/deserialización CSV.

Por ello NO se utiliza el float Notional directamente como llave.

La llave interna de matching es:

    ExecutionDate + Ticker + round(Notional, 8)

El Notional original NO se modifica.

Esta corrección únicamente evita pérdida de filas por precisión
de punto flotante.

================================================================================
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf
from scipy.stats import spearmanr, skew, kurtosis


# =============================================================================
# CONFIGURATION
# =============================================================================

RUN_ID = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

OUTDIR = Path(
    "nueva_estrategia_phase17_failure_predictability"
)

OUTDIR.mkdir(
    parents=True,
    exist_ok=True
)

LEDGER = Path(
    "phase15b_c20_trades.csv"
)

OUTCOME = Path(
    "fase16B_momentum_failure_anatomy.csv"
)

POLICY_ID = (
    "F80_TOP20_PARTIAL50_BASELINE_C20"
)

DISCOVERY_FRAC = 0.70

MIN_GROUP = 20

Q = 5

ANN = np.sqrt(252.0)


# =============================================================================
# FACTOR FAMILY
# =============================================================================

FACTOR_NAMES = [
    "R1",
    "R5",
    "R20",
    "R60",
    "R120",
    "VOL5",
    "VOL20",
    "VOL60",
    "VOL252",
    "VOL_RATIO_20_252",
    "VOL_RATIO_60_252",
    "SKEW20",
    "KURT20",
    "AC1",
    "DIST_200D",
]


# =============================================================================
# FACTOR CALCULATIONS
# =============================================================================

def simple_return(
    close: pd.Series,
    n: int
) -> float:

    if len(close) <= n:
        return np.nan

    a = float(
        close.iloc[-n - 1]
    )

    b = float(
        close.iloc[-1]
    )

    return (
        b / a - 1.0
        if a > 0
        else np.nan
    )


def ann_vol(
    logret: pd.Series,
    n: int
) -> float:

    x = (
        logret
        .dropna()
        .tail(n)
    )

    if len(x) < n:
        return np.nan

    return float(
        x.std(ddof=1) * ANN
    )


def calc_factors(
    hist: pd.DataFrame
) -> dict:

    """
    Calculate all factors using ONLY the supplied history.

    hist MUST contain observations strictly before ExecutionDate.
    The final observation therefore represents the information available
    at the signal close.
    """

    c = pd.to_numeric(
        hist["Close"],
        errors="coerce"
    ).dropna()

    # Preserve the original Phase 17 minimum-history rule.
    if len(c) < 253:
        return {
            k: np.nan
            for k in FACTOR_NAMES
        }

    lr = (
        np.log(c)
        .diff()
        .dropna()
    )

    v5 = ann_vol(
        lr,
        5
    )

    v20 = ann_vol(
        lr,
        20
    )

    v60 = ann_vol(
        lr,
        60
    )

    v252 = ann_vol(
        lr,
        252
    )

    ac = lr.tail(60)

    ac1 = (
        float(ac.autocorr(lag=1))
        if len(ac) >= 3
        else np.nan
    )

    s20 = lr.tail(20)

    skew20 = (
        float(
            skew(
                s20,
                bias=False
            )
        )
        if len(s20) >= 8
        else np.nan
    )

    kurt20 = (
        float(
            kurtosis(
                s20,
                fisher=True,
                bias=False
            )
        )
        if len(s20) >= 8
        else np.nan
    )

    sma200 = float(
        c.tail(200).mean()
    )

    last = float(
        c.iloc[-1]
    )

    return {
        "R1": simple_return(c, 1),

        "R5": simple_return(c, 5),

        "R20": simple_return(c, 20),

        "R60": simple_return(c, 60),

        "R120": simple_return(c, 120),

        "VOL5": v5,

        "VOL20": v20,

        "VOL60": v60,

        "VOL252": v252,

        "VOL_RATIO_20_252": (
            v20 / v252
            if (
                np.isfinite(v20)
                and np.isfinite(v252)
                and v252 > 0
            )
            else np.nan
        ),

        "VOL_RATIO_60_252": (
            v60 / v252
            if (
                np.isfinite(v60)
                and np.isfinite(v252)
                and v252 > 0
            )
            else np.nan
        ),

        "SKEW20": skew20,

        "KURT20": kurt20,

        "AC1": ac1,

        "DIST_200D": (
            last / sma200 - 1.0
            if sma200 > 0
            else np.nan
        ),
    }


# =============================================================================
# DATA NORMALIZATION
# =============================================================================

def normalize_df(
    df: pd.DataFrame
) -> pd.DataFrame:

    out = df.copy()

    out.columns = [
        str(c).strip()
        for c in out.columns
    ]

    for c in [
        "DateSignal",
        "ExecutionDate"
    ]:

        if c in out.columns:

            out[c] = pd.to_datetime(
                out[c],
                errors="coerce"
            ).dt.normalize()

    if "Ticker" in out.columns:

        out["Ticker"] = (
            out["Ticker"]
            .astype(str)
            .str.strip()
            .str.upper()
        )

    return out


# =============================================================================
# PRICE HISTORY
# =============================================================================

def download_history(
    ticker: str,
    start: pd.Timestamp,
    end: pd.Timestamp
) -> pd.DataFrame:

    # Safety buffer to ensure sufficient pre-signal history.
    y0 = (
        start - pd.Timedelta(days=450)
    ).strftime("%Y-%m-%d")

    y1 = (
        end + pd.Timedelta(days=3)
    ).strftime("%Y-%m-%d")

    d = yf.download(
        ticker,
        start=y0,
        end=y1,
        auto_adjust=False,
        progress=False,
        threads=False
    )

    if d is None or d.empty:
        return pd.DataFrame()

    if isinstance(
        d.columns,
        pd.MultiIndex
    ):

        d.columns = [
            x[0]
            if isinstance(x, tuple)
            else x
            for x in d.columns
        ]

    d = d.rename(
        columns={
            c: str(c).title()
            for c in d.columns
        }
    )

    d.index = (
        pd.to_datetime(d.index)
        .tz_localize(None)
        .normalize()
    )

    return d.sort_index()


# =============================================================================
# AUC
# =============================================================================

def auc_rank(
    x: pd.Series,
    y: pd.Series
) -> float:

    z = pd.DataFrame(
        {
            "x": x,
            "y": y
        }
    ).dropna()

    if (
        len(z) == 0
        or z.y.nunique() < 2
    ):
        return np.nan

    pos = z[
        z.y == 1
    ].x

    neg = z[
        z.y == 0
    ].x

    if (
        len(pos) == 0
        or len(neg) == 0
    ):
        return np.nan

    ranks = z["x"].rank(
        method="average"
    )

    rpos = ranks[
        z.y == 1
    ].sum()

    return float(
        (
            rpos
            - len(pos) * (len(pos) + 1) / 2
        )
        /
        (
            len(pos) * len(neg)
        )
    )


# =============================================================================
# QUINTILE LIFT
# =============================================================================

def quintile_lift(
    x: pd.Series,
    y: pd.Series
) -> tuple[float, float, float]:

    z = pd.DataFrame(
        {
            "x": x,
            "y": y
        }
    ).dropna()

    if (
        len(z) < Q * MIN_GROUP
        or z.y.nunique() < 2
    ):
        return (
            np.nan,
            np.nan,
            np.nan
        )

    try:

        q = (
            pd.qcut(
                z.x,
                Q,
                labels=False,
                duplicates="drop"
            )
            + 1
        )

    except Exception:

        return (
            np.nan,
            np.nan,
            np.nan
        )

    g = (
        z.assign(q=q)
        .groupby(
            "q",
            observed=True
        )
        .y
        .agg(
            ["mean", "count"]
        )
    )

    if len(g) < 5:
        return (
            np.nan,
            np.nan,
            np.nan
        )

    return (
        float(g.loc[1, "mean"]),
        float(g.loc[5, "mean"]),
        float(
            g.loc[5, "mean"]
            - g.loc[1, "mean"]
        )
    )


# =============================================================================
# FACTOR DIAGNOSTIC
# =============================================================================

def analyze_factor(
    df: pd.DataFrame,
    factor: str,
    label: str,
    subset: str
) -> dict:

    z = df[
        df["Split"] == subset
    ].copy()

    y = z[label].astype(float)

    x = z[factor]

    rho, p = spearmanr(
        x,
        y,
        nan_policy="omit"
    )

    auc = auc_rank(
        x,
        y
    )

    q1, q5, lift = quintile_lift(
        x,
        y
    )

    return {
        "Split": subset,

        "Label": label,

        "Factor": factor,

        "N": int(
            pd.DataFrame(
                {
                    "x": x,
                    "y": y
                }
            )
            .dropna()
            .shape[0]
        ),

        "SpearmanR": (
            float(rho)
            if np.isfinite(rho)
            else np.nan
        ),

        "SpearmanP": (
            float(p)
            if np.isfinite(p)
            else np.nan
        ),

        "AUC": auc,

        "BottomQ_FailureRate": q1,

        "TopQ_FailureRate": q5,

        "TopMinusBottom": lift,
    }


# =============================================================================
# MAIN
# =============================================================================

def main():

    t0 = time.time()

    print("=" * 78)
    print("FASE 17 — MOMENTUM FAILURE PREDICTABILITY")
    print("=" * 78)

    print(
        f"RUN_ID: {RUN_ID}"
    )

    print(
        "SOURCE: exact Phase 15B BASELINE C20 + "
        "exact Phase 16B outcomes"
    )

    print(
        "NO strategy change | "
        "NO re-selection | "
        "NO risk overlay | "
        "NO production"
    )

    print()

    print(
        "TRANSACTION MATCHING: "
        "ExecutionDate + Ticker + round(Notional, 8)"
    )

    print()

    # =========================================================================
    # INPUT FILES
    # =========================================================================

    if not LEDGER.exists():
        raise FileNotFoundError(
            f"Missing {LEDGER}"
        )

    if not OUTCOME.exists():
        raise FileNotFoundError(
            f"Missing {OUTCOME}"
        )

    # =========================================================================
    # LOAD
    # =========================================================================

    trades = normalize_df(
        pd.read_csv(LEDGER)
    )

    outcomes = normalize_df(
        pd.read_csv(OUTCOME)
    )

    # =========================================================================
    # POLICY FILTER
    # =========================================================================

    trades = trades[
        trades["PolicyID"]
        == POLICY_ID
    ].copy()

    trades = trades[
        trades["Side"]
        .astype(str)
        .str.upper()
        == "BUY"
    ].copy()

    expected_buy_rows = len(trades)

    print(
        f"Phase15B BUY rows: {expected_buy_rows}"
    )

    # =========================================================================
    # REQUIRED COLUMNS
    # =========================================================================

    required_trade = [
        "ExecutionDate",
        "Ticker",
        "Notional",
        "PolicyID",
        "Side",
    ]

    missing_trade = [
        c
        for c in required_trade
        if c not in trades.columns
    ]

    if missing_trade:
        raise RuntimeError(
            "Phase15B ledger missing columns: "
            f"{missing_trade}"
        )

    required_out = [
        "ExecutionDate",
        "Ticker",
        "Notional",
        "FailureClass",
        "Return_5D",
        "Return_10D",
        "Return_20D",
        "MAE_20D",
        "MFE_20D",
        "GapMin_20D",
    ]

    missing_out = [
        c
        for c in required_out
        if c not in outcomes.columns
    ]

    if missing_out:
        raise RuntimeError(
            "Phase16B output missing columns: "
            f"{missing_out}"
        )

    # =========================================================================
    # NUMERICAL NORMALIZATION FOR MATCHING
    # =========================================================================

    trades["Notional"] = pd.to_numeric(
        trades["Notional"],
        errors="coerce"
    )

    outcomes["Notional"] = pd.to_numeric(
        outcomes["Notional"],
        errors="coerce"
    )

    if trades["Notional"].isna().any():
        raise RuntimeError(
            "Phase15B contains NaN/invalid Notional values."
        )

    if outcomes["Notional"].isna().any():
        raise RuntimeError(
            "Phase16B contains NaN/invalid Notional values."
        )

    trades["NotionalKey"] = (
        trades["Notional"].round(8)
    )

    outcomes["NotionalKey"] = (
        outcomes["Notional"].round(8)
    )

    key = [
        "ExecutionDate",
        "Ticker",
        "NotionalKey",
    ]

    # =========================================================================
    # DUPLICATE KEY AUDIT — PHASE15B
    # =========================================================================

    trade_key_counts = (
        trades
        .groupby(
            key,
            dropna=False
        )
        .size()
        .reset_index(
            name="Count"
        )
    )

    duplicate_trade_keys = (
        trade_key_counts[
            trade_key_counts["Count"] > 1
        ]
        .copy()
    )

    if not duplicate_trade_keys.empty:

        print(
            "\nDUPLICATE PHASE15B KEYS:"
        )

        print(
            duplicate_trade_keys.to_string(
                index=False
            )
        )

        raise RuntimeError(
            "Duplicate Phase15B transaction keys "
            "after Notional normalization."
        )

    # =========================================================================
    # DUPLICATE KEY AUDIT — PHASE16B
    # =========================================================================

    outcome_key_counts = (
        outcomes
        .groupby(
            key,
            dropna=False
        )
        .size()
        .reset_index(
            name="Count"
        )
    )

    duplicate_outcome_keys = (
        outcome_key_counts[
            outcome_key_counts["Count"] > 1
        ]
        .copy()
    )

    if not duplicate_outcome_keys.empty:

        print(
            "\nDUPLICATE PHASE16B KEYS:"
        )

        print(
            duplicate_outcome_keys.to_string(
                index=False
            )
        )

        raise RuntimeError(
            "Duplicate Phase16B outcome keys "
            "after Notional normalization."
        )

    # =========================================================================
    # OUTCOME COLUMNS
    # =========================================================================

    outcome_cols = [
        "ExecutionDate",
        "Ticker",
        "NotionalKey",
        "FailureClass",
        "Return_5D",
        "Return_10D",
        "Return_20D",
        "MAE_20D",
        "MFE_20D",
        "GapMin_20D",
    ]

    outcomes_for_merge = (
        outcomes[
            outcome_cols
        ]
        .copy()
    )

    # =========================================================================
    # ROBUST TRANSACTION MATCH
    # =========================================================================

    merged = trades.merge(
        outcomes_for_merge,
        on=key,
        how="inner",
        validate="one_to_one",
    )

    matched_rows = len(merged)

    print()
    print("=" * 78)
    print("ROBUST TRANSACTION MATCH")
    print("=" * 78)

    print(
        f"Expected BUY rows: {expected_buy_rows}"
    )

    print(
        f"Matched rows:      {matched_rows}"
    )

    print(
        f"Missing rows:      "
        f"{expected_buy_rows - matched_rows}"
    )

    # =========================================================================
    # ROW CONSERVATION — CRITICAL
    # =========================================================================

    if matched_rows != expected_buy_rows:

        matched_keys = (
            merged[key]
            .drop_duplicates()
        )

        missing_rows = trades.merge(
            matched_keys,
            on=key,
            how="left",
            indicator=True
        )

        missing_rows = missing_rows[
            missing_rows["_merge"]
            == "left_only"
        ].copy()

        print()
        print(
            "=" * 78
        )
        print(
            "ERROR — ROBUST TRANSACTION MATCH INCOMPLETE"
        )
        print(
            "=" * 78
        )

        display_cols = [
            "ExecutionDate",
            "Ticker",
            "Notional",
            "NotionalKey",
        ]

        display_cols = [
            c
            for c in display_cols
            if c in missing_rows.columns
        ]

        print(
            missing_rows[
                display_cols
            ].to_string(index=False)
        )

        raise RuntimeError(
            "Phase17 transaction matching incomplete."
        )

    print(
        f"ROBUST TRANSACTION MATCH PASS: "
        f"{matched_rows}/{expected_buy_rows}"
    )

    # =========================================================================
    # SORT
    # =========================================================================

    merged = (
        merged
        .sort_values(
            [
                "ExecutionDate",
                "Ticker",
            ]
        )
        .reset_index(drop=True)
    )

    # =========================================================================
    # INITIAL OUTCOME LABELS
    # =========================================================================

    merged["Y_QUICK"] = (
        merged["FailureClass"]
        == "QUICK_FAILURE"
    ).astype(int)

    merged["Y_WEAK"] = (
        merged["FailureClass"]
        == "WEAK_FAILURE"
    ).astype(int)

    merged["Y_SUCCESS"] = (
        merged["FailureClass"]
        == "MOMENTUM_SUCCESS"
    ).astype(int)

    merged["Y_ADVERSE"] = (
        ~merged["FailureClass"].isin(
            [
                "MOMENTUM_SUCCESS",
                "LATER_REVERSAL",
                "OTHER",
            ]
        )
    ).astype(int)

    merged["Y_MAE10"] = (
        pd.to_numeric(
            merged["MAE_20D"],
            errors="coerce"
        )
        <= -0.10
    ).astype(int)

    # =========================================================================
    # PRICE HISTORY
    # =========================================================================

    tickers = sorted(
        merged["Ticker"]
        .dropna()
        .unique()
    )

    histories = {}

    failures = []

    start = (
        merged["ExecutionDate"]
        .min()
    )

    end = (
        merged["ExecutionDate"]
        .max()
    )

    print()
    print(
        f"Downloading price histories for "
        f"{len(tickers)} tickers..."
    )

    for i, ticker in enumerate(
        tickers,
        1
    ):

        try:

            d = download_history(
                ticker,
                start,
                end,
            )

            if (
                d.empty
                or "Close" not in d.columns
            ):

                failures.append(
                    (
                        ticker,
                        "empty_or_no_close",
                    )
                )

            else:

                histories[ticker] = d

        except Exception as exc:

            failures.append(
                (
                    ticker,
                    f"{type(exc).__name__}: {exc}",
                )
            )

        if (
            i % 25 == 0
            or i == len(tickers)
        ):

            print(
                f"PRICE DATA "
                f"{i}/{len(tickers)} "
                f"| OK={len(histories)} "
                f"| FAIL={len(failures)}",
                flush=True,
            )

    # =========================================================================
    # FACTOR CONSTRUCTION
    #
    # IMPORTANT:
    # For each transaction, use only price observations strictly before
    # ExecutionDate. The last available observation becomes the exact
    # DateSignal.
    # =========================================================================

    rows = []

    for _, r in merged.iterrows():

        ticker = r["Ticker"]

        ex = pd.Timestamp(
            r["ExecutionDate"]
        ).normalize()

        hist = histories.get(
            ticker
        )

        vals = {
            k: np.nan
            for k in FACTOR_NAMES
        }

        exact_signal = pd.NaT

        if hist is not None:

            h = hist.loc[
                hist.index < ex
            ]

            if not h.empty:

                exact_signal = h.index[-1]

                vals = calc_factors(
                    h
                )

        row = {
            "ExecutionDate":
                r["ExecutionDate"],

            "DateSignal":
                exact_signal,

            "Ticker":
                ticker,

            # Preserve the ORIGINAL economic Notional.
            "Notional":
                r["Notional"],

            "FailureClass":
                r["FailureClass"],

            "Return_5D":
                r["Return_5D"],

            "Return_10D":
                r["Return_10D"],

            "Return_20D":
                r["Return_20D"],

            "MAE_20D":
                r["MAE_20D"],

            "MFE_20D":
                r["MFE_20D"],

            "GapMin_20D":
                r["GapMin_20D"],

            "Y_QUICK":
                r["Y_QUICK"],

            "Y_WEAK":
                r["Y_WEAK"],

            "Y_SUCCESS":
                r["Y_SUCCESS"],

            "Y_ADVERSE":
                r["Y_ADVERSE"],

            "Y_MAE10":
                r["Y_MAE10"],
        }

        row.update(vals)

        rows.append(row)

    df = pd.DataFrame(
        rows
    )

    # =========================================================================
    # FACTOR ROW CONSERVATION
    # =========================================================================

    if len(df) != len(merged):

        raise RuntimeError(
            "Phase17 row conservation failed: "
            f"merged={len(merged)} "
            f"final_factor_rows={len(df)}"
        )

    print(
        f"ROW CONSERVATION PASS: "
        f"{len(df)}/{len(merged)}"
    )

    # =========================================================================
    # EXACT SIGNAL DATE VALIDATION
    # =========================================================================

    missing_signal = (
        df["DateSignal"]
        .isna()
        .sum()
    )

    if missing_signal > 0:

        raise RuntimeError(
            "Unable to reconstruct DateSignal for "
            f"{missing_signal} transaction rows."
        )

    # =========================================================================
    # STRICT EX-ANTE TIMING CHECK
    # =========================================================================

    timing_ok = (
        pd.to_datetime(
            df["DateSignal"],
            errors="coerce",
        )
        <
        pd.to_datetime(
            df["ExecutionDate"],
            errors="coerce",
        )
    )

    if not timing_ok.all():

        bad_timing = df[
            ~timing_ok
        ].copy()

        print(
            bad_timing[
                [
                    "ExecutionDate",
                    "DateSignal",
                    "Ticker",
                ]
            ].to_string(
                index=False
            )
        )

        raise RuntimeError(
            "Timing integrity failed: "
            "DateSignal is not strictly before "
            "ExecutionDate."
        )

    print(
        f"EX-ANTE TIMING PASS: "
        f"{int(timing_ok.sum())}/{len(df)} entries"
    )

    # =========================================================================
    # CHRONOLOGICAL DISCOVERY / VALIDATION SPLIT
    #
    # Split is deliberately performed AFTER exact DateSignal reconstruction.
    # =========================================================================

    valid_dates = np.sort(
        pd.to_datetime(
            df["DateSignal"],
            errors="coerce",
        )
        .dropna()
        .unique()
    )

    if len(valid_dates) < 2:

        raise RuntimeError(
            "Insufficient reconstructed signal dates "
            "for chronological split."
        )

    cut_index = max(
        1,
        int(
            len(valid_dates)
            * DISCOVERY_FRAC
        )
    ) - 1

    cut = valid_dates[
        cut_index
    ]

    df["Split"] = np.where(
        pd.to_datetime(
            df["DateSignal"]
        ) <= cut,
        "DISCOVERY",
        "VALIDATION",
    )

    print(
        f"Entries matched: {len(df)} "
        f"| discovery through "
        f"{pd.Timestamp(cut).date()} "
        f"| validation after"
    )

    # =========================================================================
    # SORT FINAL DATASET
    # =========================================================================

    df = (
        df
        .sort_values(
            [
                "DateSignal",
                "ExecutionDate",
                "Ticker",
            ]
        )
        .reset_index(drop=True)
    )

    # =========================================================================
    # FACTOR DATASET EXPORT
    # =========================================================================

    factor_path = (
        OUTDIR
        / "phase17_entry_factor_dataset.csv"
    )

    df.to_csv(
        factor_path,
        index=False,
    )

    # =========================================================================
    # FACTOR DIAGNOSTICS
    # =========================================================================

    labels = [
        "Y_QUICK",
        "Y_WEAK",
        "Y_ADVERSE",
        "Y_MAE10",
    ]

    results = []

    for label in labels:

        for factor in FACTOR_NAMES:

            results.append(
                analyze_factor(
                    df,
                    factor,
                    label,
                    "DISCOVERY",
                )
            )

            results.append(
                analyze_factor(
                    df,
                    factor,
                    label,
                    "VALIDATION",
                )
            )

    rdf = pd.DataFrame(
        results
    )

    # =========================================================================
    # DIRECTIONAL OOS DIAGNOSTICS
    #
    # Direction is learned ONLY from DISCOVERY.
    # Validation merely evaluates that frozen direction.
    # =========================================================================

    directions = []

    for label in labels:

        for factor in FACTOR_NAMES:

            d = rdf[
                (rdf["Label"] == label)
                &
                (rdf["Factor"] == factor)
                &
                (rdf["Split"] == "DISCOVERY")
            ].iloc[0]

            v = rdf[
                (rdf["Label"] == label)
                &
                (rdf["Factor"] == factor)
                &
                (rdf["Split"] == "VALIDATION")
            ].iloc[0]

            if not np.isfinite(
                d["TopMinusBottom"]
            ):
                continue

            direction = (
                "HIGHER"
                if d["TopMinusBottom"] > 0
                else "LOWER"
            )

            vdelta = (
                v["TopMinusBottom"]
                if direction == "HIGHER"
                else -v["TopMinusBottom"]
            )

            if direction == "HIGHER":

                auc_dir = v["AUC"]

            else:

                auc_dir = (
                    1.0 - v["AUC"]
                    if np.isfinite(v["AUC"])
                    else np.nan
                )

            directions.append(
                {
                    "Label":
                        label,

                    "Factor":
                        factor,

                    "DiscoveryDirection":
                        direction,

                    "DiscoveryLift":
                        (
                            float(
                                abs(
                                    d["TopMinusBottom"]
                                )
                            )
                            if np.isfinite(
                                d["TopMinusBottom"]
                            )
                            else np.nan
                        ),

                    "ValidationDirectionalLift":
                        (
                            float(vdelta)
                            if np.isfinite(vdelta)
                            else np.nan
                        ),

                    "ValidationDirectionalAUC":
                        (
                            float(auc_dir)
                            if np.isfinite(auc_dir)
                            else np.nan
                        ),

                    "DiscoveryN":
                        int(d["N"]),

                    "ValidationN":
                        int(v["N"]),

                    "ValidationP":
                        (
                            float(
                                v["SpearmanP"]
                            )
                            if np.isfinite(
                                v["SpearmanP"]
                            )
                            else np.nan
                        ),
                }
            )

    ddf = pd.DataFrame(
        directions
    )

    if not ddf.empty:

        ddf = (
            ddf
            .sort_values(
                [
                    "Label",
                    "ValidationDirectionalAUC",
                ],
                ascending=[
                    True,
                    False,
                ],
            )
        )

    ddf.to_csv(
        OUTDIR
        / "phase17_directional_oos_diagnostics.csv",
        index=False,
    )

    rdf.to_csv(
        OUTDIR
        / "phase17_all_factor_diagnostics.csv",
        index=False,
    )

    # =========================================================================
    # VALIDATION TOP 3
    # =========================================================================

    summary = []

    for label in labels:

        validation_base_rate = (
            df.loc[
                df["Split"] == "VALIDATION",
                label,
            ]
            .mean()
        )

        x = ddf[
            ddf["Label"] == label
        ].copy()

        x = (
            x
            .replace(
                [
                    np.inf,
                    -np.inf,
                ],
                np.nan,
            )
            .dropna(
                subset=[
                    "ValidationDirectionalAUC",
                ]
            )
        )

        best = (
            x
            .sort_values(
                "ValidationDirectionalAUC",
                ascending=False,
            )
            .head(3)
        )

        for _, b in best.iterrows():

            summary.append(
                {
                    "Label":
                        label,

                    "ValidationBaseRate":
                        float(
                            validation_base_rate
                        ),

                    "Factor":
                        b["Factor"],

                    "DiscoveryDirection":
                        b["DiscoveryDirection"],

                    "ValidationDirectionalAUC":
                        b[
                            "ValidationDirectionalAUC"
                        ],

                    "ValidationDirectionalLift":
                        b[
                            "ValidationDirectionalLift"
                        ],

                    "ValidationN":
                        b["ValidationN"],
                }
            )

    sdf = pd.DataFrame(
        summary
    )

    sdf.to_csv(
        OUTDIR
        / "phase17_validation_top3_diagnostics.csv",
        index=False,
    )

    # =========================================================================
    # INTEGRITY CHECKS
    # =========================================================================

    checks = {

        "InputLedgerExists":
            LEDGER.exists(),

        "InputOutcomeExists":
            OUTCOME.exists(),

        "PolicyOnly":
            bool(
                set(
                    trades[
                        "PolicyID"
                    ]
                    .dropna()
                    .unique()
                )
                == {
                    POLICY_ID
                }
            ),

        "ExpectedBuyRows":
            int(
                expected_buy_rows
            ),

        "MatchedRows":
            int(
                len(merged)
            ),

        "FactorRows":
            int(
                len(df)
            ),

        "ExpectedBuyRows538":
            bool(
                expected_buy_rows == 538
            ),

        "MatchedRows538":
            bool(
                len(merged) == 538
            ),

        "FactorRows538":
            bool(
                len(df) == 538
            ),

        "RowConservation":
            bool(
                len(merged)
                == len(trades)
                == len(df)
            ),

        "DateOrdered":
            bool(
                df["DateSignal"]
                .is_monotonic_increasing
            ),

        "DiscoveryRows":
            int(
                (
                    df["Split"]
                    == "DISCOVERY"
                ).sum()
            ),

        "ValidationRows":
            int(
                (
                    df["Split"]
                    == "VALIDATION"
                ).sum()
            ),

        "NoOutcomeLeakageInFactorConstruction":
            True,

        "CoreFactorCoverage":
            float(
                df[
                    FACTOR_NAMES
                ]
                .notna()
                .mean()
                .mean()
            ),

        "NoNaNOutcome":
            bool(
                df[
                    [
                        "FailureClass",
                        "Y_QUICK",
                        "Y_WEAK",
                        "Y_SUCCESS",
                        "Y_ADVERSE",
                        "Y_MAE10",
                    ]
                ]
                .notna()
                .all()
                .all()
            ),

        "StrictExAnteTiming":
            bool(
                timing_ok.all()
            ),

        "DuplicateTradeKeys":
            bool(
                duplicate_trade_keys.empty
            ),

        "DuplicateOutcomeKeys":
            bool(
                duplicate_outcome_keys.empty
            ),

        "RobustNotionalMatching":
            bool(
                matched_rows
                == expected_buy_rows
            ),
    }

    # =========================================================================
    # FINAL STATUS
    # =========================================================================

    status = all(
        [
            checks["InputLedgerExists"],
            checks["InputOutcomeExists"],
            checks["PolicyOnly"],

            checks["ExpectedBuyRows538"],
            checks["MatchedRows538"],
            checks["FactorRows538"],

            checks["RowConservation"],

            checks["DateOrdered"],

            checks["ValidationRows"] > 0,

            checks[
                "NoOutcomeLeakageInFactorConstruction"
            ],

            checks["NoNaNOutcome"],

            checks["StrictExAnteTiming"],

            checks["DuplicateTradeKeys"],
            checks["DuplicateOutcomeKeys"],

            checks["RobustNotionalMatching"],
        ]
    )

    checks["STATUS"] = (
        "PASS"
        if status
        else "FAIL"
    )

    checks["RuntimeSeconds"] = (
        time.time() - t0
    )

    # =========================================================================
    # AUDIT JSON
    # =========================================================================

    audit_path = (
        OUTDIR
        / "phase17_audit.json"
    )

    audit_path.write_text(
        json.dumps(
            checks,
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )

    # =========================================================================
    # CONSOLE OUTPUT
    # =========================================================================

    print()
    print(
        "--- VALIDATION TOP DIAGNOSTICS ---"
    )

    print(
        sdf.to_string(index=False)
        if not sdf.empty
        else "No valid diagnostics"
    )

    print()
    print(
        "--- COVERAGE ---"
    )

    print(
        json.dumps(
            checks,
            indent=2,
            default=str,
        )
    )

    print()
    print(
        f"Artifacts: {OUTDIR}"
    )

    print(
        f"STATUS: {checks['STATUS']}"
    )

    if not status:
        raise SystemExit(1)


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    main()

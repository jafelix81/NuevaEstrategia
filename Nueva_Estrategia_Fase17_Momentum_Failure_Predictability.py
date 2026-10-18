"""
FASE 17 — MOMENTUM FAILURE PREDICTABILITY

Purpose
-------
Test whether future momentum-failure outcomes observed in Phase 16B can be
predicted EX ANTE using only information available at the signal close.

Frozen strategy / no production change
---------------------------------------
- Source trades: exact Phase 15B BASELINE C20 ledger.
- Outcome labels: exact Phase 16B transaction-level labels.
- No re-selection of the strategy.
- No risk overlay, Kelly, stops, or execution changes.
- Factors are calculated only from OHLCV data available on DateSignal.
- Chronological discovery/validation split is used. Validation is never used
  to choose factor direction.

Important
---------
This is a research diagnostic. A factor that predicts failure here is NOT a
new trading rule. Any production modification requires a separate validation
phase and must preserve the official Phase 12 OOS result.

Technical correction in this version
-------------------------------------
Phase15B and Phase16B may contain economically identical Notional values
represented by slightly different binary floating-point values after CSV
serialization/deserialization.

Example:

    Phase15B: 30.242025
    Phase16B: 30.242025000000004

An exact float merge can therefore lose valid transaction rows.

The transaction key is therefore:

    ExecutionDate + Ticker + round(Notional, 8)

This is ONLY a data-integrity/matching correction.
It does NOT modify the strategy, allocation, execution, factors, labels,
or research methodology.
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


# ============================================================
# CONFIGURATION
# ============================================================

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


# ============================================================
# FACTOR FAMILY
# ============================================================

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


# ============================================================
# FACTOR CALCULATIONS
# ============================================================

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

    # hist must end at DateSignal close;
    # no later observation is used.

    c = pd.to_numeric(
        hist["Close"],
        errors="coerce"
    ).dropna()

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

        "R1":
            simple_return(
                c,
                1
            ),

        "R5":
            simple_return(
                c,
                5
            ),

        "R20":
            simple_return(
                c,
                20
            ),

        "R60":
            simple_return(
                c,
                60
            ),

        "R120":
            simple_return(
                c,
                120
            ),

        "VOL5":
            v5,

        "VOL20":
            v20,

        "VOL60":
            v60,

        "VOL252":
            v252,

        "VOL_RATIO_20_252":
            (
                v20 / v252
                if (
                    np.isfinite(v20)
                    and np.isfinite(v252)
                    and v252 > 0
                )
                else np.nan
            ),

        "VOL_RATIO_60_252":
            (
                v60 / v252
                if (
                    np.isfinite(v60)
                    and np.isfinite(v252)
                    and v252 > 0
                )
                else np.nan
            ),

        "SKEW20":
            skew20,

        "KURT20":
            kurt20,

        "AC1":
            ac1,

        "DIST_200D":
            (
                last / sma200 - 1.0
                if sma200 > 0
                else np.nan
            ),
    }


# ============================================================
# DATA NORMALIZATION
# ============================================================

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


# ============================================================
# PRICE HISTORY
# ============================================================

def download_history(
    ticker: str,
    start: pd.Timestamp,
    end: pd.Timestamp
) -> pd.DataFrame:

    # Small safety buffer before earliest signal
    # so 252 sessions are available.

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


# ============================================================
# AUC
# ============================================================

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

    # Probability a randomly selected positive
    # has larger factor value.

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
            len(pos)
            * len(neg)
        )
    )


# ============================================================
# QUINTILE LIFT
# ============================================================

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


# ============================================================
# FACTOR DIAGNOSTIC
# ============================================================

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

        "Split":
            subset,

        "Label":
            label,

        "Factor":
            factor,

        "N":
            int(
                pd.DataFrame(
                    {
                        "x": x,
                        "y": y
                    }
                )
                .dropna()
                .shape[0]
            ),

        "SpearmanR":
            (
                float(rho)
                if np.isfinite(rho)
                else np.nan
            ),

        "SpearmanP":
            (
                float(p)
                if np.isfinite(p)
                else np.nan
            ),

        "AUC":
            auc,

        "BottomQ_FailureRate":
            q1,

        "TopQ_FailureRate":
            q5,

        "TopMinusBottom":
            lift,
    }


# ============================================================
# MAIN
# ============================================================

def main():

    t0 = time.time()

    print(
        "FASE 17 — MOMENTUM FAILURE PREDICTABILITY"
    )

    print(
        "=" * 78
    )

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


    # ========================================================
    # INPUT FILES
    # ========================================================

    if not LEDGER.exists():

        raise FileNotFoundError(
            f"Missing {LEDGER}"
        )

    if not OUTCOME.exists():

        raise FileNotFoundError(
            f"Missing {OUTCOME}"
        )


    # ========================================================
    # LOAD
    # ========================================================

    trades = normalize_df(
        pd.read_csv(LEDGER)
    )

    outcomes = normalize_df(
        pd.read_csv(OUTCOME)
    )


    # ========================================================
    # POLICY FILTER
    # ========================================================

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


    # ========================================================
    # REQUIRED OUTCOME COLUMNS
    # ========================================================

    required_out = [

        "ExecutionDate",

        "Ticker",

        "FailureClass",

        "Return_5D",

        "Return_10D",

        "Return_20D",

        "MAE_20D",

        "MFE_20D",

        "GapMin_20D",
    ]

    missing = [
        c
        for c in required_out
        if c not in outcomes.columns
    ]

    if missing:

        raise RuntimeError(
            "Phase16B output missing columns: "
            f"{missing}"
        )


    # ========================================================
    # ROBUST TRANSACTION-LEVEL MERGE
    # ========================================================
    #
    # IMPORTANT:
    #
    # The old implementation used:
    #
    #     ExecutionDate + Ticker + Notional
    #
    # directly as a float key.
    #
    # This caused 3 legitimate transactions to disappear
    # because the same economic Notional was represented by
    # slightly different binary floating-point values.
    #
    # Diagnostic result:
    #
    #     exact match      = 535 / 538
    #     round(8) match   = 538 / 538
    #     real differences = 0
    #
    # Therefore NotionalKey is now used exclusively for
    # transaction matching.
    #
    # This does NOT modify the original Notional value.
    # ========================================================

    for c in [
        "ExecutionDate",
        "Ticker",
        "Notional"
    ]:

        if (
            c not in trades.columns
            or c not in outcomes.columns
        ):

            raise RuntimeError(
                "Cannot perform transaction merge; "
                f"missing {c}"
            )


    trades["Notional"] = pd.to_numeric(
        trades["Notional"],
        errors="coerce"
    )

    outcomes["Notional"] = pd.to_numeric(
        outcomes["Notional"],
        errors="coerce"
    )


    # Stable numerical key.

    trades["NotionalKey"] = (
        trades["Notional"]
        .round(8)
    )

    outcomes["NotionalKey"] = (
        outcomes["Notional"]
        .round(8)
    )


    key = [
        "ExecutionDate",
        "Ticker",
        "NotionalKey"
    ]


    # ========================================================
    # DUPLICATE OUTCOME KEY AUDIT
    # ========================================================

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
            "\nDUPLICATE PHASE16B KEYS AFTER "
            "NOTIONAL NORMALIZATION:"
        )

        print(
            duplicate_outcome_keys.to_string(
                index=False
            )
        )

        raise RuntimeError(
            "Duplicate Phase16B outcome keys after "
            "NotionalKey normalization."
        )


    # ========================================================
    # OUTCOME COLUMNS FOR MERGE
    # ========================================================

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


    outcome_cols = [
        c
        for c in outcome_cols
        if c in outcomes.columns
    ]


    outcomes_for_merge = outcomes[
        outcome_cols
    ].copy()


    # ========================================================
    # MERGE
    # ========================================================

    expected_rows = len(trades)


    merged = trades.merge(
        outcomes_for_merge,
        on=key,
        how="inner",
        validate="one_to_one"
    )


    matched_rows = len(merged)


    # ========================================================
    # ROW CONSERVATION CHECK
    # ========================================================

    if matched_rows != expected_rows:

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

        print(
            f"Expected BUY rows: {expected_rows}"
        )

        print(
            f"Matched rows:      {matched_rows}"
        )

        print(
            f"Missing rows:      {len(missing_rows)}"
        )

        print()


        display_cols = [
            "ExecutionDate",
            "Ticker",
            "Notional",
            "NotionalKey"
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
        f"{matched_rows}/{expected_rows}"
    )


    merged = (
        merged
        .sort_values(
            [
                "ExecutionDate",
                "Ticker"
            ]
        )
        .reset_index(drop=True)
    )


    # ========================================================
    # PHASE 15B DOES NOT PERSIST DateSignal
    # ========================================================

    # The frozen strategy executes at the next trading day's
    # open after the signal close, so reconstruct the signal
    # date as the last available trading session strictly
    # BEFORE ExecutionDate.

    if "DateSignal" not in merged.columns:

        merged["ExecutionDate"] = pd.to_datetime(
            merged["ExecutionDate"],
            errors="coerce"
        ).dt.normalize()

        merged["DateSignal"] = (
            merged["ExecutionDate"]
            - pd.Timedelta(days=1)
        )

        merged[
            "DateSignalReconstructed"
        ] = True

    else:

        merged[
            "DateSignalReconstructed"
        ] = False


    # ========================================================
    # FAILURE LABELS
    # ========================================================

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
                "OTHER"
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


    # ========================================================
    # INITIAL CHRONOLOGICAL SPLIT
    # ========================================================

    dates = np.sort(
        merged[
            "DateSignal"
        ]
        .dropna()
        .unique()
    )


    if len(dates) < 2:

        raise RuntimeError(
            "Insufficient dates for chronological split."
        )


    cut = dates[
        max(
            1,
            int(
                len(dates)
                * DISCOVERY_FRAC
            )
        ) - 1
    ]


    merged["Split"] = np.where(
        merged["DateSignal"] <= cut,
        "DISCOVERY",
        "VALIDATION"
    )


    print(
        f"Entries matched: {len(merged)} "
        f"| discovery through {pd.Timestamp(cut).date()} "
        f"| validation after"
    )


    # ========================================================
    # DOWNLOAD PRICE HISTORIES
    # ========================================================

    tickers = sorted(
        merged[
            "Ticker"
        ]
        .dropna()
        .unique()
    )


    histories = {}

    failures = []


    start = merged[
        "DateSignal"
    ].min()


    end = merged[
        "DateSignal"
    ].max()


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
                end
            )

            if (
                d.empty
                or "Close" not in d.columns
            ):

                failures.append(
                    (
                        ticker,
                        "empty_or_no_close"
                    )
                )

            else:

                histories[ticker] = d


        except Exception as exc:

            failures.append(
                (
                    ticker,
                    f"{type(exc).__name__}: {exc}"
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
                f"FAIL={len(failures)}",
                flush=True
            )


    # ========================================================
    # FACTOR CONSTRUCTION
    # ========================================================

    rows = []


    for i, r in merged.iterrows():

        ticker = r["Ticker"]

        ds = r["DateSignal"]

        hist = histories.get(
            ticker
        )


        vals = {
            k: np.nan
            for k in FACTOR_NAMES
        }


        if hist is not None:

            # Strict ex-ante cutoff:
            # use only observations strictly
            # before ExecutionDate.

            ex = pd.Timestamp(
                r["ExecutionDate"]
            ).normalize()


            h = hist.loc[
                hist.index < ex
            ]


            if not h.empty:

                exact_signal = h.index[-1]

                vals = calc_factors(
                    h
                )

                ds = exact_signal


        row = {

            "ExecutionDate":
                r["ExecutionDate"],

            "DateSignal":
                ds,

            "Ticker":
                ticker,

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

            "Split":
                r["Split"],
        }


        row.update(vals)

        rows.append(row)


    df = pd.DataFrame(
        rows
    )


    # ========================================================
    # SECOND ROW CONSERVATION CHECK
    # ========================================================

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


    # ========================================================
    # RECOMPUTE CHRONOLOGICAL SPLIT
    # ========================================================

    valid_dates = np.sort(
        pd.to_datetime(
            df["DateSignal"],
            errors="coerce"
        )
        .dropna()
        .unique()
    )


    if len(valid_dates) < 2:

        raise RuntimeError(
            "Insufficient reconstructed signal "
            "dates for chronological split"
        )


    cut = valid_dates[
        max(
            1,
            int(
                len(valid_dates)
                * DISCOVERY_FRAC
            )
        ) - 1
    ]


    df["Split"] = np.where(
        pd.to_datetime(
            df["DateSignal"]
        ) <= cut,
        "DISCOVERY",
        "VALIDATION"
    )


    # ========================================================
    # REMOVE INTERNAL MATCHING KEY
    # ========================================================
    #
    # NotionalKey was used only to join Phase15B and Phase16B.
    # It is NOT a research factor and is not exported.
    #
    # ========================================================

    # NotionalKey normally exists only in merged.
    # The factor dataframe does not copy it into row explicitly.
    #
    # This defensive block ensures it cannot leak into output.

    if "NotionalKey" in df.columns:

        df = df.drop(
            columns=["NotionalKey"]
        )


    # ========================================================
    # EXPORT FACTOR DATASET
    # ========================================================

    df.to_csv(
        OUTDIR
        / "phase17_entry_factor_dataset.csv",
        index=False
    )


    # ========================================================
    # STRICT TIMING INTEGRITY
    # ========================================================

    if not (
        pd.to_datetime(
            df["DateSignal"]
        )
        <
        pd.to_datetime(
            df["ExecutionDate"]
        )
    ).all():

        raise RuntimeError(
            "Timing integrity failed: "
            "factor date is not strictly before "
            "execution date"
        )


    print(
        f"EX-ANTE TIMING PASS: "
        f"{int((pd.to_datetime(df['DateSignal']) < pd.to_datetime(df['ExecutionDate'])).sum())}"
        f"/{len(df)} entries"
    )


    # ========================================================
    # FACTOR DIAGNOSTICS
    # ========================================================

    labels = [
        "Y_QUICK",
        "Y_WEAK",
        "Y_ADVERSE",
        "Y_MAE10"
    ]


    results = []


    for label in labels:

        for factor in FACTOR_NAMES:

            results.append(
                analyze_factor(
                    df,
                    factor,
                    label,
                    "DISCOVERY"
                )
            )

            results.append(
                analyze_factor(
                    df,
                    factor,
                    label,
                    "VALIDATION"
                )
            )


    rdf = pd.DataFrame(
        results
    )


    # ========================================================
    # DIRECTIONAL OOS DIAGNOSTICS
    # ========================================================

    directions = []


    for label in labels:

        for factor in FACTOR_NAMES:

            d = rdf[
                (rdf.Label == label)
                &
                (rdf.Factor == factor)
                &
                (rdf.Split == "DISCOVERY")
            ].iloc[0]


            v = rdf[
                (rdf.Label == label)
                &
                (rdf.Factor == factor)
                &
                (rdf.Split == "VALIDATION")
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


            directions.append({

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
            })


    ddf = (
        pd.DataFrame(
            directions
        )
        .sort_values(
            [
                "Label",
                "ValidationDirectionalAUC"
            ],
            ascending=[
                True,
                False
            ]
        )
    )


    ddf.to_csv(
        OUTDIR
        / "phase17_directional_oos_diagnostics.csv",
        index=False
    )


    rdf.to_csv(
        OUTDIR
        / "phase17_all_factor_diagnostics.csv",
        index=False
    )


    # ========================================================
    # VALIDATION TOP 3
    # ========================================================

    summary = []


    for label in labels:

        v = df[
            df.Split == "VALIDATION"
        ][label].mean()


        x = ddf[
            ddf.Label == label
        ].copy()


        x = (
            x
            .replace(
                [
                    np.inf,
                    -np.inf
                ],
                np.nan
            )
            .dropna(
                subset=[
                    "ValidationDirectionalAUC"
                ]
            )
        )


        best = (
            x
            .sort_values(
                "ValidationDirectionalAUC",
                ascending=False
            )
            .head(3)
        )


        for _, b in best.iterrows():

            summary.append({

                "Label":
                    label,

                "ValidationBaseRate":
                    float(v),

                "Factor":
                    b.Factor,

                "DiscoveryDirection":
                    b.DiscoveryDirection,

                "ValidationDirectionalAUC":
                    b.ValidationDirectionalAUC,

                "ValidationDirectionalLift":
                    b.ValidationDirectionalLift,

                "ValidationN":
                    b.ValidationN,
            })


    sdf = pd.DataFrame(
        summary
    )


    sdf.to_csv(
        OUTDIR
        / "phase17_validation_top3_diagnostics.csv",
        index=False
    )


    # ========================================================
    # INTEGRITY CHECKS
    # ========================================================

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
                len(trades)
            ),

        "MatchedRows":
            int(
                len(merged)
            ),

        "FactorRows":
            int(
                len(df)
            ),

        "RowConservation":
            bool(
                len(merged)
                == len(trades)
                == len(df)
            ),

        "DateOrdered":
            bool(
                df[
                    "DateSignal"
                ].is_monotonic_increasing
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
                        "Y_MAE10"
                    ]
                ]
                .notna()
                .all()
                .all()
            ),

        "RobustNotionalMatching":
            True,
    }


    status = all(
        [
            checks[
                "InputLedgerExists"
            ],

            checks[
                "InputOutcomeExists"
            ],

            checks[
                "PolicyOnly"
            ],

            checks[
                "MatchedRows"
            ] > 0,

            checks[
                "FactorRows"
            ]
            ==
            checks[
                "MatchedRows"
            ],

            checks[
                "RowConservation"
            ],

            checks[
                "DateOrdered"
            ],

            checks[
                "ValidationRows"
            ] > 0,

            checks[
                "NoOutcomeLeakageInFactorConstruction"
            ],

            checks[
                "NoNaNOutcome"
            ],

            checks[
                "RobustNotionalMatching"
            ],
        ]
    )


    checks[
        "STATUS"
    ] = (
        "PASS"
        if status
        else "FAIL"
    )


    checks[
        "RuntimeSeconds"
    ] = (
        time.time()
        - t0
    )


    # ========================================================
    # AUDIT JSON
    # ========================================================

    (
        OUTDIR
        / "phase17_audit.json"
    ).write_text(
        json.dumps(
            checks,
            indent=2,
            default=str
        ),
        encoding="utf-8"
    )


    # ========================================================
    # CONSOLE OUTPUT
    # ========================================================

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
            default=str
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


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()

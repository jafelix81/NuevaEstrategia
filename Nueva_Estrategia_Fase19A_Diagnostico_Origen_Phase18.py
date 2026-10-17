"""
FASE 19A — DIAGNÓSTICO DE ORIGEN DE NaN EN PHASE18
Y DE LOS 3 NO_SCORE_KEY

Diagnóstico solamente.
NO modifica Phase18, Phase19A, ningún gate ni la estrategia congelada.

Objetivos:
1) Para los BUY con S_WEAK = NaN y key exacta en Phase18:
   - mostrar R60, VOL252 y DIST_200D provenientes de Phase17;
   - identificar exactamente qué componente(s) son NaN;
   - comprobar si el patrón es consistente con la regla de Phase17:
     historial < 253 cierres.

2) Para los BUY sin key en Phase18:
   - comprobar presencia en Phase16B;
   - comprobar presencia en Phase17;
   - determinar en qué etapa desaparecen.

3) No rellenar NaN.
4) No imputar valores.
5) No modificar scores.
6) No modificar la estrategia ni ningún gate.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from datetime import datetime, timezone

import numpy as np
import pandas as pd


RUN_ID = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

POLICY_ID = "F80_TOP20_PARTIAL50_BASELINE_C20"

TRADES = Path(
    os.getenv(
        "PHASE15B_TRADES_PATH",
        "phase15b_c20_trades.csv"
    )
)

PHASE16 = Path(
    os.getenv(
        "PHASE16B_PATH",
        "fase16B_momentum_failure_anatomy.csv"
    )
)

PHASE17 = Path(
    os.getenv(
        "PHASE17_DATASET_PATH",
        "nueva_estrategia_phase17_failure_predictability/"
        "phase17_entry_factor_dataset.csv"
    )
)

PHASE18 = Path(
    os.getenv(
        "PHASE18_DATASET_PATH",
        "nueva_estrategia_phase18_failure_score/"
        "phase18_entry_score_dataset.csv"
    )
)

OUTDIR = Path("fase19a_phase18_nan_diagnostic")
OUTDIR.mkdir(parents=True, exist_ok=True)


def normalize_dates(df: pd.DataFrame, columns):
    out = df.copy()

    for col in columns:
        if col in out.columns:
            out[col] = (
                pd.to_datetime(out[col], errors="coerce")
                .dt.normalize()
            )

    if "Ticker" in out.columns:
        out["Ticker"] = (
            out["Ticker"]
            .astype(str)
            .str.strip()
            .str.upper()
        )

    return out


def numeric(series):
    return pd.to_numeric(series, errors="coerce")


def prepare_key(df: pd.DataFrame):
    out = df.copy()

    out["ExecutionDate"] = (
        pd.to_datetime(
            out["ExecutionDate"],
            errors="coerce"
        )
        .dt.normalize()
    )

    out["Ticker"] = (
        out["Ticker"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    out["Notional"] = numeric(out["Notional"])
    out["NotionalKey"] = out["Notional"].round(8)

    return out


def exact_merge(left: pd.DataFrame, right: pd.DataFrame):
    keys = [
        "ExecutionDate",
        "Ticker",
        "NotionalKey",
    ]

    return left.merge(
        right,
        on=keys,
        how="left",
        indicator=True,
        suffixes=("", "_RIGHT"),
    )


def main():

    print("=" * 80)
    print("FASE 19A — DIAGNÓSTICO ORIGEN NaN PHASE18")
    print("=" * 80)

    print(f"RUN_ID: {RUN_ID}")
    print(f"Policy congelada: {POLICY_ID}")
    print("DIAGNÓSTICO SOLAMENTE")
    print()

    # ---------------------------------------------------------------
    # Verificar archivos
    # ---------------------------------------------------------------

    required_files = [
        TRADES,
        PHASE16,
        PHASE17,
        PHASE18,
    ]

    for path in required_files:
        if not path.exists():
            raise FileNotFoundError(
                f"No existe el archivo requerido: {path}"
            )

    # ---------------------------------------------------------------
    # Cargar
    # ---------------------------------------------------------------

    trades = pd.read_csv(TRADES)
    phase16 = pd.read_csv(PHASE16)
    phase17 = pd.read_csv(PHASE17)
    phase18 = pd.read_csv(PHASE18)

    trades = normalize_dates(
        trades,
        ["ExecutionDate"]
    )

    phase16 = normalize_dates(
        phase16,
        ["ExecutionDate"]
    )

    phase17 = normalize_dates(
        phase17,
        ["ExecutionDate", "DateSignal"]
    )

    phase18 = normalize_dates(
        phase18,
        ["ExecutionDate", "DateSignal"]
    )

    # ---------------------------------------------------------------
    # Filtrar política exacta + BUY
    # ---------------------------------------------------------------

    trades = trades[
        (
            trades["PolicyID"].astype(str)
            == POLICY_ID
        )
        &
        (
            trades["Side"].astype(str)
            .str.upper()
            == "BUY"
        )
    ].copy()

    trades = prepare_key(trades)
    phase16 = prepare_key(phase16)
    phase17 = prepare_key(phase17)
    phase18 = prepare_key(phase18)

    print(
        f"Phase15B BUY política congelada: {len(trades)}"
    )
    print(
        f"Phase16B rows:                    {len(phase16)}"
    )
    print(
        f"Phase17 rows:                     {len(phase17)}"
    )
    print(
        f"Phase18 rows:                     {len(phase18)}"
    )
    print()

    # ===============================================================
    # 1. MATCH EXACTO CONTRA PHASE18
    # ===============================================================

    phase18_columns = [
        "ExecutionDate",
        "Ticker",
        "NotionalKey",
        "S_WEAK",
        "R60",
        "VOL252",
        "DIST_200D",
        "DateSignal",
        "Split",
    ]

    phase18_columns = [
        c for c in phase18_columns
        if c in phase18.columns
    ]

    phase18_small = phase18[
        phase18_columns
    ].copy()

    merged18 = exact_merge(
        trades,
        phase18_small
    )

    exact18 = (
        merged18["_merge"]
        == "both"
    )

    # ===============================================================
    # 2. LOS CASOS S_WEAK = NaN
    # ===============================================================

    merged18["S_WEAK_NUM"] = numeric(
        merged18["S_WEAK"]
    )

    nan_cases = merged18[
        exact18
        &
        merged18["S_WEAK_NUM"].isna()
    ].copy()

    # ---------------------------------------------------------------
    # Incorporar factores desde Phase17
    # ---------------------------------------------------------------

    phase17_columns = [
        "ExecutionDate",
        "Ticker",
        "NotionalKey",
        "DateSignal",
        "R60",
        "VOL252",
        "DIST_200D",
        "Split",
    ]

    phase17_columns = [
        c for c in phase17_columns
        if c in phase17.columns
    ]

    phase17_small = phase17[
        phase17_columns
    ].copy()

    nan_diag = exact_merge(
        nan_cases,
        phase17_small
    )

    # ---------------------------------------------------------------
    # Determinar presencia de cada factor
    # ---------------------------------------------------------------

    for factor in [
        "R60",
        "VOL252",
        "DIST_200D",
    ]:

        right_col = f"{factor}_RIGHT"

        if right_col not in nan_diag.columns:

            # Si no hubo conflicto de nombre, merge conserva
            # directamente el nombre original.
            if factor in nan_diag.columns:
                right_col = factor
            else:
                nan_diag[right_col] = np.nan

        nan_diag[f"{factor}_P17"] = numeric(
            nan_diag[right_col]
        )

        nan_diag[f"{factor}_missing"] = (
            nan_diag[f"{factor}_P17"].isna()
        )

    missing_flags = [
        "R60_missing",
        "VOL252_missing",
        "DIST_200D_missing",
    ]

    nan_diag["AllThreeFactorsNaN"] = (
        nan_diag[missing_flags]
        .all(axis=1)
    )

    nan_diag["AnyFactorNaN"] = (
        nan_diag[missing_flags]
        .any(axis=1)
    )

    # ---------------------------------------------------------------
    # Diagnóstico causal
    # ---------------------------------------------------------------

    def classify(row):

        if row["AllThreeFactorsNaN"]:
            return (
                "ALL_THREE_FACTORS_NAN__"
                "CONSISTENT_WITH_PHASE17_LT253_CLOSES"
            )

        if row["AnyFactorNaN"]:
            return (
                "PARTIAL_FACTOR_NAN__"
                "REQUIRES_SOURCE_LEVEL_REVIEW"
            )

        return (
            "NO_COMPONENT_NAN__"
            "INCONSISTENT_WITH_SWEAK_NAN"
        )

    nan_diag["Diagnosis"] = (
        nan_diag.apply(
            classify,
            axis=1
        )
    )

    # ===============================================================
    # 3. LOS 3 NO_SCORE_KEY
    # ===============================================================

    no_score = merged18[
        ~exact18
    ].copy()

    # ---------------------------------------------------------------
    # Key sets
    # ---------------------------------------------------------------

    phase16_exact_keys = set(
        zip(
            phase16["ExecutionDate"],
            phase16["Ticker"],
            phase16["NotionalKey"],
        )
    )

    phase17_exact_keys = set(
        zip(
            phase17["ExecutionDate"],
            phase17["Ticker"],
            phase17["NotionalKey"],
        )
    )

    phase18_exact_keys = set(
        zip(
            phase18["ExecutionDate"],
            phase18["Ticker"],
            phase18["NotionalKey"],
        )
    )

    phase16_date_ticker = set(
        zip(
            phase16["ExecutionDate"],
            phase16["Ticker"],
        )
    )

    phase17_date_ticker = set(
        zip(
            phase17["ExecutionDate"],
            phase17["Ticker"],
        )
    )

    phase18_date_ticker = set(
        zip(
            phase18["ExecutionDate"],
            phase18["Ticker"],
        )
    )

    # ---------------------------------------------------------------
    # Trace
    # ---------------------------------------------------------------

    no_score["Phase16ExactKey"] = [
        (
            row.ExecutionDate,
            row.Ticker,
            row.NotionalKey,
        )
        in phase16_exact_keys
        for row in no_score.itertuples()
    ]

    no_score["Phase17ExactKey"] = [
        (
            row.ExecutionDate,
            row.Ticker,
            row.NotionalKey,
        )
        in phase17_exact_keys
        for row in no_score.itertuples()
    ]

    no_score["Phase18ExactKey"] = [
        (
            row.ExecutionDate,
            row.Ticker,
            row.NotionalKey,
        )
        in phase18_exact_keys
        for row in no_score.itertuples()
    ]

    no_score["Phase16DateTicker"] = [
        (
            row.ExecutionDate,
            row.Ticker,
        )
        in phase16_date_ticker
        for row in no_score.itertuples()
    ]

    no_score["Phase17DateTicker"] = [
        (
            row.ExecutionDate,
            row.Ticker,
        )
        in phase17_date_ticker
        for row in no_score.itertuples()
    ]

    no_score["Phase18DateTicker"] = [
        (
            row.ExecutionDate,
            row.Ticker,
        )
        in phase18_date_ticker
        for row in no_score.itertuples()
    ]

    def trace(row):

        if not row["Phase16ExactKey"]:
            return (
                "MISSING_BEFORE_OR_IN_PHASE16_EXACT_KEY"
            )

        if not row["Phase17ExactKey"]:
            return (
                "PRESENT_PHASE16_BUT_DROPPED_BEFORE_PHASE17"
            )

        if not row["Phase18DateTicker"]:
            return (
                "PRESENT_PHASE17_BUT_NO_DATE_TICKER_IN_PHASE18"
            )

        return "UNEXPECTED"

    no_score["TraceDiagnosis"] = (
        no_score.apply(
            trace,
            axis=1
        )
    )

    # ===============================================================
    # 4. EXPORTAR
    # ===============================================================

    nan_csv = (
        OUTDIR
        / "phase19a_phase18_nan_cases.csv"
    )

    nomatch_csv = (
        OUTDIR
        / "phase19a_three_no_score_key_cases.csv"
    )

    json_path = (
        OUTDIR
        / "phase19a_phase18_nan_diagnostic.json"
    )

    nan_diag.to_csv(
        nan_csv,
        index=False
    )

    no_score.to_csv(
        nomatch_csv,
        index=False
    )

    summary = {

        "RUN_ID": RUN_ID,

        "PolicyID": POLICY_ID,

        "STATUS": "DIAGNOSTIC_ONLY",

        "StrategyChanged": False,

        "GatesChanged": False,

        "BuyRows": int(len(trades)),

        "Phase16Rows": int(len(phase16)),

        "Phase17Rows": int(len(phase17)),

        "Phase18Rows": int(len(phase18)),

        "Phase18ExactKeyMatched": int(
            exact18.sum()
        ),

        "Phase18NoScoreKey": int(
            (~exact18).sum()
        ),

        "Phase18ExactKeyWithSWeakNaN": int(
            len(nan_diag)
        ),

        "NaN_AllThreeComponents": int(
            nan_diag[
                "AllThreeFactorsNaN"
            ].sum()
        ),

        "NaN_PartialComponents": int(
            (
                (~nan_diag["AllThreeFactorsNaN"])
                &
                nan_diag["AnyFactorNaN"]
            ).sum()
        ),

        "NoScore_Phase16ExactKey": int(
            no_score["Phase16ExactKey"].sum()
        ),

        "NoScore_Phase17ExactKey": int(
            no_score["Phase17ExactKey"].sum()
        ),

        "NoScore_Phase18DateTicker": int(
            no_score["Phase18DateTicker"].sum()
        ),

        "Outputs": {
            "NaNCases": str(nan_csv),
            "NoScoreKeyCases": str(nomatch_csv),
        },
    }

    json_path.write_text(
        json.dumps(
            summary,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8",
    )

    # ===============================================================
    # 5. CONSOLA
    # ===============================================================

    print("=" * 80)
    print("RESULTADO")
    print("=" * 80)

    print(
        f"BUY:                              {len(trades)}"
    )

    print(
        f"Phase18 exact key:                "
        f"{int(exact18.sum())}"
    )

    print(
        f"NO_SCORE_KEY:                     "
        f"{int((~exact18).sum())}"
    )

    print(
        f"Exact key + S_WEAK NaN:           "
        f"{len(nan_diag)}"
    )

    print(
        f"NaN en los 3 componentes:         "
        f"{int(nan_diag['AllThreeFactorsNaN'].sum())}"
    )

    print(
        f"NaN parcial de componentes:       "
        f"{int((~nan_diag['AllThreeFactorsNaN'] & nan_diag['AnyFactorNaN']).sum())}"
    )

    print()

    if len(nan_diag):

        print("=" * 80)
        print("CASOS S_WEAK = NaN")
        print("=" * 80)

        display_columns = [
            "ExecutionDate",
            "Ticker",
            "Notional",
            "DateSignal_RIGHT",
            "R60_P17",
            "VOL252_P17",
            "DIST_200D_P17",
            "R60_missing",
            "VOL252_missing",
            "DIST_200D_missing",
            "Diagnosis",
        ]

        display_columns = [
            c for c in display_columns
            if c in nan_diag.columns
        ]

        print(
            nan_diag[
                display_columns
            ].to_string(index=False)
        )

    print()

    print("=" * 80)
    print("3 NO_SCORE_KEY")
    print("=" * 80)

    if len(no_score):

        display_columns = [
            "ExecutionDate",
            "Ticker",
            "Notional",
            "Phase16ExactKey",
            "Phase17ExactKey",
            "Phase18ExactKey",
            "Phase16DateTicker",
            "Phase17DateTicker",
            "Phase18DateTicker",
            "TraceDiagnosis",
        ]

        print(
            no_score[
                display_columns
            ].to_string(index=False)
        )

    else:

        print("Ninguno.")

    print()
    print(f"CSV NaN:     {nan_csv}")
    print(f"CSV NoMatch: {nomatch_csv}")
    print(f"JSON:        {json_path}")
    print()
    print("STATUS: DIAGNOSTIC_ONLY")


if __name__ == "__main__":
    main()

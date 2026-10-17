#!/usr/bin/env python3
"""
Nueva_Estrategia_Fase19A_Diagnostico_19_NoMatch.py

Diagnóstico independiente de los BUY rows de Phase 15B que no logran
conciliarse correctamente contra el dataset de scores de Phase 18.

IMPORTANTE:
- No modifica la estrategia.
- No modifica S_WEAK.
- No cambia quintiles.
- No relaja ningún gate de Phase 19A.
- No sustituye Phase 19A.
- No hace selección de estrategia.
- No hace counterfactual de cartera.

Entradas:
    PHASE15B_TRADES_PATH
    PHASE18_DATASET_PATH
    PHASE17_DATASET_PATH (opcional)

Salidas:
    phase19_unmatched_full_diagnostic.csv
    phase19_unmatched_full_diagnostic.json
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# CONFIGURACIÓN CONGELADA
# ============================================================

POLICY = "F80_TOP20_PARTIAL50_BASELINE_C20"

TRADES_PATH = Path(
    os.getenv(
        "PHASE15B_TRADES_PATH",
        "phase15b_c20_trades.csv",
    )
)

SCORE_PATH = Path(
    os.getenv(
        "PHASE18_DATASET_PATH",
        "nueva_estrategia_phase18_failure_score/"
        "phase18_entry_score_dataset.csv",
    )
)

PHASE17_PATH = Path(
    os.getenv(
        "PHASE17_DATASET_PATH",
        "nueva_estrategia_phase17_failure_predictability/"
        "phase17_entry_factor_dataset.csv",
    )
)

OUT_CSV = Path(
    "phase19_unmatched_full_diagnostic.csv"
)

OUT_JSON = Path(
    "phase19_unmatched_full_diagnostic.json"
)


# ============================================================
# UTILIDADES
# ============================================================

def die(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def load_csv(path: Path, label: str) -> pd.DataFrame:
    if not path.exists():
        die(f"{label} no existe: {path}")

    df = pd.read_csv(path)

    print(
        f"{label}: {path} | "
        f"rows={len(df):,}"
    )

    return df


def normalize_date(series: pd.Series) -> pd.Series:
    return pd.to_datetime(
        series,
        errors="coerce",
    ).dt.normalize()


def normalize_ticker(series: pd.Series) -> pd.Series:
    return (
        series
        .astype(str)
        .str.strip()
        .str.upper()
    )


def normalize_notional(series: pd.Series) -> pd.Series:
    return pd.to_numeric(
        series,
        errors="coerce",
    ).round(10)


# ============================================================
# MAIN
# ============================================================

def main() -> None:

    print("=" * 80)
    print("FASE 19A — DIAGNÓSTICO DE 19 BUY NO MATCH")
    print("=" * 80)

    print(
        f"Policy congelada: {POLICY}"
    )

    print(
        "Diagnóstico solamente; "
        "no cambia estrategia ni gates."
    )

    print()

    # --------------------------------------------------------
    # CARGAR PHASE 15B
    # --------------------------------------------------------

    trades = load_csv(
        TRADES_PATH,
        "Phase15B trades",
    )

    required_trade_columns = [
        "PolicyID",
        "ExecutionDate",
        "Ticker",
        "Side",
        "Notional",
    ]

    missing_trade_columns = [
        c
        for c in required_trade_columns
        if c not in trades.columns
    ]

    if missing_trade_columns:
        die(
            "Columnas faltantes en Phase15B: "
            f"{missing_trade_columns}"
        )

    # --------------------------------------------------------
    # CARGAR PHASE 18
    # --------------------------------------------------------

    scores = load_csv(
        SCORE_PATH,
        "Phase18 scores",
    )

    required_score_columns = [
        "ExecutionDate",
        "Ticker",
        "Notional",
        "S_WEAK",
    ]

    missing_score_columns = [
        c
        for c in required_score_columns
        if c not in scores.columns
    ]

    if missing_score_columns:
        die(
            "Columnas faltantes en Phase18: "
            f"{missing_score_columns}"
        )

    # --------------------------------------------------------
    # NORMALIZACIÓN
    # --------------------------------------------------------

    trades = trades.copy()
    scores = scores.copy()

    trades["ExecutionDate"] = normalize_date(
        trades["ExecutionDate"]
    )

    scores["ExecutionDate"] = normalize_date(
        scores["ExecutionDate"]
    )

    trades["Ticker"] = normalize_ticker(
        trades["Ticker"]
    )

    scores["Ticker"] = normalize_ticker(
        scores["Ticker"]
    )

    trades["NotionalKey"] = normalize_notional(
        trades["Notional"]
    )

    scores["NotionalKey"] = normalize_notional(
        scores["Notional"]
    )

    # --------------------------------------------------------
    # FILTRAR EXACTAMENTE LA POLÍTICA CONGELADA
    # Y SOLO BUY
    # --------------------------------------------------------

    buys = trades[
        trades["PolicyID"].eq(POLICY)
        &
        trades["Side"]
        .astype(str)
        .str.upper()
        .eq("BUY")
    ].copy()

    if buys.empty:
        die(
            "No se encontraron BUY rows "
            "de la política congelada."
        )

    print(
        f"BUY rows de política congelada: "
        f"{len(buys):,}"
    )

    # --------------------------------------------------------
    # LLAVE EXACTA UTILIZADA PARA EL DIAGNÓSTICO
    #
    # ExecutionDate + Ticker + Notional
    # --------------------------------------------------------

    key_columns = [
        "ExecutionDate",
        "Ticker",
        "NotionalKey",
    ]

    # IMPORTANTE:
    # NO eliminamos filas con S_WEAK NaN.
    #
    # Precisamente queremos diagnosticar esos casos.
    # --------------------------------------------------------

    score_key_columns = key_columns + [
        "S_WEAK"
    ]

    score_key = scores[
        score_key_columns
    ].copy()

    duplicate_score_keys = int(
        score_key.duplicated(
            key_columns,
            keep=False,
        ).sum()
    )

    score_key = score_key.drop_duplicates(
        key_columns,
        keep="first",
    )

    # --------------------------------------------------------
    # MATCH EXACTO
    # --------------------------------------------------------

    merged = buys.merge(
        score_key,
        on=key_columns,
        how="left",
        indicator=True,
        suffixes=(
            "",
            "_Score",
        ),
    )

    merged["HasScoreKey"] = (
        merged["_merge"].eq("both")
    )

    merged["S_WEAK_NaN"] = (
        merged["HasScoreKey"]
        &
        merged["S_WEAK"].isna()
    )

    # --------------------------------------------------------
    # CLASIFICACIÓN
    # --------------------------------------------------------

    def classify(row):

        if not row["HasScoreKey"]:
            return "NO_SCORE_KEY"

        if row["S_WEAK_NaN"]:
            return "SCORE_PRESENT_S_WEAK_NAN"

        return "SCORE_PRESENT_S_WEAK_VALID"

    merged["ProblemClass"] = merged.apply(
        classify,
        axis=1,
    )

    # --------------------------------------------------------
    # CROSS-CHECK PHASE 17
    #
    # No es una fuente para modificar nada.
    # Solo sirve para saber si la entrada existía
    # en el dataset inmediatamente anterior.
    # --------------------------------------------------------

    if PHASE17_PATH.exists():

        phase17 = load_csv(
            PHASE17_PATH,
            "Phase17 factors",
        )

        required_phase17 = [
            "ExecutionDate",
            "Ticker",
            "Notional",
        ]

        if all(
            c in phase17.columns
            for c in required_phase17
        ):

            phase17 = phase17.copy()

            phase17["ExecutionDate"] = (
                normalize_date(
                    phase17["ExecutionDate"]
                )
            )

            phase17["Ticker"] = (
                normalize_ticker(
                    phase17["Ticker"]
                )
            )

            phase17["NotionalKey"] = (
                normalize_notional(
                    phase17["Notional"]
                )
            )

            phase17_keys = (
                phase17[
                    key_columns
                ]
                .drop_duplicates()
                .copy()
            )

            phase17_keys["Phase17Key"] = True

            merged = merged.merge(
                phase17_keys,
                on=key_columns,
                how="left",
            )

            merged["Phase17Key"] = (
                merged["Phase17Key"]
                .fillna(False)
                .astype(bool)
            )

        else:

            print(
                "Phase17 no contiene todas las "
                "columnas requeridas; "
                "cross-check omitido."
            )

            merged["Phase17Key"] = False

    else:

        print(
            f"Phase17 no encontrado; "
            f"cross-check omitido: {PHASE17_PATH}"
        )

        merged["Phase17Key"] = False

    # --------------------------------------------------------
    # DIAGNÓSTICO ALTERNATIVO:
    #
    # ¿Existe misma fecha + ticker pero con
    # otro Notional?
    #
    # Esto permite separar:
    #
    # A) realmente no existe score
    # B) existe score pero no coincide Notional
    # --------------------------------------------------------

    pair_columns = [
        "ExecutionDate",
        "Ticker",
    ]

    pair_score = scores[
        pair_columns
        + [
            "NotionalKey",
            "S_WEAK",
        ]
    ].copy()

    pair_score = pair_score.drop_duplicates(
        pair_columns
        + ["NotionalKey"]
    )

    pair_groups = {}

    for pair, group in pair_score.groupby(
        pair_columns,
        dropna=False,
    ):

        pair_groups[pair] = group

    merged["SameDateTickerScoreRows"] = [
        len(
            pair_groups.get(
                (
                    date,
                    ticker,
                ),
                [],
            )
        )
        for date, ticker
        in zip(
            merged["ExecutionDate"],
            merged["Ticker"],
        )
    ]

    def diagnose_no_match(row):

        if row["HasScoreKey"]:
            return "EXACT_KEY_MATCH"

        group = pair_groups.get(
            (
                row["ExecutionDate"],
                row["Ticker"],
            )
        )

        if group is None or len(group) == 0:
            return "NO_DATE_TICKER_SCORE"

        return (
            "DATE_TICKER_EXISTS_"
            "NOTIONAL_KEY_DIFFERS"
        )

    merged["NoMatchDiagnosis"] = merged.apply(
        diagnose_no_match,
        axis=1,
    )

    # --------------------------------------------------------
    # PARA LOS NO MATCH:
    # buscar información disponible en Phase 18
    # por ExecutionDate + Ticker, aunque Notional
    # no coincida.
    # --------------------------------------------------------

    diagnostic_columns = [
        "R60",
        "VOL252",
        "DIST_200D",
        "S_WEAK",
        "S_QUICK",
        "S_MAE10",
        "Y_WEAK",
        "Y_SUCCESS",
        "Y_MAE10",
        "Return_5D",
        "Return_10D",
        "Return_20D",
        "MAE_20D",
        "FailureClass",
        "Split",
    ]

    available_diagnostic_columns = [
        c
        for c in diagnostic_columns
        if c in scores.columns
    ]

    candidate_rows = []

    for _, row in merged.iterrows():

        if row["ProblemClass"] != "NO_SCORE_KEY":

            candidate_rows.append({})

            continue

        group = pair_groups.get(
            (
                row["ExecutionDate"],
                row["Ticker"],
            )
        )

        if group is None or len(group) == 0:

            candidate_rows.append({})

            continue

        # Para diagnóstico solamente.
        # No se utiliza para hacer matching.
        candidate = group.iloc[0]

        values = {}

        for column in available_diagnostic_columns:

            if column in candidate.index:

                values[
                    f"PAIR_{column}"
                ] = candidate[column]

        candidate_rows.append(values)

    candidate_df = pd.DataFrame(
        candidate_rows
    )

    if not candidate_df.empty:

        merged = pd.concat(
            [
                merged.reset_index(drop=True),
                candidate_df.reset_index(drop=True),
            ],
            axis=1,
        )

    # --------------------------------------------------------
    # QUEDARNOS SOLO CON LOS PROBLEMÁTICOS
    # --------------------------------------------------------

    problems = merged[
        merged["ProblemClass"]
        .ne("SCORE_PRESENT_S_WEAK_VALID")
    ].copy()

    # --------------------------------------------------------
    # ORDEN
    # --------------------------------------------------------

    sort_columns = [
        c
        for c in [
            "ProblemClass",
            "ExecutionDate",
            "Ticker",
        ]
        if c in problems.columns
    ]

    if sort_columns:

        problems = problems.sort_values(
            sort_columns
        )

    # --------------------------------------------------------
    # EXPORT CSV
    # --------------------------------------------------------

    problems.to_csv(
        OUT_CSV,
        index=False,
    )

    # --------------------------------------------------------
    # RESUMEN
    # --------------------------------------------------------

    exact_matches = int(
        merged["HasScoreKey"].sum()
    )

    unmatched = int(
        (~merged["HasScoreKey"]).sum()
    )

    no_score_key = int(
        (
            merged["ProblemClass"]
            == "NO_SCORE_KEY"
        ).sum()
    )

    score_sweak_nan = int(
        (
            merged["ProblemClass"]
            == "SCORE_PRESENT_S_WEAK_NAN"
        ).sum()
    )

    score_sweak_valid = int(
        (
            merged["ProblemClass"]
            == "SCORE_PRESENT_S_WEAK_VALID"
        ).sum()
    )

    phase17_matched = int(
        merged["Phase17Key"].sum()
    )

    # --------------------------------------------------------
    # JSON
    # --------------------------------------------------------

    problems_json = problems.replace(
        {
            np.nan: None
        }
    )

    problem_records = (
        problems_json
        .to_dict(
            orient="records"
        )
    )

    summary = {

        "Policy": POLICY,

        "TradesPath": str(
            TRADES_PATH
        ),

        "ScorePath": str(
            SCORE_PATH
        ),

        "Phase17Path": str(
            PHASE17_PATH
        ),

        "BuyRows": int(
            len(buys)
        ),

        "RawScoreRows": int(
            len(scores)
        ),

        "DuplicateScoreKeys": (
            duplicate_score_keys
        ),

        "ExactKeyMatched": (
            exact_matches
        ),

        "UnmatchedBuyRows": (
            unmatched
        ),

        "UnmatchedNoScoreKey": (
            no_score_key
        ),

        "UnmatchedScorePresentSWeakNaN": (
            score_sweak_nan
        ),

        "ScorePresentSWeakValid": (
            score_sweak_valid
        ),

        "Phase17KeyMatched": (
            phase17_matched
        ),

        "Phase17KeyMissing": (
            int(
                len(merged)
                - phase17_matched
            )
        ),

        "NoStrategyChange": True,

        "PortfolioCounterfactualClaimed": False,

        "Status": "DIAGNOSTIC_ONLY",

        "ProblemRows": problem_records,
    }

    OUT_JSON.write_text(
        json.dumps(
            summary,
            ensure_ascii=False,
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )

    # --------------------------------------------------------
    # CONSOLA
    # --------------------------------------------------------

    print()
    print("=" * 80)
    print("RESULTADO DEL DIAGNÓSTICO")
    print("=" * 80)

    print(
        f"BUY rows:                         {len(buys):,}"
    )

    print(
        f"Exact key matched:                {exact_matches:,}"
    )

    print(
        f"Unmatched BUY rows:               {unmatched:,}"
    )

    print(
        f"  NO_SCORE_KEY:                    {no_score_key:,}"
    )

    print(
        "  SCORE_PRESENT_S_WEAK_NAN:        "
        f"{score_sweak_nan:,}"
    )

    print(
        f"Phase17 key matched:              {phase17_matched:,}"
    )

    print(
        f"Duplicate Phase18 score keys:    "
        f"{duplicate_score_keys:,}"
    )

    print()
    print(
        "Archivos generados:"
    )

    print(
        f"  {OUT_CSV}"
    )

    print(
        f"  {OUT_JSON}"
    )

    print()
    print(
        "FILAS PROBLEMÁTICAS:"
    )

    display_columns = [
        c
        for c in [
            "ExecutionDate",
            "Ticker",
            "Notional",
            "ProblemClass",
            "NoMatchDiagnosis",
            "Phase17Key",
            "S_WEAK",
            "R60",
            "VOL252",
            "DIST_200D",
            "PAIR_S_WEAK",
            "PAIR_R60",
            "PAIR_VOL252",
            "PAIR_DIST_200D",
        ]
        if c in problems.columns
    ]

    if len(problems) > 0:

        print(
            problems[
                display_columns
            ].to_string(
                index=False
            )
        )

    else:

        print(
            "No se encontraron filas problemáticas."
        )

    print()
    print(
        "STATUS: DIAGNOSTIC_ONLY"
    )

    print(
        "No se modifica Phase 19A "
        "ni ningún gate de producción."
    )


if __name__ == "__main__":
    main()

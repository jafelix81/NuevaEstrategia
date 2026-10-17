from pathlib import Path
import json
import pandas as pd
import numpy as np


# ============================================================
# FASE 19A — DIAGNÓSTICO MATCHING NOTIONAL
# ============================================================
#
# Objetivo:
#
# Demostrar si las 9 filas que desaparecen en Phase 17
# son consecuencia del matching exacto de Notional como float.
#
# NO modifica Phase 17.
# NO modifica estrategia.
# NO modifica datos.
# DIAGNÓSTICO SOLAMENTE.
#
# Compara:
#
#   A) Merge exacto:
#      ExecutionDate + Ticker + Notional
#
#   B) Merge robusto:
#      ExecutionDate + Ticker + round(Notional, 8)
#
# ============================================================


POLICY = "F80_TOP20_PARTIAL50_BASELINE_C20"

TRADES_PATH = Path(
    "phase15b_c20_trades.csv"
)

PHASE16_PATH = Path(
    "fase16B_momentum_failure_anatomy.csv"
)

OUT_DIR = Path(
    "fase19a_notional_matching"
)

OUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


RUN_ID = pd.Timestamp.now("UTC").strftime(
    "%Y%m%d_%H%M%S"
)


# ============================================================
# LOAD
# ============================================================

print("=" * 80)
print("FASE 19A — DIAGNÓSTICO MATCHING NOTIONAL")
print("=" * 80)

print(f"RUN_ID: {RUN_ID}")
print(f"Policy: {POLICY}")
print("DIAGNÓSTICO SOLAMENTE")
print()


if not TRADES_PATH.exists():
    raise FileNotFoundError(TRADES_PATH)

if not PHASE16_PATH.exists():
    raise FileNotFoundError(PHASE16_PATH)


trades = pd.read_csv(TRADES_PATH)
phase16 = pd.read_csv(PHASE16_PATH)


# ============================================================
# NORMALIZACIÓN
# ============================================================

def normalize(df):

    df = df.copy()

    df.columns = [
        str(c).strip()
        for c in df.columns
    ]

    for c in [
        "ExecutionDate",
        "DateSignal"
    ]:

        if c in df.columns:

            df[c] = pd.to_datetime(
                df[c],
                errors="coerce"
            ).dt.normalize()

    if "Ticker" in df.columns:

        df["Ticker"] = (
            df["Ticker"]
            .astype(str)
            .str.strip()
            .str.upper()
        )

    if "Notional" in df.columns:

        df["Notional"] = pd.to_numeric(
            df["Notional"],
            errors="coerce"
        )

    return df


trades = normalize(trades)
phase16 = normalize(phase16)


# ============================================================
# FILTRO POLICY
# ============================================================

trades = trades[
    trades["PolicyID"].astype(str)
    == POLICY
].copy()


trades = trades[
    trades["Side"].astype(str).str.upper()
    == "BUY"
].copy()


phase16 = phase16.copy()


print("Phase15B BUY:", len(trades))
print("Phase16B rows:", len(phase16))
print()


# ============================================================
# LLAVES
# ============================================================

BASE_KEY = [
    "ExecutionDate",
    "Ticker"
]


# ============================================================
# MERGE EXACTO
# ============================================================

trades_exact = trades.copy()
phase16_exact = phase16.copy()


exact = trades_exact.merge(
    phase16_exact[
        BASE_KEY + ["Notional"]
    ],
    on=[
        "ExecutionDate",
        "Ticker",
        "Notional"
    ],
    how="inner"
)


print("=" * 80)
print("MERGE EXACTO")
print("=" * 80)

print(
    "Matches exactos:",
    len(exact)
)

print(
    "Faltantes:",
    len(trades) - len(exact)
)

print()


# ============================================================
# LLAVE ROBUSTA
# ============================================================

trades["NotionalKey"] = (
    trades["Notional"]
    .round(8)
)

phase16["NotionalKey"] = (
    phase16["Notional"]
    .round(8)
)


ROBUST_KEY = [
    "ExecutionDate",
    "Ticker",
    "NotionalKey"
]


# ============================================================
# DUPLICADOS DE LA LLAVE ROBUSTA
# ============================================================

dup_trade = (
    trades
    .groupby(ROBUST_KEY, dropna=False)
    .size()
    .reset_index(name="Count")
)

dup_trade = dup_trade[
    dup_trade["Count"] > 1
]


dup_phase16 = (
    phase16
    .groupby(ROBUST_KEY, dropna=False)
    .size()
    .reset_index(name="Count")
)

dup_phase16 = dup_phase16[
    dup_phase16["Count"] > 1
]


# ============================================================
# MERGE ROBUSTO
# ============================================================

phase16_keys = phase16[
    ROBUST_KEY + ["Notional"]
].copy()


robust = trades.merge(
    phase16_keys,
    on=ROBUST_KEY,
    how="inner",
    suffixes=("_15B", "_16B")
)


print("=" * 80)
print("MERGE ROBUSTO — NOTIONAL ROUND(8)")
print("=" * 80)

print(
    "Matches robustos:",
    len(robust)
)

print(
    "Faltantes:",
    len(trades) - len(robust)
)

print(
    "Duplicados llave 15B:",
    len(dup_trade)
)

print(
    "Duplicados llave 16B:",
    len(dup_phase16)
)

print()


# ============================================================
# IDENTIFICAR LAS FILAS PERDIDAS EN EL MERGE EXACTO
# ============================================================

exact_keys = exact[
    [
        "ExecutionDate",
        "Ticker",
        "Notional"
    ]
].drop_duplicates()


lost_exact = trades.merge(
    exact_keys,
    on=[
        "ExecutionDate",
        "Ticker",
        "Notional"
    ],
    how="left",
    indicator=True
)


lost_exact = lost_exact[
    lost_exact["_merge"] == "left_only"
].copy()


# ============================================================
# PARA CADA FILA PERDIDA:
# BUSCAR CANDIDATO EN PHASE16 POR FECHA + TICKER
# ============================================================

phase16_candidates = phase16[
    [
        "ExecutionDate",
        "Ticker",
        "Notional"
    ]
].copy()


diagnostic_rows = []


for _, r in lost_exact.iterrows():

    date = r["ExecutionDate"]
    ticker = r["Ticker"]
    notional15 = r["Notional"]

    candidates = phase16_candidates[
        (phase16_candidates["ExecutionDate"] == date)
        &
        (phase16_candidates["Ticker"] == ticker)
    ].copy()

    if candidates.empty:

        diagnostic_rows.append({
            "ExecutionDate": date,
            "Ticker": ticker,
            "Notional_15B": notional15,
            "Phase16_Candidate": np.nan,
            "AbsoluteDifference": np.nan,
            "RelativeDifference": np.nan,
            "Rounded8_Match": False,
            "Diagnosis": "NO_DATE_TICKER_CANDIDATE_IN_PHASE16"
        })

        continue


    candidates["AbsoluteDifference"] = (
        candidates["Notional"]
        - notional15
    ).abs()


    candidates = candidates.sort_values(
        "AbsoluteDifference"
    )


    best = candidates.iloc[0]

    notional16 = best["Notional"]

    abs_diff = abs(
        notional16 - notional15
    )

    if notional15 != 0:

        rel_diff = (
            abs_diff /
            abs(notional15)
        )

    else:

        rel_diff = np.nan


    rounded_match = (
        round(float(notional15), 8)
        ==
        round(float(notional16), 8)
    )


    if rounded_match:

        diagnosis = (
            "FLOAT_PRECISION_MISMATCH"
        )

    else:

        diagnosis = (
            "NOTIONAL_DIFFERENCE_REQUIRES_REVIEW"
        )


    diagnostic_rows.append({
        "ExecutionDate": date,
        "Ticker": ticker,
        "Notional_15B": notional15,
        "Notional_16B": notional16,
        "AbsoluteDifference": abs_diff,
        "RelativeDifference": rel_diff,
        "Rounded8_15B": round(float(notional15), 8),
        "Rounded8_16B": round(float(notional16), 8),
        "Rounded8_Match": rounded_match,
        "Diagnosis": diagnosis
    })


diagnostic = pd.DataFrame(
    diagnostic_rows
)


# ============================================================
# GUARDAR
# ============================================================

diagnostic.to_csv(
    OUT_DIR /
    "phase19a_notional_missing_exact.csv",
    index=False
)


robust.to_csv(
    OUT_DIR /
    "phase19a_notional_robust_matches.csv",
    index=False
)


dup_trade.to_csv(
    OUT_DIR /
    "phase19a_notional_duplicates_15b.csv",
    index=False
)


dup_phase16.to_csv(
    OUT_DIR /
    "phase19a_notional_duplicates_16b.csv",
    index=False
)


# ============================================================
# RESUMEN
# ============================================================

float_precision_count = int(
    (
        diagnostic["Diagnosis"]
        ==
        "FLOAT_PRECISION_MISMATCH"
    ).sum()
)


real_difference_count = int(
    (
        diagnostic["Diagnosis"]
        ==
        "NOTIONAL_DIFFERENCE_REQUIRES_REVIEW"
    ).sum()
)


no_candidate_count = int(
    (
        diagnostic["Diagnosis"]
        ==
        "NO_DATE_TICKER_CANDIDATE_IN_PHASE16"
    ).sum()
)


summary = {

    "RUN_ID": RUN_ID,

    "Policy": POLICY,

    "Phase15B_BUY": int(len(trades)),

    "Phase16B_rows": int(len(phase16)),

    "ExactMatches": int(len(exact)),

    "ExactMissing": int(
        len(trades) - len(exact)
    ),

    "RobustMatches": int(
        len(robust)
    ),

    "RobustMissing": int(
        len(trades) - len(robust)
    ),

    "FloatPrecisionMismatch": float_precision_count,

    "RealNotionalDifference": real_difference_count,

    "NoDateTickerCandidate": no_candidate_count,

    "DuplicateRobustKeys15B": int(
        len(dup_trade)
    ),

    "DuplicateRobustKeys16B": int(
        len(dup_phase16)
    ),

    "STATUS":

        "FLOAT_MATCHING_BUG_CONFIRMED"
        if (
            len(trades) == len(robust)
            and float_precision_count == len(lost_exact)
        )

        else
        "REQUIRES_REVIEW"
}


with open(
    OUT_DIR /
    "phase19a_notional_matching_diagnostic.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        summary,
        f,
        indent=2,
        ensure_ascii=False
    )


# ============================================================
# CONSOLA
# ============================================================

print()
print("=" * 80)
print("RESULTADO FINAL")
print("=" * 80)

print(
    f"15B BUY:                 {len(trades)}"
)

print(
    f"16B rows:                {len(phase16)}"
)

print(
    f"Merge exacto:            {len(exact)}"
)

print(
    f"Perdidas exacto:         {len(lost_exact)}"
)

print(
    f"Merge robusto round(8):  {len(robust)}"
)

print(
    f"Perdidas robusto:        "
    f"{len(trades) - len(robust)}"
)

print()

print(
    f"Float precision mismatch:"
    f" {float_precision_count}"
)

print(
    f"Notional realmente distinto:"
    f" {real_difference_count}"
)

print(
    f"Sin candidato Date+Ticker:"
    f" {no_candidate_count}"
)

print()

if len(diagnostic):

    print("=" * 80)
    print("FILAS PERDIDAS POR MERGE EXACTO")
    print("=" * 80)

    display_cols = [
        "ExecutionDate",
        "Ticker",
        "Notional_15B",
        "Notional_16B",
        "AbsoluteDifference",
        "Rounded8_15B",
        "Rounded8_16B",
        "Rounded8_Match",
        "Diagnosis"
    ]

    display_cols = [
        c for c in display_cols
        if c in diagnostic.columns
    ]

    print(
        diagnostic[
            display_cols
        ].to_string(index=False)
    )


print()
print("=" * 80)

print(
    f"STATUS: {summary['STATUS']}"
)

print("=" * 80)

import os
import json
from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# FASE 19A — DIAGNÓSTICO ORIGEN NaN / PÉRDIDAS PHASE18
# ============================================================
# DIAGNÓSTICO SOLAMENTE
#
# NO modifica:
#   - estrategia
#   - política
#   - selección
#   - gates
#   - riesgo
#   - portfolio
#
# Objetivo:
#   1. Auditar cobertura exacta 15B -> 16B -> 17 -> 18.
#   2. Identificar las filas que desaparecen entre fases.
#   3. Identificar el origen de S_WEAK = NaN.
#   4. Auditar específicamente R60, VOL252 y DIST_200D.
#   5. Trazar los BUY que no llegan a Phase18.
#
# ============================================================


POLICY = "F80_TOP20_PARTIAL50_BASELINE_C20"

TRADES_PATH = os.environ.get(
    "PHASE15B_TRADES_PATH",
    "phase15b_c20_trades.csv"
)

PHASE16_PATH = os.environ.get(
    "PHASE16B_PATH",
    "fase16B_momentum_failure_anatomy.csv"
)

PHASE17_PATH = os.environ.get(
    "PHASE17_DATASET_PATH",
    "nueva_estrategia_phase17_failure_predictability/phase17_entry_factor_dataset.csv"
)

PHASE18_PATH = os.environ.get(
    "PHASE18_DATASET_PATH",
    "nueva_estrategia_phase18_failure_score/phase18_entry_score_dataset.csv"
)

OUT_DIR = Path("fase19a_origen_phase18")
OUT_DIR.mkdir(parents=True, exist_ok=True)

RUN_ID = pd.Timestamp.utcnow().strftime("%Y%m%d_%H%M%S")


# ============================================================
# UTILIDADES
# ============================================================

def load_csv(path):
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"No existe: {path}")

    df = pd.read_csv(path)

    print(f"Cargado: {path}")
    print(f"  rows = {len(df)}")
    print(f"  cols = {len(df.columns)}")

    return df


def normalize_date(df, column):
    if column in df.columns:
        df[column] = pd.to_datetime(
            df[column],
            errors="coerce"
        ).dt.normalize()

    return df


def normalize_ticker(df, column="Ticker"):
    if column in df.columns:
        df[column] = (
            df[column]
            .astype(str)
            .str.strip()
            .str.upper()
        )

    return df


def normalize_notional(df, column="Notional"):
    if column in df.columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

        df["NotionalKey"] = df[column].round(8)

    return df


def normalize(df):
    df = df.copy()

    for c in [
        "ExecutionDate",
        "Date",
        "DateSignal",
        "EntryDate"
    ]:
        if c in df.columns:
            df = normalize_date(df, c)

    if "Ticker" in df.columns:
        df = normalize_ticker(df)

    if "Notional" in df.columns:
        df = normalize_notional(df)

    return df


def get_key_columns(df):
    """
    La llave principal de esta auditoría es:

        ExecutionDate + Ticker + NotionalKey
    """

    required = [
        "ExecutionDate",
        "Ticker",
        "NotionalKey"
    ]

    missing = [
        c for c in required
        if c not in df.columns
    ]

    if missing:
        raise RuntimeError(
            f"Faltan columnas para llave: {missing}"
        )

    return required


def add_unique_indicator(df_left, df_right, key_cols, name):
    """
    Merge left-only / both / right-only evitando conflictos
    con columnas _merge existentes.
    """

    left = df_left.copy()
    right = df_right.copy()

    # Eliminar indicadores previos para evitar:
    # ValueError: Cannot use name of an existing column...
    for df in [left, right]:
        for col in list(df.columns):
            if col.startswith("_merge"):
                df.drop(columns=[col], inplace=True)

    # Reducir right a llaves únicas para cobertura.
    right_keys = right[key_cols].drop_duplicates().copy()
    right_keys[name] = "both"

    result = left.merge(
        right_keys,
        on=key_cols,
        how="left",
        validate="many_to_one"
    )

    result[name] = result[name].fillna("left_only")

    return result


def duplicate_audit(df, key_cols):
    dup = (
        df.groupby(key_cols, dropna=False)
        .size()
        .reset_index(name="Count")
    )

    return dup[dup["Count"] > 1].copy()


def safe_bool(x):
    if pd.isna(x):
        return False

    return bool(x)


# ============================================================
# CARGA
# ============================================================

print("=" * 80)
print("FASE 19A — DIAGNÓSTICO ORIGEN PHASE18")
print("=" * 80)
print(f"RUN_ID: {RUN_ID}")
print(f"Policy congelada: {POLICY}")
print("DIAGNÓSTICO SOLAMENTE")
print()


trades = normalize(load_csv(TRADES_PATH))
phase16 = normalize(load_csv(PHASE16_PATH))
phase17 = normalize(load_csv(PHASE17_PATH))
phase18 = normalize(load_csv(PHASE18_PATH))


# ============================================================
# VALIDACIÓN DE COLUMNAS
# ============================================================

key_cols = get_key_columns(trades)

for name, df in [
    ("Phase16B", phase16),
    ("Phase17", phase17),
    ("Phase18", phase18),
]:
    missing = [
        c for c in key_cols
        if c not in df.columns
    ]

    if missing:
        raise RuntimeError(
            f"{name}: faltan columnas de llave: {missing}"
        )


# ============================================================
# FILTRO DE POLÍTICA
# ============================================================

if "PolicyID" in trades.columns:
    trades_policy = trades[
        trades["PolicyID"].astype(str).str.strip()
        == POLICY
    ].copy()
else:
    raise RuntimeError(
        "Phase15B no contiene columna PolicyID."
    )


if "Side" in trades_policy.columns:
    buys = trades_policy[
        trades_policy["Side"].astype(str).str.upper()
        == "BUY"
    ].copy()
else:
    raise RuntimeError(
        "Phase15B no contiene columna Side."
    )


print("BUY rows política congelada:", len(buys))
print()


# ============================================================
# DUPLICADOS
# ============================================================

duplicate_reports = {}

duplicate_reports["phase15b"] = duplicate_audit(
    buys,
    key_cols
)

duplicate_reports["phase16b"] = duplicate_audit(
    phase16,
    key_cols
)

duplicate_reports["phase17"] = duplicate_audit(
    phase17,
    key_cols
)

duplicate_reports["phase18"] = duplicate_audit(
    phase18,
    key_cols
)


# ============================================================
# COBERTURA 15B -> 16B
# ============================================================

coverage_15_16 = add_unique_indicator(
    buys,
    phase16,
    key_cols,
    "_coverage_15_16"
)

missing_15_16 = coverage_15_16[
    coverage_15_16["_coverage_15_16"] != "both"
].copy()


# ============================================================
# COBERTURA 16B -> 17
# ============================================================

coverage_16_17 = add_unique_indicator(
    phase16,
    phase17,
    key_cols,
    "_coverage_16_17"
)

missing_16_17 = coverage_16_17[
    coverage_16_17["_coverage_16_17"] != "both"
].copy()


# ============================================================
# COBERTURA 17 -> 18
# ============================================================

coverage_17_18 = add_unique_indicator(
    phase17,
    phase18,
    key_cols,
    "_coverage_17_18"
)

missing_17_18 = coverage_17_18[
    coverage_17_18["_coverage_17_18"] != "both"
].copy()


# ============================================================
# COBERTURA 15B -> 18
# ============================================================

coverage_15_18 = add_unique_indicator(
    buys,
    phase18,
    key_cols,
    "_coverage_15_18"
)

missing_15_18 = coverage_15_18[
    coverage_15_18["_coverage_15_18"] != "both"
].copy()


# ============================================================
# RESUMEN DE COBERTURA
# ============================================================

coverage_summary = {
    "run_id": RUN_ID,
    "policy": POLICY,

    "phase15b_buy_rows": int(len(buys)),
    "phase16b_rows": int(len(phase16)),
    "phase17_rows": int(len(phase17)),
    "phase18_rows": int(len(phase18)),

    "missing_15_to_16": int(len(missing_15_16)),
    "missing_16_to_17": int(len(missing_16_17)),
    "missing_17_to_18": int(len(missing_17_18)),
    "missing_15_to_18": int(len(missing_15_18)),

    "duplicate_phase15b_keys": int(
        len(duplicate_reports["phase15b"])
    ),
    "duplicate_phase16b_keys": int(
        len(duplicate_reports["phase16b"])
    ),
    "duplicate_phase17_keys": int(
        len(duplicate_reports["phase17"])
    ),
    "duplicate_phase18_keys": int(
        len(duplicate_reports["phase18"])
    ),
}


# ============================================================
# GUARDAR PÉRDIDAS ENTRE FASES
# ============================================================

missing_15_16.to_csv(
    OUT_DIR / "phase19a_missing_15_to_16.csv",
    index=False
)

missing_16_17.to_csv(
    OUT_DIR / "phase19a_missing_16_to_17.csv",
    index=False
)

missing_17_18.to_csv(
    OUT_DIR / "phase19a_missing_17_to_18.csv",
    index=False
)

missing_15_18.to_csv(
    OUT_DIR / "phase19a_missing_15_to_18.csv",
    index=False
)


# ============================================================
# AUDIT DE S_WEAK
# ============================================================

if "S_WEAK" not in phase18.columns:
    raise RuntimeError(
        "Phase18 no contiene columna S_WEAK."
    )


phase18_weak_nan = phase18[
    phase18["S_WEAK"].isna()
].copy()


# ============================================================
# MERGE CON PHASE17 PARA RECUPERAR FACTORES
# ============================================================

factor_cols = [
    "R60",
    "VOL252",
    "DIST_200D"
]

factor_cols_present = [
    c for c in factor_cols
    if c in phase17.columns
]


phase17_factor_subset = phase17[
    key_cols + factor_cols_present
].drop_duplicates(
    subset=key_cols
)


weak_diag = phase18_weak_nan.merge(
    phase17_factor_subset,
    on=key_cols,
    how="left",
    suffixes=("", "_P17"),
    indicator="_weak_factor_merge"
)


# ============================================================
# NORMALIZAR NOMBRES DE FACTORES
# ============================================================

for factor in factor_cols:
    if factor not in weak_diag.columns:
        right_name = factor + "_P17"

        if right_name in weak_diag.columns:
            weak_diag[factor] = weak_diag[right_name]


# ============================================================
# FLAGS DE FACTORES
# ============================================================

for factor in factor_cols:
    if factor in weak_diag.columns:
        weak_diag[f"{factor}_missing"] = (
            weak_diag[factor].isna()
        )
    else:
        weak_diag[f"{factor}_missing"] = True


weak_diag["AllThreeFactorsNaN"] = (
    weak_diag["R60_missing"]
    & weak_diag["VOL252_missing"]
    & weak_diag["DIST_200D_missing"]
)

weak_diag["AnyFactorNaN"] = (
    weak_diag["R60_missing"]
    | weak_diag["VOL252_missing"]
    | weak_diag["DIST_200D_missing"]
)

weak_diag["AllComponentsPresent"] = (
    ~weak_diag["AnyFactorNaN"]
)


def classify_nan_origin(row):

    if row["_weak_factor_merge"] != "both":
        return "NO_PHASE17_MATCH"

    if row["AllThreeFactorsNaN"]:
        return "ALL_THREE_COMPONENTS_NAN"

    if row["AnyFactorNaN"]:
        return "PARTIAL_COMPONENT_NAN"

    return "ALL_COMPONENTS_PRESENT_BUT_SCORE_NAN"


weak_diag["NaNOrigin"] = weak_diag.apply(
    classify_nan_origin,
    axis=1
)


weak_diag.to_csv(
    OUT_DIR / "phase19a_phase18_nan_cases.csv",
    index=False
)


# ============================================================
# TRAZAR LOS BUY QUE NO LLEGAN A PHASE18
# ============================================================

missing_phase18 = missing_15_18.copy()


# Información de Phase17
phase17_keys = phase17[
    key_cols
].drop_duplicates().copy()

phase17_keys["HasPhase17"] = True


missing_phase18 = missing_phase18.merge(
    phase17_keys,
    on=key_cols,
    how="left"
)

missing_phase18["HasPhase17"] = (
    missing_phase18["HasPhase17"]
    .fillna(False)
)


# Información de Phase16
phase16_keys = phase16[
    key_cols
].drop_duplicates().copy()

phase16_keys["HasPhase16"] = True


missing_phase18 = missing_phase18.merge(
    phase16_keys,
    on=key_cols,
    how="left"
)

missing_phase18["HasPhase16"] = (
    missing_phase18["HasPhase16"]
    .fillna(False)
)


missing_phase18["TraceResult"] = np.select(
    [
        (~missing_phase18["HasPhase16"])
        & (~missing_phase18["HasPhase17"]),

        missing_phase18["HasPhase16"]
        & (~missing_phase18["HasPhase17"]),

        missing_phase18["HasPhase17"]
    ],
    [
        "MISSING_ALREADY_PHASE16",
        "DISAPPEARS_16_TO_17",
        "PRESENT_PHASE17_BUT_MISSING_PHASE18"
    ],
    default="UNKNOWN"
)


missing_phase18.to_csv(
    OUT_DIR / "phase19a_missing_phase18_trace.csv",
    index=False
)


# ============================================================
# DUPLICADOS
# ============================================================

for name, df in duplicate_reports.items():

    df.to_csv(
        OUT_DIR / f"phase19a_duplicates_{name}.csv",
        index=False
    )


# ============================================================
# RESUMEN S_WEAK
# ============================================================

nan_origin_summary = (
    weak_diag["NaNOrigin"]
    .value_counts(dropna=False)
    .to_dict()
)

coverage_summary["s_weak_nan_rows"] = int(
    len(phase18_weak_nan)
)

coverage_summary["s_weak_nan_origin"] = {
    str(k): int(v)
    for k, v in nan_origin_summary.items()
}


# ============================================================
# JSON FINAL
# ============================================================

coverage_summary["files"] = {
    "missing_15_to_16":
        str(OUT_DIR / "phase19a_missing_15_to_16.csv"),

    "missing_16_to_17":
        str(OUT_DIR / "phase19a_missing_16_to_17.csv"),

    "missing_17_to_18":
        str(OUT_DIR / "phase19a_missing_17_to_18.csv"),

    "missing_15_to_18":
        str(OUT_DIR / "phase19a_missing_15_to_18.csv"),

    "phase18_nan_cases":
        str(OUT_DIR / "phase19a_phase18_nan_cases.csv"),

    "missing_phase18_trace":
        str(OUT_DIR / "phase19a_missing_phase18_trace.csv"),
}


with open(
    OUT_DIR / "phase19a_origen_phase18_diagnostic.json",
    "w",
    encoding="utf-8"
) as f:
    json.dump(
        coverage_summary,
        f,
        indent=2,
        ensure_ascii=False,
        default=str
    )


# ============================================================
# CONSOLA
# ============================================================

print()
print("=" * 80)
print("RESULTADO DEL DIAGNÓSTICO")
print("=" * 80)

print(f"15B BUY:       {len(buys)}")
print(f"16B rows:      {len(phase16)}")
print(f"17 rows:       {len(phase17)}")
print(f"18 rows:       {len(phase18)}")
print()

print(
    f"15B -> 16B faltantes: {len(missing_15_16)}"
)

print(
    f"16B -> 17 faltantes:  {len(missing_16_17)}"
)

print(
    f"17 -> 18 faltantes:  {len(missing_17_18)}"
)

print(
    f"15B -> 18 faltantes:  {len(missing_15_18)}"
)

print()

print(
    f"S_WEAK NaN:           {len(phase18_weak_nan)}"
)

print()
print("ORIGEN S_WEAK NaN:")

for k, v in nan_origin_summary.items():
    print(f"  {k}: {v}")

print()

print("ARCHIVOS GENERADOS:")

for key, path in coverage_summary["files"].items():
    print(f"  {key}: {path}")

print(
    f"  diagnostic_json: "
    f"{OUT_DIR / 'phase19a_origen_phase18_diagnostic.json'}"
)

print()
print("=" * 80)
print("STATUS: DIAGNOSTIC_ONLY")
print("=" * 80)

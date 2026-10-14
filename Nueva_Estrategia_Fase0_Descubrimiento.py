# CERE / NUEVA ESTRATEGIA — FASE 0: DESCUBRIMIENTO DE FACTORES
# Investigación pura: NO cartera, NO Kelly, NO Google Sheets, NO producción.
#
# Objetivo:
#   Identificar qué características cross-sectional contienen información
#   predictiva OOS sobre retornos futuros a 5/10/20/40 sesiones.
#
# Principios:
#   1) La estrategia anterior LOW-VOL queda fuera como tesis.
#   2) Volatilidad se conserva solamente como FACTOR DE REFERENCIA.
#   3) Los factores se seleccionan exclusivamente con DISCOVERY.
#   4) Las direcciones descubiertas se congelan antes del OOS.
#   5) OOS no modifica factores, signos ni umbrales.
#   6) No se optimiza cartera en esta fase.
#
# Salidas:
#   - phase0_factor_oos.csv
#   - phase0_factor_summary.csv
#   - phase0_discovery_selection.csv
#   - phase0_audit.csv
#
# NOTA:
#   El universo DEFAULT_UNIVERSE debe copiarse desde el proyecto vigente.
#   El script aborta si no existe o está vacío.

import os
import json
import math
import warnings
from pathlib import Path
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import yfinance as yf
from scipy.stats import spearmanr

warnings.filterwarnings("ignore")

# =========================
# CONFIGURACIÓN CONGELADA
# =========================

RUN_ID = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

PERIOD = "10y"
HORIZONS = (5, 10, 20, 40)

DISCOVERY_DATES = 12
MIN_STATE = 260
EMBARGO = 5

# Mínimo número de acciones para evaluar un cross-section.
MIN_CROSS_SECTION = 100

# Factores candidatos.
# Ninguno constituye todavía una estrategia.
FACTORS = [
    "R1",
    "R5",
    "R20",
    "R60",
    "R120",
    "MOM_ACCEL",
    "VOL20",
    "VOL60",
    "VOL252",
    "VOL_RATIO_20_252",
    "VOL_RATIO_60_252",
    "VOL_SURPRISE",
    "VOLUME_TREND",
    "DOLLAR_VOLUME_LOG",
    "RANGE_EXPANSION",
    "DIST_200D",
]

ART = Path("cere_phase0_discovery")
ART.mkdir(parents=True, exist_ok=True)

# ============================================================
# UNIVERSO
# ============================================================

DEFAULT_UNIVERSE = [
    # IMPORTANTE:
    # Reemplazar este bloque por el DEFAULT_UNIVERSE exacto
    # del proyecto vigente antes de ejecutar.
]

if not DEFAULT_UNIVERSE:
    raise RuntimeError(
        "DEFAULT_UNIVERSE está vacío. Copia el universo congelado de 335 tickers "
        "del proyecto vigente antes de ejecutar Fase 0."
    )

UNIVERSE = list(dict.fromkeys(DEFAULT_UNIVERSE))


# ============================================================
# UTILIDADES
# ============================================================

def clean_ticker(t):
    return str(t).strip().upper()


def safe_std(x):
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    if len(x) < 2:
        return np.nan
    return float(np.std(x, ddof=1))


def annualized_vol(logret, n):
    x = np.asarray(logret, dtype=float)
    if len(x) < n:
        return np.nan
    return safe_std(x[-n:]) * np.sqrt(252.0)


def compute_features(df):
    """
    Todas las variables usan información disponible hasta t.
    No se utiliza ningún dato posterior a t.
    """
    out = df.copy()

    close = pd.to_numeric(out["Close"], errors="coerce")
    open_ = pd.to_numeric(out["Open"], errors="coerce")
    volume = pd.to_numeric(out["Volume"], errors="coerce")
    high = pd.to_numeric(out["High"], errors="coerce")
    low = pd.to_numeric(out["Low"], errors="coerce")

    lr = np.log(close).diff()

    out["R1"] = close / close.shift(1) - 1.0
    out["R5"] = close / close.shift(5) - 1.0
    out["R20"] = close / close.shift(20) - 1.0
    out["R60"] = close / close.shift(60) - 1.0
    out["R120"] = close / close.shift(120) - 1.0

    # Aceleración de momentum:
    # compara retorno reciente contra una versión lenta.
    out["MOM_ACCEL"] = out["R20"] - (out["R60"] / 3.0)

    out["VOL20"] = lr.rolling(20).std(ddof=1) * np.sqrt(252.0)
    out["VOL60"] = lr.rolling(60).std(ddof=1) * np.sqrt(252.0)
    out["VOL252"] = lr.rolling(252).std(ddof=1) * np.sqrt(252.0)

    out["VOL_RATIO_20_252"] = out["VOL20"] / out["VOL252"]
    out["VOL_RATIO_60_252"] = out["VOL60"] / out["VOL252"]

    # Volumen anormal respecto de su propio historial.
    lv = np.log1p(volume.replace(0, np.nan))
    vol_mu = lv.rolling(60).mean()
    vol_sd = lv.rolling(60).std(ddof=1)
    out["VOL_SURPRISE"] = (lv - vol_mu) / vol_sd

    # Tendencia de volumen: promedio corto / promedio largo.
    v20 = volume.rolling(20).mean()
    v60 = volume.rolling(60).mean()
    out["VOLUME_TREND"] = v20 / v60 - 1.0

    # Liquidez: log del dollar volume promedio de 20 sesiones.
    dollar_volume = close * volume
    out["DOLLAR_VOLUME_LOG"] = np.log(
        dollar_volume.rolling(20).mean().replace(0, np.nan)
    )

    # Expansión del rango diario frente a su propio historial.
    # |High-Low| / Close, normalizado por su media de 60 sesiones.
    daily_range = (high - low) / close.replace(0, np.nan)
    range_mu = daily_range.rolling(60).mean()
    out["RANGE_EXPANSION"] = daily_range / range_mu - 1.0

    # Distancia respecto de media móvil de 200 sesiones.
    ma200 = close.rolling(200).mean()
    out["DIST_200D"] = close / ma200 - 1.0

    out["LOGRET"] = lr
    return out


def future_return(df, h):
    """
    Retorno definido exactamente como:
        Close[t+h] / Open[t+1] - 1
    """
    return df["Close"].shift(-h) / df["Open"].shift(-1) - 1.0


def prepare_ticker(ticker):
    try:
        raw = yf.download(
            ticker,
            period=PERIOD,
            auto_adjust=True,
            progress=False,
            actions=False,
            threads=False,
        )

        if raw is None or raw.empty:
            return None, "EMPTY"

        if isinstance(raw.columns, pd.MultiIndex):
            raw.columns = raw.columns.get_level_values(0)

        needed = ["Open", "High", "Low", "Close", "Volume"]
        if not all(c in raw.columns for c in needed):
            return None, "MISSING_COLUMNS"

        raw = raw[needed].copy()
        raw.index = pd.to_datetime(raw.index).tz_localize(None)
        raw = raw[~raw.index.duplicated(keep="last")].sort_index()

        raw = raw.dropna(subset=["Open", "High", "Low", "Close"])
        raw["Volume"] = pd.to_numeric(raw["Volume"], errors="coerce")

        if len(raw) < MIN_STATE + max(HORIZONS) + 5:
            return None, "INSUFFICIENT_HISTORY"

        feat = compute_features(raw)

        for h in HORIZONS:
            feat[f"FWD{h}"] = future_return(feat, h)

        return feat, "OK"

    except Exception as exc:
        return None, f"{type(exc).__name__}:{exc}"


# ============================================================
# CALENDARIOS
# ============================================================

def build_global_dates(datasets, horizon):
    """
    Selecciona fechas globales separadas por al menos H+EMBARGO
    sesiones de trading, no días calendario.
    """
    all_dates = sorted(
        set().union(*[set(df.index) for df in datasets.values()])
    )

    if not all_dates:
        return []

    usable = []
    for d in all_dates:
        count = 0
        for df in datasets.values():
            if d in df.index:
                row = df.loc[d]
                if all(pd.notna(row.get(f)) for f in FACTORS):
                    if pd.notna(row.get(f"FWD{horizon}")):
                        count += 1
        if count >= MIN_CROSS_SECTION:
            usable.append(d)

    if len(usable) < DISCOVERY_DATES + 5:
        raise RuntimeError(
            f"No hay suficientes fechas globales para H={horizon}. "
            f"Disponibles={len(usable)}"
        )

    selected = [usable[0]]
    for d in usable[1:]:
        prev = selected[-1]
        try:
            gap = len(pd.bdate_range(prev, d))
        except Exception:
            gap = 0
        if gap >= horizon + EMBARGO:
            selected.append(d)

    return selected


# ============================================================
# CONSTRUCCIÓN CROSS-SECTIONAL
# ============================================================

def cross_section_at_date(datasets, date, horizon):
    rows = []

    for ticker, df in datasets.items():
        if date not in df.index:
            continue

        row = df.loc[date]

        vals = {}
        valid = True

        for f in FACTORS:
            v = row.get(f, np.nan)
            if not np.isfinite(v):
                valid = False
                break
            vals[f] = float(v)

        fwd = row.get(f"FWD{horizon}", np.nan)

        if not valid or not np.isfinite(fwd):
            continue

        vals["Ticker"] = ticker
        vals["Date"] = date
        vals["ForwardReturn"] = float(fwd)

        rows.append(vals)

    return pd.DataFrame(rows)


# ============================================================
# MÉTRICAS
# ============================================================

def factor_metrics(df, factor, direction):
    if df.empty:
        return None

    x = pd.to_numeric(df[factor], errors="coerce")
    y = pd.to_numeric(df["ForwardReturn"], errors="coerce")

    mask = np.isfinite(x) & np.isfinite(y)
    x = x[mask]
    y = y[mask]

    if len(x) < MIN_CROSS_SECTION:
        return None

    score = direction * x

    rho, _ = spearmanr(score, y)

    q20 = score.quantile(0.80)
    q80 = score.quantile(0.20)

    # score alto = supuesto lado ganador
    top = y[score >= q20]
    bottom = y[score <= q80]

    if len(top) == 0 or len(bottom) == 0:
        return None

    spread = float(top.mean() - bottom.mean())

    return {
        "N": int(len(y)),
        "IC": float(rho),
        "Top20Mean": float(top.mean()),
        "Bottom20Mean": float(bottom.mean()),
        "TopBottomSpread": spread,
        "PositiveTop20Pct": float((top > 0).mean()),
        "MeanForwardTop20": float(top.mean()),
    }


def evaluate_factor_direction(discovery_df, factor):
    """
    La dirección se decide SOLO con Discovery.
    No se consulta OOS.
    """
    plus = factor_metrics(discovery_df, factor, +1)
    minus = factor_metrics(discovery_df, factor, -1)

    if plus is None and minus is None:
        return None

    candidates = []
    if plus:
        candidates.append((abs(plus["IC"]), +1, plus))
    if minus:
        candidates.append((abs(minus["IC"]), -1, minus))

    candidates.sort(reverse=True, key=lambda z: z[0])
    _, direction, best = candidates[0]

    return {
        "Direction": int(direction),
        "DiscoveryIC": best["IC"],
        "DiscoverySpread": best["TopBottomSpread"],
        "DiscoveryN": best["N"],
    }


# ============================================================
# MAIN
# ============================================================

print("=" * 72)
print("NUEVA ESTRATEGIA — FASE 0: DESCUBRIMIENTO DE FACTORES")
print("=" * 72)
print(f"RUN_ID: {RUN_ID}")
print(f"Tickers configurados: {len(UNIVERSE)}")
print(f"Period: {PERIOD}")
print(f"Horizons: {HORIZONS}")
print(f"Discovery dates: {DISCOVERY_DATES}")
print(f"Embargo: {EMBARGO}")
print("NO cartera / NO Kelly / NO producción")
print("=" * 72)

datasets = {}
failures = []

for i, ticker in enumerate(UNIVERSE, 1):
    ticker = clean_ticker(ticker)
    df, status = prepare_ticker(ticker)

    if status == "OK":
        datasets[ticker] = df
    else:
        failures.append({"Ticker": ticker, "Reason": status})

    if i % 25 == 0 or i == len(UNIVERSE):
        print(
            f"[{i}/{len(UNIVERSE)}] "
            f"OK={len(datasets)} FAIL={len(failures)}"
        )

if len(datasets) < MIN_CROSS_SECTION:
    raise RuntimeError(
        f"Dataset insuficiente: {len(datasets)} tickers válidos."
    )

# ------------------------------------------------------------
# Construir calendarios independientes por horizonte.
# ------------------------------------------------------------

calendars = {}
all_rows = []

for h in HORIZONS:
    dates = build_global_dates(datasets, h)

    if len(dates) <= DISCOVERY_DATES:
        raise RuntimeError(
            f"H{h}: calendario insuficiente ({len(dates)} fechas)."
        )

    calendars[h] = dates

    print(
        f"H{h}: {len(dates)} fechas | "
        f"Discovery={DISCOVERY_DATES} | OOS={len(dates)-DISCOVERY_DATES}"
    )

    for phase, phase_dates in [
        ("DISCOVERY", dates[:DISCOVERY_DATES]),
        ("OOS", dates[DISCOVERY_DATES:]),
    ]:
        for d in phase_dates:
            cs = cross_section_at_date(datasets, d, h)
            if cs.empty:
                continue

            cs["Horizon"] = h
            cs["Phase"] = phase
            all_rows.append(cs)

factor_data = pd.concat(all_rows, ignore_index=True)

# ------------------------------------------------------------
# Discovery: elegir dirección de cada factor.
# ------------------------------------------------------------

selection_rows = []

for h in HORIZONS:
    disc = factor_data[
        (factor_data["Horizon"] == h) &
        (factor_data["Phase"] == "DISCOVERY")
    ].copy()

    for factor in FACTORS:
        result = evaluate_factor_direction(disc, factor)

        if result is None:
            continue

        selection_rows.append({
            "Horizon": h,
            "Factor": factor,
            **result,
        })

selection = pd.DataFrame(selection_rows)

# ------------------------------------------------------------
# OOS: aplicar dirección congelada.
# ------------------------------------------------------------

oos_rows = []

for _, sel in selection.iterrows():
    h = int(sel["Horizon"])
    factor = sel["Factor"]
    direction = int(sel["Direction"])

    oos = factor_data[
        (factor_data["Horizon"] == h) &
        (factor_data["Phase"] == "OOS")
    ].copy()

    # Métricas por fecha para medir estabilidad temporal.
    for date, g in oos.groupby("Date", sort=True):
        m = factor_metrics(g, factor, direction)

        if m is None:
            continue

        oos_rows.append({
            "Horizon": h,
            "Factor": factor,
            "Date": date,
            "DirectionFrozen": direction,
            **m,
        })

oos_metrics = pd.DataFrame(oos_rows)

# ------------------------------------------------------------
# Resumen OOS.
# ------------------------------------------------------------

summary_rows = []

for (h, factor), g in oos_metrics.groupby(["Horizon", "Factor"]):
    if g.empty:
        continue

    ic = g["IC"]
    spread = g["TopBottomSpread"]

    summary_rows.append({
        "Horizon": int(h),
        "Factor": factor,
        "OOSDates": int(len(g)),
        "MeanIC": float(ic.mean()),
        "MedianIC": float(ic.median()),
        "PctPositiveIC": float((ic > 0).mean()),
        "MeanSpread": float(spread.mean()),
        "MedianSpread": float(spread.median()),
        "PctPositiveSpread": float((spread > 0).mean()),
        "ICStd": float(ic.std(ddof=1)) if len(ic) > 1 else np.nan,
    })

summary = pd.DataFrame(summary_rows)

# ------------------------------------------------------------
# Auditoría.
# ------------------------------------------------------------

audit = {
    "RUN_ID": RUN_ID,
    "ConfiguredTickers": len(UNIVERSE),
    "ValidTickers": len(datasets),
    "Failures": len(failures),
    "FactorsTested": len(FACTORS),
    "Horizons": len(HORIZONS),
    "DiscoveryDatesRequired": DISCOVERY_DATES,
    "NoEmptySummary": not summary.empty,
    "NoNaNCoreMetrics": bool(
        not summary.empty and
        np.isfinite(summary[[
            "MeanIC",
            "MedianIC",
            "MeanSpread",
            "MedianSpread",
        ]].to_numpy()).all()
    ),
    "OOSDatesValid": bool(
        all(len(calendars[h]) > DISCOVERY_DATES for h in HORIZONS)
    ),
    "Status": "PASS",
}

# No convertir el resultado en PASS si faltan resultados fundamentales.
if summary.empty or selection.empty:
    audit["Status"] = "FAIL"

# ------------------------------------------------------------
# Guardar.
# ------------------------------------------------------------

selection.to_csv(ART / "phase0_discovery_selection.csv", index=False)
oos_metrics.to_csv(ART / "phase0_factor_oos.csv", index=False)
summary.sort_values(
    ["Horizon", "MeanIC"],
    ascending=[True, False]
).to_csv(ART / "phase0_factor_summary.csv", index=False)
pd.DataFrame([audit]).to_csv(ART / "phase0_audit.csv", index=False)

if failures:
    pd.DataFrame(failures).to_csv(
        ART / "phase0_failures.csv",
        index=False
    )

with open(ART / "phase0_calendars.json", "w", encoding="utf-8") as f:
    json.dump(
        {
            str(h): [pd.Timestamp(d).strftime("%Y-%m-%d")
                     for d in dates]
            for h, dates in calendars.items()
        },
        f,
        indent=2,
    )

print("\n" + "=" * 72)
print("RESUMEN OOS — FACTORES")
print("=" * 72)

if not summary.empty:
    print(
        summary.sort_values(
            ["Horizon", "MeanIC"],
            ascending=[True, False]
        ).to_string(index=False)
    )

print("\n" + "=" * 72)
print("AUDITORÍA")
print("=" * 72)
for k, v in audit.items():
    print(f"{k}: {v}")

print("\nNO HAY ESTRATEGIA SELECCIONADA TODAVÍA.")
print("La siguiente fase debe congelar solamente los factores que sobrevivan")
print("Discovery y confirmar su comportamiento OOS.")

# NUEVA ESTRATEGIA — FASE 7: ROBUSTEZ ECONÓMICA DIAGNÓSTICA DE LONG-TERM MOMENTUM
# Investigación puramente predictiva/económica. NO cartera / NO Kelly / NO producción.
#
# Objetivo:
# Llevar la hipótesis congelada de Fase 6 a una prueba económica predefinida,
# sin seleccionar retrospectivamente horizonte, ventana o variante.
#
# Hipótesis congelada:
#   LTM_COMPOSITE = promedio simple de ranks R100/R120/R140/R160
#
# Pruebas predefinidas:
#   A) Monotonicidad completa D1-D10.
#   B) Diagnóstico long-only TOP10/TOP20/TOP30.
#   C) Diagnóstico long-short TOP-BOTTOM.
#   D) Comparación H20 vs H40.
#   E) Sensibilidad predefinida leave-one-window-out (4 variantes).
#   F) Turnover de membresía y fricción 10/20/50 bps.
#
# IMPORTANTE:
# - Los resultados son retornos cross-sectional diagnósticos, NO una simulación
#   de cartera con rebalanceo ni reglas de ejecución.
# - No se selecciona el "mejor" TOP-N, horizonte o variante después de ver OOS.
# - No hay Kelly, stops, sizing ni CASH.
#
import json, warnings
from pathlib import Path
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import yfinance as yf
from scipy.stats import spearmanr

warnings.filterwarnings("ignore")

RUN_ID = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
PERIOD = "10y"
HORIZONS = (20, 40)
DISCOVERY_DATES = 12
EMBARGO = 5
MIN_CROSS_SECTION = 100
MOM_WINDOWS = (100, 120, 140, 160)
TOP_PCTS = (0.10, 0.20, 0.30)
COST_BPS = (10, 20, 50)
ART = Path("nueva_estrategia_phase7_economic_robustness")
ART.mkdir(parents=True, exist_ok=True)

DEFAULT_UNIVERSE = ['AA', 'AAPL', 'ABNB', 'ABT', 'ADI', 'AFRM', 'ALAB', 'ALGN', 'AMAT', 'AMD', 'AMGN', 'AMT', 'AMTD', 'AMZN', 'ANET', 'APA', 'APD', 'APO', 'APP', 'ARKF', 'ARKG', 'ARKK', 'ARKQ', 'ARKW', 'ASB', 'ASML', 'ASTS', 'ATI', 'AVB', 'AVGO', 'AX', 'AXON', 'AXP', 'AZN', 'BA', 'BABA', 'BAC', 'BE', 'BEAM', 'BEN', 'BIDU', 'BIIB', 'BITO', 'BKNG', 'BKR', 'BLK', 'BLNK', 'BMY', 'BNTX', 'BOKF', 'BSX', 'BX', 'BXP', 'C', 'CACC', 'CAT', 'CATY', 'CAVA', 'CCI', 'CDNS', 'CEG', 'CELH', 'CF', 'CFG', 'CHPT', 'CHTR', 'CHWY', 'CIFR', 'CL', 'CLF', 'CLS', 'CMCSA', 'COIN', 'COMP', 'COP', 'COST', 'CRDO', 'CRSP', 'CRWD', 'CSCO', 'CSX', 'CUBI', 'CVNA', 'CVX', 'CX', 'DD', 'DDOG', 'DE', 'DELL', 'DHI', 'DIS', 'DJT', 'DKNG', 'DLR', 'DOCU', 'DOW', 'DUOL', 'DVN', 'EA', 'EBAY', 'ECL', 'EDIT', 'EOG', 'EQIX', 'EQR', 'ETN', 'ETSY', 'EW', 'EXPE', 'EXR', 'FCEL', 'FCF', 'FCX', 'FDX', 'FITB', 'FLEX', 'FLYW', 'FMC', 'FNB', 'FOXA', 'FSLR', 'GD', 'GE', 'GEV', 'GILD', 'GIS', 'GLD', 'GLW', 'GOOGL', 'GPRO', 'GS', 'GSK', 'HAL', 'HAPN', 'HBAN', 'HD', 'HOMB', 'HON', 'HOOD', 'HUT', 'IEFA', 'ILMN', 'INTC', 'IREN', 'ISRG', 'IWM', 'JD', 'JETS', 'JMIA', 'JNJ', 'JPM', 'KEY', 'KKR', 'KLAC', 'KMB', 'KO', 'KRE', 'LCID', 'LEN', 'LI', 'LIN', 'LITE', 'LLY', 'LMT', 'LOT', 'LOW', 'LPRO', 'LRCX', 'LYV', 'MA', 'MAA', 'MARA', 'MCHP', 'MDB', 'MDLZ', 'MDT', 'MELI', 'META', 'MLM', 'MMM', 'MNST', 'MOD', 'MOS', 'MP', 'MRNA', 'MRVL', 'MS', 'MSFT', 'MTB', 'MTCH', 'MU', 'NEM', 'NET', 'NFLX', 'NIO', 'NOC', 'NOW', 'NSC', 'NTLA', 'NTR', 'NTRS', 'NU', 'NUE', 'NVDA', 'NVO', 'NWSA', 'NXPI', 'O', 'OIH', 'OKTA', 'OMF', 'ON', 'OPEN', 'OPFI', 'OXY', 'OZK', 'PAGS', 'PANW', 'PARA', 'PAYS', 'PDD', 'PEP', 'PFE', 'PG', 'PHM', 'PINS', 'PLD', 'PLTR', 'PLUG', 'PSA', 'PSNY', 'PWR', 'PYPL', 'QCOM', 'QQQ', 'QS', 'RDDT', 'REGN', 'RF', 'RIOT', 'RIVN', 'RKLB', 'ROKU', 'RSG', 'RTX', 'RUM', 'RUN', 'SBAC', 'SBUX', 'SCHW', 'SE', 'SEDG', 'SHOP', 'SHW', 'SIFY', 'SLB', 'SMCI', 'SMH', 'SNAP', 'SNOW', 'SNPS', 'SNY', 'SOFI', 'SOXX', 'SPG', 'SPWR', 'STLD', 'STNE', 'STT', 'SYK', 'T', 'TAK', 'TEAM', 'TELFY', 'TEM', 'TER', 'TFC', 'TGT', 'TMDX', 'TMUS', 'TRIP', 'TROW', 'TSLA', 'TSM', 'TTWO', 'TWLO', 'TXN', 'UMBF', 'UNG', 'UNP', 'UPS', 'UPST', 'USO', 'V', 'VEA', 'VICI', 'VLY', 'VMC', 'VNQ', 'VOD', 'VRT', 'VRTX', 'VST', 'VWO', 'VZ', 'W', 'WAY', 'WBD', 'WBS', 'WDAY', 'WFC', 'WM', 'WMT', 'WULF', 'WY', 'XBI', 'XLB', 'XLE', 'XLF', 'XLI', 'XLK', 'XLP', 'XLRE', 'XLU', 'XLV', 'XLY', 'XOM', 'XPEV', 'XYZ', 'Z', 'ZBH', 'ZG', 'ZION', 'ZM', 'ZS']
if len(DEFAULT_UNIVERSE) != 335:
    raise RuntimeError(f"Universo inválido: {len(DEFAULT_UNIVERSE)}; se esperaban 335")
UNIVERSE = list(dict.fromkeys(DEFAULT_UNIVERSE))


def features(df):
    c = pd.to_numeric(df["Close"], errors="coerce")
    o = pd.to_numeric(df["Open"], errors="coerce")
    x = df.copy()
    for w in MOM_WINDOWS:
        x[f"R{w}"] = c / c.shift(w) - 1
    for h in HORIZONS:
        x[f"FWD{h}"] = c.shift(-h) / o.shift(-1) - 1
    return x


def load(t):
    try:
        r = yf.download(
            t, period=PERIOD, auto_adjust=True,
            progress=False, actions=False, threads=False
        )
        if r is None or r.empty:
            return None, "EMPTY"
        if isinstance(r.columns, pd.MultiIndex):
            r.columns = r.columns.get_level_values(0)
        need = ["Open", "High", "Low", "Close", "Volume"]
        if not all(c in r.columns for c in need):
            return None, "COLUMNS"
        r = r[need].copy()
        r.index = pd.to_datetime(r.index).tz_localize(None)
        r = r[~r.index.duplicated()].sort_index()
        r = r.dropna(subset=["Open", "High", "Low", "Close"])
        if len(r) < 300:
            return None, "HISTORY"
        return features(r), "OK"
    except Exception as e:
        return None, type(e).__name__


def usable_dates(datasets, h):
    required = [f"R{w}" for w in MOM_WINDOWS]
    dates = sorted(set().union(*[set(d.index) for d in datasets.values()]))
    usable = []
    for d in dates:
        n = 0
        for df in datasets.values():
            if d not in df.index:
                continue
            z = df.loc[d]
            if all(np.isfinite(z.get(f, np.nan)) for f in required) and np.isfinite(z.get(f"FWD{h}", np.nan)):
                n += 1
        if n >= MIN_CROSS_SECTION:
            usable.append(d)

    # Same non-overlapping OOS calendar construction used in Phase 6.
    selected = []
    last = -10**9
    for i, d in enumerate(usable):
        if i - last >= h + EMBARGO:
            selected.append(d)
            last = i
    return selected


def cross(datasets, date, h):
    required = [f"R{w}" for w in MOM_WINDOWS]
    rows = []
    for t, df in datasets.items():
        if date not in df.index:
            continue
        r = df.loc[date]
        if not all(np.isfinite(r.get(f, np.nan)) for f in required):
            continue
        y = r.get(f"FWD{h}", np.nan)
        if not np.isfinite(y):
            continue
        vals = {f: float(r[f]) for f in required}
        vals.update(Ticker=t, Date=date, ForwardReturn=float(y))
        rows.append(vals)
    return pd.DataFrame(rows)


def build_oos(datasets, h):
    rows = []
    dates = usable_dates(datasets, h)
    for dt in dates:
        g = cross(datasets, dt, h)
        if len(g) < MIN_CROSS_SECTION:
            continue
        for c in [f"R{w}" for w in MOM_WINDOWS]:
            g[c + "_RANK"] = g[c].rank(pct=True, method="average")
        g["LTM_COMPOSITE"] = g[[f"R{w}_RANK" for w in MOM_WINDOWS]].mean(axis=1)
        rows.append(g[["Date", "Ticker", "LTM_COMPOSITE", "ForwardReturn"]])
    if not rows:
        return pd.DataFrame(), []
    d = pd.concat(rows, ignore_index=True)
    all_dates = sorted(pd.to_datetime(d["Date"]).unique())
    oos_dates = all_dates[DISCOVERY_DATES + EMBARGO:]
    return d[d["Date"].isin(oos_dates)].copy(), oos_dates


def decile_table(g):
    z = g[["Ticker", "LTM_COMPOSITE", "ForwardReturn"]].dropna().copy()
    z["_decile"] = pd.qcut(
        z["LTM_COMPOSITE"].rank(method="first"), 10, labels=False
    ) + 1
    m = z.groupby("_decile", observed=True)["ForwardReturn"].agg(["mean", "median", "count"])
    m.index.name = "Decile"
    return m.reset_index()


def rank_group(g, frac):
    z = g[["Ticker", "LTM_COMPOSITE", "ForwardReturn"]].dropna().copy()
    n = max(1, int(np.floor(len(z) * frac)))
    z = z.sort_values("LTM_COMPOSITE", ascending=False)
    top = z.iloc[:n]
    bottom = z.iloc[-n:]
    return top, bottom


def daily_metrics(g, h):
    z = g.dropna(subset=["LTM_COMPOSITE", "ForwardReturn"]).copy()
    if len(z) < MIN_CROSS_SECTION:
        return None

    ic = spearmanr(z["LTM_COMPOSITE"], z["ForwardReturn"]).statistic
    dtab = decile_table(z)
    dmeans = dtab["mean"].to_numpy(float)
    monotonic = np.corrcoef(np.arange(1, 11), dmeans)[0, 1]

    top10, bot10 = rank_group(z, 0.10)
    top20, bot20 = rank_group(z, 0.20)
    top30, bot30 = rank_group(z, 0.30)

    return {
        "Horizon": h,
        "Date": z["Date"].iloc[0],
        "N": len(z),
        "IC": float(ic),
        "D10MinusD1": float(dmeans[-1] - dmeans[0]),
        "MonotonicD": float(monotonic),
        "Top10Mean": float(top10["ForwardReturn"].mean()),
        "Top20Mean": float(top20["ForwardReturn"].mean()),
        "Top30Mean": float(top30["ForwardReturn"].mean()),
        "Bottom10Mean": float(bot10["ForwardReturn"].mean()),
        "Bottom20Mean": float(bot20["ForwardReturn"].mean()),
        "Bottom30Mean": float(bot30["ForwardReturn"].mean()),
        "LongShort10": float(top10["ForwardReturn"].mean() - bot10["ForwardReturn"].mean()),
        "LongShort20": float(top20["ForwardReturn"].mean() - bot20["ForwardReturn"].mean()),
        "LongShort30": float(top30["ForwardReturn"].mean() - bot30["ForwardReturn"].mean()),
    }


def membership_turnover(oos_data, frac):
    # One-way turnover = 1 - overlap(old,new)/target_size.
    # The corresponding round-trip transaction drag is approximately
    # 2 * turnover * cost for a long-only equal-weight portfolio.
    rows = []
    previous = None
    for dt, g in oos_data.groupby("Date", sort=True):
        z = g.dropna(subset=["LTM_COMPOSITE"]).sort_values(
            "LTM_COMPOSITE", ascending=False
        )
        n = max(1, int(np.floor(len(z) * frac)))
        current = set(z.head(n)["Ticker"])
        if previous is not None:
            target = max(1, min(len(previous), len(current)))
            overlap = len(previous & current)
            one_way = 1.0 - overlap / target
            rows.append({
                "Date": dt,
                "TopPct": frac,
                "PrevN": len(previous),
                "CurrentN": len(current),
                "Overlap": overlap,
                "OneWayTurnover": float(one_way),
            })
        previous = current
    return pd.DataFrame(rows)


def net_from_turnover(gross, turnover, cost_bps):
    if pd.isna(turnover):
        return np.nan
    return float(gross - 2.0 * turnover * cost_bps / 10000.0)


# ---------------------------------------------------------------------
# RUN
# ---------------------------------------------------------------------
print("=" * 78)
print("NUEVA ESTRATEGIA — FASE 7: ROBUSTEZ ECONÓMICA DE LONG-TERM MOMENTUM")
print(f"RUN_ID: {RUN_ID}")
print(f"Tickers configurados: {len(UNIVERSE)}")
print(f"Horizons: {HORIZONS} | Windows: {MOM_WINDOWS}")
print("Hipótesis congelada: LTM_COMPOSITE = promedio simple de ranks R100/R120/R140/R160")
print("NO cartera / NO Kelly / NO producción")
print("=" * 78)

datasets = {}
failures = []
for i, t in enumerate(UNIVERSE, 1):
    df, status = load(t)
    if df is not None:
        datasets[t] = df
    else:
        failures.append({"Ticker": t, "Error": status})
    if i % 25 == 0 or i == len(UNIVERSE):
        print(f"[{i}/{len(UNIVERSE)}] OK={len(datasets)} FAIL={len(failures)}")

all_data = []
daily_rows = []

for h in HORIZONS:
    d, oos_dates = build_oos(datasets, h)
    if d.empty:
        print(f"H{h}: SIN DATOS OOS")
        continue

    print(
        f"H{h}: {len(oos_dates)} fechas OOS | "
        f"Discovery={DISCOVERY_DATES} | Embargo={EMBARGO}"
    )
    all_data.append(d.assign(Horizon=h))

    for dt, g in d.groupby("Date", sort=True):
        m = daily_metrics(g.assign(Date=dt), h)
        if m is not None:
            daily_rows.append(m)

by_date = pd.DataFrame(daily_rows)
if by_date.empty:
    raise RuntimeError("No hay métricas OOS para Fase 7.")

# ---------------------------------------------------------------------
# A) DECILE MONOTONICITY
# ---------------------------------------------------------------------
decile_rows = []
for h in HORIZONS:
    d = next((x for x in all_data if int(x["Horizon"].iloc[0]) == h), None)
    if d is None:
        continue
    for dt, g in d.groupby("Date", sort=True):
        tab = decile_table(g)
        tab["Horizon"] = h
        tab["Date"] = dt
        decile_rows.append(tab)

deciles = pd.concat(decile_rows, ignore_index=True)

# ---------------------------------------------------------------------
# B/C/D) TOP-N, LONG-SHORT, H20 vs H40
# ---------------------------------------------------------------------
economic_summary = (
    by_date.groupby("Horizon")
    .agg(
        Dates=("IC", "size"),
        MeanIC=("IC", "mean"),
        MedianIC=("IC", "median"),
        PctPositiveIC=("IC", lambda x: float((x > 0).mean())),
        MeanD10MinusD1=("D10MinusD1", "mean"),
        MedianD10MinusD1=("D10MinusD1", "median"),
        PctPositiveD10MinusD1=("D10MinusD1", lambda x: float((x > 0).mean())),
        MeanMonotonicD=("MonotonicD", "mean"),
        MeanTop10=("Top10Mean", "mean"),
        MeanTop20=("Top20Mean", "mean"),
        MeanTop30=("Top30Mean", "mean"),
        MeanBottom10=("Bottom10Mean", "mean"),
        MeanBottom20=("Bottom20Mean", "mean"),
        MeanBottom30=("Bottom30Mean", "mean"),
        MeanLongShort10=("LongShort10", "mean"),
        MeanLongShort20=("LongShort20", "mean"),
        MeanLongShort30=("LongShort30", "mean"),
    )
    .reset_index()
)

# ---------------------------------------------------------------------
# E) PREDEFINED LEAVE-ONE-WINDOW-OUT SENSITIVITY
# Every one of the four variants is reported. None is selected.
# ---------------------------------------------------------------------
loo_rows = []
for h in HORIZONS:
    d = next((x for x in all_data if int(x["Horizon"].iloc[0]) == h), None)
    if d is None:
        continue
    for omitted in MOM_WINDOWS:
        keep = [w for w in MOM_WINDOWS if w != omitted]
        for dt, g in d.groupby("Date", sort=True):
            # g only contains the frozen composite and ForwardReturn at this
            # stage. Rebuild the leave-one-window-out scores directly from the
            # original ticker datasets for this date; otherwise R120/R140/R160
            # are not present in g.
            rows = []
            for t in g["Ticker"]:
                df_t = datasets.get(t)
                if df_t is None or dt not in df_t.index:
                    continue
                r = df_t.loc[dt]
                vals = {"Ticker": t, "ForwardReturn": g.loc[g["Ticker"] == t, "ForwardReturn"].iloc[0]}
                ok = True
                for w in keep:
                    val = r.get(f"R{w}", np.nan)
                    if not np.isfinite(val):
                        ok = False
                        break
                    vals[f"R{w}"] = float(val)
                if ok and np.isfinite(vals["ForwardReturn"]):
                    rows.append(vals)

            z = pd.DataFrame(rows).dropna().copy()
            if len(z) < MIN_CROSS_SECTION:
                continue
            ranks = [z[f"R{w}"].rank(pct=True, method="average") for w in keep]
            z["LOO_SCORE"] = pd.concat(ranks, axis=1).mean(axis=1)
            ic = spearmanr(z["LOO_SCORE"], z["ForwardReturn"]).statistic
            q = pd.qcut(z["LOO_SCORE"].rank(method="first"), 5, labels=False) + 1
            qm = z.assign(_q=q).groupby("_q", observed=True)["ForwardReturn"].mean()
            loo_rows.append({
                "Horizon": h,
                "OmittedWindow": omitted,
                "Date": dt,
                "IC": float(ic),
                "Q5MinusQ1": float(qm.iloc[-1] - qm.iloc[0]),
            })

loo_by_date = pd.DataFrame(loo_rows)
loo_summary = (
    loo_by_date.groupby(["Horizon", "OmittedWindow"])
    .agg(
        Dates=("IC", "size"),
        MeanIC=("IC", "mean"),
        MedianIC=("IC", "median"),
        PctPositiveIC=("IC", lambda x: float((x > 0).mean())),
        MeanQ5MinusQ1=("Q5MinusQ1", "mean"),
        PctPositiveQ5MinusQ1=("Q5MinusQ1", lambda x: float((x > 0).mean())),
    )
    .reset_index()
)

# ---------------------------------------------------------------------
# F) TURNOVER + COST SENSITIVITY
# ---------------------------------------------------------------------
turnover_rows = []
for h in HORIZONS:
    d = next((x for x in all_data if int(x["Horizon"].iloc[0]) == h), None)
    if d is None:
        continue
    for frac in TOP_PCTS:
        tdf = membership_turnover(d, frac)
        if tdf.empty:
            continue
        tdf["Horizon"] = h
        turnover_rows.append(tdf)

turnover = pd.concat(turnover_rows, ignore_index=True)

cost_rows = []
for h in HORIZONS:
    bd = by_date[by_date.Horizon == h].copy()
    td = turnover[turnover.Horizon == h].copy()
    for frac, col in [(0.10, "Top10Mean"), (0.20, "Top20Mean"), (0.30, "Top30Mean")]:
        tt = td[td.TopPct == frac]
        avg_turn = float(tt.OneWayTurnover.mean()) if not tt.empty else np.nan
        gross = float(bd[col].mean())
        for bps in COST_BPS:
            cost_rows.append({
                "Horizon": h,
                "TopPct": frac,
                "CostBps": bps,
                "GrossMeanReturn": gross,
                "MeanOneWayTurnover": avg_turn,
                "EstimatedRoundTripCostDrag": float(2 * avg_turn * bps / 10000.0),
                "NetMeanReturnDiagnostic": net_from_turnover(gross, avg_turn, bps),
            })

cost_sensitivity = pd.DataFrame(cost_rows)

# ---------------------------------------------------------------------
# PREDEFINED VERDICT — descriptive only; no production selection.
# H20/H40 are both retained for comparison.
# ---------------------------------------------------------------------
verdict_rows = []
for h in HORIZONS:
    s = economic_summary[economic_summary.Horizon == h].iloc[0]
    verdict_rows.append({
        "Horizon": h,
        "MeanICPositive": bool(s.MeanIC > 0),
        "D10MinusD1Positive": bool(s.MeanD10MinusD1 > 0),
        "Top10GrossPositive": bool(s.MeanTop10 > 0),
        "Top20GrossPositive": bool(s.MeanTop20 > 0),
        "Top30GrossPositive": bool(s.MeanTop30 > 0),
        "LongShort20Positive": bool(s.MeanLongShort20 > 0),
        "AllCoreEconomicChecksPositive": bool(
            s.MeanIC > 0 and
            s.MeanD10MinusD1 > 0 and
            s.MeanTop20 > 0 and
            s.MeanLongShort20 > 0
        ),
    })

verdict = pd.DataFrame(verdict_rows)

# ---------------------------------------------------------------------
# OUTPUT
# ---------------------------------------------------------------------
print("\n" + "=" * 78)
print("FASE 7 — RESUMEN ECONÓMICO OOS")
print("=" * 78)
print(economic_summary.to_string(index=False))

print("\n" + "=" * 78)
print("FASE 7 — SENSIBILIDAD LEAVE-ONE-WINDOW-OUT")
print("=" * 78)
print(loo_summary.to_string(index=False))

print("\n" + "=" * 78)
print("FASE 7 — TURNOVER PROMEDIO")
print("=" * 78)
print(
    turnover.groupby(["Horizon", "TopPct"])
    .agg(
        Observations=("OneWayTurnover", "size"),
        MeanOneWayTurnover=("OneWayTurnover", "mean"),
        MedianOneWayTurnover=("OneWayTurnover", "median"),
    )
    .reset_index()
    .to_string(index=False)
)

print("\n" + "=" * 78)
print("FASE 7 — COSTOS 10/20/50 BPS")
print("=" * 78)
print(cost_sensitivity.to_string(index=False))

print("\n" + "=" * 78)
print("FASE 7 — VEREDICTO DESCRIPTIVO")
print("=" * 78)
print(verdict.to_string(index=False))

by_date.to_csv(ART / "phase7_economic_by_date.csv", index=False)
economic_summary.to_csv(ART / "phase7_economic_summary.csv", index=False)
deciles.to_csv(ART / "phase7_deciles_by_date.csv", index=False)
loo_by_date.to_csv(ART / "phase7_loo_by_date.csv", index=False)
loo_summary.to_csv(ART / "phase7_loo_summary.csv", index=False)
turnover.to_csv(ART / "phase7_turnover.csv", index=False)
cost_sensitivity.to_csv(ART / "phase7_cost_sensitivity.csv", index=False)
verdict.to_csv(ART / "phase7_verdict.csv", index=False)
pd.DataFrame(failures).to_csv(ART / "phase7_failures.csv", index=False)

audit = {
    "RUN_ID": RUN_ID,
    "ConfiguredTickers": len(UNIVERSE),
    "ValidTickers": len(datasets),
    "Failures": len(failures),
    "Horizons": len(HORIZONS),
    "MomentumWindows": len(MOM_WINDOWS),
    "TopPercentages": len(TOP_PCTS),
    "CostScenariosBps": len(COST_BPS),
    "DiscoveryDates": DISCOVERY_DATES,
    "Embargo": EMBARGO,
    "RowsByDate": len(by_date),
    "RowsDeciles": len(deciles),
    "RowsLOO": len(loo_by_date),
    "RowsTurnover": len(turnover),
    "RowsCost": len(cost_sensitivity),
    "NoNaNCore": bool(
        by_date[["IC", "D10MinusD1", "Top20Mean", "LongShort20"]]
        .notna().all().all()
    ),
    "Status": "PASS",
}
pd.DataFrame([audit]).to_csv(ART / "phase7_audit.csv", index=False)

print("\n" + "=" * 78)
print("AUDITORÍA")
print("=" * 78)
for k, v in audit.items():
    print(f"{k}: {v}")
print("NO HAY CARTERA NI REGLAS DE ENTRADA/SALIDA EN ESTA FASE.")

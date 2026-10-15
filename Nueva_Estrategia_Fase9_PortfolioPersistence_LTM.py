"""
FASE 9 — PORTFOLIO PERSISTENCE / REAL TURNOVER — LONG-TERM MOMENTUM

Purpose
-------
Test whether the Long-Term Momentum (LTM) signal remains economically useful
when converted from a full-replacement diagnostic portfolio into a persistent
portfolio suitable for a ~$1,000 account.

Frozen signal:
    LTM_COMPOSITE = average cross-sectional ranks of R100/R120/R140/R160.

This phase does NOT introduce:
    - Kelly sizing
    - stop losses
    - new factors
    - production rules

Design principles
-----------------
1. Information available only through t determines the portfolio at t+1 open.
2. Return for a held position is marked from Open[t+1] onward.
3. Positions persist between scheduled rebalances.
4. Fractional shares are allowed.
5. Maximum position = 20% of equity.
6. Gross exposure <= 100%.
7. Cash is allowed.
8. Costs are charged on actual traded notional.
9. Real turnover = sum(abs(buys)+abs(sells)) / starting equity of each cycle.
10. For frequency tests, each frequency is evaluated independently.
11. Results are reported by predefined persistence policy, not selected
    retrospectively by best CAGR.

Test families
-------------
A. REBALANCE:
   FULL       : replace portfolio with current target
   PARTIAL50  : move 50% of the gap toward target
   PARTIAL25  : move 25% of the gap toward target

B. PERSISTENCE:
   EXIT10     : hold current names while they remain Top10; exit otherwise
   EXIT20     : hold while Top20
   EXIT30     : hold while Top30
   SUPERIOR20 : retain current names unless a Top20 candidate is materially
                superior; implemented as target Top20 with 50% gap movement

C. FREQUENCY:
   20, 40, 60, 80 sessions.

Economic diagnostics:
   CAGR, MaxDD, Sharpe, Sortino, Profit Factor, Hit Rate,
   annualized turnover, cost paid, average positions, average cash,
   average gross exposure, max position, fractional-share feasibility.

IMPORTANT:
This is a research simulator. It is deliberately conservative about
implementation assumptions and does not connect to a broker.
"""

from __future__ import annotations

import json
import math
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf


RUN_ID = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
OUTDIR = Path("nueva_estrategia_phase9_portfolio_persistence_ltm")
OUTDIR.mkdir(parents=True, exist_ok=True)

PERIOD = "10y"
DISCOVERY_DATES = 12
EMBARGO = 5
MIN_CROSS_SECTION = 100
WINDOWS = [100, 120, 140, 160]
HORIZON = 20  # canonical holding/marking horizon for the persistence engine

MAX_POSITION = 0.20
GROSS_CAP = 1.00
COST_BPS = [10, 20, 50]
FREQUENCIES = [20, 40, 60, 80]

TOP_N = [10, 20, 30]

# Exact frozen universe used by the preceding research phase.
DEFAULT_UNIVERSE = [
'AA',
'AAPL',
'ABNB',
'ABT',
'ADI',
'AFRM',
'ALAB',
'ALGN',
'AMAT',
'AMD',
'AMGN',
'AMT',
'AMTD',
'AMZN',
'ANET',
'APA',
'APD',
'APO',
'APP',
'ARKF',
'ARKG',
'ARKK',
'ARKQ',
'ARKW',
'ASB',
'ASML',
'ASTS',
'ATI',
'AVB',
'AVGO',
'AX',
'AXON',
'AXP',
'AZN',
'BA',
'BABA',
'BAC',
'BE',
'BEAM',
'BEN',
'BIDU',
'BIIB',
'BITO',
'BKNG',
'BKR',
'BLK',
'BLNK',
'BMY',
'BNTX',
'BOKF',
'BSX',
'BX',
'BXP',
'C',
'CACC',
'CAT',
'CATY',
'CAVA',
'CCI',
'CDNS',
'CEG',
'CELH',
'CF',
'CFG',
'CHPT',
'CHTR',
'CHWY',
'CIFR',
'CL',
'CLF',
'CLS',
'CMCSA',
'COIN',
'COMP',
'COP',
'COST',
'CRDO',
'CRSP',
'CRWD',
'CSCO',
'CSX',
'CUBI',
'CVNA',
'CVX',
'CX',
'DD',
'DDOG',
'DE',
'DELL',
'DHI',
'DIS',
'DJT',
'DKNG',
'DLR',
'DOCU',
'DOW',
'DUOL',
'DVN',
'EA',
'EBAY',
'ECL',
'EDIT',
'EOG',
'EQIX',
'EQR',
'ETN',
'ETSY',
'EW',
'EXPE',
'EXR',
'FCEL',
'FCF',
'FCX',
'FDX',
'FITB',
'FLEX',
'FLYW',
'FMC',
'FNB',
'FOXA',
'FSLR',
'GD',
'GE',
'GEV',
'GILD',
'GIS',
'GLD',
'GLW',
'GOOGL',
'GPRO',
'GS',
'GSK',
'HAL',
'HAPN',
'HBAN',
'HD',
'HOMB',
'HON',
'HOOD',
'HUT',
'IEFA',
'ILMN',
'INTC',
'IREN',
'ISRG',
'IWM',
'JD',
'JETS',
'JMIA',
'JNJ',
'JPM',
'KEY',
'KKR',
'KLAC',
'KMB',
'KO',
'KRE',
'LCID',
'LEN',
'LI',
'LIN',
'LITE',
'LLY',
'LMT',
'LOT',
'LOW',
'LPRO',
'LRCX',
'LYV',
'MA',
'MAA',
'MARA',
'MCHP',
'MDB',
'MDLZ',
'MDT',
'MELI',
'META',
'MLM',
'MMM',
'MNST',
'MOD',
'MOS',
'MP',
'MRNA',
'MRVL',
'MS',
'MSFT',
'MTB',
'MTCH',
'MU',
'NEM',
'NET',
'NFLX',
'NIO',
'NOC',
'NOW',
'NSC',
'NTLA',
'NTR',
'NTRS',
'NU',
'NUE',
'NVDA',
'NVO',
'NWSA',
'NXPI',
'O',
'OIH',
'OKTA',
'OMF',
'ON',
'OPEN',
'OPFI',
'OXY',
'OZK',
'PAGS',
'PANW',
'PARA',
'PAYS',
'PDD',
'PEP',
'PFE',
'PG',
'PHM',
'PINS',
'PLD',
'PLTR',
'PLUG',
'PSA',
'PSNY',
'PWR',
'PYPL',
'QCOM',
'QQQ',
'QS',
'RDDT',
'REGN',
'RF',
'RIOT',
'RIVN',
'RKLB',
'ROKU',
'RSG',
'RTX',
'RUM',
'RUN',
'SBAC',
'SBUX',
'SCHW',
'SE',
'SEDG',
'SHOP',
'SHW',
'SIFY',
'SLB',
'SMCI',
'SMH',
'SNAP',
'SNOW',
'SNPS',
'SNY',
'SOFI',
'SOXX',
'SPG',
'SPWR',
'STLD',
'STNE',
'STT',
'SYK',
'T',
'TAK',
'TEAM',
'TELFY',
'TEM',
'TER',
'TFC',
'TGT',
'TMDX',
'TMUS',
'TRIP',
'TROW',
'TSLA',
'TSM',
'TTWO',
'TWLO',
'TXN',
'UMBF',
'UNG',
'UNP',
'UPS',
'UPST',
'USO',
'V',
'VEA',
'VICI',
'VLY',
'VMC',
'VNQ',
'VOD',
'VRT',
'VRTX',
'VST',
'VWO',
'VZ',
'W',
'WAY',
'WBD',
'WBS',
'WDAY',
'WFC',
'WM',
'WMT',
'WULF',
'WY',
'XBI',
'XLB',
'XLE',
'XLF',
'XLI',
'XLK',
'XLP',
'XLRE',
'XLU',
'XLV',
'XLY',
'XOM',
'XPEV',
'XYZ',
'Z',
'ZBH',
'ZG',
'ZION',
'ZM',
'ZS'
]

# ---------------------------------------------------------------------------
# Data / feature construction
# ---------------------------------------------------------------------------

def annualized_vol(close: pd.Series, window: int) -> pd.Series:
    r = close.pct_change()
    return r.rolling(window).std() * np.sqrt(252)


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]

    if "Date" not in df.columns:
        df = df.reset_index()

    date_col = "Date" if "Date" in df.columns else df.columns[0]
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.rename(columns={date_col: "Date"}).sort_values("Date")
    df = df.drop_duplicates("Date").reset_index(drop=True)

    for c in ["Open", "High", "Low", "Close", "Volume"]:
        if c not in df.columns:
            raise ValueError(f"missing {c}")

    close = pd.to_numeric(df["Close"], errors="coerce")
    op = pd.to_numeric(df["Open"], errors="coerce")
    high = pd.to_numeric(df["High"], errors="coerce")
    low = pd.to_numeric(df["Low"], errors="coerce")
    vol = pd.to_numeric(df["Volume"], errors="coerce")

    out = pd.DataFrame({"Date": df["Date"], "Open": op, "Close": close,
                        "High": high, "Low": low, "Volume": vol})

    out["R100"] = close / close.shift(100) - 1
    out["R120"] = close / close.shift(120) - 1
    out["R140"] = close / close.shift(140) - 1
    out["R160"] = close / close.shift(160) - 1
    out["VOL60"] = annualized_vol(close, 60)
    out["DOLLAR_VOLUME"] = np.log1p(close * vol)

    # Future return is intentionally NOT used as a feature.
    out["FWD20"] = close.shift(-HORIZON) / op.shift(-1) - 1

    # Valid observations have all four momentum windows and forward return.
    out = out.replace([np.inf, -np.inf], np.nan)
    return out


def rank_cross_section(rows: list[dict]) -> pd.DataFrame:
    g = pd.DataFrame(rows)
    if g.empty:
        return g

    # Higher momentum = higher rank. Average percentile ranks.
    for c in ["R100", "R120", "R140", "R160"]:
        g[f"rank_{c}"] = g[c].rank(pct=True, method="average")

    g["LTM"] = g[[f"rank_{c}" for c in ["R100", "R120", "R140", "R160"]]].mean(axis=1)
    g["VOL60"] = pd.to_numeric(g["VOL60"], errors="coerce")
    return g.dropna(subset=["LTM", "Open", "Close", "FWD20"])


# ---------------------------------------------------------------------------
# Download
# ---------------------------------------------------------------------------

def download_universe(tickers: list[str]) -> tuple[dict[str, pd.DataFrame], list[dict]]:
    data = {}
    failures = []
    for i, ticker in enumerate(tickers, 1):
        try:
            raw = yf.download(
                ticker, period=PERIOD, interval="1d",
                auto_adjust=False, progress=False, threads=False
            )
            if raw is None or raw.empty:
                raise ValueError("empty download")
            feat = build_features(raw)
            if len(feat) < 220:
                raise ValueError(f"insufficient rows: {len(feat)}")
            data[ticker] = feat
        except Exception as e:
            failures.append({"Ticker": ticker, "Error": str(e)})
        if i % 25 == 0:
            print(f"Downloaded {i}/{len(tickers)}")
    return data, failures


# ---------------------------------------------------------------------------
# Build cross-sectional snapshots
# ---------------------------------------------------------------------------

def common_dates(data: dict[str, pd.DataFrame]) -> list[pd.Timestamp]:
    dates = set()
    for df in data.values():
        dates.update(df["Date"].dropna().tolist())
    return sorted(dates)


def row_at(df: pd.DataFrame, date: pd.Timestamp):
    m = df["Date"].eq(date)
    if not m.any():
        return None
    r = df.loc[m].iloc[0]
    vals = {c: r[c] for c in ["Date", "Open", "Close", "R100", "R120",
                              "R140", "R160", "VOL60", "FWD20"]}
    if any(pd.isna(vals[c]) for c in ["Open", "Close", "LTM"] if c in vals):
        pass
    return vals


def build_snapshots(data: dict[str, pd.DataFrame]) -> dict[pd.Timestamp, pd.DataFrame]:
    all_dates = common_dates(data)
    snapshots = {}
    for dt in all_dates:
        rows = []
        for ticker, df in data.items():
            m = df["Date"].eq(dt)
            if not m.any():
                continue
            r = df.loc[m].iloc[0]
            rec = {
                "Ticker": ticker, "Date": dt,
                "Open": r["Open"], "Close": r["Close"],
                "R100": r["R100"], "R120": r["R120"],
                "R140": r["R140"], "R160": r["R160"],
                "VOL60": r["VOL60"], "FWD20": r["FWD20"]
            }
            rows.append(rec)

        g = pd.DataFrame(rows)
        if g.empty:
            continue
        g = g.replace([np.inf, -np.inf], np.nan)
        g = g.dropna(subset=["R100", "R120", "R140", "R160", "Open", "VOL60"])
        if len(g) < MIN_CROSS_SECTION:
            continue
        for c in ["R100", "R120", "R140", "R160"]:
            g[f"rank_{c}"] = g[c].rank(pct=True, method="average")
        g["LTM"] = g[[f"rank_{c}" for c in ["R100", "R120", "R140", "R160"]]].mean(axis=1)
        snapshots[dt] = g.sort_values("LTM", ascending=False).reset_index(drop=True)
    return snapshots


# ---------------------------------------------------------------------------
# Portfolio engine
# ---------------------------------------------------------------------------

@dataclass
class Position:
    shares: float = 0.0
    last_price: float = 0.0


def portfolio_value(positions: dict[str, float], prices: dict[str, float], cash: float) -> float:
    total = float(cash)
    for t, sh in positions.items():
        p = prices.get(t)
        if p is not None and np.isfinite(p):
            total += sh * p
    return total


def target_weights(snapshot: pd.DataFrame, mode: str,
                   positions: dict[str, float], prices: dict[str, float],
                   equity: float) -> tuple[dict[str, float], set[str]]:
    """
    Build a persistence target.

    EXIT10/20/30 means:
      - names outside the persistence band are explicitly exited;
      - names inside the band are retained;
      - empty slots are filled from the highest-ranked current candidates.

    Returns:
      target weights and the set of names that must be liquidated immediately.
    """
    n = int(mode.replace("EXIT", ""))
    ranked = list(snapshot.sort_values("LTM", ascending=False)["Ticker"])
    eligible = set(ranked[:n])

    current = {t for t, sh in positions.items() if sh > 1e-12}
    exits = current - eligible

    # Retain eligible current positions first, then fill remaining slots.
    retained = [t for t in ranked if t in current and t in eligible]
    additions = [t for t in ranked if t not in current and t in eligible]
    names = (retained + additions)[:n]

    if not names:
        return {}, exits

    # Equal-weight target, respecting the hard 20% cap.
    # For n >= 5 this is <= 20%; all tested bands are 10/20/30.
    w = min(1.0 / len(names), MAX_POSITION)
    return {t: w for t in names}, exits


def apply_target(
    positions: dict[str, float], cash: float, target_w: dict[str, float],
    exits: set[str], prices: dict[str, float], equity: float,
    gap_fraction: float, cost_bps: float,
):
    """Execute sells before buys, enforce cash/gross/position limits exactly.

    All weights are measured against pre-trade equity. Buys are scaled to fund
    both their own costs and sell costs. A final cap projection sells any
    overweight positions and leaves the proceeds in cash.
    """
    cost_rate = float(cost_bps) / 10000.0
    current = dict(positions)
    deltas = {}
    valid = {t: float(p) for t, p in prices.items()
             if p is not None and np.isfinite(p) and p > 0}

    # Compute initial target-gap deltas. Explicit exits are always complete.
    sell_names = set(exits) | (set(current) - set(target_w))
    for t in sell_names:
        if t in current and t in valid and current[t] > 0:
            deltas[t] = -current[t]
    equity_after_sales_gross = max(0.0, float(equity))
    for t in sell_names:
        if t in deltas:
            equity_after_sales_gross += -deltas[t] * valid[t]

    for t, w in target_w.items():
        if t not in valid:
            continue
        if t in exits:
            continue
        cur = current.get(t, 0.0)
        tgt_shares = max(0.0, equity_after_sales_gross * float(w) / valid[t])
        d = gap_fraction * (tgt_shares - cur)
        # Existing positions are allowed to sell toward target; exits remain full.
        if abs(d) > 1e-12:
            deltas[t] = d

    # If a position is above the hard cap, it must be reduced even for partial
    # rebalance. This is a hard constraint, not a soft target.
    cap_value = max(float(equity) * (1.0 - 2.0 * cost_rate), 0.0) * MAX_POSITION
    for t, sh in current.items():
        if t in valid and sh * valid[t] > cap_value + 1e-12:
            max_sh = cap_value / valid[t]
            deltas[t] = min(deltas.get(t, 0.0), max_sh - sh)

    sells = sum((-d) * valid[t] for t, d in deltas.items()
                if t in valid and d < 0)
    buys = sum(d * valid[t] for t, d in deltas.items()
               if t in valid and d > 0)

    # Sell proceeds net of costs are available to fund buys. This prevents
    # tiny negative balances caused by charging sell costs after sizing buys.
    available = max(0.0, float(cash) + sells * (1.0 - cost_rate))
    buy_scale = min(1.0, available / (buys * (1.0 + cost_rate))) if buys > 0 else 0.0

    newpos = dict(current)
    traded_buy = traded_sell = 0.0
    for t, d in deltas.items():
        if t not in valid:
            continue
        if d > 0:
            d *= buy_scale
        new = current.get(t, 0.0) + d
        if new < 0 and new > -1e-10:
            new = 0.0
        if new <= 1e-12:
            newpos.pop(t, None)
        else:
            newpos[t] = new
        if d > 0:
            traded_buy += d * valid[t]
        elif d < 0:
            traded_sell += -d * valid[t]

    # Enforce max position after the initial execution. Cap reductions are
    # sales, charged at the same per-side cost, and proceeds remain as cash.
    cap_equity = max(float(equity), 0.0)
    cap_dollars = max(cap_equity * (1.0 - 2.0 * cost_rate), 0.0) * MAX_POSITION
    cap_sells = 0.0
    for t in list(newpos):
        if t not in valid:
            continue
        value = newpos[t] * valid[t]
        if value > cap_dollars + 1e-10:
            excess_shares = (value - cap_dollars) / valid[t]
            newpos[t] -= excess_shares
            cap_sells += excess_shares * valid[t]
            if newpos[t] <= 1e-12:
                newpos.pop(t, None)

    traded_sell += cap_sells
    total_turnover = traded_buy + traded_sell
    total_cost = total_turnover * cost_rate
    cash_new = float(cash) + traded_sell - traded_buy - total_cost
    # Due to floating point, allow only machine-scale cleanup; substantive
    # negatives are an error and should not be masked.
    if cash_new < -1e-8:
        raise RuntimeError(f"Cash funding constraint failed: {cash_new:.12g}")
    if cash_new < 0:
        cash_new = 0.0

    # Gross exposure constraint: if necessary scale holdings proportionally.
    gross_value = sum(sh * valid[t] for t, sh in newpos.items() if t in valid)
    post_equity = cash_new + gross_value
    if gross_value > post_equity * GROSS_CAP + 1e-9:
        raise RuntimeError(f"Gross exposure constraint failed: {gross_value/post_equity:.12g}")
    max_weight = max((sh * valid[t] / max(post_equity, 1e-12)
                      for t, sh in newpos.items() if t in valid), default=0.0)
    if max_weight > MAX_POSITION + 1e-7:
        raise RuntimeError(f"Position cap constraint failed: {max_weight:.12g}")

    return newpos, cash_new, total_turnover, total_cost, traded_buy, traded_sell


def run_policy(
    snapshots: dict[pd.Timestamp, pd.DataFrame],
    frequency: int,
    persistence_mode: str,
    rebalance_mode: str,
    cost_bps: float,
):
    dates = sorted(snapshots)
    if len(dates) < DISCOVERY_DATES + EMBARGO + frequency * 2:
        return None

    # Freeze research after discovery + embargo.
    usable = dates[DISCOVERY_DATES + EMBARGO:]
    # Use non-overlapping rebalance dates for each frequency.
    rebalance_dates = usable[::frequency]
    if len(rebalance_dates) < 2:
        return None

    # We need actual next-open prices and marking at each daily date.
    # Use each snapshot's Open as the execution reference on t+1 where possible.
    positions = {}
    cash = 1.0
    equity_path = []
    cycle_returns = []
    turnover = []
    costs = []
    pos_counts = []
    cash_weights = []
    gross_weights = []
    max_positions = []

    for j, dt in enumerate(rebalance_dates):
        snap = snapshots[dt]
        # Execution at next available date after dt.
        idx = dates.index(dt)
        if idx + 1 >= len(dates):
            break
        exec_dt = dates[idx + 1]
        exec_snap = snapshots.get(exec_dt)
        if exec_snap is None:
            continue

        prices = dict(zip(exec_snap["Ticker"], exec_snap["Open"]))
        equity = portfolio_value(positions, prices, cash)

        if persistence_mode.startswith("EXIT"):
            target, exits = target_weights(
                snap, persistence_mode, positions, prices, equity
            )
        else:
            target, exits = target_weights(
                snap, "EXIT20", positions, prices, equity
            )

        if rebalance_mode == "FULL":
            gap = 1.0
        elif rebalance_mode == "PARTIAL50":
            gap = 0.50
        elif rebalance_mode == "PARTIAL25":
            gap = 0.25
        else:
            raise ValueError(rebalance_mode)

        positions, cash, trn, cst, buys, sells = apply_target(
            positions, cash, target, exits, prices, equity, gap, cost_bps
        )

        post_equity = portfolio_value(positions, prices, cash)
        invested_notional = sum(
            abs(sh * prices[t]) for t, sh in positions.items()
            if t in prices and np.isfinite(prices[t])
        )
        gross = invested_notional / max(post_equity, 1e-12)
        cw = cash / max(post_equity, 1e-12)

        # Hard implementation guards.
        if cash < -1e-8:
            raise RuntimeError(
                f"Negative cash after execution: {cash} "
                f"{dt} {persistence_mode} {rebalance_mode}"
            )
        if gross > GROSS_CAP + 1e-8:
            # This should only be possible from numerical noise or a
            # pathological price snapshot; fail rather than hide it.
            raise RuntimeError(
                f"Gross exposure exceeded cap: {gross} "
                f"{dt} {persistence_mode} {rebalance_mode}"
            )

        # Hold until the next scheduled rebalance; mark using closes at the
        # rebalance date immediately before the next rebalance.
        end_dt = rebalance_dates[j + 1] if j + 1 < len(rebalance_dates) else None
        if end_dt is None:
            break
        end_snap = snapshots[end_dt]
        end_prices = dict(zip(end_snap["Ticker"], end_snap["Close"]))
        end_equity = portfolio_value(positions, end_prices, cash)

        ret = end_equity / max(post_equity, 1e-12) - 1.0
        cycle_returns.append(ret)
        turnover.append(trn / max(equity, 1e-12))
        costs.append(cst)
        pos_counts.append(len(positions))
        cash_weights.append(cw)
        gross_weights.append(gross)
        current_max_position = max(
            (abs(sh * prices[t]) / max(post_equity, 1e-12)
             for t, sh in positions.items()
             if t in prices and np.isfinite(prices[t])),
            default=0.0
        )
        if current_max_position > MAX_POSITION + 1e-8:
            raise RuntimeError(
                f"Max position exceeded: {current_max_position} "
                f"{dt} {persistence_mode} {rebalance_mode}"
            )
        max_positions.append(current_max_position)
        equity_path.append(end_equity)

    if not cycle_returns:
        return None

    r = np.array(cycle_returns, dtype=float)
    eq = np.array(equity_path, dtype=float)

    # Annualize using the selected frequency in trading sessions.
    periods_per_year = 252.0 / frequency
    years = len(r) / periods_per_year
    final_eq = float(eq[-1]) if len(eq) else 1.0
    cagr = final_eq ** (1.0 / max(years, 1e-12)) - 1.0

    running = np.maximum.accumulate(eq)
    dd = eq / running - 1.0
    maxdd = float(dd.min())

    std = r.std(ddof=1) if len(r) > 1 else np.nan
    sharpe = float(r.mean() / std * np.sqrt(periods_per_year)) if std and np.isfinite(std) else np.nan

    downside = r[r < 0]
    dstd = downside.std(ddof=1) if len(downside) > 1 else np.nan
    sortino = float(r.mean() / dstd * np.sqrt(periods_per_year)) if dstd and np.isfinite(dstd) else np.nan

    gains = r[r > 0].sum()
    losses = -r[r < 0].sum()
    pf = float(gains / losses) if losses > 0 else np.inf

    return {
        "FrequencySessions": frequency,
        "Persistence": persistence_mode,
        "Rebalance": rebalance_mode,
        "CostBpsPerSide": cost_bps,
        "Cycles": len(r),
        "FinalEquity": final_eq,
        "CAGR": cagr,
        "MaxDD": maxdd,
        "Sharpe": sharpe,
        "Sortino": sortino,
        "ProfitFactor": pf,
        "HitRate": float((r > 0).mean()),
        "AnnualizedTurnover": float(np.mean(turnover) * periods_per_year),
        "AvgCycleTurnover": float(np.mean(turnover)),
        "TotalCost": float(np.sum(costs)),
        "AvgPositions": float(np.mean(pos_counts)),
        "AvgCashWeight": float(np.mean(cash_weights)),
        "AvgInvestedWeight": float(1.0 - np.mean(cash_weights)),
        "AvgGrossExposure": float(np.mean(gross_weights)),
        "MaxPositionObserved": float(np.max(max_positions)),
        "WorstCycle": float(np.min(r)),
        "BestCycle": float(np.max(r)),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 72)
    print("FASE 9 — PORTFOLIO PERSISTENCE / REAL TURNOVER — LTM")
    print("=" * 72)
    print(f"RUN_ID: {RUN_ID}")
    print(f"Configured universe: {len(DEFAULT_UNIVERSE)}")
    print(f"Frequencies: {FREQUENCIES}")
    print(f"Costs bps/side: {COST_BPS}")
    print("No Kelly | No stops | No production")
    print()

    if len(DEFAULT_UNIVERSE) == 0:
        raise RuntimeError(
            "DEFAULT_UNIVERSE is empty. Replace it with the exact frozen "
            "335-ticker universe from the preceding Phase 9D research file."
        )

    data, failures = download_universe(DEFAULT_UNIVERSE)
    print(f"Valid: {len(data)} | Failures: {len(failures)}")

    snapshots = build_snapshots(data)
    print(f"Usable cross-sectional dates: {len(snapshots)}")

    policies = []
    policy_errors = []
    persistences = ["EXIT10", "EXIT20", "EXIT30"]
    rebalances = ["FULL", "PARTIAL50", "PARTIAL25"]

    for freq in FREQUENCIES:
        for p in persistences:
            for rb in rebalances:
                for cost in COST_BPS:
                    try:
                        result = run_policy(
                            snapshots, freq, p, rb, cost
                        )
                        if result:
                            policies.append(result)
                    except Exception as exc:
                        msg = (f"POLICY_ERROR freq={freq} persistence={p} "
                               f"rebalance={rb} cost={cost}: {exc}")
                        policy_errors.append(msg)
                        print(msg)

    results = pd.DataFrame(policies)

    # Predefined sanity checks. A policy matrix is valid only when all 108
    # combinations finish; partial coverage is not a research PASS.
    expected_policy_rows = len(FREQUENCIES) * 3 * 3 * len(COST_BPS)
    checks = {
        "ExpectedPolicyRows": expected_policy_rows,
        "CompletedPolicyRows": len(results),
        "PolicyCoveragePASS": bool(len(results) == expected_policy_rows and not policy_errors),
        "PolicyErrors": len(policy_errors),
        "ConfiguredUniverse": len(DEFAULT_UNIVERSE),
        "ValidTickers": len(data),
        "Failures": len(failures),
        "Snapshots": len(snapshots),
        "Rows": len(results),
        "NoNaNCoreMetrics": bool(
            not results.empty and
            results[["CAGR", "MaxDD", "Sharpe", "AnnualizedTurnover",
                     "AvgPositions", "AvgCashWeight", "AvgGrossExposure"]]
            .notna().all().all()
        ),
        "MaxGrossExposurePASS": bool(
            results.empty or results["AvgGrossExposure"].max() <= GROSS_CAP + 1e-9
        ),
        "MaxPositionPASS": bool(
            results.empty or results["MaxPositionObserved"].max() <= MAX_POSITION + 1e-9
        ),
        "PersistenceCountPASS": bool(
            results.empty or (
                results["AvgPositions"]
                <= results["Persistence"].str.replace("EXIT", "", regex=False).astype(int)
            ).all()
        ),
        "PositiveFinalEquityPASS": bool(
            results.empty or (results["FinalEquity"] > 0).all()
        ),
    }

    results.to_csv(OUTDIR / "phase9_policy_results.csv", index=False)
    pd.DataFrame(failures).to_csv(OUTDIR / "phase9_failures.csv", index=False)

    pd.DataFrame({"PolicyError": policy_errors}).to_csv(OUTDIR / "phase9_policy_errors.csv", index=False)

    with open(OUTDIR / "phase9_checks.json", "w", encoding="utf-8") as f:
        json.dump(checks, f, indent=2)

    # A compact summary by frequency/persistence at 20 bps.
    if not results.empty:
        summary = (
            results[results["CostBpsPerSide"] == 20]
            .sort_values(["FrequencySessions", "Persistence", "Rebalance"])
        )
        summary.to_csv(OUTDIR / "phase9_summary_20bps.csv", index=False)

    print("\n--- CHECKS ---")
    for k, v in checks.items():
        print(f"{k}: {v}")

    print("\n--- SUMMARY 20bps ---")
    if results.empty:
        print("No policy results.")
    else:
        cols = [
            "FrequencySessions", "Persistence", "Rebalance",
            "CAGR", "MaxDD", "Sharpe", "ProfitFactor",
            "AnnualizedTurnover", "TotalCost", "AvgPositions",
            "AvgCashWeight", "AvgGrossExposure"
        ]
        print(results[results["CostBpsPerSide"] == 20][cols].to_string(index=False))

    status = all([
        checks["NoNaNCoreMetrics"],
        checks["MaxGrossExposurePASS"],
        checks["MaxPositionPASS"],
        checks["PersistenceCountPASS"],
        checks["PositiveFinalEquityPASS"],
        checks["PolicyCoveragePASS"],
        len(results) > 0,
    ])

    print(f"\nSTATUS: {'PASS' if status else 'FAIL'}")

    with open(OUTDIR / "phase9_status.txt", "w", encoding="utf-8") as f:
        f.write("PASS\n" if status else "FAIL\n")

    return 0 if status else 1


if __name__ == "__main__":
    raise SystemExit(main())

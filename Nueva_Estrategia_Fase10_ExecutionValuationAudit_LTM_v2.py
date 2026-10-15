"""
FASE 10 v2 — EXECUTION & VALUATION AUDIT — LONG-TERM MOMENTUM

Purpose
-------
Audit the frozen Phase 9 LTM portfolio engine without changing the signal.
This version is computationally optimized and instrumented with heartbeats.

Frozen signal:
    LTM = average cross-sectional percentile ranks of R100/R120/R140/R160.

Execution convention:
    Signal is known at close t.
    Rebalance executes at open t+1.
    Existing positions are marked at every session close.

No Kelly, stops, new factors, or production rules.

Key v2 changes:
    1. Precompute Open/Close price maps ONCE instead of rebuilding them inside
       every policy/date loop.
    2. Precompute LTM snapshots ONCE.
    3. Keep the full 108-policy audit, but emit progress by policy and date.
    4. Use python -u in the GitHub workflow so progress is visible immediately.
    5. Write compact per-policy diagnostics plus daily ledger.
    6. Hard timeout is defined in the workflow; a hung job cannot run forever.
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

RUN_ID = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
OUTDIR = Path("nueva_estrategia_phase10_execution_valuation_audit_v2")
OUTDIR.mkdir(parents=True, exist_ok=True)

PERIOD = "10y"
DISCOVERY_DATES = 12
EMBARGO = 5
MIN_CROSS_SECTION = 100
WINDOWS = [100, 120, 140, 160]
MAX_POSITION = 0.20
GROSS_CAP = 1.00
COST_BPS = [10, 20, 50]
FREQUENCIES = [20, 40, 60, 80]
PERSISTENCES = ["EXIT10", "EXIT20", "EXIT30"]
REBALANCES = ["FULL", "PARTIAL50", "PARTIAL25"]

# Exact frozen 335-ticker universe.
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

def annualized_vol(close, window):
    return close.pct_change().rolling(window).std() * np.sqrt(252)


def build_features(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
    if "Date" not in df.columns:
        df = df.reset_index()
    date_col = "Date" if "Date" in df.columns else df.columns[0]
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.rename(columns={date_col: "Date"}).sort_values("Date").drop_duplicates("Date").reset_index(drop=True)
    for c in ["Open", "Close"]:
        if c not in df.columns:
            raise ValueError(f"missing {c}")
    out = pd.DataFrame({
        "Date": df["Date"],
        "Open": pd.to_numeric(df["Open"], errors="coerce"),
        "Close": pd.to_numeric(df["Close"], errors="coerce"),
    })
    close = out["Close"]
    for w in WINDOWS:
        out[f"R{w}"] = close / close.shift(w) - 1
    out["VOL60"] = annualized_vol(close, 60)
    return out.replace([np.inf, -np.inf], np.nan)


def download_universe(tickers):
    data, failures = {}, []
    t0 = time.time()
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
        if i % 25 == 0 or i == len(tickers):
            print(f"DOWNLOAD {i}/{len(tickers)} | valid={len(data)} | elapsed={time.time()-t0:.1f}s", flush=True)
    return data, failures


def build_price_maps(data):
    """Precompute per-date price dictionaries once."""
    opens, closes = {}, {}
    for ticker, df in data.items():
        for row in df[["Date", "Open", "Close"]].itertuples(index=False):
            dt = row.Date
            if pd.notna(row.Open) and float(row.Open) > 0:
                opens.setdefault(dt, {})[ticker] = float(row.Open)
            if pd.notna(row.Close) and float(row.Close) > 0:
                closes.setdefault(dt, {})[ticker] = float(row.Close)
    return opens, closes


def build_snapshots(data, calendar):
    """Build cross-sectional LTM snapshots once, using only information at t."""
    snapshots = {}
    by_ticker = {t: df.set_index("Date", drop=False) for t, df in data.items()}
    t0 = time.time()
    for n, dt in enumerate(calendar, 1):
        rows = []
        for ticker, idx in by_ticker.items():
            if dt not in idx.index:
                continue
            r = idx.loc[dt]
            if isinstance(r, pd.DataFrame):
                r = r.iloc[0]
            vals = [r.get(f"R{w}", np.nan) for w in WINDOWS]
            if not all(pd.notna(v) for v in vals):
                continue
            if not pd.notna(r.get("Open")) or not pd.notna(r.get("Close")) or not pd.notna(r.get("VOL60")):
                continue
            rows.append({
                "Ticker": ticker,
                "Date": dt,
                "Open": float(r["Open"]),
                "Close": float(r["Close"]),
                "VOL60": float(r["VOL60"]),
                **{f"R{w}": float(r[f"R{w}"]) for w in WINDOWS},
            })
        g = pd.DataFrame(rows)
        if len(g) >= MIN_CROSS_SECTION:
            for w in WINDOWS:
                g[f"rank_R{w}"] = g[f"R{w}"].rank(pct=True, method="average")
            g["LTM"] = g[[f"rank_R{w}" for w in WINDOWS]].mean(axis=1)
            snapshots[dt] = g.sort_values("LTM", ascending=False).reset_index(drop=True)
        if n % 250 == 0 or n == len(calendar):
            print(f"SNAPSHOTS {n}/{len(calendar)} | usable={len(snapshots)} | elapsed={time.time()-t0:.1f}s", flush=True)
    return snapshots


def portfolio_value(positions, prices, cash):
    return float(cash) + sum(
        float(sh) * float(prices[t])
        for t, sh in positions.items()
        if t in prices and np.isfinite(prices[t])
    )


def build_target(snapshot, persistence, positions):
    n = int(persistence.replace("EXIT", ""))
    ranked = list(snapshot.sort_values("LTM", ascending=False)["Ticker"])
    eligible = set(ranked[:n])
    current = {t for t, sh in positions.items() if sh > 1e-12}
    exits = current - eligible
    retained = [t for t in ranked if t in current and t in eligible]
    additions = [t for t in ranked if t not in current and t in eligible]
    names = (retained + additions)[:n]
    w = min(1.0 / max(len(names), 1), MAX_POSITION)
    return {t: w for t in names}, exits


def execute_rebalance(positions, cash, target, exits, open_prices, equity,
                      gap, cost_bps, signal_dt, execution_dt, policy_id, trade_rows):
    rate = cost_bps / 10000.0
    valid = {t: p for t, p in open_prices.items() if np.isfinite(p) and p > 0}
    cur = dict(positions)
    deltas = {}

    # Explicit exits and removal of names outside target.
    for t in exits | (set(cur) - set(target)):
        if t in cur and t in valid:
            deltas[t] = -cur[t]

    # Target dollar cap is conservative: leave room for transaction cost.
    cap_dollars = max(equity * (1 - 2 * rate), 0.0) * MAX_POSITION
    for t, w in target.items():
        if t not in valid or t in exits:
            continue
        sh = cur.get(t, 0.0)
        desired = max(0.0, min(equity * float(w), cap_dollars)) / valid[t]
        d = gap * (desired - sh)
        if abs(d) > 1e-12:
            deltas[t] = d

    # Existing oversized positions are reduced before buys.
    for t, sh in cur.items():
        if t in valid and sh * valid[t] > cap_dollars + 1e-10:
            deltas[t] = min(deltas.get(t, 0.0), cap_dollars / valid[t] - sh)

    sell_notional = sum(-d * valid[t] for t, d in deltas.items() if t in valid and d < 0)
    buy_notional = sum(d * valid[t] for t, d in deltas.items() if t in valid and d > 0)
    available = max(0.0, cash + sell_notional * (1 - rate))
    scale = min(1.0, available / (buy_notional * (1 + rate))) if buy_notional > 0 else 0.0

    new = dict(cur)
    buys = sells = 0.0
    for t, d0 in deltas.items():
        if t not in valid:
            continue
        d = d0 * scale if d0 > 0 else d0
        nsh = cur.get(t, 0.0) + d
        if nsh <= 1e-12:
            new.pop(t, None)
        else:
            new[t] = nsh
        notional = abs(d) * valid[t]
        if d > 0:
            buys += notional
            side = "BUY"
        elif d < 0:
            sells += notional
            side = "SELL"
        else:
            continue
        trade_rows.append({
            "PolicyID": policy_id,
            "DateSignal": str(signal_dt.date()),
            "ExecutionDate": str(execution_dt.date()),
            "Ticker": t,
            "Side": side,
            "SharesDelta": d,
            "ExecutionOpen": valid[t],
            "Notional": notional,
            "Cost": notional * rate,
            "CostBpsPerSide": cost_bps,
        })

    # Final cap projection. Any reduction is a real SELL and is costed.
    cap_dollars = max(equity * (1 - 2 * rate), 0.0) * MAX_POSITION
    cap_sells = 0.0
    for t in list(new):
        if t not in valid:
            continue
        value = new[t] * valid[t]
        if value > cap_dollars + 1e-9:
            extra = (value - cap_dollars) / valid[t]
            new[t] -= extra
            cap_sells += extra * valid[t]
            trade_rows.append({
                "PolicyID": policy_id,
                "DateSignal": str(signal_dt.date()),
                "ExecutionDate": str(execution_dt.date()),
                "Ticker": t,
                "Side": "SELL_CAP",
                "SharesDelta": -extra,
                "ExecutionOpen": valid[t],
                "Notional": extra * valid[t],
                "Cost": extra * valid[t] * rate,
                "CostBpsPerSide": cost_bps,
            })
            if new[t] <= 1e-12:
                new.pop(t, None)

    sells += cap_sells
    cost = (buys + sells) * rate
    cash_new = cash + sells - buys - cost
    if cash_new < -1e-8:
        raise RuntimeError(f"cash negative {cash_new}")
    cash_new = max(0.0, cash_new)

    gross = sum(sh * valid[t] for t, sh in new.items() if t in valid)
    post_eq = cash_new + gross
    if post_eq <= 0:
        raise RuntimeError("non-positive post-trade equity")
    gross_w = gross / post_eq
    maxw = max((sh * valid[t] / post_eq for t, sh in new.items() if t in valid), default=0.0)
    if gross_w > GROSS_CAP + 1e-7:
        raise RuntimeError(f"gross cap {gross_w}")
    if maxw > MAX_POSITION + 1e-6:
        raise RuntimeError(f"position cap {maxw}")
    return new, cash_new, buys, sells, cost


def run_policy(data, calendar, snapshots, open_maps, close_maps,
               frequency, persistence, rebalance, cost_bps,
               policy_number, total_policies):
    policy_id = f"F{frequency}_{persistence}_{rebalance}_C{cost_bps}"
    t0 = time.time()
    signal_dates = [d for d in calendar[DISCOVERY_DATES + EMBARGO::frequency] if d in snapshots]
    if len(signal_dates) < 2:
        raise RuntimeError("insufficient signal observations")
    signal_set = {d for d in signal_dates}

    positions = {}
    cash = 1.0
    trade_rows = []
    daily_rows = []
    checks = []
    last_close = {}
    prev_equity = 1.0
    max_pos_obs = 0.0
    stale_marks = 0
    missing_open_trades = 0
    gap = {"FULL": 1.0, "PARTIAL50": 0.5, "PARTIAL25": 0.25}[rebalance]

    for i, dt in enumerate(calendar):
        opens = open_maps.get(dt, {})
        closes = close_maps.get(dt, {})
        open_marks = dict(last_close)
        open_marks.update(opens)
        open_equity = portfolio_value(positions, open_marks, cash)
        equity_before_trade = open_equity
        traded_buy = traded_sell = cost = 0.0

        prev_dt = calendar[i - 1] if i > 0 else None
        if prev_dt in signal_set:
            target, exits = build_target(snapshots[prev_dt], persistence, positions)
            if not opens:
                missing_open_trades += 1
            else:
                positions, cash, traded_buy, traded_sell, cost = execute_rebalance(
                    positions, cash, target, exits, opens, equity_before_trade,
                    gap, cost_bps, prev_dt, dt, policy_id, trade_rows
                )

        post_trade_open_marks = dict(last_close)
        post_trade_open_marks.update(opens)
        post_trade_open_equity = portfolio_value(positions, post_trade_open_marks, cash)

        close_marks = dict(last_close)
        close_marks.update(closes)
        held_missing = [t for t in positions if t not in closes]
        stale_marks += len(held_missing)
        close_equity = portfolio_value(positions, close_marks, cash)
        gross_value = sum(sh * close_marks[t] for t, sh in positions.items() if t in close_marks)
        maxw = max((sh * close_marks[t] / max(close_equity, 1e-12) for t, sh in positions.items() if t in close_marks), default=0.0)
        max_pos_obs = max(max_pos_obs, maxw)

        identity = cash + gross_value
        accounting_error = abs(identity - close_equity)
        overnight_ret = equity_before_trade / prev_equity - 1 if prev_equity > 0 else np.nan
        execution_ret = post_trade_open_equity / equity_before_trade - 1 if equity_before_trade > 0 else np.nan
        intraday_ret = close_equity / post_trade_open_equity - 1 if post_trade_open_equity > 0 else np.nan
        daily_ret = close_equity / prev_equity - 1 if prev_equity > 0 else np.nan
        vals = [overnight_ret, execution_ret, intraday_ret, daily_ret]
        decomp_error = abs((1 + overnight_ret) * (1 + execution_ret) * (1 + intraday_ret) - (1 + daily_ret)) if all(np.isfinite(x) for x in vals) else np.nan

        checks.append({
            "PolicyID": policy_id,
            "Date": str(dt.date()),
            "Cash": cash,
            "GrossMarketValue": gross_value,
            "Equity": close_equity,
            "AccountingIdentityError": accounting_error,
            "HeldWithoutFreshClose": len(held_missing),
            "GrossExposure": gross_value / max(close_equity, 1e-12),
            "MaxPositionWeight": maxw,
        })
        daily_rows.append({
            "PolicyID": policy_id,
            "Date": str(dt.date()),
            "PreviousCloseEquity": prev_equity,
            "OpenEquityBeforeTrade": equity_before_trade,
            "EquityAfterOpenExecution": post_trade_open_equity,
            "EquityClose": close_equity,
            "OvernightReturn": overnight_ret,
            "ExecutionReturn": execution_ret,
            "IntradayReturn": intraday_ret,
            "DailyReturn": daily_ret,
            "ReturnDecompositionError": decomp_error,
            "Cash": cash,
            "GrossMarketValue": gross_value,
            "Positions": len(positions),
            "BuyNotional": traded_buy,
            "SellNotional": traded_sell,
            "TransactionCost": cost,
            "FreshCloseMissingCount": len(held_missing),
        })
        prev_equity = close_equity
        last_close.update(closes)

    daily = pd.DataFrame(daily_rows)
    if daily.empty:
        raise RuntimeError("empty daily ledger")
    eq = daily["EquityClose"].astype(float).to_numpy()
    ret = daily["DailyReturn"].dropna().astype(float)
    running = np.maximum.accumulate(eq)
    dd = eq / running - 1.0
    years = max(len(daily) / 252.0, 1e-12)
    final = float(eq[-1])
    cagr = final ** (1 / years) - 1 if final > 0 else -1.0
    sd = ret.std(ddof=1) if len(ret) > 1 else np.nan
    sharpe = float(ret.mean() / sd * np.sqrt(252)) if sd and np.isfinite(sd) else np.nan
    down = ret[ret < 0]
    dsd = down.std(ddof=1) if len(down) > 1 else np.nan
    sortino = float(ret.mean() / dsd * np.sqrt(252)) if dsd and np.isfinite(dsd) else np.nan
    gains = ret[ret > 0].sum(); losses = -ret[ret < 0].sum()
    pf = float(gains / losses) if losses > 0 else np.inf
    trades = pd.DataFrame(trade_rows)
    total_buy = float(trades.loc[trades.Side.str.startswith("BUY"), "Notional"].sum()) if not trades.empty else 0.0
    total_sell = float(trades.loc[trades.Side.str.startswith("SELL"), "Notional"].sum()) if not trades.empty else 0.0
    total_cost = float(trades["Cost"].sum()) if not trades.empty else 0.0
    years_turn = max(len(daily) / 252.0, 1e-12)

    result = {
        "PolicyID": policy_id,
        "FrequencySessions": frequency,
        "Persistence": persistence,
        "Rebalance": rebalance,
        "CostBpsPerSide": cost_bps,
        "SignalCycles": len(signal_dates),
        "DailyObservations": len(daily),
        "FinalEquity": final,
        "CAGR_DailyMark": cagr,
        "MaxDD_DailyMark": float(dd.min()),
        "Sharpe_Daily": sharpe,
        "Sortino_Daily": sortino,
        "ProfitFactor_Daily": pf,
        "DailyHitRate": float((ret > 0).mean()),
        "TotalBuyNotional": total_buy,
        "TotalSellNotional": total_sell,
        "TotalTransactionCost": total_cost,
        "AnnualizedTurnover_Daily": ((total_buy + total_sell) / max(float(daily["EquityClose"].iloc[0]), 1e-12)) / years_turn,
        "AvgPositions": float(daily["Positions"].mean()),
        "AvgCashWeight": float((daily["Cash"] / daily["EquityClose"]).mean()),
        "AvgGrossExposure": float((daily["GrossMarketValue"] / daily["EquityClose"]).mean()),
        "MaxPositionObserved": max_pos_obs,
        "MaxAccountingIdentityError": float(pd.DataFrame(checks)["AccountingIdentityError"].max()),
        "MaxReturnDecompositionError": float(daily["ReturnDecompositionError"].max()),
        "HeldWithoutFreshCloseMarks": int(stale_marks),
        "MissingOpenExecutionDays": int(missing_open_trades),
        "RuntimeSeconds": time.time() - t0,
    }

    # Heartbeat every policy. This is deliberately visible in GitHub Actions.
    print(
        f"POLICY {policy_number}/{total_policies} DONE | {policy_id} | "
        f"cycles={len(signal_dates)} daily={len(daily)} | "
        f"CAGR={cagr:.4f} MaxDD={float(dd.min()):.4f} | "
        f"runtime={result['RuntimeSeconds']:.1f}s",
        flush=True,
    )
    return result, daily_rows, trade_rows, checks


def main():
    t_all = time.time()
    print("=" * 72, flush=True)
    print("FASE 10 v2 — EXECUTION & VALUATION AUDIT — LTM", flush=True)
    print("=" * 72, flush=True)
    print(f"RUN_ID: {RUN_ID}", flush=True)
    print(f"Configured universe: {len(DEFAULT_UNIVERSE)}", flush=True)
    print(f"Frequencies: {FREQUENCIES} | Costs bps/side: {COST_BPS}", flush=True)
    print("Frozen LTM = average ranks R100/R120/R140/R160", flush=True)
    print("No Kelly | No stops | No production", flush=True)

    data, failures = download_universe(DEFAULT_UNIVERSE)
    print(f"DOWNLOAD COMPLETE | valid={len(data)} failures={len(failures)} | elapsed={time.time()-t_all:.1f}s", flush=True)

    calendar = sorted(set(d for df in data.values() for d in df["Date"].dropna().tolist()))
    print(f"CALENDAR | dates={len(calendar)}", flush=True)

    price_t0 = time.time()
    open_maps, close_maps = build_price_maps(data)
    print(f"PRICE MAPS READY | open_dates={len(open_maps)} close_dates={len(close_maps)} | elapsed={time.time()-price_t0:.1f}s", flush=True)

    snap_t0 = time.time()
    snapshots = build_snapshots(data, calendar)
    print(f"SNAPSHOTS READY | usable={len(snapshots)} | elapsed={time.time()-snap_t0:.1f}s", flush=True)

    combos = [(f, p, r, c) for f in FREQUENCIES for p in PERSISTENCES for r in REBALANCES for c in COST_BPS]
    total = len(combos)
    print(f"POLICY AUDIT START | {total} policies", flush=True)

    results, daily_all, trades_all, checks_all, policy_errors = [], [], [], [], []
    for n, (freq, persistence, rebalance, cost) in enumerate(combos, 1):
        try:
            result, daily, trades, checks = run_policy(
                data, calendar, snapshots, open_maps, close_maps,
                freq, persistence, rebalance, cost, n, total
            )
            results.append(result)
            daily_all.extend(daily)
            trades_all.extend(trades)
            checks_all.extend(checks)
        except Exception as e:
            msg = f"POLICY_ERROR {freq} {persistence} {rebalance} {cost}: {type(e).__name__}: {e}"
            policy_errors.append(msg)
            print(msg, flush=True)

    res = pd.DataFrame(results)
    daily = pd.DataFrame(daily_all)
    trades = pd.DataFrame(trades_all)
    checks_df = pd.DataFrame(checks_all)
    expected = total

    identity_max = float(checks_df["AccountingIdentityError"].max()) if not checks_df.empty else float("inf")
    decomposition_max = float(daily["ReturnDecompositionError"].max()) if not daily.empty else float("inf")
    gross_max = float(checks_df["GrossExposure"].max()) if not checks_df.empty else float("inf")
    pos_max = float(checks_df["MaxPositionWeight"].max()) if not checks_df.empty else float("inf")
    stale_rows = int(checks_df["HeldWithoutFreshClose"].sum()) if not checks_df.empty else -1

    checks = {
        "ExpectedPolicyRows": expected,
        "CompletedPolicyRows": len(res),
        "PolicyCoveragePASS": bool(len(res) == expected and not policy_errors),
        "PolicyErrors": len(policy_errors),
        "ConfiguredUniverse": len(DEFAULT_UNIVERSE),
        "ValidTickers": len(data),
        "DownloadFailures": len(failures),
        "TradingCalendarDates": len(calendar),
        "SignalSnapshots": len(snapshots),
        "DailyRows": len(daily),
        "TradeRows": len(trades),
        "MaxAccountingIdentityError": identity_max,
        "AccountingIdentityPASS": bool(identity_max < 1e-8),
        "MaxReturnDecompositionError": decomposition_max,
        "ReturnDecompositionPASS": bool(decomposition_max < 1e-8),
        "MaxGrossExposureObserved": gross_max,
        "GrossExposurePASS": bool(gross_max <= GROSS_CAP + 1e-6),
        "MaxPositionObserved": pos_max,
        "MaxPositionPASS": bool(pos_max <= MAX_POSITION + 1e-5),
        "AllFinalEquityPositive": bool(not res.empty and (res.FinalEquity > 0).all()),
        "NoNaNCoreMetrics": bool(not res.empty and res[["CAGR_DailyMark", "MaxDD_DailyMark", "Sharpe_Daily", "FinalEquity"]].notna().all().all()),
        "StaleMarkRows": stale_rows,
        "TotalRuntimeSeconds": time.time() - t_all,
    }

    res.to_csv(OUTDIR / "phase10v2_policy_results.csv", index=False)
    daily.to_csv(OUTDIR / "phase10v2_daily_equity.csv", index=False)
    trades.to_csv(OUTDIR / "phase10v2_trade_ledger.csv", index=False)
    checks_df.to_csv(OUTDIR / "phase10v2_valuation_checks.csv", index=False)
    pd.DataFrame(failures).to_csv(OUTDIR / "phase10v2_download_failures.csv", index=False)
    pd.DataFrame({"PolicyError": policy_errors}).to_csv(OUTDIR / "phase10v2_policy_errors.csv", index=False)
    with open(OUTDIR / "phase10v2_checks.json", "w", encoding="utf-8") as f:
        json.dump(checks, f, indent=2)

    print("\n--- CHECKS ---", flush=True)
    for k, v in checks.items():
        print(f"{k}: {v}", flush=True)

    if not res.empty:
        print("\n--- SUMMARY 20bps ---", flush=True)
        cols = [
            "FrequencySessions", "Persistence", "Rebalance",
            "CAGR_DailyMark", "MaxDD_DailyMark", "Sharpe_Daily",
            "FinalEquity", "AnnualizedTurnover_Daily",
            "TotalTransactionCost", "AvgCashWeight", "AvgGrossExposure",
            "MaxPositionObserved", "RuntimeSeconds",
        ]
        print(res[res.CostBpsPerSide == 20][cols].to_string(index=False), flush=True)

    status = all([
        checks["PolicyCoveragePASS"],
        checks["AccountingIdentityPASS"],
        checks["ReturnDecompositionPASS"],
        checks["GrossExposurePASS"],
        checks["MaxPositionPASS"],
        checks["AllFinalEquityPositive"],
        checks["NoNaNCoreMetrics"],
    ])
    print(f"\nSTATUS: {'PASS' if status else 'FAIL'}", flush=True)
    (OUTDIR / "phase10v2_status.txt").write_text("PASS\n" if status else "FAIL\n", encoding="utf-8")
    return 0 if status else 1


if __name__ == "__main__":
    raise SystemExit(main())

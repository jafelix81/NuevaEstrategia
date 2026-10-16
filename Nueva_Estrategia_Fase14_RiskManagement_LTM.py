"""
FASE 14A — RISK MANAGEMENT — LONG-TERM MOMENTUM

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

No Kelly, no new factors, no production rules. Stops are reserved for a later sub-phase.

Key v3 changes:
    1. Precompute Open/Close price maps ONCE instead of rebuilding them inside
       every policy/date loop.
    2. Precompute LTM snapshots ONCE.
    3. Keep the full 108-policy audit, but emit progress by policy and date.
    4. Use python -u in the GitHub workflow so progress is visible immediately.
    5. Write compact per-policy diagnostics plus daily ledger.
    6. Separate executed-entry position cap from daily marked position weight.
    7. Report turnover normalized by average daily equity, plus buy/sell turnover.
    8. Hard timeout is defined in the workflow; a hung job cannot run forever.
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
OUTDIR = Path("nueva_estrategia_phase14_risk_management_ltm")
OUTDIR.mkdir(parents=True, exist_ok=True)

PERIOD = "10y"
DISCOVERY_DATES = 12
EMBARGO = 5
MIN_CROSS_SECTION = 100
WINDOWS = [100, 120, 140, 160]
INITIAL_CAPITAL = 1000.0
MAX_POSITION = 0.20
GROSS_CAP = 1.00
COST_BPS = [10, 20, 50]
FREQUENCY = 80
TOP_N = 20
PERSISTENCE_BUFFER = 20
REBALANCE = "PARTIAL50"
COST_BPS = [10, 20, 50]
# Risk overlays. The baseline reproduces the exact Phase 12 implementation.
# Static caps reduce target gross exposure at scheduled rebalances.
# Drawdown throttle reacts to the previous fully closed day's equity and can
# de-risk at the next open; it never uses today's close.
RISK_POLICIES = [
    "BASELINE",
    "STATIC75",
    "STATIC50",
    "DD10_75_DD20_50",
    "DD10_75_DD20_50_DD30_25",
]
STATIC_CAPS = {"BASELINE": 1.00, "STATIC75": 0.75, "STATIC50": 0.50}


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
    """Build cross-sectional LTM snapshots once, using only information at t.

    v3 deliberately mirrors the proven Phase 10 calendar representation and
    normalizes dates to midnight before indexing, eliminating any Timestamp
    / time-component mismatch. Includes a small diagnostic on the first
    usable calendar date.
    """
    snapshots = {}
    by_ticker = {}
    for t, df in data.items():
        x = df.copy()
        x["Date"] = pd.to_datetime(x["Date"], errors="coerce").dt.normalize()
        x = x.dropna(subset=["Date"]).drop_duplicates("Date")
        by_ticker[t] = x.set_index("Date", drop=False)
    calendar = sorted(pd.Timestamp(d).normalize() for d in calendar if pd.notna(d))
    t0 = time.time()
    diag_done = False
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
        if not diag_done and n <= len(calendar):
            # Diagnose the first date with enough raw ticker/date matches.
            date_hits = 0
            r100_hits = r120_hits = r140_hits = r160_hits = vol_hits = price_hits = 0
            for ticker, idx in by_ticker.items():
                if dt not in idx.index:
                    continue
                date_hits += 1
                r = idx.loc[dt]
                if isinstance(r, pd.DataFrame):
                    r = r.iloc[0]
                vals = [r.get(f"R{w}", np.nan) for w in WINDOWS]
                if pd.notna(vals[0]): r100_hits += 1
                if pd.notna(vals[1]): r120_hits += 1
                if pd.notna(vals[2]): r140_hits += 1
                if pd.notna(vals[3]): r160_hits += 1
                if pd.notna(r.get("VOL60")): vol_hits += 1
                if pd.notna(r.get("Open")) and pd.notna(r.get("Close")): price_hits += 1
            if date_hits > 0:
                print(
                    f"SNAPSHOT DIAG | date={dt.date()} | date_hits={date_hits} "
                    f"R100={r100_hits} R120={r120_hits} R140={r140_hits} R160={r160_hits} "
                    f"VOL60={vol_hits} prices={price_hits} final_rows={len(g)}",
                    flush=True,
                )
                diag_done = True
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


def build_target(snapshot, top_n, positions, persistence_buffer=PERSISTENCE_BUFFER):
    """Top-N portfolio with frozen EXIT20-style rank hysteresis.

    New entries come only from the top N. Existing holdings may be retained
    while their rank remains within N + persistence_buffer, reducing needless
    churn without changing the LTM signal. The target is capped at N names.
    """
    ranked = list(snapshot.sort_values("LTM", ascending=False)["Ticker"])
    rank = {t: i + 1 for i, t in enumerate(ranked)}
    current = [t for t, sh in positions.items() if sh > 1e-12]
    eligible_current = [t for t in current if rank.get(t, 10**9) <= top_n + persistence_buffer]
    exits = {t for t in current if t not in eligible_current and t not in ranked[:top_n]}
    target_names = []
    for t in ranked[:top_n]:
        if t not in target_names:
            target_names.append(t)
    # Keep incumbent names inside the persistence buffer only if there is room.
    for t in eligible_current:
        if t not in target_names and len(target_names) < top_n:
            target_names.append(t)
    target_names = target_names[:top_n]
    w = min(1.0 / max(len(target_names), 1), MAX_POSITION)
    return {t: w for t in target_names}, exits


def execute_rebalance(positions, cash, target, exits, open_prices, equity,
                      gap, cost_bps, signal_dt, execution_dt, policy_id, trade_rows,
                      risk_cap=1.0):
    rate = cost_bps / 10000.0
    risk_cap = float(max(0.0, min(1.0, risk_cap)))
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
        desired = max(0.0, min(equity * float(w) * risk_cap, cap_dollars)) / valid[t]
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


def risk_cap_for(policy_id, dd):
    """Exposure cap based only on prior fully closed equity drawdown."""
    dd = float(max(0.0, dd))
    if policy_id == "BASELINE":
        return 1.00
    if policy_id == "STATIC75":
        return 0.75
    if policy_id == "STATIC50":
        return 0.50
    if policy_id == "DD10_75_DD20_50":
        return 0.50 if dd >= 0.20 else (0.75 if dd >= 0.10 else 1.00)
    if policy_id == "DD10_75_DD20_50_DD30_25":
        if dd >= 0.30:
            return 0.25
        if dd >= 0.20:
            return 0.50
        if dd >= 0.10:
            return 0.75
        return 1.00
    raise ValueError(policy_id)


def run_policy(data, calendar, snapshots, open_maps, close_maps,
               risk_policy, cost_bps, policy_number, total_policies):
    policy_id = f"F80_TOP20_PARTIAL50_{risk_policy}_C{cost_bps}"
    t0 = time.time()
    signal_dates = [d for d in calendar[DISCOVERY_DATES + EMBARGO::FREQUENCY] if d in snapshots]
    if len(signal_dates) < 2:
        raise RuntimeError("insufficient signal observations")
    signal_set = set(signal_dates)

    positions = {}
    cash = INITIAL_CAPITAL
    trade_rows = []
    daily_rows = []
    checks = []
    last_close = {}
    prev_equity = INITIAL_CAPITAL
    peak_equity = INITIAL_CAPITAL
    max_pos_obs = 0.0
    max_entry_pos_obs = 0.0
    stale_marks = 0
    missing_open_trades = 0
    gap = 0.5  # exact Phase 12 PARTIAL50
    risk_cap_used = 1.0
    forced_risk_events = 0

    for i, dt in enumerate(calendar):
        opens = open_maps.get(dt, {})
        closes = close_maps.get(dt, {})
        open_marks = dict(last_close); open_marks.update(opens)
        open_equity = portfolio_value(positions, open_marks, cash)
        equity_before_trade = open_equity
        prior_dd = max(0.0, 1.0 - equity_before_trade / max(peak_equity, 1e-12))
        current_risk_cap = risk_cap_for(risk_policy, prior_dd)
        prev_risk_cap = risk_cap_used
        risk_cap_used = current_risk_cap
        traded_buy = traded_sell = cost = 0.0

        prev_dt = calendar[i - 1] if i > 0 else None
        is_signal = prev_dt in signal_set
        risk_change = abs(current_risk_cap - prev_risk_cap) > 1e-12
        should_trade = is_signal or (risk_change and current_risk_cap < prev_risk_cap)

        if should_trade:
            if is_signal:
                target, exits = build_target(snapshots[prev_dt], TOP_N, positions)
            else:
                # Forced de-risk: retain current names, scale gross only.
                target = {t: 1.0 / max(len(positions), 1) for t in positions}
                exits = set()
            if not opens:
                missing_open_trades += 1
            else:
                if risk_change and current_risk_cap < prev_risk_cap and not is_signal:
                    forced_risk_events += 1
                positions, cash, traded_buy, traded_sell, cost = execute_rebalance(
                    positions, cash, target, exits, opens, equity_before_trade,
                    gap, cost_bps, prev_dt if prev_dt is not None else dt, dt,
                    policy_id, trade_rows, risk_cap=current_risk_cap
                )
                entry_marks = dict(last_close); entry_marks.update(opens)
                entry_equity = portfolio_value(positions, entry_marks, cash)
                entry_maxw = max(
                    (sh * entry_marks[t] / max(entry_equity, 1e-12)
                     for t, sh in positions.items() if t in entry_marks), default=0.0)
                max_entry_pos_obs = max(max_entry_pos_obs, entry_maxw)

        post_trade_open_marks = dict(last_close); post_trade_open_marks.update(opens)
        post_trade_open_equity = portfolio_value(positions, post_trade_open_marks, cash)
        close_marks = dict(last_close); close_marks.update(closes)
        held_missing = [t for t in positions if t not in close_marks]
        stale_marks += len(held_missing)
        close_equity = portfolio_value(positions, close_marks, cash)
        gross_value = sum(sh * close_marks[t] for t, sh in positions.items() if t in close_marks)
        maxw = max((sh * close_marks[t] / max(close_equity, 1e-12)
                    for t, sh in positions.items() if t in close_marks), default=0.0)
        max_pos_obs = max(max_pos_obs, maxw)
        peak_equity = max(peak_equity, close_equity)
        accounting_error = abs(close_equity - (cash + gross_value))
        overnight_ret = post_trade_open_equity / max(prev_equity, 1e-12) - 1.0
        execution_ret = post_trade_open_equity / max(open_equity, 1e-12) - 1.0
        intraday_ret = close_equity / max(post_trade_open_equity, 1e-12) - 1.0
        daily_ret = close_equity / max(prev_equity, 1e-12) - 1.0
        decomp_error = abs((1 + execution_ret) * (1 + intraday_ret) - (1 + daily_ret))
        checks.append({"AccountingIdentityError": accounting_error})
        daily_rows.append({
            "PolicyID": policy_id, "Date": str(dt.date()),
            "PreviousCloseEquity": prev_equity, "OpenEquityBeforeTrade": open_equity,
            "EquityAfterOpenExecution": post_trade_open_equity, "EquityClose": close_equity,
            "OvernightReturn": overnight_ret, "ExecutionReturn": execution_ret,
            "IntradayReturn": intraday_ret, "DailyReturn": daily_ret,
            "ReturnDecompositionError": decomp_error, "Cash": cash,
            "GrossMarketValue": gross_value, "Positions": len(positions),
            "BuyNotional": traded_buy, "SellNotional": traded_sell,
            "TransactionCost": cost, "FreshCloseMissingCount": len(held_missing),
            "PriorDrawdown": prior_dd, "RiskCap": current_risk_cap,
            "RiskChange": risk_change, "ForcedRiskEvent": bool(risk_change and current_risk_cap < prev_risk_cap),
        })
        prev_equity = close_equity
        last_close.update(closes)

    daily = pd.DataFrame(daily_rows)
    if daily.empty: raise RuntimeError("empty daily ledger")
    eq = daily["EquityClose"].astype(float).to_numpy()
    ret = daily["DailyReturn"].dropna().astype(float)
    running = np.maximum.accumulate(eq); dd = eq / running - 1.0
    years = max(len(daily) / 252.0, 1e-12); final = float(eq[-1])
    cagr = final ** (1 / years) - 1 if final > 0 else -1.0
    sd = ret.std(ddof=1) if len(ret) > 1 else np.nan
    sharpe = float(ret.mean() / sd * np.sqrt(252)) if sd and np.isfinite(sd) else np.nan
    down = ret[ret < 0]; dsd = down.std(ddof=1) if len(down) > 1 else np.nan
    sortino = float(ret.mean() / dsd * np.sqrt(252)) if dsd and np.isfinite(dsd) else np.nan
    gains = ret[ret > 0].sum(); losses = -ret[ret < 0].sum(); pf = float(gains / losses) if losses > 0 else np.inf
    trades = pd.DataFrame(trade_rows)
    total_buy = float(trades.loc[trades.Side.str.startswith("BUY"), "Notional"].sum()) if not trades.empty else 0.0
    total_sell = float(trades.loc[trades.Side.str.startswith("SELL"), "Notional"].sum()) if not trades.empty else 0.0
    total_cost = float(trades["Cost"].sum()) if not trades.empty else 0.0
    avg_equity = max(float(daily["EquityClose"].mean()), 1e-12); years_turn = max(len(daily) / 252.0, 1e-12)
    result = {
        "PolicyID": policy_id, "RiskPolicy": risk_policy, "FrequencySessions": FREQUENCY,
        "TopN": TOP_N, "Rebalance": REBALANCE, "CostBpsPerSide": cost_bps,
        "SignalCycles": len(signal_dates), "DailyObservations": len(daily),
        "InitialCapital": INITIAL_CAPITAL, "FinalEquity": final, "CAGR_DailyMark": cagr,
        "MaxDD_DailyMark": float(dd.min()), "Sharpe_Daily": sharpe, "Sortino_Daily": sortino,
        "ProfitFactor_Daily": pf, "DailyHitRate": float((ret > 0).mean()),
        "TotalBuyNotional": total_buy, "TotalSellNotional": total_sell,
        "TotalTransactionCost": total_cost, "AverageDailyEquity": avg_equity,
        "AnnualizedTurnover": ((total_buy + total_sell) / avg_equity) / years_turn,
        "AnnualizedBuyTurnover": (total_buy / avg_equity) / years_turn,
        "AnnualizedSellTurnover": (total_sell / avg_equity) / years_turn,
        "AvgPositions": float(daily["Positions"].mean()),
        "AvgCashWeight": float((daily["Cash"] / daily["EquityClose"]).mean()),
        "AvgGrossExposure": float((daily["GrossMarketValue"] / daily["EquityClose"]).mean()),
        "MaxEntryPositionObserved": max_entry_pos_obs, "MaxDailyMarkedPositionObserved": max_pos_obs,
        "MaxAccountingIdentityError": float(pd.DataFrame(checks)["AccountingIdentityError"].max()),
        "MaxReturnDecompositionError": float(daily["ReturnDecompositionError"].max()),
        "HeldWithoutFreshCloseMarks": int(stale_marks), "ForcedRiskEvents": forced_risk_events,
        "RuntimeSeconds": time.time() - t0,
    }
    print(f"POLICY {policy_number}/{total_policies} DONE | {policy_id} | CAGR={cagr:.4f} MaxDD={float(dd.min()):.4f} Sharpe={sharpe:.3f} | runtime={result['RuntimeSeconds']:.1f}s", flush=True)
    return result, daily_rows, trade_rows, checks

def main():
    t_all = time.time()
    print("FASE 14A — RISK MANAGEMENT — LONG-TERM MOMENTUM", flush=True)
    print("=" * 78, flush=True)
    print(f"RUN_ID: {RUN_ID}", flush=True)
    print("FROZEN STRATEGY: F80_TOP20_PARTIAL50 | exact Phase 12 semantics", flush=True)
    print(f"Risk policies: {RISK_POLICIES}", flush=True)
    print(f"Costs bps/side: {COST_BPS}", flush=True)
    print("No new factors | No re-selection | No Kelly | No stops | No production", flush=True)

    data, failures = download_universe(DEFAULT_UNIVERSE)
    valid = len(data)
    if valid < MIN_CROSS_SECTION: raise RuntimeError(f"valid universe too small: {valid}")
    calendar = sorted(set(d for df in data.values() for d in df["Date"].dropna().tolist()))
    last_fully_closed = pd.Timestamp(datetime.now(timezone.utc).date()) - pd.Timedelta(days=1)
    # Conservative: exclude the current UTC date and anything after it.
    calendar = [d for d in calendar if pd.Timestamp(d).normalize() <= last_fully_closed.normalize()]
    open_maps, close_maps = build_price_maps(data)
    snapshots = build_snapshots(data, calendar)
    print(f"Valid tickers={valid} | failures={len(failures)} | snapshots={len(snapshots)}", flush=True)
    print(f"LastFullyClosedDate={last_fully_closed.date()}", flush=True)

    policies = [(rp,c) for rp in RISK_POLICIES for c in COST_BPS]
    total=len(policies); results=[]; all_daily=[]; all_trades=[]; all_checks=[]; errors=[]
    for k,(rp,c) in enumerate(policies,1):
        try:
            res,daily,trades,checks=run_policy(data,calendar,snapshots,open_maps,close_maps,rp,c,k,total)
            results.append(res); all_daily.extend(daily); all_trades.extend(trades); all_checks.extend(checks)
        except Exception as e:
            errors.append({"RiskPolicy":rp,"CostBps":c,"Error":str(e)})
            print(f"POLICY ERROR {k}/{total}: {rp} C{c} | {e}",flush=True)
    resdf=pd.DataFrame(results); daily=pd.DataFrame(all_daily); trades=pd.DataFrame(all_trades); checks_df=pd.DataFrame(all_checks)
    expected=total; completed=len(resdf)
    checks={
        "ExpectedPolicyRows":expected,"CompletedPolicyRows":completed,"PolicyCoveragePASS":bool(completed==expected),
        "PolicyErrors":len(errors),"ConfiguredUniverse":len(DEFAULT_UNIVERSE),"ValidTickers":valid,"Failures":len(failures),
        "Snapshots":len(snapshots),"Rows":len(resdf),"NoNaNCoreMetrics":bool(resdf.notna().all().all()) if not resdf.empty else False,
        "AccountingIdentityPASS":bool(checks_df["AccountingIdentityError"].max()<=1e-8) if not checks_df.empty else False,
        "ReturnDecompositionPASS":bool(daily["ReturnDecompositionError"].max()<=1e-8) if not daily.empty else False,
        "GrossExposurePASS":bool(resdf["AvgGrossExposure"].max()<=GROSS_CAP+1e-8) if not resdf.empty else False,
        "EntryPositionPASS":bool(resdf["MaxEntryPositionObserved"].max()<=MAX_POSITION+1e-6) if not resdf.empty else False,
        "PositiveFinalEquityPASS":bool((resdf["FinalEquity"]>0).all()) if not resdf.empty else False,
        "InitialCapital":INITIAL_CAPITAL,
        "MaxEntryPositionObserved":float(resdf["MaxEntryPositionObserved"].max()) if not resdf.empty else np.nan,
        "MaxDailyMarkedPositionObserved":float(resdf["MaxDailyMarkedPositionObserved"].max()) if not resdf.empty else np.nan,
        "LastFullyClosedDate":str(last_fully_closed.date()),
        "RuntimeSeconds":time.time()-t_all,
    }
    resdf.to_csv(OUTDIR/"phase14A_policy_results.csv",index=False)
    daily.to_csv(OUTDIR/"phase14A_daily_equity.csv",index=False)
    trades.to_csv(OUTDIR/"phase14A_trade_ledger.csv",index=False)
    checks_df.to_csv(OUTDIR/"phase14A_valuation_checks.csv",index=False)
    pd.DataFrame(failures).to_csv(OUTDIR/"phase14A_download_failures.csv",index=False)
    pd.DataFrame(errors).to_csv(OUTDIR/"phase14A_policy_errors.csv",index=False)
    json.dump(checks,open(OUTDIR/"phase14A_checks.json","w"),indent=2)
    print("\n--- CHECKS ---",flush=True)
    for k,v in checks.items(): print(f"{k}: {v}",flush=True)
    if not resdf.empty:
        print("\n--- SUMMARY 20bps ---",flush=True)
        cols=["RiskPolicy","CostBpsPerSide","CAGR_DailyMark","MaxDD_DailyMark","Sharpe_Daily","Sortino_Daily","FinalEquity","AnnualizedTurnover","TotalTransactionCost","AvgCashWeight","AvgGrossExposure","ForcedRiskEvents"]
        print(resdf[resdf.CostBpsPerSide==20][cols].to_string(index=False),flush=True)
    status = all(bool(v) for k,v in checks.items() if k.endswith("PASS"))
    print(f"\nSTATUS: {'PASS' if status and not errors else 'FAIL'}",flush=True)

if __name__ == "__main__":
    main()

"""
FASE 10 — EXECUTION & VALUATION AUDIT — LONG-TERM MOMENTUM

Audits the frozen Phase 9 LTM portfolio policies using a daily mark-to-market
ledger. Signal is calculated from close t; orders execute at open t+1. Holdings
are valued at each session close, including overnight gaps and intraday moves.
No Kelly, stops, new factors, or live trading.

Outputs:
- phase10_policy_results.csv: 108 policies
- phase10_daily_equity.csv: daily equity for every policy
- phase10_trade_ledger.csv: each executed buy/sell
- phase10_valuation_checks.csv: daily accounting identities and price-mark checks
- phase10_failures.csv / phase10_checks.json / phase10_status.txt
"""
from __future__ import annotations
import json, math
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd
import yfinance as yf

RUN_ID = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
OUTDIR = Path("nueva_estrategia_phase10_execution_valuation_audit")
OUTDIR.mkdir(parents=True, exist_ok=True)
PERIOD="10y"
DISCOVERY_DATES=12
EMBARGO=5
MIN_CROSS_SECTION=100
WINDOWS=[100,120,140,160]
HORIZON=20
MAX_POSITION=0.20
GROSS_CAP=1.00
COST_BPS=[10,20,50]
FREQUENCIES=[20,40,60,80]
PERSISTENCES=["EXIT10","EXIT20","EXIT30"]
REBALANCES=["FULL","PARTIAL50","PARTIAL25"]

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
        df.columns=[c[0] if isinstance(c,tuple) else c for c in df.columns]
    if "Date" not in df.columns: df=df.reset_index()
    date_col="Date" if "Date" in df.columns else df.columns[0]
    df[date_col]=pd.to_datetime(df[date_col],errors="coerce")
    df=df.rename(columns={date_col:"Date"}).sort_values("Date").drop_duplicates("Date").reset_index(drop=True)
    for c in ["Open","High","Low","Close","Volume"]:
        if c not in df.columns: raise ValueError(f"missing {c}")
    out=pd.DataFrame({"Date":df["Date"], **{c:pd.to_numeric(df[c],errors="coerce") for c in ["Open","High","Low","Close","Volume"]}})
    close=out["Close"]
    for w in WINDOWS: out[f"R{w}"]=close/close.shift(w)-1
    out["VOL60"]=annualized_vol(close,60)
    out["FWD20"]=close.shift(-HORIZON)/out["Open"].shift(-1)-1 # diagnostic only; never used in signals
    return out.replace([np.inf,-np.inf],np.nan)

def download_universe(tickers):
    data, failures={},[]
    for i,ticker in enumerate(tickers,1):
        try:
            raw=yf.download(ticker,period=PERIOD,interval="1d",auto_adjust=False,progress=False,threads=False)
            if raw is None or raw.empty: raise ValueError("empty download")
            feat=build_features(raw)
            if len(feat)<220: raise ValueError(f"insufficient rows: {len(feat)}")
            data[ticker]=feat
        except Exception as e: failures.append({"Ticker":ticker,"Error":str(e)})
        if i%25==0: print(f"Downloaded {i}/{len(tickers)}")
    return data,failures

def build_snapshots(data, calendar):
    snapshots={}
    # A signal snapshot uses only values present at that date's close.
    by_ticker={t:df.set_index("Date",drop=False) for t,df in data.items()}
    for dt in calendar:
        rows=[]
        for ticker,idx in by_ticker.items():
            if dt not in idx.index: continue
            r=idx.loc[dt]
            if isinstance(r,pd.DataFrame): r=r.iloc[0]
            vals=[r.get(f"R{w}",np.nan) for w in WINDOWS]
            if not all(pd.notna(v) for v in vals) or not pd.notna(r.get("Close")) or not pd.notna(r.get("Open")) or not pd.notna(r.get("VOL60")): continue
            rows.append({"Ticker":ticker,"Date":dt,"Open":float(r["Open"]),"Close":float(r["Close"]),"VOL60":float(r["VOL60"]),**{f"R{w}":float(r[f"R{w}"]) for w in WINDOWS}})
        g=pd.DataFrame(rows)
        if len(g)<MIN_CROSS_SECTION: continue
        for w in WINDOWS: g[f"rank_R{w}"]=g[f"R{w}"].rank(pct=True,method="average")
        g["LTM"]=g[[f"rank_R{w}" for w in WINDOWS]].mean(axis=1)
        snapshots[dt]=g.sort_values("LTM",ascending=False).reset_index(drop=True)
    return snapshots

def price_map(data, dt, field):
    out={}
    for t,df in data.items():
        row=df.loc[df["Date"].eq(dt),field]
        if len(row) and pd.notna(row.iloc[0]) and float(row.iloc[0])>0: out[t]=float(row.iloc[0])
    return out

def last_close_map(data, dt, last_close):
    # Carry forward only the last observed close for marking; never use a future price.
    out=dict(last_close)
    for t,df in data.items():
        rows=df.loc[df["Date"].eq(dt),"Close"]
        if len(rows) and pd.notna(rows.iloc[0]) and float(rows.iloc[0])>0: out[t]=float(rows.iloc[0])
    return out

def portfolio_value(positions, prices, cash):
    return float(cash)+sum(float(sh)*float(prices[t]) for t,sh in positions.items() if t in prices and np.isfinite(prices[t]))

def build_target(snapshot, persistence, positions):
    n=int(persistence.replace("EXIT",""))
    ranked=list(snapshot.sort_values("LTM",ascending=False)["Ticker"])
    eligible=set(ranked[:n])
    current={t for t,sh in positions.items() if sh>1e-12}
    exits=current-eligible
    retained=[t for t in ranked if t in current and t in eligible]
    additions=[t for t in ranked if t not in current and t in eligible]
    names=(retained+additions)[:n]
    w=min(1.0/max(len(names),1),MAX_POSITION)
    return {t:w for t in names},exits

def execute_rebalance(positions,cash,target,exits,open_prices,equity,gap,cost_bps,signal_dt,execution_dt,policy_id,trade_rows):
    rate=cost_bps/10000.0
    valid={t:p for t,p in open_prices.items() if np.isfinite(p) and p>0}
    cur=dict(positions); deltas={}
    # Full liquidations for names outside persistence band, when tradable.
    for t in exits | (set(cur)-set(target)):
        if t in cur and t in valid: deltas[t]=-cur[t]
    # Target gaps, with a hard 20% dollar cap measured on pre-trade equity.
    cap_dollars=max(equity*(1-2*rate),0)*MAX_POSITION
    for t,w in target.items():
        if t not in valid or t in exits: continue
        sh=cur.get(t,0.0); desired=max(0.0,min(equity*float(w),cap_dollars))/valid[t]
        d=gap*(desired-sh)
        if abs(d)>1e-12: deltas[t]=d
    for t,sh in cur.items():
        if t in valid and sh*valid[t]>cap_dollars+1e-10:
            deltas[t]=min(deltas.get(t,0.0),cap_dollars/valid[t]-sh)
    # Sell first. A name without an open price cannot be traded; keep it and flag it.
    sell_notional=sum(-d*valid[t] for t,d in deltas.items() if t in valid and d<0)
    buy_notional=sum(d*valid[t] for t,d in deltas.items() if t in valid and d>0)
    available=max(0.0,cash+sell_notional*(1-rate))
    scale=min(1.0,available/(buy_notional*(1+rate))) if buy_notional>0 else 0.0
    new=dict(cur); buys=sells=0.0
    for t,d0 in deltas.items():
        if t not in valid: continue
        d=d0*scale if d0>0 else d0
        nsh=cur.get(t,0.0)+d
        if nsh<=1e-12: new.pop(t,None)
        else: new[t]=nsh
        notional=abs(d)*valid[t]
        if d>0: buys+=notional; side="BUY"
        elif d<0: sells+=notional; side="SELL"
        else: continue
        trade_rows.append({"PolicyID":policy_id,"DateSignal":str(signal_dt.date()),"ExecutionDate":str(execution_dt.date()),"Ticker":t,"Side":side,"SharesDelta":d,"ExecutionOpen":valid[t],"Notional":notional,"Cost":notional*rate,"CostBpsPerSide":cost_bps})
    # Post-trade cap projection; cap sells are real trades with costs.
    cap_dollars=max(equity*(1-2*rate),0)*MAX_POSITION
    cap_sells=0.0
    for t in list(new):
        if t not in valid: continue
        value=new[t]*valid[t]
        if value>cap_dollars+1e-9:
            extra=(value-cap_dollars)/valid[t]
            new[t]-=extra; cap_sells+=extra*valid[t]
            trade_rows.append({"PolicyID":policy_id,"DateSignal":str(signal_dt.date()),"ExecutionDate":str(execution_dt.date()),"Ticker":t,"Side":"SELL_CAP","SharesDelta":-extra,"ExecutionOpen":valid[t],"Notional":extra*valid[t],"Cost":extra*valid[t]*rate,"CostBpsPerSide":cost_bps})
            if new[t]<=1e-12: new.pop(t,None)
    sells+=cap_sells
    cost=(buys+sells)*rate
    cash_new=cash+sells-buys-cost
    if cash_new < -1e-8: raise RuntimeError(f"cash negative {cash_new}")
    cash_new=max(0.0,cash_new)
    gross=sum(sh*valid[t] for t,sh in new.items() if t in valid)
    post_eq=cash_new+gross
    if post_eq<=0: raise RuntimeError("non-positive post-trade equity")
    maxw=max((sh*valid[t]/post_eq for t,sh in new.items() if t in valid),default=0.0)
    if gross/post_eq>GROSS_CAP+1e-7: raise RuntimeError(f"gross cap {gross/post_eq}")
    if maxw>MAX_POSITION+1e-6: raise RuntimeError(f"position cap {maxw}")
    return new,cash_new,buys,sells,cost

def run_policy(data, calendar, snapshots, frequency, persistence, rebalance, cost_bps):
    policy_id=f"F{frequency}_{persistence}_{rebalance}_C{cost_bps}"
    if len(calendar)<DISCOVERY_DATES+EMBARGO+frequency*2: return None,[],[],[]
    signal_dates=[d for d in calendar[DISCOVERY_DATES+EMBARGO::frequency] if d in snapshots]
    if len(signal_dates)<2: return None,[],[],[]
    signal_set={d:i for i,d in enumerate(signal_dates)}
    positions={}; cash=1.0; trade_rows=[]; daily_rows=[]; checks=[]; failures=[]
    last_close={}; prev_equity=1.0; max_pos_obs=0.0; stale_marks=0; missing_open_trades=0
    for i,dt in enumerate(calendar):
        opens=price_map(data,dt,"Open")
        closes=price_map(data,dt,"Close")
        # At today's open, mark existing holdings. This includes overnight gaps.
        open_marks=dict(last_close); open_marks.update(opens)
        open_equity=portfolio_value(positions,open_marks,cash)
        equity_before_trade=open_equity
        traded_buy=traded_sell=cost=0.0
        if dt in signal_set and i+1<len(calendar):
            snap=snapshots[dt]
            exec_dt=calendar[i+1]
            exec_open=price_map(data,exec_dt,"Open")
            # Rebalance at next session open; defer until that date in execution loop.
            # Store order intent, not future prices, to avoid lookahead in this day's state.
            pass
        # Execute signal generated at previous calendar session's close.
        prev_dt=calendar[i-1] if i>0 else None
        if prev_dt in signal_set:
            snap=snapshots[prev_dt]
            target,exits=build_target(snap,persistence,positions)
            gap={"FULL":1.0,"PARTIAL50":0.5,"PARTIAL25":0.25}[rebalance]
            # Use today's open prices and equity marked at today's open.
            if not opens:
                missing_open_trades+=1
            else:
                positions,cash,traded_buy,traded_sell,cost=execute_rebalance(
                    positions,cash,target,exits,opens,equity_before_trade,gap,cost_bps,prev_dt,dt,policy_id,trade_rows)
        # Equity immediately after open execution, then mark to today's close.
        post_trade_open_marks=dict(last_close); post_trade_open_marks.update(opens)
        post_trade_open_equity=portfolio_value(positions,post_trade_open_marks,cash)
        # Missing same-day close uses last available close only; this is explicitly audited.
        close_marks=dict(last_close); close_marks.update(closes)
        held_missing=[t for t in positions if t not in closes]
        stale_marks+=len(held_missing)
        close_equity=portfolio_value(positions,close_marks,cash)
        gross_value=sum(sh*close_marks[t] for t,sh in positions.items() if t in close_marks)
        maxw=max((sh*close_marks[t]/max(close_equity,1e-12) for t,sh in positions.items() if t in close_marks),default=0.0)
        max_pos_obs=max(max_pos_obs,maxw)
        identity=cash+gross_value
        checks.append({"PolicyID":policy_id,"Date":str(dt.date()),"Cash":cash,"GrossMarketValue":gross_value,"Equity":close_equity,"AccountingIdentityError":abs(identity-close_equity),"HeldWithoutFreshClose":len(held_missing),"GrossExposure":gross_value/max(close_equity,1e-12),"MaxPositionWeight":maxw})
        overnight_ret=equity_before_trade/prev_equity-1 if prev_equity>0 else np.nan
        execution_ret=post_trade_open_equity/equity_before_trade-1 if equity_before_trade>0 else np.nan
        intraday_ret=close_equity/post_trade_open_equity-1 if post_trade_open_equity>0 else np.nan
        daily_ret=close_equity/prev_equity-1 if prev_equity>0 else np.nan
        decomposition_error=abs((1+overnight_ret)*(1+execution_ret)*(1+intraday_ret)-(1+daily_ret)) if all(np.isfinite(x) for x in [overnight_ret,execution_ret,intraday_ret,daily_ret]) else np.nan
        daily_rows.append({"PolicyID":policy_id,"Date":str(dt.date()),"PreviousCloseEquity":prev_equity,"OpenEquityBeforeTrade":equity_before_trade,"EquityAfterOpenExecution":post_trade_open_equity,"EquityClose":close_equity,"OvernightReturn":overnight_ret,"ExecutionReturn":execution_ret,"IntradayReturn":intraday_ret,"DailyReturn":daily_ret,"ReturnDecompositionError":decomposition_error,"Cash":cash,"GrossMarketValue":gross_value,"Positions":len(positions),"BuyNotional":traded_buy,"SellNotional":traded_sell,"TransactionCost":cost,"FreshCloseMissingCount":len(held_missing)})
        prev_equity=close_equity
        # update last close only after valuation
        last_close.update(closes)
    daily=pd.DataFrame(daily_rows)
    if daily.empty: return None,daily_rows,trade_rows,checks
    eq=daily["EquityClose"].astype(float).to_numpy(); ret=daily["DailyReturn"].dropna().astype(float)
    running=np.maximum.accumulate(eq); dd=eq/running-1
    years=max(len(daily)/252.0,1e-12); final=float(eq[-1]); cagr=final**(1/years)-1 if final>0 else -1.0
    sd=ret.std(ddof=1) if len(ret)>1 else np.nan
    sharpe=float(ret.mean()/sd*np.sqrt(252)) if sd and np.isfinite(sd) else np.nan
    down=ret[ret<0]; dsd=down.std(ddof=1) if len(down)>1 else np.nan
    sortino=float(ret.mean()/dsd*np.sqrt(252)) if dsd and np.isfinite(dsd) else np.nan
    gains=ret[ret>0].sum(); losses=-ret[ret<0].sum(); pf=float(gains/losses) if losses>0 else np.inf
    trades=pd.DataFrame([x for x in trade_rows if x["PolicyID"]==policy_id])
    total_buys=float(trades.loc[trades.Side.str.startswith("BUY"),"Notional"].sum()) if not trades.empty else 0.0
    total_sells=float(trades.loc[trades.Side.str.startswith("SELL"),"Notional"].sum()) if not trades.empty else 0.0
    total_cost=float(trades["Cost"].sum()) if not trades.empty else 0.0
    n_cycles=max(len(signal_dates)-1,1)
    result={"PolicyID":policy_id,"FrequencySessions":frequency,"Persistence":persistence,"Rebalance":rebalance,"CostBpsPerSide":cost_bps,"SignalCycles":len(signal_dates),"DailyObservations":len(daily),"FinalEquity":final,"CAGR_DailyMark":cagr,"MaxDD_DailyMark":float(dd.min()),"Sharpe_Daily":sharpe,"Sortino_Daily":sortino,"ProfitFactor_Daily":pf,"DailyHitRate":float((ret>0).mean()),"TotalBuyNotional":total_buys,"TotalSellNotional":total_sells,"TotalTransactionCost":total_cost,"AnnualizedTurnover_Daily":((total_buys+total_sells)/max(float(daily.EquityClose.iloc[0]),1e-12))/years,"AvgPositions":float(daily.Positions.mean()),"AvgCashWeight":float((daily.Cash/daily.EquityClose).mean()),"AvgGrossExposure":float((daily.GrossMarketValue/daily.EquityClose).mean()),"MaxPositionObserved":max_pos_obs,"MaxAccountingIdentityError":float(pd.DataFrame(checks)["AccountingIdentityError"].max()),"MaxReturnDecompositionError":float(daily["ReturnDecompositionError"].max()),"HeldWithoutFreshCloseMarks":int(stale_marks),"MissingOpenExecutionDays":int(missing_open_trades)}
    return result,daily_rows,trade_rows,checks



def main():
    print("="*72); print("FASE 10 — EXECUTION & VALUATION AUDIT — LTM"); print("="*72)
    print(f"RUN_ID: {RUN_ID}"); print(f"Configured universe: {len(DEFAULT_UNIVERSE)}")
    print(f"Frequencies: {FREQUENCIES}; Costs bps/side: {COST_BPS}")
    print("Frozen LTM average-rank R100/R120/R140/R160 | no Kelly | no stops | no production")
    data,failures=download_universe(DEFAULT_UNIVERSE)
    print(f"Valid: {len(data)} | Failures: {len(failures)}")
    calendar=sorted(set(d for df in data.values() for d in df["Date"].dropna().tolist()))
    snapshots=build_snapshots(data,calendar)
    print(f"Trading calendar dates: {len(calendar)} | Signal snapshots: {len(snapshots)}")
    results=[]; daily_all=[]; trades_all=[]; checks_all=[]; policy_errors=[]
    for freq in FREQUENCIES:
      for persistence in PERSISTENCES:
       for rebalance in REBALANCES:
        for cost in COST_BPS:
         try:
          result,daily,trades,checks=run_policy(data,calendar,snapshots,freq,persistence,rebalance,cost)
          if result is None: raise RuntimeError("insufficient observations")
          results.append(result); daily_all.extend(daily); trades_all.extend(trades); checks_all.extend(checks)
         except Exception as e:
          msg=f"POLICY_ERROR {freq} {persistence} {rebalance} {cost}: {e}"
          policy_errors.append(msg); print(msg)
    res=pd.DataFrame(results); daily=pd.DataFrame(daily_all); trades=pd.DataFrame(trades_all); checks_df=pd.DataFrame(checks_all)
    expected=len(FREQUENCIES)*len(PERSISTENCES)*len(REBALANCES)*len(COST_BPS)
    identity_max=float(checks_df.AccountingIdentityError.max()) if not checks_df.empty else float("inf")
    decomposition_max=float(daily.ReturnDecompositionError.max()) if not daily.empty else float("inf")
    gross_max=float(checks_df.GrossExposure.max()) if not checks_df.empty else float("inf")
    pos_max=float(checks_df.MaxPositionWeight.max()) if not checks_df.empty else float("inf")
    checks={"ExpectedPolicyRows":expected,"CompletedPolicyRows":len(res),"PolicyCoveragePASS":bool(len(res)==expected and not policy_errors),"PolicyErrors":len(policy_errors),"ConfiguredUniverse":len(DEFAULT_UNIVERSE),"ValidTickers":len(data),"DownloadFailures":len(failures),"TradingCalendarDates":len(calendar),"SignalSnapshots":len(snapshots),"DailyRows":len(daily),"TradeRows":len(trades),"MaxAccountingIdentityError":identity_max,"AccountingIdentityPASS":bool(identity_max<1e-8),"MaxReturnDecompositionError":decomposition_max,"ReturnDecompositionPASS":bool(decomposition_max<1e-8),"MaxGrossExposureObserved":gross_max,"GrossExposurePASS":bool(gross_max<=GROSS_CAP+1e-6),"MaxPositionObserved":pos_max,"MaxPositionPASS":bool(pos_max<=MAX_POSITION+1e-5),"AllFinalEquityPositive":bool(not res.empty and (res.FinalEquity>0).all()),"NoNaNCoreMetrics":bool(not res.empty and res[["CAGR_DailyMark","MaxDD_DailyMark","Sharpe_Daily","FinalEquity"]].notna().all().all()),"StaleMarkRows":int(checks_df.HeldWithoutFreshClose.sum()) if not checks_df.empty else -1}
    res.to_csv(OUTDIR/"phase10_policy_results.csv",index=False)
    daily.to_csv(OUTDIR/"phase10_daily_equity.csv",index=False)
    trades.to_csv(OUTDIR/"phase10_trade_ledger.csv",index=False)
    checks_df.to_csv(OUTDIR/"phase10_valuation_checks.csv",index=False)
    pd.DataFrame(failures).to_csv(OUTDIR/"phase10_download_failures.csv",index=False)
    pd.DataFrame({"PolicyError":policy_errors}).to_csv(OUTDIR/"phase10_policy_errors.csv",index=False)
    with open(OUTDIR/"phase10_checks.json","w") as f: json.dump(checks,f,indent=2)
    print("\n--- CHECKS ---")
    for k,v in checks.items(): print(f"{k}: {v}")
    if not res.empty:
      print("\n--- SUMMARY 20bps ---")
      cols=["FrequencySessions","Persistence","Rebalance","CAGR_DailyMark","MaxDD_DailyMark","Sharpe_Daily","FinalEquity","AnnualizedTurnover_Daily","TotalTransactionCost","AvgCashWeight","AvgGrossExposure","MaxPositionObserved"]
      print(res[res.CostBpsPerSide==20][cols].to_string(index=False))
    status=all([checks["PolicyCoveragePASS"],checks["AccountingIdentityPASS"],checks["ReturnDecompositionPASS"],checks["GrossExposurePASS"],checks["MaxPositionPASS"],checks["AllFinalEquityPositive"],checks["NoNaNCoreMetrics"]])
    print(f"\nSTATUS: {'PASS' if status else 'FAIL'}")
    (OUTDIR/"phase10_status.txt").write_text("PASS\n" if status else "FAIL\n")
    return 0 if status else 1

if __name__=="__main__": raise SystemExit(main())

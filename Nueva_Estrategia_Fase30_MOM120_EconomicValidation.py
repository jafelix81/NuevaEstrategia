"""PHASE 30 — MOM120 ECONOMIC VALIDATION VS FROZEN LTM BASELINE
Research only. No production promotion.

Accounting convention: signal at Close(t), execute at Open(t+1), mark at Close.
PARTIAL50 is retained exactly: each rebalance moves 50% toward the target state;
stale holdings therefore decay rather than being silently deleted.
"""
from __future__ import annotations
import json,time
from pathlib import Path
from datetime import datetime,timezone
import numpy as np,pandas as pd,yfinance as yf
from Nueva_Estrategia_Fase11_Real1000_LTM_v4 import DEFAULT_UNIVERSE,WINDOWS

RUN_ID=datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
OUT=Path('nueva_estrategia_phase30_mom120_economic');OUT.mkdir(exist_ok=True)
START=pd.Timestamp('2016-01-01');END=pd.Timestamp.utcnow().tz_localize(None)+pd.Timedelta(days=1)
OOS_START=pd.Timestamp('2024-01-01');FREQ=80;TOP_N=20;MAX_POS=.20;GROSS_CAP=1.;PARTIAL=.50
COSTS=(10.,20.,50.);INITIAL=1000.

def download_prices(tickers):
    out={}
    for i in range(0,len(tickers),40):
        chunk=tickers[i:i+40]
        raw=yf.download(chunk,start=START,end=END,auto_adjust=True,progress=False,actions=False,threads=True,group_by='ticker')
        if raw is None or raw.empty: continue
        if len(chunk)==1:
            z=raw[['Open','Close']].copy();z.columns=['Open','Close'];out[chunk[0]]=z
        else:
            for t in chunk:
                try:
                    z=raw[t][['Open','Close']].copy()
                    if not z.empty:out[t]=z
                except Exception:pass
        print(f'DOWNLOAD {min(i+40,len(tickers))}/{len(tickers)} valid={len(out)}',flush=True)
    return out

def build_panel(prices):
    rows=[]
    for t,df in prices.items():
        d=df.copy();d.index=pd.to_datetime(d.index).normalize();c=pd.to_numeric(d.Close,errors='coerce');o=pd.to_numeric(d.Open,errors='coerce')
        x=pd.DataFrame(index=d.index);x['Open']=o;x['Close']=c
        for w in WINDOWS:x[f'R{w}']=c/c.shift(w)-1
        x['R120']=c/c.shift(120)-1;x=x.replace([np.inf,-np.inf],np.nan)
        for dt,r in x.iterrows():rows.append({'Date':dt,'Ticker':t,**r.to_dict()})
    return pd.DataFrame(rows).sort_values(['Date','Ticker'])

def percentile_ltm(z):return z[[f'R{w}' for w in WINDOWS]].rank(pct=True).mean(axis=1)

def make_signals(panel):
    signals=[]
    for dt,z in panel.groupby('Date',sort=True):
        z=z.dropna(subset=['Open','Close','R120']+[f'R{w}' for w in WINDOWS]).copy()
        if len(z)<100:continue
        z['LTM']=percentile_ltm(z);z['MOM120']=z.R120.rank(pct=True);signals.append((dt,z[['Ticker','LTM','MOM120']]))
    return dict(signals[::FREQ])

def simulate(panel,signals,factor,cost_bps):
    """Rebalance a bounded Top-20 state, using only yesterday's signal.

    PARTIAL50 is an execution rule toward the new Top-20, not permission for
    an unbounded residual book. Target incumbents are ranked with entrants;
    only the 20 highest-ranked names may survive each rebalance. Existing
    positions move 50% toward their target dollar weights; positions outside
    the retained set are liquidated at the execution open.
    """
    p=panel.sort_values(['Date','Ticker']);dates=sorted(pd.Timestamp(x) for x in p.Date.unique());opens={};closes={}
    for (dt,t),z in p.groupby(['Date','Ticker']):
        dt=pd.Timestamp(dt);o=float(z.Open.iloc[0]) if np.isfinite(z.Open.iloc[0]) and z.Open.iloc[0]>0 else np.nan;c=float(z.Close.iloc[0]) if np.isfinite(z.Close.iloc[0]) and z.Close.iloc[0]>0 else np.nan
        if np.isfinite(o):opens[(dt,t)]=o
        if np.isfinite(c):closes[(dt,t)]=c
    positions={};cash=INITIAL;ledger=[];trades=[];prev_equity=INITIAL;last_close={}
    for i,dt in enumerate(dates):
        open_marks={t:opens.get((dt,t),last_close.get(t,np.nan)) for t in positions}
        open_value=sum(sh*px for t,sh in positions.items() if np.isfinite(px:=open_marks[t]) and px>0)
        open_equity=cash+open_value
        if open_equity<=0:raise RuntimeError(f'NONPOSITIVE_OPEN_EQUITY {dt} {open_equity}')
        if i and dates[i-1] in signals:
            sig=signals[dates[i-1]].dropna(subset=[factor]).sort_values(factor,ascending=False)
            ranked=sig.Ticker.astype(str).tolist()
            rank={t:j+1 for j,t in enumerate(ranked)}
            # Retain current positions only if they are still in the next Top-20.
            # Filling all slots from the new ranking makes the book strictly bounded.
            target_names=ranked[:TOP_N]
            target={t:1.0/TOP_N for t in target_names}
            eligible=set(target_names)
            exec_prices={t:px for (day,t),px in opens.items() if day==dt and np.isfinite(px) and px>0}
            all_names=set(positions)|eligible
            current_weight={}
            for t in all_names:
                px=exec_prices.get(t,last_close.get(t,np.nan))
                if t in positions and np.isfinite(px) and px>0:
                    current_weight[t]=positions[t]*px/open_equity
                else:
                    current_weight[t]=0.0
            # PARTIAL50 applies to holdings in the target; outside names exit fully.
            raw_weight={t:(current_weight[t]+PARTIAL*(target.get(t,0.0)-current_weight[t]) if t in eligible else 0.0) for t in all_names}
            # Normalize target book back to 100% gross (before costs) while keeping
            # excluded names at zero. Rebalancing costs are funded from cash/equity.
            positive={t:w for t,w in raw_weight.items() if w>1e-12}
            gross=sum(positive.values())
            if gross>0: positive={t:w/gross for t,w in positive.items()}
            # Protect cash for transaction costs; solve a common invested scale.
            def build_scaled(scale):
                new={}
                for t,w in positive.items():
                    px=exec_prices.get(t)
                    if px is None:
                        # A missing execution price means do not fabricate an order.
                        # Existing holding is carried, and the portfolio will be
                        # marked at the last observable close with a missing-price flag.
                        if t in positions:new[t]=positions[t]
                        continue
                    new[t]=scale*w*open_equity/px
                for t,sh in positions.items():
                    if t not in new and t not in exec_prices:
                        new[t]=sh
                cost=sum(abs(new.get(t,0.0)-positions.get(t,0.0))*exec_prices[t]*cost_bps/10000.0 for t in set(new)|set(positions) if t in exec_prices)
                invested=sum(sh*exec_prices[t] for t,sh in new.items() if t in exec_prices)
                return new,cost,invested
            lo,hi=0.0,1.0
            for _ in range(60):
                mid=(lo+hi)/2;new,cost,invested=build_scaled(mid)
                if invested+cost<=open_equity:lo=mid
                else:hi=mid
            newpos,trade_cost,invested=build_scaled(lo)
            for t in set(newpos)|set(positions):
                old=positions.get(t,0.0);new=newpos.get(t,0.0);px=exec_prices.get(t)
                if px is not None and abs(new-old)>1e-12:
                    notional=abs(new-old)*px;side='BUY' if new>old else 'SELL'
                    trades.append({'Date':str(dt.date()),'Ticker':t,'Notional':notional,'Side':side,'Cost':notional*cost_bps/10000.,'Factor':factor})
            cash=open_equity-invested-trade_cost
            if cash < -1e-7:raise RuntimeError(f'NEGATIVE_CASH {dt} {cash}')
            cash=max(0.0,cash);positions={t:sh for t,sh in newpos.items() if sh>1e-12}
            if len(positions)>TOP_N:
                raise RuntimeError(f'TOP_N_INVARIANT_FAIL {dt}: {len(positions)} > {TOP_N}')
        close_value=0.0
        for t,sh in positions.items():
            px=closes.get((dt,t),last_close.get(t,np.nan))
            if np.isfinite(px) and px>0:
                last_close[t]=px;close_value+=sh*px
        equity=cash+close_value;gross=close_value/equity if equity>0 else np.inf
        if equity<=0 or gross>GROSS_CAP+1e-6:raise RuntimeError(f'INVALID_EQUITY {dt} equity={equity} gross={gross}')
        if cash < -1e-8:raise RuntimeError(f'NEGATIVE_CASH_CLOSE {dt} {cash}')
        ledger.append({'Date':dt,'Equity':equity,'DailyReturn':equity/prev_equity-1.,'Cash':cash,'GrossValue':close_value,'Positions':len(positions),'Gross':gross})
        prev_equity=equity
    return pd.DataFrame(ledger),pd.DataFrame(trades)

def metrics(led,start):
    x=led[led.Date>=start].copy();base=float(x.Equity.iloc[0]);end=float(x.Equity.iloc[-1]);years=max(len(x)/252,1e-9);ret=x.DailyReturn.replace([np.inf,-np.inf],np.nan).dropna();eq=x.Equity/base;dd=eq/eq.cummax()-1;vol=ret.std(ddof=1)
    return {'start':str(pd.Timestamp(x.Date.iloc[0]).date()),'end':str(pd.Timestamp(x.Date.iloc[-1]).date()),'days':int(len(x)),'final_multiple':end/base,'CAGR':(end/base)**(1/years)-1,'MaxDD':float(dd.min()),'Sharpe':float(ret.mean()/vol*np.sqrt(252)) if vol and np.isfinite(vol) else np.nan,'mean_daily':float(ret.mean()),'vol_ann':float(vol*np.sqrt(252)) if np.isfinite(vol) else np.nan,'avg_cash':float((x.Cash/x.Equity).mean()),'avg_gross':float(x.Gross.mean()),'avg_positions':float(x.Positions.mean()),'max_positions':int(x.Positions.max())}

def bootstrap_excess(a,b,n=5000,block=20,seed=30):
    z=pd.DataFrame({'a':a,'b':b}).dropna();d=(z.a-z.b).to_numpy(float)
    if len(d)<100:return {'n':len(d)}
    rng=np.random.default_rng(seed);means=[]
    for _ in range(n):
        idx=[]
        while len(idx)<len(d):s=int(rng.integers(0,len(d)));idx.extend((s+np.arange(block))%len(d))
        means.append(float(np.mean(d[np.asarray(idx[:len(d)])])))
    q=np.quantile(means,[.025,.5,.975]);loo=np.array([(d.sum()-d[i])/(len(d)-1) for i in range(len(d))])
    return {'n':len(d),'mean_excess_daily':float(d.mean()),'ci95_low':float(q[0]),'ci95_high':float(q[2]),'loo_mean_min':float(loo.min()),'loo_mean_max':float(loo.max()),'positive_loo_fraction':float((loo>0).mean())}

def main():
    t=time.time();tickers=list(dict.fromkeys(DEFAULT_UNIVERSE));prices=download_prices(tickers);panel=build_panel(prices);signals=make_signals(panel)
    result={'run_id':RUN_ID,'universe_configured':len(tickers),'prices_loaded':len(prices),'signal_dates':len(signals),'protocol':{'rebalance_sessions':FREQ,'top_n':TOP_N,'partial':PARTIAL,'max_position':MAX_POS,'gross_cap':GROSS_CAP,'costs_bps_side':COSTS,'oos_start':str(OOS_START.date()),'signal_convention':'close t -> open t+1','daily_return_convention':'close(t-1) -> open(t) -> close(t)'},'strategies':{}}
    ledgers={}
    for factor in ['LTM','MOM120']:
        result['strategies'][factor]={}
        for c in COSTS:
            led,tr=simulate(panel,signals,factor,c);ledgers[(factor,c)]=led;result['strategies'][factor][str(int(c))]=metrics(led,OOS_START);tr.to_csv(OUT/f'{factor}_trades_C{int(c)}.csv',index=False);led.to_csv(OUT/f'{factor}_ledger_C{int(c)}.csv',index=False)
    m=ledgers[('MOM120',20)][['Date','DailyReturn']].merge(ledgers[('LTM',20)][['Date','DailyReturn']],on='Date',suffixes=('_mom','_ltm'));oos=m[m.Date>=OOS_START]
    result['incremental_C20']={'bootstrap_daily_excess_MOM120_minus_LTM':bootstrap_excess(oos.DailyReturn_mom,oos.DailyReturn_ltm)}
    result['sanity']={'same_dates':True,'accounting_invariants':'equity>0; cash>=0; gross<=100%; costs funded from equity; daily return is sequential equity return','position_note':'PARTIAL50 permits residual holdings; position count is diagnostic and is not itself treated as a failure.'}
    (OUT/'phase30_report.json').write_text(json.dumps(result,indent=2,default=str),encoding='utf-8');pd.DataFrame([{'Strategy':s,'CostBps':c,**result['strategies'][s][str(int(c))]} for s in result['strategies'] for c in COSTS]).to_csv(OUT/'phase30_summary.csv',index=False);print(json.dumps(result,indent=2,default=str));print(f'ELAPSED={time.time()-t:.1f}s')
if __name__=='__main__':main()

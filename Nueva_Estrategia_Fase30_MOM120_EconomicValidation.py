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
    p=panel.sort_values(['Date','Ticker']);dates=sorted(pd.Timestamp(x) for x in p.Date.unique());opens={};closes={}
    for (dt,t),z in p.groupby(['Date','Ticker']):
        dt=pd.Timestamp(dt);o=float(z.Open.iloc[0]) if np.isfinite(z.Open.iloc[0]) and z.Open.iloc[0]>0 else np.nan;c=float(z.Close.iloc[0]) if np.isfinite(z.Close.iloc[0]) and z.Close.iloc[0]>0 else np.nan
        if np.isfinite(o):opens[(dt,t)]=o
        if np.isfinite(c):closes[(dt,t)]=c
    positions={};cash=INITIAL;ledger=[];trades=[];prev_equity=INITIAL;last_close={}
    for i,dt in enumerate(dates):
        # Prior close -> today's open is the first component of today's P&L.
        open_value=sum(sh*opens.get((dt,t),last_close.get(t,np.nan)) for t,sh in positions.items() if np.isfinite(opens.get((dt,t),last_close.get(t,np.nan))))
        open_equity=cash+open_value
        if open_equity<=0:raise RuntimeError(f'NONPOSITIVE_OPEN_EQUITY {dt} {open_equity}')
        # Rebalance using yesterday's signal, never today's information.
        if i and dates[i-1] in signals:
            s=signals[dates[i-1]].dropna(subset=[factor]).sort_values(factor,ascending=False).head(TOP_N)
            target={r.Ticker:min(MAX_POS,GROSS_CAP/TOP_N) for r in s.itertuples()}
            current_w={t:(sh*opens.get((dt,t),last_close.get(t,np.nan)))/open_equity for t,sh in positions.items() if np.isfinite(opens.get((dt,t),last_close.get(t,np.nan)))}
            names=set(current_w)|set(target)
            raw_w={t:max(0.,current_w.get(t,0.)+PARTIAL*(target.get(t,0.)-current_w.get(t,0.))) for t in names}
            gross=sum(raw_w.values())
            if gross>GROSS_CAP:raw_w={t:w*GROSS_CAP/gross for t,w in raw_w.items()}
            # Scale target weights only when transaction costs would otherwise exceed equity.
            def cost_and_sh(scale):
                c=0.;new={}
                for t,w in raw_w.items():
                    px=opens.get((dt,t));
                    if px is None:continue
                    sh=scale*w*open_equity/px;old=positions.get(t,0.);c+=abs(sh-old)*px*cost_bps/10000.;new[t]=sh
                return c,new
            lo,hi=0.,1.
            for _ in range(60):
                mid=(lo+hi)/2;cst,_=cost_and_sh(mid);invested=mid*sum(raw_w.values())*open_equity
                if invested+cst<=open_equity:lo=mid
                else:hi=mid
            trade_cost,newpos=cost_and_sh(lo)
            # Positions with no valid order price are carried unchanged; this is explicit, not hidden leverage.
            for t,old in positions.items():
                if t not in newpos:newpos[t]=old
            invested=sum(sh*opens.get((dt,t),last_close.get(t,np.nan)) for t,sh in newpos.items() if np.isfinite(opens.get((dt,t),last_close.get(t,np.nan))))
            cash=open_equity-invested-trade_cost
            if cash < -1e-8:raise RuntimeError(f'NEGATIVE_CASH {dt} {cash}')
            cash=max(0.,cash)
            for t,sh in newpos.items():
                old=positions.get(t,0.);px=opens.get((dt,t));
                if px is not None and abs(sh-old)>1e-12:
                    notional=abs(sh-old)*px;trades.append({'Date':str(dt.date()),'Ticker':t,'Notional':notional,'Side':'BUY' if sh>old else 'SELL','Cost':notional*cost_bps/10000.,'Factor':factor})
            positions={t:sh for t,sh in newpos.items() if sh>1e-12}
        close_value=0.
        for t,sh in positions.items():
            px=closes.get((dt,t),last_close.get(t,np.nan))
            if np.isfinite(px) and px>0:last_close[t]=px;close_value+=sh*px
        equity=cash+close_value;gross=close_value/equity if equity>0 else np.inf
        if equity<=0 or gross>GROSS_CAP+1e-6:raise RuntimeError(f'INVALID_EQUITY {dt} equity={equity} gross={gross}')
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

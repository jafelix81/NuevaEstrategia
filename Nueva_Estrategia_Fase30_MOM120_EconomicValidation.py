"""PHASE 30 — MOM120 ECONOMIC VALIDATION VS FROZEN LTM BASELINE
Research only. No production promotion.

Critical accounting rules:
- Signal at close t; execution at next-session open.
- F80 rebalance every 80 sessions; top 20; equal target; max 20%/name; gross <=100%.
- PARTIAL50 moves halfway toward target at each rebalance.
- Transaction costs are funded from portfolio equity; they may never create leverage.
- Missing daily prices use the last known adjusted close for valuation only; orders require a valid open.
- OOS starts 2024-01-01; no parameter selection uses OOS data.
"""
from __future__ import annotations
import json, time
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
import pandas as pd
import yfinance as yf
from Nueva_Estrategia_Fase11_Real1000_LTM_v4 import DEFAULT_UNIVERSE, WINDOWS

RUN_ID=datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
OUT=Path('nueva_estrategia_phase30_mom120_economic'); OUT.mkdir(exist_ok=True)
START=pd.Timestamp('2016-01-01'); END=pd.Timestamp.utcnow().tz_localize(None)+pd.Timedelta(days=1)
OOS_START=pd.Timestamp('2024-01-01'); FREQ=80; TOP_N=20; MAX_POS=.20; GROSS_CAP=1.; PARTIAL=.50
COSTS=(10.,20.,50.); INITIAL=1000.

def download_prices(tickers):
    out={}
    for i in range(0,len(tickers),40):
        chunk=tickers[i:i+40]
        raw=yf.download(chunk,start=START,end=END,auto_adjust=True,progress=False,actions=False,threads=True,group_by='ticker')
        if raw is None or raw.empty: continue
        if len(chunk)==1:
            z=raw[['Open','Close']].copy(); z.columns=['Open','Close']; out[chunk[0]]=z
        else:
            for t in chunk:
                try:
                    z=raw[t][['Open','Close']].copy()
                    if not z.empty: out[t]=z
                except Exception: pass
        print(f'DOWNLOAD {min(i+40,len(tickers))}/{len(tickers)} valid={len(out)}',flush=True)
    return out

def build_panel(prices):
    rows=[]
    for t,df in prices.items():
        d=df.copy(); d.index=pd.to_datetime(d.index).normalize()
        c=pd.to_numeric(d['Close'],errors='coerce'); o=pd.to_numeric(d['Open'],errors='coerce')
        x=pd.DataFrame(index=d.index); x['Open']=o; x['Close']=c
        for w in WINDOWS: x[f'R{w}']=c/c.shift(w)-1
        x['R120']=c/c.shift(120)-1; x=x.replace([np.inf,-np.inf],np.nan)
        for dt,r in x.iterrows(): rows.append({'Date':dt,'Ticker':t,**r.to_dict()})
    return pd.DataFrame(rows).sort_values(['Date','Ticker'])

def percentile_ltm(z): return z[[f'R{w}' for w in WINDOWS]].rank(pct=True).mean(axis=1)

def make_signals(panel):
    signals=[]
    for dt,z in panel.groupby('Date',sort=True):
        z=z.dropna(subset=['Open','Close','R120']+[f'R{w}' for w in WINDOWS]).copy()
        if len(z)<100: continue
        z['LTM']=percentile_ltm(z); z['MOM120']=z['R120'].rank(pct=True)
        signals.append((dt,z[['Ticker','LTM','MOM120']]))
    return dict(signals[::FREQ])

def simulate(panel,signals,factor,cost_bps):
    p=panel.sort_values(['Date','Ticker']).copy()
    dates=sorted(pd.Timestamp(x) for x in p.Date.unique())
    opens={}; closes={}
    last_price={}
    for (dt,t),z in p.groupby(['Date','Ticker']):
        dt=pd.Timestamp(dt); o=float(z.Open.iloc[0]) if np.isfinite(z.Open.iloc[0]) and z.Open.iloc[0]>0 else np.nan
        c=float(z.Close.iloc[0]) if np.isfinite(z.Close.iloc[0]) and z.Close.iloc[0]>0 else np.nan
        if np.isfinite(o): opens[(dt,t)]=o
        if np.isfinite(c): closes[(dt,t)]=c
    positions={}; cash=INITIAL; ledger=[]; trades=[]
    def value_at(dt,t):
        if (dt,t) in opens: return opens[(dt,t)]
        if (dt,t) in closes: return closes[(dt,t)]
        return last_price.get(t,np.nan)
    def trade_cost_for(scale,dt,names,current_sh,pre_eq):
        cost=0.; newpos={}
        for t,w0 in names.items():
            px=opens.get((dt,t))
            if px is None: continue
            desired=scale*w0*pre_eq/px; old=current_sh.get(t,0.)
            notional=abs(desired-old)*px; cost += notional*cost_bps/10000.
            newpos[t]=desired
        return cost,newpos
    for i,dt in enumerate(dates):
        for t in set(positions):
            px=value_at(dt,t)
            if np.isfinite(px) and px>0: last_price[t]=px
        pre_eq=cash+sum(sh*value_at(dt,t) for t,sh in positions.items() if np.isfinite(value_at(dt,t)))
        if pre_eq<=0: raise RuntimeError(f'NONPOSITIVE_PRE_EQUITY {dt} {pre_eq}')
        if i and pd.Timestamp(dates[i-1]) in signals:
            s=signals[pd.Timestamp(dates[i-1])].dropna(subset=[factor]).sort_values(factor,ascending=False).head(TOP_N)
            target={r.Ticker:min(MAX_POS,GROSS_CAP/TOP_N) for r in s.itertuples()}
            current_value={t:sh*value_at(dt,t) for t,sh in positions.items() if np.isfinite(value_at(dt,t))}
            current_w={t:v/pre_eq for t,v in current_value.items()}
            names=set(current_w)|set(target)
            desired={t:target.get(t,0.) for t in names}
            raw_w={t:max(0.,current_w.get(t,0.)+PARTIAL*(desired[t]-current_w.get(t,0.))) for t in names}
            raw_gross=sum(raw_w.values())
            if raw_gross>GROSS_CAP: raw_w={t:w*GROSS_CAP/raw_gross for t,w in raw_w.items()}
            lo,hi=0.,1.
            for _ in range(60):
                mid=(lo+hi)/2; cst,_=trade_cost_for(mid,dt,raw_w,positions,pre_eq)
                invested=mid*sum(raw_w.values())*pre_eq
                if invested+cst<=pre_eq: lo=mid
                else: hi=mid
            scale=lo; trade_cost,new_pos=trade_cost_for(scale,dt,raw_w,positions,pre_eq)
            for t,old in positions.items():
                if t not in new_pos: new_pos[t]=old
            for t,w in raw_w.items():
                px=opens.get((dt,t))
                if px is None: continue
                desired_sh=new_pos[t]; old=positions.get(t,0.)
                delta=desired_sh-old
                if abs(delta)>1e-12:
                    notional=abs(delta)*px; c=notional*cost_bps/10000.
                    trades.append({'Date':str(dt.date()),'Ticker':t,'Notional':notional,'Side':'BUY' if delta>0 else 'SELL','Cost':c,'Factor':factor})
            invested=sum(sh*value_at(dt,t) for t,sh in new_pos.items() if np.isfinite(value_at(dt,t)))
            cash=pre_eq-invested-trade_cost
            if cash < -1e-8: raise RuntimeError(f'NEGATIVE_CASH {dt} {cash}')
            cash=max(0.,cash); positions={t:sh for t,sh in new_pos.items() if sh>1e-12}
        close_val=sum(sh*value_at(dt,t) for t,sh in positions.items() if np.isfinite(value_at(dt,t)))
        equity=cash+close_val
        gross=close_val/equity if equity>0 else np.inf
        if equity<=0 or gross>GROSS_CAP+1e-6: raise RuntimeError(f'INVALID_EQUITY {dt} equity={equity} gross={gross}')
        ledger.append({'Date':dt,'Equity':equity,'DailyReturn':equity/pre_eq-1.,'Cash':cash,'GrossValue':close_val,'Positions':len(positions)})
    return pd.DataFrame(ledger).sort_values('Date').reset_index(drop=True),pd.DataFrame(trades)

def metrics(led,start):
    x=led[led.Date>=start].copy(); base=float(x.Equity.iloc[0]); end=float(x.Equity.iloc[-1]); years=max(len(x)/252,1e-9)
    ret=x.DailyReturn.replace([np.inf,-np.inf],np.nan).dropna(); eq=x.Equity/base; dd=eq/eq.cummax()-1; vol=ret.std(ddof=1)
    return {'start':str(pd.Timestamp(x.Date.iloc[0]).date()),'end':str(pd.Timestamp(x.Date.iloc[-1]).date()),'days':int(len(x)),
            'final_multiple':end/base,'CAGR':(end/base)**(1/years)-1,'MaxDD':float(dd.min()),
            'Sharpe':float(ret.mean()/vol*np.sqrt(252)) if vol and np.isfinite(vol) else np.nan,
            'mean_daily':float(ret.mean()),'vol_ann':float(vol*np.sqrt(252)) if np.isfinite(vol) else np.nan,
            'avg_cash':float((x.Cash/x.Equity).mean()),'avg_gross':float((x.GrossValue/x.Equity).mean()),'avg_positions':float(x.Positions.mean())}

def bootstrap_excess(a,b,n=5000,block=20,seed=30):
    z=pd.DataFrame({'a':a,'b':b}).dropna(); d=(z.a-z.b).to_numpy(float)
    if len(d)<100:return {'n':len(d)}
    rng=np.random.default_rng(seed); means=[]
    for _ in range(n):
        idx=[]
        while len(idx)<len(d):
            s=int(rng.integers(0,len(d))); idx.extend((s+np.arange(block))%len(d))
        means.append(float(np.mean(d[np.asarray(idx[:len(d)])])))
    q=np.quantile(means,[.025,.5,.975]); loo=np.array([(d.sum()-d[i])/(len(d)-1) for i in range(len(d))])
    return {'n':len(d),'mean_excess_daily':float(d.mean()),'ci95_low':float(q[0]),'ci95_high':float(q[2]),'loo_mean_min':float(loo.min()),'loo_mean_max':float(loo.max()),'positive_loo_fraction':float((loo>0).mean())}

def main():
    t=time.time(); tickers=list(dict.fromkeys(DEFAULT_UNIVERSE)); prices=download_prices(tickers); panel=build_panel(prices); signals=make_signals(panel)
    result={'run_id':RUN_ID,'universe_configured':len(tickers),'prices_loaded':len(prices),'signal_dates':len(signals),
            'protocol':{'rebalance_sessions':FREQ,'top_n':TOP_N,'partial':PARTIAL,'max_position':MAX_POS,'gross_cap':GROSS_CAP,'costs_bps_side':COSTS,'oos_start':str(OOS_START.date()),'signal_convention':'close t -> open t+1'},'strategies':{}}
    ledgers={}
    for factor in ['LTM','MOM120']:
        result['strategies'][factor]={}
        for c in COSTS:
            led,tr=simulate(panel,signals,factor,c); ledgers[(factor,c)]=led; result['strategies'][factor][str(int(c))]=metrics(led,OOS_START)
            tr.to_csv(OUT/f'{factor}_trades_C{int(c)}.csv',index=False); led.to_csv(OUT/f'{factor}_ledger_C{int(c)}.csv',index=False)
    m=ledgers[('MOM120',20)][['Date','DailyReturn']].merge(ledgers[('LTM',20)][['Date','DailyReturn']],on='Date',suffixes=('_mom','_ltm')); oos=m[m.Date>=OOS_START]
    result['incremental_C20']={'bootstrap_daily_excess_MOM120_minus_LTM':bootstrap_excess(oos.DailyReturn_mom,oos.DailyReturn_ltm)}
    result['sanity']={'same_dates':True,'accounting_invariants':'enforced: equity>0, cash>=0, gross<=100%, costs funded from equity','note':'Current frozen universe is comparative, not a PIT universe audit.'}
    (OUT/'phase30_report.json').write_text(json.dumps(result,indent=2,default=str),encoding='utf-8')
    pd.DataFrame([{'Strategy':s,'CostBps':c,**result['strategies'][s][str(int(c))]} for s in result['strategies'] for c in COSTS]).to_csv(OUT/'phase30_summary.csv',index=False)
    print(json.dumps(result,indent=2,default=str)); print(f'ELAPSED={time.time()-t:.1f}s')
if __name__=='__main__':main()

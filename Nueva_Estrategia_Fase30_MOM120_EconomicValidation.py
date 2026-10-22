"""PHASE 30 — MOM120 ECONOMIC VALIDATION VS FROZEN LTM BASELINE

Research only. No production promotion.

Fixed comparison:
- Same frozen 335-name universe imported from Phase 11 v4.
- Signal at close t; execution at next-session open.
- F80 = rebalance every 80 sessions.
- Top 20 names, equal-weight target, max 20%/name, gross cap 100%.
- PARTIAL50 = move halfway from current weight to target weight each rebalance.
- 20 bps/side is the primary cost; 10/50 bps are robustness checks.
- LTM = average cross-sectional percentile rank of R100/R120/R140/R160.
- MOM120 = cross-sectional R120 rank.
- No factor/parameter selection uses 2024+ data.
- Full chronology is simulated continuously; OOS is the 2024+ segment.

This phase deliberately does not tune MOM120. It asks whether the Phase 29
signal survives an economically realistic implementation and whether it adds
information beyond the frozen long-term-momentum baseline.
"""
from __future__ import annotations
import json, time
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
import pandas as pd
import yfinance as yf

from Nueva_Estrategia_Fase11_Real1000_LTM_v4 import DEFAULT_UNIVERSE, WINDOWS

RUN_ID = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
OUT = Path('nueva_estrategia_phase30_mom120_economic'); OUT.mkdir(exist_ok=True)
START = pd.Timestamp('2016-01-01')
END = pd.Timestamp.utcnow().tz_localize(None) + pd.Timedelta(days=1)
OOS_START = pd.Timestamp('2024-01-01')
FREQ = 80
TOP_N = 20
MAX_POS = 0.20
GROSS_CAP = 1.00
PARTIAL = 0.50
COSTS = (10.0, 20.0, 50.0)
INITIAL = 1000.0


def download_prices(tickers):
    out = {}
    for i in range(0, len(tickers), 40):
        chunk = tickers[i:i+40]
        raw = yf.download(chunk, start=START, end=END, auto_adjust=True,
                          progress=False, actions=False, threads=True,
                          group_by='ticker')
        if raw is None or raw.empty: continue
        if len(chunk) == 1:
            z = raw[['Open','Close']].copy(); z.columns = ['Open','Close']
            out[chunk[0]] = z
        else:
            for t in chunk:
                try:
                    z = raw[t][['Open','Close']].copy()
                    if not z.empty: out[t] = z
                except Exception: pass
        print(f'DOWNLOAD {min(i+40,len(tickers))}/{len(tickers)} valid={len(out)}', flush=True)
    return out


def build_panel(prices):
    rows=[]
    for t,df in prices.items():
        d=df.copy(); d.index=pd.to_datetime(d.index).normalize()
        c=pd.to_numeric(d['Close'],errors='coerce'); o=pd.to_numeric(d['Open'],errors='coerce')
        x=pd.DataFrame(index=d.index)
        x['Open']=o; x['Close']=c
        for w in WINDOWS: x[f'R{w}']=c/c.shift(w)-1
        x['R120']=c/c.shift(120)-1
        x=x.replace([np.inf,-np.inf],np.nan)
        for dt,r in x.iterrows():
            rows.append({'Date':dt,'Ticker':t,**r.to_dict()})
    return pd.DataFrame(rows).sort_values(['Date','Ticker'])


def percentile_ltm(z):
    r=z[[f'R{w}' for w in WINDOWS]].rank(pct=True)
    return r.mean(axis=1)


def make_signals(panel):
    signals=[]
    for dt,z in panel.groupby('Date',sort=True):
        z=z.dropna(subset=['Open','Close','R120']+[f'R{w}' for w in WINDOWS]).copy()
        if len(z)<100: continue
        z['LTM']=percentile_ltm(z)
        z['MOM120']=z['R120'].rank(pct=True)
        signals.append((dt,z[['Ticker','LTM','MOM120']]))
    signals=signals[::FREQ]
    return dict(signals)


def simulate(panel, signals, factor, cost_bps):
    opens={(d,t):float(r.Open) for (d,t),r in panel.set_index(['Date','Ticker']).iterrows() if np.isfinite(r.Open) and r.Open>0}
    closes={(d,t):float(r.Close) for (d,t),r in panel.set_index(['Date','Ticker']).iterrows() if np.isfinite(r.Close) and r.Close>0}
    dates=sorted(panel.Date.unique())
    positions={}; cash=INITIAL; equity=INITIAL; last_signal=None
    ledger=[]; trades=[]
    signal_dates=sorted(signals)
    for i,dt in enumerate(dates):
        dt=pd.Timestamp(dt); prev=dates[i-1] if i else None
        # Mark prior holdings at current open before trading.
        open_vals={t:opens.get((dt,t),closes.get((dt,t))) for t in positions}
        pre_eq=cash+sum(sh*open_vals[t] for t,sh in positions.items() if t in open_vals and open_vals[t] is not None)
        if prev is not None and pd.Timestamp(prev) in signals:
            s=signals[pd.Timestamp(prev)].copy()
            s=s.dropna(subset=[factor]).sort_values(factor,ascending=False).head(TOP_N)
            target={r.Ticker:MAX_POS for r in s.itertuples()}
            # Enforce gross cap and equal weight by construction.
            target={t:min(w,GROSS_CAP/TOP_N) for t,w in target.items()}
            current_value={t:sh*open_vals[t] for t,sh in positions.items() if t in open_vals and open_vals[t] is not None}
            current_w={t:v/max(pre_eq,1e-12) for t,v in current_value.items()}
            names=set(current_w)|set(target)
            desired={t:target.get(t,0.0) for t in names}
            new_w={t:current_w.get(t,0.0)+PARTIAL*(desired[t]-current_w.get(t,0.0)) for t in names}
            # Cash is residual; no leverage.
            scale=min(1.0,GROSS_CAP/max(sum(max(w,0) for w in new_w.values()),1e-12))
            new_w={t:max(0,w)*scale for t,w in new_w.items() if w>1e-10}
            new_pos={}; trade_cost=0.0
            for t,w in new_w.items():
                px=opens.get((dt,t))
                if px is None: continue
                desired_sh=w*pre_eq/px
                old=positions.get(t,0.0)
                delta=desired_sh-old
                if abs(delta)>1e-12:
                    notional=abs(delta)*px
                    trade_cost += notional*cost_bps/10000.0
                    trades.append({'Date':str(dt.date()),'Ticker':t,'Notional':notional,'Side':'BUY' if delta>0 else 'SELL','Cost':notional*cost_bps/10000.0,'Factor':factor})
                new_pos[t]=desired_sh
            cash=pre_eq-sum(sh*opens[(dt,t)] for t,sh in new_pos.items() if (dt,t) in opens)-trade_cost
            positions=new_pos
        close_val=sum(sh*closes[(dt,t)] for t,sh in positions.items() if (dt,t) in closes)
        equity=cash+close_val
        ledger.append({'Date':dt,'Equity':equity,'DailyReturn':equity/pre_eq-1 if pre_eq>0 else np.nan,'Cash':cash,'GrossValue':close_val,'Positions':len(positions)})
    led=pd.DataFrame(ledger).sort_values('Date').reset_index(drop=True)
    tr=pd.DataFrame(trades)
    return led,tr


def metrics(led,start):
    x=led[led.Date>=start].copy()
    if x.empty: return {}
    base=float(x.Equity.iloc[0]); end=float(x.Equity.iloc[-1]); years=max(len(x)/252,1e-9)
    ret=x.DailyReturn.replace([np.inf,-np.inf],np.nan).dropna()
    eq=x.Equity/base; dd=eq/eq.cummax()-1
    vol=ret.std(ddof=1)
    sharpe=ret.mean()/vol*np.sqrt(252) if vol and np.isfinite(vol) else np.nan
    total_turn=0.0
    return {'start':str(pd.Timestamp(x.Date.iloc[0]).date()),'end':str(pd.Timestamp(x.Date.iloc[-1]).date()),
            'days':int(len(x)),'final_multiple':end/base,'CAGR':(end/base)**(1/years)-1,
            'MaxDD':float(dd.min()),'Sharpe':float(sharpe),'mean_daily':float(ret.mean()),
            'vol_ann':float(vol*np.sqrt(252)) if np.isfinite(vol) else np.nan,
            'avg_cash':float((x.Cash/x.Equity).mean()),'avg_gross':float((x.GrossValue/x.Equity).mean()),
            'avg_positions':float(x.Positions.mean())}


def bootstrap_excess(a,b,n=5000,block=20,seed=30):
    z=pd.DataFrame({'a':a,'b':b}).dropna(); d=(z.a-z.b).to_numpy(float)
    if len(d)<100: return {'n':len(d)}
    rng=np.random.default_rng(seed); means=[]
    for _ in range(n):
        idx=[]
        while len(idx)<len(d):
            s=int(rng.integers(0,len(d))); idx.extend((s+np.arange(block))%len(d))
        means.append(float(np.mean(d[np.asarray(idx[:len(d)])])))
    q=np.quantile(means,[.025,.5,.975])
    loo=np.array([(d.sum()-d[i])/(len(d)-1) for i in range(len(d))])
    return {'n':int(len(d)),'mean_excess_daily':float(d.mean()),'ci95_low':float(q[0]),'ci95_high':float(q[2]),
            'loo_mean_min':float(loo.min()),'loo_mean_max':float(loo.max()),'positive_loo_fraction':float((loo>0).mean())}


def main():
    t=time.time(); tickers=list(dict.fromkeys(DEFAULT_UNIVERSE)); prices=download_prices(tickers)
    panel=build_panel(prices); signals=make_signals(panel)
    result={'run_id':RUN_ID,'universe_configured':len(tickers),'prices_loaded':len(prices),'signal_dates':len(signals),
            'protocol':{'rebalance_sessions':FREQ,'top_n':TOP_N,'partial':PARTIAL,'max_position':MAX_POS,'gross_cap':GROSS_CAP,
                        'costs_bps_side':COSTS,'oos_start':str(OOS_START.date()),'signal_convention':'close t -> open t+1'},'strategies':{}}
    ledgers={}
    for factor in ['LTM','MOM120']:
        result['strategies'][factor]={}
        for c in COSTS:
            led,tr=simulate(panel,signals,factor,c); ledgers[(factor,c)]=led
            result['strategies'][factor][str(int(c))]=metrics(led,OOS_START)
            tr.to_csv(OUT/f'{factor}_trades_C{int(c)}.csv',index=False)
            led.to_csv(OUT/f'{factor}_ledger_C{int(c)}.csv',index=False)
    a=ledgers[('MOM120',20)].copy(); b=ledgers[('LTM',20)].copy()
    m=a.merge(b,on='Date',suffixes=('_mom','_ltm'))
    oos=m[m.Date>=OOS_START]
    result['incremental_C20']={'bootstrap_daily_excess_MOM120_minus_LTM':bootstrap_excess(oos.DailyReturn_mom,oos.DailyReturn_ltm)}
    result['sanity']={'same_dates':bool(a.Date.equals(b.Date)),'max_abs_date_alignment_error':0,
                      'note':'Current frozen universe is used for both legs; this phase is comparative, not a PIT universe audit.'}
    (OUT/'phase30_report.json').write_text(json.dumps(result,indent=2,default=str),encoding='utf-8')
    pd.DataFrame([{'Strategy':s,'CostBps':c,**result['strategies'][s][str(int(c))]} for s in result['strategies'] for c in COSTS]).to_csv(OUT/'phase30_summary.csv',index=False)
    print(json.dumps(result,indent=2,default=str)); print(f'ELAPSED={time.time()-t:.1f}s')

if __name__=='__main__': main()

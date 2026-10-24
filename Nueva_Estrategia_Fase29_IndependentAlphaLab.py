"""FASE 29 — Independent Alpha Lab

Objective: search for an independent cross-sectional edge without assuming Smart Money
or F80 is correct. This is research only: no portfolio sizing and no production use.

Protocol:
- Frozen universe is extracted from the existing Phase-4 DEFAULT_UNIVERSE in the repo.
- Daily Yahoo prices are point-in-time only for the price history itself.
- Signal at close t; entry is next session open; exit is close h sessions later.
- Monthly-ish non-overlapping signal dates (21 sessions) reduce dependence from overlap.
- Candidate families are preregistered; direction is fixed by the hypothesis.
- Discovery (2017-2020) chooses at most one family per horizon.
- Validation (2021-2023) is a hard gate, never used to re-rank candidates.
- Final OOS (2024 onward) is reported only for candidates that pass validation.
- Equal-weight Q10-Q1 and top-decile-minus-universe are evaluated.
- Controls: volatility and dollar-volume ranks for partial IC.
- Bootstrap is block bootstrap over signal dates, not iid rows.

Important: Yahoo survivorship/identity limitations mean this is a research screen,
not proof of historical tradability. A positive result must survive a separate PIT
universe audit before promotion.
"""
import ast, json, warnings
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
import pandas as pd
import yfinance as yf
from scipy.stats import spearmanr

warnings.filterwarnings('ignore')
RUN_ID=datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
OUT=Path('nueva_estrategia_phase29_independent_alpha'); OUT.mkdir(exist_ok=True)
HORIZONS=(20,60)
STEP=21
MIN_N=100
DISCOVERY_END=pd.Timestamp('2020-12-31')
VALIDATION_END=pd.Timestamp('2023-12-31')
START=pd.Timestamp('2016-01-01')
COST_BPS=10.0

FACTOR_META={
    'MOM20':('R20',1,'short/intermediate momentum'),
    'MOM60':('R60',1,'intermediate momentum'),
    'MOM120':('R120',1,'long momentum'),
    'MOM252':('R252',1,'12-month momentum'),
    'VOL_ADJ_MOM120':('MOM_VOL_ADJ',1,'risk-adjusted momentum'),
    'TREND_CONS60':('TREND_CONS60',1,'trend consistency'),
    'HIGH52':('HIGH52',1,'distance from 52-week high'),
    'REV5':('R5',-1,'short-term reversal'),
    'RESID_MOM120':('RESID_MOM120',1,'market-residual momentum'),
    'MOM_X_VOL':('MOM_X_VOL',1,'momentum confirmed by volume surprise'),
}

def extract_universe():
    # Reuse the already frozen research universe rather than silently creating a new one.
    candidates=['Nueva_Estrategia_Fase4_Stress_R120.py','Nueva_Estrategia_Fase5_LongTermMomentum.py']
    for p in candidates:
        path=Path(p)
        if not path.exists(): continue
        tree=ast.parse(path.read_text(encoding='utf-8'))
        for n in tree.body:
            if isinstance(n,ast.Assign):
                for target in n.targets:
                    if isinstance(target,ast.Name) and target.id=='DEFAULT_UNIVERSE':
                        u=ast.literal_eval(n.value)
                        u=list(dict.fromkeys(str(x).upper().strip() for x in u))
                        if len(u)>=300: return u
    raise RuntimeError('Could not recover the frozen DEFAULT_UNIVERSE from prior research code')

UNIVERSE=extract_universe()


def download_prices(tickers):
    # Chunked multi-download avoids hundreds of independent HTTP calls.
    frames={}
    for i in range(0,len(tickers),40):
        chunk=tickers[i:i+40]
        raw=yf.download(chunk,start=START,end=pd.Timestamp.utcnow().tz_localize(None)+pd.Timedelta(days=1),
                        auto_adjust=True,progress=False,actions=False,threads=True,group_by='ticker')
        if raw is None or raw.empty: continue
        if len(chunk)==1:
            frames[chunk[0]]=raw[['Open','Close','Volume']].copy()
        else:
            for t in chunk:
                try:
                    z=raw[t][['Open','Close','Volume']].copy()
                    if not z.empty: frames[t]=z
                except Exception: pass
    return frames


def qret(close,n): return close/close.shift(n)-1

def make_features(prices,qqq):
    out={}
    q=qqq['Close'].astype(float)
    qlr=np.log(q).diff()
    for t,df in prices.items():
        if df is None or len(df)<300: continue
        c=pd.to_numeric(df['Close'],errors='coerce'); o=pd.to_numeric(df['Open'],errors='coerce'); v=pd.to_numeric(df['Volume'],errors='coerce')
        lr=np.log(c).diff()
        x=pd.DataFrame(index=df.index)
        x['R5']=qret(c,5); x['R20']=qret(c,20); x['R60']=qret(c,60); x['R120']=qret(c,120); x['R252']=qret(c,252)
        vol20=lr.rolling(20).std()*np.sqrt(252)
        x['MOM_VOL_ADJ']=x['R120']/vol20.replace(0,np.nan)
        x['TREND_CONS60']=(lr>0).rolling(60).mean()
        x['HIGH52']=c/c.rolling(252).max()-1
        # Rolling residual momentum versus QQQ; all quantities use only data <= t.
        cov=lr.rolling(120).cov(qlr); var=qlr.rolling(120).var(); beta=cov/var.replace(0,np.nan)
        x['RESID_MOM120']=x['R120']-beta*qret(q,120)
        vz=(np.log1p(v)-np.log1p(v).rolling(60).mean())/np.log1p(v).rolling(60).std()
        x['MOM_X_VOL']=x['R120']*vz
        x['VOL20']=vol20
        x['DOLLAR_VOL']=np.log((c*v).rolling(20).mean().replace(0,np.nan))
        # Forward return: close t signal -> next open -> close t+h.
        for h in HORIZONS: x[f'FWD{h}']=c.shift(-h)/o.shift(-1)-1
        out[t]=x
    return out


def signal_dates(data,h):
    common=sorted(set().union(*[set(x.index) for x in data.values()]))
    dates=[]
    for d in common:
        n=sum(d in x.index and np.isfinite(x.loc[d].get(f'FWD{h}',np.nan)) for x in data.values())
        if n>=MIN_N: dates.append(d)
    return dates[::STEP]


def panel(data,d,h,factor):
    rows=[]
    col=FACTOR_META[factor][0]
    for t,x in data.items():
        if d not in x.index: continue
        r=x.loc[d]
        if not np.isfinite(r.get(col,np.nan)) or not np.isfinite(r.get(f'FWD{h}',np.nan)): continue
        rows.append({'Ticker':t,'Date':d,'Score':float(r[col]),'Forward':float(r[f'FWD{h}']),
                     'VOL20':float(r.get('VOL20',np.nan)),'DOLLAR_VOL':float(r.get('DOLLAR_VOL',np.nan))})
    z=pd.DataFrame(rows)
    if len(z)<MIN_N:return z
    return z.replace([np.inf,-np.inf],np.nan).dropna(subset=['Score','Forward'])


def metric(z,direction):
    if len(z)<MIN_N:return None
    s=direction*z.Score
    q=pd.qcut(s.rank(method='first'),10,labels=False)+1
    means=z.assign(Q=q).groupby('Q',observed=True).Forward.mean()
    if len(means)!=10:return None
    return {'n':int(len(z)),'ic':float(spearmanr(s,z.Forward).statistic),
            'd10_d1':float(means.iloc[-1]-means.iloc[0]),
            'top10':float(means.iloc[-1]),'universe':float(z.Forward.mean()),
            'top10_minus_universe':float(means.iloc[-1]-z.Forward.mean()),
            'monotonic':float(np.corrcoef(np.arange(1,11),means.to_numpy())[0,1])}


def partial_ic(z,direction):
    z=z.dropna(subset=['Score','Forward','VOL20','DOLLAR_VOL']).copy()
    if len(z)<MIN_N:return np.nan
    # Rank-transform controls to avoid scale assumptions.
    y=z.Forward.to_numpy(float); s=(direction*z.Score.rank(pct=True)).to_numpy(float)
    X=np.column_stack([np.ones(len(z)),z.VOL20.rank(pct=True),z.DOLLAR_VOL.rank(pct=True)])
    b=np.linalg.lstsq(X,s,rcond=None)[0]; resid=s-X@b
    return float(spearmanr(resid,y).statistic)


def aggregate(records):
    if not records:return {}
    df=pd.DataFrame(records)
    return {'dates':int(len(df)),'mean_ic':float(df.ic.mean()),'median_ic':float(df.ic.median()),
            'mean_d10_d1':float(df.d10_d1.mean()),'mean_top10_minus_universe':float(df.top10_minus_universe.mean()),
            'hit_rate_d10_d1':float((df.d10_d1>0).mean()),'mean_partial_ic':float(df.partial_ic.mean()),
            'mean_monotonic':float(df.monotonic.mean()),'mean_n':float(df.n.mean())}


def block_bootstrap(vals,n=5000,seed=29,block=3):
    vals=np.asarray(vals,float); vals=vals[np.isfinite(vals)]
    if len(vals)<5:return {'n':int(len(vals))}
    rng=np.random.default_rng(seed); out=[]
    for _ in range(n):
        idx=[]
        while len(idx)<len(vals):
            s=rng.integers(0,len(vals)); idx.extend((s+np.arange(block))%len(vals))
        out.append(np.mean(vals[np.asarray(idx[:len(vals)])]))
    q=np.quantile(out,[.025,.5,.975])
    return {'n':int(len(vals)),'mean':float(vals.mean()),'ci95_low':float(q[0]),'ci95_high':float(q[2])}

prices=download_prices(UNIVERSE)
if 'QQQ' not in prices: raise RuntimeError('QQQ missing; cannot construct residual factor')
data=make_features(prices,prices['QQQ'])
# QQQ itself remains a benchmark/reference, not an investable cross-sectional candidate.
data.pop('QQQ',None)

all_results=[]; selected={}
for h in HORIZONS:
    dates=signal_dates(data,h)
    discovery=[d for d in dates if d<=DISCOVERY_END]
    validation=[d for d in dates if DISCOVERY_END<d<=VALIDATION_END]
    final=[d for d in dates if d>VALIDATION_END]
    disc_summary=[]
    for factor,(col,direction,desc) in FACTOR_META.items():
        rec=[]
        for d in discovery:
            z=panel(data,d,h,factor); m=metric(z,direction)
            if m:
                m.update(Date=str(d.date()),factor=factor,horizon=h,partial_ic=partial_ic(z,direction)); rec.append(m)
        a=aggregate(rec)
        if a: disc_summary.append((factor,a,rec,direction,desc))
    # Selection is ONLY from discovery. Prefer positive IC and spread, with stability penalty.
    disc_summary.sort(key=lambda x:(x[1]['mean_d10_d1'],x[1]['mean_ic'],x[1]['hit_rate_d10_d1']),reverse=True)
    winner=None
    for item in disc_summary:
        factor,a,rec,direction,desc=item
        if a['dates']>=6 and a['mean_d10_d1']>0 and a['mean_ic']>0 and a['hit_rate_d10_d1']>=0.5:
            winner=item; break
    if winner is None and disc_summary: winner=disc_summary[0]
    if winner is None: continue
    factor,a,rec,direction,desc=winner
    # Validation hard gate. We do not change factor after seeing validation.
    val=[]
    for d in validation:
        z=panel(data,d,h,factor); m=metric(z,direction)
        if m:
            m.update(Date=str(d.date()),factor=factor,horizon=h,partial_ic=partial_ic(z,direction)); val.append(m)
    va=aggregate(val)
    passes=bool(va and va['dates']>=8 and va['mean_d10_d1']>0 and va['mean_ic']>0 and va['hit_rate_d10_d1']>=0.5)
    selected[h]={'factor':factor,'direction':direction,'description':desc,'discovery':a,'validation':va,'passes_validation':passes}
    # Final OOS only gets a promotion-grade label if validation passed.
    fin=[]
    for d in final:
        z=panel(data,d,h,factor); m=metric(z,direction)
        if m:
            m.update(Date=str(d.date()),factor=factor,horizon=h,partial_ic=partial_ic(z,direction)); fin.append(m)
    fa=aggregate(fin)
    boot=block_bootstrap([r['d10_d1'] for r in fin]) if passes else {'n':len(fin),'status':'NOT_ELIGIBLE'}
    all_results.append({'horizon':h,'factor':factor,'direction':direction,'description':desc,'discovery':a,'validation':va,
                        'passes_validation':passes,'final_oos':fa,'final_bootstrap_d10_d1':boot,
                        'final_records':fin,'discovery_records':rec,'validation_records':val})

report={'run_id':RUN_ID,'universe_configured':len(UNIVERSE),'prices_loaded':len(prices),'data_series':len(data),
        'protocol':{'horizons':HORIZONS,'step':STEP,'min_cross_section':MIN_N,'discovery_end':str(DISCOVERY_END.date()),
                    'validation_end':str(VALIDATION_END.date()),'final_start':str((VALIDATION_END+pd.Timedelta(days=1)).date()),
                    'cost_bps_per_side':COST_BPS},'selected_by_horizon':selected,'results':all_results}
(OUT/'phase29_report.json').write_text(json.dumps(report,indent=2,default=str),encoding='utf-8')

rows=[]
for r in all_results:
    x={'Horizon':r['horizon'],'Factor':r['factor'],'Direction':r['direction'],'PassValidation':r['passes_validation']}
    for stage in ['discovery','validation','final_oos']:
        a=r.get(stage) or {}
        x[f'{stage}_dates']=a.get('dates'); x[f'{stage}_mean_ic']=a.get('mean_ic'); x[f'{stage}_mean_d10_d1']=a.get('mean_d10_d1'); x[f'{stage}_hit']=a.get('hit_rate_d10_d1'); x[f'{stage}_partial_ic']=a.get('mean_partial_ic')
    b=r.get('final_bootstrap_d10_d1',{}); x['final_boot_low']=b.get('ci95_low'); x['final_boot_high']=b.get('ci95_high')
    rows.append(x)
pd.DataFrame(rows).to_csv(OUT/'phase29_summary.csv',index=False)
print(json.dumps({'run_id':RUN_ID,'universe':len(UNIVERSE),'prices_loaded':len(prices),'data_series':len(data),'selected':selected,'results':[{k:v for k,v in r.items() if k not in ('final_records','discovery_records','validation_records')} for r in all_results]},indent=2,default=str))

"""Phase 31 — FINRA short-flow × short-interest divergence.

Pre-registered diagnostic hypothesis: daily Reg SHO short-sale flow may mean
something different when it coincides with a rise versus a fall in outstanding
short interest. The joint factors are tested without selecting the winning
direction on the OOS sample. F80/LTM remains frozen.

PIT rules:
- Flow is used only through signal-date close (close t -> open t+1).
- Short-interest settlement data uses KnowledgeDate = settlement + 7 business
  days, and a snapshot is usable only when KnowledgeDate < SignalDate.
- No OOS date is used to choose a factor, direction, threshold, or parameter.

Evaluation:
- OOS: 2024-01-02 through 2026-10-23.
- Signal cadence: every 20 business days, giving materially more dates than
  the 80-business-day rebalance cadence while keeping date-level observations
  separated.
- Fixed factor definitions only; no hyperparameter search.
- Reports raw Spearman, LTM-residual Spearman, top-decile minus bottom-decile
  spread, block bootstrap CI over signal dates, and leave-one-date-out (LOO).
- This phase is factor-level. Portfolio promotion requires a later identical
  exposure/cost economic test and is never automatic.
"""
from __future__ import annotations
import json, math, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import requests
import numpy as np
import pandas as pd
import yfinance as yf
from scipy.stats import spearmanr
from Nueva_Estrategia_Fase11_Real1000_LTM_v4 import DEFAULT_UNIVERSE

OUT=Path('nueva_estrategia_phase31_finra_flow_si_divergence'); OUT.mkdir(exist_ok=True)
CACHE=OUT/'flow_cache'; CACHE.mkdir(exist_ok=True)
FLOW_URL='https://cdn.finra.org/equity/regsho/daily/CNMSshvol{date}.txt'
SI_API='https://api.finra.org/data/group/otcmarket/name/consolidatedShortInterest'
START=pd.Timestamp('2022-06-01'); OOS_START=pd.Timestamp('2024-01-02'); END=pd.Timestamp('2026-10-23')
SIGNALS=pd.bdate_range(OOS_START, END, freq='20B')
FIELDS=['settlementDate','symbolCode','currentShortPositionQuantity','previousShortPositionQuantity','changePreviousNumber','changePercent','daysToCoverQuantity','revisionFlag','stockSplitFlag','marketClassCode','issueName']
UNIVERSE={str(x).upper() for x in DEFAULT_UNIVERSE}


def bday_knowledge(d): return (pd.Timestamp(d)+pd.offsets.BDay(7)).normalize()

def download_flow_day(d):
    ds=pd.Timestamp(d).strftime('%Y%m%d'); p=CACHE/f'{ds}.csv'
    if p.exists() and p.stat().st_size>20: return str(d.date()), 'cached', p
    last=''
    for k in range(4):
        try:
            r=requests.get(FLOW_URL.format(date=ds),timeout=45)
            if r.status_code==200 and r.content:
                raw=pd.read_csv(pd.io.common.BytesIO(r.content),sep='|',dtype={'Symbol':str},engine='python')
                raw.columns=[str(c).strip() for c in raw.columns]
                need={'Date','Symbol','ShortVolume','ShortExemptVolume','TotalVolume','Market'}
                if not need.issubset(raw.columns): raise RuntimeError(f'bad schema {raw.columns.tolist()}')
                raw=raw[raw.Symbol.astype(str).str.upper().isin(UNIVERSE)].copy()
                for c in ['ShortVolume','ShortExemptVolume','TotalVolume']: raw[c]=pd.to_numeric(raw[c],errors='coerce')
                raw['Date']=pd.to_datetime(raw['Date'],format='%Y%m%d',errors='coerce')
                raw=raw[raw.Date.notna() & (raw.TotalVolume>0)]
                raw.to_csv(p,index=False)
                return str(d.date()), 'downloaded', p
            if r.status_code in (403,404): return str(d.date()), f'http_{r.status_code}', None
            last=f'http_{r.status_code}'
        except Exception as e: last=repr(e)
        time.sleep(2**k)
    return str(d.date()), f'error_{last}', None


def load_flow():
    days=pd.bdate_range(START,END)
    audit=[]; paths=[]
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs=[ex.submit(download_flow_day,d) for d in days]
        for fut in as_completed(futs):
            ds,status,p=fut.result(); audit.append({'date':ds,'status':status});
            if p is not None: paths.append(p)
    pd.DataFrame(audit).sort_values('date').to_csv(OUT/'flow_download_audit.csv',index=False)
    frames=[]
    for p in sorted(paths):
        try: frames.append(pd.read_csv(p))
        except Exception: pass
    if not frames: raise RuntimeError('No FINRA short-flow files were loaded')
    x=pd.concat(frames,ignore_index=True)
    x['Ticker']=x.Symbol.astype(str).str.upper()
    x['Date']=pd.to_datetime(x.Date,errors='coerce').dt.normalize()
    x['ShortRatio']=x.ShortVolume/x.TotalVolume
    x['ShortExemptRatio']=x.ShortExemptVolume/x.TotalVolume
    x=x[['Date','Ticker','ShortRatio','ShortExemptRatio','TotalVolume']].dropna(subset=['Date','Ticker','ShortRatio'])
    x=x.sort_values(['Ticker','Date']).drop_duplicates(['Ticker','Date'],keep='last')
    return x


def load_si():
    rows=[]; audit=[]
    dates=[]
    for m in pd.period_range(START,END,freq='M'):
        d1=pd.Timestamp(m.start_time.year,m.start_time.month,15)
        while d1.weekday()>=5: d1-=pd.Timedelta(days=1)
        d2=pd.Timestamp(m.end_time).normalize()
        while d2.weekday()>=5: d2-=pd.Timedelta(days=1)
        dates += [d1,d2]
    for d in sorted(set(dates)):
        try:
            payload={'limit':10000,'offset':0,'fields':FIELDS,'compareFilters':[{'compareType':'equal','fieldName':'settlementDate','fieldValue':d.strftime('%Y-%m-%d')}]}
            batch=[]
            while True:
                r=requests.post(SI_API,json=payload,timeout=60,headers={'Accept':'application/json','Content-Type':'application/json'}); r.raise_for_status()
                obj=r.json(); data=obj.get('data',obj) if isinstance(obj,(dict,list)) else []
                if isinstance(data,dict): data=data.get('data',[])
                if not data: break
                batch.extend(data)
                if len(data)<payload['limit']: break
                payload['offset']+=len(data)
            hits=[z for z in batch if str(z.get('symbolCode','')).upper() in UNIVERSE]
            rows.extend(hits); audit.append({'settlementDate':str(d.date()),'rows':len(batch),'universeRows':len(hits),'status':'ok'})
        except Exception as e: audit.append({'settlementDate':str(d.date()),'rows':0,'universeRows':0,'status':'error','error':repr(e)})
    pd.DataFrame(audit).to_csv(OUT/'si_download_audit.csv',index=False)
    x=pd.DataFrame(rows)
    if x.empty: raise RuntimeError('No FINRA short-interest rows')
    x['Date']=pd.to_datetime(x.settlementDate,errors='coerce').dt.normalize(); x['KnowledgeDate']=x.Date.map(bday_knowledge); x['Ticker']=x.symbolCode.astype(str).str.upper()
    for c in ['currentShortPositionQuantity','previousShortPositionQuantity','changePreviousNumber','changePercent','daysToCoverQuantity']: x[c]=pd.to_numeric(x[c],errors='coerce')
    return x.sort_values(['Ticker','Date']).drop_duplicates(['Ticker','Date'],keep='last')


def add_flow_features(flow):
    flow=flow.copy().sort_values(['Ticker','Date']); g=flow.groupby('Ticker',group_keys=False)
    for col,base in [('FLOW_Z20','ShortRatio'),('FLOW_Z60','ShortRatio')]:
        w=20 if col.endswith('20') else 60
        mean=g[base].transform(lambda s:s.rolling(w,min_periods=max(10,w//2)).mean())
        std=g[base].transform(lambda s:s.rolling(w,min_periods=max(10,w//2)).std())
        flow[col]=(flow[base]-mean)/std.replace(0,np.nan)
    flow['FLOW_CHG']=g.ShortRatio.transform(lambda s:s.diff())
    flow['FLOW_PERSIST20']=g.ShortRatio.transform(lambda s:s.rolling(20,min_periods=10).apply(lambda z:np.mean(z>=np.quantile(z,.8)),raw=True))
    return flow


def add_si_features(si):
    si=si.copy().sort_values(['Ticker','Date']); g=si.groupby('Ticker',group_keys=False)
    si['SI_CHG_PCT']=si.changePercent
    si['SI_CHG_SHARES']=si.changePreviousNumber
    for col,src,w,mp in [('SI_CHG_Z6','changePreviousNumber',6,4),('SI_LEVEL_Z6','currentShortPositionQuantity',6,4),('SI_LEVEL_Z12','currentShortPositionQuantity',12,6)]:
        mean=g[src].transform(lambda s:s.rolling(w,min_periods=mp).mean()); std=g[src].transform(lambda s:s.rolling(w,min_periods=mp).std())
        si[col]=(si[src]-mean)/std.replace(0,np.nan)
    return si


def prices():
    px=yf.download(sorted(UNIVERSE),start='2021-01-01',end='2026-11-01',auto_adjust=False,progress=False,threads=True,group_by='column')
    close=px['Close'] if isinstance(px.columns,pd.MultiIndex) else px[['Close']]
    close.columns=[str(c).upper() for c in close.columns]
    return close.sort_index()


def ltm_at(close, sig):
    pos=close.index.searchsorted(sig,side='left');
    if pos<161: return pd.Series(dtype=float)
    c=close.iloc[:pos]
    out=pd.DataFrame(index=c.columns)
    for n in [100,120,140,160]: out[f'R{n}']=c.iloc[-1].div(c.iloc[-n-1])-1
    return out.rank(pct=True).mean(axis=1)


def snapshot(flow,si,close,sig):
    pos=close.index.searchsorted(sig,side='left')
    if pos>=len(close)-20: return pd.DataFrame()
    f=flow[flow.Date<=sig].groupby('Ticker',as_index=False).tail(1).set_index('Ticker')
    s=si[si.KnowledgeDate<sig].groupby('Ticker',as_index=False).tail(1).set_index('Ticker')
    names=sorted(set(f.index)&set(s.index)&set(close.columns))
    if not names: return pd.DataFrame()
    out=pd.DataFrame(index=names)
    for c in ['FLOW_Z20','FLOW_Z60','FLOW_CHG','FLOW_PERSIST20']: out[c]=f.reindex(names)[c]
    for c in ['SI_CHG_PCT','SI_CHG_SHARES','SI_CHG_Z6','SI_LEVEL_Z6','SI_LEVEL_Z12']: out[c]=s.reindex(names)[c]
    out['JOINT_RISE']=out.FLOW_Z20*out.SI_CHG_Z6
    out['JOINT_FALL']=out.FLOW_Z20*(-out.SI_CHG_Z6)
    out['LTM']=ltm_at(close,sig).reindex(names)
    base=close.iloc[pos];
    for h in [5,10,20]: out[f'FWD{h}']=close.iloc[pos+h].reindex(names).div(base.reindex(names))-1
    return out.replace([np.inf,-np.inf],np.nan)


def resid_rank(x,y):
    z=pd.concat([x,y],axis=1).dropna()
    if len(z)<30: return np.nan
    # cross-sectional linear residual from LTM rank; avoids crediting a factor
    # merely for re-identifying the existing momentum signal.
    a=z.iloc[:,0].rank(pct=True).to_numpy(); b=z.iloc[:,1].rank(pct=True).to_numpy()
    X=np.column_stack([np.ones(len(a)),b]); beta=np.linalg.lstsq(X,a,rcond=None)[0]; r=a-X@beta
    return r


def spearman(a,b):
    z=pd.concat([pd.Series(a),pd.Series(b)],axis=1).dropna()
    if len(z)<30 or z.iloc[:,0].nunique()<5 or z.iloc[:,1].nunique()<5: return np.nan
    return float(spearmanr(z.iloc[:,0],z.iloc[:,1]).statistic)


def date_spread(df,f,h):
    z=df[[f,f'FWD{h}']].dropna();
    if len(z)<30: return np.nan
    q=z[f].rank(pct=True); return float(z.loc[q>=.9,f'FWD{h}'].mean()-z.loc[q<=.1,f'FWD{h}'].mean())


def block_boot(vals,n=5000,block=3,seed=31031):
    a=np.asarray([v for v in vals if np.isfinite(v)],float)
    if len(a)<5:return (np.nan,np.nan,np.nan)
    rng=np.random.default_rng(seed); out=[]
    for _ in range(n):
        idx=[]
        while len(idx)<len(a):
            st=int(rng.integers(0,len(a))); idx.extend([(st+j)%len(a) for j in range(block)])
        out.append(a[idx[:len(a)]].mean())
    return float(a.mean()),float(np.quantile(out,.025)),float(np.quantile(out,.975))


def main():
    flow=add_flow_features(load_flow()); flow.to_csv(OUT/'flow_features.csv',index=False)
    si=add_si_features(load_si()); si.to_csv(OUT/'short_interest_features.csv',index=False)
    close=prices(); rows=[]
    for sig in SIGNALS:
        snap=snapshot(flow,si,close,pd.Timestamp(sig))
        if snap.empty: continue
        for f in ['JOINT_RISE','JOINT_FALL']:
            row={'SignalDate':str(pd.Timestamp(sig).date()),'Factor':f,'N':int(snap[f].notna().sum())}
            for h in [5,10,20]:
                row[f'IC{h}']=spearman(snap[f],snap[f'FWD{h}'])
                row[f'IC{h}_RESID_LTM']=spearman(pd.Series(resid_rank(snap[f],snap['LTM']),index=snap.index),snap[f'FWD{h}'])
                row[f'SPREAD{h}']=date_spread(snap,f,h)
            rows.append(row)
    res=pd.DataFrame(rows); res.to_csv(OUT/'phase31_signal_results.csv',index=False)
    summary=[]
    for f,g in res.groupby('Factor'):
        row={'Factor':f,'dates':len(g)}
        for h in [5,10,20]:
            for c in [f'IC{h}',f'IC{h}_RESID_LTM',f'SPREAD{h}']:
                vals=g[c].to_numpy(float); row[c+'_mean']=float(np.nanmean(vals)); row[c+'_median']=float(np.nanmedian(vals)); row[c+'_positive_dates']=int(np.nansum(vals>0))
                if c.startswith('SPREAD'): row[c+'_boot_mean'],row[c+'_boot_lo'],row[c+'_boot_hi']=block_boot(vals)
                if c.startswith('IC') and c.endswith('RESID_LTM'):
                    loo=[]
                    for i in range(len(vals)):
                        q=np.delete(vals,i); loo.append(np.nanmean(q))
                    row[c+'_loo_min']=float(np.nanmin(loo)); row[c+'_loo_max']=float(np.nanmax(loo)); row[c+'_loo_positive']=float(np.mean(np.asarray(loo)>0))
        summary.append(row)
    summary=pd.DataFrame(summary); summary.to_csv(OUT/'phase31_summary.csv',index=False)
    report={'phase':'31','hypothesis':'short-flow meaning differs conditional on short-interest change','oos_start':str(OOS_START.date()),'oos_end':str(END.date()),'signal_cadence':'20 business days','pit':'flow through close t; short interest KnowledgeDate < SignalDate','frozen_baseline':'F80_TOP20_PARTIAL50_BASELINE_C20','factors':['JOINT_RISE','JOINT_FALL'],'results':summary.to_dict(orient='records')}
    (OUT/'phase31_report.json').write_text(json.dumps(report,indent=2,default=str))
    print(json.dumps(report,indent=2,default=str))

if __name__=='__main__': main()

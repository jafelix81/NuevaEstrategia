"""Phase 25C — corrected FINRA Short Interest walk-forward + LTM incremental audit.
Diagnostic only. Fixes Phase 25B training-snapshot leakage bug: every signal uses all prior eligible snapshots, not only snapshots before the first OOS date.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np, pandas as pd, requests, yfinance as yf
from scipy.stats import spearmanr
from Nueva_Estrategia_Fase11_Real1000_LTM_v4 import DEFAULT_UNIVERSE
OUT=Path('nueva_estrategia_phase25c_finra_short_interest_corrected'); OUT.mkdir(exist_ok=True)
API='https://api.finra.org/data/group/otcmarket/name/consolidatedShortInterest'
START=pd.Timestamp('2022-06-01'); END=pd.Timestamp('2024-10-28')
TEST_DATES=pd.to_datetime(['2023-03-27','2023-07-21','2023-11-13','2024-03-11','2024-07-05','2024-10-28'])
FEATURES=['SI_DTC','SI_CHG_PCT','SI_CHG_SHARES','SI_LEVEL_Z6','SI_LEVEL_Z12','SI_CHG_Z6','SI_PERSIST_HIGH6','SI_ACCEL']
FIELDS=['settlementDate','symbolCode','currentShortPositionQuantity','previousShortPositionQuantity','changePreviousNumber','changePercent','daysToCoverQuantity','revisionFlag','stockSplitFlag','marketClassCode','issueName']
def knowledge_date(d): return (pd.Timestamp(d)+pd.offsets.BDay(7)).normalize()
def parse_payload(text):
    text=text.lstrip('\ufeff').strip()
    if not text: return []
    try:
        v=json.loads(text); return v.get('data',[]) if isinstance(v,dict) else v
    except Exception: pass
    dec=json.JSONDecoder(); vals=[]; pos=0
    while pos<len(text):
        while pos<len(text) and text[pos].isspace(): pos+=1
        if pos>=len(text): break
        try:v,end=dec.raw_decode(text,pos); vals.append(v); pos=end
        except Exception: break
    rows=[]
    for v in vals: rows.extend(v if isinstance(v,list) else [v] if isinstance(v,dict) else [])
    if rows:return rows
    for line in text.splitlines():
        try: rows.append(json.loads(line))
        except Exception: return []
    return rows
def settlement_dates():
    out=[]
    for m in pd.period_range(START,END,freq='M'):
        a=pd.Timestamp(m.start_time.year,m.start_time.month,15)
        while a.weekday()>=5:a-=pd.Timedelta(days=1)
        b=pd.Timestamp(m.end_time).normalize()
        while b.weekday()>=5:b-=pd.Timedelta(days=1)
        out += [a,b]
    return sorted(set(d.normalize() for d in out if START<=d<=END))
def download_si():
    universe=set(DEFAULT_UNIVERSE); rows=[]; audit=[]
    for d in settlement_dates():
        payload={'limit':10000,'offset':0,'fields':FIELDS,'compareFilters':[{'compareType':'equal','fieldName':'settlementDate','fieldValue':d.strftime('%Y-%m-%d')}]}
        try:
            r=requests.post(API,json=payload,timeout=60,headers={'Accept':'application/json','Content-Type':'application/json'}); r.raise_for_status(); batch=parse_payload(r.text)
            hits=[x for x in batch if str(x.get('symbolCode','')).upper() in universe]; rows.extend(hits); audit.append({'settlementDate':str(d.date()),'rows':len(batch),'universeRows':len(hits),'status':'ok' if batch else 'empty'})
        except Exception as e:audit.append({'settlementDate':str(d.date()),'rows':0,'universeRows':0,'status':'error','error':repr(e)})
    pd.DataFrame(audit).to_csv(OUT/'download_audit.csv',index=False)
    raw=pd.DataFrame(rows)
    if raw.empty: raise RuntimeError('No FINRA short-interest rows retrieved')
    raw['Date']=pd.to_datetime(raw.settlementDate,errors='coerce'); raw['KnowledgeDate']=raw.Date.map(knowledge_date); raw['Ticker']=raw.symbolCode.astype(str).str.upper()
    for c in ['currentShortPositionQuantity','previousShortPositionQuantity','changePreviousNumber','changePercent','daysToCoverQuantity']:raw[c]=pd.to_numeric(raw[c],errors='coerce')
    raw=raw.sort_values(['Ticker','Date']).drop_duplicates(['Ticker','Date'],keep='last'); raw.to_csv(OUT/'short_interest_raw.csv',index=False); return raw
def add_features(r):
    r=r.copy(); g=r.groupby('Ticker',group_keys=False); r['SI_DTC']=r.daysToCoverQuantity; r['SI_CHG_PCT']=r.changePercent; r['SI_CHG_SHARES']=r.changePreviousNumber
    r['SI_LEVEL_Z6']=g.currentShortPositionQuantity.transform(lambda s:(s-s.rolling(6,min_periods=4).mean())/s.rolling(6,min_periods=4).std())
    r['SI_LEVEL_Z12']=g.currentShortPositionQuantity.transform(lambda s:(s-s.rolling(12,min_periods=6).mean())/s.rolling(12,min_periods=6).std())
    r['SI_CHG_Z6']=g.changePreviousNumber.transform(lambda s:(s-s.rolling(6,min_periods=4).mean())/s.rolling(6,min_periods=4).std())
    r['SI_PERSIST_HIGH6']=g.currentShortPositionQuantity.transform(lambda s:s.rolling(6,min_periods=4).apply(lambda x:np.mean(x>np.median(x)),raw=True))
    r['SI_ACCEL']=g.changePreviousNumber.transform(lambda s:s.diff())
    return r
def prices():
    px=yf.download(list(DEFAULT_UNIVERSE),start='2021-01-01',end='2025-03-01',auto_adjust=False,progress=False,threads=True,group_by='column'); return (px['Close'] if isinstance(px.columns,pd.MultiIndex) else px[['Close']]).sort_index()
def sp(a,b):
    x=pd.concat([a,b],axis=1).dropna(); return spearmanr(x.iloc[:,0],x.iloc[:,1]).statistic if len(x)>=30 else np.nan
def ltm_score(close,dt):
    p=close.loc[:dt].iloc[-1]; vals={}
    for t in close.columns:
        s=close[t].dropna();
        if len(s)==0:continue
        idx=s.index.searchsorted(dt,side='right')-1
        if idx<160:continue
        vals[t]=np.mean([(s.iloc[idx]/s.iloc[idx-n]-1) for n in [100,120,140,160]])
    return pd.Series(vals)
def main():
    raw=add_features(download_si()); close=prices(); rows=[]; factor_audit=[]
    # Build ALL point-in-time snapshots. This is the critical correction to Phase 25B.
    snaps=[]
    for kd,g in raw.groupby('KnowledgeDate'):
        kd=pd.Timestamp(kd); pos=close.index.searchsorted(kd,side='left')
        if pos>=len(close)-20:continue
        f=g.groupby('Ticker',as_index=False).tail(1).copy(); base=close.iloc[pos]
        for h in [5,10,20]:f[f'FWD{h}']=f.Ticker.map(close.iloc[pos+h].div(base).sub(1))
        snaps.append(f)
    snap=pd.concat(snaps,ignore_index=True)
    for sig in TEST_DATES:
        train=snap[snap.KnowledgeDate<sig]; scores=[]
        for feat in FEATURES:
            cs=[sp(g[feat],g.FWD5) for _,g in train.groupby('KnowledgeDate')]; cs=[x for x in cs if np.isfinite(x)]
            if len(cs)>=4:scores.append((feat,float(np.mean(cs)),len(cs)))
        if not scores:continue
        feat,score,n=max(scores,key=lambda x:abs(x[1])); direction=1 if score>=0 else -1; factor_audit += [{'SignalDate':str(sig.date()),'Feature':a,'TrainMeanSpearman5':b,'TrainSnapshots':c} for a,b,c in scores]
        pos=close.index.searchsorted(sig,side='left'); base=close.iloc[pos]; oos=raw[raw.KnowledgeDate<sig].groupby('Ticker',as_index=False).tail(1).copy(); oos=oos[oos.Ticker.isin(close.columns)].copy()
        for h in [5,10,20]:oos[f'ret{h}']=oos.Ticker.map(close.iloc[pos+h].div(base).sub(1))
        oos=oos.dropna(subset=[feat,'ret5']); oos['rank']=direction*(oos[feat].rank(pct=True)-.5); med=oos['rank'].median(); lo=oos[oos['rank']>=med]; sh=oos[oos['rank']<med]
        ltm=ltm_score(close,sig); oos['LTM']=oos.Ticker.map(ltm); z=oos.dropna(subset=['LTM',feat]).copy()
        if len(z)>=30:
            X=np.c_[np.ones(len(z)),z.LTM.to_numpy()]; beta=np.linalg.lstsq(X,z[feat].to_numpy(),rcond=None)[0]; z['RESID']=z[feat]-(X@beta); resid5=sp(z.RESID,z.ret5); resid10=sp(z.RESID,z.ret10); resid20=sp(z.RESID,z.ret20)
        else: resid5=resid10=resid20=np.nan
        row={'SignalDate':str(sig.date()),'SelectedFeature':feat,'Direction':direction,'TrainMeanSpearman5':score,'TrainSnapshots':n,'N':len(oos),'OOS_LS_5':direction*(lo.ret5.mean()-sh.ret5.mean()),'OOS_LS_10':direction*(lo.ret10.mean()-sh.ret10.mean()),'OOS_LS_20':direction*(lo.ret20.mean()-sh.ret20.mean()),'ResidualSpearman5':resid5,'ResidualSpearman10':resid10,'ResidualSpearman20':resid20,'LTM_Corr':sp(oos[feat],oos.LTM)}; rows.append(row)
    res=pd.DataFrame(rows); res.to_csv(OUT/'corrected_walkforward_results.csv',index=False); pd.DataFrame(factor_audit).to_csv(OUT/'factor_selection_audit.csv',index=False)
    summary={str(h):{'n':int(res[f'OOS_LS_{h}'].notna().sum()),'mean':float(res[f'OOS_LS_{h}'].mean()),'median':float(res[f'OOS_LS_{h}'].median()),'positive':int((res[f'OOS_LS_{h}']>0).sum())} for h in [5,10,20]}; audit={'phase':'25C','status':'COMPLETE_CORRECTED_INCREMENTAL','critical_fix':'Training snapshots are now all eligible KnowledgeDate < SignalDate; Phase 25B incorrectly limited snapshots to dates before the first OOS signal.','summary':summary,'production_change':False}; (OUT/'audit.json').write_text(json.dumps(audit,indent=2)); print(json.dumps(audit,indent=2)); print(res.to_string(index=False))
if __name__=='__main__':main()

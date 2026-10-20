"""Phase 25C — FINRA Short Interest walk-forward.
Uses the official FINRA short-interest API with a conservative point-in-time knowledge date.
Diagnostic only; F80 remains frozen.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np, pandas as pd, requests, yfinance as yf
from scipy.stats import spearmanr
from Nueva_Estrategia_Fase11_Real1000_LTM_v4 import DEFAULT_UNIVERSE

OUT=Path('nueva_estrategia_phase25c_finra_short_interest_walkforward'); OUT.mkdir(exist_ok=True)
API='https://api.finra.org/data/group/otcmarket/name/consolidatedShortInterest'
START=pd.Timestamp('2022-06-01'); END=pd.Timestamp('2024-10-28')
FEATURES=['SI_DTC','SI_CHG_PCT','SI_CHG_SHARES','SI_LEVEL_Z6','SI_LEVEL_Z12','SI_CHG_Z6','SI_PERSIST_HIGH6','SI_ACCEL']
FIELDS=['settlementDate','symbolCode','currentShortPositionQuantity','previousShortPositionQuantity','changePreviousNumber','changePercent','daysToCoverQuantity','revisionFlag','stockSplitFlag','marketClassCode','issueName']

def knowledge_date(d): return (pd.Timestamp(d)+pd.offsets.BDay(7)).normalize()

def parse_payload(text):
    text=text.lstrip('\ufeff').strip()
    try: return json.loads(text)
    except json.JSONDecodeError: pass
    dec=json.JSONDecoder(); vals=[]; pos=0
    while pos<len(text):
        while pos<len(text) and text[pos].isspace(): pos+=1
        if pos>=len(text): break
        try: v,end=dec.raw_decode(text,pos); vals.append(v); pos=end
        except json.JSONDecodeError: break
    rows=[]
    for v in vals: rows.extend(v if isinstance(v,list) else [v] if isinstance(v,dict) else [])
    if rows: return rows
    raise ValueError('FINRA response is not parseable JSON')

def api_rows(d):
    payload={'limit':10000,'offset':0,'fields':FIELDS,'compareFilters':[{'compareType':'equal','fieldName':'settlementDate','fieldValue':pd.Timestamp(d).strftime('%Y-%m-%d')}]}
    rows=[]
    while True:
        r=requests.post(API,json=payload,timeout=60,headers={'Accept':'application/json','Content-Type':'application/json'}); r.raise_for_status(); batch=parse_payload(r.text)
        if isinstance(batch,dict): batch=batch.get('data',[])
        if not batch: break
        rows.extend(batch)
        if len(batch)<payload['limit']: break
        payload['offset']+=len(batch)
        if payload['offset']>200000: raise RuntimeError('unexpectedly large settlement response')
    return rows

def settlement_dates():
    out=[]
    for m in pd.period_range(START,END,freq='M'):
        d1=pd.Timestamp(m.start_time.year,m.start_time.month,15)
        while d1.weekday()>=5: d1-=pd.Timedelta(days=1)
        d2=pd.Timestamp(m.end_time).normalize()
        while d2.weekday()>=5: d2-=pd.Timedelta(days=1)
        out.extend([d1,d2])
    return sorted(set(d.normalize() for d in out if START<=d<=END))

def load_si():
    universe=set(DEFAULT_UNIVERSE); rows=[]; audit=[]
    for i,d in enumerate(settlement_dates(),1):
        try:
            batch=api_rows(d); hits=[x for x in batch if str(x.get('symbolCode','')).upper() in universe]; rows.extend(hits); audit.append({'settlementDate':str(d.date()),'rows':len(batch),'universeRows':len(hits),'status':'ok'})
        except Exception as e: audit.append({'settlementDate':str(d.date()),'rows':0,'universeRows':0,'status':'error','error':repr(e)})
    pd.DataFrame(audit).to_csv(OUT/'phase25c_download_audit.csv',index=False)
    raw=pd.DataFrame(rows)
    if raw.empty: raise RuntimeError('No short-interest rows')
    raw['Date']=pd.to_datetime(raw.settlementDate,errors='coerce'); raw['KnowledgeDate']=raw.Date.map(knowledge_date); raw['Ticker']=raw.symbolCode.astype(str).str.upper()
    for c in ['currentShortPositionQuantity','previousShortPositionQuantity','changePreviousNumber','changePercent','daysToCoverQuantity']: raw[c]=pd.to_numeric(raw[c],errors='coerce')
    raw=raw.sort_values(['Ticker','Date']).drop_duplicates(['Ticker','Date'],keep='last')
    return raw

def features(raw):
    raw=raw.copy(); g=raw.groupby('Ticker',group_keys=False)
    raw['SI_DTC']=raw.daysToCoverQuantity; raw['SI_CHG_PCT']=raw.changePercent; raw['SI_CHG_SHARES']=raw.changePreviousNumber
    raw['SI_LEVEL_Z6']=g.currentShortPositionQuantity.transform(lambda s:(s-s.rolling(6,min_periods=4).mean())/s.rolling(6,min_periods=4).std())
    raw['SI_LEVEL_Z12']=g.currentShortPositionQuantity.transform(lambda s:(s-s.rolling(12,min_periods=6).mean())/s.rolling(12,min_periods=6).std())
    raw['SI_CHG_Z6']=g.changePreviousNumber.transform(lambda s:(s-s.rolling(6,min_periods=4).mean())/s.rolling(6,min_periods=4).std())
    raw['SI_PERSIST_HIGH6']=g.currentShortPositionQuantity.transform(lambda s:s.rolling(6,min_periods=4).apply(lambda x:np.mean(x>np.median(x)),raw=True))
    raw['SI_ACCEL']=g.changePreviousNumber.transform(lambda s:s.diff())
    return raw

def prices():
    px=yf.download(list(DEFAULT_UNIVERSE),start='2021-01-01',end='2025-03-01',auto_adjust=False,progress=False,threads=True,group_by='column'); return (px['Close'] if isinstance(px.columns,pd.MultiIndex) else px[['Close']]).sort_index()

def corr(a,b):
    x=pd.concat([a,b],axis=1).dropna()
    if len(x)<30 or x.iloc[:,0].nunique()<3 or x.iloc[:,1].nunique()<3: return np.nan
    return float(spearmanr(x.iloc[:,0],x.iloc[:,1]).statistic)

def main():
    raw=features(load_si()); raw.to_csv(OUT/'phase25c_short_interest_features.csv',index=False); close=prices()
    # 80-business-day pseudo-OOS cadence, matching the frozen F80 rebalance cadence as closely as possible.
    candidates=pd.bdate_range('2022-08-05','2024-10-28',freq='80B')
    dates=[pd.Timestamp(x) for x in candidates if x<=END]
    snaps=[]
    for kd in sorted(raw.KnowledgeDate.dropna().unique()):
        kd=pd.Timestamp(kd); pos=close.index.searchsorted(kd,side='left')
        if pos>=len(close)-20: continue
        fr=raw[raw.KnowledgeDate==kd].groupby('Ticker',as_index=False).tail(1).copy(); base=close.iloc[pos]
        for h in (5,10,20): fr[f'FWD{h}']=fr.Ticker.map(close.iloc[pos+h].div(base).sub(1))
        snaps.append(fr)
    snap=pd.concat(snaps,ignore_index=True)
    results=[]; selections=[]
    for sig in dates:
        train=snap[snap.KnowledgeDate<sig]; scores=[]
        for f in FEATURES:
            cs=[corr(g[f],g.FWD5) for _,g in train.groupby('KnowledgeDate')]; cs=[x for x in cs if np.isfinite(x)]
            if len(cs)>=3: scores.append((f,float(np.mean(cs)),len(cs)))
        if not scores: continue
        f,sc,n=max(scores,key=lambda x:abs(x[1])); direction=1 if sc>=0 else -1
        pos=close.index.searchsorted(sig,side='left')
        if pos>=len(close)-20: continue
        oos=raw[raw.KnowledgeDate<sig].groupby('Ticker',as_index=False).tail(1).copy(); oos=oos[oos.Ticker.isin(close.columns)].copy(); base=close.iloc[pos]
        for h in (5,10,20): oos[f'R{h}']=oos.Ticker.map(close.iloc[pos+h].div(base).sub(1))
        oos=oos.dropna(subset=[f,'R5'])
        if len(oos)<40: continue
        oos['score']=direction*(oos[f].rank(pct=True)-0.5); med=oos.score.median(); long=oos[oos.score>=med]; short=oos[oos.score<med]
        row={'SignalDate':str(sig.date()),'Feature':f,'Direction':direction,'TrainMeanSpearman5':sc,'TrainSnapshots':n,'N':len(oos)}
        for h in (5,10,20): row[f'LS{h}']=float(direction*(long[f'R{h}'].mean()-short[f'R{h}'].mean()))
        results.append(row)
        selections.extend({'SignalDate':str(sig.date()),'Feature':a,'TrainMeanSpearman5':b,'TrainSnapshots':c} for a,b,c in scores)
    res=pd.DataFrame(results); res.to_csv(OUT/'phase25c_walkforward_results.csv',index=False); pd.DataFrame(selections).to_csv(OUT/'phase25c_factor_selection_audit.csv',index=False)
    summary={str(h):{'n':int(res[f'LS{h}'].notna().sum()),'mean':float(res[f'LS{h}'].mean()) if len(res) else None,'median':float(res[f'LS{h}'].median()) if len(res) else None,'positive':int((res[f'LS{h}']>0).sum())} for h in (5,10,20)}
    audit={'phase':'25C','status':'COMPLETE_DIAGNOSTIC','cadence':'80 business days','knowledge_policy':'KnowledgeDate = settlementDate + 7 US business days; test requires KnowledgeDate < SignalDate','dates':[str(x.date()) for x in dates],'features':FEATURES,'summary':summary,'production_change':False}
    (OUT/'phase25c_audit.json').write_text(json.dumps(audit,indent=2)); print(json.dumps(audit,indent=2))
if __name__=='__main__': main()

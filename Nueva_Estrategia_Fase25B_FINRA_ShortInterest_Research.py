"""Phase 25B — FINRA Short Interest predictive research.
Diagnostic only. Strict point-in-time knowledge policy; no production change.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np,pandas as pd,requests,yfinance as yf
from scipy.stats import spearmanr
from Nueva_Estrategia_Fase11_Real1000_LTM_v4 import DEFAULT_UNIVERSE
OUT=Path('nueva_estrategia_phase25b_finra_short_interest_research'); OUT.mkdir(exist_ok=True)
API='https://api.finra.org/data/group/otcmarket/name/consolidatedShortInterest'; START=pd.Timestamp('2022-06-01'); END=pd.Timestamp('2024-10-28')
TEST_DATES=pd.to_datetime(['2023-03-27','2023-07-21','2023-11-13','2024-03-11','2024-07-05','2024-10-28'])
FEATURES=['SI_DTC','SI_CHG_PCT','SI_CHG_SHARES','SI_LEVEL_Z6','SI_LEVEL_Z12','SI_CHG_Z6','SI_PERSIST_HIGH6','SI_ACCEL']
FIELDS=['settlementDate','symbolCode','currentShortPositionQuantity','previousShortPositionQuantity','changePreviousNumber','changePercent','daysToCoverQuantity','revisionFlag','stockSplitFlag','marketClassCode','issueName']
def knowledge_date(d): return (pd.Timestamp(d)+pd.offsets.BDay(7)).normalize()
def parse_finra_payload(text):
    text=text.lstrip('\ufeff').strip()
    try:return json.loads(text)
    except json.JSONDecodeError:pass
    dec=json.JSONDecoder(); vals=[]; pos=0
    while pos<len(text):
        while pos<len(text) and text[pos].isspace():pos+=1
        if pos>=len(text):break
        try:v,end=dec.raw_decode(text,pos); vals.append(v); pos=end
        except json.JSONDecodeError:break
    if vals:
        rows=[]
        for v in vals: rows.extend(v if isinstance(v,list) else [v] if isinstance(v,dict) else [])
        if rows:return rows
    rows=[]
    for line in text.splitlines():
        line=line.strip()
        if not line:continue
        try: rows.append(json.loads(line))
        except Exception: rows=[]; break
    if rows:return rows
    raise ValueError(f'FINRA response is not valid JSON; prefix={text[:160]!r}')
def api_rows_for_settlement(d):
    payload={'limit':10000,'offset':0,'fields':FIELDS,'compareFilters':[{'compareType':'equal','fieldName':'settlementDate','fieldValue':pd.Timestamp(d).strftime('%Y-%m-%d')}]}; rows=[]
    while True:
        r=requests.post(API,json=payload,timeout=60,headers={'Accept':'application/json','Content-Type':'application/json'}); r.raise_for_status(); batch=parse_finra_payload(r.text)
        if isinstance(batch,dict):batch=batch.get('data',[])
        if not batch:break
        rows.extend(batch)
        if len(batch)<payload['limit']:break
        payload['offset']+=len(batch)
        if payload['offset']>200000:raise RuntimeError('unexpectedly large FINRA settlement response')
    return rows
def get_settlement_dates():
    dates=[]
    for m in pd.period_range(START,END,freq='M'):
        d1=pd.Timestamp(m.start_time.year,m.start_time.month,15)
        while d1.weekday()>=5:d1-=pd.Timedelta(days=1)
        d2=pd.Timestamp(m.end_time).normalize()
        while d2.weekday()>=5:d2-=pd.Timedelta(days=1)
        dates.extend([d1,d2])
    return sorted({d.normalize() for d in dates if START<=d<=END})
def download_short_interest():
    universe=set(DEFAULT_UNIVERSE); all_rows=[]; probes=[]; dates=get_settlement_dates()
    for i,d in enumerate(dates,1):
        try:
            rows=api_rows_for_settlement(d); hits=[x for x in rows if str(x.get('symbolCode','')).upper() in universe]; all_rows.extend(hits); probes.append({'settlementDate':str(d.date()),'rows':len(rows),'universeRows':len(hits),'status':'ok'}); print(f'FINRA SI {i}/{len(dates)}: {d.date()} universe_rows={len(hits)}',flush=True)
        except Exception as e: probes.append({'settlementDate':str(d.date()),'rows':0,'universeRows':0,'status':'error','error':repr(e)}); print(f'FINRA SI ERROR {d.date()}: {e}',flush=True)
    pd.DataFrame(probes).to_csv(OUT/'phase25b_download_audit.csv',index=False); raw=pd.DataFrame(all_rows)
    if raw.empty:raise RuntimeError('No FINRA short-interest rows retrieved')
    raw['Date']=pd.to_datetime(raw['settlementDate'],errors='coerce'); raw['KnowledgeDate']=raw['Date'].map(knowledge_date); raw['Ticker']=raw['symbolCode'].astype(str).str.upper()
    for c in ['currentShortPositionQuantity','previousShortPositionQuantity','changePreviousNumber','changePercent','daysToCoverQuantity']:raw[c]=pd.to_numeric(raw[c],errors='coerce')
    raw=raw.sort_values(['Ticker','Date']).drop_duplicates(['Ticker','Date'],keep='last'); raw.to_csv(OUT/'phase25b_short_interest_raw.csv',index=False); return raw
def add_features(raw):
    g=raw.groupby('Ticker',group_keys=False); raw=raw.copy(); raw['SI_DTC']=raw['daysToCoverQuantity']; raw['SI_CHG_PCT']=raw['changePercent']; raw['SI_CHG_SHARES']=raw['changePreviousNumber']
    raw['SI_LEVEL_Z6']=g['currentShortPositionQuantity'].transform(lambda s:(s-s.rolling(6,min_periods=4).mean())/s.rolling(6,min_periods=4).std()); raw['SI_LEVEL_Z12']=g['currentShortPositionQuantity'].transform(lambda s:(s-s.rolling(12,min_periods=6).mean())/s.rolling(12,min_periods=6).std()); raw['SI_CHG_Z6']=g['changePreviousNumber'].transform(lambda s:(s-s.rolling(6,min_periods=4).mean())/s.rolling(6,min_periods=4).std()); raw['SI_PERSIST_HIGH6']=g['currentShortPositionQuantity'].transform(lambda s:s.rolling(6,min_periods=4).apply(lambda x:np.mean(x>np.median(x)),raw=True)); raw['SI_ACCEL']=g['changePreviousNumber'].transform(lambda s:s.diff()); return raw
def download_prices():
    px=yf.download(list(DEFAULT_UNIVERSE),start='2021-01-01',end='2025-03-01',auto_adjust=False,progress=False,threads=True,group_by='column'); close=px['Close'] if isinstance(px.columns,pd.MultiIndex) else px[['Close']]; return close.sort_index()
def corr(a,b):
    x=pd.concat([a,b],axis=1).dropna(); return spearmanr(x.iloc[:,0],x.iloc[:,1]).statistic if len(x)>=30 else np.nan
def main():
    raw=add_features(download_short_interest()); raw.to_csv(OUT/'phase25b_short_interest_features.csv',index=False); close=download_prices(); snapshots=[]
    for kd in sorted(raw['KnowledgeDate'].dropna().unique()):
        kd=pd.Timestamp(kd)
        if kd>=TEST_DATES.min():continue
        pos=close.index.searchsorted(kd,side='left')
        if pos>=len(close)-20:continue
        frame=raw[raw['KnowledgeDate']==kd].groupby('Ticker',as_index=False).tail(1).copy(); base=close.iloc[pos]
        for h in [5,10,20]:frame[f'FWD{h}']=frame['Ticker'].map(close.iloc[pos+h].div(base).sub(1))
        snapshots.append(frame)
    snap=pd.concat(snapshots,ignore_index=True) if snapshots else pd.DataFrame(); results=[]; factor_audit=[]
    for sig in TEST_DATES:
        train=snap[snap['KnowledgeDate']<sig]; scores=[]
        for f in FEATURES:
            cs=[corr(g[f],g['FWD5']) for _,g in train.groupby('KnowledgeDate')]; cs=[x for x in cs if np.isfinite(x)]
            if len(cs)>=2:scores.append((f,float(np.mean(cs)),len(cs)))
        if not scores:continue
        f,sc,n=max(scores,key=lambda x:abs(x[1])); direction=1 if sc>=0 else -1; pos=close.index.searchsorted(sig,side='left'); base=close.iloc[pos]; oos=raw[raw['KnowledgeDate']<sig].groupby('Ticker',as_index=False).tail(1).copy(); oos=oos[oos['Ticker'].isin(close.columns)].copy()
        for h in [5,10,20]:oos[f'ret{h}']=oos['Ticker'].map(close.iloc[min(pos+h,len(close)-1)].div(base).sub(1))
        oos=oos.dropna(subset=[f,'ret5']); oos['score']=direction*(oos[f].rank(pct=True)-0.5); med=oos['score'].median(); long=oos[oos['score']>=med]; short=oos[oos['score']<med]; row={'SignalDate':str(sig.date()),'SelectedFeature':f,'Direction':direction,'TrainMeanSpearman5':sc,'TrainSnapshots':n,'N':len(oos),'LongN':len(long),'ShortN':len(short)}
        for h in [5,10,20]:row[f'OOS_LS_{h}']=float(direction*(long[f'ret{h}'].mean()-short[f'ret{h}'].mean())) if len(short) else np.nan
        results.append(row); factor_audit.extend([{'SignalDate':str(sig.date()),'Feature':a,'TrainMeanSpearman5':b,'TrainSnapshots':c} for a,b,c in scores])
    res=pd.DataFrame(results); pd.DataFrame(factor_audit).to_csv(OUT/'phase25b_factor_selection_audit.csv',index=False); res.to_csv(OUT/'phase25b_walkforward_results.csv',index=False); summary={str(h):{'n':int(res[f'OOS_LS_{h}'].notna().sum()),'mean':float(res[f'OOS_LS_{h}'].mean()) if len(res) else None,'median':float(res[f'OOS_LS_{h}'].median()) if len(res) else None,'positive':int((res[f'OOS_LS_{h}']>0).sum())} for h in [5,10,20]}; audit={'phase':'25B','status':'COMPLETE_DIAGNOSTIC','knowledge_policy':'KnowledgeDate = settlementDate + 7 US business days; test requires KnowledgeDate < SignalDate','settlement_schedule':'15th and final business day','test_dates':[str(x.date()) for x in TEST_DATES],'features':FEATURES,'summary':summary,'production_change':False}; (OUT/'phase25b_audit.json').write_text(json.dumps(audit,indent=2)); print(json.dumps(audit,indent=2))
if __name__=='__main__':main()

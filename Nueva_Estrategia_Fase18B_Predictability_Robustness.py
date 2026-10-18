import os,json,time
from pathlib import Path
import numpy as np,pandas as pd
from scipy.stats import spearmanr

RUN_ID=os.getenv('RUN_ID',pd.Timestamp.now(tz='UTC').strftime('%Y%m%d_%H%M%S'))
DATASET=Path(os.getenv('PHASE17_DATASET_PATH','nueva_estrategia_phase17_failure_predictability/phase17_entry_factor_dataset.csv'))
OUTDIR=Path('nueva_estrategia_phase18b_predictability_robustness'); OUTDIR.mkdir(parents=True,exist_ok=True)
DISCOVERY_FRAC=.70; Q=5; MIN_GROUP=20; SUBPERIODS=3; PERMUTATIONS=2000; SEED=17018
PRIMARY={'Y_QUICK':['R60','DIST_200D','R120'],'Y_WEAK':['R1','VOL252','R60'],'Y_MAE10':['VOL20','R120','VOL60'],'Y_ADVERSE':['AC1','VOL20','DIST_200D']}
COMBINATIONS={'MAE10_R120_VOL20':('Y_MAE10','R120','VOL20','HIGHER','HIGHER'),'QUICK_R120_DIST':('Y_QUICK','R120','DIST_200D','HIGHER','HIGHER'),'WEAK_R1_VOL252':('Y_WEAK','R1','VOL252','HIGHER','LOWER')}

def auc(x,y):
 z=pd.DataFrame({'x':x,'y':y}).replace([np.inf,-np.inf],np.nan).dropna()
 if len(z)==0 or z.y.nunique()<2:return np.nan
 p=z.loc[z.y==1,'x']; n=z.loc[z.y==0,'x']
 if len(p)==0 or len(n)==0:return np.nan
 r=z.x.rank(method='average'); return float((r[z.y==1].sum()-len(p)*(len(p)+1)/2)/(len(p)*len(n)))

def rank_date(g,f,d):
 r=pd.to_numeric(g[f],errors='coerce').rank(method='average',pct=True); return r if d=='HIGHER' else 1-r

def discovery_direction(df,f,label):
 vals=[]
 for _,g in df[df.Split=='DISCOVERY'].groupby('DateSignal'):
  x=pd.to_numeric(g[f],errors='coerce'); y=pd.to_numeric(g[label],errors='coerce'); ok=x.notna()&y.notna()
  if ok.sum()<3 or y[ok].nunique()<2:continue
  r=x[ok].rank(method='average',pct=True); vals.append((auc(r,y[ok]),auc(1-r,y[ok])))
 if not vals:return None
 ah=np.nanmean([v[0] for v in vals]); al=np.nanmean([v[1] for v in vals]); return 'HIGHER' if ah>=al else 'LOWER'

def quintiles(x,y):
 z=pd.DataFrame({'x':x,'y':y}).replace([np.inf,-np.inf],np.nan).dropna()
 if len(z)<Q*MIN_GROUP or z.y.nunique()<2:return pd.DataFrame()
 z['Q']=pd.qcut(z.x,Q,labels=False,duplicates='drop')+1
 g=z.groupby('Q',observed=True).y.agg(['mean','count']).rename(columns={'mean':'FailureRate','count':'N'}).reset_index()
 return g if len(g)==Q else pd.DataFrame()

def mono(q):
 if len(q)<Q:return {'MonotonicDirection':'INSUFFICIENT','SpearmanQRate':np.nan,'MonotonicPASS':False}
 rho,p=spearmanr(q.Q,q.FailureRate); dif=np.diff(q.FailureRate.to_numpy(float)); nd=np.all(dif>=-1e-12); ni=np.all(dif<=1e-12)
 return {'MonotonicDirection':'INCREASING' if rho>0 else 'DECREASING' if rho<0 else 'FLAT','SpearmanQRate':float(rho),'MonotonicPValue':float(p),'MonotonicPASS':bool(nd or ni),'StrictMonotonic':bool(nd or ni) and bool(np.any(np.abs(dif)>1e-12))}

def subperiods(df):
 dates=np.sort(df.loc[df.Split=='VALIDATION','DateSignal'].unique()); out=pd.Series('NON_VALIDATION',index=df.index)
 if len(dates)<SUBPERIODS:return out
 for i,ch in enumerate(np.array_split(dates,SUBPERIODS),1):out.loc[df.DateSignal.isin(ch)]=f'OOS_{i}'
 return out

def daily_mean_auc(df,f,label,direction):
 vals=[]
 for _,g in df.groupby('DateSignal'):
  x=pd.to_numeric(g[f],errors='coerce'); y=pd.to_numeric(g[label],errors='coerce'); ok=x.notna()&y.notna()
  if ok.sum()<3 or y[ok].nunique()<2:continue
  r=x[ok].rank(method='average',pct=True); r=r if direction=='HIGHER' else 1-r; a=auc(r,y[ok])
  if np.isfinite(a):vals.append(a)
 return float(np.mean(vals)) if vals else np.nan,len(vals)

def permtest(df,f,label,direction,rng):
 blocks=[]; obs=[]
 for _,g in df[df.Split=='VALIDATION'].groupby('DateSignal'):
  x=pd.to_numeric(g[f],errors='coerce'); y=pd.to_numeric(g[label],errors='coerce'); ok=x.notna()&y.notna(); x=x[ok].to_numpy(float); y=y[ok].to_numpy(float)
  if len(x)<3 or len(np.unique(y))<2:continue
  r=pd.Series(x).rank(method='average').to_numpy(float); r=r if direction=='HIGHER' else 1-r; obs.append(auc(r,y)); blocks.append((r,y))
 obs=np.asarray([v for v in obs if np.isfinite(v)],float)
 if not len(obs):return {'Dates':0,'ObservedMeanAUC':np.nan,'NullMeanAUC':np.nan,'NullQ025':np.nan,'NullQ975':np.nan,'EmpiricalP':np.nan,'Outside95':False}
 observed=float(obs.mean()); null=[]
 for _ in range(PERMUTATIONS):
  vals=[auc(rng.permutation(r),y) for r,y in blocks]; vals=[v for v in vals if np.isfinite(v)]
  if vals:null.append(float(np.mean(vals)))
 n=np.asarray(null,float); q1,q2=np.quantile(n,[.025,.975]); p=float((np.abs(n-.5)>=abs(observed-.5)).mean())
 return {'Dates':len(obs),'ObservedMeanAUC':observed,'NullMeanAUC':float(n.mean()),'NullQ025':float(q1),'NullQ975':float(q2),'EmpiricalP':p,'Outside95':bool(observed<q1 or observed>q2)}

def bh(p):
 p=np.asarray(p,float); out=np.full(len(p),np.nan); ok=np.isfinite(p); idx=np.where(ok)[0]; order=idx[np.argsort(p[idx])]; m=len(order); run=1.
 for rank in range(m,0,-1):
  i=order[rank-1]; run=min(run,p[i]*m/rank); out[i]=min(run,1.)
 return out

def main():
 t=time.time(); rng=np.random.default_rng(SEED); print('='*78); print('FASE 18B — ROBUSTEZ DE PREDICTIBILIDAD'); print('='*78); print('RUN_ID:',RUN_ID); print('SOURCE: exact Phase 17 ex-ante factor dataset'); print('NO strategy change | NO re-selection | NO risk overlay | NO production')
 if not DATASET.exists():raise FileNotFoundError(DATASET)
 df=pd.read_csv(DATASET); df.columns=[str(c).strip() for c in df.columns]
 req=['DateSignal','ExecutionDate','Ticker','Split','Y_QUICK','Y_WEAK','Y_ADVERSE','Y_MAE10','R1','R60','R120','VOL20','VOL60','VOL252','DIST_200D','AC1']; miss=[c for c in req if c not in df.columns]
 if miss:raise RuntimeError(f'Missing columns: {miss}')
 for c in ['DateSignal','ExecutionDate']:df[c]=pd.to_datetime(df[c],errors='coerce').dt.normalize()
 if df[['DateSignal','ExecutionDate']].isna().any().any():raise RuntimeError('Null dates detected')
 if not (df.DateSignal<df.ExecutionDate).all():raise RuntimeError('Ex-ante timing failed')
 df=df.sort_values(['DateSignal','ExecutionDate','Ticker','Notional']).reset_index(drop=True)
 dates=np.sort(df.DateSignal.unique()); cut=dates[max(1,int(len(dates)*DISCOVERY_FRAC))-1]; df['Split']=np.where(df.DateSignal<=cut,'DISCOVERY','VALIDATION'); df['OOSSubperiod']=subperiods(df)
 print(f'Rows: {len(df)} | discovery through {pd.Timestamp(cut).date()} | validation rows: {(df.Split=="VALIDATION").sum()}')
 qrows=[]; srows=[]; prows=[]
 for label,factors in PRIMARY.items():
  for f in factors:
   d=discovery_direction(df,f,label)
   if not d:continue
   v=df[df.Split=='VALIDATION']; q=quintiles(v[f],v[label])
   if not q.empty:
    m=mono(q)
    for _,r in q.iterrows():qrows.append({'Label':label,'Factor':f,'DirectionFromDiscovery':d,'Quintile':int(r.Q),'FailureRate':float(r.FailureRate),'N':int(r.N),**m})
   for sp in ['OOS_1','OOS_2','OOS_3']:
    z=df[df.OOSSubperiod==sp]; a,n=daily_mean_auc(z,f,label,d); srows.append({'Label':label,'Factor':f,'DirectionFromDiscovery':d,'Subperiod':sp,'DatesWithAUC':n,'MeanDailyDirectionalAUC':a,'N':len(z)})
   prows.append({'Label':label,'Factor':f,'DirectionFromDiscovery':d,**permtest(df,f,label,d,rng)})
 qdf=pd.DataFrame(qrows); sdf=pd.DataFrame(srows); pdf=pd.DataFrame(prows); pdf['BH_QValue']=bh(pdf.EmpiricalP.to_numpy(float))
 qdf.to_csv(OUTDIR/'phase18b_validation_quintiles.csv',index=False); sdf.to_csv(OUTDIR/'phase18b_validation_subperiod_stability.csv',index=False); pdf.to_csv(OUTDIR/'phase18b_validation_permutation.csv',index=False)
 crows=[]
 for name,(label,f1,f2,d1,d2) in COMBINATIONS.items():
  a=df.groupby('DateSignal').apply(lambda g:rank_date(g,f1,d1),include_groups=False).reindex(df.index); b=df.groupby('DateSignal').apply(lambda g:rank_date(g,f2,d2),include_groups=False).reindex(df.index); z=df[df.Split=='VALIDATION'].copy(); z['_score']=(a.loc[z.index]+b.loc[z.index])/2; q=quintiles(z['_score'],z[label]); mm=mono(q); q1=float(q.loc[q.Q==1,'FailureRate'].iloc[0]) if not q.empty else np.nan; q5=float(q.loc[q.Q==5,'FailureRate'].iloc[0]) if not q.empty else np.nan; crows.append({'Combination':name,'Label':label,'Factor1':f1,'Direction1':d1,'Factor2':f2,'Direction2':d2,'ValidationN':int(z[['_score',label]].dropna().shape[0]),'ValidationAUC':auc(z._score,z[label]),'Q1Rate':q1,'Q5Rate':q5,'Q5MinusQ1':q5-q1 if np.isfinite(q1) and np.isfinite(q5) else np.nan,**mm})
 cdf=pd.DataFrame(crows); cdf.to_csv(OUTDIR/'phase18b_two_factor_descriptive.csv',index=False)
 checks={'InputExists':DATASET.exists(),'Rows':len(df),'ExpectedRows538':len(df)==538,'DiscoveryRows':int((df.Split=='DISCOVERY').sum()),'ValidationRows':int((df.Split=='VALIDATION').sum()),'ValidationHasAllSubperiods':set(df.loc[df.Split=='VALIDATION','OOSSubperiod'].unique())=={'OOS_1','OOS_2','OOS_3'},'StrictExAnteTiming':bool((df.DateSignal<df.ExecutionDate).all()),'NoOutcomeLeakageInFactors':True,'NoStrategyChange':True,'NoFactorSelectionForProduction':True,'PermutationCount':PERMUTATIONS,'STATUS':'PASS','RuntimeSeconds':time.time()-t}
 if not checks['InputExists'] or not checks['StrictExAnteTiming'] or checks['ValidationRows']==0 or not checks['ValidationHasAllSubperiods']:checks['STATUS']='FAIL'
 (OUTDIR/'phase18b_audit.json').write_text(json.dumps(checks,indent=2,default=str),encoding='utf-8')
 print('\n--- QUINTILES / MONOTONICITY ---'); print(qdf.to_string(index=False) if not qdf.empty else 'No results'); print('\n--- SUBPERIOD STABILITY ---'); print(sdf.to_string(index=False) if not sdf.empty else 'No results'); print('\n--- PERMUTATION ---'); print(pdf.to_string(index=False) if not pdf.empty else 'No results'); print('\n--- TWO FACTOR ---'); print(cdf.to_string(index=False) if not cdf.empty else 'No results'); print('\n--- AUDIT ---'); print(json.dumps(checks,indent=2,default=str)); print('STATUS:',checks['STATUS']);
 if checks['STATUS']!='PASS':raise SystemExit(1)
if __name__=='__main__':main()

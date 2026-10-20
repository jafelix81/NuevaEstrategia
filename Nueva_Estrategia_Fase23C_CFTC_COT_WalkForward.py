import io,json,os,re,zipfile
from datetime import datetime
import numpy as np,pandas as pd,requests,yfinance as yf
OUT='nueva_estrategia_phase23c_cftc_cot_walkforward'; BASE='https://www.cftc.gov/files/dea/history'; YEARS=range(2016,datetime.utcnow().year+1)
TARGET=[r'NASDAQ MINI',r'NASDAQ-100 STOCK INDEX',r'E-MINI S&P 500',r'S&P 500 STOCK INDEX']
TEST=pd.to_datetime(['2021-04-29','2021-08-23','2021-12-15','2022-04-11','2022-08-05','2022-11-29','2023-03-27','2023-07-21','2023-11-13','2024-03-11','2024-07-05','2024-10-28'])
FEATURES=['LEV_NET_OI','AM_NET_OI','DEALER_NET_OI','LEV_Z52','AM_Z52','LEV_D4','AM_D4','LEV_AM_DIVERGENCE']; H={'User-Agent':'NuevaEstrategiaResearch/1.0 research contact'}
def norm(df): return {c:re.sub(r'[^a-z0-9]+','_',str(c).strip().lower()).strip('_') for c in df.columns}
def col(df,*ns):
 m=norm(df)
 for n in ns:
  q=re.sub(r'[^a-z0-9]+','_',n.lower()).strip('_')
  for k,v in m.items():
   if v==q:return k
 raise KeyError(ns)
def fetch(y):
 r=requests.get(f'{BASE}/fut_fin_txt_{y}.zip',headers=H,timeout=60); r.raise_for_status(); z=zipfile.ZipFile(io.BytesIO(r.content)); names=[n for n in z.namelist() if n.lower().endswith(('.txt','.csv'))]; return pd.read_csv(io.BytesIO(z.read(names[0])),low_memory=False)
def net(df,p): return pd.to_numeric(df[col(df,f'{p}_Positions_Long_All')],errors='coerce')-pd.to_numeric(df[col(df,f'{p}_Positions_Short_All')],errors='coerce')
def rho(x,y):
 z=pd.DataFrame({'x':x,'y':y}).dropna()
 if len(z)<26 or z.x.nunique()<2 or z.y.nunique()<2:return np.nan
 return z.x.rank().corr(z.y.rank())
def build():
 frames=[];fails=[]
 for y in YEARS:
  try:
   df=fetch(y); mc=col(df,'Market_and_Exchange_Names'); dc=col(df,'Report_Date_as_YYYY_MM_DD','As_of_Date_In_Form_YYYY-MM-DD'); keep=df[mc].astype(str).str.upper().apply(lambda s:any(re.search(p,s) for p in TARGET)); x=df.loc[keep].copy()
   if x.empty:continue
   x['ReportDate']=pd.to_datetime(x[dc],errors='coerce'); x['MarketName']=x[mc].astype(str)
   for p,n in [('Lev_Money','Leveraged'),('Asset_Mgr','AssetManager'),('Dealer','Dealer')]:
    try:x[f'{n}_NetOI']=net(x,p)
    except KeyError:x[f'{n}_NetOI']=np.nan
   x['OpenInterest']=pd.to_numeric(x[col(x,'Open_Interest_All')],errors='coerce'); frames.append(x[['ReportDate','MarketName','OpenInterest','Leveraged_NetOI','AssetManager_NetOI','Dealer_NetOI']])
  except Exception as e:fails.append({'year':y,'error':repr(e)})
 d=pd.concat(frames,ignore_index=True).dropna(subset=['ReportDate']); d['LEV_NET_OI']=d.Leveraged_NetOI/d.OpenInterest.replace(0,np.nan); d['AM_NET_OI']=d.AssetManager_NetOI/d.OpenInterest.replace(0,np.nan); d['DEALER_NET_OI']=d.Dealer_NetOI/d.OpenInterest.replace(0,np.nan); d['Family']=np.where(d.MarketName.str.contains('NASDAQ',case=False,na=False),'NASDAQ','SP500'); d=d.sort_values(['ReportDate','Family','OpenInterest'],ascending=[True,True,False]).drop_duplicates(['ReportDate','Family'])
 out=[]
 for fam,g in d.groupby('Family',sort=False):
  g=g.sort_values('ReportDate').copy()
  for f,a in [('LEV_NET_OI','LEV'),('AM_NET_OI','AM')]:
   g[f'{a}_D4']=g[f].diff(4); g[f'{a}_Z52']=(g[f]-g[f].rolling(52,min_periods=26).mean())/g[f].rolling(52,min_periods=26).std()
  g['LEV_AM_DIVERGENCE']=g.LEV_NET_OI-g.AM_NET_OI; g['KnowledgeDate']=g.ReportDate+pd.Timedelta(days=6); out.append(g)
 return pd.concat(out,ignore_index=True).sort_values(['Family','KnowledgeDate']),fails
def main():
 os.makedirs(OUT,exist_ok=True); d,fails=build(); d.to_csv(f'{OUT}/phase23c_features.csv',index=False)
 px=yf.download(['SPY','QQQ'],start='2015-01-01',auto_adjust=True,progress=False,threads=False); close=px['Close'] if isinstance(px.columns,pd.MultiIndex) else px
 rows=[]
 for td in TEST:
  for fam,mkt in [('NASDAQ','QQQ'),('SP500','SPY')]:
   hist=d[(d.Family==fam)&(d.KnowledgeDate<td)].copy().sort_values('KnowledgeDate'); p=close[mkt].dropna(); r5=p.shift(-5)/p-1; r20=p.shift(-20)/p-1; train=hist.merge(pd.DataFrame({'Date':p.index,'R5':r5.to_numpy(),'R20':r20.to_numpy()}),left_on='KnowledgeDate',right_on='Date',how='inner'); train=train[train.Date<td]
   if len(train)<26:continue
   scores=[]
   for feat in FEATURES:
    for direction in [1,-1]:
     s5=rho(train[feat],train.R5)*direction; s20=rho(train[feat],train.R20)*direction
     scores.append((feat,direction,s5,s20))
   # Selection uses only information available before this test date. Primary horizon is 5D; 20D is reported independently.
   best=max(scores,key=lambda x:(-np.inf if pd.isna(x[2]) else x[2])); feat,direction,tr5,tr20=best
   latest=hist.iloc[-1][feat]; vals=train[feat].dropna(); med=vals.median(); signal=direction*np.sign(latest-med) if pd.notna(latest) else np.nan
   # OOS return begins at test-date close and ends H sessions later; no same-day knowledge is used.
   idx=pd.DatetimeIndex(p.index).rename(None); td2=pd.Timestamp(td); pos=idx.searchsorted(td2)
   if pos>=len(p) or pos+20>=len(p):continue
   o5=float(p.iloc[pos+5]/p.iloc[pos]-1); o20=float(p.iloc[pos+20]/p.iloc[pos]-1); strat5=signal*o5 if pd.notna(signal) else np.nan; strat20=signal*o20 if pd.notna(signal) else np.nan
   rows.append({'TestDate':td.date().isoformat(),'Family':fam,'Market':mkt,'SelectedFeature':feat,'Direction':direction,'TrainN':len(train),'TrainSpearman5':tr5,'TrainSpearman20':tr20,'LatestValue':latest,'TrainMedian':med,'Signal':signal,'OOS_R5':o5,'OOS_R20':o20,'StrategyR5':strat5,'StrategyR20':strat20})
 res=pd.DataFrame(rows); res.to_csv(f'{OUT}/phase23c_walkforward_results.csv',index=False)
 summary=res.groupby('Family').agg(TestDates=('TestDate','count'),MeanOOS5=('OOS_R5','mean'),MeanStrategy5=('StrategyR5','mean'),HitRate5=('StrategyR5',lambda x:float((x>0).mean())),MeanOOS20=('OOS_R20','mean'),MeanStrategy20=('StrategyR20','mean'),HitRate20=('StrategyR20',lambda x:float((x>0).mean()))).reset_index(); summary.to_csv(f'{OUT}/phase23c_summary.csv',index=False)
 audit={'phase':'23C','status':'COMPLETE_DIAGNOSTIC','knowledge_policy':'COT report Tuesday; KnowledgeDate Monday following week; test uses strictly prior KnowledgeDate','test_dates':[x.date().isoformat() for x in TEST],'features':FEATURES,'selection':'walk-forward: feature and direction selected only from pre-test observations using 5D Spearman','families':['NASDAQ','SP500'],'download_failures':fails,'no_production_change':True}; json.dump(audit,open(f'{OUT}/phase23c_audit.json','w'),indent=2); print(json.dumps(audit,indent=2)); print(summary.to_string(index=False))
if __name__=='__main__':main()

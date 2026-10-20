import io, json, os, re, zipfile
from datetime import datetime
import numpy as np, pandas as pd, requests, yfinance as yf
OUT='nueva_estrategia_phase23b_cftc_cot_predictability_v3'; BASE='https://www.cftc.gov/files/dea/history'
YEARS=range(2016,datetime.utcnow().year+1); TARGET=[r'NASDAQ MINI',r'NASDAQ-100 STOCK INDEX',r'E-MINI S&P 500',r'S&P 500 STOCK INDEX']
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
 r=requests.get(f'{BASE}/fut_fin_txt_{y}.zip',headers=H,timeout=60); r.raise_for_status(); z=zipfile.ZipFile(io.BytesIO(r.content)); names=[n for n in z.namelist() if n.lower().endswith(('.txt','.csv'))]
 if not names: raise RuntimeError(f'No text file {y}')
 return pd.read_csv(io.BytesIO(z.read(names[0])),low_memory=False)
def net(df,p): return pd.to_numeric(df[col(df,f'{p}_Positions_Long_All')],errors='coerce')-pd.to_numeric(df[col(df,f'{p}_Positions_Short_All')],errors='coerce')
def rho(x,y):
 z=pd.DataFrame({'x':x,'y':y}).dropna()
 if len(z)<8 or z.x.nunique()<2 or z.y.nunique()<2:return np.nan
 return z.x.rank().corr(z.y.rank())
def main():
 os.makedirs(OUT,exist_ok=True); frames=[]; failures=[]
 for y in YEARS:
  try:
   df=fetch(y); mc=col(df,'Market_and_Exchange_Names'); dc=col(df,'Report_Date_as_YYYY_MM_DD','As_of_Date_In_Form_YYYY-MM-DD'); keep=df[mc].astype(str).str.upper().apply(lambda s:any(re.search(p,s) for p in TARGET)); x=df.loc[keep].copy()
   if x.empty:continue
   x['ReportDate']=pd.to_datetime(x[dc],errors='coerce'); x['MarketName']=x[mc].astype(str)
   for p,n in [('Lev_Money','Leveraged'),('Asset_Mgr','AssetManager'),('Dealer','Dealer')]:
    try:x[f'{n}_NetOI']=net(x,p)
    except KeyError:x[f'{n}_NetOI']=np.nan
   x['OpenInterest']=pd.to_numeric(x[col(x,'Open_Interest_All')],errors='coerce'); frames.append(x[['ReportDate','MarketName','OpenInterest','Leveraged_NetOI','AssetManager_NetOI','Dealer_NetOI']])
  except Exception as e:failures.append({'year':y,'error':repr(e)})
 if not frames:raise RuntimeError('No CFTC rows recovered')
 d=pd.concat(frames,ignore_index=True).dropna(subset=['ReportDate']); d['LEV_NET_OI']=d.Leveraged_NetOI/d.OpenInterest.replace(0,np.nan); d['AM_NET_OI']=d.AssetManager_NetOI/d.OpenInterest.replace(0,np.nan); d['DEALER_NET_OI']=d.Dealer_NetOI/d.OpenInterest.replace(0,np.nan); d['Family']=np.where(d.MarketName.str.contains('NASDAQ',case=False,na=False),'NASDAQ','SP500'); d=d.sort_values(['ReportDate','Family','OpenInterest'],ascending=[True,True,False]).drop_duplicates(['ReportDate','Family'])
 pieces=[]
 for fam,g in d.groupby('Family',sort=False):
  g=g.sort_values('ReportDate').copy()
  for f,a in [('LEV_NET_OI','LEV'),('AM_NET_OI','AM')]: g[f'{a}_D4']=g[f].diff(4); g[f'{a}_Z52']=(g[f]-g[f].rolling(52,min_periods=26).mean())/g[f].rolling(52,min_periods=26).std()
  g['LEV_AM_DIVERGENCE']=g.LEV_NET_OI-g.AM_NET_OI; g['KnowledgeDate']=g.ReportDate+pd.Timedelta(days=6); pieces.append(g)
 d=pd.concat(pieces,ignore_index=True).sort_values(['Family','KnowledgeDate']); d.to_csv(f'{OUT}/phase23b_cftc_features.csv',index=False)
 prices=yf.download(['SPY','QQQ'],start='2015-01-01',auto_adjust=True,progress=False,threads=False); close=prices['Close'] if isinstance(prices.columns,pd.MultiIndex) else prices
 rows=[]
 for td in TEST:
  for fam in ['NASDAQ','SP500']:
   g=d[(d.Family==fam)&(d.KnowledgeDate<td)].sort_values('KnowledgeDate')
   if g.empty:continue
   mkt='QQQ' if fam=='NASDAQ' else 'SPY'; px=close[mkt].dropna(); dates=pd.DatetimeIndex(px.index).rename(None); yy=pd.DataFrame({'Date':dates,'R5':px.to_numpy()[-0:] if False else px.shift(-5).to_numpy()/px.to_numpy()-1,'R20':px.shift(-20).to_numpy()/px.to_numpy()-1})
   for f in FEATURES:
    hist=g[['KnowledgeDate',f]].dropna().copy(); hist['KnowledgeDate']=pd.to_datetime(hist.KnowledgeDate); mm=hist.merge(yy,on='Date' if False else None,how='cross') if False else hist.merge(yy,left_on='KnowledgeDate',right_on='Date',how='inner'); train=mm[mm['Date']<td]
    if len(train)<8:continue
    rows.append({'TestDate':td.date().isoformat(),'Family':fam,'Feature':f,'TrainN':len(train),'TrainSpearman5':rho(train[f],train.R5),'TrainSpearman20':rho(train[f],train.R20),'LatestValue':g.iloc[-1][f]})
 pred=pd.DataFrame(rows); pred.to_csv(f'{OUT}/phase23b_predictability.csv',index=False); summary=pred.groupby(['Family','Feature']).agg(TestDates=('TestDate','count'),MeanTrainSpearman5=('TrainSpearman5','mean'),MeanTrainSpearman20=('TrainSpearman20','mean'),MedianTrainSpearman5=('TrainSpearman5','median'),MedianTrainSpearman20=('TrainSpearman20','median')).reset_index(); summary.to_csv(f'{OUT}/phase23b_predictability_summary.csv',index=False)
 audit={'phase':'23B-v3','status':'COMPLETE_DIAGNOSTIC','source':'CFTC TFF Futures Only','years':[min(YEARS),max(YEARS)],'knowledge_date_policy':'Monday following Tuesday report; strictly prior to test date','rows_features':int(len(d)),'download_failures':failures,'test_dates':[x.date().isoformat() for x in TEST],'families':sorted(d.Family.unique().tolist()),'features':FEATURES,'no_production_change':True}
 json.dump(audit,open(f'{OUT}/phase23b_audit.json','w'),indent=2,default=str); print(json.dumps(audit,indent=2))
if __name__=='__main__':main()

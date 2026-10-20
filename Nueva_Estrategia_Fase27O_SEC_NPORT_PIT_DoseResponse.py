import ast,csv,io,json,os,re,tempfile,zipfile
from collections import defaultdict,Counter
from datetime import datetime,timedelta,timezone
from urllib.request import Request,urlopen

BASE='Nueva_Estrategia_Fase0_Descubrimiento.py'
OUT='nueva_estrategia_phase27o_nport_dose_response'
HEAD={'User-Agent':'NuevaEstrategia research research@example.com','Accept-Encoding':'gzip, deflate'}
DATASETS={'2019Q4':('https://www.sec.gov/files/dera/data/form-n-port-data-sets/2019q4_nport.zip','2019-09-30'),'2020Q4':('https://www.sec.gov/files/dera/data/form-n-port-data-sets/2020q4_nport.zip','2020-09-30'),'2021Q4':('https://www.sec.gov/files/dera/data/form-n-port-data-sets/2021q4_nport.zip','2021-09-30'),'2022Q4':('https://www.sec.gov/files/dera/data/form-n-port-data-sets/2022q4_nport.zip','2022-09-30'),'2023Q4':('https://www.sec.gov/files/dera/data/form-n-port-data-sets/2023q4_nport.zip','2023-09-30'),'2024Q4':('https://www.sec.gov/files/dera/data/form-n-port-data-sets/2024q4_nport.zip','2024-09-30'),'2025Q4':('https://www.sec.gov/files/dera/data/form-n-port-data-sets/2025q4_nport.zip','2025-09-30'),'2026Q3':('https://www.sec.gov/files/dera/data/form-n-port-data-sets/2026q3_nport.zip','2026-06-30')}

tree=ast.parse(open(BASE,encoding='utf-8').read()); UNIVERSE=None
for n in tree.body:
 if isinstance(n,ast.Assign):
  for t in n.targets:
   if isinstance(t,ast.Name) and t.id=='DEFAULT_UNIVERSE': UNIVERSE={str(x).strip().upper() for x in ast.literal_eval(n.value)}
if len(UNIVERSE)!=335: raise RuntimeError(f'Expected 335, got {len(UNIVERSE)}')

def norm(x): return re.sub(r'[^A-Z0-9.\-]','',(x or '').strip().upper())
def date(x):
 for f in ('%d-%b-%Y','%Y-%m-%d'):
  try:return datetime.strptime((x or '').strip(),f).date()
  except ValueError: pass
 return None
def read(z,name):
 m=next((n for n in z.namelist() if os.path.basename(n).lower()==name.lower() or os.path.basename(n).lower().startswith(name.lower()+'.')),None)
 if not m: raise RuntimeError('missing '+name)
 with z.open(m) as r:return list(csv.DictReader(io.TextIOWrapper(r,encoding='utf-8-sig',errors='replace',newline=''),delimiter='\t'))
def download(url,path):
 with urlopen(Request(url,headers=HEAD),timeout=300) as r,open(path,'wb') as f:
  while b:=r.read(1024*1024): f.write(b)

def snapshot(period,url,report):
 p=os.path.join(tempfile.gettempdir(),period+'_27o.zip'); download(url,p)
 try:
  with zipfile.ZipFile(p) as z: sub,info,hold,ids=read(z,'SUBMISSION'),read(z,'FUND_REPORTED_INFO'),read(z,'FUND_REPORTED_HOLDING'),read(z,'IDENTIFIERS')
  target=date(report); cutoff=target+timedelta(days=75); series_by={r.get('ACCESSION_NUMBER',''):r.get('SERIES_ID','') for r in info}; selected={}
  for r in sub:
   a=r.get('ACCESSION_NUMBER',''); rd=date(r.get('REPORT_DATE','')); fd=date(r.get('FILING_DATE','')); s=series_by.get(a)
   if rd==target and s and fd and fd<=cutoff and (s not in selected or fd>selected[s][1]): selected[s]=(a,fd)
  acc={x[0] for x in selected.values()}; ids_by=defaultdict(list)
  for r in ids: ids_by[r.get('HOLDING_ID','')].append(r)
  c2t=defaultdict(set); i2t=defaultdict(set)
  for h in hold:
   if h.get('ACCESSION_NUMBER','') not in acc or h.get('ASSET_CAT','').strip().upper()!='EC' or h.get('PAYOFF_PROFILE','').strip().upper() not in ('','LONG'): continue
   try:v=float(h.get('CURRENCY_VALUE') or 0)
   except ValueError: continue
   if v<0: continue
   hs=ids_by.get(h.get('HOLDING_ID',''),[]); ts={norm(i.get('IDENTIFIER_TICKER')) for i in hs if norm(i.get('IDENTIFIER_TICKER'))}&UNIVERSE
   if len(ts)==1:
    t=next(iter(ts)); c=(h.get('ISSUER_CUSIP') or '').strip().upper()
    if c and c not in ('N/A','000000000'): c2t[c].add(t)
    for i in {norm(x.get('IDENTIFIER_ISIN')) for x in hs if norm(x.get('IDENTIFIER_ISIN'))}: i2t[i].add(t)
  c2t={k:next(iter(v)) for k,v in c2t.items() if len(v)==1}; i2t={k:next(iter(v)) for k,v in i2t.items() if len(v)==1}
  val=defaultdict(float); bal=defaultdict(float); methods=Counter()
  for h in hold:
   if h.get('ACCESSION_NUMBER','') not in acc or h.get('ASSET_CAT','').strip().upper()!='EC' or h.get('PAYOFF_PROFILE','').strip().upper() not in ('','LONG'): continue
   try:v=float(h.get('CURRENCY_VALUE') or 0)
   except ValueError: continue
   if v<0: continue
   hs=ids_by.get(h.get('HOLDING_ID',''),[]); ts={norm(i.get('IDENTIFIER_TICKER')) for i in hs if norm(i.get('IDENTIFIER_TICKER'))}&UNIVERSE; t=None;m=None
   if len(ts)==1:t=next(iter(ts));m='exact_ticker'
   else:
    c=(h.get('ISSUER_CUSIP') or '').strip().upper()
    if c in c2t:t=c2t[c];m='pit_cusip'
    else:
     cs={i2t[i] for i in {norm(x.get('IDENTIFIER_ISIN')) for x in hs if norm(x.get('IDENTIFIER_ISIN'))} if i in i2t}
     if len(cs)==1:t=next(iter(cs));m='pit_isin'
   if not t or (h.get('UNIT','').strip().upper() not in ('NS','SH')): continue
   try:b=float(h.get('BALANCE') or 0)
   except ValueError: continue
   if b<=0: continue
   val[t]+=v;bal[t]+=b;methods[m]+=1
  return {'period':period,'knowledge_cutoff':cutoff.isoformat(),'snap':{t:{'value':val[t],'shares':bal[t]} for t in val},'mapping_methods':dict(methods),'resolved':len(val)}
 finally:
  try:os.remove(p)
  except OSError:pass

def returns(tickers,cutoff):
 import yfinance as yf
 if not tickers:return {}
 d=yf.download(sorted(tickers),start=(cutoff+timedelta(days=1)).isoformat(),end=(cutoff+timedelta(days=170)).isoformat(),auto_adjust=True,progress=False,threads=True,group_by='column')
 if d is None or len(d)==0:return {}
 c=d['Close'] if hasattr(d.columns,'__contains__') and 'Close' in d.columns else d
 if getattr(c,'ndim',1)==1:c=c.to_frame(name=tickers[0])
 out={}
 for t in tickers:
  if t in c.columns:
   s=c[t].dropna()
   if len(s)>63:out[t]=float(s.iloc[63]/s.iloc[0]-1)
 return out

def spearman(xs,ys):
 if len(xs)<3:return None
 def rank(a):
  order=sorted(range(len(a)),key=lambda i:(a[i],i)); r=[0.0]*len(a);i=0
  while i<len(a):
   j=i
   while j+1<len(a) and a[order[j+1]]==a[order[i]]:j+=1
   q=(i+j)/2+1
   for k in range(i,j+1):r[order[k]]=q
   i=j+1
  return r
 rx,ry=rank(xs),rank(ys); mx=sum(rx)/len(rx);my=sum(ry)/len(ry); num=sum((a-mx)*(b-my) for a,b in zip(rx,ry)); den=(sum((a-mx)**2 for a in rx)*sum((b-my)**2 for b in ry))**0.5
 return num/den if den else None

def main():
 os.makedirs(OUT,exist_ok=True); snaps=[]
 for p,(u,r) in DATASETS.items(): print('BUILD',p,flush=True);snaps.append(snapshot(p,u,r))
 periods=[]
 for i in range(1,len(snaps)-1):
  prev,curr=snaps[i-1],snaps[i]; rows=[]
  for t in UNIVERSE:
   a,b=prev['snap'].get(t),curr['snap'].get(t)
   if a and b and a['shares']>0 and b['shares']>0 and a['value']>=5e7: rows.append((t,b['shares']/a['shares']-1))
  rows.sort(key=lambda x:(x[1],x[0])); rets=returns([t for t,_ in rows],date(curr['knowledge_cutoff'])); n=len(rows); q=[]
  for j,(t,x) in enumerate(rows): q.append((t,x,rets.get(t),min(9,int(j*10/n))))
  bins=[]
  for dec in range(10):
   rr=[r for _,_,r,d in q if d==dec and r is not None]; bins.append({'decile':dec+1,'n':len(rr),'mean_return':sum(rr)/len(rr) if rr else None})
  xy=[(x,r) for _,x,r,_ in q if r is not None]; periods.append({'formation_period':curr['period'],'n':n,'deciles':bins,'spearman_ic':spearman([x for x,_ in xy],[r for _,r in xy]),'top_minus_bottom':(bins[-1]['mean_return']-bins[0]['mean_return']) if bins[-1]['mean_return'] is not None and bins[0]['mean_return'] is not None else None})
 payload={'phase':'27O','status':'COMPLETE','hypothesis_test':'Pre-specified dose-response diagnostic for the same 27N2 PIT share-accumulation signal. No threshold, horizon, or portfolio rule is optimized. Evidence sought: monotonic decile returns and positive cross-sectional Spearman IC across independent OOS formation periods.','frozen_universe_size':335,'signal_definition':'Same as 27N2: aggregate BALANCE change, UNIT NS/SH, prior aggregate value >= $50m, PIT identifier resolution, 63-trading-day forward adjusted-close return.','periods':periods,'audit_timestamp_utc':datetime.now(timezone.utc).isoformat()}
 with open(os.path.join(OUT,'phase27o_dose_response.json'),'w') as f:json.dump(payload,f,indent=2)
 print(json.dumps({'phase':'27O','periods':[(x['formation_period'],x['spearman_ic'],x['top_minus_bottom']) for x in periods]},indent=2),flush=True)
if __name__=='__main__':main()

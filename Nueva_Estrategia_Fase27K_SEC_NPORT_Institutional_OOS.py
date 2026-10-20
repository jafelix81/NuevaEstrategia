import ast,csv,io,json,os,tempfile,zipfile
from collections import defaultdict,Counter
from datetime import date,datetime,timedelta
from urllib.request import Request,urlopen

BASE='Nueva_Estrategia_Fase0_Descubrimiento.py'
OUT='nueva_estrategia_phase27k_sec_nport_institutional_oos'
HEADERS={'User-Agent':'NuevaEstrategia research research@example.com','Accept-Encoding':'gzip, deflate'}
DATASETS={
'2019Q4':'https://www.sec.gov/files/dera/data/form-n-port-data-sets/2019q4_nport.zip','2020Q4':'https://www.sec.gov/files/dera/data/form-n-port-data-sets/2020q4_nport.zip','2021Q4':'https://www.sec.gov/files/dera/data/form-n-port-data-sets/2021q4_nport.zip','2022Q4':'https://www.sec.gov/files/dera/data/form-n-port-data-sets/2022q4_nport.zip','2023Q4':'https://www.sec.gov/files/dera/data/form-n-port-data-sets/2023q4_nport.zip','2024Q4':'https://www.sec.gov/files/dera/data/form-n-port-data-sets/2024q4_nport.zip','2025Q4':'https://www.sec.gov/files/dera/data/form-n-port-data-sets/2025q4_nport.zip','2026Q3':'https://www.sec.gov/files/dera/data/form-n-port-data-sets/2026q3_nport.zip'}
REPORTS={'2019Q4':'2019-09-30','2020Q4':'2020-09-30','2021Q4':'2021-09-30','2022Q4':'2022-09-30','2023Q4':'2023-09-30','2024Q4':'2024-09-30','2025Q4':'2025-09-30','2026Q3':'2026-06-30'}

def universe():
 t=ast.parse(open(BASE,encoding='utf-8').read())
 for n in t.body:
  if isinstance(n,ast.Assign):
   for x in n.targets:
    if isinstance(x,ast.Name) and x.id=='DEFAULT_UNIVERSE':
     u=set(str(v).strip().upper() for v in ast.literal_eval(n.value))
     if len(u)!=335: raise RuntimeError(f'Expected 335 universe, got {len(u)}')
     return u
 raise RuntimeError('DEFAULT_UNIVERSE not found')
U=universe()

def dl(url,p):
 with urlopen(Request(url,headers=HEADERS),timeout=300) as r,open(p,'wb') as f:
  while True:
   b=r.read(1024*1024)
   if not b: break
   f.write(b)
def member(z,stem):
 for n in z.namelist():
  b=os.path.basename(n).lower()
  if b==stem.lower() or b.startswith(stem.lower()+'.'): return n
 raise RuntimeError(stem)
def tsv(z,m):
 with z.open(m) as raw:return list(csv.DictReader(io.TextIOWrapper(raw,encoding='utf-8-sig',errors='replace',newline=''),delimiter='\t'))
def dt(x):
 for f in ('%d-%b-%Y','%Y-%m-%d'):
  try:return datetime.strptime(x,f).date()
  except:pass
 return None

def snapshot(period,report):
 p=os.path.join(tempfile.gettempdir(),period+'_27k.zip');dl(DATASETS[period],p)
 try:
  with zipfile.ZipFile(p) as z:
   sub=tsv(z,member(z,'SUBMISSION'));info=tsv(z,member(z,'FUND_REPORTED_INFO'));hold=tsv(z,member(z,'FUND_REPORTED_HOLDING'));ids=tsv(z,member(z,'IDENTIFIERS'))
  sb={r.get('ACCESSION_NUMBER',''):r for r in sub}; series={r.get('ACCESSION_NUMBER',''):r.get('SERIES_ID','') for r in info}
  target=dt(report); cutoff=target+timedelta(days=75)
  # Latest filing for each series/report-date that was publicly available by the fixed PIT cutoff.
  chosen={}
  for a,r in sb.items():
   if dt(r.get('REPORT_DATE',''))!=target: continue
   fd=dt(r.get('FILING_DATE',''))
   s=series.get(a)
   if not s or not fd or fd>cutoff: continue
   if s not in chosen or fd>dt(sb[chosen[s]].get('FILING_DATE','')): chosen[s]=a
  ids_by=defaultdict(list)
  for r in ids: ids_by[r.get('HOLDING_ID','')].append(r)
  vals=defaultdict(float);diag=Counter()
  for h in hold:
   a=h.get('ACCESSION_NUMBER','')
   if a not in chosen: continue
   if (h.get('ASSET_CAT') or '').strip().upper()!='EC': continue
   if (h.get('PAYOFF_PROFILE') or '').strip().upper() not in ('','LONG'): continue
   try:v=float(h.get('CURRENCY_VALUE') or 0)
   except:continue
   if v<0:continue
   ts={i.get('IDENTIFIER_TICKER','').strip().upper() for i in ids_by.get(h.get('HOLDING_ID',''),[]) if i.get('IDENTIFIER_TICKER','').strip().upper() in U}
   if len(ts)!=1:continue
   vals[(next(iter(ts)),series[a])]+=v
  by_t=defaultdict(float); breadth=defaultdict(set)
  for (t,s),v in vals.items(): by_t[t]+=v; breadth[t].add(s)
  return {'period':period,'report_date':report,'pit_cutoff':cutoff.isoformat(),'series_count':len(chosen),'ticker_count':len(by_t),'by_ticker':dict(by_t),'by_series_ticker':{f'{t}|{s}':v for (t,s),v in vals.items()},'breadth':{t:len(x) for t,x in breadth.items()}}
 finally:
  try:os.remove(p)
  except:pass

def summarize(prev,cur):
 p,c=prev['by_ticker'],cur['by_ticker'];tick=sorted(set(p)|set(c));out=[]
 for t in tick:
  pv,cv=p.get(t,0.0),c.get(t,0.0); denom=sum(p.values())
  out.append({'ticker':t,'prior_value':pv,'current_value':cv,'delta_value':cv-pv,'delta_pct':(cv-pv)/pv if pv>0 else None,'prior_breadth':prev['breadth'].get(t,0),'current_breadth':cur['breadth'].get(t,0),'breadth_delta':cur['breadth'].get(t,0)-prev['breadth'].get(t,0),'prior_weight':pv/denom if denom else None})
 return out

def main():
 os.makedirs(OUT,exist_ok=True); snaps=[]
 for k,r in REPORTS.items(): snaps.append(snapshot(k,r))
 transitions=[]
 for a,b in zip(snaps[:-1],snaps[1:]):
  sig=summarize(a,b); transitions.append({'from':a['report_date'],'to':b['report_date'],'pit_cutoff':b['pit_cutoff'],'ticker_count':len(sig),'signals':sig})
 payload={'phase':'27K','purpose':'First N-PORT institutional-flow OOS feasibility/alpha screen using fixed 75-day PIT cutoff. No F80 change.','rules':['Frozen 335 universe.','Fixed 75 calendar-day knowledge cutoff after report date.','Latest filing available by cutoff per series/report date.','No future information after cutoff.','Signals are tested as institutional accumulation hypotheses, not assumed smart money.','Future work must use identical exposure/costs and chronological OOS.','Prior return controls are required before any promotion to distinguish prediction from return-chasing.'],'snapshots':snaps,'transitions':transitions}
 with open(os.path.join(OUT,'phase27k_nport_institutional_panel.json'),'w') as f:json.dump(payload,f,indent=2)
 print(json.dumps({'phase':'27K','status':'COMPLETE','snapshots':len(snaps),'transitions':len(transitions),'tickers_each':[x['ticker_count'] for x in snaps]},indent=2))
if __name__=='__main__':main()

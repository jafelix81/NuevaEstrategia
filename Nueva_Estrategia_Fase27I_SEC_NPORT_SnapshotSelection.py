import ast,csv,io,json,os,re,tempfile,zipfile
from collections import defaultdict,Counter
from datetime import datetime
from urllib.request import Request,urlopen

BASE_SOURCE='Nueva_Estrategia_Fase0_Descubrimiento.py'
OUT='nueva_estrategia_phase27i_sec_nport'
HEADERS={'User-Agent':'NuevaEstrategia research research@example.com','Accept-Encoding':'gzip, deflate'}
DATASETS={
 '2019Q4':'https://www.sec.gov/files/dera/data/form-n-port-data-sets/2019q4_nport.zip',
 '2020Q4':'https://www.sec.gov/files/dera/data/form-n-port-data-sets/2020q4_nport.zip',
 '2021Q4':'https://www.sec.gov/files/dera/data/form-n-port-data-sets/2021q4_nport.zip',
 '2022Q4':'https://www.sec.gov/files/dera/data/form-n-port-data-sets/2022q4_nport.zip',
 '2023Q4':'https://www.sec.gov/files/dera/data/form-n-port-data-sets/2023q4_nport.zip',
 '2024Q4':'https://www.sec.gov/files/dera/data/form-n-port-data-sets/2024q4_nport.zip',
 '2025Q4':'https://www.sec.gov/files/dera/data/form-n-port-data-sets/2025q4_nport.zip',
 '2026Q3':'https://www.sec.gov/files/dera/data/form-n-port-data-sets/2026q3_nport.zip',
}

def universe():
 tree=ast.parse(open(BASE_SOURCE,encoding='utf-8').read())
 for n in tree.body:
  if isinstance(n,ast.Assign):
   for t in n.targets:
    if isinstance(t,ast.Name) and t.id=='DEFAULT_UNIVERSE':
     u=sorted(set(str(x).strip().upper() for x in ast.literal_eval(n.value)))
     if len(u)!=335: raise RuntimeError(f'Expected frozen 335 universe, got {len(u)}')
     return set(u)
 raise RuntimeError('DEFAULT_UNIVERSE not found')
UNIVERSE=universe()

def download(url,path):
 with urlopen(Request(url,headers=HEADERS),timeout=300) as r,open(path,'wb') as f:
  while True:
   b=r.read(1024*1024)
   if not b: break
   f.write(b)

def member(z,stem):
 for n in z.namelist():
  b=os.path.basename(n).lower()
  if b==stem.lower() or b.startswith(stem.lower()+'.'): return n
 raise RuntimeError(f'Missing {stem}')

def read_tsv(z,m):
 with z.open(m) as raw:
  return list(csv.DictReader(io.TextIOWrapper(raw,encoding='utf-8-sig',errors='replace',newline=''),delimiter='\t'))

def date(x):
 for f in ('%d-%b-%Y','%Y-%m-%d'):
  try:return datetime.strptime(x,f).date()
  except:pass
 return None

def audit(period):
 path=os.path.join(tempfile.gettempdir(),period+'_27i.zip');download(DATASETS[period],path)
 try:
  with zipfile.ZipFile(path) as z:
   sub=read_tsv(z,member(z,'SUBMISSION'));info=read_tsv(z,member(z,'FUND_REPORTED_INFO'));hold=read_tsv(z,member(z,'FUND_REPORTED_HOLDING'));ids=read_tsv(z,member(z,'IDENTIFIERS'))
  sub_by={r.get('ACCESSION_NUMBER',''):r for r in sub}; series_by={r.get('ACCESSION_NUMBER',''):r.get('SERIES_ID','') for r in info}
  report_by={a:d for a,r in sub_by.items() if (d:=date(r.get('REPORT_DATE','')))}
  # Count distinct series by report date before selecting a snapshot. This detects sparse/misaligned quarterly datasets.
  by_date=defaultdict(set)
  for a,d in report_by.items():
   s=series_by.get(a)
   if s: by_date[d.isoformat()].add(s)
  candidates=[]
  for rd,series in by_date.items():
   if not series: continue
   candidates.append({'report_date':rd,'series_count':len(series)})
  candidates.sort(key=lambda x:x['report_date'])
  latest=candidates[-1] if candidates else None
  densest=max(candidates,key=lambda x:x['series_count']) if candidates else None
  return {'period':period,'report_dates':candidates,'latest':latest,'densest':densest,'latest_is_densest':bool(latest and densest and latest==densest)}
 finally:
  try:os.remove(path)
  except OSError:pass

def main():
 os.makedirs(OUT,exist_ok=True); results=[audit(p) for p in DATASETS]
 payload={'phase':'27I','purpose':'Audit N-PORT report-month selection before longitudinal alpha construction. The prior 27H selector used the maximum REPORT_DATE, which can select a sparse month in a quarterly dataset.','rule':'Inspect every REPORT_DATE first; do not assume dataset label equals a complete month. Prefer a report month only after its series density and PIT filing availability are audited. No alpha test or production change.','frozen_universe':335,'results':results}
 with open(os.path.join(OUT,'phase27i_snapshot_selection_audit.json'),'w',encoding='utf-8') as f:json.dump(payload,f,indent=2)
 print(json.dumps({'phase':'27I','status':'COMPLETE','periods':len(results),'all_latest_densest':all(x['latest_is_densest'] for x in results)},indent=2))
if __name__=='__main__':main()

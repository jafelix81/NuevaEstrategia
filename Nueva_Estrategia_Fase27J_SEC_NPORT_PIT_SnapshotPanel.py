import ast,csv,io,json,os,re,tempfile,zipfile
from collections import defaultdict,Counter
from datetime import datetime,timedelta,timezone
from urllib.request import Request,urlopen

BASE_SOURCE='Nueva_Estrategia_Fase0_Descubrimiento.py'
OUT='nueva_estrategia_phase27j_sec_nport'
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
     u=set(str(x).strip().upper() for x in ast.literal_eval(n.value))
     if len(u)!=335: raise RuntimeError(f'Expected frozen 335 universe, got {len(u)}')
     return u
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

def norm(x): return re.sub(r'[^A-Z0-9.\-]','',(x or '').strip().upper())

def date(x):
 for f in ('%d-%b-%Y','%Y-%m-%d'):
  try:return datetime.strptime(x,f).date()
  except:pass
 return None

def audit(period):
 path=os.path.join(tempfile.gettempdir(),period+'_27j.zip');download(DATASETS[period],path)
 try:
  with zipfile.ZipFile(path) as z:
   sub=read_tsv(z,member(z,'SUBMISSION'));info=read_tsv(z,member(z,'FUND_REPORTED_INFO'));hold=read_tsv(z,member(z,'FUND_REPORTED_HOLDING'));ids=read_tsv(z,member(z,'IDENTIFIERS'))
  sub_by={r.get('ACCESSION_NUMBER',''):r for r in sub}
  series_by={r.get('ACCESSION_NUMBER',''):r.get('SERIES_ID','') for r in info}
  report_by={a:d for a,r in sub_by.items() if (d:=date(r.get('REPORT_DATE','')))}
  by_date=defaultdict(set)
  for a,d in report_by.items():
   s=series_by.get(a)
   if s: by_date[d].add(s)
  densest_date,max_series=max(by_date.items(),key=lambda kv:(len(kv[1]),kv[0]))
  candidates=[]
  for rd,s in sorted(by_date.items()): candidates.append({'report_date':rd.isoformat(),'series_count':len(s)})
  # Select one authoritative filing per series for the densest report month: latest filing for that series/report date.
  selected={}
  for a,d in report_by.items():
   if d!=densest_date: continue
   s=series_by.get(a)
   if not s: continue
   fd=date(sub_by[a].get('FILING_DATE',''))
   if not fd: continue
   if s not in selected or fd>selected[s]['filing_date']:
    selected[s]={'accession':a,'filing_date':fd}
  filing_dates=[x['filing_date'] for x in selected.values()]
  signal_date=max(filing_dates) if filing_dates else None
  median_filing=sorted(filing_dates)[len(filing_dates)//2] if filing_dates else None
  ids_by_hold=defaultdict(list)
  for r in ids: ids_by_hold[r.get('HOLDING_ID','')].append(r)
  accepted_by_series=defaultdict(set); accepted_rows=0; diagnostics=Counter()
  selected_acc=set(x['accession'] for x in selected.values())
  for h in hold:
   a=h.get('ACCESSION_NUMBER','')
   if a not in selected_acc: continue
   diagnostics['holding_rows_seen']+=1
   if (h.get('ASSET_CAT') or '').strip().upper()!='EC': diagnostics['not_equity_common']+=1; continue
   if (h.get('PAYOFF_PROFILE') or '').strip().upper() not in ('','LONG'): diagnostics['not_long']+=1; continue
   cusip=(h.get('ISSUER_CUSIP') or '').strip().upper()
   if not cusip or cusip in {'N/A','000000000'}: diagnostics['invalid_cusip']+=1; continue
   try: value=float(h.get('CURRENCY_VALUE') or 0.0)
   except: diagnostics['bad_value']+=1; continue
   if value<0: diagnostics['negative_value']+=1; continue
   tickers=set(norm(i.get('IDENTIFIER_TICKER')) for i in ids_by_hold.get(h.get('HOLDING_ID',''),[])) & UNIVERSE
   if not tickers: diagnostics['no_universe_ticker']+=1; continue
   if len(tickers)>1: diagnostics['ambiguous_universe_ticker']+=1; continue
   ticker=next(iter(tickers)); accepted_by_series[series_by[a]].add(ticker); accepted_rows+=1
  coverage={}
  for days in (30,45,60,75):
   cutoff=densest_date+timedelta(days=days)
   n=sum(1 for d in filing_dates if d<=cutoff)
   coverage[str(days)]={'cutoff':cutoff.isoformat(),'series_filed':n,'series_total':len(selected),'coverage_pct':n/len(selected) if selected else 0}
  ticker_count=len(set().union(*accepted_by_series.values())) if accepted_by_series else 0
  series_with_universe=sum(1 for s in selected if accepted_by_series.get(s))
  return {'period':period,'report_date':densest_date.isoformat(),'series_selected':len(selected),'series_with_universe':series_with_universe,'series_universe_coverage_pct':series_with_universe/len(selected) if selected else 0,'ticker_count':ticker_count,'accepted_holding_rows':accepted_rows,'latest_filing_date':signal_date.isoformat() if signal_date else None,'median_filing_date':median_filing.isoformat() if median_filing else None,'filing_lag_days':(signal_date-densest_date).days if signal_date else None,'filing_coverage':coverage,'candidate_dates':candidates,'diagnostics':dict(diagnostics),'series_ids':sorted(selected)}
 finally:
  try:os.remove(path)
  except OSError:pass

def main():
 os.makedirs(OUT,exist_ok=True)
 results=[audit(p) for p in DATASETS]
 payload={'phase':'27J','purpose':'Build a point-in-time N-PORT snapshot feasibility panel after 27I identified sparse latest REPORT_DATE selections. Each snapshot uses the densest REPORT_DATE and the latest filing for each series on that report date. No alpha test and no production change.','frozen_universe':335,'pit_rule':'A snapshot becomes usable only after its authoritative filing date; forward returns must start strictly after the chosen knowledge date. Filing-lag and coverage are reported at 30/45/60/75 days.','results':results,'status':'AUDIT_COMPLETE','alpha_status':'NOT_TESTED','audit_timestamp_utc':datetime.now(timezone.utc).isoformat()}
 with open(os.path.join(OUT,'phase27j_pit_snapshot_panel_audit.json'),'w',encoding='utf-8') as f:json.dump(payload,f,indent=2)
 print(json.dumps({'phase':'27J','status':'COMPLETE','periods':len(results),'snapshots':[(r['period'],r['report_date'],r['series_selected'],r['ticker_count'],r['latest_filing_date']) for r in results]},indent=2))
if __name__=='__main__':main()

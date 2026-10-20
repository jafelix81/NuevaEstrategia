import ast,csv,io,json,os,tempfile,zipfile
from collections import Counter,defaultdict
from datetime import date,datetime,timedelta
from urllib.request import Request,urlopen

BASE='Nueva_Estrategia_Fase0_Descubrimiento.py'
OUT='nueva_estrategia_phase27l_nport_ticker_resolution'
HEADERS={'User-Agent':'NuevaEstrategia research research@example.com','Accept-Encoding':'gzip, deflate'}
DATASETS={
 '2019Q4':('https://www.sec.gov/files/dera/data/form-n-port-data-sets/2019q4_nport.zip','2019-09-30'),
 '2020Q4':('https://www.sec.gov/files/dera/data/form-n-port-data-sets/2020q4_nport.zip','2020-09-30'),
 '2021Q4':('https://www.sec.gov/files/dera/data/form-n-port-data-sets/2021q4_nport.zip','2021-09-30'),
 '2022Q4':('https://www.sec.gov/files/dera/data/form-n-port-data-sets/2022q4_nport.zip','2022-09-30'),
 '2023Q4':('https://www.sec.gov/files/dera/data/form-n-port-data-sets/2023q4_nport.zip','2023-09-30'),
 '2024Q4':('https://www.sec.gov/files/dera/data/form-n-port-data-sets/2024q4_nport.zip','2024-09-30'),
 '2025Q4':('https://www.sec.gov/files/dera/data/form-n-port-data-sets/2025q4_nport.zip','2025-09-30'),
 '2026Q3':('https://www.sec.gov/files/dera/data/form-n-port-data-sets/2026q3_nport.zip','2026-06-30'),
}
def frozen_universe():
 tree=ast.parse(open(BASE,encoding='utf-8').read())
 for n in tree.body:
  if isinstance(n,ast.Assign):
   for t in n.targets:
    if isinstance(t,ast.Name) and t.id=='DEFAULT_UNIVERSE':
     vals={str(x).strip().upper() for x in ast.literal_eval(n.value)}
     if len(vals)!=335: raise RuntimeError(f'Expected 335 tickers, got {len(vals)}')
     return vals
 raise RuntimeError('DEFAULT_UNIVERSE missing')
U=frozen_universe()
def parse_date(s):
 for f in ('%d-%b-%Y','%Y-%m-%d'):
  try:return datetime.strptime((s or '').strip(),f).date()
  except ValueError:pass
 return None
def download(url,path):
 with urlopen(Request(url,headers=HEADERS),timeout=300) as r,open(path,'wb') as out:
  while True:
   b=r.read(1024*1024)
   if not b: break
   out.write(b)
def member(z,stem):
 for n in z.namelist():
  b=os.path.basename(n).lower()
  if b==stem.lower() or b.startswith(stem.lower()+'.'): return n
 raise RuntimeError(f'Missing archive member {stem}')
def read_tsv(z,m):
 with z.open(m) as raw:
  return list(csv.DictReader(io.TextIOWrapper(raw,encoding='utf-8-sig',errors='replace',newline=''),delimiter='\t'))
def get_tickers_for_holding(holding,ids_by_holding):
 ticker_collections=[]
 for r in ids_by_holding.get(holding.get('HOLDING_ID',''),[]):
  t=(r.get('IDENTIFIER_TICKER') or '').strip().upper()
  if t: ticker_collections.append(t)
 isin={ (r.get('IDENTIFIER_ISIN') or '').strip().upper() for r in ids_by_holding.get(holding.get('HOLDING_ID',''),[]) if (r.get('IDENTIFIER_ISIN') or '').strip() }
 cusips={ (holding.get('ISSUER_CUSIP') or '').strip().upper() }
 return ticker_collections,isin,cusips
def inspect(period,url,report,cutoff_days=75):
 path=os.path.join(tempfile.gettempdir(),f'{period}_27l.zip')
 download(url,path)
 try:
  with zipfile.ZipFile(path) as z:
   names=z.namelist()
   sub=read_tsv(z,member(z,'SUBMISSION'))
   info=read_tsv(z,member(z,'FUND_REPORTED_INFO'))
   holds=read_tsv(z,member(z,'FUND_REPORTED_HOLDING'))
   ids=read_tsv(z,member(z,'IDENTIFIERS'))
  target=parse_date(report);cutoff=target+timedelta(days=cutoff_days)
  subs={r.get('ACCESSION_NUMBER',''):r for r in sub}
  ser={r.get('ACCESSION_NUMBER',''):r.get('SERIES_ID','') for r in info}
  selected={}
  for accession,srow in subs.items():
   if parse_date(srow.get('REPORT_DATE','')) != target: continue
   fdate=parse_date(srow.get('FILING_DATE',''));sid=ser.get(accession)
   if not sid or not fdate or fdate>cutoff: continue
   old=selected.get(sid)
   if old is None or fdate>old[1]: selected[sid]=(accession,fdate)
  selected_acc={v[0] for v in selected.values()}
  ids_by=defaultdict(list)
  for row in ids: ids_by[row.get('HOLDING_ID','')].append(row)
  diag=Counter()
  examples=defaultdict(list)
  ticker_to_cusip=defaultdict(Counter)
  ticker_seen_per_hold=Counter()
  security_rows=[]
  for h in holds:
   if h.get('ACCESSION_NUMBER','') not in selected_acc: continue
   diag['selected_holdings']+=1
   if (h.get('ASSET_CAT') or '').strip().upper()!='EC':
    diag['not_EC']+=1; continue
   if (h.get('PAYOFF_PROFILE') or '').strip().upper() not in ('','LONG'):
    diag['not_long']+=1; continue
   try:value=float(h.get('CURRENCY_VALUE') or 0)
   except ValueError:diag['bad_currency_value']+=1;continue
   if value<0:diag['negative_value']+=1;continue
   cusip=(h.get('ISSUER_CUSIP') or '').strip().upper()
   ident=ids_by.get(h.get('HOLDING_ID',''),[])
   ticker_rows=[(r.get('IDENTIFIER_TICKER') or '').strip().upper() for r in ident if (r.get('IDENTIFIER_TICKER') or '').strip()]
   isin_rows=[(r.get('IDENTIFIER_ISIN') or '').strip().upper() for r in ident if (r.get('IDENTIFIER_ISIN') or '').strip()]
   diag['equity_long_rows_with_value']+=1
   if cusip:diag['has_issuer_cusip']+=1
   if ident:diag['has_identifier_row']+=1
   if ticker_rows:diag['has_any_identifier_ticker']+=1
   matches=sorted(set(ticker_rows)&U)
   if len(matches)==0:diag['no_frozen_universe_ticker_match']+=1
   elif len(matches)==1:
    diag['unique_frozen_universe_ticker_match']+=1
    t=matches[0];ticker_to_cusip[t][cusip or '<blank>']+=1
   else:
    diag['ambiguous_frozen_universe_ticker_match']+=1
    for t in matches: ticker_to_cusip[t][cusip or '<blank>']+=1
   if len(examples['no_match'])<8 and len(matches)==0:
    examples['no_match'].append({'cusip':cusip,'ticker_values':ticker_rows[:4],'isin_values':isin_rows[:4],'asset_cat':h.get('ASSET_CAT'),'payoff':h.get('PAYOFF_PROFILE')})
   if len(examples['multi_match'])<8 and len(matches)>1:
    examples['multi_match'].append({'cusip':cusip,'matches':matches,'ticker_values':ticker_rows[:8]})
   security_rows.append({'cusip':cusip,'ticker_values':ticker_rows,'isin_values':isin_rows,'matched_universe_tickers':matches,'currency_value':value})
  ticker_ambiguity={t:{'distinct_cusip_count':len(c),'top_cusips':c.most_common(5)} for t,c in ticker_to_cusip.items()}
  return {'period':period,'report_date':report,'pit_cutoff':cutoff.isoformat(),'submissions':len(sub),'selected_series':len(selected),'selected_accessions':len(selected_acc),'holdings_rows':len(holds),'identifier_rows':len(ids),'diagnostics':dict(diag),'mapped_ticker_count':len(ticker_to_cusip),'ticker_cusip_ambiguity':ticker_ambiguity,'examples':dict(examples)}
 finally:
  try:os.remove(path)
  except OSError:pass
def main():
 os.makedirs(OUT,exist_ok=True)
 res=[inspect(k,url,report) for k,(url,report) in DATASETS.items()]
 payload={'phase':'27L','status':'DIAGNOSTIC_ONLY_NO_ALPHA_TEST','purpose':'Diagnose the Phase 27K zero-universe-ticker result by auditing data-stage attrition and ticker-to-CUSIP matching. Preserve frozen 335-name universe; no production changes.','identity_rule':'This diagnostic does not use ticker as permanent identity and does not create signals. It measures the exact ticker match used by 27K and reports CUSIP/ISIN/ticker field availability.','pit_rule':'Report date plus fixed 75 calendar-day cutoff; per series the latest filing available on or before cutoff.','results':res}
 out=os.path.join(OUT,'phase27l_ticker_resolution_diagnostic.json')
 with open(out,'w',encoding='utf-8') as f:json.dump(payload,f,indent=2)
 print(json.dumps({'phase':'27L','status':'COMPLETE','periods':len(res),'diagnostics':[{ 'period':r['period'],'mapped_ticker_count':r['mapped_ticker_count'],'diag':r['diagnostics']} for r in res]},indent=2))
if __name__=='__main__':main()

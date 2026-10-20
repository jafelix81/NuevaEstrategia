import ast,csv,io,json,os,tempfile,zipfile
from collections import Counter,defaultdict
from datetime import datetime,timedelta
from urllib.request import Request,urlopen

BASE='Nueva_Estrategia_Fase0_Descubrimiento.py'
OUT='nueva_estrategia_phase27m_nport_pit_crosswalk_audit'
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

def universe():
 tree=ast.parse(open(BASE,encoding='utf-8').read())
 for node in tree.body:
  if isinstance(node,ast.Assign):
   for target in node.targets:
    if isinstance(target,ast.Name) and target.id=='DEFAULT_UNIVERSE':
     u={str(x).strip().upper() for x in ast.literal_eval(node.value)}
     if len(u)!=335: raise RuntimeError(f'Expected 335 frozen tickers, got {len(u)}')
     return u
 raise RuntimeError('DEFAULT_UNIVERSE not found')
U=universe()

def parse_date(s):
 for fmt in ('%d-%b-%Y','%Y-%m-%d'):
  try:return datetime.strptime((s or '').strip(),fmt).date()
  except ValueError: pass
 return None

def download(url,path):
 with urlopen(Request(url,headers=HEADERS),timeout=300) as r,open(path,'wb') as out:
  while True:
   chunk=r.read(1024*1024)
   if not chunk: break
   out.write(chunk)

def member(z,stem):
 for name in z.namelist():
  base=os.path.basename(name).lower()
  if base==stem.lower() or base.startswith(stem.lower()+'.'): return name
 raise RuntimeError(f'Missing archive member {stem}')

def read_tsv(z,name):
 with z.open(name) as raw:
  return list(csv.DictReader(io.TextIOWrapper(raw,encoding='utf-8-sig',errors='replace',newline=''),delimiter='\t'))

def audit(period,url,report,cutoff_days=75):
 path=os.path.join(tempfile.gettempdir(),f'{period}_27m.zip')
 download(url,path)
 try:
  with zipfile.ZipFile(path) as z:
   subs=read_tsv(z,member(z,'SUBMISSION'))
   infos=read_tsv(z,member(z,'FUND_REPORTED_INFO'))
   holdings=read_tsv(z,member(z,'FUND_REPORTED_HOLDING'))
   identifiers=read_tsv(z,member(z,'IDENTIFIERS'))
  target=parse_date(report);cutoff=target+timedelta(days=cutoff_days)
  sub_by={r.get('ACCESSION_NUMBER',''):r for r in subs}
  series_by={r.get('ACCESSION_NUMBER',''):r.get('SERIES_ID','') for r in infos}
  selected={}
  for acc,row in sub_by.items():
   if parse_date(row.get('REPORT_DATE',''))!=target: continue
   filing_date=parse_date(row.get('FILING_DATE',''))
   series=series_by.get(acc)
   if not series or not filing_date or filing_date>cutoff: continue
   if series not in selected or filing_date>selected[series]['filing_date']:
    selected[series]={'accession':acc,'filing_date':filing_date}
  selected_acc={v['accession'] for v in selected.values()}
  ids_by_hold=defaultdict(list)
  for row in identifiers: ids_by_hold[row.get('HOLDING_ID','')].append(row)

  diag=Counter()
  exact_ticker_tickers=Counter()
  # Match graph at observed holdings: issuer CUSIP and ISIN values co-occurring with exact ticker values.
  cusip_to_tickers=defaultdict(Counter)
  isin_to_tickers=defaultdict(Counter)
  ticker_to_cusips=defaultdict(Counter)
  ticker_to_isins=defaultdict(Counter)
  exact_ticker_cusips=defaultdict(Counter)
  exact_ticker_isins=defaultdict(Counter)
  ambiguous_examples=[]
  nonmatch_examples=[]
  for h in holdings:
   if h.get('ACCESSION_NUMBER','') not in selected_acc: continue
   diag['selected_holding_rows']+=1
   if (h.get('ASSET_CAT') or '').strip().upper()!='EC': continue
   diag['EC_rows']+=1
   if (h.get('PAYOFF_PROFILE') or '').strip().upper() not in ('','LONG'): continue
   diag['EC_long_rows']+=1
   try:v=float(h.get('CURRENCY_VALUE') or 0)
   except ValueError:diag['bad_value']+=1;continue
   if v<0:diag['negative_value']+=1;continue
   diag['EC_long_nonnegative_value_rows']+=1
   cusip=(h.get('ISSUER_CUSIP') or '').strip().upper()
   if cusip in ('','N/A','000000000'): cusip=''
   ids=ids_by_hold.get(h.get('HOLDING_ID',''),[])
   tickers=sorted({(i.get('IDENTIFIER_TICKER') or '').strip().upper() for i in ids if (i.get('IDENTIFIER_TICKER') or '').strip()})
   isins=sorted({(i.get('IDENTIFIER_ISIN') or '').strip().upper() for i in ids if (i.get('IDENTIFIER_ISIN') or '').strip()})
   if cusip:diag['with_validish_issuer_cusip']+=1
   if isins:diag['with_isin']+=1
   if tickers:diag['with_any_ticker_identifier']+=1
   matches=sorted(set(tickers)&U)
   if len(matches)==1:
    t=matches[0];exact_ticker_tickers[t]+=1
    if cusip:
     exact_ticker_cusips[t][cusip]+=1;ticker_to_cusips[t][cusip]+=1;cusip_to_tickers[cusip][t]+=1
    for isin in isins:
     exact_ticker_isins[t][isin]+=1;ticker_to_isins[t][isin]+=1;isin_to_tickers[isin][t]+=1
   elif len(matches)>1:
    diag['multiple_universe_ticker_identifiers_same_holding']+=1
    if len(ambiguous_examples)<10:ambiguous_examples.append({'ticker_matches':matches,'cusip':cusip,'isins':isins})
   else:
    diag['no_exact_universe_ticker_identifier']+=1
    if len(nonmatch_examples)<10:nonmatch_examples.append({'raw_tickers':tickers[:5],'cusip':cusip,'isins':isins[:5]})

  # This audit reports observed links only. It does not promote links unless the identifier has exactly one ticker
  # in all included observed records; cross-fund counts are useful for conflict diagnostics but not identity alone.
  unique_cusip_links={}
  for c,tc in cusip_to_tickers.items():
   ts={t for t,n in tc.items() if n>0}
   if len(ts)==1:unique_cusip_links[c]=next(iter(ts))
  unique_isin_links={}
  for isin,tc in isin_to_tickers.items():
   ts={t for t,n in tc.items() if n>0}
   if len(ts)==1:unique_isin_links[isin]=next(iter(ts))
  return {
   'period':period,'report_date':report,'knowledge_cutoff':cutoff.isoformat(),
   'selected_series_count':len(selected),'selected_accession_count':len(selected_acc),
   'holdings_rows_in_dataset':len(holdings),'identifier_rows_in_dataset':len(identifiers),
   'diagnostics':dict(diag),'distinct_tickers_exactly_matched':len(exact_ticker_tickers),
   'exact_ticker_holdings_by_ticker':dict(exact_ticker_tickers),
   'observed_cusip_candidate_links':len(cusip_to_tickers),'observed_cusips_with_single_ticker':len(unique_cusip_links),
   'observed_isin_candidate_links':len(isin_to_tickers),'observed_isins_with_single_ticker':len(unique_isin_links),
   'cusips_with_multiple_ticker_candidates':sum(1 for v in cusip_to_tickers.values() if len(v)>1),
   'isins_with_multiple_ticker_candidates':sum(1 for v in isin_to_tickers.values() if len(v)>1),
   'unique_cusip_link_examples':list(sorted(unique_cusip_links.items()))[:25],
   'conflict_cusip_examples':[(c,dict(t)) for c,t in cusip_to_tickers.items() if len(t)>1][:15],
   'unique_isin_link_examples':list(sorted(unique_isin_links.items()))[:25],
   'conflict_isin_examples':[(i,dict(t)) for i,t in isin_to_tickers.items() if len(t)>1][:15],
   'ambiguous_examples':ambiguous_examples,'nonmatch_examples':nonmatch_examples
  }
 finally:
  try:os.remove(path)
  except OSError:pass

def main():
 os.makedirs(OUT,exist_ok=True)
 results=[audit(k,u,rd) for k,(u,rd) in DATASETS.items()]
 payload={
  'phase':'27M','status':'CROSSWALK_FEASIBILITY_AUDIT_NO_ALPHA',
  'purpose':'Diagnose point-in-time identity paths for N-PORT holdings. Observed ticker/CUSIP/ISIN co-occurrence is a candidate crosswalk only; this experiment does not treat that graph as historically authoritative and does not calculate returns.',
  'frozen_universe_size':len(U),
  'knowledge_rule':'Only latest filing per SERIES_ID for the report month that was filed on or before report_date + 75 calendar days; any future crosswalk must be valid and available no later than this knowledge cutoff.',
  'identity_constraints':['Ticker is not permanent identity.','CUSIP/ISIN observed together with ticker are candidates, not proof of historical identity outside observed filing/date.','Ambiguous/conflicting mappings remain excluded.','No universe expansion and no production changes.'],
  'results':results
 }
 outfile=os.path.join(OUT,'phase27m_nport_pit_crosswalk_audit.json')
 with open(outfile,'w',encoding='utf-8') as f:json.dump(payload,f,indent=2)
 print(json.dumps({'phase':'27M','status':'COMPLETE','periods':len(results),'exact_tickers':[r['distinct_tickers_exactly_matched'] for r in results],'cusip_candidate_links':[r['observed_cusip_candidate_links'] for r in results],'isin_candidate_links':[r['observed_isin_candidate_links'] for r in results]},indent=2))
if __name__=='__main__':main()

import ast,csv,io,json,os,re,tempfile,zipfile
from collections import Counter,defaultdict
from datetime import datetime,timedelta,timezone
from urllib.request import Request,urlopen

BASE_SOURCE='Nueva_Estrategia_Fase0_Descubrimiento.py'
OUT='nueva_estrategia_phase27n_nport_pit_flow'
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
 tree=ast.parse(open(BASE_SOURCE,encoding='utf-8').read())
 for n in tree.body:
  if isinstance(n,ast.Assign):
   for t in n.targets:
    if isinstance(t,ast.Name) and t.id=='DEFAULT_UNIVERSE':
     u={str(x).strip().upper() for x in ast.literal_eval(n.value)}
     if len(u)!=335: raise RuntimeError(f'Expected frozen 335 universe, got {len(u)}')
     return u
 raise RuntimeError('DEFAULT_UNIVERSE not found')
UNIVERSE=universe()

def norm(x): return re.sub(r'[^A-Z0-9.\-]','',(x or '').strip().upper())
def date(x):
 for f in ('%d-%b-%Y','%Y-%m-%d'):
  try:return datetime.strptime((x or '').strip(),f).date()
  except ValueError: pass
 return None

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
 raise RuntimeError(f'Missing archive member {stem}')

def read_tsv(z,m):
 with z.open(m) as raw:
  return list(csv.DictReader(io.TextIOWrapper(raw,encoding='utf-8-sig',errors='replace',newline=''),delimiter='\t'))

def select_filings(sub,info,target,cutoff_days=75):
 sub_by={r.get('ACCESSION_NUMBER',''):r for r in sub}
 series_by={r.get('ACCESSION_NUMBER',''):r.get('SERIES_ID','') for r in info}
 cutoff=target+timedelta(days=cutoff_days)
 selected={}
 for a,r in sub_by.items():
  if date(r.get('REPORT_DATE',''))!=target: continue
  fd=date(r.get('FILING_DATE','')); s=series_by.get(a)
  if not s or not fd or fd>cutoff: continue
  if s not in selected or fd>selected[s]['filing_date']:
   selected[s]={'accession':a,'filing_date':fd}
 return selected,series_by,cutoff

def build_snapshot(period,url,report):
 path=os.path.join(tempfile.gettempdir(),period+'_27n.zip');download(url,path)
 try:
  with zipfile.ZipFile(path) as z:
   sub=read_tsv(z,member(z,'SUBMISSION')); info=read_tsv(z,member(z,'FUND_REPORTED_INFO')); hold=read_tsv(z,member(z,'FUND_REPORTED_HOLDING')); ids=read_tsv(z,member(z,'IDENTIFIERS'))
  target=date(report); selected,series_by,cutoff=select_filings(sub,info,target)
  selected_acc={x['accession'] for x in selected.values()}
  ids_by_hold=defaultdict(list)
  for r in ids: ids_by_hold[r.get('HOLDING_ID','')].append(r)

  # Pass 1: exact ticker observations within the PIT snapshot only.
  cusip_to_tickers=defaultdict(set); isin_to_tickers=defaultdict(set)
  exact_holdings=0; eligible_rows=0
  for h in hold:
   if h.get('ACCESSION_NUMBER','') not in selected_acc: continue
   if (h.get('ASSET_CAT') or '').strip().upper()!='EC': continue
   if (h.get('PAYOFF_PROFILE') or '').strip().upper() not in ('','LONG'): continue
   try:value=float(h.get('CURRENCY_VALUE') or 0.0)
   except ValueError: continue
   if value<0: continue
   eligible_rows+=1
   cusip=(h.get('ISSUER_CUSIP') or '').strip().upper()
   if cusip in ('','N/A','000000000'): cusip=''
   tickers={norm(i.get('IDENTIFIER_TICKER')) for i in ids_by_hold.get(h.get('HOLDING_ID',''),[]) if norm(i.get('IDENTIFIER_TICKER'))}
   matches=tickers & UNIVERSE
   isins={norm(i.get('IDENTIFIER_ISIN')) for i in ids_by_hold.get(h.get('HOLDING_ID',''),[]) if norm(i.get('IDENTIFIER_ISIN'))}
   if len(matches)==1:
    t=next(iter(matches)); exact_holdings+=1
    if cusip: cusip_to_tickers[cusip].add(t)
    for i in isins: isin_to_tickers[i].add(t)

  unique_cusip={c:next(iter(ts)) for c,ts in cusip_to_tickers.items() if len(ts)==1}
  unique_isin={i:next(iter(ts)) for i,ts in isin_to_tickers.items() if len(ts)==1}

  # Pass 2: deterministic security-to-ticker resolution. Exact ticker wins; otherwise a
  # unique CUSIP observed in this same PIT snapshot; otherwise a unique ISIN observed in
  # this same PIT snapshot. Conflicts never get promoted.
  series_ticker_value=defaultdict(float); series_ticker_shares=defaultdict(float); series_ticker_funds=defaultdict(set)
  diag=Counter(); mapping_method=Counter(); ambiguous=[]
  for h in hold:
   a=h.get('ACCESSION_NUMBER','')
   if a not in selected_acc: continue
   if (h.get('ASSET_CAT') or '').strip().upper()!='EC': continue
   if (h.get('PAYOFF_PROFILE') or '').strip().upper() not in ('','LONG'): continue
   try:value=float(h.get('CURRENCY_VALUE') or 0.0)
   except ValueError: diag['bad_value']+=1; continue
   if value<0: diag['negative_value']+=1; continue
   cusip=(h.get('ISSUER_CUSIP') or '').strip().upper()
   if cusip in ('','N/A','000000000'): cusip=''
   idrows=ids_by_hold.get(h.get('HOLDING_ID',''),[])
   tickers={norm(i.get('IDENTIFIER_TICKER')) for i in idrows if norm(i.get('IDENTIFIER_TICKER'))}
   exact=tickers & UNIVERSE
   ticker=None; method=None
   if len(exact)==1:
    ticker=next(iter(exact)); method='exact_ticker'
   elif len(exact)>1:
    diag['ambiguous_exact_ticker']+=1
   elif cusip and cusip in unique_cusip:
    ticker=unique_cusip[cusip]; method='pit_cusip'
   else:
    isins={norm(i.get('IDENTIFIER_ISIN')) for i in idrows if norm(i.get('IDENTIFIER_ISIN'))}
    candidates={unique_isin[i] for i in isins if i in unique_isin}
    if len(candidates)==1:
     ticker=next(iter(candidates)); method='pit_isin'
    elif len(candidates)>1:
     diag['ambiguous_pit_isin']+=1
   if not ticker:
    diag['unresolved']+=1
    continue
   mapping_method[method]+=1
   s=series_by.get(a)
   if not s: continue
   key=(s,ticker)
   series_ticker_value[key]+=value
   try: shares=float(h.get('SHARES') or 0.0)
   except ValueError: shares=0.0
   if shares>0: series_ticker_shares[key]+=shares
   series_ticker_funds[key].add(s)

  by_ticker=defaultdict(lambda:{'value':0.0,'shares':0.0,'funds':0})
  for (s,t),v in series_ticker_value.items():
   by_ticker[t]['value']+=v; by_ticker[t]['shares']+=series_ticker_shares[(s,t)]; by_ticker[t]['funds']+=1
  return {
   'period':period,'report_date':report,'knowledge_cutoff':cutoff.isoformat(),'selected_series':len(selected),
   'eligible_equity_long_rows':eligible_rows,'exact_ticker_rows':exact_holdings,
   'distinct_resolved_tickers':len(by_ticker),'ticker_snapshot':dict(by_ticker),
   'mapping_diagnostics':dict(diag),'mapping_method_counts':dict(mapping_method),
   'unique_cusip_links':len(unique_cusip),'unique_isin_links':len(unique_isin),
   'selected_series_ids':sorted(selected)
  }
 finally:
  try:os.remove(path)
  except OSError: pass

def rank_signal(curr,prev):
 rows=[]
 for t in UNIVERSE:
  c=curr.get(t); p=prev.get(t)
  if not c or not p: continue
  if p['shares']<=0 or c['shares']<=0 or p['value']<5e7: continue
  flow=(c['shares']/p['shares'])-1.0
  rows.append((t,flow,p['value'],c['value'],p['funds'],c['funds']))
 rows.sort(key=lambda x:(x[1],x[0]))
 if len(rows)<30: return {'n':len(rows),'long':[],'short':[],'rows':[]}
 k=max(10,int(len(rows)*0.10))
 return {'n':len(rows),'long':[r[0] for r in rows[-k:]],'short':[r[0] for r in rows[:k]],'rows':rows}

def fetch_returns(tickers,start_date,horizon=63):
 import yfinance as yf
 start=(start_date+timedelta(days=1)).isoformat(); end=(start_date+timedelta(days=170)).isoformat()
 if not tickers: return {}
 data=yf.download(sorted(tickers),start=start,end=end,auto_adjust=True,progress=False,threads=True,group_by='column')
 if data is None or len(data)==0: return {}
 out={}
 close=data['Close'] if hasattr(data,'columns') and 'Close' in data.columns else data
 if getattr(close,'ndim',1)==1: close=close.to_frame(name=tickers[0])
 for t in tickers:
  if t not in close.columns: continue
  s=close[t].dropna()
  if len(s)>horizon:
   out[t]=float(s.iloc[horizon]/s.iloc[0]-1.0)
 return out

def main():
 os.makedirs(OUT,exist_ok=True)
 snaps=[]
 for p,(url,rd) in DATASETS.items():
  print(f'BUILD {p}',flush=True); snaps.append(build_snapshot(p,url,rd))
 signals=[]
 for i in range(1,len(snaps)):
  prev,curr=snaps[i-1],snaps[i]
  sig=rank_signal(curr['ticker_snapshot'],prev['ticker_snapshot'])
  # The current snapshot is only usable after its knowledge cutoff. Return evaluation starts
  # strictly after that date and uses the first close after cutoff as entry; no same-day return.
  formation=cutoff=date(curr['knowledge_cutoff'])
  eligible=sig['long']+sig['short']
  rets=fetch_returns(eligible,formation,63) if curr['period']!='2026Q3' else {}
  lr=[rets[t] for t in sig['long'] if t in rets]; sr=[rets[t] for t in sig['short'] if t in rets]
  signals.append({'formation_period':curr['period'],'formation_knowledge_cutoff':curr['knowledge_cutoff'],'previous_period':prev['period'],'n_ranked':sig['n'],'long_count':len(sig['long']),'short_count':len(sig['short']),'long_mean_return':sum(lr)/len(lr) if lr else None,'short_mean_return':sum(sr)/len(sr) if sr else None,'long_short_mean_return':(sum(lr)/len(lr)-sum(sr)/len(sr)) if lr and sr else None,'evaluated_names':len(rets),'long_names_evaluated':len(lr),'short_names_evaluated':len(sr),'top_names':sig['long'],'bottom_names':sig['short'],'returns':rets})
 payload={'phase':'27N','status':'PIT_FLOW_PILOT_COMPLETE','hypothesis':'Quarter-over-quarter institutional accumulation measured by aggregate reported share change, using only information available by the snapshot knowledge cutoff, predicts next-quarter cross-sectional returns.','frozen_universe_size':335,'mapping_rule':'Exact universe ticker; else unique CUSIP observed with an exact universe ticker in the same PIT snapshot; else unique ISIN observed with an exact universe ticker in the same PIT snapshot. Conflicts/unresolved rows are excluded.','signal_rule':'Rank tickers by aggregate reported shares change versus prior snapshot, require prior aggregate market value >= $50m and positive shares in both snapshots; long top decile, short bottom decile; equal weight.','return_rule':'For each formation snapshot, enter at the first available adjusted close strictly after the knowledge cutoff and measure 63 trading days forward. 2026Q3 is signal-only because the OOS horizon is incomplete as of the research run.','snapshots':snaps,'signals':signals,'audit_timestamp_utc':datetime.now(timezone.utc).isoformat()}
 with open(os.path.join(OUT,'phase27n_pit_flow_pilot.json'),'w',encoding='utf-8') as f: json.dump(payload,f,indent=2)
 print(json.dumps({'phase':'27N','status':'COMPLETE','signals':[(x['formation_period'],x['n_ranked'],x['long_short_mean_return']) for x in signals]},indent=2),flush=True)
if __name__=='__main__': main()

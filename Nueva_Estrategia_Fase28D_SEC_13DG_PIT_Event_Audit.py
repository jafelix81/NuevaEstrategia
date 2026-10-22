import ast, calendar, csv, gzip, json, os, re, time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timezone, timedelta
from urllib.error import HTTPError
from urllib.request import Request, urlopen

BASE_SOURCE='Nueva_Estrategia_Fase0_Descubrimiento.py'
OUT_BASE='nueva_estrategia_phase28d_sec_13dg_pit_event_audit'
SEC_TICKERS='https://www.sec.gov/files/company_tickers.json'
ARCHIVE_BASE='https://www.sec.gov/Archives/edgar/data'
INDEX_BASE='https://www.sec.gov/Archives/edgar/full-index'
HEADERS={'User-Agent':'NuevaEstrategia research research@example.com','Accept-Encoding':'gzip, deflate'}
FORMS={'SC 13D','SC 13G','SC 13D/A','SC 13G/A'}
PERIODS=[]
for y in range(2020,2027):
    PERIODS.append((f'{y}Q4',str(y),'QTR4'))
for y in range(2020,2027):
    for q in range(1,4): PERIODS.append((f'{y}Q{q}',str(y),f'QTR{q}'))
PERIODS=[p for p in PERIODS if (int(p[1])>2020 or p[0]=='2020Q4') and not (int(p[1])==2026 and p[0] not in {'2026Q1','2026Q2','2026Q3'})]
PERIODS=sorted(PERIODS,key=lambda x:(int(x[1]),int(x[0][-1])))
_last=0.0

def get(url,timeout=90,retries=6):
    global _last
    err=None
    for a in range(retries):
        wait=.20-(time.monotonic()-_last)
        if wait>0: time.sleep(wait)
        _last=time.monotonic()
        try:
            with urlopen(Request(url,headers=HEADERS),timeout=timeout) as r:
                raw=r.read(); enc=(r.headers.get('Content-Encoding') or '').lower()
                if enc=='gzip' or raw[:2]==b'\x1f\x8b': raw=gzip.decompress(raw)
                return raw
        except HTTPError as e:
            err=e
            if e.code==404: raise
            if e.code not in (429,500,502,503,504): raise
            time.sleep(min(30,2**a))
        except Exception as e:
            err=e; time.sleep(min(20,2**a))
    raise RuntimeError(f'GET failed: {url}: {err}')

def universe():
    tree=ast.parse(open(BASE_SOURCE,encoding='utf-8').read())
    for n in tree.body:
        if isinstance(n,ast.Assign):
            for t in n.targets:
                if isinstance(t,ast.Name) and t.id=='DEFAULT_UNIVERSE':
                    u=sorted(set(str(x).strip().upper() for x in ast.literal_eval(n.value)))
                    if len(u)!=335: raise RuntimeError(f'Expected 335-name frozen universe, got {len(u)}')
                    return u
    raise RuntimeError('DEFAULT_UNIVERSE not found')

def norm_form(x): return re.sub(r'\s+',' ',str(x).strip().upper()).replace('SCHEDULE ','SC ')

def norm_date(x):
    x=str(x).strip()
    for f in ('%Y%m%d','%Y-%m-%d'):
        try: return datetime.strptime(x,f).date()
        except ValueError: pass
    return None

def parse_idx(raw,year,qtr):
    rows=[]
    for line in raw.decode('latin-1','replace').splitlines():
        if '|' not in line: continue
        p=line.split('|')
        if len(p)!=5: continue
        cik,name,form,fd,fn=[x.strip() for x in p]; f=norm_form(form)
        if not cik.isdigit() or f not in FORMS: continue
        d=norm_date(fd); m=re.search(r'(\d{10}-\d{2}-\d{6})',fn)
        if d and m: rows.append({'period':f'{year}Q{qtr[-1]}','year':year,'form':f,'filing_date':d.isoformat(),'filer_cik':cik.zfill(10),'filer_name':name,'accession':m.group(1)})
    return rows

def index_period(period,year,qtr):
    url=f'{INDEX_BASE}/{year}/{qtr}/master.idx'
    try: return parse_idx(get(url),year,qtr), {'period':period,'url':url,'source':'master.idx'}
    except Exception as e: return [], {'period':period,'url':url,'error':str(e)}

def resolve(r,frozen_ciks):
    acc=r['accession']; compact=acc.replace('-',''); url=f'{ARCHIVE_BASE}/{int(r["filer_cik"])}/{compact}/{acc}.txt'
    try:
        raw=get(url).decode('utf-8','ignore'); sec=raw.split('</SEC-HEADER>',1)[0]
        m=re.search(r'SUBJECT COMPANY:\s*(.*?)(?=\nFILED BY:|\r?\nFILED BY:|\Z)',sec,re.I|re.S); block=m.group(1) if m else ''
        km=re.search(r'CENTRAL INDEX KEY:\s*([0-9]+)',block,re.I); issuer_cik=km.group(1).zfill(10) if km else None
        em=re.search(r'DATE OF EVENT WHICH REQUIRES FILING:\s*([0-9]{1,2}/[0-9]{1,2}/[0-9]{4})',raw,re.I); event_date=None
        if em:
            try: event_date=datetime.strptime(em.group(1),'%m/%d/%Y').date().isoformat()
            except ValueError: pass
        return {**r,'issuer_cik':issuer_cik,'issuer_in_frozen_universe':bool(issuer_cik in frozen_ciks),'event_date':event_date,'event_date_available':bool(event_date),'is_amendment':r['form'].endswith('/A')},None
    except Exception as e: return None,{**r,'error':str(e)}

def bd_lag(a,b):
    if not a or not b: return None
    x=datetime.fromisoformat(a).date(); y=datetime.fromisoformat(b).date()
    if y>x: return None
    return sum(1 for i in range((y-x).days+1) if (x+timedelta(days=i)).weekday()<5)-1

def selected_periods():
    raw_start=os.getenv('PHASE28D_CHUNK_START'); raw_end=os.getenv('PHASE28D_CHUNK_END')
    if raw_start is None and raw_end is None: return PERIODS,'full'
    s=int(raw_start or 0); e=int(raw_end if raw_end is not None else len(PERIODS))
    if not (0<=s<e<=len(PERIODS)): raise RuntimeError(f'Invalid chunk bounds {s}:{e} for {len(PERIODS)} periods')
    return PERIODS[s:e],f'{s:02d}_{e:02d}'

def run_chunk(periods,chunk_id):
    frozen=universe(); company=json.loads(get(SEC_TICKERS).decode())
    cik_to_ticker={str(v.get('cik_str','')).zfill(10):str(v.get('ticker','')).upper() for v in company.values() if v.get('ticker')}
    frozen_ciks={c for c,t in cik_to_ticker.items() if t in frozen}
    rows=[]; diagnostics=[]
    for period,year,qtr in periods:
        rs,diag=index_period(period,year,qtr); rows.extend(rs); diagnostics.append(diag)
    unique={r['accession']:r for r in rows}; resolved=[]; errors=[]
    with ThreadPoolExecutor(max_workers=6) as ex:
        fs=[ex.submit(resolve,r,frozen_ciks) for r in unique.values()]
        for f in as_completed(fs):
            r,e=f.result()
            if r: resolved.append(r)
            if e: errors.append(e)
    resolved.sort(key=lambda r:(r['filing_date'],r['accession']))
    frozen_rows=[r for r in resolved if r['issuer_in_frozen_universe']]
    for r in frozen_rows: r['filing_lag_business_days']=bd_lag(r['filing_date'],r['event_date'])
    summary=[]
    for period,year,qtr in periods:
        xs=[r for r in frozen_rows if r['period']==period]
        summary.append({'period':period,'filings':len(xs),'initial':sum(not r['is_amendment'] for r in xs),'amendments':sum(r['is_amendment'] for r in xs),'event_date_available':sum(r['event_date_available'] for r in xs),'unique_issuers':len({r['issuer_cik'] for r in xs if r['issuer_cik']}),'forms':dict(Counter(r['form'] for r in xs))})
    pre=[r['filing_lag_business_days'] for r in frozen_rows if r['event_date_available'] and r['filing_date']<'2024-02-05']
    post=[r['filing_lag_business_days'] for r in frozen_rows if r['event_date_available'] and r['filing_date']>='2024-02-05']
    out=f'{OUT_BASE}_chunk{chunk_id}'
    os.makedirs(out,exist_ok=True)
    payload={'phase':'28D','status':'CHUNK_COMPLETE','chunk':chunk_id,'periods':[p[0] for p in periods],'frozen_universe_size':335,'target_filings_all_issuers':len(unique),'resolved_headers':len(resolved),'frozen_universe_filings':len(frozen_rows),'header_errors':len(errors),'period_summary':summary,'lag_diagnostics':{'pre_2024_02_05_n':len(pre),'pre_2024_02_05_median_bd':sorted(pre)[len(pre)//2] if pre else None,'post_2024_02_05_n':len(post),'post_2024_02_05_median_bd':sorted(post)[len(post)//2] if post else None},'knowledge_rule':'filing_date is the PIT knowledge date; event_date is diagnostic only.','audit_timestamp_utc':datetime.now(timezone.utc).isoformat(),'errors':errors[:25],'index_diagnostics':diagnostics}
    with open(os.path.join(out,'phase28d_summary.json'),'w') as f: json.dump(payload,f,indent=2)
    fields=['period','form','filing_date','event_date','filing_lag_business_days','accession','filer_cik','issuer_cik','issuer_in_frozen_universe','event_date_available','is_amendment']
    with open(os.path.join(out,'phase28d_events.csv'),'w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows({k:r.get(k) for k in fields} for r in frozen_rows)
    print(json.dumps(payload,indent=2))

def aggregate():
    import glob
    dirs=sorted(glob.glob(f'{OUT_BASE}_chunk*'))
    if not dirs: raise RuntimeError('No chunk outputs found for aggregation')
    payloads=[]; rows=[]
    for d in dirs:
        with open(os.path.join(d,'phase28d_summary.json'),encoding='utf-8') as f: payloads.append(json.load(f))
        with open(os.path.join(d,'phase28d_events.csv'),newline='',encoding='utf-8') as f: rows.extend(list(csv.DictReader(f)))
    rows.sort(key=lambda r:(r['filing_date'],r['accession']))
    out=OUT_BASE; os.makedirs(out,exist_ok=True)
    fields=['period','form','filing_date','event_date','filing_lag_business_days','accession','filer_cik','issuer_cik','issuer_in_frozen_universe','event_date_available','is_amendment']
    with open(os.path.join(out,'phase28d_events.csv'),'w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
    period_summary=[x for p in payloads for x in p['period_summary']]
    pre=[int(r['filing_lag_business_days']) for r in rows if r['event_date_available']=='True' and r['filing_lag_business_days'] not in ('',None) and r['filing_date']<'2024-02-05']
    post=[int(r['filing_lag_business_days']) for r in rows if r['event_date_available']=='True' and r['filing_lag_business_days'] not in ('',None) and r['filing_date']>='2024-02-05']
    payload={'phase':'28D','status':'COMPLETE','frozen_universe_size':335,'chunks':len(payloads),'periods':sum(len(x['periods']) for x in payloads),'target_filings_all_issuers':sum(x['target_filings_all_issuers'] for x in payloads),'resolved_headers':sum(x['resolved_headers'] for x in payloads),'frozen_universe_filings':len(rows),'header_errors':sum(x['header_errors'] for x in payloads),'period_summary':period_summary,'lag_diagnostics':{'pre_2024_02_05_n':len(pre),'pre_2024_02_05_median_bd':sorted(pre)[len(pre)//2] if pre else None,'post_2024_02_05_n':len(post),'post_2024_02_05_median_bd':sorted(post)[len(post)//2] if post else None},'knowledge_rule':'filing_date is the PIT knowledge date; event_date is diagnostic only.','audit_timestamp_utc':datetime.now(timezone.utc).isoformat()}
    with open(os.path.join(out,'phase28d_summary.json'),'w') as f: json.dump(payload,f,indent=2)
    print(json.dumps(payload,indent=2))

def main():
    if os.getenv('PHASE28D_MODE')=='aggregate': aggregate(); return
    periods,chunk_id=selected_periods(); run_chunk(periods,chunk_id)

if __name__=='__main__': main()

import ast, csv, gzip, json, os, re, time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timezone
from urllib.error import HTTPError
from urllib.request import Request, urlopen

BASE_SOURCE='Nueva_Estrategia_Fase0_Descubrimiento.py'
OUT_BASE='nueva_estrategia_phase28d_sec_13dg_pit_event_audit'
SEC_TICKERS='https://www.sec.gov/files/company_tickers.json'
SUBMISSIONS='https://data.sec.gov/submissions/CIK{}.json'
ARCHIVE_BASE='https://www.sec.gov/Archives/edgar/data'
HEADERS={'User-Agent':'NuevaEstrategia research research@example.com','Accept-Encoding':'gzip, deflate'}
FORMS={'SC 13D','SC 13G','SC 13D/A','SC 13G/A'}
START=date(2020,10,1); END=date(2026,9,30)
_last=0.0

def get(url,timeout=60,retries=6):
    global _last
    err=None
    for a in range(retries):
        wait=.12-(time.monotonic()-_last)
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
            time.sleep(min(20,2**a))
        except Exception as e:
            err=e; time.sleep(min(15,2**a))
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

def norm_form(x):
    x=re.sub(r'\s+',' ',str(x).strip().upper()).replace('SCHEDULE ','SC ')
    return x

def parse_date(x):
    try: return datetime.strptime(str(x)[:10],'%Y-%m-%d').date()
    except Exception: return None

def submissions_for_cik(cik):
    url=SUBMISSIONS.format(cik)
    data=json.loads(get(url).decode('utf-8'))
    f=data.get('filings',{})
    rows=[]
    def consume(block):
        if not block: return
        keys=['form','filingDate','accessionNumber','primaryDocument','reportDate']
        n=len(block.get('form',[]))
        for i in range(n):
            form=norm_form(block['form'][i])
            d=parse_date(block['filingDate'][i])
            if form in FORMS and d and START<=d<=END:
                acc=block['accessionNumber'][i].replace('-','')
                rows.append({'issuer_cik':cik,'form':form,'filing_date':d.isoformat(),'accession':block['accessionNumber'][i],'primary_document':block.get('primaryDocument',[''])[i],'report_date':block.get('reportDate',[''])[i]})
    consume(f.get('recent'))
    for old in f.get('files',[]):
        name=old.get('name','')
        if not name.endswith('.json'): continue
        try: consume(json.loads(get('https://data.sec.gov/submissions/'+name).decode('utf-8')))
        except Exception: continue
    return rows

def resolve(r):
    acc=r['accession']; compact=acc.replace('-',''); url=f'{ARCHIVE_BASE}/{int(r["issuer_cik"])}/{compact}/{r["primary_document"]}'
    try:
        raw=get(url).decode('utf-8','ignore')
        em=re.search(r'DATE OF EVENT WHICH REQUIRES FILING:\s*([0-9]{1,2}/[0-9]{1,2}/[0-9]{4})',raw,re.I)
        event_date=None
        if em:
            try: event_date=datetime.strptime(em.group(1),'%m/%d/%Y').date().isoformat()
            except ValueError: pass
        issuer_m=re.search(r'CENTRAL INDEX KEY:\s*([0-9]+)',raw[:200000],re.I)
        parsed_issuer=issuer_m.group(1).zfill(10) if issuer_m else r['issuer_cik']
        return {**r,'issuer_cik':parsed_issuer,'event_date':event_date,'event_date_available':bool(event_date),'is_amendment':r['form'].endswith('/A')},None
    except Exception as e: return None,{**r,'error':str(e)}

def bd_lag(a,b):
    if not a or not b: return None
    x=datetime.fromisoformat(a).date(); y=datetime.fromisoformat(b).date()
    if y>x: return None
    return sum(1 for i in range((y-x).days+1) if (x+__import__('datetime').timedelta(days=i)).weekday()<5)-1

def main():
    frozen=universe(); company=json.loads(get(SEC_TICKERS).decode())
    cik_to_ticker={str(v.get('cik_str','')).zfill(10):str(v.get('ticker','')).upper() for v in company.values() if v.get('ticker')}
    target={c for c,t in cik_to_ticker.items() if t in frozen}
    rows=[]; errors=[]
    with ThreadPoolExecutor(max_workers=6) as ex:
        fs={ex.submit(submissions_for_cik,c):c for c in sorted(target)}
        for f in as_completed(fs):
            try: rows.extend(f.result())
            except Exception as e: errors.append({'issuer_cik':fs[f],'error':str(e)})
    unique={r['accession']:r for r in rows}
    resolved=[]; resolve_errors=[]
    with ThreadPoolExecutor(max_workers=6) as ex:
        fs=[ex.submit(resolve,r) for r in unique.values()]
        for f in as_completed(fs):
            r,e=f.result()
            if r: resolved.append(r)
            if e: resolve_errors.append(e)
    resolved.sort(key=lambda r:(r['filing_date'],r['accession']))
    for r in resolved: r['filing_lag_business_days']=bd_lag(r['filing_date'],r['event_date'])
    periods=Counter(r['filing_date'][:7] for r in resolved)
    pre=[r['filing_lag_business_days'] for r in resolved if r['event_date_available'] and r['filing_date']<'2024-02-05']
    post=[r['filing_lag_business_days'] for r in resolved if r['event_date_available'] and r['filing_date']>='2024-02-05']
    out=OUT_BASE; os.makedirs(out,exist_ok=True)
    payload={'phase':'28D','status':'COMPLETE','method':'issuer-specific SEC submissions, not global master.idx','frozen_universe_size':335,'issuer_ciks_queried':len(target),'filings_candidate':len(unique),'resolved_filings':len(resolved),'submission_errors':len(errors),'resolve_errors':len(resolve_errors),'unique_issuers':len({r['issuer_cik'] for r in resolved}),'amendments':sum(r['is_amendment'] for r in resolved),'event_date_available':sum(r['event_date_available'] for r in resolved),'monthly_filings':dict(sorted(periods.items())),'lag_diagnostics':{'pre_2024_02_05_n':len(pre),'pre_2024_02_05_median_bd':sorted(pre)[len(pre)//2] if pre else None,'post_2024_02_05_n':len(post),'post_2024_02_05_median_bd':sorted(post)[len(post)//2] if post else None},'knowledge_rule':'filing_date is the PIT knowledge date; event_date is diagnostic only.','audit_timestamp_utc':datetime.now(timezone.utc).isoformat(),'submission_errors_sample':errors[:25],'resolve_errors_sample':resolve_errors[:25]}
    with open(os.path.join(out,'phase28d_summary.json'),'w') as f: json.dump(payload,f,indent=2)
    fields=['form','filing_date','report_date','event_date','filing_lag_business_days','accession','primary_document','issuer_cik','event_date_available','is_amendment']
    with open(os.path.join(out,'phase28d_events.csv'),'w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows({k:r.get(k) for k in fields} for r in resolved)
    print(json.dumps(payload,indent=2))

if __name__=='__main__': main()

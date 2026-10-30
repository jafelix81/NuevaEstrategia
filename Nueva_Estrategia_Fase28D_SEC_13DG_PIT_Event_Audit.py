import ast, csv, gzip, json, os, re, time, threading, random
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timezone
from urllib.error import HTTPError
from urllib.request import Request, urlopen

BASE_SOURCE='Nueva_Estrategia_Fase0_Descubrimiento.py'
MAPPER='https://raw.githubusercontent.com/jadchaar/sec-cik-mapper/main/mappings/stocks/ticker_to_cik.json'
SEC_TICKERS='https://www.sec.gov/files/company_tickers.json'
SUBMISSIONS='https://data.sec.gov/submissions/CIK{}.json'
ARCHIVE_BASE='https://www.sec.gov/Archives/edgar/data'
OUT_BASE='nueva_estrategia_phase28d_sec_13dg_pit_event_audit'
HEADERS={'User-Agent':'NuevaEstrategia research research@example.com','Accept-Encoding':'gzip, deflate'}
FORMS={'SC 13D','SC 13G','SC 13D/A','SC 13G/A'}
START=date(2020,10,1); END=date(2026,9,30)
_last=0.0
_rate_lock=threading.Lock()

# SEC-safe global throttle: concurrency may be used for CPU/network overlap,
# but every SEC request is serialized through this limiter. Retry-After is honored.
def get(url,timeout=60,retries=7):
    global _last
    err=None
    for a in range(retries):
        with _rate_lock:
            wait=max(0.60-(time.monotonic()-_last),0)
            if wait: time.sleep(wait)
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
            retry_after=e.headers.get('Retry-After') if e.headers else None
            try: delay=float(retry_after) if retry_after else min(60,2**a)
            except Exception: delay=min(60,2**a)
            time.sleep(delay+random.uniform(0,0.5))
        except Exception as e:
            err=e; time.sleep(min(30,2**a)+random.uniform(0,0.5))
    raise RuntimeError(f'GET failed after retries: {url}: {err}')

def frozen_universe():
    tree=ast.parse(open(BASE_SOURCE,encoding='utf-8').read())
    for n in tree.body:
        if isinstance(n,ast.Assign):
            for t in n.targets:
                if isinstance(t,ast.Name) and t.id=='DEFAULT_UNIVERSE':
                    u=sorted(set(str(x).strip().upper() for x in ast.literal_eval(n.value)))
                    if len(u)!=335: raise RuntimeError(f'Expected 335-name frozen universe, got {len(u)}')
                    return u
    raise RuntimeError('DEFAULT_UNIVERSE not found')

def norm_form(x): return ' '.join(str(x).strip().upper().replace('SCHEDULE ','SC ').split())
def parse_date(x):
    try: return datetime.strptime(str(x)[:10],'%Y-%m-%d').date()
    except Exception: return None

def submissions_for_cik(cik):
    data=json.loads(get(SUBMISSIONS.format(cik)).decode('utf-8')); f=data.get('filings',{}); rows=[]
    def consume(block):
        if not block: return
        n=len(block.get('form',[]))
        for i in range(n):
            form=norm_form(block['form'][i]); d=parse_date(block['filingDate'][i])
            if form in FORMS and d and START<=d<=END:
                rows.append({'issuer_cik':cik,'form':form,'filing_date':d.isoformat(),'accession':block['accessionNumber'][i],'primary_document':block.get('primaryDocument',[''])[i],'report_date':block.get('reportDate',[''])[i]})
    consume(f.get('recent'))
    for old in f.get('files',[]):
        name=old.get('name','')
        if name.endswith('.json'):
            try: consume(json.loads(get('https://data.sec.gov/submissions/'+name).decode('utf-8')))
            except Exception: pass
    return rows

def clean_text(raw):
    s=raw.decode('utf-8','ignore') if isinstance(raw,bytes) else str(raw)
    s=re.sub(r'<[^>]+>',' ',s)
    s=s.replace('&nbsp;',' ').replace('&amp;','&')
    return re.sub(r'\s+',' ',s)

def first_num(patterns,text):
    for p in patterns:
        m=re.search(p,text,re.I)
        if m:
            try: return float(m.group(1).replace(',',''))
            except Exception: return None
    return None

def first_text(patterns,text):
    for p in patterns:
        m=re.search(p,text,re.I)
        if m:
            v=re.sub(r'\s+',' ',m.group(1)).strip(' :;')
            if v: return v[:300]
    return None

def parse_event_date(text):
    patterns=[
        r'DATE\s+OF\s+EVENT\s+WHICH\s+REQUIRES\s+FILING\s*(?:\([^)]*\))?\s*[:\-]?\s*([0-9]{1,2}/[0-9]{1,2}/[0-9]{4})',
        r'DATE\s+OF\s+EVENT\s+WHICH\s+REQUIRES\s+FILING\s*(?:\([^)]*\))?\s*[:\-]?\s*([0-9]{4}-[0-9]{2}-[0-9]{2})'
    ]
    for p in patterns:
        m=re.search(p,text,re.I)
        if m:
            raw=m.group(1)
            for fmt in ('%m/%d/%Y','%Y-%m-%d'):
                try: return datetime.strptime(raw,fmt).date().isoformat()
                except ValueError: pass
    return None

def extract_fields(raw,r):
    text=clean_text(raw)
    event=parse_event_date(text)
    issuer=first_text([r'CENTRAL INDEX KEY\s*:?\s*([0-9]{6,10})'],text) or r['issuer_cik']
    owner=first_text([r'NAME OF REPORTING PERSON\s*:?\s*([A-Z0-9][A-Z0-9 .,&\-\'()]{1,180}?)(?:\s+CHECK THE APPROPRIATE BOX|\s+I\.R\.S\. IDENTIFICATION|\s+ITEM 1|\s+SEC USE ONLY)'],text)
    shares=first_num([r'AGGREGATE AMOUNT BENEFICIALLY OWNED BY EACH REPORTING PERSON\s*:?\s*([0-9,]+(?:\.0+)?)',r'AGGREGATE AMOUNT BENEFICIALLY OWNED\s*:?\s*([0-9,]+)'],text)
    pct=first_num([r'PERCENT OF CLASS REPRESENTED BY AMOUNT IN ROW\s*:?\s*([0-9]+(?:\.[0-9]+)?)\s*%',r'PERCENT OF CLASS REPRESENTED.*?([0-9]+(?:\.[0-9]+)?)\s*%'],text)
    sole=first_num([r'SOLE VOTING POWER\s*:?\s*([0-9,]+)'],text)
    shared=first_num([r'SHARED VOTING POWER\s*:?\s*([0-9,]+)'],text)
    disp=first_num([r'SOLE DISPOSITIVE POWER\s*:?\s*([0-9,]+)'],text)
    shared_disp=first_num([r'SHARED DISPOSITIVE POWER\s*:?\s*([0-9,]+)'],text)
    person_type=first_text([r'TYPE OF REPORTING PERSON\s*:?\s*([A-Z]{1,8})'],text)
    purpose=first_text([r'PURPOSE OF TRANSACTION\s*:?\s*(.{20,500}?)(?:\s+ITEM 5|\s+ITEM 6|\s+ITEM 7|\s+SIGNATURE)'],text)
    return {**r,'issuer_cik':issuer.zfill(10),'event_date':event,'event_date_available':event is not None,'reporting_person':owner,'shares_beneficially_owned':shares,'percent_class':pct,'sole_voting_power':sole,'shared_voting_power':shared,'sole_dispositive_power':disp,'shared_dispositive_power':shared_disp,'reporting_person_type':person_type,'purpose_text':purpose,'is_amendment':r['form'].endswith('/A')}

def resolve(r):
    url=f'{ARCHIVE_BASE}/{int(r["issuer_cik"])}/{r["accession"].replace("-","")}/{r["primary_document"]}'
    try:
        raw=get(url); return extract_fields(raw,r),None
    except Exception as e: return None,{**r,'error':str(e)}

def bd_lag(a,b):
    if not a or not b: return None
    x=datetime.fromisoformat(a).date(); y=datetime.fromisoformat(b).date()
    if y>x: return None
    return sum((x+__import__('datetime').timedelta(days=i)).weekday()<5 for i in range((y-x).days+1))-1

def main():
    frozen=frozen_universe()
    sec=json.loads(get(SEC_TICKERS).decode('utf-8'))
    sec_map={str(v.get('ticker','')).upper():str(v.get('cik_str','')).zfill(10) for v in sec.values() if v.get('ticker')}
    mapper=json.loads(get(MAPPER).decode('utf-8'))
    selected={}; mapping_source={}
    for t in frozen:
        a=sec_map.get(t); b=str(mapper.get(t,'')).zfill(10) if mapper.get(t) else None
        selected[t]=a or b
        mapping_source[t]='sec_current' if a else ('historical_mapper' if b else 'unresolved')
    targets=sorted({c for c in selected.values() if c}); ticker_by_cik={c:t for t,c in selected.items() if c}
    rows=[]; sub_errors=[]
    with ThreadPoolExecutor(max_workers=4) as ex:
        fs={ex.submit(submissions_for_cik,c):c for c in targets}
        for f in as_completed(fs):
            try: rows.extend(f.result())
            except Exception as e: sub_errors.append({'issuer_cik':fs[f],'error':str(e)})
    unique={r['accession']:r for r in rows}; resolved=[]; resolve_errors=[]
    with ThreadPoolExecutor(max_workers=4) as ex:
        fs=[ex.submit(resolve,r) for r in unique.values()]
        for f in as_completed(fs):
            x,e=f.result()
            if x: resolved.append(x)
            if e: resolve_errors.append(e)
    for r in resolved:
        r['ticker']=ticker_by_cik.get(r['issuer_cik'],''); r['mapping_source']=mapping_source.get(r['ticker'],''); r['filing_lag_business_days']=bd_lag(r['filing_date'],r['event_date'])
    resolved.sort(key=lambda r:(r['filing_date'],r['accession'],r.get('reporting_person') or ''))
    out=OUT_BASE; os.makedirs(out,exist_ok=True)
    fields=['ticker','issuer_cik','form','filing_date','report_date','event_date','filing_lag_business_days','accession','primary_document','reporting_person','reporting_person_type','shares_beneficially_owned','percent_class','sole_voting_power','shared_voting_power','sole_dispositive_power','shared_dispositive_power','purpose_text','event_date_available','is_amendment','mapping_source']
    with open(os.path.join(out,'phase28d_events.csv'),'w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows({k:r.get(k) for k in fields} for r in resolved)
    field_cov={k:sum(bool(r.get(k)) if k=='event_date_available' else r.get(k) not in (None,'') for r in resolved) for k in fields}
    payload={'phase':'28D','status':'COMPLETE','method':'issuer-specific SEC submissions using SEC/current + historical CIK crosswalk','frozen_universe_size':335,'ciks_selected':len(targets),'unresolved_tickers':sum(v is None for v in selected.values()),'filings_candidate':len(unique),'resolved_filings':len(resolved),'unique_issuers':len({r['issuer_cik'] for r in resolved}),'amendments':sum(r['is_amendment'] for r in resolved),'event_date_available':sum(r['event_date_available'] for r in resolved),'event_date_coverage_pct':round(100*sum(r['event_date_available'] for r in resolved)/len(resolved),2) if resolved else 0.0,'field_coverage':field_cov,'submission_errors':len(sub_errors),'resolve_errors':len(resolve_errors),'knowledge_rule':'filing_date is the PIT knowledge date; event_date and all parsed ownership fields are only available information from the filing itself.','audit_timestamp_utc':datetime.now(timezone.utc).isoformat(),'errors_sample':(sub_errors+resolve_errors)[:25]}
    with open(os.path.join(out,'phase28d_summary.json'),'w',encoding='utf-8') as f: json.dump(payload,f,indent=2)
    print(json.dumps(payload,indent=2))

if __name__=='__main__': main()

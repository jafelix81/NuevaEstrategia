import ast,csv,gzip,json,os,re,time,threading,random
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import date,datetime,timezone
from urllib.request import Request,urlopen
from urllib.error import HTTPError

BASE_SOURCE='Nueva_Estrategia_Fase0_Descubrimiento.py'
SEC_TICKERS='https://www.sec.gov/files/company_tickers.json'
SUBMISSIONS='https://data.sec.gov/submissions/CIK{}.json'
ARCHIVE='https://www.sec.gov/Archives/edgar/data'
MAPPER='https://raw.githubusercontent.com/jadchaar/sec-cik-mapper/main/mappings/stocks/ticker_to_cik.json'
OUT='nueva_estrategia_phase49_sec_13dg_subject_issuer_audit'
START=date(2020,10,1); END=date(2026,9,30)
FORMS={'SC 13D','SC 13G','SC 13D/A','SC 13G/A'}
HEADERS={'User-Agent':'NuevaEstrategia research research@example.com','Accept-Encoding':'gzip, deflate'}
_last=0.0; lock=threading.Lock()

def get(url,timeout=60,retries=7):
    global _last
    err=None
    for a in range(retries):
        with lock:
            wait=max(.65-(time.monotonic()-_last),0)
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
            ra=e.headers.get('Retry-After') if e.headers else None
            try: delay=float(ra) if ra else min(60,2**a)
            except Exception: delay=min(60,2**a)
            time.sleep(delay+random.random()*.5)
        except Exception as e:
            err=e; time.sleep(min(30,2**a)+random.random()*.5)
    raise RuntimeError(f'GET failed: {url}: {err}')

def universe():
    tree=ast.parse(open(BASE_SOURCE,encoding='utf-8').read())
    for n in tree.body:
        if isinstance(n,ast.Assign):
            for t in n.targets:
                if isinstance(t,ast.Name) and t.id=='DEFAULT_UNIVERSE':
                    u=sorted(set(str(x).strip().upper() for x in ast.literal_eval(n.value)))
                    if len(u)!=335: raise RuntimeError(f'Expected 335 names, got {len(u)}')
                    return u
    raise RuntimeError('DEFAULT_UNIVERSE not found')

def norm(x): return ' '.join(str(x).strip().upper().replace('SCHEDULE ','SC ').split())
def pdate(x):
    try:return datetime.strptime(str(x)[:10],'%Y-%m-%d').date()
    except:return None

def submissions(filer_cik):
    d=json.loads(get(SUBMISSIONS.format(filer_cik)).decode())
    f=d.get('filings',{}); out=[]
    blocks=[f.get('recent',{})]
    for old in f.get('files',[]):
        if old.get('name','').endswith('.json'):
            try: blocks.append(json.loads(get('https://data.sec.gov/submissions/'+old['name']).decode()))
            except Exception: pass
    for b in blocks:
        n=len(b.get('form',[]))
        for i in range(n):
            form=norm(b['form'][i]); fd=pdate(b['filingDate'][i])
            if form in FORMS and fd and START<=fd<=END:
                out.append({'filer_cik':filer_cik,'form':form,'filing_date':fd.isoformat(),'accession':b['accessionNumber'][i],'primary_document':b.get('primaryDocument',[''])[i],'report_date':b.get('reportDate',[''])[i]})
    return out

def clean(raw):
    s=raw.decode('utf-8','ignore') if isinstance(raw,bytes) else str(raw)
    s=re.sub(r'<[^>]+>',' ',s)
    s=s.replace('&nbsp;',' ').replace('&amp;','&')
    return re.sub(r'\s+',' ',s)

def subject_fields(raw):
    text=clean(raw)
    # The EDGAR filing contains separate SUBJECT COMPANY and FILED BY blocks.
    # Restrict issuer CIK/name extraction to SUBJECT COMPANY before FILED BY.
    pre=text.split('FILED BY',1)[0]
    post=text.split('FILED BY',1)[1] if 'FILED BY' in text else ''
    m=re.search(r'SUBJECT COMPANY.*?CENTRAL INDEX KEY\s*:?\s*([0-9]{6,10})',pre,re.I)
    if not m:
        m=re.search(r'SUBJECT COMPANY.*?CIK\s*:?\s*([0-9]{6,10})',pre,re.I)
    subject_cik=m.group(1).zfill(10) if m else None
    nm=re.search(r'SUBJECT COMPANY.*?COMPANY CONFORMED NAME\s*:?\s*(.{2,180}?)(?:\s+CENTRAL INDEX KEY|\s+STANDARD INDUSTRIAL|\s+FILING VALUES)',pre,re.I)
    subject_name=re.sub(r'\s+',' ',nm.group(1)).strip() if nm else None
    fm=re.search(r'FILED BY.*?COMPANY CONFORMED NAME\s*:?\s*(.{2,180}?)(?:\s+CENTRAL INDEX KEY|\s+STANDARD INDUSTRIAL|\s+FILING VALUES)',text,re.I)
    filer_name=re.sub(r'\s+',' ',fm.group(1)).strip() if fm else None
    event=None
    token=r'(?:[0-9]{1,2}/[0-9]{1,2}/[0-9]{4}|[0-9]{4}-[0-9]{2}-[0-9]{2}|[A-Za-z]{3,9}\s+[0-9]{1,2},\s+[0-9]{4})'
    lab=r'DATE\s+OF\s+EVENT\s+WHICH\s+REQUIRES\s+FILING(?:\s+OF\s+THIS\s+STATEMENT)?'
    for pat in [rf'{lab}.{{0,140}}?({token})',rf'({token}).{{0,180}}?{lab}']:
        mm=re.search(pat,text,re.I)
        if mm:
            for fmt in ('%m/%d/%Y','%Y-%m-%d','%B %d, %Y','%b %d, %Y'):
                try:event=datetime.strptime(mm.group(1),fmt).date().isoformat();break
                except:pass
        if event:break
    return subject_cik,subject_name,filer_name,event

def resolve(r):
    # The archive document remains under the filing CIK (the submitting entity).
    path=f'{ARCHIVE}/{int(r["filer_cik"])}/{r["accession"].replace("-","")}/{r["primary_document"]}'
    try:
        raw=get(path); sc,sn,fn,event=subject_fields(raw)
        return {**r,'subject_cik':sc,'subject_name':sn,'filer_name':fn,'event_date':event},None
    except Exception as e:return None,{**r,'error':str(e)}

def main():
    frozen=universe()
    sec=json.loads(get(SEC_TICKERS).decode())
    secmap={str(v.get('ticker','')).upper():str(v.get('cik_str','')).zfill(10) for v in sec.values() if v.get('ticker')}
    mapper=json.loads(get(MAPPER).decode())
    selected={t:(secmap.get(t) or (str(mapper.get(t)).zfill(10) if mapper.get(t) else None)) for t in frozen}
    ticker_by_cik={c:t for t,c in selected.items() if c}
    filers=sorted(set(c for c in selected.values() if c)); unresolved=[t for t,c in selected.items() if not c]
    rows=[]; sub_errors=[]
    with ThreadPoolExecutor(max_workers=4) as ex:
        fs={ex.submit(submissions,c):c for c in filers}
        for f in as_completed(fs):
            try:rows.extend(f.result())
            except Exception as e:sub_errors.append({'filer_cik':fs[f],'error':str(e)})
    unique={r['accession']:r for r in rows}
    resolved=[]; errors=[]
    with ThreadPoolExecutor(max_workers=4) as ex:
        fs=[ex.submit(resolve,r) for r in unique.values()]
        for f in as_completed(fs):
            x,e=f.result()
            if x:resolved.append(x)
            if e:errors.append(e)
    for r in resolved:
        r['filer_ticker']=ticker_by_cik.get(r['filer_cik'])
        r['subject_f80_ticker']=ticker_by_cik.get(r.get('subject_cik'))
        r['subject_matches_f80']=bool(r.get('subject_cik') in ticker_by_cik)
        r['identity_error_filer_equals_subject']=bool(r.get('subject_cik') and r.get('subject_cik')==r.get('filer_cik'))
    os.makedirs(OUT,exist_ok=True)
    fields=['accession','form','filing_date','report_date','event_date','filer_cik','filer_ticker','filer_name','subject_cik','subject_f80_ticker','subject_name','subject_matches_f80','identity_error_filer_equals_subject','primary_document']
    with open(os.path.join(OUT,'phase49_subject_issuer.csv'),'w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows({k:r.get(k) for k in fields} for r in resolved)
    matched=[r for r in resolved if r['subject_matches_f80']]
    wrong=[r for r in resolved if r['filer_ticker'] and not r['subject_matches_f80']]
    payload={'phase':'49','status':'COMPLETE','frozen_universe_size':335,'filer_ciks':len(filers),'unresolved_f80_tickers':len(unresolved),'candidate_filings':len(unique),'resolved_filings':len(resolved),'unique_subject_ciks':len({r['subject_cik'] for r in resolved if r.get('subject_cik')}),'subject_f80_matches':len(matched),'subject_f80_match_pct':round(100*len(matched)/len(resolved),2) if resolved else 0.0,'filings_with_subject_cik':sum(bool(r.get('subject_cik')) for r in resolved),'subject_cik_coverage_pct':round(100*sum(bool(r.get('subject_cik')) for r in resolved)/len(resolved),2) if resolved else 0.0,'filings_where_filer_equals_subject':sum(r['identity_error_filer_equals_subject'] for r in resolved),'filings_by_f80_filer_but_subject_outside_f80':len(wrong),'download_errors':len(errors),'submission_errors':len(sub_errors),'knowledge_rule':'filing_date is the PIT KnowledgeDate; subject issuer identity is parsed from the filing SUBJECT COMPANY block, never inferred from the submitting filer CIK.','next_gate':'historical active-universe membership/crosswalk; no alpha test authorized','audit_timestamp_utc':datetime.now(timezone.utc).isoformat(),'errors_sample':(sub_errors+errors)[:25]}
    with open(os.path.join(OUT,'phase49_summary.json'),'w',encoding='utf-8') as f:json.dump(payload,f,indent=2)
    print(json.dumps(payload,indent=2))

if __name__=='__main__':main()

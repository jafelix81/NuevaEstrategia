import ast, csv, gzip, json, os, re, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime
from urllib.request import Request, urlopen
from urllib.error import HTTPError

BASE_SOURCE='Nueva_Estrategia_Fase0_Descubrimiento.py'
SEC_TICKERS='https://www.sec.gov/files/company_tickers.json'
SUBMISSIONS='https://data.sec.gov/submissions/CIK{}.json'
ARCHIVE='https://www.sec.gov/Archives/edgar/data'
OUT='phase48_sec_13dg_source_regime_audit'
HEADERS={'User-Agent':'NuevaEstrategia research research@example.com','Accept-Encoding':'gzip, deflate'}
FORMS={'SC 13D','SC 13G','SC 13D/A','SC 13G/A','SCHEDULE 13D','SCHEDULE 13G','SCHEDULE 13D/A','SCHEDULE 13G/A'}
CUTOFF=date(2024,12,18)
START=date(2020,10,1); END=date(2026,9,30)
_last=0.0

def get(url,timeout=60,retries=5):
    global _last
    err=None
    for a in range(retries):
        wait=.25-(time.monotonic()-_last)
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
            time.sleep(min(10,2**a))
        except Exception as e:
            err=e; time.sleep(min(10,2**a))
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

def pd(x):
    try:return datetime.strptime(str(x)[:10],'%Y-%m-%d').date()
    except:return None

def norm(x): return ' '.join(str(x).upper().replace('SCHEDULE ','SC ').split())

def clean(s): return re.sub(r'\s+',' ',re.sub(r'<[^>]+>',' ',s.decode('utf-8','ignore') if isinstance(s,bytes) else str(s))).strip()

def parse_doc(raw):
    raw_text=raw.decode('utf-8','ignore') if isinstance(raw,bytes) else str(raw)
    text=clean(raw_text)
    xml=('<?xml' in raw_text[:5000] or '<edgarSubmission' in raw_text[:20000] or '<formData' in raw_text[:20000] or '<ownershipDocument' in raw_text[:20000])
    cusip=bool(re.search(r'<issuerCusip>\s*[^<\s]+\s*</issuerCusip>',raw_text,re.I)) or bool(re.search(r'CUSIP(?:\s+NO\.?|\s*NUMBER)?\s*[:#]?\s*[A-Z0-9]{6,12}',text,re.I))
    issuer_cik=bool(re.search(r'<issuerCik>\s*[^<\s]+\s*</issuerCik>',raw_text,re.I)) or bool(re.search(r'CENTRAL INDEX KEY\s*[:#]?\s*\d{7,10}',text,re.I))
    event=bool(re.search(r'<eventDateRequiresFilingThisStatement>\s*[^<]+\s*</eventDateRequiresFilingThisStatement>',raw_text,re.I)) or bool(re.search(r'DATE OF EVENT WHICH REQUIRES FILING',text,re.I))
    owner=bool(re.search(r'<reportingPersonName>\s*.*?</reportingPersonName>',raw_text,re.I|re.S)) or bool(re.search(r'NAME OF REPORTING PERSON',text,re.I))
    pct=bool(re.search(r'<percentOfClass>\s*[^<]+\s*</percentOfClass>',raw_text,re.I)) or bool(re.search(r'PERCENT OF CLASS',text,re.I))
    return {'xml_detected':xml,'cusip':cusip,'issuer_cik':issuer_cik,'event_date':event,'reporting_person':owner,'ownership_pct':pct}

def main():
    os.makedirs(OUT,exist_ok=True)
    frozen=universe()
    sec=json.loads(get(SEC_TICKERS).decode())
    sec_map={str(v.get('ticker','')).upper():str(v.get('cik_str','')).zfill(10) for v in sec.values() if v.get('ticker')}
    targets={t:sec_map.get(t) for t in frozen}
    unresolved=[t for t,c in targets.items() if not c]
    filings=[]
    errors=[]
    def one(t,c):
        data=json.loads(get(SUBMISSIONS.format(c)).decode()); rows=[]
        recent=data.get('filings',{}).get('recent',{})
        for i,form in enumerate(recent.get('form',[])):
            f=norm(form); d=pd(recent.get('filingDate',[''])[i])
            if f in FORMS and d and START<=d<=END:
                rows.append({'ticker':t,'cik':c,'form':f,'filing_date':d.isoformat(),'accession':recent['accessionNumber'][i],'doc':recent.get('primaryDocument',[''])[i]})
        return rows
    with ThreadPoolExecutor(max_workers=8) as ex:
        fs={ex.submit(one,t,c):t for t,c in targets.items() if c}
        for f in as_completed(fs):
            try: filings.extend(f.result())
            except Exception as e: errors.append({'ticker':fs[f],'error':str(e)})
    filings.sort(key=lambda r:r['filing_date'])
    pre=[r for r in filings if pd(r['filing_date'])<CUTOFF]
    post=[r for r in filings if pd(r['filing_date'])>=CUTOFF]
    def sample(rows,n=25):
        if not rows:return []
        idx=[round(i*(len(rows)-1)/(n-1)) for i in range(min(n,len(rows)))] if len(rows)>1 else [0]
        return [rows[i] for i in idx]
    samples=sample(pre)+sample(post)
    results=[]
    for r in samples:
        url=f"{ARCHIVE}/{int(r['cik'])}/{r['accession'].replace('-','')}/{r['doc']}"
        try:
            p=parse_doc(get(url)); results.append({**r,'regime':'pre_structured' if pd(r['filing_date'])<CUTOFF else 'structured_expected','url':url,**p})
        except Exception as e:
            results.append({**r,'regime':'pre_structured' if pd(r['filing_date'])<CUTOFF else 'structured_expected','url':url,'error':str(e)})
    def agg(rows):
        return {'sample':len(rows),'download_ok':sum('error' not in r for r in rows),'xml_detected':sum(r.get('xml_detected',False) for r in rows),'cusip':sum(r.get('cusip',False) for r in rows),'issuer_cik':sum(r.get('issuer_cik',False) for r in rows),'event_date':sum(r.get('event_date',False) for r in rows),'reporting_person':sum(r.get('reporting_person',False) for r in rows),'ownership_pct':sum(r.get('ownership_pct',False) for r in rows)}
    summary={'phase':'48','status':'COMPLETE','frozen_universe':len(frozen),'unresolved_current_cik':len(unresolved),'filings_found':len(filings),'pre_cutoff_filings':len(pre),'post_cutoff_filings':len(post),'cutoff':'2024-12-18','pre_regime':agg([r for r in results if r['regime']=='pre_structured']),'post_regime':agg([r for r in results if r['regime']=='structured_expected']),'submission_errors':len(errors),'knowledge_rule':'filing_date is the PIT knowledge date; event/report dates are not substituted for availability.','interpretation':'source-regime feasibility only; no alpha authorization and no historical-universe membership inference.'}
    with open(os.path.join(OUT,'summary.json'),'w') as f: json.dump(summary,f,indent=2)
    with open(os.path.join(OUT,'sample_results.csv'),'w',newline='') as f:
        fields=sorted({k for r in results for k in r}); w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(results)
    print(json.dumps(summary,indent=2))

if __name__=='__main__': main()

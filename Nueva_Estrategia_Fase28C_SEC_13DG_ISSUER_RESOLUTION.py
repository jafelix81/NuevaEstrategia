import ast, csv, gzip, json, os, re, time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from urllib.error import HTTPError
from urllib.request import Request, urlopen

BASE_SOURCE='Nueva_Estrategia_Fase0_Descubrimiento.py'
OUT='nueva_estrategia_phase28c_sec_13dg_issuer_resolution'
SEC_TICKERS='https://www.sec.gov/files/company_tickers.json'
SUB_URL='https://data.sec.gov/submissions/CIK{cik}.json'
HEADERS={'User-Agent':'NuevaEstrategia research research@example.com','Accept-Encoding':'gzip, deflate'}
TARGET_FORMS={'SC 13D','SC 13G','SC 13D/A','SC 13G/A'}
PERIODS=[('2020Q4','2020-10-01','2020-12-31'),('2021Q4','2021-10-01','2021-12-31'),('2022Q4','2022-10-01','2022-12-31'),('2023Q4','2023-10-01','2023-12-31'),('2024Q4','2024-10-01','2024-12-31'),('2025Q4','2025-10-01','2025-12-31')]
SEC_WORKERS=2
MIN_REQUEST_INTERVAL=0.20
_last_request=0.0

def throttle():
    global _last_request
    wait=MIN_REQUEST_INTERVAL-(time.monotonic()-_last_request)
    if wait>0: time.sleep(wait)
    _last_request=time.monotonic()

def get(url,timeout=60,retries=6):
    for attempt in range(retries):
        throttle()
        try:
            req=Request(url,headers=HEADERS)
            with urlopen(req,timeout=timeout) as r:
                raw=r.read(); enc=(r.headers.get('Content-Encoding') or '').lower()
                if enc=='gzip' or raw[:2]==b'\x1f\x8b': raw=gzip.decompress(raw)
                return raw
        except HTTPError as e:
            if e.code not in (429,500,502,503,504): raise
            ra=e.headers.get('Retry-After')
            delay=float(ra) if ra and ra.replace('.','',1).isdigit() else min(30.0,2.0**attempt)
            time.sleep(delay)
    raise RuntimeError(f'HTTP retry exhaustion: {url}')

def get_json(url): return json.loads(get(url).decode('utf-8'))

def universe():
    tree=ast.parse(open(BASE_SOURCE,encoding='utf-8').read())
    for n in tree.body:
        if isinstance(n,ast.Assign):
            for t in n.targets:
                if isinstance(t,ast.Name) and t.id=='DEFAULT_UNIVERSE':
                    u=sorted(set(str(x).strip().upper() for x in ast.literal_eval(n.value)))
                    if len(u)!=335: raise RuntimeError(f'Expected frozen 335 universe, got {len(u)}')
                    return u
    raise RuntimeError('DEFAULT_UNIVERSE not found')

def in_period(d): return any(start<=d<=end for _,start,end in PERIODS)

def extract_target_filings(ticker,cik,sub):
    rows=[]; recent=sub.get('filings',{}).get('recent',{})
    for i,form in enumerate(recent.get('form',[])):
        if form not in TARGET_FORMS: continue
        d=recent.get('filingDate',[''])[i]
        if in_period(d): rows.append({'filer_ticker':ticker,'filer_cik':cik,'form':form,'filing_date':d,'accession':recent.get('accessionNumber',[''])[i],'primary':recent.get('primaryDocument',[''])[i]})
    for f in sub.get('filings',{}).get('files',[]):
        name=f.get('name','')
        if not name.endswith('.json'): continue
        try: old=get_json('https://data.sec.gov/submissions/'+name)
        except Exception: continue
        for i,form in enumerate(old.get('form',[])):
            if form not in TARGET_FORMS: continue
            d=old.get('filingDate',[''])[i]
            if in_period(d): rows.append({'filer_ticker':ticker,'filer_cik':cik,'form':form,'filing_date':d,'accession':old.get('accessionNumber',[''])[i],'primary':old.get('primaryDocument',[''])[i]})
    return rows

def fetch_submission(item):
    t,cik=item
    try:
        sub=get_json(SUB_URL.format(cik=cik))
        return t,cik,sub,None
    except Exception as e:return t,cik,None,{'filer_ticker':t,'error':str(e)}

def build_accession_issuer_crosswalk(frozen,ticker_to_cik):
    """PIT-safe issuer diagnostic: for each frozen-universe CIK, inspect its SEC submission history.
    A target 13D/13G accession that appears in an issuer's own submission history establishes
    the issuer CIK without fetching the archive URL. This avoids confusing FILED BY with SUBJECT.
    """
    crosswalk={}; errors=[]; issuer_submission_counts=Counter()
    with ThreadPoolExecutor(max_workers=SEC_WORKERS) as ex:
        futs=[ex.submit(fetch_submission,x) for x in sorted(ticker_to_cik.items())]
        for fut in as_completed(futs):
            ticker,cik,sub,err=fut.result()
            if err: errors.append(err); continue
            issuer_submission_counts[ticker]+=1
            recent=sub.get('filings',{}).get('recent',{})
            for i,form in enumerate(recent.get('form',[])):
                if form not in TARGET_FORMS: continue
                d=recent.get('filingDate',[''])[i]
                if not in_period(d): continue
                acc=recent.get('accessionNumber',[''])[i]
                if acc: crosswalk[acc]={'issuer_ticker':ticker,'issuer_cik':cik,'issuer_source':'universe_submission_history'}
            for f in sub.get('filings',{}).get('files',[]):
                name=f.get('name','')
                if not name.endswith('.json'): continue
                try: old=get_json('https://data.sec.gov/submissions/'+name)
                except Exception: continue
                for i,form in enumerate(old.get('form',[])):
                    if form not in TARGET_FORMS: continue
                    d=old.get('filingDate',[''])[i]
                    if not in_period(d): continue
                    acc=old.get('accessionNumber',[''])[i]
                    if acc: crosswalk[acc]={'issuer_ticker':ticker,'issuer_cik':cik,'issuer_source':'universe_submission_history'}
    return crosswalk,errors

def main():
    os.makedirs(OUT,exist_ok=True)
    frozen=universe(); company=get_json(SEC_TICKERS)
    cik_to_ticker={str(v.get('cik_str','')).zfill(10):str(v.get('ticker','')).strip().upper() for v in company.values() if v.get('ticker')}
    ticker_to_cik={t:cik for cik,t in cik_to_ticker.items() if t in frozen}

    filings=[]; fetch_errors=[]
    # First collect filings from the frozen universe as filing-person submissions.
    with ThreadPoolExecutor(max_workers=SEC_WORKERS) as ex:
        futs=[ex.submit(fetch_submission,x) for x in sorted(ticker_to_cik.items())]
        for fut in as_completed(futs):
            ticker,cik,sub,err=fut.result()
            if err: fetch_errors.append(err); continue
            filings.extend(extract_target_filings(ticker,cik,sub))
    filings=sorted({r['accession']:r for r in filings if r.get('accession')}.values(),key=lambda r:(r['filing_date'],r['filer_ticker'],r['accession']))

    # Resolve issuer from the SEC's own submission history, keyed by accession.
    accession_crosswalk,crosswalk_errors=build_accession_issuer_crosswalk(frozen,ticker_to_cik)
    mapped=[]; unmapped=[]
    for r in filings:
        x=accession_crosswalk.get(r['accession'])
        row={**r,**(x or {'issuer_ticker':None,'issuer_cik':None,'issuer_source':None}),
             'issuer_in_frozen_universe':bool(x and x.get('issuer_ticker') in frozen)}
        (mapped if row['issuer_in_frozen_universe'] else unmapped).append(row)

    period=defaultdict(list)
    for r in filings:
        p=next((x[0] for x in PERIODS if x[1]<=r['filing_date']<=x[2]),None)
        if p: period[p].append(r)
    summary=[]
    for p,_,_ in PERIODS:
        xs=period[p]; mapped_p=[r for r in xs if accession_crosswalk.get(r['accession'],{}).get('issuer_ticker') in frozen]
        summary.append({'period':p,'filings':len(xs),'issuer_mapped':len(mapped_p),'issuer_unmapped':len(xs)-len(mapped_p),'unique_filers':len({r['filer_cik'] for r in xs}),'unique_issuers_mapped':len({accession_crosswalk[r['accession']]['issuer_ticker'] for r in xs if r['accession'] in accession_crosswalk and accession_crosswalk[r['accession']]['issuer_ticker'] in frozen})})

    top_filer=Counter(r['filer_ticker'] for r in filings).most_common(25)
    top_issuer=Counter(r['issuer_ticker'] for r in mapped).most_common(25)
    payload={'phase':'28C','status':'COMPLETE','hypothesis':'SEC 13D/13G filings must be mapped by SUBJECT COMPANY issuer, not filing-person CIK/ticker.','frozen_universe_size':335,'frozen_universe_mapped_ciks':len(ticker_to_cik),'filings_collected':len(filings),'issuer_submission_crosswalk_entries':len(accession_crosswalk),'issuer_mapped_filings':len(mapped),'issuer_unmapped_filings':len(unmapped),'issuer_mapping_rate':len(mapped)/len(filings) if filings else None,'period_summary':summary,'top_filer_tickers':top_filer,'top_mapped_issuer_tickers':top_issuer,'sample_mapped':mapped[:50],'sample_unmapped':unmapped[:25],'fetch_errors':fetch_errors,'crosswalk_errors':crosswalk_errors,'knowledge_rule':'filingDate is the earliest public-availability timestamp; accession-to-issuer mapping is a diagnostic only and does not estimate returns.','audit_timestamp_utc':datetime.now(timezone.utc).isoformat()}
    with open(os.path.join(OUT,'phase28c_sec_13dg_issuer_resolution.json'),'w',encoding='utf-8') as f: json.dump(payload,f,indent=2)
    fields=['filing_date','form','accession','filer_ticker','filer_cik','issuer_ticker','issuer_cik','issuer_source','issuer_in_frozen_universe']
    with open(os.path.join(OUT,'phase28c_filing_mapping.csv'),'w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows({k:r.get(k) for k in fields} for r in filings)
    print(json.dumps({'phase':'28C','status':'COMPLETE','filings':len(filings),'crosswalk_entries':len(accession_crosswalk),'issuer_mapped':len(mapped),'issuer_unmapped':len(unmapped),'mapping_rate':len(mapped)/len(filings) if filings else None,'period_summary':summary},indent=2))

if __name__=='__main__': main()

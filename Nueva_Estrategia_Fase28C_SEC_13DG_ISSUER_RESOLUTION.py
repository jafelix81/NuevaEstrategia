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
ARCHIVE_BASE='https://www.sec.gov/Archives/edgar/data'
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

def extract_filings(ticker,cik,sub):
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
    try:return extract_filings(t,cik,get_json(SUB_URL.format(cik=cik))),None
    except Exception as e:return [],{'filer_ticker':t,'error':str(e)}

def parse_header(r):
    acc=r['accession'].replace('-','')
    candidates=[
        f'{ARCHIVE_BASE}/{int(r["filer_cik"])}/{acc}/{acc}-index-headers.html',
        f'{ARCHIVE_BASE}/{int(r["filer_cik"])}/{acc}/{acc}.txt',
    ]
    errors=[]
    for url in candidates:
        try:
            raw=get(url).decode('utf-8',errors='ignore')
            sec=raw.split('</SEC-HEADER>',1)[0]
            m=re.search(r'SUBJECT COMPANY:\s*(.*?)(?=\n\s*FILED BY:|\Z)',sec,re.I|re.S)
            block=m.group(1) if m else ''
            km=re.search(r'CENTRAL INDEX KEY:\s*([0-9]+)',block,re.I)
            nm=re.search(r'COMPANY CONFORMED NAME:\s*(.*?)\s*(?:CENTRAL INDEX KEY:|STANDARD INDUSTRIAL CLASSIFICATION:)',block,re.I|re.S)
            issuer_cik=km.group(1).zfill(10) if km else None
            issuer_name=re.sub(r'\s+',' ',nm.group(1)).strip() if nm else None
            if issuer_cik:
                return {**r,'issuer_cik':issuer_cik,'issuer_name':issuer_name,'header_url':url},None
            errors.append(f'no issuer CIK parsed from {url}')
        except Exception as e:
            errors.append(f'{url}: {e}')
    return None,{**r,'error':' | '.join(errors)}

def main():
    os.makedirs(OUT,exist_ok=True)
    frozen=universe(); company=get_json(SEC_TICKERS)
    cik_to_ticker={str(v.get('cik_str','')).zfill(10):str(v.get('ticker','')).strip().upper() for v in company.values() if v.get('ticker')}
    ticker_to_cik={t:cik for cik,t in cik_to_ticker.items() if t in frozen}
    filings=[]; fetch_errors=[]
    with ThreadPoolExecutor(max_workers=SEC_WORKERS) as ex:
        futs=[ex.submit(fetch_submission,x) for x in sorted(ticker_to_cik.items())]
        for fut in as_completed(futs):
            rows,err=fut.result(); filings.extend(rows)
            if err: fetch_errors.append(err)
    filings=sorted({r['accession']:r for r in filings if r.get('accession')}.values(),key=lambda r:(r['filing_date'],r['filer_ticker'],r['accession']))

    parsed=[]; parse_errors=[]
    with ThreadPoolExecutor(max_workers=SEC_WORKERS) as ex:
        futs=[ex.submit(parse_header,r) for r in filings]
        for fut in as_completed(futs):
            row,err=fut.result()
            if row: parsed.append(row)
            if err: parse_errors.append(err)
    parsed.sort(key=lambda r:(r['filing_date'],r['filer_ticker'],r['accession']))

    mapped=[]; unmapped=[]
    for r in parsed:
        issuer_ticker=cik_to_ticker.get(r.get('issuer_cik'))
        row={**r,'issuer_ticker':issuer_ticker,'issuer_in_frozen_universe':bool(issuer_ticker in frozen)}
        (mapped if issuer_ticker in frozen else unmapped).append(row)

    period=defaultdict(list)
    for r in parsed:
        p=next((x[0] for x in PERIODS if x[1]<=r['filing_date']<=x[2]),None)
        if p: period[p].append(r)
    summary=[]
    for p,_,_ in PERIODS:
        xs=period[p]; mapped_p=[r for r in xs if r.get('issuer_ticker') in frozen]
        summary.append({'period':p,'filings':len(xs),'issuer_mapped':len(mapped_p),'issuer_unmapped':len(xs)-len(mapped_p),'unique_filers':len({r['filer_cik'] for r in xs}),'unique_issuers_mapped':len({r['issuer_ticker'] for r in mapped_p})})

    top_filer=Counter(r['filer_ticker'] for r in parsed).most_common(25)
    top_issuer=Counter(r['issuer_ticker'] for r in mapped).most_common(25)
    payload={'phase':'28C','status':'COMPLETE','hypothesis':'SEC 13D/13G filings must be mapped by SUBJECT COMPANY issuer, not filing-person CIK/ticker.','frozen_universe_size':335,'frozen_universe_mapped_ciks':len(ticker_to_cik),'filings_collected':len(filings),'parsed_headers':len(parsed),'header_parse_errors':len(parse_errors),'issuer_mapped_filings':len(mapped),'issuer_unmapped_filings':len(unmapped),'issuer_mapping_rate':len(mapped)/len(parsed) if parsed else None,'period_summary':summary,'top_filer_tickers':top_filer,'top_mapped_issuer_tickers':top_issuer,'sample_mapped':mapped[:50],'sample_unmapped':unmapped[:25],'fetch_errors':fetch_errors,'parse_error_samples':parse_errors[:25],'knowledge_rule':'filingDate is the earliest public-availability timestamp; this phase is a mapping audit only and does not estimate returns.','audit_timestamp_utc':datetime.now(timezone.utc).isoformat()}
    with open(os.path.join(OUT,'phase28c_sec_13dg_issuer_resolution.json'),'w',encoding='utf-8') as f: json.dump(payload,f,indent=2)
    if parsed:
        fields=['filing_date','form','accession','filer_ticker','filer_cik','issuer_ticker','issuer_cik','issuer_name','issuer_in_frozen_universe','header_url']
        with open(os.path.join(OUT,'phase28c_filing_mapping.csv'),'w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows({k:r.get(k) for k in fields} for r in parsed)
    print(json.dumps({'phase':'28C','status':'COMPLETE','filings':len(filings),'parsed_headers':len(parsed),'issuer_mapped':len(mapped),'issuer_unmapped':len(unmapped),'mapping_rate':len(mapped)/len(parsed) if parsed else None,'period_summary':summary,'parse_error_samples':parse_errors[:5]},indent=2))

if __name__=='__main__': main()

import ast, csv, gzip, json, os, re, time
from collections import defaultdict, Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from urllib.error import HTTPError
from urllib.request import Request, urlopen

BASE_SOURCE='Nueva_Estrategia_Fase0_Descubrimiento.py'
OUT='nueva_estrategia_phase28c2_sec_13dg_quarterly_index_census'
SEC_TICKERS='https://www.sec.gov/files/company_tickers.json'
ARCHIVE_BASE='https://www.sec.gov/Archives/edgar/data'
INDEX_BASE='https://www.sec.gov/Archives/edgar/full-index'
HEADERS={'User-Agent':'NuevaEstrategia research research@example.com','Accept-Encoding':'gzip, deflate'}
TARGET_FORMS={'SC 13D','SC 13G','SC 13D/A','SC 13G/A'}
PERIODS=[('2020Q4','2020','QTR4'),('2021Q4','2021','QTR4'),('2022Q4','2022','QTR4'),('2023Q4','2023','QTR4'),('2024Q4','2024','QTR4'),('2025Q4','2025','QTR4')]
SEC_WORKERS=2
MIN_REQUEST_INTERVAL=0.35
_last_request=0.0

def throttle():
    global _last_request
    wait=MIN_REQUEST_INTERVAL-(time.monotonic()-_last_request)
    if wait>0: time.sleep(wait)
    _last_request=time.monotonic()

def get(url,timeout=60,retries=7):
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
            ra=e.headers.get('Retry-After'); delay=float(ra) if ra and re.fullmatch(r'\d+(?:\.\d+)?',ra) else min(45.0,2.0**attempt)
            time.sleep(delay)
    raise RuntimeError(f'HTTP retry exhaustion: {url}')

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

def parse_idx(raw,year,qtr):
    text=raw.decode('latin-1',errors='replace')
    rows=[]; started=False
    for line in text.splitlines():
        if not started:
            if line.startswith('CIK|Company Name|Form Type|Date Filed|File Name'):
                started=True
            continue
        parts=line.split('|')
        if len(parts)!=5: continue
        cik,name,form,date_filed,file_name=parts
        if form not in TARGET_FORMS: continue
        acc=re.search(r'(\d{10}-\d{2}-\d{6})',file_name)
        if not acc: continue
        rows.append({'period':f'{year}Q4','year':year,'filer_cik':cik.zfill(10),'filer_name':name.strip(),'form':form,'filing_date':date_filed,'file_name':file_name,'accession':acc.group(1)})
    return rows

def main():
    os.makedirs(OUT,exist_ok=True)
    frozen=universe(); company=json.loads(get(SEC_TICKERS).decode('utf-8'))
    cik_to_ticker={str(v.get('cik_str','')).zfill(10):str(v.get('ticker','')).strip().upper() for v in company.values() if v.get('ticker')}
    frozen_ciks={cik for cik,t in cik_to_ticker.items() if t in frozen}
    ticker_by_cik={cik:t for cik,t in cik_to_ticker.items() if t in frozen}

    census=[]; index_stats=[]; errors=[]
    for period,year,qtr in PERIODS:
        url=f'{INDEX_BASE}/{year}/{qtr}/form.idx'
        try:
            rows=parse_idx(get(url),year,qtr)
            matched=[r for r in rows if r['filer_cik'] in frozen_ciks]
            census.extend(matched)
            index_stats.append({'period':period,'all_target_filings_in_SEC_index':len(rows),'frozen_universe_filer_filings':len(matched),'index_url':url})
        except Exception as e:
            errors.append({'period':period,'url':url,'error':str(e)})

    # Deduplicate accessions and resolve issuer from the actual SEC submission header.
    unique={r['accession']:r for r in census}
    filings=sorted(unique.values(),key=lambda r:(r['filing_date'],r['accession']))
    def resolve(r):
        try:
            acc=r['accession']; acc_dash=acc; acc_compact=acc.replace('-','')
            url=f'{ARCHIVE_BASE}/{int(r["filer_cik"])}/{acc_compact}/{acc_dash}.txt'
            raw=get(url).decode('utf-8',errors='ignore'); sec=raw.split('</SEC-HEADER>',1)[0]
            m=re.search(r'SUBJECT COMPANY:\s*(.*?)(?=\nFILED BY:|\r?\nFILED BY:|\Z)',sec,re.I|re.S)
            if not m: raise RuntimeError('missing SUBJECT COMPANY block')
            block=m.group(1)
            km=re.search(r'CENTRAL INDEX KEY:\s*([0-9]+)',block,re.I)
            nm=re.search(r'COMPANY CONFORMED NAME:\s*(.*?)(?:\r?\n|CENTRAL INDEX KEY:)',block,re.I|re.S)
            issuer_cik=km.group(1).zfill(10) if km else None
            if not issuer_cik: raise RuntimeError('missing issuer CIK')
            issuer_ticker=ticker_by_cik.get(issuer_cik)
            return {**r,'filer_ticker':ticker_by_cik.get(r['filer_cik']),'issuer_cik':issuer_cik,'issuer_name':re.sub(r'\s+',' ',nm.group(1)).strip() if nm else None,'issuer_ticker':issuer_ticker,'issuer_in_frozen_universe':bool(issuer_ticker)},None
        except Exception as e: return None,{**r,'error':str(e)}

    resolved=[]; parse_errors=[]
    with ThreadPoolExecutor(max_workers=SEC_WORKERS) as ex:
        futs=[ex.submit(resolve,r) for r in filings]
        for fut in as_completed(futs):
            row,err=fut.result()
            if row: resolved.append(row)
            if err: parse_errors.append(err)
    resolved.sort(key=lambda r:(r['filing_date'],r['accession']))

    period=defaultdict(list)
    for r in resolved: period[r['period']].append(r)
    summary=[]
    for p,_,_ in PERIODS:
        xs=period[p]; mapped=[r for r in xs if r['issuer_in_frozen_universe']]
        summary.append({'period':p,'filings_from_frozen_filers':len(xs),'issuer_mapped':len(mapped),'issuer_unmapped':len(xs)-len(mapped),'mapping_rate':len(mapped)/len(xs) if xs else None,'unique_issuers_mapped':len({r['issuer_ticker'] for r in mapped})})

    payload={'phase':'28C2','status':'COMPLETE','purpose':'Comprehensive Q4 SEC EDGAR form-index census to remove the submissions.json historical-coverage gap before any 13D/13G OOS test.','frozen_universe_size':335,'frozen_universe_mapped_ciks':len(frozen_ciks),'index_stats':index_stats,'period_summary':summary,'filings_after_filer_filter':len(filings),'headers_resolved':len(resolved),'header_parse_errors':len(parse_errors),'knowledge_rule':'filingDate is the earliest public-availability date; issuer is taken only from SUBJECT COMPANY in the SEC submission header; this phase does not estimate returns.','errors':errors,'parse_error_samples':parse_errors[:25],'audit_timestamp_utc':datetime.now(timezone.utc).isoformat()}
    with open(os.path.join(OUT,'phase28c2_sec_13dg_quarterly_index_census.json'),'w',encoding='utf-8') as f: json.dump(payload,f,indent=2)
    fields=['period','filing_date','form','accession','filer_ticker','filer_cik','filer_name','issuer_ticker','issuer_cik','issuer_name','issuer_in_frozen_universe']
    with open(os.path.join(OUT,'phase28c2_filing_census.csv'),'w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows({k:r.get(k) for k in fields} for r in resolved)
    print(json.dumps({'phase':'28C2','status':'COMPLETE','filings':len(filings),'headers_resolved':len(resolved),'parse_errors':len(parse_errors),'period_summary':summary,'index_errors':errors},indent=2))

if __name__=='__main__': main()

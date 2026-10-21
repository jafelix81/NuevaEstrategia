import ast, calendar, csv, gzip, json, os, re, time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from urllib.error import HTTPError
from urllib.request import Request, urlopen

BASE_SOURCE='Nueva_Estrategia_Fase0_Descubrimiento.py'
OUT='nueva_estrategia_phase28c2_sec_13dg_quarterly_index_census'
SEC_TICKERS='https://www.sec.gov/files/company_tickers.json'
ARCHIVE_BASE='https://www.sec.gov/Archives/edgar/data'
INDEX_BASE='https://www.sec.gov/Archives/edgar/full-index'
DAILY_BASE='https://www.sec.gov/Archives/edgar/daily-index'
HEADERS={'User-Agent':'NuevaEstrategia research research@example.com','Accept-Encoding':'gzip, deflate'}
TARGET_FORMS={'SC 13D','SC 13G','SC 13D/A','SC 13G/A','SCHEDULE 13D','SCHEDULE 13G','SCHEDULE 13D/A','SCHEDULE 13G/A'}
PERIODS=[('2020Q4','2020','QTR4'),('2021Q4','2021','QTR4'),('2022Q4','2022','QTR4'),('2023Q4','2023','QTR4'),('2024Q4','2024','QTR4'),('2025Q4','2025','QTR4')]
SEC_WORKERS=4
MIN_REQUEST_INTERVAL=0.20
_last_request=0.0

def throttle():
    global _last_request
    wait=MIN_REQUEST_INTERVAL-(time.monotonic()-_last_request)
    if wait>0: time.sleep(wait)
    _last_request=time.monotonic()

def get(url,timeout=90,retries=7):
    last=None
    for attempt in range(retries):
        throttle()
        try:
            req=Request(url,headers=HEADERS)
            with urlopen(req,timeout=timeout) as r:
                raw=r.read(); enc=(r.headers.get('Content-Encoding') or '').lower()
                if enc=='gzip' or raw[:2]==b'\x1f\x8b': raw=gzip.decompress(raw)
                return raw
        except HTTPError as e:
            last=e
            if e.code==404: raise
            if e.code not in (429,500,502,503,504): raise
            ra=e.headers.get('Retry-After')
            delay=float(ra) if ra and re.fullmatch(r'\d+(?:\.\d+)?',ra) else min(45.0,2.0**attempt)
            time.sleep(delay)
        except Exception as e:
            last=e
            if attempt==retries-1: break
            time.sleep(min(20.0,2.0**attempt))
    raise RuntimeError(f'HTTP retry exhaustion: {url}: {last}')

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

def normalize_form(form):
    f=re.sub(r'\s+',' ',str(form).strip().upper())
    f=f.replace('SCHEDULE ','SC ')
    return f

def parse_idx(raw,year):
    text=raw.decode('latin-1',errors='replace')
    rows=[]
    for line in text.splitlines():
        if '|' not in line: continue
        parts=line.split('|')
        if len(parts)!=5: continue
        cik,name,form,date_filed,file_name=[p.strip() for p in parts]
        form_norm=normalize_form(form)
        if not cik.isdigit() or form_norm not in {'SC 13D','SC 13G','SC 13D/A','SC 13G/A'}: continue
        if not re.fullmatch(r'\d{8}',date_filed): continue
        acc=re.search(r'(\d{10}-\d{2}-\d{6})',file_name)
        if not acc: continue
        rows.append({'period':f'{year}Q4','year':year,'filer_cik':cik.zfill(10),'filer_name':name,'form':form,'filing_date':date_filed,'file_name':file_name,'accession':acc.group(1)})
    return rows

def fetch_index(year,qtr):
    diagnostics=[]
    for url in [f'{INDEX_BASE}/{year}/{qtr}/form.idx',f'{INDEX_BASE}/{year}/{qtr}/master.idx']:
        try:
            raw=get(url)
            rows=parse_idx(raw,year)
            diagnostics.append({'url':url,'bytes':len(raw),'target_rows':len(rows)})
            if rows: return rows,diagnostics
        except Exception as e:
            diagnostics.append({'url':url,'error':str(e)})

    dates=[]
    for month in range(10,13):
        for day in range(1,calendar.monthrange(int(year),month)[1]+1):
            dates.append(f'{year}{month:02d}{day:02d}')
    def one(ds):
        url=f'{DAILY_BASE}/{year}/{qtr}/master.{ds}.idx'
        try:
            raw=get(url,timeout=45,retries=3)
            return parse_idx(raw,year),{'url':url,'bytes':len(raw)}
        except HTTPError as e:
            if e.code==404: return [],{'url':url,'status':404}
            return [],{'url':url,'error':str(e)}
        except Exception as e: return [],{'url':url,'error':str(e)}
    rows=[]; daily_diag=[]
    with ThreadPoolExecutor(max_workers=4) as ex:
        for rs,diag in ex.map(one,dates):
            rows.extend(rs); daily_diag.append(diag)
    diagnostics.append({'fallback':'daily-index','days_attempted':len(dates),'days_with_rows':sum(1 for d in daily_diag if d.get('bytes')),'target_rows':len(rows),'errors':sum(1 for d in daily_diag if d.get('error'))})
    return rows,diagnostics

def resolve_header(r,ticker_by_cik):
    try:
        acc=r['accession']; compact=acc.replace('-','')
        url=f'{ARCHIVE_BASE}/{int(r["filer_cik"])}/{compact}/{acc}.txt'
        raw=get(url).decode('utf-8',errors='ignore')
        sec=raw.split('</SEC-HEADER>',1)[0]
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

def main():
    os.makedirs(OUT,exist_ok=True)
    frozen=universe(); company=json.loads(get(SEC_TICKERS).decode('utf-8'))
    cik_to_ticker={str(v.get('cik_str','')).zfill(10):str(v.get('ticker','')).strip().upper() for v in company.values() if v.get('ticker')}
    frozen_ciks={cik for cik,t in cik_to_ticker.items() if t in frozen}
    ticker_by_cik={cik:t for cik,t in cik_to_ticker.items() if t in frozen}
    all_rows=[]; index_stats=[]; errors=[]
    for period,year,qtr in PERIODS:
        try:
            rows,diag=fetch_index(year,qtr); all_rows.extend(rows)
            index_stats.append({'period':period,'all_target_filings_in_SEC_index':len(rows),'index_diagnostics':diag})
        except Exception as e: errors.append({'period':period,'error':str(e)})
    unique={r['accession']:r for r in all_rows}
    filings=sorted(unique.values(),key=lambda r:(r['filing_date'],r['accession']))
    resolved=[]; parse_errors=[]
    with ThreadPoolExecutor(max_workers=SEC_WORKERS) as ex:
        futs=[ex.submit(resolve_header,r,ticker_by_cik) for r in filings]
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
        idx_n=next((x['all_target_filings_in_SEC_index'] for x in index_stats if x['period']==p),0)
        summary.append({'period':p,'all_target_filings':idx_n,'headers_resolved':len(xs),'issuer_mapped':len(mapped),'issuer_unmapped':len(xs)-len(mapped),'issuer_mapping_rate':len(mapped)/len(xs) if xs else None,'unique_issuers_mapped':len({r['issuer_ticker'] for r in mapped})})
    payload={'phase':'28C2','status':'COMPLETE','purpose':'Issuer-first historical census of Q4 13D/13G filings; SEC form labels are normalized across legacy SC and current SCHEDULE labels before issuer resolution.','frozen_universe_size':335,'frozen_universe_current_ciks':len(frozen_ciks),'index_stats':index_stats,'period_summary':summary,'target_filings_discovered':len(filings),'headers_resolved':len(resolved),'header_parse_errors':len(parse_errors),'knowledge_rule':'filingDate is the earliest public-availability date; issuer is taken only from SUBJECT COMPANY in the SEC submission header; this phase does not estimate returns.','errors':errors,'parse_error_samples':parse_errors[:25],'audit_timestamp_utc':datetime.now(timezone.utc).isoformat()}
    with open(os.path.join(OUT,'phase28c2_sec_13dg_quarterly_index_census.json'),'w',encoding='utf-8') as f: json.dump(payload,f,indent=2)
    fields=['period','filing_date','form','accession','filer_ticker','filer_cik','filer_name','issuer_ticker','issuer_cik','issuer_name','issuer_in_frozen_universe']
    with open(os.path.join(OUT,'phase28c2_filing_census.csv'),'w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows({k:r.get(k) for k in fields} for r in resolved)
    print(json.dumps({'phase':'28C2','status':'COMPLETE','target_filings':len(filings),'headers_resolved':len(resolved),'parse_errors':len(parse_errors),'period_summary':summary,'index_errors':errors},indent=2))

if __name__=='__main__': main()

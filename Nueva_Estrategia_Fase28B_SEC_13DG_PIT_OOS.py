import ast, csv, gzip, json, os, re, time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from html import unescape
from urllib.error import HTTPError
from urllib.request import Request, urlopen

BASE_SOURCE='Nueva_Estrategia_Fase0_Descubrimiento.py'
OUT='nueva_estrategia_phase28b_sec_13dg_pit_oos'
SEC_TICKERS='https://www.sec.gov/files/company_tickers.json'
SUB_URL='https://data.sec.gov/submissions/CIK{cik}.json'
ARCHIVE_BASE='https://www.sec.gov/Archives/edgar/data'
HEADERS={'User-Agent':'NuevaEstrategia research research@example.com','Accept-Encoding':'gzip, deflate'}
TARGET_FORMS={'SC 13D','SC 13G','SC 13D/A','SC 13G/A'}
PERIODS=[('2020Q4','2020-10-01','2020-12-31'),('2021Q4','2021-10-01','2021-12-31'),('2022Q4','2022-10-01','2022-12-31'),('2023Q4','2023-10-01','2023-12-31'),('2024Q4','2024-10-01','2024-12-31'),('2025Q4','2025-10-01','2025-12-31')]
WINDOW_START=min(p[1] for p in PERIODS)
FORWARD_DAYS=63
SEC_WORKERS=2
PRICE_WORKERS=2
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
            retry_after=e.headers.get('Retry-After')
            delay=float(retry_after) if retry_after and retry_after.replace('.','',1).isdigit() else min(30.0,2.0**attempt)
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

def clean_text(raw):
    s=unescape(raw.decode('utf-8',errors='ignore'))
    s=re.sub(r'<[^>]+>',' ',s)
    return re.sub(r'\s+',' ',s)

def pct_from_text(text):
    pats=[r'Percent of Class Represented by Amount in Row \(11\)\s*([0-9]+(?:\.[0-9]+)?)\s*%',r'Percent of class represented by amount in Row \(11\)\s*([0-9]+(?:\.[0-9]+)?)\s*%',r'Percent of Class\s*([0-9]+(?:\.[0-9]+)?)\s*%',r'Percent of class\s*([0-9]+(?:\.[0-9]+)?)\s*%']
    for p in pats:
        m=re.search(p,text,re.I)
        if m:
            try:return float(m.group(1))
            except ValueError: pass
    return None

def shares_from_text(text):
    pats=[r'Aggregate Amount Beneficially Owned by Each Reporting Person\s*([0-9][0-9,]*)',r'Aggregate Amount Beneficially Owned\s*([0-9][0-9,]*)',r'Number of Shares Beneficially Owned by Each Reporting Person\s*([0-9][0-9,]*)']
    for p in pats:
        m=re.search(p,text,re.I)
        if m:
            try:return int(m.group(1).replace(',',''))
            except ValueError: pass
    return None

def in_period(d): return any(start<=d<=end for _,start,end in PERIODS)

def extract_filings(ticker,cik,sub):
    rows=[]; recent=sub.get('filings',{}).get('recent',{})
    for i,form in enumerate(recent.get('form',[])):
        if form not in TARGET_FORMS: continue
        d=recent.get('filingDate',[''])[i]
        if in_period(d): rows.append({'ticker':ticker,'cik':cik,'form':form,'filing_date':d,'accession':recent.get('accessionNumber',[''])[i],'primary':recent.get('primaryDocument',[''])[i]})
    for f in sub.get('filings',{}).get('files',[]):
        name=f.get('name','')
        if not name.endswith('.json'): continue
        try: old=get_json('https://data.sec.gov/submissions/'+name)
        except Exception: continue
        for i,form in enumerate(old.get('form',[])):
            if form not in TARGET_FORMS: continue
            d=old.get('filingDate',[''])[i]
            if in_period(d): rows.append({'ticker':ticker,'cik':cik,'form':form,'filing_date':d,'accession':old.get('accessionNumber',[''])[i],'primary':old.get('primaryDocument',[''])[i]})
    return rows

def fetch_submission(item):
    ticker,cik=item
    try:return extract_filings(ticker,cik,get_json(SUB_URL.format(cik=cik))),None
    except Exception as e:return [],{'ticker':ticker,'error':str(e)}

def parse_filing(r):
    try:
        acc=r['accession'].replace('-',''); url=f'{ARCHIVE_BASE}/{int(r["cik"])}/{acc}/{r["primary"]}'
        text=clean_text(get(url))
        return {**r,'pct':pct_from_text(text),'shares':shares_from_text(text),'source_url':url},None
    except Exception as e:return None,{**r,'error':str(e)}

def price_one(ticker,start,end):
    import urllib.parse
    try:
        url='https://stooq.com/q/d/l/?'+urllib.parse.urlencode({'s':ticker.lower()+'.us','d1':start.replace('-',''),'d2':end.replace('-',''),'i':'d'})
        raw=get(url).decode('utf-8',errors='ignore').splitlines(); vals={}
        for line in raw[1:]:
            p=line.split(',')
            if len(p)>=5 and p[4] not in ('','N/D'): vals[p[0]]=float(p[4])
        return ticker,vals,None
    except Exception as e:return ticker,{},str(e)

def next_weekday(d):
    x=d+timedelta(days=1)
    while x.weekday()>=5:x+=timedelta(days=1)
    return x

def main():
    os.makedirs(OUT,exist_ok=True); tickers=universe(); company=get_json(SEC_TICKERS)
    by_ticker={}
    for row in company.values():
        t=str(row.get('ticker','')).strip().upper(); cik=str(row.get('cik_str','')).zfill(10)
        if t and t not in by_ticker: by_ticker[t]=cik
    mapped={t:by_ticker[t] for t in tickers if t in by_ticker}

    filings=[]; errors=[]
    with ThreadPoolExecutor(max_workers=SEC_WORKERS) as ex:
        futs=[ex.submit(fetch_submission,x) for x in sorted(mapped.items())]
        for fut in as_completed(futs):
            rows,err=fut.result(); filings.extend(rows)
            if err: errors.append(err)
    filings=sorted({r['accession']:r for r in filings if r.get('accession')}.values(),key=lambda r:(r['filing_date'],r['ticker'],r['accession']))

    parsed=[]; parse_errors=[]
    with ThreadPoolExecutor(max_workers=SEC_WORKERS) as ex:
        futs=[ex.submit(parse_filing,r) for r in filings]
        for fut in as_completed(futs):
            row,err=fut.result()
            if row: parsed.append(row)
            if err: parse_errors.append(err)
    parsed.sort(key=lambda r:(r['filing_date'],r['ticker'],r['accession']))

    events=[]; last_by_ticker={}
    for r in parsed:
        initial=not r['form'].endswith('/A'); prior=last_by_ticker.get(r['ticker'])
        signal=r['pct'] is not None and r['pct']>=5.0 and (initial or prior is None or prior.get('pct')!=r['pct'])
        events.append({**r,'initial_or_amendment':'initial' if initial else 'amendment','signal':bool(signal)})
        last_by_ticker[r['ticker']]={'pct':r['pct'],'shares':r['shares'],'filing_date':r['filing_date']}
    signal_events=[e for e in events if e['signal']]
    if not signal_events: raise RuntimeError('No parsed PIT 5% ownership events; do not infer alpha from empty data.')

    prices={}; price_errors=[]
    with ThreadPoolExecutor(max_workers=PRICE_WORKERS) as ex:
        futs=[ex.submit(price_one,t,WINDOW_START,'2026-03-31') for t in sorted(set(e['ticker'] for e in signal_events))]
        for fut in as_completed(futs):
            t,vals,err=fut.result(); prices[t]=vals
            if err: price_errors.append({'ticker':t,'error':err})

    observations=[]
    for e in signal_events:
        entry=next_weekday(datetime.strptime(e['filing_date'],'%Y-%m-%d').date()); vals=prices.get(e['ticker'],{})
        dates=sorted(d for d in vals if d>=entry.isoformat())
        if len(dates)<FORWARD_DAYS: continue
        ed=dates[FORWARD_DAYS-1]; ep=vals[dates[0]]; xp=vals[ed]
        if ep>0: observations.append({**e,'entry_date':dates[0],'exit_date':ed,'forward_return':xp/ep-1.0})

    by_period=defaultdict(list)
    for o in observations:
        key=next((p[0] for p in PERIODS if p[1]<=o['filing_date']<=p[2]),None)
        if key: by_period[key].append(o['forward_return'])
    summary=[]
    for key,_,_ in PERIODS:
        xs=by_period.get(key,[]); sx=sorted(xs)
        summary.append({'period':key,'n':len(xs),'mean_return':sum(xs)/len(xs) if xs else None,'median_return':sx[len(sx)//2] if xs else None,'hit_rate':sum(x>0 for x in xs)/len(xs) if xs else None})

    payload={'phase':'28B','status':'COMPLETE','hypothesis':'PIT 13D/13G beneficial ownership events with parsed >=5% ownership may predict subsequent returns.','frozen_universe_size':335,'mapped_universe':len(mapped),'periods':PERIODS,'filings_collected':len(filings),'parsed_events':len(parsed),'signal_events':len(signal_events),'observations':len(observations),'parse_errors':len(parse_errors),'fetch_errors':errors,'price_errors':price_errors,'period_summary':summary,'forward_days':FORWARD_DAYS,'knowledge_rule':'filingDate is earliest public availability; signal enters next trading day; only six predefined Q4 OOS periods are parsed; prices are downloaded only after signals are frozen.','price_source':'Stooq daily CSV.','alpha_status':'PILOT_ONLY','performance_note':'Technical rerun required because prior run was SEC-rate-limited; no alpha conclusion is drawn from zero observations.','audit_timestamp_utc':datetime.now(timezone.utc).isoformat()}
    with open(os.path.join(OUT,'phase28b_sec_13dg_pit_oos.json'),'w',encoding='utf-8') as f: json.dump(payload,f,indent=2)
    if observations:
        with open(os.path.join(OUT,'phase28b_events.csv'),'w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=sorted(observations[0].keys())); w.writeheader(); w.writerows(observations)
    print(json.dumps({'phase':'28B','status':'COMPLETE','mapped':len(mapped),'filings':len(filings),'parsed_events':len(parsed),'signals':len(signal_events),'observations':len(observations),'parse_errors':len(parse_errors),'period_summary':summary},indent=2))

if __name__=='__main__': main()

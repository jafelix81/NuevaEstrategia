import ast, csv, gzip, json, os, re, time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from html import unescape
from urllib.request import Request, urlopen

BASE_SOURCE = 'Nueva_Estrategia_Fase0_Descubrimiento.py'
OUT = 'nueva_estrategia_phase28b_sec_13dg_pit_oos'
SEC_TICKERS = 'https://www.sec.gov/files/company_tickers.json'
SUB_URL = 'https://data.sec.gov/submissions/CIK{cik}.json'
ARCHIVE_BASE = 'https://www.sec.gov/Archives/edgar/data'
HEADERS = {'User-Agent': 'NuevaEstrategia research research@example.com', 'Accept-Encoding': 'gzip, deflate'}
TARGET_FORMS = {'SC 13D','SC 13G','SC 13D/A','SC 13G/A'}
PERIODS = [('2020Q4','2020-10-01','2020-12-31'),('2021Q4','2021-10-01','2021-12-31'),('2022Q4','2022-10-01','2022-12-31'),('2023Q4','2023-10-01','2023-12-31'),('2024Q4','2024-10-01','2024-12-31'),('2025Q4','2025-10-01','2025-12-31')]
FORWARD_DAYS = 63


def universe():
    tree = ast.parse(open(BASE_SOURCE, encoding='utf-8').read())
    for n in tree.body:
        if isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Name) and t.id == 'DEFAULT_UNIVERSE':
                    u = sorted(set(str(x).strip().upper() for x in ast.literal_eval(n.value)))
                    if len(u) != 335: raise RuntimeError(f'Expected frozen 335 universe, got {len(u)}')
                    return u
    raise RuntimeError('DEFAULT_UNIVERSE not found')


def get(url):
    req = Request(url, headers=HEADERS)
    with urlopen(req, timeout=60) as r:
        raw = r.read(); enc = (r.headers.get('Content-Encoding') or '').lower()
        if enc == 'gzip' or raw[:2] == b'\x1f\x8b': raw = gzip.decompress(raw)
        return raw


def get_json(url): return json.loads(get(url).decode('utf-8'))


def clean_text(raw):
    s = unescape(raw.decode('utf-8', errors='ignore'))
    s = re.sub(r'<[^>]+>', ' ', s)
    s = re.sub(r'\s+', ' ', s)
    return s


def pct_from_text(text):
    pats = [
        r'Percent of Class Represented by Amount in Row \(11\)\s*([0-9]+(?:\.[0-9]+)?)\s*%',
        r'Percent of class represented by amount in Row \(11\)\s*([0-9]+(?:\.[0-9]+)?)\s*%',
        r'Percent of Class\s*([0-9]+(?:\.[0-9]+)?)\s*%',
        r'Percent of class\s*([0-9]+(?:\.[0-9]+)?)\s*%'
    ]
    for p in pats:
        m = re.search(p, text, re.I)
        if m:
            try: return float(m.group(1))
            except ValueError: pass
    return None


def shares_from_text(text):
    pats = [
        r'Aggregate Amount Beneficially Owned by Each Reporting Person\s*([0-9][0-9,]*)',
        r'Aggregate Amount Beneficially Owned\s*([0-9][0-9,]*)',
        r'Number of Shares Beneficially Owned by Each Reporting Person\s*([0-9][0-9,]*)'
    ]
    for p in pats:
        m = re.search(p, text, re.I)
        if m:
            try: return int(m.group(1).replace(',',''))
            except ValueError: pass
    return None


def filing_doc(cik, accession, primary):
    acc = accession.replace('-','')
    url = f'{ARCHIVE_BASE}/{int(cik)}/{acc}/{primary}'
    return get(url), url


def extract_filings(ticker, cik, sub):
    rows = []
    recent = sub.get('filings',{}).get('recent',{})
    arrays = {k: recent.get(k,[]) for k in ['form','filingDate','accessionNumber','primaryDocument','reportDate']}
    for i, form in enumerate(arrays['form']):
        if form not in TARGET_FORMS: continue
        d = arrays['filingDate'][i] if i < len(arrays['filingDate']) else ''
        if not d or d < '2020-01-01' or d > '2025-12-31': continue
        rows.append({'ticker':ticker,'cik':cik,'form':form,'filing_date':d,'accession':arrays['accessionNumber'][i],'primary':arrays['primaryDocument'][i] if i < len(arrays['primaryDocument']) else ''})
    # Historical submissions files are explicitly used when present.
    for f in sub.get('filings',{}).get('files',[]):
        name = f.get('name','')
        if not name.endswith('.json'): continue
        try:
            old = get_json('https://data.sec.gov/submissions/'+name)
            for i, form in enumerate(old.get('form',[])):
                if form not in TARGET_FORMS: continue
                d = old.get('filingDate',[''])[i]
                if not d or d < '2020-01-01' or d > '2025-12-31': continue
                rows.append({'ticker':ticker,'cik':cik,'form':form,'filing_date':d,'accession':old.get('accessionNumber',[''])[i],'primary':old.get('primaryDocument',[''])[i] if i < len(old.get('primaryDocument',[])) else ''})
        except Exception:
            continue
    return rows


def next_weekday(d, days):
    x = d + timedelta(days=days)
    while x.weekday() >= 5: x += timedelta(days=1)
    return x


def price_series(tickers, start, end):
    import urllib.parse
    # Stooq CSV is used only for prices; it is downloaded after the signal set is frozen.
    out = {}
    for t in tickers:
        try:
            url = 'https://stooq.com/q/d/l/?' + urllib.parse.urlencode({'s':t.lower()+'.us','d1':start.replace('-',''),'d2':end.replace('-',''),'i':'d'})
            raw = get(url).decode('utf-8', errors='ignore').splitlines()
            vals = {}
            for line in raw[1:]:
                p = line.split(',')
                if len(p) >= 5 and p[4] not in ('','N/D'):
                    vals[p[0]] = float(p[4])
            out[t] = vals
        except Exception:
            out[t] = {}
        time.sleep(0.15)
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    tickers = universe()
    company = get_json(SEC_TICKERS)
    by_ticker = {}
    for row in company.values():
        t = str(row.get('ticker','')).strip().upper(); cik = str(row.get('cik_str','')).zfill(10)
        if t and t not in by_ticker: by_ticker[t] = cik
    mapped = {t:by_ticker[t] for t in tickers if t in by_ticker}

    filings=[]; errors=[]
    for idx,(ticker,cik) in enumerate(sorted(mapped.items()),1):
        try: filings.extend(extract_filings(ticker,cik,get_json(SUB_URL.format(cik=cik))))
        except Exception as e: errors.append({'ticker':ticker,'error':str(e)})
        if idx%25==0: time.sleep(0.5)
    # Deduplicate accession numbers and keep chronological order.
    uniq={r['accession']:r for r in filings if r.get('accession')}
    filings=sorted(uniq.values(), key=lambda r:(r['filing_date'],r['ticker'],r['accession']))

    events=[]; parse_errors=[]
    last_by_ticker={}
    for idx,r in enumerate(filings,1):
        try:
            raw,url=filing_doc(r['cik'],r['accession'],r['primary'])
            text=clean_text(raw)
            pct=pct_from_text(text); shares=shares_from_text(text)
            initial = not r['form'].endswith('/A')
            prior = last_by_ticker.get(r['ticker'])
            # PIT signal: a new/amended ownership filing is only eligible if parsed ownership is >=5%.
            # Initial filings and amendments are separated; no use of future filings.
            signal = pct is not None and pct >= 5.0 and (initial or prior is None or prior.get('pct') != pct)
            events.append({**r,'pct':pct,'shares':shares,'initial_or_amendment':'initial' if initial else 'amendment','signal':bool(signal),'source_url':url})
            last_by_ticker[r['ticker']]={'pct':pct,'shares':shares,'filing_date':r['filing_date']}
        except Exception as e: parse_errors.append({**r,'error':str(e)})
        if idx%10==0: time.sleep(0.2)

    # Freeze events first; prices are queried only afterward. Signal is available at filingDate close -> next trading day.
    signal_events=[e for e in events if e['signal']]
    if not signal_events: raise RuntimeError('No parsed PIT 5% ownership events; do not infer alpha from empty data.')
    p_start=min(e['filing_date'] for e in signal_events); p_end='2026-03-31'
    prices=price_series(sorted(set(e['ticker'] for e in signal_events)),p_start,p_end)
    observations=[]
    for e in signal_events:
        entry=next_weekday(datetime.strptime(e['filing_date'],'%Y-%m-%d').date(),1)
        exitd=entry+timedelta(days=FORWARD_DAYS*2)
        vals=prices.get(e['ticker'],{})
        dates=sorted(d for d in vals if d>=entry.isoformat())
        if not dates: continue
        ed=dates[min(FORWARD_DAYS-1,len(dates)-1)]
        ep=vals[dates[0]]; xp=vals[ed]
        if ep<=0: continue
        observations.append({**e,'entry_date':dates[0],'exit_date':ed,'forward_return':xp/ep-1.0})

    by_period=defaultdict(list)
    for o in observations:
        d=o['filing_date']
        key=next((p[0] for p in PERIODS if p[1]<=d<=p[2]),None)
        if key: by_period[key].append(o['forward_return'])
    summary=[]
    for key,_,_ in PERIODS:
        xs=by_period.get(key,[]); summary.append({'period':key,'n':len(xs),'mean_return':sum(xs)/len(xs) if xs else None,'median_return':sorted(xs)[len(xs)//2] if xs else None,'hit_rate':sum(x>0 for x in xs)/len(xs) if xs else None})

    payload={'phase':'28B','status':'COMPLETE','hypothesis':'PIT 13D/13G beneficial ownership events with parsed >=5% ownership may predict subsequent returns.','frozen_universe_size':335,'mapped_universe':len(mapped),'filings_collected':len(filings),'parsed_events':len(events),'signal_events':len(signal_events),'observations':len(observations),'parse_errors':len(parse_errors),'fetch_errors':errors,'period_summary':summary,'forward_days':FORWARD_DAYS,'knowledge_rule':'filingDate is the earliest public-availability date; signal enters next trading day; no later filing or price data is used to construct the signal.','price_source':'Stooq daily CSV, downloaded after signal events were frozen.','alpha_status':'PILOT_ONLY','audit_timestamp_utc':datetime.now(timezone.utc).isoformat()}
    with open(os.path.join(OUT,'phase28b_sec_13dg_pit_oos.json'),'w',encoding='utf-8') as f: json.dump(payload,f,indent=2)
    with open(os.path.join(OUT,'phase28b_events.csv'),'w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=sorted(observations[0].keys())); w.writeheader(); w.writerows(observations)
    print(json.dumps({'phase':'28B','status':'COMPLETE','filings':len(filings),'parsed_events':len(events),'signals':len(signal_events),'observations':len(observations),'period_summary':summary},indent=2))

if __name__=='__main__': main()

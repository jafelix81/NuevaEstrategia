import ast, csv, gzip, hashlib, json, os, time, zlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from urllib.error import HTTPError
from urllib.request import Request, urlopen

BASE_SOURCE = 'Nueva_Estrategia_Fase0_Descubrimiento.py'
OUT_DIR = 'nueva_estrategia_phase28e_sec_13dg_historical_cik_crosswalk'
SEC_TICKERS = 'https://www.sec.gov/files/company_tickers.json'
SEC_SUBMISSIONS = 'https://data.sec.gov/submissions/CIK{}.json'
MAPPER = 'https://raw.githubusercontent.com/jadchaar/sec-cik-mapper/main/mappings/stocks/ticker_to_cik.json'
HEADERS = {'User-Agent':'NuevaEstrategia research research@example.com','Accept-Encoding':'gzip, deflate'}
FORMS = {'SC 13D','SC 13G','SC 13D/A','SC 13G/A'}
START='2020-10-01'; END='2026-09-30'

_last = 0.0

def decode_http_body(raw):
    # urllib does not reliably decompress every compressed HTTP response.
    # Detect the wire format from magic bytes so JSON parsing is deterministic.
    if raw[:2] == b'\x1f\x8b':
        return gzip.decompress(raw)
    try:
        return zlib.decompress(raw)
    except zlib.error:
        return raw

def get(url, timeout=60, retries=6):
    global _last
    err=None
    for attempt in range(retries):
        wait = 0.25 - (time.monotonic()-_last)
        if wait > 0: time.sleep(wait)
        _last=time.monotonic()
        try:
            with urlopen(Request(url,headers=HEADERS),timeout=timeout) as r:
                return decode_http_body(r.read())
        except HTTPError as e:
            err=e
            if e.code == 404: raise
            if e.code not in (429,500,502,503,504): raise
            time.sleep(min(20,2**attempt))
        except Exception as e:
            err=e; time.sleep(min(15,2**attempt))
    raise RuntimeError(f'GET failed: {url}: {err}')

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

def norm_form(x):
    return ' '.join(str(x).strip().upper().replace('SCHEDULE ','SC ').split())

def validate_cik(cik):
    data=json.loads(get(SEC_SUBMISSIONS.format(cik)).decode('utf-8'))
    recent=data.get('filings',{}).get('recent',{})
    forms=recent.get('form',[]); dates=recent.get('filingDate',[])
    n=0; first=None; last=None
    for form,d in zip(forms,dates):
        if norm_form(form) in FORMS and START<=str(d)[:10]<=END:
            n+=1; first=min(first,str(d)[:10]) if first else str(d)[:10]; last=max(last,str(d)[:10]) if last else str(d)[:10]
    return {'cik':str(cik).zfill(10),'company_name':data.get('name',''),'sic':data.get('sic',''),'sic_description':data.get('sicDescription',''),'recent_13dg_filings':n,'first_recent_13dg':first,'last_recent_13dg':last},None

def main():
    universe=frozen_universe()
    sec=json.loads(get(SEC_TICKERS).decode('utf-8'))
    sec_map={str(v.get('ticker','')).upper():str(v.get('cik_str','')).zfill(10) for v in sec.values() if v.get('ticker')}
    mapper_raw=get(MAPPER)
    mapper_hash=hashlib.sha256(mapper_raw).hexdigest()
    mapper=json.loads(mapper_raw.decode('utf-8'))
    rows=[]; candidate_ciks={}
    for ticker in universe:
        sec_cik=sec_map.get(ticker)
        hist_cik=str(mapper.get(ticker,'')).zfill(10) if mapper.get(ticker) else None
        source='sec_current' if sec_cik else ('sec_cik_mapper' if hist_cik else 'unresolved')
        cik=sec_cik or hist_cik
        if sec_cik and hist_cik and sec_cik!=hist_cik: source='conflict_sec_vs_mapper'
        rows.append({'ticker':ticker,'sec_current_cik':sec_cik or '','mapper_cik':hist_cik or '','selected_cik':cik or '','mapping_source':source})
        if cik: candidate_ciks[cik]=ticker
    validations={}; errors=[]
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs={ex.submit(validate_cik,cik):cik for cik in sorted(candidate_ciks)}
        for fut in as_completed(futs):
            cik=futs[fut]
            try: validations[cik]=fut.result()[0]
            except Exception as e: errors.append({'cik':cik,'ticker':candidate_ciks[cik],'error':str(e)})
    for r in rows:
        v=validations.get(r['selected_cik'])
        if v:
            r.update({'validated_name':v['company_name'],'sic':v['sic'],'recent_13dg_filings':v['recent_13dg_filings'],'first_recent_13dg':v['first_recent_13dg'] or '','last_recent_13dg':v['last_recent_13dg'] or '','sec_validated':True})
        else:
            r.update({'validated_name':'','sic':'','recent_13dg_filings':0,'first_recent_13dg':'','last_recent_13dg':'','sec_validated':False})
    os.makedirs(OUT_DIR,exist_ok=True)
    fields=list(rows[0].keys())
    with open(os.path.join(OUT_DIR,'phase28e_crosswalk.csv'),'w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
    summary={
        'phase':'28E','status':'COMPLETE','frozen_universe_size':len(universe),
        'sec_current_mapped':sum(bool(r['sec_current_cik']) for r in rows),
        'mapper_mapped':sum(bool(r['mapper_cik']) for r in rows),
        'selected_cik':sum(bool(r['selected_cik']) for r in rows),
        'validated_sec':sum(r['sec_validated'] for r in rows),
        'unresolved':sum(not r['selected_cik'] for r in rows),
        'mapping_conflicts':sum(r['mapping_source']=='conflict_sec_vs_mapper' for r in rows),
        'selected_with_13dg_history':sum(r['sec_validated'] and r['recent_13dg_filings']>0 for r in rows),
        'validation_errors':len(errors),
        'mapper_source':MAPPER,'mapper_sha256':mapper_hash,
        'knowledge_rule':'mapping is identity resolution only; filing_date remains the PIT knowledge date.',
        'audit_timestamp_utc':datetime.now(timezone.utc).isoformat(),
        'validation_errors_sample':errors[:25]
    }
    with open(os.path.join(OUT_DIR,'phase28e_summary.json'),'w',encoding='utf-8') as f: json.dump(summary,f,indent=2)
    print(json.dumps(summary,indent=2))

if __name__=='__main__': main()

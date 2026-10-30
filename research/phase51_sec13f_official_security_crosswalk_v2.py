# Phase 51 v2 audit: official SEC 13(f) quarterly security-list crosswalk.
import gzip, json, re, subprocess, tempfile, time, unicodedata
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

BASE='Nueva_Estrategia_Fase0_Descubrimiento.py'
TICKERS='https://www.sec.gov/files/company_tickers.json'
TICKERS_ALT='https://www.sec.gov/files/company_tickers_exchange.json'
SUB='https://data.sec.gov/submissions/CIK{cik}.json'
HEADERS={'User-Agent':'NuevaEstrategia quantitative research jose.felix@felixsarmiento.com','Accept-Encoding':'gzip, deflate','Accept':'application/json,text/plain,*/*'}
OUT=Path('phase51_sec13f_official_security_crosswalk_v2'); OUT.mkdir(exist_ok=True)
SAMPLES={
 '2018Q1':('https://www.sec.gov/divisions/investment/13f/13flist2018q1.pdf','pdf'),
 '2020Q1':('https://www.sec.gov/divisions/investment/13f/13flist2020q1.pdf','pdf'),
 '2024Q1':('https://www.sec.gov/files/investment/13flist2024q1.txt','txt'),
 '2026Q3':('https://www.sec.gov/files/investment/13flist2026q3.txt','txt'),
}

def get(url,retries=5):
    last=None
    for i in range(retries):
        try:
            with urlopen(Request(url,headers=HEADERS),timeout=60) as r:
                raw=r.read()
                # SEC may return gzip-compressed payloads even when urllib does not
                # transparently decode them. Decode by header or gzip magic bytes.
                enc=str(r.headers.get('Content-Encoding','')).lower()
                if enc=='gzip' or raw[:2]==b'\x1f\x8b':
                    raw=gzip.decompress(raw)
                return raw
        except HTTPError as e:
            last=e
            if e.code in (429,500,502,503,504): time.sleep(min(20,2**i)); continue
            raise
        except (URLError,TimeoutError,OSError) as e:
            last=e; time.sleep(min(15,2**i))
    raise RuntimeError(f'GET failed {url}: {last}')

def norm(s):
    s=unicodedata.normalize('NFKD',str(s)).encode('ascii','ignore').decode().upper()
    s=re.sub(r'[^A-Z0-9 ]+',' ',s)
    s=re.sub(r'\b(THE|INC|INCORPORATED|CORP|CORPORATION|CO|COMPANY|LTD|LIMITED|PLC|HLDGS|HOLDINGS|GROUP|SA|NV|LP|LLC|CLASS|CL|ORD|COM|COMMON|SHS|SHARE|NEW)\b',' ',s)
    return re.sub(r'\s+',' ',s).strip()

def universe():
    txt=Path(BASE).read_text(encoding='utf-8'); m=re.search(r'DEFAULT_UNIVERSE\s*=\s*\[(.*?)\]\n\n',txt,re.S)
    if not m: raise RuntimeError('DEFAULT_UNIVERSE not found')
    vals=re.findall(r"'([^']+)'",m.group(1)); vals=sorted(set(x.upper() for x in vals))
    if len(vals)!=335: raise RuntimeError(f'Expected 335 names, got {len(vals)}')
    return vals

def parse_company_payload(data):
    out={}
    if isinstance(data,dict):
        records=data.values()
    elif isinstance(data,list):
        records=data
    else:
        return out
    for r in records:
        t=str(r.get('ticker','')).upper().strip()
        cik=r.get('cik_str',r.get('cik',''))
        if t and cik not in (None,''):
            out[t]={'cik':str(cik).zfill(10),'name':r.get('title',r.get('name',''))}
    return out

def sec_company_map():
    errors=[]
    for url in (TICKERS,TICKERS_ALT):
        try:
            raw=get(url); data=json.loads(raw.decode()); out=parse_company_payload(data)
            if out: return out,errors
            errors.append({'url':url,'error':'empty_or_unrecognized_payload'})
        except Exception as e:
            errors.append({'url':url,'error':str(e)})
    raise RuntimeError('SEC ticker/CIK mapping unavailable: '+json.dumps(errors))

def submissions(item):
    try:
        d=json.loads(get(SUB.format(cik=item['cik'])).decode())
        names=[d.get('name','')]+[x.get('name','') for x in d.get('formerNames',[]) if x.get('name')]
        return sorted(set(norm(x) for x in names if norm(x)))
    except Exception as e: return {'error':str(e)}

def parse_txt(raw):
    rows=[]
    for line in raw.decode('latin1','ignore').splitlines():
        if len(line)<40: continue
        cusip=line[:9].strip(); name=line[10:40].strip(); desc=line[40:67].strip(); status=line[67:70].strip()
        if re.fullmatch(r'[A-Z0-9]{6,9}',cusip) and name: rows.append((cusip,name,desc,status))
    return rows

def parse_pdf(raw):
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/'l.pdf'; out=Path(td)/'l.txt'; p.write_bytes(raw)
        r=subprocess.run(['pdftotext','-layout',str(p),str(out)],capture_output=True,text=True)
        if r.returncode!=0: raise RuntimeError('pdftotext unavailable or failed: '+r.stderr[:500])
        lines=out.read_text(errors='ignore').splitlines()
    rows=[]
    for line in lines:
        m=re.match(r'^\s*([A-Z0-9]{6,9})\s+10\s+\d\s+\*?\s*(.*)$',line)
        if m: rows.append((m.group(1),m.group(2).strip(),'',''))
    return rows

def main():
    uni=universe(); cmap,cmap_errors=sec_company_map(); mapped={t:cmap[t] for t in uni if t in cmap}; unmapped=[t for t in uni if t not in cmap]
    aliases={}; errors=[]
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs={ex.submit(submissions,v):t for t,v in mapped.items()}
        for f in as_completed(futs):
            t=futs[f]
            try:
                r=f.result()
                if isinstance(r,dict): errors.append({'ticker':t,'error':r['error']})
                else: aliases[t]=r
            except Exception as e: errors.append({'ticker':t,'error':str(e)})
    for t,v in mapped.items():
        aliases.setdefault(t,[]).append(norm(v['name'])); aliases[t]=sorted(set(x for x in aliases[t] if x))
    quarter_rows={}; download_errors={}
    for q,(url,kind) in SAMPLES.items():
        try:
            raw=get(url); quarter_rows[q]=parse_txt(raw) if kind=='txt' else parse_pdf(raw)
        except Exception as e: download_errors[q]=str(e); quarter_rows[q]=[]
    results={}
    for q,rows in quarter_rows.items():
        hits=[]
        for t in uni:
            als=aliases.get(t,[]); matched=[]
            for cusip,name,desc,status in rows:
                nn=norm(name)
                if nn and any(nn==a or (len(a)>=6 and (a in nn or nn in a)) for a in als):
                    if not re.search(r'\b(CALL|PUT|WARRANT|RIGHT|UNIT|DEBT|NOTE|PREF|PREFERRED)\b',desc.upper()): matched.append((cusip,name,desc,status))
            hits.append({'ticker':t,'mapped_cik':mapped.get(t,{}).get('cik'),'aliases':als,'matches':matched[:10],'match_count':len(matched)})
        covered=sum(1 for x in hits if x['match_count']>0); ambiguous=sum(1 for x in hits if x['match_count']>1)
        results[q]={'covered':covered,'coverage_pct':round(100*covered/len(uni),3),'ambiguous':ambiguous,'rows':hits}
    gate=(len(cmap_errors)==0 and not download_errors and len(errors)==0 and len(mapped)>=301 and all(results[q]['coverage_pct']>=95 for q in results))
    summary={'phase':'51-v2','source':'SEC Official List of Section 13(f) Securities','status':'COMPLETE','universe_size':len(uni),'current_sec_ticker_cik_mapped':len(mapped),'current_sec_ticker_cik_unmapped':len(unmapped),'unmapped_tickers':unmapped,'mapping_endpoint_errors':cmap_errors,'submission_errors':len(errors),'samples':{q:{k:v for k,v in r.items() if k!='rows'} for q,r in results.items()},'download_errors':download_errors,'identity_rule':'Ticker-to-CIK from SEC current association endpoint; issuer aliases from SEC current/former names; quarterly CUSIP from SEC official Section 13(f) security list. Knowledge date is the quarter list effective date, not a later lookup date.','interpretation':'Feasibility only. No alpha testing. The v2 change is limited to robust SEC ticker/CIK endpoint fallback and gzip-aware SEC response decoding; it does not relax the historical coverage gate.','gate_rule':'PASS only if all four historical snapshots have >=95% issuer-name coverage, no SEC mapping/submission/download errors, and at least 301/335 current ticker-CIK mappings.','gate':'PASS' if gate else 'FAIL','alpha_authorized':False,'next_step':'If PASS, use this crosswalk as an independent PIT identity layer for 13F research and reassess the prior 13F coverage gate. If FAIL, do not run 13F alpha and record the precise identity limitation.'}
    json.dump(summary,open(OUT/'summary.json','w'),indent=2); json.dump(results,open(OUT/'matches.json','w'),indent=2); print(json.dumps(summary,indent=2))
    if not gate: raise SystemExit(1)
if __name__=='__main__': main()

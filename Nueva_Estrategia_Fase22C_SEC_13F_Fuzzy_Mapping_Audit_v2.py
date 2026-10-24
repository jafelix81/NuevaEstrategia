import io, json, re, zipfile, time
from pathlib import Path
import requests
import pandas as pd

OUT=Path('nueva_estrategia_phase22c_sec_13f_fuzzy_mapping_audit'); OUT.mkdir(exist_ok=True)
HEADERS={'User-Agent':'NuevaEstrategia research research@example.com'}
SEC_TICKERS='https://www.sec.gov/files/company_tickers_exchange.json'
DATASETS={
    '2016Q1':'https://www.sec.gov/files/structureddata/data/form-13f-data-sets/2016q1_form13f.zip',
    '2020Q1':'https://www.sec.gov/files/structureddata/data/form-13f-data-sets/2020q1_form13f.zip',
    '2024Q1':'https://www.sec.gov/files/structureddata/data/form-13f-data-sets/01mar2024-31may2024_form13f.zip',
}

def get(u, timeout=120):
    r=requests.get(u,headers=HEADERS,timeout=timeout); r.raise_for_status(); return r.content

def get_json(u, timeout=30):
    r=requests.get(u,headers=HEADERS,timeout=timeout); r.raise_for_status(); return r.json()

def norm(s):
    s=re.sub(r'[^A-Z0-9 ]',' ',str(s).upper())
    s=re.sub(r'\b(THE|INC|INCORPORATED|CORP|CORPORATION|LTD|LIMITED|PLC|HOLDINGS|HOLDING|COMPANY|CO|LP|LLC|N A|NA)\b',' ',s)
    return re.sub(r'\s+',' ',s).strip()

def tokens(s):
    return {x for x in norm(s).split() if len(x)>=3}

def load_sec_universe():
    payload=json.loads(get(SEC_TICKERS).decode())
    fields=payload.get('fields',[]); rows=payload.get('data',[])
    pos={str(f).lower():i for i,f in enumerate(fields)}
    required={'cik','name','ticker'}
    if not required.issubset(pos): raise RuntimeError(f'Unexpected SEC ticker schema: fields={fields}')
    out=[]
    for row in rows:
        if not isinstance(row,list) or len(row)<len(fields): continue
        ticker=str(row[pos['ticker']]).upper().strip(); name=str(row[pos['name']]).strip()
        if ticker and name: out.append({'cik':str(row[pos['cik']]).zfill(10),'ticker':ticker,'name':name,'norm':norm(name)})
    return out

def load_frozen():
    src=Path('Nueva_Estrategia_Fase0_Descubrimiento.py').read_text(encoding='utf-8')
    block=src.split('DEFAULT_UNIVERSE = [',1)[1].split(']\n',1)[0]
    return set(re.findall(r"'([A-Z0-9.\-]+)'",block))

def load_sec_name_history(candidates):
    """Build a deterministic historical-name crosswalk from official SEC submissions formerNames."""
    alias_to_tickers={}; failures=[]
    for c in candidates:
        cik=c['cik'].lstrip('0') or '0'
        try:
            data=get_json(f'https://data.sec.gov/submissions/CIK{int(cik):010d}.json')
            aliases={norm(c['name'])}
            for item in data.get('formerNames',[]) or []:
                n=norm(item.get('name',''))
                if n: aliases.add(n)
            for a in aliases: alias_to_tickers.setdefault(a,set()).add(c['ticker'])
        except Exception as e:
            failures.append({'ticker':c['ticker'],'error':str(e)})
        time.sleep(0.12)
    unique={a:next(iter(ts)) for a,ts in alias_to_tickers.items() if len(ts)==1}
    ambiguous={a:sorted(ts) for a,ts in alias_to_tickers.items() if len(ts)>1}
    return unique, ambiguous, failures

def issuer_col(z):
    for n in z.namelist():
        if n.upper().endswith('INFOTABLE.TSV'):
            with z.open(n) as f: head=pd.read_csv(f,sep='\t',dtype=str,nrows=0)
            cols={c.lower():c for c in head.columns}
            return n, (cols.get('nameissuer') or cols.get('nameofissuer') or cols.get('name'))
    raise RuntimeError('INFOTABLE.TSV not found')

def audit_dataset(raw, candidates, sec_aliases):
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        info,namecol=issuer_col(z)
        names=set()
        with z.open(info) as f:
            for chunk in pd.read_csv(f,sep='\t',dtype=str,usecols=[namecol],chunksize=200000):
                for x in chunk[namecol].fillna(''):
                    n=norm(x)
                    if n: names.add(n)
    candidate_by_ticker={x['ticker']:x for x in candidates}; candidate_tokens={x['ticker']:tokens(x['name']) for x in candidates}
    hist_token_index={}; hist_tokens={}
    for n in names:
        nt=tokens(n); hist_tokens[n]=nt
        for t in nt: hist_token_index.setdefault(t,set()).add(n)
    matched={}; ambiguous=[]
    for ticker,c in candidate_by_ticker.items():
        target=c['norm']
        if target in names:
            matched[ticker]={'method':'exact','issuer_name':target,'score':1.0}; continue
        alias_names=[a for a,t in sec_aliases.items() if t==ticker and a in names]
        if alias_names:
            matched[ticker]={'method':'sec_former_name','issuer_name':sorted(alias_names)[0],'score':1.0}; continue
        tt=candidate_tokens[ticker]; hits=set()
        for t in tt: hits |= hist_token_index.get(t,set())
        scored=[]
        for n in hits:
            nt=hist_tokens[n]; j=len(tt & nt)/len(tt | nt) if tt and nt else 0; scored.append((j,n))
        scored.sort(reverse=True)
        if scored:
            best=scored[0]; second=scored[1][0] if len(scored)>1 else 0.0
            if best[0]>=0.80 and best[0]-second>=0.15:
                matched[ticker]={'method':'token','issuer_name':best[1],'score':round(best[0],4)}
            else:
                ambiguous.append({'ticker':ticker,'current_name':c['name'],'best_issuer':best[1],'best_score':round(best[0],4),'second_score':round(second,4)})
    return {
        'historical_unique_issuers':len(names),'candidate_universe':len(candidates),'matched_candidates':len(matched),
        'coverage_rate':len(matched)/len(candidates) if candidates else 0,
        'exact_matches':sum(v['method']=='exact' for v in matched.values()),
        'sec_former_name_matches':sum(v['method']=='sec_former_name' for v in matched.values()),
        'token_matches':sum(v['method']=='token' for v in matched.values()),
        'ambiguous_candidates':len(ambiguous),'unmatched_candidates':len(candidates)-len(matched)-len(ambiguous),
        'mapping_examples':list(matched.items())[:20],'ambiguous_examples':ambiguous[:20]
    }

def main():
    universe=load_sec_universe(); frozen=load_frozen(); candidates=[x for x in universe if x['ticker'] in frozen]
    audit={'phase':'22C_SEC_13F_MAPPING_FEASIBILITY_V6_FORMER_NAMES','frozen_universe':len(frozen),'sec_exchange_rows':len(universe),'sec_current_matches':len(candidates),'datasets':{},'rule':'current-name exact + unique official SEC former-name alias + unique deterministic token; ambiguous matches rejected; audit only'}
    if not candidates: audit['conclusion']='BLOCKED_CURRENT_SEC_MATCHES'
    else:
        aliases,alias_ambiguous,alias_failures=load_sec_name_history(candidates)
        audit['sec_former_name_aliases']=len(aliases); audit['sec_former_name_ambiguous_aliases']=len(alias_ambiguous); audit['sec_former_name_fetch_failures']=alias_failures
        for label,url in DATASETS.items(): audit['datasets'][label]=audit_dataset(get(url),candidates,aliases)
        rates=[v['coverage_rate'] for v in audit['datasets'].values()]
        audit['conclusion']='PROCEED_TO_CUSIP_CROSSWALK' if rates and min(rates)>=0.90 else 'INSUFFICIENT_COVERAGE_FOR_PRODUCTION'
    (OUT/'phase22c_mapping_summary_v6.json').write_text(json.dumps(audit,indent=2),encoding='utf-8'); print(json.dumps(audit,indent=2))

if __name__=='__main__': main()

import io, json, re, zipfile
from pathlib import Path
import requests
import pandas as pd

OUT=Path('nueva_estrategia_phase22c_sec_13f_fuzzy_mapping_audit'); OUT.mkdir(exist_ok=True)
HEADERS={'User-Agent':'NuevaEstrategia research research@example.com'}
SEC_TICKERS='https://www.sec.gov/files/company_tickers_exchange.json'
# Three spaced checkpoints are enough for a feasibility audit; do not repeatedly download five full datasets.
DATASETS={
    '2016Q1':'https://www.sec.gov/files/structureddata/data/form-13f-data-sets/2016q1_form13f.zip',
    '2020Q1':'https://www.sec.gov/files/structureddata/data/form-13f-data-sets/2020q1_form13f.zip',
    '2024Q1':'https://www.sec.gov/files/structureddata/data/form-13f-data-sets/01mar2024-31may2024_form13f.zip',
}

def get(u, timeout=120):
    r=requests.get(u,headers=HEADERS,timeout=timeout); r.raise_for_status(); return r.content

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

def issuer_col(z):
    for n in z.namelist():
        if n.upper().endswith('INFOTABLE.TSV'):
            with z.open(n) as f:
                head=pd.read_csv(f,sep='\t',dtype=str,nrows=0)
            cols={c.lower():c for c in head.columns}
            return n, (cols.get('nameissuer') or cols.get('nameofissuer') or cols.get('name'))
    raise RuntimeError('INFOTABLE.TSV not found')

def audit_dataset(raw, candidates):
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        info,namecol=issuer_col(z)
        if not namecol: raise RuntimeError(f'No issuer-name column in {info}')
        names=set()
        with z.open(info) as f:
            for chunk in pd.read_csv(f,sep='\t',dtype=str,usecols=[namecol],chunksize=200000):
                names.update(norm(x) for x in chunk[namecol].fillna('') if norm(x))
    by_norm={x['norm']:x for x in candidates if x['norm']}
    # Fast, deterministic candidate retrieval by token overlap. This is a feasibility screen, not production mapping.
    token_index={}
    for c in candidates:
        for t in tokens(c['name']): token_index.setdefault(t,set()).add(c['ticker'])
    exact=0; token_candidate=0; ambiguous=0; no_match=0
    examples=[]
    for n in names:
        if n in by_norm:
            exact+=1; continue
        hits=set()
        for t in tokens(n): hits |= token_index.get(t,set())
        scored=[]
        nt=tokens(n)
        for ticker in hits:
            ct=next(c for c in candidates if c['ticker']==ticker)
            jt=len(nt & tokens(ct['name']))/len(nt | tokens(ct['name'])) if nt and tokens(ct['name']) else 0
            scored.append((jt,ticker))
        scored.sort(reverse=True)
        if scored and scored[0][0]>=0.80 and (len(scored)==1 or scored[0][0]-scored[1][0]>=0.15):
            token_candidate+=1
            if len(examples)<10: examples.append({'issuer':n,'ticker':scored[0][1],'jaccard':round(scored[0][0],3)})
        elif scored and scored[0][0]>=0.65:
            ambiguous+=1
        else: no_match+=1
    accepted=exact+token_candidate
    return {'unique_issuers':len(names),'exact':exact,'token_screen_accepted':token_candidate,'accepted_total':accepted,'accepted_rate':accepted/len(names) if names else 0,'ambiguous':ambiguous,'no_match':no_match,'examples':examples}

def main():
    universe=load_sec_universe(); frozen=load_frozen(); candidates=[x for x in universe if x['ticker'] in frozen]
    audit={'phase':'22C_SEC_13F_MAPPING_FEASIBILITY_V4','frozen_universe':len(frozen),'sec_exchange_rows':len(universe),'sec_current_matches':len(candidates),'datasets':{},'rule':'exact + deterministic token-overlap screen only; no production mapping; ambiguous matches rejected'}
    if not candidates:
        audit['conclusion']='BLOCKED_CURRENT_SEC_MATCHES'; audit['reason']='No frozen tickers resolved against SEC current exchange table; historical crosswalk cannot be inferred from current names.'
    else:
        for label,url in DATASETS.items():
            audit['datasets'][label]=audit_dataset(get(url),candidates)
        rates=[v['accepted_rate'] for v in audit['datasets'].values()]
        audit['conclusion']='PROCEED_TO_HISTORICAL_CUSIP_CROSSWALK' if rates and min(rates)>=0.70 else 'INSUFFICIENT_FOR_PRODUCTION_MAPPING'
    (OUT/'phase22c_mapping_summary_v4.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
    print(json.dumps(audit,indent=2))

if __name__=='__main__': main()

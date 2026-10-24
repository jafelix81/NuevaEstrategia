import io, json, re, zipfile
from pathlib import Path
import requests
import pandas as pd

OUT = Path('nueva_estrategia_phase22c_cusip_crosswalk_audit'); OUT.mkdir(exist_ok=True)
HEADERS = {'User-Agent': 'NuevaEstrategia research research@example.com'}
SEC_TICKERS = 'https://www.sec.gov/files/company_tickers_exchange.json'
DATASETS = {
    '2016Q1': ('https://www.sec.gov/files/structureddata/data/form-13f-data-sets/2016q1_form13f.zip', '2016-03-31'),
    '2020Q1': ('https://www.sec.gov/files/structureddata/data/form-13f-data-sets/2020q1_form13f.zip', '2020-03-31'),
    '2024Q1': ('https://www.sec.gov/files/structureddata/data/form-13f-data-sets/01mar2024-31may2024_form13f.zip', '2024-05-31'),
}

def get(u, timeout=180):
    r = requests.get(u, headers=HEADERS, timeout=timeout); r.raise_for_status(); return r.content

def norm(s):
    s = re.sub(r'[^A-Z0-9 ]', ' ', str(s).upper())
    s = re.sub(r'\b(THE|INC|INCORPORATED|CORP|CORPORATION|LTD|LIMITED|PLC|HOLDINGS|HOLDING|COMPANY|CO|LP|LLC|N A|NA)\b', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()

def load_sec_universe():
    p = requests.get(SEC_TICKERS, headers=HEADERS, timeout=60).json()
    fields, rows = p.get('fields', []), p.get('data', [])
    pos = {str(f).lower(): i for i, f in enumerate(fields)}
    return [{'cik': str(r[pos['cik']]).zfill(10), 'ticker': str(r[pos['ticker']]).upper().strip(), 'name': str(r[pos['name']]).strip()}
            for r in rows if isinstance(r, list) and len(r) >= len(fields) and str(r[pos['ticker']]).strip()]

def load_frozen():
    src = Path('Nueva_Estrategia_Fase0_Descubrimiento.py').read_text(encoding='utf-8')
    block = src.split('DEFAULT_UNIVERSE = [', 1)[1].split(']\n', 1)[0]
    return set(re.findall(r"'([A-Z0-9.\-]+)'", block))

def issuer_and_cusip_columns(z):
    for n in z.namelist():
        if n.upper().endswith('INFOTABLE.TSV'):
            with z.open(n) as f: head = pd.read_csv(f, sep='\t', dtype=str, nrows=0)
            cols = {c.lower(): c for c in head.columns}
            issuer = cols.get('nameofissuer') or cols.get('nameissuer') or cols.get('name')
            cusip = cols.get('cusip')
            if not issuer or not cusip: raise RuntimeError(f'Missing issuer/CUSIP columns: {head.columns.tolist()}')
            return n, issuer, cusip
    raise RuntimeError('INFOTABLE.TSV not found')

def load_13f_issuer_cusips(raw):
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        info, issuer_col, cusip_col = issuer_and_cusip_columns(z)
        pairs = set()
        with z.open(info) as f:
            for chunk in pd.read_csv(f, sep='\t', dtype=str, usecols=[issuer_col, cusip_col], chunksize=200000):
                chunk['issuer_norm'] = chunk[issuer_col].fillna('').map(norm)
                chunk['cusip_norm'] = chunk[cusip_col].fillna('').str.replace(r'[^0-9A-Z]', '', regex=True).str.upper()
                pairs.update((r[0], r[1]) for r in chunk[['issuer_norm','cusip_norm']].itertuples(index=False) if r[0] and r[1])
    out = {}
    for issuer, cusip in pairs: out.setdefault(issuer, set()).add(cusip)
    return out

def load_former_names(candidates):
    out = {}
    for c in candidates:
        try:
            data = requests.get(f"https://data.sec.gov/submissions/CIK{c['cik']}.json", headers=HEADERS, timeout=30).json()
            out[c['cik']] = [x.get('name','') for x in data.get('formerNames', []) if x.get('name')]
        except Exception:
            out[c['cik']] = []
    return out

def audit_dataset(raw, candidates, former_names, asof):
    name_cusips = load_13f_issuer_cusips(raw)
    matched, ambiguous, missing = {}, [], []
    for c in candidates:
        names = [norm(c['name'])] + [norm(x) for x in former_names.get(c['cik'], [])]
        hits = set(); hit_names = []
        for name in names:
            cs = name_cusips.get(name, set())
            if cs:
                hits |= cs; hit_names.append(name)
        if len(hits) == 1:
            matched[c['ticker']] = {'method':'pit_13f_issuer_name_to_cusip','issuer_names_used':sorted(set(hit_names)),'cusip':next(iter(hits))}
        elif len(hits) > 1:
            ambiguous.append({'ticker':c['ticker'],'issuer_names_used':sorted(set(hit_names)),'candidate_cusips':sorted(hits),'reason':'multiple CUSIPs for current/former issuer labels'})
        else:
            missing.append({'ticker':c['ticker'],'issuer_name':c['name'],'reason':'no exact normalized issuer/former-name hit in this 13F info table'})
    return {'asof':asof,'historical_unique_issuers':len(name_cusips),'candidate_universe':len(candidates),'matched_candidates':len(matched),'coverage_rate':len(matched)/len(candidates) if candidates else 0,'ambiguous_candidates':len(ambiguous),'no_crosswalk_candidates':len(missing),'mapping_examples':list(matched.items())[:25],'ambiguous_examples':ambiguous[:25],'no_crosswalk_examples':missing[:25]}

def main():
    universe = load_sec_universe(); frozen = load_frozen(); candidates = [x for x in universe if x['ticker'] in frozen]
    former = load_former_names(candidates)
    audit={'phase':'22C_SEC_13F_PIT_ISSUER_CUSIP_AUDIT_V8','frozen_universe':len(frozen),'sec_current_matches':len(candidates),'mapping_source':'historical 13F INFOTABLE issuer/CUSIP pairs; SEC formerNames expand issuer identity','pit_rule':'mapping is derived only from the report-date 13F dataset; no future CUSIP is injected','datasets':{}}
    for label,(url,asof) in DATASETS.items(): audit['datasets'][label]=audit_dataset(get(url,timeout=240),candidates,former,asof)
    rates=[v['coverage_rate'] for v in audit['datasets'].values()]; audit['minimum_coverage']=min(rates) if rates else 0
    audit['conclusion']='PROCEED_TO_13F_SIGNAL_BUILD' if rates and min(rates)>=0.90 else '13F_IDENTITY_MAPPING_NEEDS_FURTHER_RESOLUTION'
    (OUT/'phase22c_pit_issuer_cusip_summary_v8.json').write_text(json.dumps(audit,indent=2),encoding='utf-8'); print(json.dumps(audit,indent=2))
if __name__=='__main__': main()

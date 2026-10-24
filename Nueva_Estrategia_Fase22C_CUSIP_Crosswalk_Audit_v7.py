import io, gzip, json, re, zipfile
from pathlib import Path
import requests
import pandas as pd

OUT = Path('nueva_estrategia_phase22c_cusip_crosswalk_audit'); OUT.mkdir(exist_ok=True)
HEADERS = {'User-Agent': 'NuevaEstrategia research research@example.com'}
SEC_TICKERS = 'https://www.sec.gov/files/company_tickers_exchange.json'
CROSSWALK = 'https://raw.githubusercontent.com/john-friedman/datamule-data/master/data/datasets/cik_cusip_crosswalk.csv.gz'
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
    out = []
    for row in rows:
        if not isinstance(row, list) or len(row) < len(fields): continue
        ticker = str(row[pos['ticker']]).upper().strip(); name = str(row[pos['name']]).strip()
        if ticker and name:
            out.append({'cik': str(row[pos['cik']]).zfill(10), 'ticker': ticker, 'name': name})
    return out

def load_frozen():
    src = Path('Nueva_Estrategia_Fase0_Descubrimiento.py').read_text(encoding='utf-8')
    block = src.split('DEFAULT_UNIVERSE = [', 1)[1].split(']\n', 1)[0]
    return set(re.findall(r"'([A-Z0-9.\-]+)'", block))

def load_crosswalk(ciks):
    raw = get(CROSSWALK, timeout=240)
    cols = ['accession_number', 'filing_date', 'issuer_cik', 'cusip']
    df = pd.read_csv(io.BytesIO(raw), compression='gzip', usecols=cols, dtype=str)
    df['issuer_cik'] = df['issuer_cik'].str.zfill(10)
    df['filing_date'] = pd.to_datetime(df['filing_date'], format='%Y%m%d', errors='coerce')
    df['cusip'] = df['cusip'].str.replace(r'[^0-9A-Z]', '', regex=True).str.upper()
    df = df[df['issuer_cik'].isin(ciks) & df['cusip'].ne('') & df['filing_date'].notna()].copy()
    return df

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

def audit_dataset(raw, candidates, crosswalk, asof):
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        info, issuer_col, cusip_col = issuer_and_cusip_columns(z)
        rows = []
        with z.open(info) as f:
            for chunk in pd.read_csv(f, sep='\t', dtype=str, usecols=[issuer_col, cusip_col], chunksize=200000):
                chunk['issuer_norm'] = chunk[issuer_col].fillna('').map(norm)
                chunk['cusip_norm'] = chunk[cusip_col].fillna('').str.replace(r'[^0-9A-Z]', '', regex=True).str.upper()
                rows.append(chunk[['issuer_norm','cusip_norm']])
        holdings = pd.concat(rows, ignore_index=True)
    name_cusips = {}
    for r in holdings.itertuples(index=False):
        if r.issuer_norm and r.cusip_norm:
            name_cusips.setdefault(r.issuer_norm, set()).add(r.cusip_norm)
    asof_ts = pd.Timestamp(asof)
    cw = crosswalk[crosswalk['filing_date'] <= asof_ts].sort_values(['issuer_cik','filing_date'])
    # PIT rule: latest observed mapping date on/before the 13F report date; retain all CUSIPs tied on that latest date.
    latest = cw.groupby('issuer_cik', as_index=False)['filing_date'].max()
    cw = cw.merge(latest, on=['issuer_cik','filing_date'], how='inner')
    cik_cusips = cw.groupby('issuer_cik')['cusip'].apply(set).to_dict()
    matched = {}; ambiguous = []; no_cw = []
    for c in candidates:
        target = norm(c['name']); issuer_set = name_cusips.get(target, set())
        allowed = cik_cusips.get(c['cik'], set())
        inter = sorted(issuer_set & allowed)
        if len(inter) == 1:
            matched[c['ticker']] = {'method':'pit_cik_cusip_intersection','issuer_name':target,'cusip':inter[0]}
        elif len(inter) > 1:
            ambiguous.append({'ticker':c['ticker'],'issuer_name':target,'candidate_cusips':inter,'reason':'multiple PIT CUSIPs'})
        elif not allowed:
            no_cw.append({'ticker':c['ticker'],'issuer_name':target,'reason':'no PIT CIK-CUSIP mapping as of report date'})
        else:
            # Former-name matching is deliberately not used here; this audit measures the independent identifier path.
            ambiguous.append({'ticker':c['ticker'],'issuer_name':target,'candidate_cusips':sorted(issuer_set),'pit_cusips':sorted(allowed),'reason':'no CUSIP intersection'})
    return {
        'asof': asof,
        'historical_unique_issuers': int(holdings['issuer_norm'].nunique()),
        'candidate_universe': len(candidates),
        'matched_candidates': len(matched),
        'coverage_rate': len(matched)/len(candidates) if candidates else 0,
        'ambiguous_candidates': len(ambiguous),
        'no_crosswalk_candidates': len(no_cw),
        'mapping_examples': list(matched.items())[:25],
        'ambiguous_examples': ambiguous[:25],
        'no_crosswalk_examples': no_cw[:25],
    }

def main():
    universe = load_sec_universe(); frozen = load_frozen()
    candidates = [x for x in universe if x['ticker'] in frozen]
    ciks = {x['cik'] for x in candidates}
    cw = load_crosswalk(ciks)
    audit = {
        'phase':'22C_SEC_13F_PIT_CUSIP_CROSSWALK_AUDIT_V7',
        'frozen_universe':len(frozen), 'sec_current_matches':len(candidates),
        'crosswalk_rows_for_candidate_ciks':len(cw),
        'crosswalk_source':CROSSWALK,
        'crosswalk_pit_rule':'latest CIK-CUSIP filing on/before 13F report date; no future mapping allowed',
        'datasets':{}
    }
    for label,(url,asof) in DATASETS.items():
        audit['datasets'][label] = audit_dataset(get(url), candidates, cw, asof)
    rates = [v['coverage_rate'] for v in audit['datasets'].values()]
    audit['minimum_coverage'] = min(rates) if rates else 0
    audit['conclusion'] = 'PROCEED_TO_13F_SIGNAL_BUILD' if rates and min(rates) >= 0.90 else 'CUSIP_CROSSWALK_NEEDS_FURTHER_RESOLUTION'
    (OUT/'phase22c_cusip_crosswalk_summary_v7.json').write_text(json.dumps(audit, indent=2, default=str), encoding='utf-8')
    print(json.dumps(audit, indent=2, default=str))

if __name__ == '__main__': main()

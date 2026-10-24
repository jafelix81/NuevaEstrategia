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

def issuer_and_columns(z):
    for n in z.namelist():
        if n.upper().endswith('INFOTABLE.TSV'):
            with z.open(n) as f: head = pd.read_csv(f, sep='\t', dtype=str, nrows=0)
            cols = {c.lower(): c for c in head.columns}
            issuer = cols.get('nameofissuer') or cols.get('nameissuer') or cols.get('name')
            cusip = cols.get('cusip')
            title = cols.get('titleofclass') or cols.get('titleofclass')
            putcall = cols.get('putcall')
            value = cols.get('value') or cols.get('marketvalue')
            if not issuer or not cusip: raise RuntimeError(f'Missing issuer/CUSIP columns: {head.columns.tolist()}')
            return n, issuer, cusip, title, putcall, value
    raise RuntimeError('INFOTABLE.TSV not found')

def is_equity_title(s):
    x = norm(s)
    bad = ('OPTION','WARRANT','RIGHT','BOND','NOTE','DEBENTURE','PREFERRED','PREF ','UNIT','FUND','ETF','ETN','ADR PREFERRED')
    return bool(x) and not any(b in x for b in bad)

def load_13f_issuer_cusips(raw):
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        info, issuer_col, cusip_col, title_col, putcall_col, value_col = issuer_and_columns(z)
        stats = {}
        usecols = [issuer_col, cusip_col] + ([title_col] if title_col else []) + ([putcall_col] if putcall_col else []) + ([value_col] if value_col else [])
        usecols = list(dict.fromkeys(usecols))
        with z.open(info) as f:
            for chunk in pd.read_csv(f, sep='\t', dtype=str, usecols=usecols, chunksize=200000):
                chunk['issuer_norm'] = chunk[issuer_col].fillna('').map(norm)
                chunk['cusip_norm'] = chunk[cusip_col].fillna('').str.replace(r'[^0-9A-Z]', '', regex=True).str.upper()
                if title_col:
                    equity = chunk[title_col].fillna('').map(is_equity_title)
                else:
                    equity = pd.Series(True, index=chunk.index)
                if putcall_col:
                    equity &= chunk[putcall_col].fillna('').str.strip().eq('')
                chunk = chunk[equity & chunk['issuer_norm'].ne('') & chunk['cusip_norm'].ne('')]
                if chunk.empty: continue
                vals = pd.to_numeric(chunk[value_col], errors='coerce').fillna(0) if value_col else pd.Series(1, index=chunk.index)
                for (issuer, cusip), sub in chunk.groupby(['issuer_norm','cusip_norm']):
                    d = stats.setdefault(issuer, {}).setdefault(cusip, {'rows':0,'value':0.0})
                    d['rows'] += len(sub); d['value'] += float(vals.loc[sub.index].sum())
    out = {}
    for issuer, by_cusip in stats.items():
        ranked = sorted(by_cusip.items(), key=lambda kv: (kv[1]['value'], kv[1]['rows']), reverse=True)
        out[issuer] = ranked
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
    issuer_stats = load_13f_issuer_cusips(raw)
    matched, ambiguous, missing = {}, [], []
    for c in candidates:
        names = [norm(c['name'])] + [norm(x) for x in former_names.get(c['cik'], [])]
        hits = {}
        hit_names = []
        for name in names:
            ranked = issuer_stats.get(name, [])
            if ranked:
                hit_names.append(name)
                for cusip, stat in ranked: hits[cusip] = hits.get(cusip, {'rows':0,'value':0.0}) | stat
        if not hits:
            missing.append({'ticker':c['ticker'],'issuer_name':c['name'],'reason':'no exact normalized issuer/former-name hit among non-derivative equity rows'})
            continue
        ranked = sorted(hits.items(), key=lambda kv:(kv[1]['value'],kv[1]['rows']), reverse=True)
        top_cusip, top = ranked[0]
        total_rows = sum(x['rows'] for _,x in ranked); total_value = sum(x['value'] for _,x in ranked)
        row_share = top['rows']/total_rows if total_rows else 0
        value_share = top['value']/total_value if total_value else 0
        if len(ranked) == 1 or (row_share >= 0.90 and value_share >= 0.90):
            matched[c['ticker']] = {'method':'pit_13f_common_equity_dominant_cusip','issuer_names_used':sorted(set(hit_names)),'cusip':top_cusip,'candidate_cusips':len(ranked),'row_share':row_share,'value_share':value_share}
        else:
            ambiguous.append({'ticker':c['ticker'],'issuer_names_used':sorted(set(hit_names)),'candidate_cusips':[x[0] for x in ranked[:15]],'row_share_top':row_share,'value_share_top':value_share,'reason':'multiple common-equity CUSIPs/classes remain materially represented'})
    return {'asof':asof,'historical_unique_issuers':len(issuer_stats),'candidate_universe':len(candidates),'matched_candidates':len(matched),'coverage_rate':len(matched)/len(candidates) if candidates else 0,'ambiguous_candidates':len(ambiguous),'no_crosswalk_candidates':len(missing),'mapping_examples':list(matched.items())[:25],'ambiguous_examples':ambiguous[:25],'no_crosswalk_examples':missing[:25]}

def main():
    universe = load_sec_universe(); frozen = load_frozen(); candidates = [x for x in universe if x['ticker'] in frozen]
    former = load_former_names(candidates)
    audit={'phase':'22C_SEC_13F_PIT_ISSUER_CUSIP_AUDIT_V9','frozen_universe':len(frozen),'sec_current_matches':len(candidates),'mapping_source':'report-date 13F INFOTABLE issuer/CUSIP pairs restricted to non-derivative equity rows; SEC formerNames expand issuer identity','pit_rule':'mapping is derived only from the report-date 13F dataset; no future CUSIP is injected','resolution_rule':'unique common-equity CUSIP or dominant candidate >=90% of rows and >=90% of reported value; otherwise ambiguous','datasets':{}}
    for label,(url,asof) in DATASETS.items(): audit['datasets'][label]=audit_dataset(get(url,timeout=240),candidates,former,asof)
    rates=[v['coverage_rate'] for v in audit['datasets'].values()]; audit['minimum_coverage']=min(rates) if rates else 0
    audit['conclusion']='PROCEED_TO_13F_SIGNAL_BUILD' if rates and min(rates)>=0.90 else '13F_IDENTITY_MAPPING_NEEDS_FURTHER_RESOLUTION'
    (OUT/'phase22c_pit_issuer_cusip_summary_v9.json').write_text(json.dumps(audit,indent=2),encoding='utf-8'); print(json.dumps(audit,indent=2))
if __name__=='__main__': main()

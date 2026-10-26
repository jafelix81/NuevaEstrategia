import io, json, re, time, zipfile
from pathlib import Path
import requests
import pandas as pd

OUT = Path('nueva_estrategia_phase39_sec_form4_audit')
OUT.mkdir(exist_ok=True)
HEADERS = {'User-Agent': 'NuevaEstrategia research research@example.com'}
SEC_PAGE = 'https://www.sec.gov/data-research/sec-markets-data/insider-transactions-data-sets'
SEC_TICKERS = 'https://www.sec.gov/files/company_tickers_exchange.json'
QUARTERS = ['2016 Q1', '2020 Q1', '2024 Q1', '2026 Q3']


def get(url, timeout=180):
    r = requests.get(url, headers=HEADERS, timeout=timeout)
    r.raise_for_status()
    return r.content


def get_text(url, timeout=60):
    r = requests.get(url, headers=HEADERS, timeout=timeout)
    r.raise_for_status()
    return r.text


def norm_ticker(x):
    return str(x).upper().strip()


def load_frozen():
    src = Path('Nueva_Estrategia_Fase0_Descubrimiento.py').read_text(encoding='utf-8')
    block = src.split('DEFAULT_UNIVERSE = [', 1)[1].split(']\n', 1)[0]
    return sorted(set(re.findall(r"'([A-Z0-9.\-]+)'", block)))


def load_sec_ciks():
    payload = json.loads(get(SEC_TICKERS).decode())
    fields = payload['fields']
    pos = {str(f).lower(): i for i, f in enumerate(fields)}
    out = {}
    for row in payload['data']:
        if len(row) < len(fields):
            continue
        t = norm_ticker(row[pos['ticker']])
        if t:
            out[t] = str(row[pos['cik']]).zfill(10)
    return out


def dataset_links():
    html = get_text(SEC_PAGE)
    # The SEC page exposes quarter labels as link text; retain only ZIP links.
    links = {}
    for m in re.finditer(r'href=[\"\']([^\"\']+)[\"\'][^>]*>\s*([^<]+?)\s*</a>', html, flags=re.I):
        href, text = m.group(1), re.sub(r'\s+', ' ', m.group(2)).strip()
        if 'ZIP' in text.upper() or re.search(r'\b20\d{2}\s+Q[1-4]\b', text, re.I):
            q = re.search(r'\b(20\d{2}\s+Q[1-4])\b', text, re.I)
            if q:
                url = href if href.startswith('http') else 'https://www.sec.gov' + href
                links[q.group(1).upper()] = url
    missing = [q for q in QUARTERS if q not in links]
    if missing:
        raise RuntimeError(f'SEC quarter links not found: {missing}; page format may have changed')
    return {q: links[q] for q in QUARTERS}


def find_member(z, needle):
    for n in z.namelist():
        if needle in n.upper() and n.upper().endswith(('.TXT', '.TSV')):
            return n
    raise RuntimeError(f'{needle} member not found; members={z.namelist()[:20]}')


def audit_quarter(raw, frozen, ciks):
    target_ciks = {ciks[t]: t for t in frozen if t in ciks}
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        sub = find_member(z, 'SUBMISSION')
        cols = pd.read_csv(z.open(sub), sep='\t', dtype=str, nrows=0).columns.tolist()
        required = {'ACCESSION_NUMBER', 'FILING_DATE', 'DOCUMENT_TYPE', 'ISSUERCIK', 'ISSUERTRADINGSYMBOL'}
        if not required.issubset(cols):
            raise RuntimeError(f'Unexpected SUBMISSION columns: {cols}')
        keep = list(required)
        rows = []
        for chunk in pd.read_csv(z.open(sub), sep='\t', dtype=str, usecols=keep, chunksize=100000):
            chunk['ISSUERCIK'] = chunk['ISSUERCIK'].astype(str).str.zfill(10)
            x = chunk[chunk['ISSUERCIK'].isin(target_ciks)].copy()
            if not x.empty:
                x['TICKER_CURRENT'] = x['ISSUERCIK'].map(target_ciks)
                rows.append(x)
        df = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame(columns=keep + ['TICKER_CURRENT'])
        if df.empty:
            return {'rows': 0, 'covered': 0, 'coverage_rate': 0.0, 'form4_rows': 0, 'form4_tickers': 0, 'sample_accessions': []}
        form4 = df[df['DOCUMENT_TYPE'].isin(['4', '4/A'])].copy()
        covered = sorted(df['TICKER_CURRENT'].dropna().unique())
        form4_tickers = sorted(form4['TICKER_CURRENT'].dropna().unique())
        sample = form4[['ACCESSION_NUMBER','ISSUERCIK','TICKER_CURRENT','FILING_DATE']].drop_duplicates().head(25).to_dict('records')
        return {
            'rows': int(len(df)),
            'covered': len(covered),
            'coverage_rate': len(covered) / len(frozen),
            'form4_rows': int(len(form4)),
            'form4_tickers': len(form4_tickers),
            'form4_coverage_rate': len(form4_tickers) / len(frozen),
            'sample_accessions': sample,
            'covered_tickers_sample': covered[:30],
        }


def acceptance_datetime_sample(samples):
    out = []
    for s in samples[:12]:
        acc = str(s['ACCESSION_NUMBER'])
        cik = str(s['ISSUERCIK']).lstrip('0') or '0'
        accession_compact = acc.replace('-', '')
        url = f'https://www.sec.gov/Archives/edgar/data/{int(cik):d}/{accession_compact}/{acc}.txt'
        try:
            text = get_text(url, timeout=30)
            m = re.search(r'ACCEPTANCE-DATETIME:\s*(\d{14})', text)
            out.append({**s, 'acceptance_datetime': m.group(1) if m else None, 'acceptance_url_ok': True})
        except Exception as e:
            out.append({**s, 'acceptance_datetime': None, 'acceptance_url_ok': False, 'error': str(e)})
        time.sleep(0.12)
    return out


def main():
    frozen = load_frozen()
    ciks = load_sec_ciks()
    links = dataset_links()
    audit = {
        'phase': '39_SEC_FORM4_INSIDER_FEASIBILITY',
        'frozen_universe': len(frozen),
        'sec_current_cik_matches': sum(t in ciks for t in frozen),
        'quarters': {},
        'pit': {},
        'conclusion': None,
    }
    all_samples = []
    for q, url in links.items():
        raw = get(url, timeout=180)
        result = audit_quarter(raw, frozen, ciks)
        audit['quarters'][q] = {'url': url, **result}
        all_samples.extend(result.get('sample_accessions', []))
    pit = acceptance_datetime_sample(all_samples)
    audit['pit'] = {
        'sampled_filings': len(pit),
        'acceptance_datetime_found': sum(x.get('acceptance_datetime') is not None for x in pit),
        'filing_date_present': sum(bool(x.get('FILING_DATE')) for x in pit),
        'examples': pit[:12],
        'interpretation': 'SEC insider datasets provide filing dates but not filing-time-of-day; EDGAR submission headers expose ACCEPTANCE-DATETIME and should be used for transaction-level PIT when reconstructing signals.',
    }
    rates = [v['form4_coverage_rate'] for v in audit['quarters'].values()]
    audit['coverage_min_form4'] = min(rates) if rates else 0.0
    audit['coverage_min_all_forms'] = min(v['coverage_rate'] for v in audit['quarters'].values()) if audit['quarters'] else 0.0
    audit['conclusion'] = 'PROCEED_TO_PIT_TRANSACTION_FILTER_AUDIT' if rates and min(rates) >= 0.90 and audit['pit']['acceptance_datetime_found'] >= 8 else 'INSUFFICIENT_COVERAGE_OR_PIT_EVIDENCE'
    (OUT / 'phase39_sec_form4_summary.json').write_text(json.dumps(audit, indent=2), encoding='utf-8')
    print(json.dumps(audit, indent=2))


if __name__ == '__main__':
    main()

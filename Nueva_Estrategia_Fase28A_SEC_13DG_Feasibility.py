import ast, json, os, time, gzip
from collections import Counter, defaultdict
from datetime import datetime, timezone
from urllib.request import Request, urlopen

BASE_SOURCE = 'Nueva_Estrategia_Fase0_Descubrimiento.py'
OUT = 'nueva_estrategia_phase28a_sec_13dg'
SEC_TICKERS = 'https://www.sec.gov/files/company_tickers.json'
SUB_URL = 'https://data.sec.gov/submissions/CIK{cik}.json'
HEADERS = {'User-Agent': 'NuevaEstrategia research research@example.com', 'Accept-Encoding': 'gzip, deflate'}
TARGET_FORMS = {'SC 13D','SC 13G','SC 13D/A','SC 13G/A'}


def universe():
    tree = ast.parse(open(BASE_SOURCE, encoding='utf-8').read())
    for n in tree.body:
        if isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Name) and t.id == 'DEFAULT_UNIVERSE':
                    u = sorted(set(str(x).strip().upper() for x in ast.literal_eval(n.value)))
                    if len(u) != 335:
                        raise RuntimeError(f'Expected frozen 335 universe, got {len(u)}')
                    return u
    raise RuntimeError('DEFAULT_UNIVERSE not found')


def get(url):
    req = Request(url, headers=HEADERS)
    with urlopen(req, timeout=60) as r:
        raw = r.read()
        encoding = (r.headers.get('Content-Encoding') or '').lower()
        if encoding == 'gzip' or raw[:2] == b'\x1f\x8b':
            raw = gzip.decompress(raw)
        return json.loads(raw.decode('utf-8'))


def main():
    os.makedirs(OUT, exist_ok=True)
    tickers = universe()
    company = get(SEC_TICKERS)
    by_ticker = {}
    for row in company.values():
        t = str(row.get('ticker','')).strip().upper()
        cik = str(row.get('cik_str','')).zfill(10)
        if t and t not in by_ticker:
            by_ticker[t] = cik

    mapped = {t: by_ticker[t] for t in tickers if t in by_ticker}
    missing = [t for t in tickers if t not in by_ticker]
    stats = Counter()
    form_counts = Counter()
    first_dates = {}
    last_dates = {}
    filing_examples = defaultdict(list)
    errors = []

    for idx, (ticker, cik) in enumerate(sorted(mapped.items()), 1):
        try:
            data = get(SUB_URL.format(cik=cik))
            recent = data.get('filings', {}).get('recent', {})
            forms = recent.get('form', [])
            dates = recent.get('filingDate', [])
            accessions = recent.get('accessionNumber', [])
            docs = recent.get('primaryDocument', [])
            for i, form in enumerate(forms):
                if form not in TARGET_FORMS:
                    continue
                stats['target_filings_recent'] += 1
                form_counts[form] += 1
                d = dates[i] if i < len(dates) else ''
                acc = accessions[i] if i < len(accessions) else ''
                doc = docs[i] if i < len(docs) else ''
                if d:
                    first_dates[ticker] = min(first_dates.get(ticker, d), d)
                    last_dates[ticker] = max(last_dates.get(ticker, d), d)
                if len(filing_examples[ticker]) < 5:
                    filing_examples[ticker].append({'form': form, 'filing_date': d, 'accession': acc, 'primary_document': doc})
            stats['companies_checked'] += 1
        except Exception as e:
            errors.append({'ticker': ticker, 'cik': cik, 'error': str(e)})
            stats['errors'] += 1
        if idx % 25 == 0:
            time.sleep(0.2)

    payload = {
        'phase': '28A',
        'status': 'COMPLETE',
        'purpose': 'Historical feasibility audit of SEC Schedule 13D/13G beneficial-ownership filings as a potential institutional/activist smart-money source.',
        'hypothesis': 'Large beneficial-ownership changes may contain information beyond frozen LTM/F80, but this is only a hypothesis and no alpha is inferred from filing frequency.',
        'frozen_universe_size': len(tickers),
        'mapping_source': SEC_TICKERS,
        'mapped_universe': len(mapped),
        'missing_universe': missing,
        'companies_checked': stats['companies_checked'],
        'errors': errors,
        'target_forms': sorted(TARGET_FORMS),
        'recent_target_filings': stats['target_filings_recent'],
        'form_counts': dict(form_counts),
        'tickers_with_recent_13dg': len(first_dates),
        'first_recent_filing_by_ticker': first_dates,
        'last_recent_filing_by_ticker': last_dates,
        'filing_examples': dict(filing_examples),
        'pit_rule_for_future_research': 'Use filingDate as minimum public-availability date; never use report/transaction dates as knowledge dates. Amendments must be handled chronologically and same-day availability assumptions must be explicit.',
        'selection_rule_for_future_research': 'Do not trade merely on filing presence. Future signal candidates must be defined ex ante from ownership percentage/change, filer type/relationship, and amendment status, then tested chronologically.',
        'alpha_status': 'NOT_TESTED',
        'audit_timestamp_utc': datetime.now(timezone.utc).isoformat(),
    }
    with open(os.path.join(OUT, 'phase28a_sec_13dg_feasibility.json'), 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=2)
    print(json.dumps({
        'phase':'28A', 'status':'COMPLETE', 'mapped_universe':len(mapped),
        'recent_target_filings':stats['target_filings_recent'], 'tickers_with_recent_13dg':len(first_dates),
        'errors':stats['errors'], 'alpha_status':'NOT_TESTED'
    }, indent=2))

if __name__ == '__main__':
    main()

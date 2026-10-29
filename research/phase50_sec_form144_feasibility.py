import ast, gzip, io, json, os, re, time
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_SOURCE = 'Nueva_Estrategia_Fase0_Descubrimiento.py'
SEC_TICKERS_URL = 'https://www.sec.gov/files/company_tickers.json'
EFTS_URL = 'https://efts.sec.gov/LATEST/search-index'
SEC_ARCHIVES = 'https://www.sec.gov/Archives/edgar/data'
OUT_DIR = 'phase50_sec_form144_feasibility'
HEADERS = {
    'User-Agent': 'NuevaEstrategia research research@example.com',
    'Accept-Encoding': 'gzip, deflate',
}
START_DATE = '2023-04-13'
END_DATE = '2026-10-29'
MIN_COVERAGE = 0.95
SAMPLE_ISSUERS = 25


def get_bytes(url, retries=8, timeout=60):
    last = None
    for attempt in range(retries):
        try:
            req = Request(url, headers=HEADERS)
            with urlopen(req, timeout=timeout) as r:
                raw = r.read()
                enc = (r.headers.get('Content-Encoding') or '').lower()
                if enc == 'gzip' or raw[:2] == b'\x1f\x8b':
                    raw = gzip.decompress(raw)
                return raw
        except HTTPError as e:
            last = e
            if e.code in (429, 500, 502, 503, 504):
                time.sleep(min(30, 2 ** attempt))
                continue
            raise
        except (URLError, TimeoutError, OSError) as e:
            last = e
            time.sleep(min(20, 2 ** attempt))
    raise RuntimeError(f'GET failed: {url}: {last}')


def get_json(url):
    return json.loads(get_bytes(url).decode('utf-8'))


def frozen_universe():
    tree = ast.parse(open(BASE_SOURCE, encoding='utf-8').read())
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == 'DEFAULT_UNIVERSE':
                    u = sorted(set(str(x).strip().upper() for x in ast.literal_eval(node.value)))
                    if len(u) != 335:
                        raise RuntimeError(f'Expected 335-name frozen universe, got {len(u)}')
                    return u
    raise RuntimeError('DEFAULT_UNIVERSE not found')


def norm_cik(x):
    if x in (None, ''):
        return None
    return str(x).strip().zfill(10)


def search_issuer(cik):
    params = {
        'forms': '144',
        'ciks': cik,
        'startdt': START_DATE,
        'enddt': END_DATE,
        'from': 0,
        'size': 1,
    }
    url = EFTS_URL + '?' + urlencode(params)
    data = get_json(url)
    hits = data.get('hits', {})
    total = hits.get('total', {})
    if isinstance(total, dict):
        total = total.get('value', 0)
    return {'cik': cik, 'count': int(total or 0), 'sample_hit': (hits.get('hits') or [None])[0]}


def sample_records(rows):
    eligible = [r for r in rows if r.get('count', 0) > 0 and r.get('sample_hit')]
    if not eligible:
        return []
    eligible.sort(key=lambda r: r['cik'])
    if len(eligible) <= SAMPLE_ISSUERS:
        return eligible
    idx = [round(i * (len(eligible)-1)/(SAMPLE_ISSUERS-1)) for i in range(SAMPLE_ISSUERS)]
    return [eligible[i] for i in sorted(set(idx))]


def hit_source(hit):
    return (hit or {}).get('_source') or (hit or {}).get('source') or {}


def hit_accession(hit):
    s = hit_source(hit)
    for k in ('accession_no', 'accession_number', 'adsh'):
        v = s.get(k) if isinstance(s, dict) else None
        if v:
            return str(v).replace('-', '') if '-' in str(v) else str(v)
    for k in ('_id', 'id'):
        v = (hit or {}).get(k)
        if v and re.fullmatch(r'\d{10}-\d{2}-\d{6}', str(v)):
            return str(v).replace('-', '')
    return None


def hit_ciks(hit):
    s = hit_source(hit)
    vals = s.get('ciks') if isinstance(s, dict) else None
    if isinstance(vals, list):
        return [norm_cik(v) for v in vals if norm_cik(v)]
    if isinstance(vals, str):
        return [norm_cik(v) for v in re.split(r'[,; ]+', vals) if norm_cik(v)]
    return []


def download_index_and_xml(hit):
    accession = hit_accession(hit)
    ciks = hit_ciks(hit)
    if not accession or not ciks:
        return {'ok': False, 'reason': 'missing_accession_or_ciks', 'hit_keys': sorted((hit or {}).keys()), 'source_keys': sorted(hit_source(hit).keys()) if isinstance(hit_source(hit), dict) else []}
    acc_dashed = accession[:10] + '-' + accession[10:12] + '-' + accession[12:]
    tried = []
    for cik in ciks:
        cik_path = str(int(cik))
        index_url = f'{SEC_ARCHIVES}/{cik_path}/{accession}/{acc_dashed}-index.html'
        try:
            index = get_bytes(index_url).decode('utf-8', errors='replace')
            xml_names = re.findall(r'href=[\"\']([^\"\']+primary_doc\.xml)[\"\']', index, flags=re.I)
            xml_url = None
            if xml_names:
                name = xml_names[0]
                if name.startswith('http'):
                    xml_url = name
                else:
                    xml_url = f'{SEC_ARCHIVES}/{cik_path}/{accession}/{name.lstrip("./")}'
            if not xml_url:
                xml_url = f'{SEC_ARCHIVES}/{cik_path}/{accession}/primary_doc.xml'
            xml = get_bytes(xml_url).decode('utf-8', errors='replace')
            return {'ok': True, 'index_url': index_url, 'xml_url': xml_url, 'xml': xml, 'accession': acc_dashed, 'filer_cik': cik}
        except Exception as e:
            tried.append({'cik': cik, 'error': str(e)})
    return {'ok': False, 'reason': 'archive_download_failed', 'accession': acc_dashed, 'tried': tried}


def field_presence(xml):
    x = xml.lower()
    fields = {
        'issuer_cik': [r'<issuercik>', r'issuer cik'],
        'issuer_name': [r'<issuername>', r'issuer name'],
        'security_title': [r'<securitytitle>', r'security title'],
        'shares_to_be_sold': [r'<unitstosold>', r'<unitstobesold>', r'units to be sold', r'shares to be sold'],
        'aggregate_market_value': [r'<aggregatemarketvalue>', r'aggregate market value'],
        'proposed_sale_date': [r'<approxsaledate>', r'approx sale date', r'approximate sale date'],
        'acquisition_date': [r'<securitiesacquireddate>', r'securities acquired date'],
        'nature_of_acquisition': [r'<natureofacquisition>', r'nature of acquisition'],
        'broker': [r'<broker>', r'broker'],
        'acceptance_datetime_header': [r'<acceptance-datetime>', r'acceptance-datetime'],
    }
    return {k: any(re.search(p, x) for p in pats) for k, pats in fields.items()}


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    universe = frozen_universe()
    sec = get_json(SEC_TICKERS_URL)
    sec_map = {}
    for row in sec.values():
        t = str(row.get('ticker', '')).strip().upper()
        if t:
            sec_map[t] = norm_cik(row.get('cik_str'))

    mapping = [{'ticker': t, 'cik': sec_map.get(t)} for t in universe]
    mapped = [r for r in mapping if r['cik']]
    unmapped = [r['ticker'] for r in mapping if not r['cik']]

    results = []
    errors = []
    # Conservative SEC request rate: two workers and retries; no broad parallel burst.
    with ThreadPoolExecutor(max_workers=2) as ex:
        futs = {ex.submit(search_issuer, r['cik']): r['ticker'] for r in mapped}
        for fut in as_completed(futs):
            ticker = futs[fut]
            try:
                r = fut.result()
                r['ticker'] = ticker
                results.append(r)
            except Exception as e:
                errors.append({'ticker': ticker, 'error': str(e)})

    covered = [r for r in results if r['count'] > 0]
    coverage = len(covered) / len(mapped) if mapped else 0.0
    sample = []
    for r in sample_records(results):
        doc = download_index_and_xml(r['sample_hit'])
        fields = field_presence(doc['xml']) if doc.get('ok') else {}
        sample.append({
            'ticker': r['ticker'], 'cik': r['cik'], 'filing_count': r['count'],
            'download_ok': doc.get('ok', False), 'accession': doc.get('accession'),
            'index_url': doc.get('index_url'), 'xml_url': doc.get('xml_url'),
            'field_presence': fields, 'download_reason': doc.get('reason'),
            'download_error_detail': doc.get('tried'),
        })

    field_rates = {}
    if sample:
        for field in next(iter(sample)) and sorted(set(k for s in sample for k in s.get('field_presence', {}))):
            vals = [s.get('field_presence', {}).get(field, False) for s in sample if s.get('download_ok')]
            if vals:
                field_rates[field] = sum(vals) / len(vals)

    # Filing counts are discovery/coverage diagnostics only. Absence of Form 144 is not interpreted as a zero event.
    gate = (
        len(mapped) >= 300 and
        coverage >= MIN_COVERAGE and
        len(errors) == 0 and
        bool(sample) and
        all(s.get('download_ok') for s in sample) and
        all(rate >= 0.95 for rate in field_rates.values())
    )

    summary = {
        'phase': '50',
        'source': 'SEC EDGAR Form 144',
        'status': 'COMPLETE',
        'electronic_compliance_start': START_DATE,
        'end_date': END_DATE,
        'frozen_universe': len(universe),
        'current_sec_cik_mapped': len(mapped),
        'current_sec_cik_unmapped': len(unmapped),
        'unmapped_tickers': unmapped,
        'issuers_with_form144_hits': len(covered),
        'issuer_hit_coverage_among_current_cik_mapped': coverage,
        'query_errors': len(errors),
        'query_error_samples': errors[:10],
        'sample_size': len(sample),
        'sample': sample,
        'field_presence_rates': field_rates,
        'knowledge_rule': 'SEC acceptance datetime / filing dissemination is the PIT availability timestamp; proposed sale date is an event attribute, never the information timestamp.',
        'economic_hypothesis': 'Form 144 proposed sales may contain incremental information about planned insider/affiliate supply; no directional sign is assumed a priori.',
        'gate_rule': 'Feasibility only: >=95% issuer coverage among current SEC-mapped frozen names, zero query errors, and complete actual-XML field sample. No alpha testing until a separate PIT issuer/security identity audit passes.',
        'gate': 'PASS' if gate else 'FAIL',
        'alpha_authorized': False,
        'next_step': 'If PASS, run historical PIT issuer/security identity and filing-field completeness audit, then pre-register a small proposed-sale intensity feature set. If FAIL, archive as infeasible without alpha testing.'
    }
    with open(os.path.join(OUT_DIR, 'summary.json'), 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    with open(os.path.join(OUT_DIR, 'issuer_results.json'), 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    print(json.dumps(summary, indent=2))
    if not gate:
        raise SystemExit(1)


if __name__ == '__main__':
    main()

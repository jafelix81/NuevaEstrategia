import ast, json, os, time, gzip
from urllib.request import Request, urlopen
from urllib.error import HTTPError

BASE_SOURCE = 'Nueva_Estrategia_Fase0_Descubrimiento.py'
MAPPER_URL = 'https://raw.githubusercontent.com/jadchaar/sec-cik-mapper/main/mappings/stocks/ticker_to_cik.json'
SEC_TICKERS_URL = 'https://www.sec.gov/files/company_tickers.json'
OUT_DIR = 'phase49_sec_13dg_historical_identity_audit'
HEADERS = {'User-Agent': 'NuevaEstrategia research research@example.com', 'Accept-Encoding': 'gzip, deflate'}


def get_json(url, retries=7):
    err = None
    for attempt in range(retries):
        try:
            with urlopen(Request(url, headers=HEADERS), timeout=60) as r:
                raw = r.read()
                if (r.headers.get('Content-Encoding') or '').lower() == 'gzip' or raw[:2] == b'\x1f\x8b':
                    raw = gzip.decompress(raw)
                return json.loads(raw.decode('utf-8'))
        except HTTPError as e:
            err = e
            if e.code == 404:
                raise
            if e.code in (429, 500, 502, 503, 504):
                time.sleep(min(30, 2 ** attempt))
                continue
            raise
        except Exception as e:
            err = e
            time.sleep(min(20, 2 ** attempt))
    raise RuntimeError(f'GET failed: {url}: {err}')


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


def main():
    universe = frozen_universe()
    sec = get_json(SEC_TICKERS_URL)
    mapper = get_json(MAPPER_URL)
    sec_map = {}
    for row in sec.values():
        t = str(row.get('ticker', '')).strip().upper()
        if t:
            sec_map[t] = norm_cik(row.get('cik_str'))

    rows = []
    for ticker in universe:
        sec_cik = sec_map.get(ticker)
        hist_cik = norm_cik(mapper.get(ticker)) if isinstance(mapper, dict) else None
        if sec_cik and hist_cik and sec_cik == hist_cik:
            status = 'AGREE'
            cik = sec_cik
            source = 'SEC_CURRENT+HISTORICAL_MAPPER'
        elif sec_cik:
            status = 'SEC_ONLY'
            cik = sec_cik
            source = 'SEC_CURRENT'
        elif hist_cik:
            status = 'HISTORICAL_MAPPER_ONLY'
            cik = hist_cik
            source = 'HISTORICAL_MAPPER'
        else:
            status = 'UNRESOLVED'
            cik = None
            source = 'NONE'
        rows.append({'ticker': ticker, 'sec_current_cik': sec_cik, 'historical_mapper_cik': hist_cik, 'selected_cik': cik, 'status': status, 'source': source})

    agree = sum(r['status'] == 'AGREE' for r in rows)
    sec_only = sum(r['status'] == 'SEC_ONLY' for r in rows)
    mapper_only = sum(r['status'] == 'HISTORICAL_MAPPER_ONLY' for r in rows)
    unresolved = [r['ticker'] for r in rows if r['status'] == 'UNRESOLVED']
    mapped = len(universe) - len(unresolved)
    mapping_coverage = mapped / len(universe)
    dual_source_coverage = agree / len(universe)
    disagreement = [r for r in rows if r['sec_current_cik'] and r['historical_mapper_cik'] and r['sec_current_cik'] != r['historical_mapper_cik']]

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, 'crosswalk.json'), 'w', encoding='utf-8') as f:
        json.dump(rows, f, indent=2)
    summary = {
        'phase': '49',
        'status': 'COMPLETE',
        'frozen_universe': len(universe),
        'mapped_cik': mapped,
        'mapping_coverage': mapping_coverage,
        'dual_source_agreement': agree,
        'dual_source_agreement_rate': dual_source_coverage,
        'sec_only': sec_only,
        'historical_mapper_only': mapper_only,
        'unresolved': len(unresolved),
        'unresolved_tickers': unresolved,
        'source_disagreements': len(disagreement),
        'source_disagreement_tickers': [r['ticker'] for r in disagreement],
        'knowledge_rule': 'CIK mapping is identity discovery only; no filing event date or transaction date is used as availability information.',
        'alpha_authorized': False,
        'gate_rule': 'Alpha testing requires >=95% frozen-universe issuer identity coverage and zero unresolved source disagreements for the mapped set; no universe shrinkage is permitted.',
        'gate': 'PASS' if mapping_coverage >= 0.95 and not disagreement else 'FAIL',
        'next_step': 'If FAIL, do not test 13D/13G alpha; continue identity resolution or pivot to another feasible source. If PASS, run a separate PIT filing-coverage audit before alpha.'
    }
    with open(os.path.join(OUT_DIR, 'summary.json'), 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary, indent=2))
    if summary['gate'] != 'PASS':
        raise SystemExit(1)


if __name__ == '__main__':
    main()

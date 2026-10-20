import io
import json
import re
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

OUT = Path('nueva_estrategia_phase22_sec_13f_feasibility')
OUT.mkdir(exist_ok=True)
SEC_PAGE = 'https://www.sec.gov/data-research/sec-markets-data/form-13f-data-sets'
SEC_SUB = 'https://data.sec.gov/submissions/CIK0001081198.json'
HEADERS = {'User-Agent': 'NuevaEstrategia research contact research@example.com'}
TIMEOUT = 60


def get(url):
    r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    r.raise_for_status()
    return r


def main():
    audit = {
        'phase': '22_SEC_13F_FEASIBILITY',
        'started_utc': datetime.now(timezone.utc).isoformat(),
        'source': SEC_PAGE,
        'status': 'RUNNING',
        'historical_quarters_found': [],
        'download_tests': [],
        'point_in_time_sample': None,
        'mapping_assessment': {},
        'conclusion': None,
    }
    html = get(SEC_PAGE).text
    soup = BeautifulSoup(html, 'html.parser')
    links = []
    for a in soup.find_all('a', href=True):
        href = a['href']
        text = ' '.join(a.get_text(' ', strip=True).split())
        if '.zip' in href.lower() and '13f' in (href.lower() + text.lower()):
            if href.startswith('/'):
                href = 'https://www.sec.gov' + href
            links.append({'label': text, 'url': href})
    # Preserve page order and remove duplicates.
    seen = set()
    links = [x for x in links if not (x['url'] in seen or seen.add(x['url']))]
    audit['historical_quarters_found'] = links

    # Test reproducibility and actual payload availability at widely separated dates.
    wanted = ['2016 Q1', '2018 Q1', '2020 Q1', '2022 Q1', '2024 March April May']
    for label in wanted:
        candidates = [x for x in links if label.lower() in x['label'].lower()]
        if not candidates:
            # Fall back to year-quarter token matching.
            candidates = [x for x in links if label.split()[0] in x['label']]
        item = {'requested': label, 'found': bool(candidates)}
        if candidates:
            u = candidates[0]['url']
            item['url'] = u
            try:
                rr = requests.get(u, headers=HEADERS, timeout=TIMEOUT, stream=True)
                item['http_status'] = rr.status_code
                item['content_length'] = rr.headers.get('Content-Length')
                if rr.ok:
                    data = rr.content
                    item['bytes_downloaded'] = len(data)
                    with zipfile.ZipFile(io.BytesIO(data)) as z:
                        names = z.namelist()
                        item['zip_entries'] = len(names)
                        item['sample_entries'] = names[:10]
                else:
                    item['error'] = rr.text[:500]
            except Exception as exc:
                item['error'] = repr(exc)
        audit['download_tests'].append(item)

    # Point-in-time proof: SEC EDGAR filing index exposes accepted timestamp.
    sample_url = 'https://www.sec.gov/Archives/edgar/data/1719087/000171908720000009/0001719087-20-000009-index.htm'
    try:
        txt = get(sample_url).text
        accepted = re.search(r'Accepted\s*</th>\s*<td[^>]*>\s*([^<]+)', txt, re.I)
        filing = re.search(r'Filing Date\s*</th>\s*<td[^>]*>\s*([^<]+)', txt, re.I)
        period = re.search(r'Period of Report\s*</th>\s*<td[^>]*>\s*([^<]+)', txt, re.I)
        audit['point_in_time_sample'] = {
            'url': sample_url,
            'accepted': accepted.group(1).strip() if accepted else None,
            'filing_date': filing.group(1).strip() if filing else None,
            'period_of_report': period.group(1).strip() if period else None,
            'point_in_time_rule': 'Use EDGAR acceptance timestamp; holdings are not available before dissemination/acceptance.'
        }
    except Exception as exc:
        audit['point_in_time_sample'] = {'error': repr(exc)}

    audit['mapping_assessment'] = {
        'historical_coverage': 'Strong: SEC lists quarterly 13F datasets from 2013-05 through current period.',
        'frequency': 'Quarterly.',
        'publication_lag': 'Material: managers report holdings as of quarter-end, generally due within 45 days.',
        'security_identifier': 'Dataset contains CUSIP and, in newer schema versions, optional FIGI; ticker is not the primary stable identifier.',
        'universe_mapping_risk': 'Material: mapping 13F CUSIP/FIGI to the frozen ticker universe must be historical/point-in-time to avoid survivorship and identifier drift.',
        'economic_hypothesis': 'Institutional ownership changes, new positions, exits, concentration and consensus changes may predict medium-horizon returns, but can also be return-chasing due to reporting lag.',
    }

    successful_tests = sum(1 for x in audit['download_tests'] if x.get('http_status') == 200 and x.get('bytes_downloaded', 0) > 0)
    audit['status'] = 'COMPLETE'
    audit['conclusion'] = 'PROMOTE_TO_RESEARCH_WITH_MAPPING_CAUTION' if successful_tests >= 3 and len(links) >= 20 else 'FEASIBILITY_INCOMPLETE'
    audit['successful_download_tests'] = successful_tests
    audit['completed_utc'] = datetime.now(timezone.utc).isoformat()
    (OUT / 'phase22_sec_13f_audit.json').write_text(json.dumps(audit, indent=2), encoding='utf-8')
    print(json.dumps({k: audit[k] for k in ['phase','status','successful_download_tests','conclusion','mapping_assessment']}, indent=2))


if __name__ == '__main__':
    main()

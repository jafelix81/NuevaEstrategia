"""Compatibility runner for Phase 31 FINRA short-interest API payloads.

The research script remains unchanged; this wrapper replaces only the loader so
FINRA top-level-list and nested-dict JSON responses are normalized to a list of
records before ticker filtering. PIT rules and all factor definitions remain
those registered in the Phase 31 research script.
"""
from __future__ import annotations
import runpy
import requests
import pandas as pd

MODULE = 'Nueva_Estrategia_Fase31_FINRA_Flow_SI_Divergence.py'


def _records(obj):
    if isinstance(obj, list):
        return [x for x in obj if isinstance(x, dict)]
    if isinstance(obj, dict):
        for key in ('data', 'results', 'items'):
            value = obj.get(key)
            if isinstance(value, list):
                return [x for x in value if isinstance(x, dict)]
            if isinstance(value, dict):
                nested = _records(value)
                if nested:
                    return nested
        return []
    return []


def load_si_fixed():
    ns = runpy.run_path(MODULE, run_name='phase31_module')
    rows, audit, dates = [], [], []
    start, end = ns['START'], ns['END']
    fields, universe = ns['FIELDS'], ns['UNIVERSE']
    out, api = ns['OUT'], ns['SI_API']
    for m in pd.period_range(start, end, freq='M'):
        d1 = pd.Timestamp(m.start_time.year, m.start_time.month, 15)
        while d1.weekday() >= 5: d1 -= pd.Timedelta(days=1)
        d2 = pd.Timestamp(m.end_time).normalize()
        while d2.weekday() >= 5: d2 -= pd.Timedelta(days=1)
        dates += [d1, d2]

    for d in sorted(set(dates)):
        try:
            payload = {
                'limit': 10000,
                'offset': 0,
                'fields': fields,
                'compareFilters': [{'compareType': 'equal', 'fieldName': 'settlementDate', 'fieldValue': d.strftime('%Y-%m-%d')}],
            }
            batch = []
            while True:
                r = requests.post(api, json=payload, timeout=60,
                                  headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
                r.raise_for_status()
                data = _records(r.json())
                if not data:
                    break
                batch.extend(data)
                if len(data) < payload['limit']:
                    break
                payload['offset'] += len(data)
            hits = [z for z in batch if str(z.get('symbolCode', '')).upper() in universe]
            rows.extend(hits)
            audit.append({'settlementDate': str(d.date()), 'rows': len(batch), 'universeRows': len(hits), 'status': 'ok'})
        except Exception as e:
            audit.append({'settlementDate': str(d.date()), 'rows': 0, 'universeRows': 0, 'status': 'error', 'error': repr(e)})

    pd.DataFrame(audit).to_csv(out / 'si_download_audit.csv', index=False)
    x = pd.DataFrame(rows)
    if x.empty:
        raise RuntimeError('No FINRA short-interest rows after response normalization')
    x['Date'] = pd.to_datetime(x.settlementDate, errors='coerce').dt.normalize()
    x['KnowledgeDate'] = x.Date.map(ns['bday_knowledge'])
    x['Ticker'] = x.symbolCode.astype(str).str.upper()
    for c in ['currentShortPositionQuantity','previousShortPositionQuantity','changePreviousNumber','changePercent','daysToCoverQuantity']:
        x[c] = pd.to_numeric(x[c], errors='coerce')
    return x.sort_values(['Ticker','Date']).drop_duplicates(['Ticker','Date'], keep='last'), ns


# Execute the original script's definitions, replace only load_si, then call main.
ns = runpy.run_path(MODULE, run_name='phase31_module')
fixed_si, _ = load_si_fixed()
ns['load_si'] = lambda: fixed_si
ns['main']()

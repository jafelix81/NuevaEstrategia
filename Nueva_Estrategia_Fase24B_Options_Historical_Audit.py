import hashlib, json, os, requests, pandas as pd

OUT='nueva_estrategia_phase24b_options_historical_audit'
HEADERS={'User-Agent':'NuevaEstrategiaResearch/1.0 research contact'}
DATES=pd.to_datetime([
 '2016-01-06','2017-01-04','2018-01-03','2019-01-02','2020-01-02',
 '2021-01-04','2022-01-03','2023-01-03','2024-01-02','2025-01-02','2026-01-02'
])

def probe(name,url):
    try:
        r=requests.get(url,headers=HEADERS,timeout=60)
        raw=r.content
        text=''
        try: text=raw.decode('utf-8','replace')[:500]
        except Exception: pass
        return {
            'name':name,'url':url,'status_code':r.status_code,'ok':r.ok,
            'content_type':r.headers.get('content-type',''),'bytes':len(raw),
            'sha256':hashlib.sha256(raw).hexdigest(),
            'prefix_text':text.replace('\n',' ')[:300],
            'prefix_hex':raw[:80].hex()
        }
    except Exception as e:
        return {'name':name,'url':url,'ok':False,'error':repr(e)}

def main():
    os.makedirs(OUT,exist_ok=True)
    rows=[]
    for dt in DATES:
        d=dt.strftime('%Y%m%d')
        rows += [
            probe('daily_volume_statistics',f'https://marketdata.theocc.com/daily-volume-statistics?reportDate={d}&format=csv'),
            probe('contract_volume_download',f'https://marketdata.theocc.com/cont-volume-download?reportDate={d}&format=txt'),
            probe('trade_volume_download',f'https://marketdata.theocc.com/trade-volume-download?reportDate={d}&format=xml'),
            probe('dlp_http_download',f'https://marketdata.theocc.com/daily-delo-download?reportDate={d}&format=xml'),
            probe('volume_by_account_type',f'https://marketdata.theocc.com/onn-volume-download?productKind=options&reportType=D&reportDate={d}&reportFormat=percent&issues=all&reportView=raw'),
        ]
    df=pd.DataFrame(rows)
    df.to_csv(f'{OUT}/phase24b_endpoint_audit.csv',index=False)
    summary=(df.groupby('name',dropna=False).agg(samples=('name','size'),http_ok=('ok','sum'),nontrivial_bytes=('bytes',lambda s:int((s>100).sum())),max_bytes=('bytes','max')).reset_index())
    summary.to_csv(f'{OUT}/phase24b_endpoint_summary.csv',index=False)
    audit={
        'phase':'24B','status':'COMPLETE_FEASIBILITY_AUDIT','sample_dates':[d.strftime('%Y-%m-%d') for d in DATES],
        'purpose':'Determine whether OCC historical option volume/account-type endpoints return substantive, reproducible data across the research history.',
        'no_lookahead_policy':'This phase is data feasibility only. Any predictive phase must use a verified publication/availability timestamp strictly before SignalDate.',
        'open_interest_not_assumed':True,
        'next_step':'Promote only endpoints with substantive historical payloads and stable identifiers; otherwise kill the corresponding data source before predictability testing.',
        'summary':summary.to_dict(orient='records')
    }
    json.dump(audit,open(f'{OUT}/phase24b_audit.json','w'),indent=2)
    print(json.dumps(audit,indent=2))

if __name__=='__main__': main()

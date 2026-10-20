import json, os, io, zipfile, requests, pandas as pd
OUT='nueva_estrategia_phase24a_options_feasibility'
DATES=['2017-01-04','2020-06-03','2024-06-03','2026-06-03']
HEADERS={'User-Agent':'NuevaEstrategiaResearch/1.0 research contact'}

def probe(name,url):
 try:
  r=requests.get(url,headers=HEADERS,timeout=30)
  return {'name':name,'url':url,'status_code':r.status_code,'content_type':r.headers.get('content-type',''),'bytes':len(r.content),'ok':r.ok,'prefix':r.text[:120] if 'text' in r.headers.get('content-type','').lower() else ''}
 except Exception as e:return {'name':name,'url':url,'ok':False,'error':repr(e)}

def main():
 os.makedirs(OUT,exist_ok=True); rows=[]
 for d in DATES:
  ymd=d.replace('-','')
  rows += [
   probe('daily_volume_statistics',f'https://marketdata.theocc.com/daily-volume-statistics?reportDate={ymd}&format=csv'),
   probe('contract_volume_download',f'https://marketdata.theocc.com/cont-volume-download?reportDate={ymd}&format=txt'),
   probe('trade_volume_download',f'https://marketdata.theocc.com/trade-volume-download?reportDate={ymd}&format=xml'),
   probe('dlp_http_download',f'https://marketdata.theocc.com/daily-delo-download?reportDate={ymd}&format=xml'),
   probe('volume_by_account_type',f'https://marketdata.theocc.com/onn-volume-download?productKind=options&reportType=D&reportDate={ymd}&reportFormat=percent&issues=all&reportView=raw'),
  ]
 pd.DataFrame(rows).to_csv(f'{OUT}/phase24a_endpoint_probe.csv',index=False)
 audit={'phase':'24A','status':'FEASIBILITY_PROBE','source':'OCC Market Data','sample_dates':DATES,'official_batch_docs':'OCC documents daily volume, contract volume, trade volume, DLP and volume-by-account-type batch endpoints','endpoint_results':rows,'critical_open_interest_question':'OCC current Open Interest page is documented, but a historical options-OI batch endpoint was not exposed in the batch-processing documentation reviewed; do not assume historical OI availability until a dated endpoint/file is independently verified.','point_in_time_rule':'Use only data whose publication/availability timestamp is known to precede the signal; do not infer institutional intent from raw options volume.','no_production_change':True,'next_step':'If dated contract/volume/account-type files are reproducible across samples, audit historical coverage and identifier mapping before any predictability test.'}
 json.dump(audit,open(f'{OUT}/phase24a_audit.json','w'),indent=2)
 print(json.dumps(audit,indent=2))
if __name__=='__main__': main()

import io, json, re, zipfile
from pathlib import Path
from difflib import SequenceMatcher
import requests

OUT=Path('nueva_estrategia_phase22c_sec_13f_fuzzy_mapping_audit'); OUT.mkdir(exist_ok=True)
HEADERS={'User-Agent':'NuevaEstrategia research research@example.com'}
SEC_TICKERS='https://www.sec.gov/files/company_tickers_exchange.json'
DATASETS={'2016Q1':'https://www.sec.gov/files/structureddata/data/form-13f-data-sets/2016q1_form13f.zip','2018Q1':'https://www.sec.gov/files/structureddata/data/form-13f-data-sets/2018q1_form13f.zip','2020Q1':'https://www.sec.gov/files/structureddata/data/form-13f-data-sets/2020q1_form13f.zip','2022Q1':'https://www.sec.gov/files/structureddata/data/form-13f-data-sets/2022q1_form13f.zip','2024Q1':'https://www.sec.gov/files/structureddata/data/form-13f-data-sets/01mar2024-31may2024_form13f.zip'}

def get(u):
 r=requests.get(u,headers=HEADERS,timeout=180); r.raise_for_status(); return r.content

def norm(s):
 s=re.sub(r'[^A-Z0-9 ]',' ',str(s).upper())
 s=re.sub(r'\b(THE|INC|INCORPORATED|CORP|CORPORATION|LTD|LIMITED|PLC|HOLDINGS|HOLDING|COMPANY|CO|LP|LLC|N A|NA)\b',' ',s)
 return re.sub(r'\s+',' ',s).strip()

def sim(a,b): return SequenceMatcher(None,a,b).ratio()

def main():
 import pandas as pd
 tick=json.loads(get(SEC_TICKERS).decode()); vals=tick.get('data',tick)
 if isinstance(vals,dict): vals=list(vals.values())
 universe=[{'ticker':str(x['ticker']).upper(),'name':str(x['name']),'norm':norm(x['name'])} for x in vals if isinstance(x,dict) and x.get('ticker') and x.get('name')]
 src=Path('Nueva_Estrategia_Fase0_Descubrimiento.py').read_text(encoding='utf-8'); block=src.split('DEFAULT_UNIVERSE = [',1)[1].split(']\n',1)[0]
 frozen=set(re.findall(r"'([A-Z0-9.\-]+)'",block)); candidates=[x for x in universe if x['ticker'] in frozen]; by_norm={x['norm']:x for x in candidates}
 audit={'phase':'22C_SEC_13F_FUZZY_MAPPING_AUDIT','frozen_universe':len(frozen),'sec_name_rows':len(candidates),'datasets':{},'rule':'issuer-name similarity only; no production mapping; ambiguous matches are rejected'}
 for label,url in DATASETS.items():
  raw=get(url)
  with zipfile.ZipFile(io.BytesIO(raw)) as z:
   info=[n for n in z.namelist() if n.upper().endswith('INFOTABLE.TSV')][0]
   df=pd.read_csv(z.open(info),sep='\t',dtype=str,low_memory=False); cols={c.lower():c for c in df.columns}; namecol=cols.get('nameissuer') or cols.get('nameofissuer') or cols.get('name')
   names=sorted(set(norm(x) for x in df[namecol].fillna('') if norm(x))); exact=sum(n in by_norm for n in names); accepted=0; ambiguous=0; no_match=0
   for n in names:
    if n in by_norm: accepted+=1; continue
    scores=sorted(((sim(n,c['norm']),c) for c in candidates),key=lambda z:z[0],reverse=True); score,c=scores[0]; gap=score-scores[1][0] if len(scores)>1 else score
    if score>=0.92 and gap>=0.03: accepted+=1
    elif score>=0.88: ambiguous+=1
    else: no_match+=1
   audit['datasets'][label]={'unique_issuers':len(names),'exact':exact,'fuzzy_accepted':accepted-exact,'accepted_total':accepted,'accepted_rate':accepted/len(names) if names else 0,'ambiguous':ambiguous,'no_match':no_match}
 audit['conclusion']='PROCEED_TO_HISTORICAL_CUSIP_CROSSWALK' if min(v['accepted_rate'] for v in audit['datasets'].values())>=0.70 else 'INSUFFICIENT_FOR_PRODUCTION_MAPPING'
 (OUT/'phase22c_mapping_summary.json').write_text(json.dumps(audit,indent=2),encoding='utf-8'); print(json.dumps(audit,indent=2))
if __name__=='__main__': main()

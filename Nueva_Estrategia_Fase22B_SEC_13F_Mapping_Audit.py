import io, json, re, zipfile
from pathlib import Path
import pandas as pd
import requests

OUT = Path('nueva_estrategia_phase22b_sec_13f_mapping_audit'); OUT.mkdir(exist_ok=True)
HEADERS={'User-Agent':'NuevaEstrategia research contact research@example.com'}
SEC_TICKERS='https://www.sec.gov/files/company_tickers_exchange.json'
DATASETS={
 '2016Q1':'https://www.sec.gov/files/structureddata/data/form-13f-data-sets/2016q1_form13f.zip',
 '2018Q1':'https://www.sec.gov/files/structureddata/data/form-13f-data-sets/2018q1_form13f.zip',
 '2020Q1':'https://www.sec.gov/files/structureddata/data/form-13f-data-sets/2020q1_form13f.zip',
 '2022Q1':'https://www.sec.gov/files/structureddata/data/form-13f-data-sets/2022q1_form13f.zip',
 '2024Q1':'https://www.sec.gov/files/structureddata/data/form-13f-data-sets/01mar2024-31may2024_form13f.zip',
}

def norm(s):
 s=re.sub(r'[^A-Z0-9 ]',' ',str(s).upper()); s=re.sub(r'\b(THE|INC|INCORPORATED|CORP|CORPORATION|LTD|LIMITED|PLC|HOLDINGS|HOLDING|COMPANY|CO)\b',' ',s); return re.sub(r'\s+',' ',s).strip()

def get(u):
 r=requests.get(u,headers=HEADERS,timeout=120); r.raise_for_status(); return r.content

def main():
 audit={'phase':'22B_SEC_13F_MAPPING_AUDIT','datasets':{},'status':'RUNNING'}
 tick=json.loads(get(SEC_TICKERS).decode())
 vals=tick.get('data',tick)
 universe=[]
 if isinstance(vals,dict): vals=list(vals.values())
 for x in vals:
  if isinstance(x,dict):
   t=x.get('ticker'); n=x.get('name'); cik=x.get('cik') or x.get('cik_str')
   if t and n: universe.append({'ticker':t,'name':n,'cik':str(cik) if cik else None,'norm':norm(n)})
 # This is explicitly a mapping audit, not a production mapping.
 by_name={x['norm']:x for x in universe}
 for label,url in DATASETS.items():
  raw=get(url)
  with zipfile.ZipFile(io.BytesIO(raw)) as z:
   names=z.namelist(); info=[n for n in names if n.upper().endswith('INFOTABLE.TSV')][0]
   df=pd.read_csv(z.open(info),sep='\t',dtype=str,low_memory=False)
   cols={c.lower():c for c in df.columns}
   namecol=cols.get('nameissuer') or cols.get('nameofissuer') or cols.get('name')
   cusipcol=cols.get('cusip') or cols.get('cusipnumber')
   if not namecol: raise RuntimeError(f'{label}: issuer-name column not found: {list(df.columns)}')
   names_norm=df[namecol].fillna('').map(norm)
   exact=names_norm.map(lambda x: x in by_name if x else False)
   result={'rows':int(len(df)),'unique_issuers':int(names_norm[names_norm!=''].nunique()),'exact_name_matches':int(exact.sum()),'exact_name_match_rate':float(exact.mean()),'identifier_column':cusipcol,'issuer_name_column':namecol}
   audit['datasets'][label]=result
 audit['status']='COMPLETE'
 audit['conclusion']='MAPPING_NEEDS_HISTORICAL_IDENTIFIER_WORK'
 (OUT/'phase22b_mapping_audit.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
 print(json.dumps(audit,indent=2))
if __name__=='__main__': main()

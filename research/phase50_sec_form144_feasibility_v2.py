import ast, gzip, json, os, re, time
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_SOURCE='Nueva_Estrategia_Fase0_Descubrimiento.py'
SEC_TICKERS_URL='https://www.sec.gov/files/company_tickers.json'
EFTS_URL='https://efts.sec.gov/LATEST/search-index'
SEC_ARCHIVES='https://www.sec.gov/Archives/edgar/data'
OUT_DIR='phase50_sec_form144_feasibility_v2'
HEADERS={'User-Agent':'NuevaEstrategia research research@example.com','Accept-Encoding':'gzip, deflate'}
START_DATE='2023-04-13'; END_DATE='2026-10-29'; MIN_COVERAGE=.95; SAMPLE_ISSUERS=25

def get_bytes(url,retries=8,timeout=60):
    last=None
    for attempt in range(retries):
        try:
            with urlopen(Request(url,headers=HEADERS),timeout=timeout) as r:
                raw=r.read(); enc=(r.headers.get('Content-Encoding') or '').lower()
                if enc=='gzip' or raw[:2]==b'\x1f\x8b': raw=gzip.decompress(raw)
                return raw
        except HTTPError as e:
            last=e
            if e.code in (429,500,502,503,504): time.sleep(min(30,2**attempt)); continue
            raise
        except (URLError,TimeoutError,OSError) as e:
            last=e; time.sleep(min(20,2**attempt))
    raise RuntimeError(f'GET failed: {url}: {last}')

def get_json(url): return json.loads(get_bytes(url).decode('utf-8'))
def norm_cik(x): return None if x in (None,'') else str(x).strip().zfill(10)

def frozen_universe():
    tree=ast.parse(open(BASE_SOURCE,encoding='utf-8').read())
    for n in tree.body:
        if isinstance(n,ast.Assign):
            for t in n.targets:
                if isinstance(t,ast.Name) and t.id=='DEFAULT_UNIVERSE':
                    u=sorted(set(str(x).strip().upper() for x in ast.literal_eval(n.value)))
                    if len(u)!=335: raise RuntimeError(f'Expected 335-name frozen universe, got {len(u)}')
                    return u
    raise RuntimeError('DEFAULT_UNIVERSE not found')

def search_issuer(cik):
    q=urlencode({'forms':'144','ciks':cik,'startdt':START_DATE,'enddt':END_DATE,'from':0,'size':1})
    h=get_json(EFTS_URL+'?'+q).get('hits',{}); total=h.get('total',0)
    if isinstance(total,dict): total=total.get('value',0)
    return {'cik':cik,'count':int(total or 0),'sample_hit':(h.get('hits') or [None])[0]}

def source(hit): return (hit or {}).get('_source') or (hit or {}).get('source') or {}
def accession(hit):
    s=source(hit)
    for k in ('accession_no','accession_number','adsh'):
        if s.get(k): return str(s[k]).replace('-','')
    for k in ('_id','id'):
        if re.fullmatch(r'\d{10}-\d{2}-\d{6}',str((hit or {}).get(k,''))): return str(hit[k]).replace('-','')
    return None

def hit_ciks(hit):
    s=source(hit); v=s.get('ciks')
    if isinstance(v,list): return [norm_cik(x) for x in v if norm_cik(x)]
    if isinstance(v,str): return [norm_cik(x) for x in re.split(r'[,; ]+',v) if norm_cik(x)]
    return []

def download_doc(hit):
    acc=accession(hit); ciks=hit_ciks(hit)
    if not acc: return {'ok':False,'reason':'missing_accession'}
    dashed=f'{acc[:10]}-{acc[10:12]}-{acc[12:]}'
    # SEC filing archive is keyed by the filing CIK (first 10 accession digits), not necessarily issuer CIK.
    filer_path=str(int(acc[:10]))
    base=f'{SEC_ARCHIVES}/{filer_path}/{acc}'
    urls=[f'{base}/{dashed}-index.htm',f'{base}/{dashed}-index.html']
    tried=[]
    for index_url in urls:
        try:
            index=get_bytes(index_url).decode('utf-8','replace')
            names=re.findall(r'href=[\"\']([^\"\']+\.xml)[\"\']',index,re.I)
            names += re.findall(r'>([^<\"\']+\.xml)<',index,re.I)
            names=list(dict.fromkeys(names))
            if not names: raise RuntimeError('no_xml_document_in_index')
            for name in names:
                name=name.split('/')[-1]
                xml_url=name if name.startswith('http') else f'{base}/{name.lstrip("./")}'
                try:
                    xml=get_bytes(xml_url).decode('utf-8','replace')
                    if re.search(r'<(?:form144|ownership|issuer|reportingowner|securities)',xml,re.I):
                        return {'ok':True,'index_url':index_url,'xml_url':xml_url,'xml':xml,'accession':dashed,'filer_cik':filer_path}
                except Exception as e: tried.append({'url':xml_url,'error':str(e)})
            raise RuntimeError('xml_documents_found_but_form144_not_identified')
        except Exception as e: tried.append({'url':index_url,'error':str(e)})
    return {'ok':False,'reason':'archive_download_failed','accession':dashed,'tried':tried,'issuer_ciks':ciks}

def field_presence(xml):
    x=xml.lower()
    pats={'issuer_cik':[r'<issuercik[ >]',r'issuer cik'],'issuer_name':[r'<issuername[ >]',r'issuer name'],'security_title':[r'<securitytitle[ >]',r'security title'],'shares_to_be_sold':[r'<unitstosold[ >]',r'<unitstobesold[ >]',r'units to be sold',r'shares to be sold'],'aggregate_market_value':[r'<aggregatemarketvalue[ >]',r'aggregate market value'],'proposed_sale_date':[r'<approxsaledate[ >]',r'approx sale date',r'approximate sale date'],'acquisition_date':[r'<securitiesacquireddate[ >]',r'securities acquired date'],'nature_of_acquisition':[r'<natureofacquisition[ >]',r'nature of acquisition'],'broker':[r'<broker[ >]',r'broker']}
    return {k:any(re.search(p,x) for p in ps) for k,ps in pats.items()}

def main():
    os.makedirs(OUT_DIR,exist_ok=True); universe=frozen_universe(); sec=get_json(SEC_TICKERS_URL)
    sec_map={str(r.get('ticker','')).strip().upper():norm_cik(r.get('cik_str')) for r in sec.values() if r.get('ticker')}
    mapping=[(t,sec_map.get(t)) for t in universe]; mapped=[x for x in mapping if x[1]]; unmapped=[x[0] for x in mapping if not x[1]]
    results=[]; errors=[]
    with ThreadPoolExecutor(max_workers=2) as ex:
        futs={ex.submit(search_issuer,cik):tick for tick,cik in mapped}
        for f in as_completed(futs):
            tick=futs[f]
            try: r=f.result(); r['ticker']=tick; results.append(r)
            except Exception as e: errors.append({'ticker':tick,'error':str(e)})
    covered=[r for r in results if r['count']>0]; coverage=len(covered)/len(mapped) if mapped else 0
    eligible=sorted([r for r in results if r['count']>0 and r.get('sample_hit')],key=lambda r:r['cik'])
    if eligible and len(eligible)>SAMPLE_ISSUERS:
        idx=[round(i*(len(eligible)-1)/(SAMPLE_ISSUERS-1)) for i in range(SAMPLE_ISSUERS)]; eligible=[eligible[i] for i in sorted(set(idx))]
    sample=[]
    for r in eligible:
        d=download_doc(r['sample_hit']); fields=field_presence(d['xml']) if d.get('ok') else {}
        sample.append({'ticker':r['ticker'],'cik':r['cik'],'filing_count':r['count'],'download_ok':d.get('ok',False),'accession':d.get('accession'),'index_url':d.get('index_url'),'xml_url':d.get('xml_url'),'field_presence':fields,'download_reason':d.get('reason'),'download_error_detail':d.get('tried')})
    rates={}
    for k in sorted(set(k for s in sample for k in s.get('field_presence',{}))):
        vals=[s['field_presence'][k] for s in sample if s['download_ok']]
        if vals: rates[k]=sum(vals)/len(vals)
    gate=(len(mapped)>=300 and coverage>=MIN_COVERAGE and not errors and len(sample)==min(SAMPLE_ISSUERS,len(eligible)) and all(s['download_ok'] for s in sample) and all(v>=.95 for v in rates.values()))
    summary={'phase':'50-v2','source':'SEC EDGAR Form 144','status':'COMPLETE','electronic_compliance_start':START_DATE,'end_date':END_DATE,'frozen_universe':len(universe),'current_sec_cik_mapped':len(mapped),'current_sec_cik_unmapped':len(unmapped),'unmapped_tickers':unmapped,'issuers_with_form144_hits':len(covered),'issuer_hit_coverage_among_current_cik_mapped':coverage,'query_errors':len(errors),'query_error_samples':errors[:10],'sample_size':len(sample),'sample':sample,'field_presence_rates':rates,'knowledge_rule':'SEC acceptance/dissemination datetime is PIT; proposed sale date is an event attribute only.','economic_hypothesis':'Form 144 proposed sales may contain incremental information about planned insider/affiliate supply; no directional sign assumed.','gate_rule':'>=95% issuer coverage among current SEC-mapped frozen names, zero query errors, complete actual-XML sample. Separate historical PIT identity gate required before alpha.','gate':'PASS' if gate else 'FAIL','alpha_authorized':False,'next_step':'If PASS, run historical PIT issuer/security identity and filing-field completeness audit; then pre-register proposed-sale intensity features. If FAIL, archive as infeasible without alpha testing.'}
    json.dump(summary,open(os.path.join(OUT_DIR,'summary.json'),'w'),indent=2); json.dump(results,open(os.path.join(OUT_DIR,'issuer_results.json'),'w'),indent=2); print(json.dumps(summary,indent=2))
    if not gate: raise SystemExit(1)
if __name__=='__main__': main()

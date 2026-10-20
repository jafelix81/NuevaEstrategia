"""Phase 21B v2 — official SEC quarterly Form 4 dataset.

Uses SEC Insider Transactions Data Sets instead of per-filing EDGAR crawling.
Original Form 4 only; 4/A is audited but excluded initially to avoid double
counting. KnowledgeDate is the SEC FILING_DATE. Downstream research must use
KnowledgeDate < SignalDate, so same-day filings are conservatively excluded.
Transaction rows and reporting-owner rows remain separate; joint filings are
never duplicated by an owner join.
"""
from __future__ import annotations
import io, json, re, zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin
import pandas as pd, requests
from Nueva_Estrategia_Fase11_Real1000_LTM_v4 import DEFAULT_UNIVERSE

OUTDIR=Path("nueva_estrategia_phase21b_sec_form4_official"); OUTDIR.mkdir(parents=True,exist_ok=True)
PAGE="https://www.sec.gov/data-research/sec-markets-data/insider-transactions-data-sets"
TICKERS="https://www.sec.gov/files/company_tickers.json"
START=pd.Timestamp("2016-01-01"); END=pd.Timestamp(datetime.now(timezone.utc).date())
UA="NuevaEstrategia research contact research@example.com"
SUB=["ACCESSION_NUMBER","FILING_DATE","PERIOD_OF_REPORT","DATE_OF_ORIG_SUB","DOCUMENT_TYPE","ISSUERCIK","ISSUERNAME","ISSUERTRADINGSYMBOL","AFF10B5ONE"]
OWN=["ACCESSION_NUMBER","RPTOWNERCIK","RPTOWNERNAME","RPTOWNER_RELATIONSHIP","RPTOWNER_TITLE"]
TRN=["ACCESSION_NUMBER","NONDERIV_TRANS_SK","SECURITY_TITLE","TRANS_DATE","TRANS_FORM_TYPE","TRANS_CODE","TRANS_SHARES","TRANS_PRICEPERSHARE","TRANS_ACQUIRED_DISP_CD","DIRECT_INDIRECT_OWNERSHIP","SHRS_OWND_FOLWNG_TRANS","VALU_OWND_FOLWNG_TRANS","NATURE_OF_OWNERSHIP"]

def get(url):
    r=requests.get(url,headers={"User-Agent":UA,"Accept-Encoding":"gzip, deflate"},timeout=90); r.raise_for_status(); return r

def tsv(z,member,cols):
    names={x.upper():x for x in z.namelist()}; key=member.upper()
    if key not in names: raise FileNotFoundError(f"{member} missing: {z.namelist()[:20]}")
    with z.open(names[key]) as f: d=pd.read_csv(f,sep="\t",dtype=str,low_memory=False)
    d.columns=[str(c).strip().upper() for c in d.columns]
    for c in cols:
        if c not in d: d[c]=pd.NA
    return d[cols]

def quarters():
    html=get(PAGE).text; hrefs=re.findall(r'href=["\']([^"\']+_form345\.zip)["\']',html,re.I); out={}
    for h in hrefs:
        m=re.search(r'(20\d{2})q([1-4])_form345\.zip',h,re.I)
        if not m: continue
        y,q=int(m.group(1)),int(m.group(2)); label=f"{y}Q{q}"
        if pd.Timestamp(f"{y}-{q*3:02d}-01") >= START-pd.Timedelta(days=120): out[label]=urljoin(PAGE,h)
    return sorted(out.items())

def main():
    started=datetime.now(timezone.utc); universe=sorted(set(DEFAULT_UNIVERSE))
    sec={str(x.get("ticker","")).upper().strip():str(x.get("cik_str","")).zfill(10) for x in get(TICKERS).json().values() if x.get("ticker")}
    ciks={sec[t] for t in universe if t in sec}; mapping_fail=sorted(t for t in universe if t not in sec)
    qs=quarters(); assert qs,"No SEC quarterly dataset links discovered"
    subs=[]; trans=[]; owners=[]; audits=[]
    for label,url in qs:
        print(f"DOWNLOAD {label}",flush=True); blob=get(url).content
        with zipfile.ZipFile(io.BytesIO(blob)) as z:
            s=tsv(z,"SUBMISSION.tsv",SUB); s["_date"]=pd.to_datetime(s.FILING_DATE,errors="coerce",dayfirst=True)
            s=s[s._date.between(START,END)].copy(); s=s[s.DOCUMENT_TYPE.isin(["4","4/A"])]; s=s[s.ISSUERCIK.astype(str).str.zfill(10).isin(ciks)]
            if s.empty: audits.append({"Quarter":label,"UniverseForms":0,"Form4":0,"Form4A":0,"Transactions":0,"Owners":0}); continue
            a=s[s.DOCUMENT_TYPE.eq("4")].copy(); acc=set(a.ACCESSION_NUMBER)
            o=tsv(z,"REPORTINGOWNER.tsv",OWN); o=o[o.ACCESSION_NUMBER.isin(acc)].copy()
            t=tsv(z,"NONDERIV_TRANS.tsv",TRN); t=t[t.ACCESSION_NUMBER.isin(acc)].copy()
            subs.append(a); trans.append(t); owners.append(o)
            audits.append({"Quarter":label,"UniverseForms":len(s),"Form4":len(a),"Form4A":int(s.DOCUMENT_TYPE.eq("4/A").sum()),"Transactions":len(t),"Owners":len(o)})
            print(f"  Form4={len(a):,} Form4A={int(s.DOCUMENT_TYPE.eq('4/A').sum()):,} transactions={len(t):,}",flush=True)
    if not subs: raise RuntimeError("No Form 4 rows matched frozen universe")
    s=pd.concat(subs,ignore_index=True).drop_duplicates("ACCESSION_NUMBER")
    t=pd.concat(trans,ignore_index=True).drop_duplicates(["ACCESSION_NUMBER","NONDERIV_TRANS_SK"])
    o=pd.concat(owners,ignore_index=True).drop_duplicates(["ACCESSION_NUMBER","RPTOWNERCIK"])
    meta=s[["ACCESSION_NUMBER","FILING_DATE","PERIOD_OF_REPORT","ISSUERCIK","ISSUERNAME","ISSUERTRADINGSYMBOL","DOCUMENT_TYPE","AFF10B5ONE"]].copy()
    tx=t.merge(meta,on="ACCESSION_NUMBER",how="left",validate="many_to_one")
    tx["KnowledgeDate"]=pd.to_datetime(tx.FILING_DATE,errors="coerce",dayfirst=True)
    tx["TransactionDate"]=pd.to_datetime(tx.TRANS_DATE,errors="coerce",dayfirst=True)
    tx["Shares"]=pd.to_numeric(tx.TRANS_SHARES,errors="coerce"); tx["PricePerShare"]=pd.to_numeric(tx.TRANS_PRICEPERSHARE,errors="coerce"); tx["Notional"]=tx.Shares*tx.PricePerShare
    tx["IsPurchase"]=tx.TRANS_CODE.eq("P")&tx.TRANS_ACQUIRED_DISP_CD.eq("A"); tx["IsSale"]=tx.TRANS_CODE.eq("S")&tx.TRANS_ACQUIRED_DISP_CD.eq("D"); tx["IsOpenMarket"]=tx.TRANS_CODE.isin(["P","S"])
    tx["SignedShares"]=tx.Shares.fillna(0.0); tx.loc[tx.IsSale,"SignedShares"]*=-1; tx["SignedNotional"]=tx.Notional.fillna(0.0); tx.loc[tx.IsSale,"SignedNotional"]*=-1; tx["LagDays"]=(tx.KnowledgeDate-tx.TransactionDate).dt.days
    txcols=["ACCESSION_NUMBER","NONDERIV_TRANS_SK","ISSUERCIK","ISSUERNAME","ISSUERTRADINGSYMBOL","FILING_DATE","KnowledgeDate","PERIOD_OF_REPORT","DOCUMENT_TYPE","AFF10B5ONE","SECURITY_TITLE","TransactionDate","TRANS_FORM_TYPE","TRANS_CODE","TRANS_ACQUIRED_DISP_CD","DIRECT_INDIRECT_OWNERSHIP","Shares","PricePerShare","Notional","SignedShares","SignedNotional","IsPurchase","IsSale","IsOpenMarket","LagDays","NATURE_OF_OWNERSHIP"]
    tx[txcols].to_csv(OUTDIR/"phase21b_form4_transactions_original_only.csv",index=False)
    o.to_csv(OUTDIR/"phase21b_form4_reporting_owners_original_only.csv",index=False)
    s.to_csv(OUTDIR/"phase21b_form4_filing_index_original_only.csv",index=False)
    om=tx[tx.IsOpenMarket].copy()
    if not om.empty:
        daily=om.groupby(["ISSUERCIK","ISSUERTRADINGSYMBOL","KnowledgeDate"],dropna=False).agg(OpenMarketRows=("ACCESSION_NUMBER","count"),UniqueFilings=("ACCESSION_NUMBER","nunique"),PurchaseRows=("IsPurchase","sum"),SaleRows=("IsSale","sum"),GrossPurchaseNotional=("Notional",lambda x:x[om.loc[x.index,"IsPurchase"]].sum()),GrossSaleNotional=("Notional",lambda x:x[om.loc[x.index,"IsSale"]].sum()),NetOpenMarketNotional=("SignedNotional","sum"),NetOpenMarketShares=("SignedShares","sum"),MaxPurchaseNotional=("Notional",lambda x:x[om.loc[x.index,"IsPurchase"]].max())).reset_index()
    else: daily=pd.DataFrame()
    daily.to_csv(OUTDIR/"phase21b_form4_daily_original_only.csv",index=False)
    audit={"phase":"21B","status":"OFFICIAL_SEC_DATASET_READY","source":PAGE,"quarters":[q for q,_ in qs],"research_start":str(START.date()),"research_end":str(END.date()),"universe_size":len(universe),"mapped_universe_ciks":len(ciks),"mapping_failures":mapping_fail,"original_form4_filings":len(s),"original_form4_transaction_rows":len(t),"reporting_owner_rows":len(o),"purchase_rows":int(tx.IsPurchase.sum()),"sale_rows":int(tx.IsSale.sum()),"open_market_rows":int(tx.IsOpenMarket.sum()),"form4a_excluded":sum(x.get("Form4A",0) for x in audits),"knowledge_date_policy":"FILING_DATE; downstream must require KnowledgeDate < SignalDate","acceptance_datetime_available":False,"same_day_filings_excluded_downstream":True,"amendment_policy":"original Form 4 only; Form 4/A excluded from research population to prevent duplicate original/amendment counting","joint_owner_policy":"transactions and reporting owners stored separately; no owner is assigned to a transaction row in this phase","quarter_audit":audits,"started_at":started.isoformat(),"finished_at":datetime.now(timezone.utc).isoformat(),"next_step":"21C point-in-time predictability and incremental test"}
    (OUTDIR/"phase21b_sec_official_audit.json").write_text(json.dumps(audit,indent=2,default=str),encoding="utf-8"); print(json.dumps(audit,indent=2,default=str),flush=True)
if __name__=="__main__": main()

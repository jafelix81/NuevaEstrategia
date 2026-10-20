import io, json, os, re, zipfile
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import requests
import yfinance as yf

OUT = "nueva_estrategia_phase23b_cftc_cot_predictability"
BASE = "https://www.cftc.gov/files/dea/history"
YEARS = range(2016, datetime.utcnow().year + 1)
TARGET_PATTERNS = [
    r"NASDAQ MINI",
    r"NASDAQ-100 STOCK INDEX",
    r"E-MINI S&P 500",
    r"S&P 500 STOCK INDEX",
]
# Twelve chronological pseudo-OOS dates from the closed Phase 20C walk-forward.
TEST_DATES = pd.to_datetime([
    "2021-04-29","2021-08-23","2021-12-15","2022-04-11",
    "2022-08-05","2022-11-29","2023-03-27","2023-07-21",
    "2023-11-13","2024-03-11","2024-07-05","2024-10-28"
])
FEATURES = ["LEV_NET_OI","AM_NET_OI","DEALER_NET_OI","LEV_Z52","AM_Z52","LEV_D4","AM_D4","LEV_AM_DIVERGENCE"]

HEADERS={"User-Agent":"NuevaEstrategiaResearch/1.0 research contact"}

def fetch_year(year):
    url=f"{BASE}/fut_fin_txt_{year}.zip"
    r=requests.get(url,headers=HEADERS,timeout=60)
    r.raise_for_status()
    if not r.content.startswith(b"PK"):
        raise RuntimeError(f"Non-ZIP payload for {year}: {r.status_code} {r.headers.get('content-type')}")
    z=zipfile.ZipFile(io.BytesIO(r.content))
    names=z.namelist()
    csv_names=[n for n in names if n.lower().endswith((".txt",".csv"))]
    if not csv_names: raise RuntimeError(f"No text file in {year} zip")
    raw=z.read(csv_names[0])
    return pd.read_csv(io.BytesIO(raw),low_memory=False)

def norm_cols(df):
    return {c:re.sub(r"[^a-z0-9]+","_",str(c).strip().lower()).strip("_") for c in df.columns}

def col(df,*names):
    m=norm_cols(df)
    for n in names:
        nn=re.sub(r"[^a-z0-9]+","_",n.lower()).strip("_")
        for k,v in m.items():
            if v==nn:return k
    raise KeyError(names)

def net(df,prefix):
    long=col(df,f"{prefix}_Positions_Long_All")
    short=col(df,f"{prefix}_Positions_Short_All")
    return pd.to_numeric(df[long],errors="coerce")-pd.to_numeric(df[short],errors="coerce")

def safe_spearman(x,y):
    z=pd.DataFrame({"x":x,"y":y}).dropna()
    if len(z)<6 or z.x.nunique()<2 or z.y.nunique()<2:return np.nan
    return z.x.rank().corr(z.y.rank())

def main():
    os.makedirs(OUT,exist_ok=True)
    frames=[]; failures=[]
    for y in YEARS:
        try:
            df=fetch_year(y)
            m=norm_cols(df)
            market=col(df,"Market_and_Exchange_Names")
            datec=col(df,"Report_Date_as_YYYY_MM_DD","As_of_Date_In_Form_YYYY-MM-DD")
            keep=df[market].astype(str).str.upper().apply(lambda s:any(re.search(p,s) for p in TARGET_PATTERNS))
            x=df.loc[keep].copy()
            if x.empty: continue
            x["ReportDate"]=pd.to_datetime(x[datec],errors="coerce")
            x["MarketName"]=x[market].astype(str)
            for p,n in [("Lev_Money","Leveraged"),("Asset_Mgr","AssetManager"),("Dealer","Dealer")]:
                try:x[f"{n}_NetOI"]=net(x,p)
                except KeyError: x[f"{n}_NetOI"]=np.nan
            oi=col(x,"Open_Interest_All")
            x["OpenInterest"]=pd.to_numeric(x[oi],errors="coerce")
            frames.append(x[["ReportDate","MarketName","OpenInterest","Leveraged_NetOI","AssetManager_NetOI","Dealer_NetOI"]])
        except Exception as e:
            failures.append({"year":y,"error":repr(e)})
    if not frames: raise RuntimeError("No CFTC TFF rows recovered")
    d=pd.concat(frames,ignore_index=True).dropna(subset=["ReportDate"]).sort_values(["ReportDate","MarketName"])
    # Keep the most direct current aliases and aggregate duplicates at a report date.
    d["LEV_NET_OI"]=d["Leveraged_NetOI"]/d["OpenInterest"].replace(0,np.nan)
    d["AM_NET_OI"]=d["AssetManager_NetOI"]/d["OpenInterest"].replace(0,np.nan)
    d["DEALER_NET_OI"]=d["Dealer_NetOI"]/d["OpenInterest"].replace(0,np.nan)
    d["Family"]=np.where(d.MarketName.str.contains("NASDAQ",case=False,na=False),"NASDAQ","SP500")
    # One row per family/date; use the row with the largest OI to avoid mixing micro/mini duplicates.
    d=d.sort_values(["ReportDate","Family","OpenInterest"],ascending=[True,True,False]).drop_duplicates(["ReportDate","Family"])
    pieces=[]
    for fam,g in d.groupby("Family",sort=False):
        g=g.sort_values("ReportDate").copy()
        for f in ["LEV_NET_OI","AM_NET_OI","DEALER_NET_OI"]:
            g[f+"_D4"]=g[f].diff(4)
            g[f+"_Z52"]=(g[f]-g[f].rolling(52,min_periods=26).mean())/g[f].rolling(52,min_periods=26).std()
        g["LEV_AM_DIVERGENCE"]=g["LEV_NET_OI"]-g["AM_NET_OI"]
        # Conservative knowledge date: Monday following the Tuesday report.
        g["KnowledgeDate"]=(g["ReportDate"]+pd.to_timedelta((7-g["ReportDate"].dt.weekday)%7+0,unit="D"))
        # For Tuesday reports this is the following Monday; if already Monday, add 7.
        g.loc[g.ReportDate.dt.weekday==1,"KnowledgeDate"]=g.loc[g.ReportDate.dt.weekday==1,"ReportDate"]+pd.Timedelta(days=6)
        pieces.append(g)
    d=pd.concat(pieces,ignore_index=True).sort_values(["Family","KnowledgeDate"])
    d.to_csv(os.path.join(OUT,"phase23b_cftc_features.csv"),index=False)

    prices=yf.download(["SPY","QQQ"],start="2015-01-01",auto_adjust=True,progress=False,threads=False)
    close=prices["Close"] if isinstance(prices.columns,pd.MultiIndex) else prices
    close=close.dropna(how="all")
    ret=pd.DataFrame(index=close.index)
    for t in ["SPY","QQQ"]:
        ret[t+"_R5"]=close[t].shift(-5)/close[t]-1
        ret[t+"_R20"]=close[t].shift(-20)/close[t]-1
    rows=[]
    # No feature selection on the final test dates: each date only uses history strictly before it.
    for td in TEST_DATES:
        for fam in ["NASDAQ","SP500"]:
            g=d[(d.Family==fam)&(d.KnowledgeDate<td)].sort_values("KnowledgeDate")
            if g.empty:continue
            latest=g.iloc[-1]
            # Training observations end strictly before the test date; predict market returns from the next trading day.
            market="QQQ" if fam=="NASDAQ" else "SPY"
            y=ret.loc[ret.index<td,[market+"_R5",market+"_R20"]].copy()
            for f in FEATURES:
                # align historical feature observations to future market returns by report knowledge date.
                hist=g[["KnowledgeDate",f]].dropna().copy()
                hist["KnowledgeDate"]=pd.to_datetime(hist["KnowledgeDate"])
                yy=ret[[market+"_R5",market+"_R20"]].copy().reset_index().rename(columns={"index":"Date"})
                yy["Date"]=pd.to_datetime(yy["Date"])
                m=hist.merge(yy,left_on="KnowledgeDate",right_on="Date",how="inner")
                train=m[m.Date<td]
                if len(train)<8: continue
                for h in [5,20]:
                    rho=safe_spearman(train[f],train[f"{market}_R{h}"])
                    rows.append({"TestDate":td.date().isoformat(),"Family":fam,"Feature":f,"Horizon":h,"TrainN":len(train),"TrainSpearman":rho,"LatestValue":latest[f]})
    pred=pd.DataFrame(rows)
    pred.to_csv(os.path.join(OUT,"phase23b_predictability.csv"),index=False)
    summary=pred.groupby(["Family","Feature","Horizon"],dropna=False).agg(TestDates=("TestDate","count"),MeanTrainSpearman=("TrainSpearman","mean"),MedianTrainSpearman=("TrainSpearman","median")).reset_index()
    summary.to_csv(os.path.join(OUT,"phase23b_predictability_summary.csv"),index=False)
    audit={"phase":"23B","status":"COMPLETE_DIAGNOSTIC","source":"CFTC TFF Futures Only","years": [min(YEARS),max(YEARS)],"knowledge_date_policy":"strictly prior to signal; conservative Monday following Tuesday report","rows_features":int(len(d)),"download_failures":failures,"test_dates":[x.date().isoformat() for x in TEST_DATES],"families":sorted(d.Family.unique().tolist()),"no_production_change":True,"next_step":"If a feature/family is consistently promising, run a pre-registered F80 overlay walk-forward; otherwise kill the hypothesis."}
    with open(os.path.join(OUT,"phase23b_audit.json"),"w") as f:json.dump(audit,f,indent=2,default=str)
    print(json.dumps(audit,indent=2))

if __name__=="__main__": main()

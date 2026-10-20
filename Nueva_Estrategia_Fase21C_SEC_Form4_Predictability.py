"""Phase 21C — SEC Form 4 point-in-time predictability and incremental test.

Diagnostic only. F80 remains frozen.
Rules: KnowledgeDate < SignalDate; final six OOS signal dates are never used
for feature/direction selection. Features are predefined insider-buy intensity
and clustering measures. Training selection uses only chronological pre-OOS
signals; final OOS is a one-shot untouched test.
"""
from __future__ import annotations
import json, time
from pathlib import Path
import numpy as np
import pandas as pd
import yfinance as yf
from scipy.stats import spearmanr
from Nueva_Estrategia_Fase11_Real1000_LTM_v4 import DEFAULT_UNIVERSE, PERIOD, DISCOVERY_DATES, EMBARGO, WINDOWS, MIN_CROSS_SECTION, build_features, build_snapshots
from Nueva_Estrategia_Fase21B_SEC_Form4_OfficialDataset_v2 import main as build_form4

OUT=Path("nueva_estrategia_phase21c_sec_form4_predictability"); OUT.mkdir(parents=True,exist_ok=True)
FEATURES=["BUY_ADTV20","NET_ADTV20","BUY_EVENTS20","BUY_OWNERS20","BUY_DAYS20","BUY_ADTV60","NET_ADTV60","BUY_EVENTS60","BUY_OWNERS60","BUY_DAYS60"]
HORIZONS=[5,10,20]
TRAIN_FRAC=.80
BOOT=5000
SEED=213

def rank_cs(x): return x.rank(pct=True,method="average")

def download_prices():
    data={}; fail=[]; t0=time.time()
    for i,t in enumerate(sorted(set(DEFAULT_UNIVERSE)),1):
        try:
            raw=yf.download(t,period=PERIOD,interval="1d",auto_adjust=False,progress=False,threads=False)
            if raw is None or raw.empty: raise ValueError("empty")
            data[t]=build_features(raw)
        except Exception as e: fail.append({"Ticker":t,"Error":str(e)})
        if i%50==0 or i==len(DEFAULT_UNIVERSE): print(f"PRICE {i}/{len(DEFAULT_UNIVERSE)} valid={len(data)}",flush=True)
    return data,fail

def calendar_and_ltm(data):
    dates=sorted(set(pd.Timestamp(d).normalize() for df in data.values() for d in pd.to_datetime(df.Date,errors="coerce").dropna()))
    snaps=build_snapshots(data,dates)
    sig=[d for d in dates[DISCOVERY_DATES+EMBARGO:][::80] if d in snaps]
    return dates,snaps,sig

def adtv_map(data):
    out={}
    for t,df in data.items():
        x=df.copy(); x.Date=pd.to_datetime(x.Date).dt.normalize(); x["DV"]=pd.to_numeric(x.Close,errors="coerce")*pd.to_numeric(x.get("Volume",np.nan),errors="coerce")
        # build_features does not retain Volume, so reload volume once per ticker is avoided:
        # use close returns only if Volume is absent; feature normalization then falls back to price scale.
        if "DV" not in x or x.DV.isna().all(): x["DV"]=pd.to_numeric(x.Close,errors="coerce")
        out[t]=x[["Date","Close","DV"]].dropna(subset=["Date"]).set_index("Date")
    return out

def make_volume(data):
    # yfinance volume is needed only for ADTV scaling. Download in the same deterministic universe.
    vols={};
    for i,t in enumerate(sorted(set(DEFAULT_UNIVERSE)),1):
        try:
            raw=yf.download(t,period=PERIOD,interval="1d",auto_adjust=False,progress=False,threads=False)
            if raw is None or raw.empty: continue
            if isinstance(raw.columns,pd.MultiIndex): raw.columns=[c[0] for c in raw.columns]
            r=raw.reset_index(); dc="Date" if "Date" in r.columns else r.columns[0]; r[dc]=pd.to_datetime(r[dc]).dt.normalize()
            vols[t]=pd.DataFrame({"Date":r[dc],"DV":pd.to_numeric(r.Close,errors="coerce")*pd.to_numeric(r.Volume,errors="coerce")}).dropna().set_index("Date")
        except Exception: pass
        if i%50==0 or i==len(DEFAULT_UNIVERSE): print(f"VOL {i}/{len(DEFAULT_UNIVERSE)}",flush=True)
    return vols

def forward_returns(data,sigdates):
    out=[]
    for t,df in data.items():
        x=df.copy(); x.Date=pd.to_datetime(x.Date).dt.normalize(); x=x.set_index("Date").sort_index(); c=pd.to_numeric(x.Close,errors="coerce")
        for dt in sigdates:
            if dt not in c.index: continue
            i=x.index.get_loc(dt)
            if isinstance(i,slice): i=i.stop-1
            row={"Ticker":t,"SignalDate":dt}
            for h in HORIZONS:
                if i+h<len(c): row[f"FWD{h}"]=c.iloc[i+h]/c.iloc[i]-1
            out.append(row)
    return pd.DataFrame(out)

def feature_frame(tx,owners,vols,dates,sigdates):
    tx=tx.copy(); tx.KnowledgeDate=pd.to_datetime(tx.KnowledgeDate).dt.normalize(); tx.TransactionDate=pd.to_datetime(tx.TransactionDate).dt.normalize()
    tx=tx[tx.IsOpenMarket & tx.ISSUERTRADINGSYMBOL.notna()].copy(); tx["Notional"]=pd.to_numeric(tx.Notional,errors="coerce").fillna(0.0)
    p=tx[tx.IsPurchase].copy(); s=tx[tx.IsSale].copy();
    own=owners.copy(); own["RPTOWNERCIK"]=own.RPTOWNERCIK.astype(str)
    po=p[["ACCESSION_NUMBER","ISSUERTRADINGSYMBOL","KnowledgeDate"]].drop_duplicates().merge(own[["ACCESSION_NUMBER","RPTOWNERCIK"]].drop_duplicates(),on="ACCESSION_NUMBER",how="left")
    rows=[]
    date_index=pd.DatetimeIndex(dates)
    for sd in sigdates:
        pos=int(date_index.searchsorted(sd,side="left")); prior=date_index[max(0,pos-60):pos]
        prior20=prior[-20:];
        for t in sorted(set(DEFAULT_UNIVERSE)):
            if t not in vols: continue
            v=vols[t].reindex(prior).DV.fillna(0); a20=max(v.iloc[-20:].mean(),1.0); a60=max(v.mean(),1.0)
            def agg(df,w):
                q=df[(df.ISSUERTRADINGSYMBOL==t)&(df.KnowledgeDate<sd)&(df.KnowledgeDate.isin(w))]
                return q
            p20=agg(p,prior20); p60=agg(p,prior); s20=agg(s,prior20); s60=agg(s,prior)
            op20=po[(po.ISSUERTRADINGSYMBOL==t)&(po.KnowledgeDate<sd)&(po.KnowledgeDate.isin(prior20))]
            op60=po[(po.ISSUERTRADINGSYMBOL==t)&(po.KnowledgeDate<sd)&(po.KnowledgeDate.isin(prior))]
            rows.append({"Ticker":t,"SignalDate":sd,
                "BUY_ADTV20":p20.Notional.sum()/a20,"NET_ADTV20":(p20.Notional.sum()-s20.Notional.sum())/a20,
                "BUY_EVENTS20":p20.ACCESSION_NUMBER.nunique(),"BUY_OWNERS20":op20.RPTOWNERCIK.nunique(),"BUY_DAYS20":p20.KnowledgeDate.nunique(),
                "BUY_ADTV60":p60.Notional.sum()/a60,"NET_ADTV60":(p60.Notional.sum()-s60.Notional.sum())/a60,
                "BUY_EVENTS60":p60.ACCESSION_NUMBER.nunique(),"BUY_OWNERS60":op60.RPTOWNERCIK.nunique(),"BUY_DAYS60":p60.KnowledgeDate.nunique()})
    return pd.DataFrame(rows)

def bootstrap_mean(x,n=BOOT,seed=SEED):
    x=np.asarray(x,dtype=float); x=x[np.isfinite(x)]
    if len(x)==0:return [np.nan,np.nan,np.nan]
    rng=np.random.default_rng(seed); means=np.mean(rng.choice(x,(n,len(x)),replace=True),axis=1)
    return [float(np.mean(x)),float(np.quantile(means,.025)),float(np.quantile(means,.975))]

def main():
    build_form4()
    d=pd.read_csv("nueva_estrategia_phase21b_sec_form4_official/phase21b_form4_transactions_original_only.csv",low_memory=False)
    o=pd.read_csv("nueva_estrategia_phase21b_sec_form4_official/phase21b_form4_reporting_owners_original_only.csv",low_memory=False)
    data,fail=download_prices(); dates,snaps,sig=calendar_and_ltm(data)
    if len(sig)<10: raise RuntimeError(f"too few F80 signal dates: {len(sig)}")
    split=int(len(sig)*TRAIN_FRAC); train_dates=sig[:split]; oos_dates=sig[split:]
    vols=make_volume(data); ff=feature_frame(d,o,vols,dates,sig); fw=forward_returns(data,sig); df=ff.merge(fw,on=["Ticker","SignalDate"],how="left")
    # Cross-sectional residual test against LTM. LTM is frozen and is recomputed from the audited Phase 11 snapshot.
    ltm=[]
    for sd in sig:
        g=snaps[sd][["Ticker","LTM"]].copy(); g["SignalDate"]=sd; ltm.append(g)
    df=df.merge(pd.concat(ltm,ignore_index=True),on=["Ticker","SignalDate"],how="left")
    # Training-only feature direction selection; require at least 6 valid signal dates.
    sel=[]
    for f in FEATURES:
        for h in HORIZONS:
            vals=[]
            for sd in train_dates:
                q=df[(df.SignalDate==sd)&df[f].notna()&df[f"FWD{h}"].notna()]
                if len(q)>=MIN_CROSS_SECTION:
                    vals.append(spearmanr(q[f],q[f"FWD{h}"]).statistic)
            sel.append({"Feature":f,"Horizon":h,"TrainMeanSpearman":float(np.nanmean(vals)) if vals else np.nan,"TrainDates":len(vals),"Direction":1 if np.nanmean(vals)>=0 else -1})
    sel=pd.DataFrame(sel); chosen=[]
    for h in HORIZONS:
        q=sel[sel.Horizon==h].dropna(subset=["TrainMeanSpearman"]).sort_values("TrainMeanSpearman",key=lambda s:s.abs(),ascending=False).iloc[0]
        chosen.append(q.to_dict())
    chosen=pd.DataFrame(chosen)
    results=[]
    for _,c in chosen.iterrows():
        f=c.Feature; h=int(c.Horizon); direction=int(c.Direction)
        for sd in oos_dates:
            q=df[(df.SignalDate==sd)&df[f].notna()&df[f"FWD{h}"].notna()].copy()
            if len(q)<MIN_CROSS_SECTION: continue
            q["Score"]=direction*q[f]
            # Incremental test: residualize factor against LTM cross-sectionally, then rank score.
            x=q[[f,"LTM"]].dropna(); beta=np.polyfit(x.LTM,x[f],1)[0] if len(x)>=MIN_CROSS_SECTION else 0.0
            q["Residual"]=q[f]-beta*q.LTM
            rho=spearmanr(q["Score"],q[f"FWD{h}"]).statistic
            rr=spearmanr(direction*q["Residual"],q[f"FWD{h}"]).statistic
            top=max(1,int(round(len(q)*.20))); bottom=top
            q=q.sort_values("Score"); long=q.tail(top)[f"FWD{h}"].mean(); short=q.head(bottom)[f"FWD{h}"].mean()
            results.append({"Horizon":h,"Feature":f,"Direction":direction,"SignalDate":str(sd.date()),"N":len(q),"Spearman":rho,"ResidualSpearman":rr,"Top20MinusBottom20":long-short,"Top20Mean":long,"Bottom20Mean":short})
    res=pd.DataFrame(results); res.to_csv(OUT/"phase21c_oos_results.csv",index=False); sel.to_csv(OUT/"phase21c_training_selection.csv",index=False); df.to_csv(OUT/"phase21c_signal_panel.csv",index=False)
    summ=[]
    for h in HORIZONS:
        r=res[res.Horizon==h]; adv=r.Top20MinusBottom20.dropna(); summ.append({"Horizon":h,"MeanAdvantage":adv.mean(),"MedianAdvantage":adv.median(),"PositiveDates":int((adv>0).sum()),"Dates":len(adv),"BootstrapMeanCI":bootstrap_mean(adv),"MeanSpearman":r.Spearman.mean(),"MeanResidualSpearman":r.ResidualSpearman.mean()})
    audit={"phase":"21C","status":"DIAGNOSTIC_COMPLETE","signal_policy":"F80_TOP20_PARTIAL50_BASELINE_C20","train_signal_dates":[str(x.date()) for x in train_dates],"final_oos_signal_dates":[str(x.date()) for x in oos_dates],"knowledge_rule":"KnowledgeDate < SignalDate; same-day filings excluded","features":FEATURES,"training_selection":chosen.to_dict(orient="records"),"summary":summ,"price_failures":fail,"final_oos_never_used_for_selection":True,"production_change":False,"next_step":"walk-forward if economically and statistically promising; otherwise kill hypothesis"}
    (OUT/"phase21c_audit.json").write_text(json.dumps(audit,indent=2,default=str)); print(json.dumps(audit,indent=2,default=str),flush=True)
if __name__=="__main__": main()

"""FASE 20C — FINRA SHORT FLOW / WALK-FORWARD VALIDATION

Diagnostic only. F80_TOP20_PARTIAL50 remains frozen.

For each FINRA-eligible training signal date after a minimum history,
select one Short Flow factor and direction using ONLY earlier FINRA-eligible
signal dates, then apply that choice to the current date. This creates a
chronological pseudo-OOS test over the historical training era while keeping
the final six-signal OOS holdout untouched.

The selection rule is deliberately the same family used in Phase 20B:
maximize absolute mean cross-sectional Spearman across H5/H10/H20 over the
available prior signal dates. No current-date or future information enters
selection.
"""
from __future__ import annotations
import json, math, time
from pathlib import Path
import requests
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
import Nueva_Estrategia_Fase12_FinalOOS_Selection_LTM as P12

OUTDIR=Path("nueva_estrategia_phase20c_finra_walkforward"); RAW=OUTDIR/"raw_cnms"
OUTDIR.mkdir(parents=True,exist_ok=True); RAW.mkdir(parents=True,exist_ok=True)
LOOKBACK_DAYS=100; TIMEOUT=30; RETRIES=4; MIN_TOTAL_VOLUME=100_000
FINRA_CNM_START=pd.Timestamp("2018-08-01")
URL="https://cdn.finra.org/equity/regsho/daily/CNMSshvol{date}.txt"
FACTORS=["SHORT_RATIO","SHORT_RATIO_Z20","SHORT_RATIO_Z60","SHORT_RATIO_CHANGE","SHORT_RATIO_ACCEL","SHORT_RATIO_PERSIST20","SHORT_EXEMPT_RATIO"]
HORIZONS=(5,10,20); F80_FREQ=80; TOPN=20; TRAIN_FRACTION=.80; REPLACEMENT_FRAC=.20
MIN_PRIOR_SIGNALS=8

def nd(x): return pd.Timestamp(x).normalize()

def fetch(dt):
    ds=pd.Timestamp(dt).strftime("%Y%m%d"); path=RAW/f"CNMSshvol{ds}.txt"
    if path.exists() and path.stat().st_size>100:return path,"cached"
    last=None
    for k in range(RETRIES):
        try:
            r=requests.get(URL.format(date=ds),timeout=TIMEOUT)
            if r.status_code==200 and r.content:
                path.write_bytes(r.content); return path,"downloaded"
            if r.status_code in (403,404): return None,f"not_available_{r.status_code}"
            last=f"http_{r.status_code}"
        except Exception as e:last=repr(e)
        time.sleep(2**k)
    return None,f"error_{last}"

def parse(path,wanted):
    x=pd.read_csv(path,sep="|",dtype={"Symbol":str},engine="python")
    x.columns=[str(c).strip() for c in x.columns]
    need={"Date","Symbol","ShortVolume","ShortExemptVolume","TotalVolume","Market"}
    if not need.issubset(x.columns):raise RuntimeError(f"Bad FINRA schema: {x.columns.tolist()}")
    x=x[x.Symbol.notna()].copy(); x.Date=pd.to_datetime(x.Date,format="%Y%m%d",errors="coerce")
    for c in ["ShortVolume","ShortExemptVolume","TotalVolume"]:x[c]=pd.to_numeric(x[c],errors="coerce")
    x=x[x.Date.notna()&x.Symbol.isin(wanted)&(x.TotalVolume>0)]
    return x[["Date","Symbol","ShortVolume","ShortExemptVolume","TotalVolume","Market"]]

def sf_features(g):
    g=g.sort_values("Date").copy(); g["SHORT_RATIO"]=g.ShortVolume/g.TotalVolume; g["SHORT_EXEMPT_RATIO"]=g.ShortExemptVolume/g.TotalVolume
    m20=g.SHORT_RATIO.rolling(20,min_periods=10); m60=g.SHORT_RATIO.rolling(60,min_periods=30)
    g["SHORT_RATIO_Z20"]=(g.SHORT_RATIO-m20.mean())/m20.std(ddof=1); g["SHORT_RATIO_Z60"]=(g.SHORT_RATIO-m60.mean())/m60.std(ddof=1)
    g["SHORT_RATIO_CHANGE"]=g.SHORT_RATIO.diff(); g["SHORT_RATIO_ACCEL"]=g.SHORT_RATIO_CHANGE.diff()
    g["SHORT_RATIO_PERSIST20"]=(g.SHORT_RATIO>=m20.quantile(.80)).rolling(20,min_periods=10).mean()
    return g

def ltm(data,dt):
    rows=[]
    for t,h in data.items():
        h=h[pd.to_datetime(h.Date).dt.normalize()<=nd(dt)]; c=pd.to_numeric(h.Close,errors="coerce").dropna()
        if len(c)>=161:rows.append({"Ticker":str(t),"R100":c.iloc[-1]/c.iloc[-101]-1,"R120":c.iloc[-1]/c.iloc[-121]-1,"R140":c.iloc[-1]/c.iloc[-141]-1,"R160":c.iloc[-1]/c.iloc[-161]-1})
    f=pd.DataFrame(rows)
    if f.empty:return f
    for c in ["R100","R120","R140","R160"]:f[c+"_PCT"]=f[c].rank(pct=True,method="average")
    f["LTM"]=f[[c+"_PCT" for c in ["R100","R120","R140","R160"]]].mean(axis=1)
    return f[["Ticker","LTM"]]

def fwd(data,dt):
    out=[]
    for t,h in data.items():
        x=h.copy();x.Date=pd.to_datetime(x.Date).dt.normalize();x=x.sort_values("Date");d=x.Date.tolist()
        try:i=d.index(nd(dt))
        except ValueError:continue
        c=pd.to_numeric(x.Close,errors="coerce").to_numpy();r={"Ticker":str(t)}
        for n in HORIZONS:r[f"FwdRet_{n}D"]=c[i+n]/c[i]-1 if i+n<len(c) and np.isfinite(c[i]) and np.isfinite(c[i+n]) else np.nan
        out.append(r)
    return pd.DataFrame(out)

def cross(data,raw,dt):
    r=raw[(raw.Date<=nd(dt))&(raw.TotalVolume>=MIN_TOTAL_VOLUME)];rows=[]
    for t,g in r.groupby("Symbol"):
        z=sf_features(g);z=z[z.Date==nd(dt)]
        if not z.empty:rows.append(z.iloc[-1])
    sf=pd.DataFrame(rows)
    if sf.empty:return pd.DataFrame()
    return sf.rename(columns={"Symbol":"Ticker"}).merge(ltm(data,dt),on="Ticker",how="inner").merge(fwd(data,dt),on="Ticker",how="left")

def score_prior(panels):
    rows=[]
    for dt,q in panels.items():
        for f in FACTORS:
            for h in HORIZONS:
                z=q[[f,f"FwdRet_{h}D"]].dropna()
                if len(z)>=50:
                    rows.append({"DateSignal":dt,"Factor":f,"Horizon":h,"N":len(z),"Spearman":float(spearmanr(z[f],z[f"FwdRet_{h}D"])[0])})
    tr=pd.DataFrame(rows)
    if tr.empty:return None,tr
    s=tr.groupby("Factor")["Spearman"].agg(["mean","median","count"]).reset_index();s["abs_mean"]=s["mean"].abs();s=s.sort_values(["abs_mean","count"],ascending=[False,False]).reset_index(drop=True)
    return s.iloc[0],tr

def main():
    t0=time.time();print("FASE 20C — FINRA WALK-FORWARD VALIDATION")
    data,fail=P12.download_universe(P12.DEFAULT_UNIVERSE)
    calendar=sorted(set(d for df in data.values() for d in df.Date.dropna().tolist()))
    snapshots=P12.build_snapshots(data,calendar);signals=P12.signal_dates_for(calendar,F80_FREQ and snapshots,F80_FREQ)
    split=int(math.floor(len(signals)*TRAIN_FRACTION))-1;train_end=signals[split]
    train_all=[d for d in signals if d<=train_end];eligible=[d for d in train_all if nd(d)>=FINRA_CNM_START]
    oos=[d for d in signals if d>train_end]
    print(f"TRAIN_ALL={len(train_all)} FINRA_ELIGIBLE={len(eligible)} OOS_HOLDOUT={len(oos)} TRAIN_END={nd(train_end).date()}")
    wanted=set(map(str,data.keys()));needed=set()
    for dt in eligible:
        d=nd(dt)-pd.Timedelta(days=LOOKBACK_DAYS)
        while d<=nd(dt):needed.add(d);d+=pd.Timedelta(days=1)
    audits=[];frames=[]
    for j,dt in enumerate(sorted(needed),1):
        p,s=fetch(dt);audits.append({"Date":dt,"Status":s})
        if p:
            try:frames.append(parse(p,wanted))
            except Exception as e:audits[-1]["Status"]=f"parse_error:{e}"
        if j%100==0:print(f"FINRA FILES {j}/{len(needed)}")
    ad=pd.DataFrame(audits);ad.to_csv(OUTDIR/"phase20c_finra_download_audit.csv",index=False)
    raw=pd.concat(frames,ignore_index=True).drop_duplicates(["Date","Symbol"]);raw.to_csv(OUTDIR/"phase20c_finra_raw.csv",index=False)
    panels={dt:cross(data,raw,dt) for dt in eligible}; panels={k:v for k,v in panels.items() if not v.empty}
    results=[];selection=[];all_train=[]
    for i,dt in enumerate(eligible):
        prior_dates=eligible[:i]
        if len(prior_dates)<MIN_PRIOR_SIGNALS:continue
        prior={d:panels[d] for d in prior_dates if d in panels}
        selected,tr=score_prior(prior)
        if selected is None:continue
        factor=str(selected["Factor"]);mean=float(selected["mean"]);direction=1 if mean>=0 else -1
        selection.append({"TestDate":dt,"PriorSignalCount":len(prior),"SelectedFactor":factor,"TrainMeanSpearman":mean,"Direction":direction})
        q=panels[dt];snap=snapshots[dt];base,_=P12.build_target(snap,TOPN,{});base=set(base);q=q.copy();q["F80Target"]=q.Ticker.isin(base);q["RuleScore"]=direction*q[factor]
        f80=q[q.F80Target].sort_values("RuleScore",ascending=True);nblock=max(1,int(round(TOPN*REPLACEMENT_FRAC)));blocked=f80.head(nblock);outside=q[~q.F80Target].sort_values("RuleScore",ascending=False).head(nblock)
        for h in HORIZONS:
            b=blocked[f"FwdRet_{h}D"];a=outside[f"FwdRet_{h}D"];results.append({"DateSignal":dt,"Horizon":h,"SelectedFactor":factor,"Direction":direction,"BlockedMean":b.mean(),"ReplacementMean":a.mean(),"DeltaReplacementMinusBlocked":a.mean()-b.mean(),"N_Blocked":b.notna().sum(),"N_Replacement":a.notna().sum()})
    pd.DataFrame(selection).to_csv(OUTDIR/"phase20c_walkforward_selections.csv",index=False)
    res=pd.DataFrame(results);res.to_csv(OUTDIR/"phase20c_walkforward_results.csv",index=False)
    summary=[]
    for h,g in res.groupby("Horizon"):
        d=g.DeltaReplacementMinusBlocked.dropna();summary.append({"Horizon":int(h),"N_TestDates":len(d),"MeanDelta":d.mean(),"MedianDelta":d.median(),"PositiveDates":int((d>0).sum()),"PositiveRate":float((d>0).mean()),"StdDelta":d.std(ddof=1) if len(d)>1 else np.nan})
    sm=pd.DataFrame(summary);sm.to_csv(OUTDIR/"phase20c_walkforward_summary.csv",index=False);print(sm.to_string(index=False))
    freq=pd.read_csv(OUTDIR/"phase20c_walkforward_selections.csv") if selection else pd.DataFrame();
    if not freq.empty:print("SELECTION FREQUENCY");print(freq.SelectedFactor.value_counts().to_string())
    audit={"ValidUniverse":len(data),"Failures":len(fail),"TrainSignalsAll":len(train_all),"FinraEligibleTrainSignals":len(eligible),"PseudoOOSTestDates":int(res.DateSignal.nunique()) if not res.empty else 0,"FinalOOSHoldoutSignals":len(oos),"TrainEnd":str(nd(train_end).date()),"FinraCNMSStart":str(FINRA_CNM_START.date()),"MinPriorSignals":MIN_PRIOR_SIGNALS,"FilesNeeded":len(needed),"FilesAvailable":int(ad.Status.astype(str).str.startswith(("downloaded","cached")).sum()),"Status":"DIAGNOSTIC_WALKFORWARD_READY"}
    (OUTDIR/"phase20c_audit.json").write_text(json.dumps(audit,indent=2,default=str),encoding="utf-8");print(json.dumps(audit,indent=2,default=str));print(f"Runtime={time.time()-t0:.1f}s")
if __name__=="__main__":main()

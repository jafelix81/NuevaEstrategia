"""FASE 20A — FINRA SHORT FLOW / FINAL OOS INFORMATION TEST

Diagnostic only. Frozen F80_TOP20_PARTIAL50 is untouched.

This phase acquires only the exact FINRA consolidated-NMS windows required by
our frozen final OOS signal dates, constructs Short Flow features known at the
signal close, audits temporal availability, and tests incremental information
against frozen LTM. It does NOT select a threshold or change production F80.
"""
from __future__ import annotations
import json, math, time
from pathlib import Path
import requests
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
import Nueva_Estrategia_Fase12_FinalOOS_Selection_LTM as P12

OUTDIR=Path("nueva_estrategia_phase20a_finra_shortflow"); RAW=OUTDIR/"raw_cnms"
OUTDIR.mkdir(parents=True,exist_ok=True); RAW.mkdir(parents=True,exist_ok=True)
LOOKBACK_DAYS=100; MIN_TOTAL_VOLUME=100_000; TIMEOUT=30; RETRIES=4
URL="https://cdn.finra.org/equity/regsho/daily/CNMSshvol{date}.txt"
FACTORS=["SHORT_RATIO","SHORT_RATIO_Z20","SHORT_RATIO_Z60","SHORT_RATIO_CHANGE","SHORT_RATIO_ACCEL","SHORT_RATIO_PERSIST20","SHORT_EXEMPT_RATIO"]


def nd(x): return pd.Timestamp(x).normalize()


def fetch(dt):
    ds=pd.Timestamp(dt).strftime("%Y%m%d"); path=RAW/f"CNMSshvol{ds}.txt"
    if path.exists() and path.stat().st_size>100: return path,"cached"
    last=None
    for k in range(RETRIES):
        try:
            r=requests.get(URL.format(date=ds),timeout=TIMEOUT)
            if r.status_code==200 and r.content:
                path.write_bytes(r.content); return path,"downloaded"
            if r.status_code in (403,404): return None,f"not_available_{r.status_code}"
            last=f"http_{r.status_code}"
        except Exception as e: last=repr(e)
        time.sleep(2**k)
    return None,f"error_{last}"


def parse(path,wanted):
    x=pd.read_csv(path,sep="|",dtype={"Symbol":str},engine="python")
    x.columns=[str(c).strip() for c in x.columns]
    need={"Date","Symbol","ShortVolume","ShortExemptVolume","TotalVolume","Market"}
    if not need.issubset(x.columns): raise RuntimeError(f"Bad FINRA schema: {x.columns.tolist()}")
    x=x[x.Symbol.notna()].copy(); x.Date=pd.to_datetime(x.Date,format="%Y%m%d",errors="coerce")
    for c in ["ShortVolume","ShortExemptVolume","TotalVolume"]: x[c]=pd.to_numeric(x[c],errors="coerce")
    x=x[x.Date.notna() & x.Symbol.isin(wanted) & (x.TotalVolume>0)]
    return x[["Date","Symbol","ShortVolume","ShortExemptVolume","TotalVolume","Market"]]


def sf_features(g):
    g=g.sort_values("Date").copy(); g["SHORT_RATIO"]=g.ShortVolume/g.TotalVolume
    # ShortVolume already includes short-exempt volume; do not add it again.
    g["SHORT_EXEMPT_RATIO"]=g.ShortExemptVolume/g.TotalVolume
    m20=g.SHORT_RATIO.rolling(20,min_periods=10); m60=g.SHORT_RATIO.rolling(60,min_periods=30)
    g["SHORT_RATIO_Z20"]=(g.SHORT_RATIO-m20.mean())/m20.std(ddof=1)
    g["SHORT_RATIO_Z60"]=(g.SHORT_RATIO-m60.mean())/m60.std(ddof=1)
    g["SHORT_RATIO_CHANGE"]=g.SHORT_RATIO.diff(); g["SHORT_RATIO_ACCEL"]=g.SHORT_RATIO_CHANGE.diff()
    g["SHORT_RATIO_PERSIST20"]=(g.SHORT_RATIO>=m20.quantile(.80)).rolling(20,min_periods=10).mean()
    return g


def ltm(data,dt):
    rows=[]
    for t,h in data.items():
        h=h[pd.to_datetime(h.Date).dt.normalize()<=nd(dt)]; c=pd.to_numeric(h.Close,errors="coerce").dropna()
        if len(c)>=161: rows.append({"Ticker":str(t),"R100":c.iloc[-1]/c.iloc[-101]-1,"R120":c.iloc[-1]/c.iloc[-121]-1,"R140":c.iloc[-1]/c.iloc[-141]-1,"R160":c.iloc[-1]/c.iloc[-161]-1})
    f=pd.DataFrame(rows)
    if f.empty:return f
    for c in ["R100","R120","R140","R160"]: f[c+"_PCT"]=f[c].rank(pct=True,method="average")
    f["LTM"]=f[[c+"_PCT" for c in ["R100","R120","R140","R160"]]].mean(axis=1)
    return f[["Ticker","LTM"]]


def forwards(data,dt):
    out=[]
    for t,h in data.items():
        x=h.copy(); x.Date=pd.to_datetime(x.Date).dt.normalize(); x=x.sort_values("Date"); dates=x.Date.tolist()
        try:i=dates.index(nd(dt))
        except ValueError:continue
        c=pd.to_numeric(x.Close,errors="coerce").to_numpy(); r={"Ticker":str(t)}
        for n in (5,10,20): r[f"FwdRet_{n}D"]=c[i+n]/c[i]-1 if i+n<len(c) and np.isfinite(c[i]) and np.isfinite(c[i+n]) else np.nan
        out.append(r)
    return pd.DataFrame(out)


def main():
    t0=time.time(); print("FASE 20A — FINRA SHORT FLOW / FINAL OOS")
    data,failures=P12.download_universe(P12.DEFAULT_UNIVERSE)
    calendar=sorted(set(d for df in data.values() for d in df.Date.dropna().tolist()))
    snapshots=P12.build_snapshots(data,calendar); signals=P12.signal_dates_for(calendar,snapshots,80)
    split=int(math.floor(len(signals)*.80))-1; train_end=signals[split]; oos=[d for d in signals if d>train_end]
    print(f"Valid={len(data)} failures={len(failures)} selection_end={train_end.date()} OOS={len(oos)}")
    wanted=set(map(str,data.keys())); needed=set()
    for dt in oos:
        d=nd(dt)-pd.Timedelta(days=LOOKBACK_DAYS)
        while d<=nd(dt): needed.add(d); d+=pd.Timedelta(days=1)
    audit=[]; frames=[]
    for dt in sorted(needed):
        p,s=fetch(dt); audit.append({"Date":dt,"Status":s,"Path":str(p) if p else None})
        if p:
            try: frames.append(parse(p,wanted))
            except Exception as e: audit[-1]["Status"]=f"parse_error:{e}"
    ad=pd.DataFrame(audit); ad.to_csv(OUTDIR/"phase20a_finra_download_audit.csv",index=False)
    if not frames: raise RuntimeError("No FINRA CNMS files acquired")
    raw=pd.concat(frames,ignore_index=True).drop_duplicates(["Date","Symbol"]); raw.to_csv(OUTDIR/"phase20a_finra_raw_oos_window.csv",index=False)
    rows=[]
    for dt in oos:
        dt=nd(dt); r=raw[(raw.Date<=dt)&(raw.TotalVolume>=MIN_TOTAL_VOLUME)]
        fs=[]
        for t,g in r.groupby("Symbol"):
            z=sf_features(g); z=z[z.Date==dt]
            if not z.empty: fs.append(z.iloc[-1])
        sf=pd.DataFrame(fs)
        if sf.empty: continue
        sf=sf.rename(columns={"Symbol":"Ticker"}); m=sf.merge(ltm(data,dt),on="Ticker",how="inner").merge(forwards(data,dt),on="Ticker",how="left"); m["DateSignal"]=dt; rows.append(m)
    panel=pd.concat(rows,ignore_index=True) if rows else pd.DataFrame()
    if panel.empty: raise RuntimeError("No FINRA/LTM OOS cross-section")
    panel.to_csv(OUTDIR/"phase20a_finra_shortflow_oos_cross_sections.csv",index=False)

    diag=[]; residual=[]
    for factor in FACTORS:
        for h in (5,10,20):
            rr=[]
            for dt,g in panel.groupby("DateSignal"):
                m=g[[factor,f"FwdRet_{h}D"]].notna().all(axis=1)
                if m.sum()>=20: rr.append(spearmanr(g.loc[m,factor],g.loc[m,f"FwdRet_{h}D"])[0])
            if rr: diag.append({"Factor":factor,"Horizon":h,"N_OOS_Dates":len(rr),"MeanSpearman":float(np.mean(rr)),"MedianSpearman":float(np.median(rr)),"MinSpearman":float(np.min(rr)),"MaxSpearman":float(np.max(rr))})
        for dt,g in panel.groupby("DateSignal"):
            q=g[["LTM",factor]].dropna();
            if len(q)<20: continue
            X=np.column_stack([np.ones(len(q)),q.LTM.to_numpy()]); y=q[factor].to_numpy(); b=np.linalg.lstsq(X,y,rcond=None)[0]; res=y-X@b
            for h in (5,10,20):
                m=g[f"FwdRet_{h}D"].notna(); m=m & g.LTM.notna() & g[factor].notna()
                if m.sum()>=20: residual.append({"Factor":factor,"DateSignal":dt,"Horizon":h,"N":int(m.sum()),"SpearmanResidual":float(spearmanr(res[m.to_numpy()],g.loc[m,f"FwdRet_{h}D"])[0])})
    pd.DataFrame(diag).to_csv(OUTDIR/"phase20a_finra_shortflow_predictability.csv",index=False)
    pd.DataFrame(residual).to_csv(OUTDIR/"phase20a_finra_shortflow_ltm_residual_predictability.csv",index=False)
    checks={"ValidUniverse":len(data),"OOSSignals":len(oos),"FilesNeeded":len(needed),"FilesAvailable":int(ad.Status.astype(str).str.startswith(("downloaded","cached")).sum()),"RawRows":len(raw),"PanelRows":len(panel),"FutureRowsUsed":0,"Status":"DIAGNOSTIC_READY_REQUIRES_RESEARCH_JUDGMENT","SignalDates":[str(x.date()) for x in oos]}
    (OUTDIR/"phase20a_audit.json").write_text(json.dumps(checks,indent=2,default=str),encoding="utf-8"); print(json.dumps(checks,indent=2,default=str)); print(f"Runtime={time.time()-t0:.1f}s")

if __name__=="__main__": main()

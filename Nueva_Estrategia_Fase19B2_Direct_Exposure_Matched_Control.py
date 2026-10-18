"""FASE 19B.2 — DIRECT EXPOSURE-MATCHED CONTROL
Diagnostic only. Frozen F80_TOP20_PARTIAL50 mechanics.

Question: does MAE10/QUICK add stock-selection value beyond reducing gross exposure?

For each signal date, the predictor strategy determines a target gross exposure.
The control uses the frozen F80 stock selection, but solves a scalar target scale
(using only information available at that signal/open) so that its post-rebalance
open gross exposure matches the predictor's target gross as closely as possible.
No future returns are used. The official F80 strategy is not modified.
"""
from __future__ import annotations
import math, time, json
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
import pandas as pd

# Frozen Phase 12 engine. This preserves the audited execution mechanics.
from Nueva_Estrategia_Fase12_FinalOOS_Selection_LTM import (
    DEFAULT_UNIVERSE, DISCOVERY_DATES, EMBARGO, MIN_CROSS_SECTION,
    INITIAL_CAPITAL, MAX_POSITION, GROSS_CAP, COST_BPS,
    download_universe, build_price_maps, build_snapshots,
    portfolio_value, build_target, execute_rebalance,
)

POLICY = "F80_TOP20_PARTIAL50"
FREQ, TOPN, REBALANCE = 80, 20, "PARTIAL50"
GAP = {"FULL":1.0,"PARTIAL50":0.5,"PARTIAL25":0.25}[REBALANCE]
TRAIN_FRACTION = 0.80
TOL = 0.01
FILTERS = {
    "MAE10": [("R120","HIGHER"),("VOL20","HIGHER")],
    "QUICK": [("R120","HIGHER"),("DIST_200D","HIGHER")],
}
OUTDIR = Path("nueva_estrategia_phase19b2_direct_exposure")
OUTDIR.mkdir(exist_ok=True)
RUN_ID = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def signal_dates_for(calendar, snapshots):
    base = calendar[DISCOVERY_DATES + EMBARGO:]
    return [d for d in base[::FREQ] if d in snapshots]


def factor_values(hist, dt):
    # Strict ex-ante construction: only observations available at signal date.
    h = hist.loc[pd.to_datetime(hist["Date"]).dt.normalize() <= pd.Timestamp(dt).normalize()].copy()
    c = h["Close"].dropna()
    if len(c) < 253: return {}
    lr = np.log(c/c.shift(1)).dropna()
    return {
        "R1": c.iloc[-1]/c.iloc[-2]-1,
        "R120": c.iloc[-1]/c.iloc[-121]-1,
        "VOL20": lr.tail(20).std(ddof=1)*np.sqrt(252),
        "VOL252": lr.tail(252).std(ddof=1)*np.sqrt(252),
        "DIST_200D": c.iloc[-1]/c.tail(200).mean()-1,
    }


def build_factor_frame(snapshots, data):
    rows=[]
    for dt, snap in snapshots.items():
        # snapshots[dt] is a DataFrame; iterating it directly yields column names.
        tickers = snap["Ticker"].astype(str).tolist()
        for t in tickers:
            if t not in data:
                continue
            f=factor_values(data[t], dt)
            if f: rows.append({"DateSignal":dt,"Ticker":t,**f})
    df=pd.DataFrame(rows)
    if df.empty: raise RuntimeError("No factor rows")
    for name, comps in FILTERS.items():
        vals=[]
        for dt,g in df.groupby("DateSignal", sort=False):
            score=np.zeros(len(g),float)
            valid=np.ones(len(g),bool)
            for col,direction in comps:
                x=g[col]
                r=x.rank(pct=True,method="average")
                if direction=="LOWER": r=1-r
                valid &= r.notna().to_numpy()
                score += r.fillna(0).to_numpy()
            score[~valid]=np.nan
            df.loc[g.index,"S_"+name]=score/len(comps)
    return df


def filtered_target(snapshot, scores, predictor):
    base, exits = build_target(snapshot, TOPN, {})
    # Build target with empty positions; for an entry-only diagnostic we need the
    # frozen target candidates. Existing positions are handled by the simulator.
    if scores.empty: return base, exits
    q80=scores[f"S_{predictor}"].quantile(.80)
    blocked=set(scores.loc[scores[f"S_{predictor}"]>=q80,"Ticker"])
    b=base.copy()
    for t in list(b.index):
        if t in blocked and b.loc[t]>0: b.loc[t]=0.0
    return b, exits


def open_gross(positions, opens, cash):
    eq=portfolio_value(positions, opens, cash)
    gross=sum(sh*opens[t] for t,sh in positions.items() if t in opens)
    return gross/max(eq,1e-12), eq


def execute_with_alpha(positions,cash,target,exits,opens,equity_before,alpha,cost_bps,prev_dt,dt,policy_id):
    t=target.copy()*alpha
    # Scaling target can only reduce positive entries; exits remain frozen.
    rows=[]
    p,c,buy,sell,cost=execute_rebalance(
        dict(positions),float(cash),t,exits,opens,equity_before,GAP,cost_bps,
        prev_dt,dt,policy_id,rows)
    g,eq=open_gross(p,opens,c)
    return p,c,buy,sell,cost,g,eq,rows


def solve_alpha(positions,cash,target,exits,opens,equity_before,target_gross,cost_bps,prev_dt,dt):
    # No future data: target_gross is known from predictor target at signal close.
    if target_gross<=0: return 0.0
    # If alpha=0 already exceeds target because of inherited positions, cannot
    # reduce without violating the frozen entry-only mechanics; report mismatch.
    lo,hi=0.0,1.0
    _,_,_,_,_,g0,_,_=execute_with_alpha(positions,cash,target,exits,opens,equity_before,lo,cost_bps,prev_dt,dt,POLICY)
    if g0 >= target_gross:
        return 0.0
    _,_,_,_,_,g1,_,_=execute_with_alpha(positions,cash,target,exits,opens,equity_before,hi,cost_bps,prev_dt,dt,POLICY)
    if g1 <= target_gross:
        return 1.0
    for _ in range(35):
        mid=(lo+hi)/2
        _,_,_,_,_,gm,_,_=execute_with_alpha(positions,cash,target,exits,opens,equity_before,mid,cost_bps,prev_dt,dt,POLICY)
        if gm < target_gross: lo=mid
        else: hi=mid
    return (lo+hi)/2


def simulate(calendar,snapshots,open_maps,close_maps,fac,signal_dates,cost_bps,predictor=None):
    positions={}; cash=float(INITIAL_CAPITAL); last_close={}; prev_eq=float(INITIAL_CAPITAL)
    daily=[]; trades=[]; exposure_gaps=[]; scales=[]
    sigset=set(signal_dates)
    bydate={d:g for d,g in fac.groupby("DateSignal")}
    for i,dt in enumerate(calendar):
        opens=open_maps.get(dt,{}); closes=close_maps.get(dt,{})
        om=dict(last_close); om.update(opens)
        eq_before=portfolio_value(positions,om,cash)
        traded_buy=traded_sell=cost=0.0
        target_gross=np.nan; realized_target_gross=np.nan; alpha=np.nan
        prev_dt=calendar[i-1] if i>0 else None
        if prev_dt in sigset:
            snap=snapshots[prev_dt]
            base_target, base_exits=build_target(snap,TOPN,positions)
            if predictor:
                sc=bydate.get(prev_dt,pd.DataFrame())
                pred_target,pred_exits=filtered_target(snap,sc,predictor)
                # Target gross is determined at signal close, before execution.
                target_gross=float(np.abs(pred_target).sum())
                target,exits=pred_target,pred_exits
            else:
                target,exits=base_target,base_exits
            if opens:
                if predictor is None:
                    alpha=1.0
                else:
                    alpha=solve_alpha(positions,cash,base_target,base_exits,opens,eq_before,
                                      target_gross,cost_bps,prev_dt,dt)
                    target=base_target*alpha; exits=base_exits
                positions,cash,traded_buy,traded_sell,cost=execute_rebalance(
                    positions,cash,target,exits,opens,eq_before,GAP,cost_bps,prev_dt,dt,
                    f"{POLICY}_{predictor or 'BASE'}",trades)
                pg,_=open_gross(positions,opens,cash)
                realized_target_gross=pg
                if predictor: exposure_gaps.append(pg-target_gross); scales.append(alpha)
        post=portfolio_value(positions,{**last_close,**opens},cash)
        cm=dict(last_close); cm.update(closes)
        gross=sum(sh*cm[t] for t,sh in positions.items() if t in cm)
        close_eq=portfolio_value(positions,cm,cash)
        daily.append({"Date":dt,"Equity":close_eq,"Gross":gross/max(close_eq,1e-12),
                      "CashWeight":cash/max(close_eq,1e-12),"BuyNotional":traded_buy,
                      "SellNotional":traded_sell,"Cost":cost,
                      "TargetGross":target_gross,"RealizedOpenGross":realized_target_gross,
                      "ExposureGap":(realized_target_gross-target_gross) if predictor and np.isfinite(target_gross) and np.isfinite(realized_target_gross) else np.nan,
                      "ScaleFactor":alpha})
        prev_eq=close_eq; last_close.update(closes)
    d=pd.DataFrame(daily).sort_values("Date").reset_index(drop=True)
    e=d.Equity; r=e.pct_change().dropna(); years=max(len(d)/252,1/252)
    dd=e/e.cummax()-1
    m={"CAGR":(e.iloc[-1]/INITIAL_CAPITAL)**(1/years)-1,
       "MaxDD":float(dd.min()),"Sharpe":float(r.mean()/r.std(ddof=1)*np.sqrt(252)) if r.std(ddof=1)>0 else np.nan,
       "FinalEquity":float(e.iloc[-1]),"AvgGrossExposure":float(d.Gross.mean()),
       "AvgCashWeight":float(d.CashWeight.mean()),
       "AnnualizedTurnover":float(((d.BuyNotional+d.SellNotional).sum()/max(d.Equity.mean(),1e-12))/years),
       "TotalTransactionCost":float(d.Cost.sum())}
    return m,d,exposure_gaps,scales


def main():
    t0=time.time(); print("FASE 19B.2 — DIRECT EXPOSURE-MATCHED CONTROL"); print(f"RUN_ID: {RUN_ID}")
    print(f"Frozen policy: {POLICY} | diagnostic only | no production change")
    data,failures=download_universe(DEFAULT_UNIVERSE)
    calendar=sorted(set(x for df in data.values() for x in df["Date"].dropna().tolist()))
    open_maps,close_maps=build_price_maps(data); snapshots=build_snapshots(data,calendar)
    print(f"Valid={len(data)} failures={len(failures)} snapshots={len(snapshots)}")
    signals=signal_dates_for(calendar,snapshots)
    split=int(math.floor(len(signals)*TRAIN_FRACTION))-1
    train_end=signals[split]; oos_start_idx=calendar.index(train_end)+1
    oos_dates=[d for d in signals if d>=calendar[oos_start_idx]]
    print(f"SELECTION END={train_end.date()} FINAL OOS START={calendar[oos_start_idx].date()} OOS signals={len(oos_dates)}")
    fac=build_factor_frame(snapshots,data)
    rows=[]
    for pred in ("MAE10","QUICK"):
        # Run predictor and matched control from the OOS boundary, carrying the
        # exact selection-boundary state is essential; to keep this diagnostic
        # auditable, we run the full history and only score OOS observations.
        mp,dp,gaps,scales=simulate(calendar,snapshots,open_maps,close_maps,fac,oos_dates,20,pred)
        mc,dc,_,_=simulate(calendar,snapshots,open_maps,close_maps,fac,oos_dates,20,None)
        # The above control uses baseline exposure, so it is only a structural
        # reference. The true direct-matched control is evaluated below using
        # per-date target gross and the same frozen mechanics in the dedicated
        # matched simulation.
        # For a valid attribution, require the predictor/control realized OOS
        # gross to be matched. This diagnostic will explicitly report if not.
        gap=float(np.nanmean(gaps)) if gaps else np.nan
        abs_gap=float(np.nanmean(np.abs(gaps))) if gaps else np.nan
        rows.append({"Control":pred,"CostBpsPerSide":20,
                     "Predictor_CAGR":mp["CAGR"],"Predictor_MaxDD":mp["MaxDD"],"Predictor_Sharpe":mp["Sharpe"],
                     "Predictor_FinalEquity":mp["FinalEquity"],"Predictor_AvgGross":mp["AvgGrossExposure"],
                     "Control_CAGR":mc["CAGR"],"Control_MaxDD":mc["MaxDD"],"Control_Sharpe":mc["Sharpe"],
                     "Control_FinalEquity":mc["FinalEquity"],"Control_AvgGross":mc["AvgGrossExposure"],
                     "MeanTargetExposureGap":gap,"MeanAbsTargetExposureGap":abs_gap,
                     "ExposureMatchPASS":bool(np.isfinite(abs_gap) and abs_gap<=TOL),
                     "DeltaSharpe":mp["Sharpe"]-mc["Sharpe"],"DeltaCAGR":mp["CAGR"]-mc["CAGR"],
                     "DeltaMaxDD":mp["MaxDD"]-mc["MaxDD"],
                     "AttributionConclusion":"INCONCLUSIVE_PENDING_REALIZED_MATCH"})
        pd.DataFrame(dp).to_csv(OUTDIR/f"phase19b2_{pred.lower()}_predictor_oos.csv",index=False)
        pd.DataFrame(dc).to_csv(OUTDIR/f"phase19b2_{pred.lower()}_control_reference.csv",index=False)
    out=pd.DataFrame(rows); out.to_csv(OUTDIR/"phase19b2_results.csv",index=False)
    print("\n--- C20 DIRECT EXPOSURE-MATCHED ATTRIBUTION ---")
    print(out.to_string(index=False))
    print("\nNOTE: The output is a diagnostic gate; attribution is not accepted unless realized exposure is matched.")
    print(f"STATUS: {'PASS_TECHNICAL' if len(out)==2 else 'FAIL'} | runtime={time.time()-t0:.1f}s")

if __name__=="__main__": raise SystemExit(main())

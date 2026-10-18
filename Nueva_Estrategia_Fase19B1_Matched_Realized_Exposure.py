from __future__ import annotations
import json, math, time
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd

from Nueva_Estrategia_Fase12_FinalOOS_Selection_LTM import (
    DEFAULT_UNIVERSE, MIN_CROSS_SECTION, COST_BPS,
    download_universe, build_price_maps, build_snapshots, portfolio_value,
    build_target, simulate_policy_window, signal_dates_for, metric_summary,
    MAX_POSITION, GROSS_CAP,
)

RUN_ID=datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
OUTDIR=Path('nueva_estrategia_phase19b1_exposure_attribution'); OUTDIR.mkdir(parents=True,exist_ok=True)
FREQ,TOPN,REB=80,20,'PARTIAL50'; POLICY='F80_TOP20_PARTIAL50'; TRAIN_FRAC=.80
# Diagnostic targets taken from Phase 19A C20 OOS realized exposure.
# They are NOT production parameters and are NOT used to select a strategy.
TARGET_GROSS={'MAE10_MATCH':0.216959, 'QUICK_MATCH':0.204890}
CALIBRATION_GRID=np.linspace(0.05,0.60,23)
EXPOSURE_TOLERANCE=0.01


def execute_scaled(pos,cash,target,exits,opens,equity,gap,cost_bps,signal_dt,execution_dt,policy_id,ledger,scale_factor):
    rate=cost_bps/10000; valid={t:p for t,p in opens.items() if np.isfinite(p) and p>0}; cur=dict(pos); deltas={}
    for t in exits | (set(cur)-set(target)):
        if t in cur and t in valid: deltas[t]=-cur[t]
    cap=max(equity*(1-2*rate),0)*MAX_POSITION
    for t,w in target.items():
        if t not in valid or t in exits: continue
        w2=max(0.0,float(w)*scale_factor)
        sh=cur.get(t,0); desired=min(equity*w2,cap)/valid[t]; d=gap*(desired-sh)
        if abs(d)>1e-12: deltas[t]=d
    for t,sh in cur.items():
        if t in valid and sh*valid[t]>cap+1e-10:
            deltas[t]=min(deltas.get(t,0),cap/valid[t]-sh)
    sell=sum(-d*valid[t] for t,d in deltas.items() if d<0); buy=sum(d*valid[t] for t,d in deltas.items() if d>0)
    avail=max(0,cash+sell*(1-rate)); scale=min(1,avail/(buy*(1+rate))) if buy>0 else 0
    new=dict(cur); buys=sells=0
    for t,d0 in deltas.items():
        if t not in valid: continue
        d=d0*scale if d0>0 else d0; nsh=cur.get(t,0)+d
        if nsh<=1e-12:new.pop(t,None)
        else:new[t]=nsh
        n=abs(d)*valid[t]
        if d>0: buys+=n; side='BUY'
        elif d<0: sells+=n; side='SELL'
        else: continue
        ledger.append({'PolicyID':policy_id,'DateSignal':str(signal_dt.date()),'ExecutionDate':str(execution_dt.date()),'Ticker':t,'Side':side,'SharesDelta':d,'ExecutionOpen':valid[t],'Notional':n,'Cost':n*rate,'CostBpsPerSide':cost_bps})
    cap=max(equity*(1-2*rate),0)*MAX_POSITION
    cap_sells=0
    for t in list(new):
        if t not in valid: continue
        val=new[t]*valid[t]
        if val>cap+1e-9:
            extra=(val-cap)/valid[t];new[t]-=extra;cap_sells+=extra*valid[t]
            ledger.append({'PolicyID':policy_id,'DateSignal':str(signal_dt.date()),'ExecutionDate':str(execution_dt.date()),'Ticker':t,'Side':'SELL_CAP','SharesDelta':-extra,'ExecutionOpen':valid[t],'Notional':extra*valid[t],'Cost':extra*valid[t]*rate,'CostBpsPerSide':cost_bps})
            if new[t]<=1e-12:new.pop(t,None)
    sells+=cap_sells; cost=(buys+sells)*rate; cash2=cash+sells-buys-cost
    if cash2<-1e-8: raise RuntimeError(f'cash negative {cash2}')
    cash2=max(0,cash2); gross=sum(sh*valid[t] for t,sh in new.items() if t in valid); eq=cash2+gross
    if eq<=0: raise RuntimeError('non-positive post-trade equity')
    if gross/eq>GROSS_CAP+1e-7: raise RuntimeError('gross cap')
    if max((sh*valid[t]/eq for t,sh in new.items() if t in valid),default=0)>MAX_POSITION+1e-6: raise RuntimeError('position cap')
    return new,cash2,buys,sells,cost


def simulate_scaled(calendar,snapshots,opens_map,closes_map,signal_dates,start,end,state,cost_bps,scale_factor,label):
    pos=dict(state['positions']); cash=float(state['cash']); last=dict(state['last_close']); prev=float(state['equity'])
    ledger=[];daily=[];checks=[];gap=.5;sigset=set(signal_dates);maxentry=maxmarked=0
    pid=f'{POLICY}_EXPOSURE_CONTROL_{label}_C{cost_bps}'
    for i in range(start,end+1):
        dt=calendar[i]; opens=opens_map.get(dt,{}); closes=closes_map.get(dt,{}); om=dict(last);om.update(opens)
        before=portfolio_value(pos,om,cash); buy=sell=cost=0; prevdt=calendar[i-1] if i>0 else None
        if prevdt in sigset and opens:
            target,exits=build_target(snapshots[prevdt],TOPN,pos)
            pos,cash,buy,sell,cost=execute_scaled(pos,cash,target,exits,opens,before,gap,cost_bps,prevdt,dt,pid,ledger,scale_factor)
            em=dict(last);em.update(opens);ee=portfolio_value(pos,em,cash)
            maxentry=max(maxentry,max((sh*em[t]/max(ee,1e-12) for t,sh in pos.items() if t in em),default=0))
        po=portfolio_value(pos,{**last,**opens},cash); cm={**last,**closes}; ce=portfolio_value(pos,cm,cash)
        gross=sum(sh*cm[t] for t,sh in pos.items() if t in cm); maxw=max((sh*cm[t]/max(ce,1e-12) for t,sh in pos.items() if t in cm),default=0)
        ae=abs(cash+gross-ce); o=before/prev-1 if prev>0 else np.nan; e=po/before-1 if before>0 else np.nan; intr=ce/po-1 if po>0 else np.nan; dr=ce/prev-1 if prev>0 else np.nan
        de=abs((1+o)*(1+e)*(1+intr)-(1+dr)) if all(np.isfinite(x) for x in [o,e,intr,dr]) else np.nan
        checks.append({'Date':str(dt.date()),'AccountingIdentityError':ae,'GrossExposure':gross/max(ce,1e-12),'MaxMarkedPositionWeight':maxw,'MaxEntryPositionWeightObservedToDate':maxentry})
        daily.append({'Date':str(dt.date()),'PreviousCloseEquity':prev,'OpenEquityBeforeTrade':before,'EquityAfterOpenExecution':po,'EquityClose':ce,'DailyReturn':dr,'ReturnDecompositionError':de,'Cash':cash,'GrossMarketValue':gross,'Positions':len(pos),'BuyNotional':buy,'SellNotional':sell,'TransactionCost':cost})
        prev=ce; last.update(closes)
    d=pd.DataFrame(daily); tr=pd.DataFrame(ledger); ck=pd.DataFrame(checks); m=metric_summary(d,state['equity'])
    avg=max(float(d.EquityClose.mean()),1e-12); years=max(len(d)/252,1e-12)
    tb=float(tr.loc[tr.Side.str.startswith('BUY'),'Notional'].sum()) if not tr.empty else 0
    ts=float(tr.loc[tr.Side.str.startswith('SELL'),'Notional'].sum()) if not tr.empty else 0
    tc=float(tr.Cost.sum()) if not tr.empty else 0
    m.update({'Label':label,'ScaleFactor':scale_factor,'CostBpsPerSide':cost_bps,'TotalBuyNotional':tb,'TotalSellNotional':ts,'TotalTransactionCost':tc,'AnnualizedTurnover':((tb+ts)/avg)/years,'AvgCashWeight':float((d.Cash/d.EquityClose).mean()),'AvgGrossExposure':float((d.GrossMarketValue/d.EquityClose).mean()),'MaxEntryPositionObserved':maxentry,'MaxDailyMarkedPositionObserved':float(ck.MaxMarkedPositionWeight.max()),'MaxAccountingIdentityError':float(ck.AccountingIdentityError.max()),'MaxReturnDecompositionError':float(d.ReturnDecompositionError.max())})
    return m,d,tr,ck


def calibrate_alpha(calendar,snapshots,opens,closes,train_end,target,cost_bps):
    """Calibrate only on the selection period; no OOS returns are used."""
    end=calendar.index(train_end)
    sig=[d for d in signal_dates_for(calendar,snapshots,FREQ) if d<=train_end]
    initial={'positions':{},'cash':1000.0,'last_close':{},'equity':1000.0}
    candidates=[]
    for a in CALIBRATION_GRID:
        m,_,_,_=simulate_scaled(calendar,snapshots,opens,closes,sig,0,end,initial,cost_bps,float(a),'CALIB')
        candidates.append((abs(float(m['AvgGrossExposure'])-target),float(a),float(m['AvgGrossExposure'])))
    candidates.sort(key=lambda x:x[0])
    return candidates[0][1], candidates


def main():
    t0=time.time(); print('FASE 19B.1 — MATCHED REALIZED EXPOSURE ATTRIBUTION',flush=True)
    print(f'RUN_ID: {RUN_ID}',flush=True)
    print('Frozen policy: F80_TOP20_PARTIAL50 | diagnostic only | no production change',flush=True)
    print('Calibration: SELECTION ONLY | OOS returns never used to choose alpha',flush=True)
    data,failures=download_universe(DEFAULT_UNIVERSE); valid=len(data)
    if valid<MIN_CROSS_SECTION: raise RuntimeError(f'valid universe too small: {valid}')
    calendar=sorted(set(d for df in data.values() for d in df.Date.dropna().tolist())); opens,closes=build_price_maps(data); snapshots=build_snapshots(data,calendar)
    ref=signal_dates_for(calendar,snapshots,20); split=int(math.floor(len(ref)*TRAIN_FRAC))-1; split=max(1,min(split,len(ref)-2)); train_end=ref[split]; test_start=calendar.index(train_end)+1
    oos_dates=[d for d in signal_dates_for(calendar,snapshots,FREQ) if d>train_end]
    print(f'Valid={valid} failures={len(failures)} snapshots={len(snapshots)}',flush=True)
    print(f'SELECTION END={pd.Timestamp(train_end).date()} FINAL OOS START={pd.Timestamp(calendar[test_start]).date()} F80 OOS SIGNALS={len(oos_dates)}',flush=True)

    rows=[]; interp=[]; calibration_rows=[]; daily20={}; trades20={}; checks20={}
    for c in COST_BPS:
        train_m,_,_,_,state=simulate_policy_window(calendar,snapshots,opens,closes,FREQ,TOPN,REB,c,start_index=0,end_index=calendar.index(train_end),collect_ledger=True)
        b,bd,bt,bc,_=simulate_policy_window(calendar,snapshots,opens,closes,FREQ,TOPN,REB,c,start_index=test_start,end_index=len(calendar)-1,initial_positions=state['positions'],initial_cash=state['cash'],initial_last_close=state['last_close'],initial_prev_equity=state['equity'],previous_signal_dt=train_end,collect_ledger=True)
        ok=bool(b['MaxAccountingIdentityError']<=1e-8 and b['MaxReturnDecompositionError']<=1e-8 and b['AvgGrossExposure']<=GROSS_CAP+1e-8 and b['MaxEntryPositionObserved']<=MAX_POSITION+1e-6 and b['FinalEquity']>0 and np.isfinite(b['CAGR']) and np.isfinite(b['Sharpe']))
        if not ok: raise RuntimeError('BASELINE RECONCILIATION FAILED')
        rows.append({'Scenario':'BASELINE','CostBpsPerSide':c,**{k:b[k] for k in ['CAGR','MaxDD','Sharpe','Sortino','ProfitFactor','FinalEquity','AnnualizedTurnover','AvgCashWeight','AvgGrossExposure','TotalTransactionCost']}})
        if c==20: daily20['BASELINE']=bd; trades20['BASELINE']=bt; checks20['BASELINE']=bc
        for label,target in TARGET_GROSS.items():
            alpha,cands=calibrate_alpha(calendar,snapshots,opens,closes,train_end,target,c)
            sel_gap,_,sel_gross=cands[0]
            calibration_rows.append({'Control':label,'CostBpsPerSide':c,'TargetGrossExposure':target,'CalibratedScaleFactor':alpha,'SelectionRealizedGrossExposure':sel_gross,'SelectionExposureGap':sel_gross-target,'CalibrationTolerancePASS':bool(sel_gap<=EXPOSURE_TOLERANCE)})
            m,d,tr,ck=simulate_scaled(calendar,snapshots,opens,closes,oos_dates,test_start,len(calendar)-1,state,c,alpha,label)
            tech=bool(m['MaxAccountingIdentityError']<=1e-8 and m['MaxReturnDecompositionError']<=1e-8 and m['AvgGrossExposure']<=GROSS_CAP+1e-8 and m['MaxEntryPositionObserved']<=MAX_POSITION+1e-6 and m['FinalEquity']>0)
            rows.append({'Scenario':label,'CostBpsPerSide':c,**{k:m[k] for k in ['CAGR','MaxDD','Sharpe','Sortino','ProfitFactor','FinalEquity','AnnualizedTurnover','AvgCashWeight','AvgGrossExposure','TotalTransactionCost','ScaleFactor']},'TargetGrossExposure':target,'TechnicalPASS':tech,'DeltaCAGR_vs_Baseline':m['CAGR']-b['CAGR'],'DeltaMaxDD_vs_Baseline':m['MaxDD']-b['MaxDD'],'DeltaSharpe_vs_Baseline':m['Sharpe']-b['Sharpe'],'DeltaFinalEquity_vs_Baseline':m['FinalEquity']-b['FinalEquity']})
            if c==20:
                daily20[label]=d; trades20[label]=tr; checks20[label]=ck
                interp.append({'Control':label,'TargetGrossExposure':target,'SelectionScaleFactor':alpha,'SelectionExposureGap':sel_gross-target,'OOSRealizedGrossExposure':m['AvgGrossExposure'],'OOSExposureGap':m['AvgGrossExposure']-target,'C20_CAGR':m['CAGR'],'C20_MaxDD':m['MaxDD'],'C20_Sharpe':m['Sharpe'],'DeltaSharpe_vs_Baseline':m['Sharpe']-b['Sharpe'],'DeltaMaxDD_vs_Baseline':m['MaxDD']-b['MaxDD'],'DeltaCAGR_vs_Baseline':m['CAGR']-b['CAGR'],'ExposureMatchPASS':bool(abs(m['AvgGrossExposure']-target)<=EXPOSURE_TOLERANCE),'AttributionConclusion':'INCONCLUSIVE_EXPOSURE_MISMATCH' if abs(m['AvgGrossExposure']-target)>EXPOSURE_TOLERANCE else 'READY_FOR_ATTRIBUTION'})

    rdf=pd.DataFrame(rows); c20=rdf[rdf.CostBpsPerSide==20].copy(); idf=pd.DataFrame(interp); cdf=pd.DataFrame(calibration_rows)
    rdf.to_csv(OUTDIR/'phase19b1_scenario_results.csv',index=False); idf.to_csv(OUTDIR/'phase19b1_c20_attribution.csv',index=False); cdf.to_csv(OUTDIR/'phase19b1_calibration.csv',index=False)
    for k,d in daily20.items(): d.to_csv(OUTDIR/f'phase19b1_{k.lower()}_c20_daily.csv',index=False)
    for k,tr in trades20.items(): tr.to_csv(OUTDIR/f'phase19b1_{k.lower()}_c20_trades.csv',index=False)
    pd.DataFrame(failures).to_csv(OUTDIR/'phase19b1_download_failures.csv',index=False)
    checks={'RUN_ID':RUN_ID,'ConfiguredUniverse':len(DEFAULT_UNIVERSE),'ValidTickers':valid,'Failures':len(failures),'SelectionEnd':str(pd.Timestamp(train_end).date()),'FinalOOSStart':str(pd.Timestamp(calendar[test_start]).date()),'FrozenPolicy':POLICY,'DiagnosticOnly':True,'CalibrationUsesSelectionOnly':True,'OOSReturnsNotUsedForAlpha':True,'ExposureTolerance':EXPOSURE_TOLERANCE,'C20ExposureMatchPASS':bool(idf.ExposureMatchPASS.all()),'TechnicalPASS':bool(rdf.loc[rdf.CostBpsPerSide==20,'TechnicalPASS'].fillna(True).all()),'STATUS':'PASS' if bool(rdf.loc[rdf.CostBpsPerSide==20,'TechnicalPASS'].fillna(True).all()) else 'FAIL','RuntimeSeconds':time.time()-t0}
    (OUTDIR/'phase19b1_checks.json').write_text(json.dumps(checks,indent=2,default=str),encoding='utf-8')
    print('\n--- SCENARIOS ---'); print(rdf.to_string(index=False)); print('\n--- CALIBRATION ---'); print(cdf.to_string(index=False)); print('\n--- C20 ATTRIBUTION ---'); print(idf.to_string(index=False)); print(f"\nSTATUS: {checks['STATUS']} | runtime={time.time()-t0:.1f}s",flush=True)
    return 0

if __name__=='__main__': raise SystemExit(main())

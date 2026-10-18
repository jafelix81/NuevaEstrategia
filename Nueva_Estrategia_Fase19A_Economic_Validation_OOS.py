from __future__ import annotations
import json, math, time
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd
from Nueva_Estrategia_Fase12_FinalOOS_Selection_LTM import (
    DEFAULT_UNIVERSE, DISCOVERY_DATES, EMBARGO, MIN_CROSS_SECTION,
    INITIAL_CAPITAL, MAX_POSITION, GROSS_CAP, COST_BPS,
    download_universe, build_price_maps, build_snapshots, portfolio_value,
    build_target, simulate_policy_window, signal_dates_for, metric_summary,
)

RUN_ID=datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
OUTDIR=Path('nueva_estrategia_phase19a_economic_oos'); OUTDIR.mkdir(parents=True,exist_ok=True)
FREQ,TOPN,REB=80,20,'PARTIAL50'; POLICY='F80_TOP20_PARTIAL50'; TRAIN_FRAC=.80
FILTERS={
 'WEAK_R1_VOL252': [('R1','HIGHER'),('VOL252','LOWER')],
 'MAE10_R120_VOL20': [('R120','HIGHER'),('VOL20','HIGHER')],
 'QUICK_R120_DIST': [('R120','HIGHER'),('DIST_200D','HIGHER')],
}

def factor_series(df,dt):
    x=df.copy(); x['Date']=pd.to_datetime(x['Date'],errors='coerce').dt.normalize(); x=x[x.Date<=pd.Timestamp(dt).normalize()].sort_values('Date').drop_duplicates('Date')
    c=pd.to_numeric(x['Close'],errors='coerce'); c=c.dropna()
    if len(c)<253:return {}
    lr=np.log(c).diff()
    def r(n): return float(c.iloc[-1]/c.iloc[-n-1]-1) if len(c)>n else np.nan
    def v(n): return float(lr.dropna().tail(n).std(ddof=1)*np.sqrt(252)) if len(lr.dropna())>=n else np.nan
    m200=c.tail(200).mean()
    return {'R1':r(1),'R120':r(120),'VOL20':v(20),'VOL252':v(252),'DIST_200D':float(c.iloc[-1]/m200-1) if m200>0 else np.nan}

def build_factors(data,dates):
    out={}
    for i,dt in enumerate(dates,1):
        rows=[]
        for t,df in data.items():
            f=factor_series(df,dt)
            if f: rows.append({'Ticker':t,**f})
        out[dt]=pd.DataFrame(rows)
        if i%5==0 or i==len(dates):print(f'FACTORS {i}/{len(dates)} | {pd.Timestamp(dt).date()} | rows={len(rows)}',flush=True)
    return out

def scores(fmaps):
    allscores={}
    for name,spec in FILTERS.items():
        dct={}
        for dt,g in fmaps.items():
            z=g.copy()
            if z.empty:z['RiskScore']=np.nan;z['RiskQ5']=False;dct[dt]=z[['Ticker','RiskScore','RiskQ5']];continue
            rs=[]
            for f,direction in spec:
                r=pd.to_numeric(z[f],errors='coerce').rank(method='average',pct=True)
                rs.append(r if direction=='HIGHER' else 1-r)
            z['RiskScore']=pd.concat(rs,axis=1).mean(axis=1,skipna=False)
            z['RiskQ5']=False
            ok=z.RiskScore.notna()
            if ok.sum()>=5:
                q=pd.qcut(z.loc[ok,'RiskScore'],5,labels=False,duplicates='drop')
                if q.nunique()==5:z.loc[ok,'RiskQ5']=q.eq(4).to_numpy()
            dct[dt]=z[['Ticker','RiskScore','RiskQ5']]
        allscores[name]=dct
    return allscores

def execute_filtered(pos,cash,target,exits,opens,equity,gap,cost_bps,signal_dt,execution_dt,policy_id,ledger,blocked):
    rate=cost_bps/10000; valid={t:p for t,p in opens.items() if np.isfinite(p) and p>0}; cur=dict(pos); deltas={}
    for t in exits | (set(cur)-set(target)):
        if t in cur and t in valid:deltas[t]=-cur[t]
    cap=max(equity*(1-2*rate),0)*MAX_POSITION
    for t,w in target.items():
        if t not in valid or t in exits:continue
        sh=cur.get(t,0); desired=max(0,min(equity*float(w),cap))/valid[t]; d=gap*(desired-sh)
        if d>0 and t in blocked:
            continue
        if abs(d)>1e-12:deltas[t]=d
    for t,sh in cur.items():
        if t in valid and sh*valid[t]>cap+1e-10:deltas[t]=min(deltas.get(t,0),cap/valid[t]-sh)
    sell=sum(-d*valid[t] for t,d in deltas.items() if d<0); buy=sum(d*valid[t] for t,d in deltas.items() if d>0)
    avail=max(0,cash+sell*(1-rate)); scale=min(1,avail/(buy*(1+rate))) if buy>0 else 0
    new=dict(cur); buys=sells=0
    for t,d0 in deltas.items():
        if t not in valid:continue
        d=d0*scale if d0>0 else d0; nsh=cur.get(t,0)+d
        if nsh<=1e-12:new.pop(t,None)
        else:new[t]=nsh
        n=abs(d)*valid[t]
        if d>0:buys+=n;side='BUY'
        elif d<0:sells+=n;side='SELL'
        else:continue
        ledger.append({'PolicyID':policy_id,'DateSignal':str(signal_dt.date()),'ExecutionDate':str(execution_dt.date()),'Ticker':t,'Side':side,'SharesDelta':d,'ExecutionOpen':valid[t],'Notional':n,'Cost':n*rate,'CostBpsPerSide':cost_bps})
    cap=max(equity*(1-2*rate),0)*MAX_POSITION; cap_sells=0
    for t in list(new):
        if t not in valid:continue
        val=new[t]*valid[t]
        if val>cap+1e-9:
            extra=(val-cap)/valid[t];new[t]-=extra;cap_sells+=extra*valid[t]
            ledger.append({'PolicyID':policy_id,'DateSignal':str(signal_dt.date()),'ExecutionDate':str(execution_dt.date()),'Ticker':t,'Side':'SELL_CAP','SharesDelta':-extra,'ExecutionOpen':valid[t],'Notional':extra*valid[t],'Cost':extra*valid[t]*rate,'CostBpsPerSide':cost_bps})
            if new[t]<=1e-12:new.pop(t,None)
    sells+=cap_sells;cost=(buys+sells)*rate;cash2=cash+sells-buys-cost
    if cash2<-1e-8:raise RuntimeError(f'cash negative {cash2}')
    cash2=max(0,cash2);gross=sum(sh*valid[t] for t,sh in new.items() if t in valid);eq=cash2+gross
    if eq<=0:raise RuntimeError('non-positive post-trade equity')
    if gross/eq>GROSS_CAP+1e-7:raise RuntimeError('gross cap')
    if max((sh*valid[t]/eq for t,sh in new.items() if t in valid),default=0)>MAX_POSITION+1e-6:raise RuntimeError('position cap')
    return new,cash2,buys,sells,cost

def simulate_filtered(calendar,snapshots,opens_map,closes_map,signal_dates,risk_map,filter_name,start,end,state,cost_bps):
    pos=dict(state['positions']);cash=float(state['cash']);last=dict(state['last_close']);prev=float(state['equity']);ledger=[];daily=[];checks=[];blocked_events=blocked_notional=0;gap=.5;sigset=set(signal_dates); maxentry=maxmarked=0;stale=missing=0
    pid=f'{POLICY}_FILTER_{filter_name}_C{cost_bps}'
    blocked_rows=[]
    for i in range(start,end+1):
        dt=calendar[i];opens=opens_map.get(dt,{});closes=closes_map.get(dt,{});om=dict(last);om.update(opens);before=portfolio_value(pos,om,cash);buy=sell=cost=0
        prevdt=calendar[i-1] if i>0 else None
        if prevdt in sigset and opens:
            target,exits=build_target(snapshots[prevdt],TOPN,pos); sg=risk_map.get(prevdt,pd.DataFrame(columns=['Ticker','RiskScore','RiskQ5']));q5=set(sg.loc[sg.RiskQ5.astype(bool),'Ticker'])
            rate=cost_bps/10000;cap=max(before*(1-2*rate),0)*MAX_POSITION
            for t,w in target.items():
                if t not in opens or t in exits:continue
                sh=pos.get(t,0);desired=max(0,min(before*float(w),cap))/opens[t];d=gap*(desired-sh)
                if d>0 and t in q5:
                    blocked_events+=1;blocked_notional+=d*opens[t];row=sg[sg.Ticker.eq(t)]
                    blocked_rows.append({'Filter':filter_name,'DateSignal':str(prevdt.date()),'ExecutionDate':str(dt.date()),'Ticker':t,'RiskScore':float(row.RiskScore.iloc[0])})
            pos,cash,buy,sell,cost=execute_filtered(pos,cash,target,exits,opens,before,gap,cost_bps,prevdt,dt,pid,ledger,q5)
            em=dict(last);em.update(opens);ee=portfolio_value(pos,em,cash);maxentry=max(maxentry,max((sh*em[t]/max(ee,1e-12) for t,sh in pos.items() if t in em),default=0))
        po=portfolio_value(pos,{**last,**opens},cash);cm={**last,**closes};held=[t for t in pos if t not in closes];stale+=len(held);ce=portfolio_value(pos,cm,cash);gross=sum(sh*cm[t] for t,sh in pos.items() if t in cm);maxw=max((sh*cm[t]/max(ce,1e-12) for t,sh in pos.items() if t in cm),default=0);maxmarked=max(maxmarked,maxw);ae=abs(cash+gross-ce);o=before/prev-1 if prev>0 else np.nan;e=po/before-1 if before>0 else np.nan;intr=ce/po-1 if po>0 else np.nan;dr=ce/prev-1 if prev>0 else np.nan;de=abs((1+o)*(1+e)*(1+intr)-(1+dr)) if all(np.isfinite(x) for x in [o,e,intr,dr]) else np.nan
        checks.append({'Date':str(dt.date()),'AccountingIdentityError':ae,'GrossExposure':gross/max(ce,1e-12),'MaxMarkedPositionWeight':maxw,'MaxEntryPositionWeightObservedToDate':maxentry});daily.append({'Date':str(dt.date()),'PreviousCloseEquity':prev,'OpenEquityBeforeTrade':before,'EquityAfterOpenExecution':po,'EquityClose':ce,'DailyReturn':dr,'ReturnDecompositionError':de,'Cash':cash,'GrossMarketValue':gross,'Positions':len(pos),'BuyNotional':buy,'SellNotional':sell,'TransactionCost':cost,'FreshCloseMissingCount':len(held)});prev=ce;last.update(closes)
    d=pd.DataFrame(daily);tr=pd.DataFrame(ledger);ck=pd.DataFrame(checks);m=metric_summary(d,state['equity']);avg=max(float(d.EquityClose.mean()),1e-12);years=max(len(d)/252,1e-12);tb=float(tr.loc[tr.Side.str.startswith('BUY'),'Notional'].sum()) if not tr.empty else 0;ts=float(tr.loc[tr.Side.str.startswith('SELL'),'Notional'].sum()) if not tr.empty else 0;tc=float(tr.Cost.sum()) if not tr.empty else 0
    m.update({'Filter':filter_name,'CostBpsPerSide':cost_bps,'TotalBuyNotional':tb,'TotalSellNotional':ts,'TotalTransactionCost':tc,'AnnualizedTurnover':((tb+ts)/avg)/years,'AvgCashWeight':float((d.Cash/d.EquityClose).mean()),'AvgGrossExposure':float((d.GrossMarketValue/d.EquityClose).mean()),'MaxEntryPositionObserved':maxentry,'MaxDailyMarkedPositionObserved':maxmarked,'MaxAccountingIdentityError':float(ck.AccountingIdentityError.max()),'MaxReturnDecompositionError':float(d.ReturnDecompositionError.max()),'BlockedBuyEvents':blocked_events,'BlockedBuyNotional':blocked_notional})
    return m,d,tr,ck,pd.DataFrame(blocked_rows)

def main():
    t0=time.time();print('FASE 19A — ECONOMIC VALIDATION OOS — PREDICTABILITY FILTERS',flush=True);print(f'RUN_ID: {RUN_ID}',flush=True);print('Frozen policy: F80_TOP20_PARTIAL50 | BUY filter only | no backfill',flush=True)
    data,failures=download_universe(DEFAULT_UNIVERSE);valid=len(data)
    if valid<MIN_CROSS_SECTION:raise RuntimeError(f'valid universe too small: {valid}')
    calendar=sorted(set(d for df in data.values() for d in df.Date.dropna().tolist()));opens,closes=build_price_maps(data);snapshots=build_snapshots(data,calendar)
    ref=signal_dates_for(calendar,snapshots,20);split=int(math.floor(len(ref)*TRAIN_FRAC))-1;split=max(1,min(split,len(ref)-2));train_end=ref[split];test_start=calendar.index(train_end)+1;oos_dates=[d for d in signal_dates_for(calendar,snapshots,FREQ) if d>train_end]
    print(f'Valid={valid} failures={len(failures)} snapshots={len(snapshots)}',flush=True);print(f'SELECTION END={pd.Timestamp(train_end).date()} FINAL OOS START={pd.Timestamp(calendar[test_start]).date()} F80 OOS SIGNALS={len(oos_dates)}',flush=True)
    fmaps=build_factors(data,oos_dates);rmaps=scores(fmaps)
    base_rows=[];filt_rows=[];blocked=[];base_daily=base_trades=base_checks=None
    for c in COST_BPS:
        train_m,_,_,_,state=simulate_policy_window(calendar,snapshots,opens,closes,FREQ,TOPN,REB,c,start_index=0,end_index=calendar.index(train_end),collect_ledger=True)
        b,bd,bt,bc,_=simulate_policy_window(calendar,snapshots,opens,closes,FREQ,TOPN,REB,c,start_index=test_start,end_index=len(calendar)-1,initial_positions=state['positions'],initial_cash=state['cash'],initial_last_close=state['last_close'],initial_prev_equity=state['equity'],previous_signal_dt=train_end,collect_ledger=True)
        ok=bool(b['MaxAccountingIdentityError']<=1e-8 and b['MaxReturnDecompositionError']<=1e-8 and b['AvgGrossExposure']<=GROSS_CAP+1e-8 and b['MaxEntryPositionObserved']<=MAX_POSITION+1e-6 and b['FinalEquity']>0 and np.isfinite(b['CAGR']) and np.isfinite(b['Sharpe']))
        if not ok:raise RuntimeError('BASELINE RECONCILIATION FAILED / NO ECONOMIC TEST PERFORMED')
        base_rows.append({'CostBpsPerSide':c,**{k:b[k] for k in ['CAGR','MaxDD','Sharpe','Sortino','ProfitFactor','FinalEquity','AnnualizedTurnover','AvgCashWeight','AvgGrossExposure','TotalTransactionCost']}})
        if c==20:base_daily,base_trades,base_checks=bd,bt,bc
        sig=[d for d in signal_dates_for(calendar,snapshots,FREQ) if d>train_end]
        for name in FILTERS:
            m,d,tr,ck,bl=simulate_filtered(calendar,snapshots,opens,closes,sig,rmaps[name],name,test_start,len(calendar)-1,state,c)
            row={'Filter':name,'CostBpsPerSide':c,**{k:m[k] for k in ['CAGR','MaxDD','Sharpe','Sortino','ProfitFactor','FinalEquity','AnnualizedTurnover','AvgCashWeight','AvgGrossExposure','TotalTransactionCost','BlockedBuyEvents','BlockedBuyNotional']},'DeltaCAGR_vs_Baseline':m['CAGR']-b['CAGR'],'DeltaMaxDD_vs_Baseline':m['MaxDD']-b['MaxDD'],'DeltaSharpe_vs_Baseline':m['Sharpe']-b['Sharpe'],'DeltaSortino_vs_Baseline':m['Sortino']-b['Sortino'],'DeltaFinalEquity_vs_Baseline':m['FinalEquity']-b['FinalEquity'],'TechnicalPASS':bool(m['MaxAccountingIdentityError']<=1e-8 and m['MaxReturnDecompositionError']<=1e-8 and m['AvgGrossExposure']<=GROSS_CAP+1e-8 and m['MaxEntryPositionObserved']<=MAX_POSITION+1e-6 and m['FinalEquity']>0)};filt_rows.append(row)
            if c==20:blocked.append(bl)
    bdf=pd.DataFrame(base_rows);fdf=pd.DataFrame(filt_rows);blk=pd.concat(blocked,ignore_index=True) if blocked else pd.DataFrame();b20=bdf[bdf.CostBpsPerSide==20].iloc[0]
    interp=[]
    for name in FILTERS:
        r=fdf[(fdf.Filter==name)&(fdf.CostBpsPerSide==20)].iloc[0];interp.append({'Filter':name,'C20_DeltaSharpe':r.DeltaSharpe_vs_Baseline,'C20_DeltaMaxDD':r.DeltaMaxDD_vs_Baseline,'C20_DeltaCAGR':r.DeltaCAGR_vs_Baseline,'C20_DeltaFinalEquity':r.DeltaFinalEquity_vs_Baseline,'ImprovesSharpeAndDrawdown':bool(r.DeltaSharpe_vs_Baseline>0 and r.DeltaMaxDD_vs_Baseline>0),'CAGR>=90pctBaseline':bool(r.CAGR>=.9*b20.CAGR),'TechnicalPASS':bool(r.TechnicalPASS)})
    idf=pd.DataFrame(interp)
    bdf.to_csv(OUTDIR/'phase19a_baseline_oos.csv',index=False);fdf.to_csv(OUTDIR/'phase19a_filter_results_oos.csv',index=False);idf.to_csv(OUTDIR/'phase19a_economic_interpretation_c20.csv',index=False);base_daily.to_csv(OUTDIR/'phase19a_baseline_c20_daily.csv',index=False);base_trades.to_csv(OUTDIR/'phase19a_baseline_c20_trades.csv',index=False);base_checks.to_csv(OUTDIR/'phase19a_baseline_c20_checks.csv',index=False);blk.to_csv(OUTDIR/'phase19a_blocked_buys_c20.csv',index=False);pd.DataFrame(failures).to_csv(OUTDIR/'phase19a_download_failures.csv',index=False)
    checks={'RUN_ID':RUN_ID,'ConfiguredUniverse':len(DEFAULT_UNIVERSE),'ValidTickers':valid,'Failures':len(failures),'SelectionEnd':str(pd.Timestamp(train_end).date()),'FinalOOSStart':str(pd.Timestamp(calendar[test_start]).date()),'FrozenPolicy':POLICY,'EntryFilterOnly':True,'NoBackfill':True,'BaselineReconciliationPASS':True,'TechnicalPASS':bool(fdf.TechnicalPASS.all()),'RuntimeSeconds':time.time()-t0}
    (OUTDIR/'phase19a_checks.json').write_text(json.dumps(checks,indent=2,default=str),encoding='utf-8')
    print('\n--- BASELINE OOS ---');print(bdf.to_string(index=False));print('\n--- FILTER RESULTS ---');print(fdf.to_string(index=False));print('\n--- C20 INTERPRETATION ---');print(idf.to_string(index=False));print(f'\nSTATUS: PASS | runtime={time.time()-t0:.1f}s',flush=True)
    return 0
if __name__=='__main__':raise SystemExit(main())

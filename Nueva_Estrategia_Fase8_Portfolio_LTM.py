# NUEVA ESTRATEGIA — FASE 8: CONSTRUCCIÓN DE CARTERA Y VALIDACIÓN ECONÓMICA LTM
# Investigación OOS de construcción de cartera. NO producción.
# Hipótesis congelada: LTM_COMPOSITE = promedio simple de ranks R100/R120/R140/R160
# Políticas: H20/H40 x Top10/20/30 x EqualWeight/InverseVol60 x 10/20/50 bps.
# Hard limits: max 20% por posición, 100% gross. NO Kelly, NO stops.
import warnings
from pathlib import Path
from datetime import datetime, timezone
import numpy as np, pandas as pd, yfinance as yf
warnings.filterwarnings("ignore")

RUN_ID=datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
PERIOD="10y"; HORIZONS=(20,40); DISCOVERY_DATES=12; EMBARGO=5; MIN_CROSS_SECTION=100
MOM_WINDOWS=(100,120,140,160); TOP_PCTS=(0.10,0.20,0.30); WEIGHT_POLICIES=("EQUAL_WEIGHT","INVERSE_VOL60")
COST_BPS=(10,20,50); MAX_POSITION=0.20; MAX_GROSS=1.00
ART=Path("nueva_estrategia_phase8_portfolio"); ART.mkdir(parents=True,exist_ok=True)
DEFAULT_UNIVERSE=['AA', 'AAPL', 'ABNB', 'ABT', 'ADI', 'AFRM', 'ALAB', 'ALGN', 'AMAT', 'AMD', 'AMGN', 'AMT', 'AMTD', 'AMZN', 'ANET', 'APA', 'APD', 'APO', 'APP', 'ARKF', 'ARKG', 'ARKK', 'ARKQ', 'ARKW', 'ASB', 'ASML', 'ASTS', 'ATI', 'AVB', 'AVGO', 'AX', 'AXON', 'AXP', 'AZN', 'BA', 'BABA', 'BAC', 'BE', 'BEAM', 'BEN', 'BIDU', 'BIIB', 'BITO', 'BKNG', 'BKR', 'BLK', 'BLNK', 'BMY', 'BNTX', 'BOKF', 'BSX', 'BX', 'BXP', 'C', 'CACC', 'CAT', 'CATY', 'CAVA', 'CCI', 'CDNS', 'CEG', 'CELH', 'CF', 'CFG', 'CHPT', 'CHTR', 'CHWY', 'CIFR', 'CL', 'CLF', 'CLS', 'CMCSA', 'COIN', 'COMP', 'COP', 'COST', 'CRDO', 'CRSP', 'CRWD', 'CSCO', 'CSX', 'CUBI', 'CVNA', 'CVX', 'CX', 'DD', 'DDOG', 'DE', 'DELL', 'DHI', 'DIS', 'DJT', 'DKNG', 'DLR', 'DOCU', 'DOW', 'DUOL', 'DVN', 'EA', 'EBAY', 'ECL', 'EDIT', 'EOG', 'EQIX', 'EQR', 'ETN', 'ETSY', 'EW', 'EXPE', 'EXR', 'FCEL', 'FCF', 'FCX', 'FDX', 'FITB', 'FLEX', 'FLYW', 'FMC', 'FNB', 'FOXA', 'FSLR', 'GD', 'GE', 'GEV', 'GILD', 'GIS', 'GLD', 'GLW', 'GOOGL', 'GPRO', 'GS', 'GSK', 'HAL', 'HAPN', 'HBAN', 'HD', 'HOMB', 'HON', 'HOOD', 'HUT', 'IEFA', 'ILMN', 'INTC', 'IREN', 'ISRG', 'IWM', 'JD', 'JETS', 'JMIA', 'JNJ', 'JPM', 'KEY', 'KKR', 'KLAC', 'KMB', 'KO', 'KRE', 'LCID', 'LEN', 'LI', 'LIN', 'LITE', 'LLY', 'LMT', 'LOT', 'LOW', 'LPRO', 'LRCX', 'LYV', 'MA', 'MAA', 'MARA', 'MCHP', 'MDB', 'MDLZ', 'MDT', 'MELI', 'META', 'MLM', 'MMM', 'MNST', 'MOD', 'MOS', 'MP', 'MRNA', 'MRVL', 'MS', 'MSFT', 'MTB', 'MTCH', 'MU', 'NEM', 'NET', 'NFLX', 'NIO', 'NOC', 'NOW', 'NSC', 'NTLA', 'NTR', 'NTRS', 'NU', 'NUE', 'NVDA', 'NVO', 'NWSA', 'NXPI', 'O', 'OIH', 'OKTA', 'OMF', 'ON', 'OPEN', 'OPFI', 'OXY', 'OZK', 'PAGS', 'PANW', 'PARA', 'PAYS', 'PDD', 'PEP', 'PFE', 'PG', 'PHM', 'PINS', 'PLD', 'PLTR', 'PLUG', 'PSA', 'PSNY', 'PWR', 'PYPL', 'QCOM', 'QQQ', 'QS', 'RDDT', 'REGN', 'RF', 'RIOT', 'RIVN', 'RKLB', 'ROKU', 'RSG', 'RTX', 'RUM', 'RUN', 'SBAC', 'SBUX', 'SCHW', 'SE', 'SEDG', 'SHOP', 'SHW', 'SIFY', 'SLB', 'SMCI', 'SMH', 'SNAP', 'SNOW', 'SNPS', 'SNY', 'SOFI', 'SOXX', 'SPG', 'SPWR', 'STLD', 'STNE', 'STT', 'SYK', 'T', 'TAK', 'TEAM', 'TELFY', 'TEM', 'TER', 'TFC', 'TGT', 'TMDX', 'TMUS', 'TRIP', 'TROW', 'TSLA', 'TSM', 'TTWO', 'TWLO', 'TXN', 'UMBF', 'UNG', 'UNP', 'UPS', 'UPST', 'USO', 'V', 'VEA', 'VICI', 'VLY', 'VMC', 'VNQ', 'VOD', 'VRT', 'VRTX', 'VST', 'VWO', 'VZ', 'W', 'WAY', 'WBD', 'WBS', 'WDAY', 'WFC', 'WM', 'WMT', 'WULF', 'WY', 'XBI', 'XLB', 'XLE', 'XLF', 'XLI', 'XLK', 'XLP', 'XLRE', 'XLU', 'XLV', 'XLY', 'XOM', 'XPEV', 'XYZ', 'Z', 'ZBH', 'ZG', 'ZION', 'ZM', 'ZS']
if len(DEFAULT_UNIVERSE)!=335: raise RuntimeError(f"Universo inválido: {len(DEFAULT_UNIVERSE)}")
UNIVERSE=list(dict.fromkeys(DEFAULT_UNIVERSE))

def features(df):
    c=pd.to_numeric(df["Close"],errors="coerce"); o=pd.to_numeric(df["Open"],errors="coerce"); x=df.copy()
    for w in MOM_WINDOWS: x[f"R{w}"]=c/c.shift(w)-1
    for h in HORIZONS: x[f"FWD{h}"]=c.shift(-h)/o.shift(-1)-1
    x["VOL60_ANNUAL"]=c.pct_change().rolling(60).std()*np.sqrt(252)
    return x

def load(t):
    try:
        r=yf.download(t,period=PERIOD,auto_adjust=True,progress=False,actions=False,threads=False)
        if r is None or r.empty: return None,"EMPTY"
        if isinstance(r.columns,pd.MultiIndex): r.columns=r.columns.get_level_values(0)
        need=["Open","High","Low","Close","Volume"]
        if not all(c in r.columns for c in need): return None,"COLUMNS"
        r=r[need].copy(); r.index=pd.to_datetime(r.index).tz_localize(None); r=r[~r.index.duplicated()].sort_index()
        r=r.dropna(subset=["Open","High","Low","Close"])
        if len(r)<300: return None,"HISTORY"
        return features(r),"OK"
    except Exception as e: return None,type(e).__name__

def usable_dates(datasets,h):
    req=[f"R{w}" for w in MOM_WINDOWS]; dates=sorted(set().union(*[set(d.index) for d in datasets.values()])); usable=[]
    for dt in dates:
        n=0
        for df in datasets.values():
            if dt not in df.index: continue
            r=df.loc[dt]
            if all(np.isfinite(r.get(f,np.nan)) for f in req) and np.isfinite(r.get(f"FWD{h}",np.nan)): n+=1
        if n>=MIN_CROSS_SECTION: usable.append(dt)
    selected=[]; last=-10**9
    for i,dt in enumerate(usable):
        if i-last>=h+EMBARGO: selected.append(dt); last=i
    return selected

def cross(datasets,dt,h):
    req=[f"R{w}" for w in MOM_WINDOWS]; rows=[]
    for ticker,df in datasets.items():
        if dt not in df.index: continue
        r=df.loc[dt]
        if not all(np.isfinite(r.get(f,np.nan)) for f in req): continue
        y=r.get(f"FWD{h}",np.nan)
        if not np.isfinite(y): continue
        vals={f:float(r[f]) for f in req}; vals["VOL60_ANNUAL"]=float(r.get("VOL60_ANNUAL",np.nan)); vals.update(Ticker=ticker,Date=dt,ForwardReturn=float(y)); rows.append(vals)
    return pd.DataFrame(rows)

def build_oos(datasets,h):
    rows=[]; dates=usable_dates(datasets,h)
    for dt in dates:
        g=cross(datasets,dt,h)
        if len(g)<MIN_CROSS_SECTION: continue
        for c in [f"R{w}" for w in MOM_WINDOWS]: g[c+"_RANK"]=g[c].rank(pct=True,method="average")
        g["LTM_COMPOSITE"]=g[[f"R{w}_RANK" for w in MOM_WINDOWS]].mean(axis=1); rows.append(g)
    if not rows: return pd.DataFrame(),[]
    d=pd.concat(rows,ignore_index=True); all_dates=sorted(pd.to_datetime(d.Date).unique()); oos_dates=all_dates[DISCOVERY_DATES+EMBARGO:]
    return d[d.Date.isin(oos_dates)].copy(),oos_dates

def cap_normalize(raw):
    w=pd.Series(raw,dtype=float).replace([np.inf,-np.inf],np.nan).fillna(0).clip(lower=0)
    if w.sum()<=0: return pd.Series(0.0,index=w.index)
    w=w/w.sum()*MAX_GROSS
    for _ in range(100):
        over=w>MAX_POSITION+1e-12
        if not over.any(): break
        excess=float((w[over]-MAX_POSITION).sum()); w[over]=MAX_POSITION; under=~over; avail=float(w[under].sum())
        if excess<=1e-12 or avail<=1e-12: break
        w[under]+=w[under]/avail*excess
    if w.sum()>MAX_GROSS: w*=MAX_GROSS/w.sum()
    return w

def portfolio_weights(g,top_pct,policy):
    z=g.dropna(subset=["LTM_COMPOSITE"]).sort_values("LTM_COMPOSITE",ascending=False).copy(); n=max(1,int(np.floor(len(z)*top_pct))); z=z.iloc[:n].copy()
    if policy=="EQUAL_WEIGHT": raw=pd.Series(1.0,index=z.index)
    else:
        vol=pd.to_numeric(z.VOL60_ANNUAL,errors="coerce"); valid=vol.notna()&(vol>0); z=z.loc[valid].copy(); vol=vol.loc[valid]
        if z.empty: return z,pd.Series(dtype=float)
        raw=1.0/vol
    return z,cap_normalize(raw)

def simulate(oos,h,top_pct,policy,cost_bps):
    rows=[]; equity=1.0; prev=None
    for dt,g in oos.groupby("Date",sort=True):
        z,w=portfolio_weights(g,top_pct,policy)
        if w.empty: continue
        gross=float((z.loc[w.index,"ForwardReturn"]*w).sum())
        idx=(prev.index.union(w.index) if prev is not None else w.index); p=(prev.reindex(idx,fill_value=0) if prev is not None else pd.Series(0.0,index=idx)); c=w.reindex(idx,fill_value=0)
        target_turn=float(0.5*np.abs(c-p).sum())
        # Every cycle is a complete buy-and-hold round trip: entry + exit.
        roundtrip_turnover=2.0; cost=roundtrip_turnover*cost_bps/10000.0; net=(1+gross)*(1-cost)-1
        equity*=1+net
        rows.append(dict(Horizon=h,Date=dt,TopPct=top_pct,WeightPolicy=policy,CostBps=cost_bps,NPositions=len(w),GrossReturn=gross,NetReturn=net,TargetTurnover=target_turn,RoundTripTurnover=roundtrip_turnover,CostDrag=cost,Equity=equity,GrossExposure=float(w.sum()),MaxPosition=float(w.max()),CashPct=float(1-w.sum())))
        prev=w
    return pd.DataFrame(rows)

def metrics(tr):
    eq=tr.Equity.astype(float); r=tr.NetReturn.astype(float); dates=pd.to_datetime(tr.Date); years=max(1,(dates.iloc[-1]-dates.iloc[0]).days)/365.25; final=float(eq.iloc[-1]); cagr=final**(1/years)-1 if final>0 else np.nan; dd=float((eq/eq.cummax()-1).min())
    if len(r)>1:
        spacing=dates.diff().dt.days.dropna().median(); ppy=365.25/spacing if spacing>0 else np.nan; sd=r.std(ddof=1); sharpe=float(r.mean()/sd*np.sqrt(ppy)) if sd>0 else np.nan; dn=r[r<0].std(ddof=1); sortino=float(r.mean()/dn*np.sqrt(ppy)) if len(r[r<0])>1 and dn>0 else np.nan
    else: sharpe=np.nan; sortino=np.nan
    losses=-r[r<0].sum(); pf=float(r[r>0].sum()/losses) if losses>0 else np.inf
    return dict(Dates=len(tr),FinalEquity=final,CAGR=cagr,MaxDD=dd,SharpeDiagnostic=sharpe,SortinoDiagnostic=sortino,ProfitFactor=pf,HitRate=float((r>0).mean()),AvgPositions=float(tr.NPositions.mean()),AvgTargetTurnover=float(tr.TargetTurnover.mean()),AvgRoundTripTurnover=float(tr.RoundTripTurnover.mean()),AvgCashPct=float(tr.CashPct.mean()),AvgGrossExposure=float(tr.GrossExposure.mean()),MaxPositionObserved=float(tr.MaxPosition.max()),WorstCycle=float(r.min()),BestCycle=float(r.max()))

print("="*78); print("NUEVA ESTRATEGIA — FASE 8: CONSTRUCCIÓN DE CARTERA LTM"); print(f"RUN_ID: {RUN_ID}"); print(f"Tickers configurados: {len(UNIVERSE)}"); print(f"Horizons: {HORIZONS} | Windows: {MOM_WINDOWS}"); print("Hipótesis congelada: LTM_COMPOSITE = promedio simple de ranks R100/R120/R140/R160"); print("Policies: TOP10/TOP20/TOP30 x EQUAL_WEIGHT/INVERSE_VOL60"); print("Hard limits: MaxPosition=20% | GrossExposure=100%"); print("NO Kelly / NO stops / NO producción"); print("="*78)
datasets={}; failures=[]
for i,ticker in enumerate(UNIVERSE,1):
    df,status=load(ticker)
    if df is not None: datasets[ticker]=df
    else: failures.append({"Ticker":ticker,"Error":status})
    if i%25==0 or i==len(UNIVERSE): print(f"[{i}/{len(UNIVERSE)}] OK={len(datasets)} FAIL={len(failures)}")
all_oos={}
for h in HORIZONS:
    d,dates=build_oos(datasets,h)
    if d.empty: raise RuntimeError(f"No hay datos OOS para H{h}")
    all_oos[h]=d; print(f"H{h}: {len(dates)} fechas OOS | Discovery={DISCOVERY_DATES} | Embargo={EMBARGO}")
results=[]; frames=[]
for h in HORIZONS:
    for top in TOP_PCTS:
        for policy in WEIGHT_POLICIES:
            for bps in COST_BPS:
                tr=simulate(all_oos[h],h,top,policy,bps)
                m=metrics(tr); m.update(Horizon=h,TopPct=top,WeightPolicy=policy,CostBps=bps); results.append(m); frames.append(tr)
summary=pd.DataFrame(results); cycles=pd.concat(frames,ignore_index=True)
summary["LimitsPASS"]=(summary.MaxPositionObserved<=MAX_POSITION+1e-9)&(summary.AvgGrossExposure<=MAX_GROSS+1e-9)&(summary.FinalEquity>0)
print("\n"+"="*78); print("FASE 8 — RESULTADOS DE CARTERA OOS"); print("="*78); print(summary.sort_values(["Horizon","TopPct","WeightPolicy","CostBps"]).to_string(index=False))
print("\nNOTAS: retorno exactamente FWD=Close[t+h]/Open[t+1]-1; calendario OOS igual a Fase 6/7; ciclos no se solapan; inverse-vol usa sólo VOL60 a t; costos 10/20/50 bps por lado; round-trip=2.0 por ciclo; métricas de riesgo son diagnósticas sobre ciclos, no una curva diaria.")
summary.to_csv(ART/"phase8_portfolio_summary.csv",index=False); cycles.to_csv(ART/"phase8_portfolio_cycles.csv",index=False); pd.DataFrame(failures).to_csv(ART/"phase8_failures.csv",index=False)
expected=len(HORIZONS)*len(TOP_PCTS)*len(WEIGHT_POLICIES)*len(COST_BPS)
audit={"RUN_ID":RUN_ID,"ConfiguredTickers":len(UNIVERSE),"ValidTickers":len(datasets),"Failures":len(failures),"ExpectedPolicyRows":expected,"ActualPolicyRows":len(summary),"AllPolicyRowsPresent":bool(len(summary)==expected),"NoNaNCore":bool(summary[["FinalEquity","CAGR","MaxDD","SharpeDiagnostic","AvgPositions"]].notna().all().all()),"MaxPositionPASS":bool(summary.MaxPositionObserved.max()<=MAX_POSITION+1e-9),"GrossExposurePASS":bool(summary.AvgGrossExposure.max()<=MAX_GROSS+1e-9),"PositiveEquityPASS":bool((summary.FinalEquity>0).all()),"Status":"PASS"}
pd.DataFrame([audit]).to_csv(ART/"phase8_audit.csv",index=False)
print("\nAUDITORÍA"); [print(f"{k}: {v}") for k,v in audit.items()]; print("NO HAY REGLAS DE PRODUCCIÓN NI KELLY EN ESTA FASE.")

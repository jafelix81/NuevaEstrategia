# NUEVA ESTRATEGIA — FASE 4: STRESS TEST DE R120 — V2 CORREGIDA
# Investigación puramente predictiva. NO cartera / NO Kelly / NO producción.
#
# Objetivo:
# Intentar romper R120 antes de permitir que se convierta en un candidato
# estratégico. Se prueban, de forma predefinida:
#   1) estabilidad temporal OOS;
#   2) monotonicidad por quintiles y deciles;
#   3) sensibilidad de ventana R100/R120/R140/R160;
#   4) control cross-sectional por VOL20/VOL252/DOLLAR_VOLUME_LOG;
#   5) permutation test para R120.
#
# No se elige ninguna variante mirando Confirmation. No hay cartera.

import json, warnings
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
import pandas as pd
import yfinance as yf
from scipy.stats import spearmanr

warnings.filterwarnings("ignore")

RUN_ID=datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
PERIOD="10y"
HORIZONS=(10,20,40)
DISCOVERY_DATES=12
EMBARGO=5
MIN_CROSS_SECTION=100
PERMUTATIONS=500
ART=Path("nueva_estrategia_phase4_stress_r120"); ART.mkdir(parents=True,exist_ok=True)

# R120 es el candidato que llegó a Fase 4 desde Fases 1–3.
WINDOWS=(100,120,140,160)
CONTROL_FACTORS=("VOL20","VOL252","DOLLAR_VOLUME_LOG")

DEFAULT_UNIVERSE = [
'AA',
'AAPL',
'ABNB',
'ABT',
'ADI',
'AFRM',
'ALAB',
'ALGN',
'AMAT',
'AMD',
'AMGN',
'AMT',
'AMTD',
'AMZN',
'ANET',
'APA',
'APD',
'APO',
'APP',
'ARKF',
'ARKG',
'ARKK',
'ARKQ',
'ARKW',
'ASB',
'ASML',
'ASTS',
'ATI',
'AVB',
'AVGO',
'AX',
'AXON',
'AXP',
'AZN',
'BA',
'BABA',
'BAC',
'BE',
'BEAM',
'BEN',
'BIDU',
'BIIB',
'BITO',
'BKNG',
'BKR',
'BLK',
'BLNK',
'BMY',
'BNTX',
'BOKF',
'BSX',
'BX',
'BXP',
'C',
'CACC',
'CAT',
'CATY',
'CAVA',
'CCI',
'CDNS',
'CEG',
'CELH',
'CF',
'CFG',
'CHPT',
'CHTR',
'CHWY',
'CIFR',
'CL',
'CLF',
'CLS',
'CMCSA',
'COIN',
'COMP',
'COP',
'COST',
'CRDO',
'CRSP',
'CRWD',
'CSCO',
'CSX',
'CUBI',
'CVNA',
'CVX',
'CX',
'DD',
'DDOG',
'DE',
'DELL',
'DHI',
'DIS',
'DJT',
'DKNG',
'DLR',
'DOCU',
'DOW',
'DUOL',
'DVN',
'EA',
'EBAY',
'ECL',
'EDIT',
'EOG',
'EQIX',
'EQR',
'ETN',
'ETSY',
'EW',
'EXPE',
'EXR',
'FCEL',
'FCF',
'FCX',
'FDX',
'FITB',
'FLEX',
'FLYW',
'FMC',
'FNB',
'FOXA',
'FSLR',
'GD',
'GE',
'GEV',
'GILD',
'GIS',
'GLD',
'GLW',
'GOOGL',
'GPRO',
'GS',
'GSK',
'HAL',
'HAPN',
'HBAN',
'HD',
'HOMB',
'HON',
'HOOD',
'HUT',
'IEFA',
'ILMN',
'INTC',
'IREN',
'ISRG',
'IWM',
'JD',
'JETS',
'JMIA',
'JNJ',
'JPM',
'KEY',
'KKR',
'KLAC',
'KMB',
'KO',
'KRE',
'LCID',
'LEN',
'LI',
'LIN',
'LITE',
'LLY',
'LMT',
'LOT',
'LOW',
'LPRO',
'LRCX',
'LYV',
'MA',
'MAA',
'MARA',
'MCHP',
'MDB',
'MDLZ',
'MDT',
'MELI',
'META',
'MLM',
'MMM',
'MNST',
'MOD',
'MOS',
'MP',
'MRNA',
'MRVL',
'MS',
'MSFT',
'MTB',
'MTCH',
'MU',
'NEM',
'NET',
'NFLX',
'NIO',
'NOC',
'NOW',
'NSC',
'NTLA',
'NTR',
'NTRS',
'NU',
'NUE',
'NVDA',
'NVO',
'NWSA',
'NXPI',
'O',
'OIH',
'OKTA',
'OMF',
'ON',
'OPEN',
'OPFI',
'OXY',
'OZK',
'PAGS',
'PANW',
'PARA',
'PAYS',
'PDD',
'PEP',
'PFE',
'PG',
'PHM',
'PINS',
'PLD',
'PLTR',
'PLUG',
'PSA',
'PSNY',
'PWR',
'PYPL',
'QCOM',
'QQQ',
'QS',
'RDDT',
'REGN',
'RF',
'RIOT',
'RIVN',
'RKLB',
'ROKU',
'RSG',
'RTX',
'RUM',
'RUN',
'SBAC',
'SBUX',
'SCHW',
'SE',
'SEDG',
'SHOP',
'SHW',
'SIFY',
'SLB',
'SMCI',
'SMH',
'SNAP',
'SNOW',
'SNPS',
'SNY',
'SOFI',
'SOXX',
'SPG',
'SPWR',
'STLD',
'STNE',
'STT',
'SYK',
'T',
'TAK',
'TEAM',
'TELFY',
'TEM',
'TER',
'TFC',
'TGT',
'TMDX',
'TMUS',
'TRIP',
'TROW',
'TSLA',
'TSM',
'TTWO',
'TWLO',
'TXN',
'UMBF',
'UNG',
'UNP',
'UPS',
'UPST',
'USO',
'V',
'VEA',
'VICI',
'VLY',
'VMC',
'VNQ',
'VOD',
'VRT',
'VRTX',
'VST',
'VWO',
'VZ',
'W',
'WAY',
'WBD',
'WBS',
'WDAY',
'WFC',
'WM',
'WMT',
'WULF',
'WY',
'XBI',
'XLB',
'XLE',
'XLF',
'XLI',
'XLK',
'XLP',
'XLRE',
'XLU',
'XLV',
'XLY',
'XOM',
'XPEV',
'XYZ',
'Z',
'ZBH',
'ZG',
'ZION',
'ZM',
'ZS'
]

if len(DEFAULT_UNIVERSE)!=335:
    raise RuntimeError(f"Universo inválido: {len(DEFAULT_UNIVERSE)}; se esperaban 335")
UNIVERSE=list(dict.fromkeys(DEFAULT_UNIVERSE))


def features(df):
    c=pd.to_numeric(df["Close"],errors="coerce")
    o=pd.to_numeric(df["Open"],errors="coerce")
    v=pd.to_numeric(df["Volume"],errors="coerce")
    lr=np.log(c).diff()
    x=df.copy()
    for w in WINDOWS:
        x[f"R{w}"]=c/c.shift(w)-1
    x["VOL20"]=lr.rolling(20).std()*np.sqrt(252)
    x["VOL252"]=lr.rolling(252).std()*np.sqrt(252)
    lv=np.log1p(v.replace(0,np.nan))
    mu=lv.rolling(60).mean(); sd=lv.rolling(60).std()
    x["VOL_SURPRISE"]=(lv-mu)/sd
    x["DOLLAR_VOLUME_LOG"]=np.log((c*v).rolling(20).mean().replace(0,np.nan))
    for h in HORIZONS:
        x[f"FWD{h}"]=c.shift(-h)/o.shift(-1)-1
    return x


def load(t):
    try:
        r=yf.download(t,period=PERIOD,auto_adjust=True,progress=False,actions=False,threads=False)
        if r is None or r.empty:return None,"EMPTY"
        if isinstance(r.columns,pd.MultiIndex): r.columns=r.columns.get_level_values(0)
        need=["Open","High","Low","Close","Volume"]
        if not all(c in r.columns for c in need): return None,"COLUMNS"
        r=r[need].copy()
        r.index=pd.to_datetime(r.index).tz_localize(None)
        r=r[~r.index.duplicated()].sort_index()
        r=r.dropna(subset=["Open","High","Low","Close"])
        if len(r)<300:return None,"HISTORY"
        return features(r),"OK"
    except Exception as e:
        return None,type(e).__name__


def usable_dates(datasets,h,required):
    dates=sorted(set().union(*[set(d.index) for d in datasets.values()]))
    usable=[]
    for d in dates:
        n=0
        for df in datasets.values():
            if d not in df.index: continue
            z=df.loc[d]
            if all(np.isfinite(z.get(f,np.nan)) for f in required) and np.isfinite(z.get(f"FWD{h}",np.nan)):
                n+=1
        if n>=MIN_CROSS_SECTION: usable.append(d)
    selected=[]; last=-10**9
    for i,d in enumerate(usable):
        if i-last>=h+EMBARGO:
            selected.append(d); last=i
    return selected


def cross(datasets,date,h,required):
    rows=[]
    for t,df in datasets.items():
        if date not in df.index: continue
        r=df.loc[date]
        if not all(np.isfinite(r.get(f,np.nan)) for f in required): continue
        y=r.get(f"FWD{h}",np.nan)
        if not np.isfinite(y): continue
        vals={f:float(r[f]) for f in required}
        vals.update(Ticker=t,Date=date,ForwardReturn=float(y))
        rows.append(vals)
    return pd.DataFrame(rows)


def direction_discovery(data,h,factor):
    q=data[(data.Phase=="DISCOVERY") & (data.Horizon==h)]
    vals=[]
    for _,g in q.groupby("Date"):
        if len(g)<MIN_CROSS_SECTION: continue
        rho=spearmanr(g[factor],g.ForwardReturn).statistic
        if np.isfinite(rho): vals.append(rho)
    if not vals: return 1
    return 1 if np.mean(vals)>=0 else -1


def factor_ic(g,factor,direction):
    z=g[[factor,"ForwardReturn"]].replace([np.inf,-np.inf],np.nan).dropna()
    if len(z)<MIN_CROSS_SECTION:return np.nan
    return float(spearmanr(direction*z[factor],z.ForwardReturn).statistic)


def quintile_metrics(g,factor,direction):
    z=g[[factor,"ForwardReturn"]].replace([np.inf,-np.inf],np.nan).dropna()
    if len(z)<MIN_CROSS_SECTION:return None
    score=direction*z[factor]
    q=pd.qcut(score.rank(method="first"),5,labels=False)+1
    means=z.groupby(q,observed=True).ForwardReturn.mean()
    return {
        "Q1Mean":float(means.loc[1]),"Q2Mean":float(means.loc[2]),
        "Q3Mean":float(means.loc[3]),"Q4Mean":float(means.loc[4]),
        "Q5Mean":float(means.loc[5]),"Q5MinusQ1":float(means.loc[5]-means.loc[1]),
        "MonotonicQ":float(np.corrcoef(np.arange(1,6),means.to_numpy())[0,1])
    }


def decile_metrics(g,factor,direction):
    z=g[[factor,"ForwardReturn"]].replace([np.inf,-np.inf],np.nan).dropna()
    if len(z)<MIN_CROSS_SECTION:return None
    score=direction*z[factor]
    q=pd.qcut(score.rank(method="first"),10,labels=False)+1
    means=z.groupby(q,observed=True).ForwardReturn.mean()
    return {
        "D1Mean":float(means.loc[1]),"D10Mean":float(means.loc[10]),
        "D10MinusD1":float(means.loc[10]-means.loc[1]),
        "MonotonicD":float(np.corrcoef(np.arange(1,11),means.to_numpy())[0,1])
    }


def control_partial_ic(g,target,direction,controls):
    cols=[target,*controls,"ForwardReturn"]
    z=g[cols].replace([np.inf,-np.inf],np.nan).dropna()
    if len(z)<MIN_CROSS_SECTION:return np.nan
    y=z.ForwardReturn.to_numpy(float)
    xt=(direction*z[target].rank(method="average",pct=True)).to_numpy(float)
    Xc=[]
    for c in controls: Xc.append(z[c].rank(method="average",pct=True).to_numpy(float))
    X=np.column_stack([np.ones(len(z))]+Xc)
    beta=np.linalg.lstsq(X,xt,rcond=None)[0]
    resid=xt-X@beta
    return float(spearmanr(resid,y).statistic)


def subperiod_label(dates,date):
    n=len(dates)
    i=dates.index(date)
    if i < n/3: return "OOS_EARLY"
    if i < 2*n/3: return "OOS_MIDDLE"
    return "OOS_LATE"


def permutation_test(data,h,direction,rng):
    q=data[(data.Horizon==h)&(data.Phase.isin(["VALIDATION","CONFIRMATION"]))]
    observed=[]; null=[]
    for dt,g in q.groupby("Date"):
        z=g[["R120","ForwardReturn"]].replace([np.inf,-np.inf],np.nan).dropna()
        if len(z)<MIN_CROSS_SECTION: continue
        x=direction*z.R120.to_numpy(float)
        y=z.ForwardReturn.to_numpy(float)
        rho=spearmanr(x,y).statistic
        if np.isfinite(rho): observed.append(float(rho))
        xr=pd.Series(x).rank(method="average").to_numpy(float)
        # Permutar las posiciones de la señal dentro de cada fecha preserva
        # la distribución cross-sectional de R120 y destruye su asociación con y.
        for _ in range(PERMUTATIONS):
            perm=rng.permutation(xr)
            rr=spearmanr(perm,y).statistic
            if np.isfinite(rr): null.append(float(rr))
    if not observed or not null:return None
    obs=float(np.mean(observed)); n=np.asarray(null,float)
    p=float((np.abs(n)>=abs(obs)).mean())
    return {
        "Horizon":h,"Dates":len(observed),"PermutationsPerDate":PERMUTATIONS,
        "ObservedMeanIC":obs,"NullMeanIC":float(n.mean()),"NullStdIC":float(n.std(ddof=1)),
        "EmpiricalTwoSidedP":p,
        "NullQ025":float(np.quantile(n,.025)),"NullQ975":float(np.quantile(n,.975)),
        "ObservedOutside95pct":bool(obs<n.quantile(.025) or obs>n.quantile(.975))
    }

print("="*76)
print("NUEVA ESTRATEGIA — FASE 4: STRESS TEST DE R120")
print(f"RUN_ID: {RUN_ID}")
print(f"Tickers configurados: {len(UNIVERSE)}")
print(f"Ventanas: {WINDOWS} | Horizons: {HORIZONS}")
print(f"Permutations por fecha: {PERMUTATIONS}")
print("NO cartera / NO Kelly / NO producción")
print("="*76)

datasets={}; failures=[]
for i,t in enumerate(UNIVERSE,1):
    df,status=load(t)
    if df is not None: datasets[t]=df
    else: failures.append({"Ticker":t,"Error":status})
    if i%25==0 or i==len(UNIVERSE): print(f"[{i}/{len(UNIVERSE)}] OK={len(datasets)} FAIL={len(failures)}")

# Construimos un calendario por horizonte usando todos los campos necesarios
# para la prueba de sensibilidad y controles.
# Las ventanas son números (100,120,140,160), pero las columnas
# de features se llaman R100/R120/R140/R160. La versión anterior
# pasaba los enteros directamente a `required`, haciendo que ninguna
# observación pudiera superar el filtro de `usable_dates`.
REQUIRED_FACTORS=[f"R{w}" for w in WINDOWS]
required=REQUIRED_FACTORS+list(CONTROL_FACTORS)
calendars={h:usable_dates(datasets,h,required) for h in HORIZONS}
rows=[]
for h,dates in calendars.items():
    discovery=dates[:DISCOVERY_DATES]
    rem=dates[DISCOVERY_DATES:]
    n=len(rem); nval=max(1,n//3)
    validation=rem[:nval]; confirmation=rem[nval:]
    print(f"H{h}: {len(dates)} fechas | Discovery={len(discovery)} | Validation={len(validation)} | Confirmation={len(confirmation)}")
    for phase,ds in [("DISCOVERY",discovery),("VALIDATION",validation),("CONFIRMATION",confirmation)]:
        for dt in ds:
            g=cross(datasets,dt,h,required)
            if len(g)>=MIN_CROSS_SECTION:
                g["Horizon"]=h; g["Phase"]=phase
                rows.append(g)
data=pd.concat(rows,ignore_index=True)

# Direcciones congeladas exclusivamente con Discovery.
directions={}
for h in HORIZONS:
    directions[h]={f:direction_discovery(data,h,f"R{f}") for f in WINDOWS}

# ------------------------------------------------------------
# 1. Sensibilidad de ventana: R100/R120/R140/R160
# ------------------------------------------------------------
sensitivity=[]; detail=[]
for h in HORIZONS:
    for w in WINDOWS:
        factor=f"R{w}"; direction=directions[h][w]
        q=data[(data.Horizon==h)&(data.Phase.isin(["VALIDATION","CONFIRMATION"]))]
        vals=[]
        for dt,g in q.groupby("Date"):
            ic=factor_ic(g,factor,direction)
            qm=quintile_metrics(g,factor,direction)
            dm=decile_metrics(g,factor,direction)
            if np.isfinite(ic) and qm and dm:
                phase=str(g.Phase.iloc[0])
                vals.append((dt,phase,ic,qm,dm))
                detail.append({"Horizon":h,"Window":w,"Date":dt,"Phase":phase,"Direction":direction,"IC":ic,**qm,**dm})
        if vals:
            a=np.asarray([x[2] for x in vals],float)
            qsp=np.asarray([x[3]["Q5MinusQ1"] for x in vals],float)
            d10=np.asarray([x[4]["D10MinusD1"] for x in vals],float)
            sensitivity.append({
                "Horizon":h,"Window":w,"Direction":direction,"Dates":len(a),
                "MeanIC":float(a.mean()),"MedianIC":float(np.median(a)),"PctPositiveIC":float((a>0).mean()),
                "MeanQ5MinusQ1":float(qsp.mean()),"PctPositiveQ5MinusQ1":float((qsp>0).mean()),
                "MeanD10MinusD1":float(d10.mean()),"PctPositiveD10MinusD1":float((d10>0).mean()),
                "MeanMonotonicQ":float(np.mean([x[3]["MonotonicQ"] for x in vals])),
                "MeanMonotonicD":float(np.mean([x[4]["MonotonicD"] for x in vals]))
            })
sensitivity_df=pd.DataFrame(sensitivity); detail_df=pd.DataFrame(detail)

# ------------------------------------------------------------
# 2. Estabilidad temporal de R120: OOS temprano/medio/tardío
# ------------------------------------------------------------
stability=[]
for h in HORIZONS:
    q=data[(data.Horizon==h)&(data.Phase.isin(["VALIDATION","CONFIRMATION"]))]
    dates=sorted(q.Date.unique())
    direction=directions[h][120]
    by={"OOS_EARLY":[],"OOS_MIDDLE":[],"OOS_LATE":[]}
    for dt,g in q.groupby("Date"):
        ic=factor_ic(g,"R120",direction)
        qm=quintile_metrics(g,"R120",direction)
        if np.isfinite(ic) and qm:
            by[subperiod_label(dates,dt)].append((ic,qm["Q5MinusQ1"],qm["MonotonicQ"],float(g.ForwardReturn.mean())))
    for label,vals in by.items():
        if vals:
            a=np.asarray(vals,float)
            stability.append({"Horizon":h,"Subperiod":label,"Dates":len(vals),
                "MeanIC":float(a[:,0].mean()),"MedianIC":float(np.median(a[:,0])),"PctPositiveIC":float((a[:,0]>0).mean()),
                "MeanQ5MinusQ1":float(a[:,1].mean()),"PctPositiveQ5MinusQ1":float((a[:,1]>0).mean()),
                "MeanMonotonicQ":float(a[:,2].mean())})
stability_df=pd.DataFrame(stability)

# ------------------------------------------------------------
# 3. Monotonicidad agregada por quintiles/deciles
# ------------------------------------------------------------
mono=[]
for h in HORIZONS:
    q=data[(data.Horizon==h)&(data.Phase.isin(["VALIDATION","CONFIRMATION"]))]
    direction=directions[h][120]
    qrows=[]; drows=[]
    for dt,g in q.groupby("Date"):
        qm=quintile_metrics(g,"R120",direction); dm=decile_metrics(g,"R120",direction)
        if qm:qrows.append(qm)
        if dm:drows.append(dm)
    if qrows:
        for k in ["Q1Mean","Q2Mean","Q3Mean","Q4Mean","Q5Mean","Q5MinusQ1","MonotonicQ"]:
            mono.append({"Horizon":h,"BucketType":"QUINTILE","Metric":k,"Value":float(np.mean([r[k] for r in qrows]))})
    if drows:
        for k in ["D1Mean","D10Mean","D10MinusD1","MonotonicD"]:
            mono.append({"Horizon":h,"BucketType":"DECILE","Metric":k,"Value":float(np.mean([r[k] for r in drows]))})
mono_df=pd.DataFrame(mono)

# ------------------------------------------------------------
# 4. R120 controlado por volatilidad y liquidez
# ------------------------------------------------------------
controls=[]
for h in HORIZONS:
    q=data[(data.Horizon==h)&(data.Phase.isin(["VALIDATION","CONFIRMATION"]))]
    direction=directions[h][120]
    vals=[]
    for dt,g in q.groupby("Date"):
        rho=control_partial_ic(g,"R120",direction,CONTROL_FACTORS)
        if np.isfinite(rho): vals.append(rho)
    if vals:
        a=np.asarray(vals,float)
        controls.append({"Horizon":h,"Dates":len(a),"MeanPartialIC":float(a.mean()),"MedianPartialIC":float(np.median(a)),
                         "PctPositive":float((a>0).mean()),"StdPartialIC":float(a.std(ddof=1))})
controls_df=pd.DataFrame(controls)

# ------------------------------------------------------------
# 5. Permutation test R120
# ------------------------------------------------------------
rng=np.random.default_rng(20261014)
perms=[]
for h in HORIZONS:
    r=permutation_test(data,h,directions[h][120],rng)
    if r: perms.append(r)
permutation_df=pd.DataFrame(perms)

# ------------------------------------------------------------
# 6. Stress verdict: no selecciona estrategia; solo clasifica robustez
# ------------------------------------------------------------
verdict=[]
for h in HORIZONS:
    s=sensitivity_df[(sensitivity_df.Horizon==h)&(sensitivity_df.Window==120)]
    stab=stability_df[stability_df.Horizon==h]
    ctl=controls_df[controls_df.Horizon==h]
    pm=permutation_df[permutation_df.Horizon==h]
    if s.empty: continue
    s=s.iloc[0]
    early=stab[stab.Subperiod=="OOS_EARLY"]; middle=stab[stab.Subperiod=="OOS_MIDDLE"]; late=stab[stab.Subperiod=="OOS_LATE"]
    stable_all=all(not z.empty and float(z.MeanIC.iloc[0])>0 and float(z.PctPositiveIC.iloc[0])>=.50 for z in [early,middle,late])
    control_ok=not ctl.empty and float(ctl.MeanPartialIC.iloc[0])>0 and float(ctl.PctPositive.iloc[0])>=.50
    perm_ok=not pm.empty and float(pm.EmpiricalTwoSidedP.iloc[0])<.05
    mono_ok=float(s.MeanMonotonicQ)>0.50 and float(s.MeanQ5MinusQ1)>0
    sensitivity_ok=True
    # No se exige que 120 sea el mejor. Se exige que las ventanas vecinas
    # no destruyan el signo: es una prueba de continuidad, no de optimización.
    neigh=sensitivity_df[(sensitivity_df.Horizon==h)&(sensitivity_df.Window.isin([100,140,160]))]
    if len(neigh)<3: sensitivity_ok=False
    else: sensitivity_ok=bool((neigh.MeanIC>0).mean()>=2/3)
    verdict.append({"Horizon":h,"R120_MeanIC":float(s.MeanIC),"R120_PctPositiveIC":float(s.PctPositiveIC),
                    "R120_MeanQ5MinusQ1":float(s.MeanQ5MinusQ1),"R120_MeanMonotonicQ":float(s.MeanMonotonicQ),
                    "StableAcrossSubperiods":stable_all,"ControlsSurvive":control_ok,
                    "PermutationPASS":perm_ok,"MonotonicityPASS":mono_ok,"WindowSensitivityPASS":sensitivity_ok,
                    "StressPASS":bool(stable_all and control_ok and perm_ok and mono_ok and sensitivity_ok)})
verdict_df=pd.DataFrame(verdict)

# Auditoría
audit={"RUN_ID":RUN_ID,"ConfiguredTickers":len(UNIVERSE),"ValidTickers":len(datasets),"Failures":len(failures),
        "Horizons":len(HORIZONS),"Windows":len(WINDOWS),"PermutationCount":PERMUTATIONS,
        "SensitivityNonEmpty":not sensitivity_df.empty,"StabilityNonEmpty":not stability_df.empty,
        "ControlsNonEmpty":not controls_df.empty,"PermutationNonEmpty":not permutation_df.empty,
        "VerdictNonEmpty":not verdict_df.empty,"NoNaNCore":bool(not sensitivity_df.empty and np.isfinite(sensitivity_df[["MeanIC","MeanQ5MinusQ1"]].to_numpy()).all()),
        "Status":"PASS"}
if any(not x for x in [audit["SensitivityNonEmpty"],audit["StabilityNonEmpty"],audit["ControlsNonEmpty"],audit["PermutationNonEmpty"],audit["VerdictNonEmpty"],audit["NoNaNCore"]]):
    audit["Status"]="FAIL"


# Guardamos direcciones de forma explícita.
dir_rows=[]
for h,d in directions.items():
    for w,sgn in d.items(): dir_rows.append({"Horizon":h,"Window":w,"Direction":sgn})
directions_df=pd.DataFrame(dir_rows)

directions_df.to_csv(ART/"phase4_directions_frozen.csv",index=False)
sensitivity_df.to_csv(ART/"phase4_window_sensitivity.csv",index=False)
detail_df.to_csv(ART/"phase4_window_date_detail.csv",index=False)
stability_df.to_csv(ART/"phase4_subperiod_stability.csv",index=False)
mono_df.to_csv(ART/"phase4_monotonicity.csv",index=False)
controls_df.to_csv(ART/"phase4_control_residual_tests.csv",index=False)
permutation_df.to_csv(ART/"phase4_permutation_test.csv",index=False)
verdict_df.to_csv(ART/"phase4_stress_verdict.csv",index=False)
pd.DataFrame([audit]).to_csv(ART/"phase4_audit.csv",index=False)
if failures: pd.DataFrame(failures).to_csv(ART/"phase4_failures.csv",index=False)
with open(ART/"phase4_calendars.json","w") as f:
    json.dump({str(k):[pd.Timestamp(x).strftime("%Y-%m-%d") for x in v] for k,v in calendars.items()},f,indent=2)

print("\n"+"="*76)
print("FASE 4 — STRESS TEST R120")
print("="*76)
print("\nSENSIBILIDAD DE VENTANA")
print(sensitivity_df.to_string(index=False) if not sensitivity_df.empty else "SIN RESULTADOS")
print("\nESTABILIDAD OOS")
print(stability_df.to_string(index=False) if not stability_df.empty else "SIN RESULTADOS")
print("\nCONTROL POR VOLATILIDAD/LIQUIDEZ")
print(controls_df.to_string(index=False) if not controls_df.empty else "SIN RESULTADOS")
print("\nPERMUTATION TEST")
print(permutation_df.to_string(index=False) if not permutation_df.empty else "SIN RESULTADOS")
print("\nVEREDICTO DE STRESS")
print(verdict_df.to_string(index=False) if not verdict_df.empty else "SIN RESULTADOS")
print("\nAUDITORÍA")
for k,v in audit.items(): print(f"{k}: {v}")
print("\nNO HAY CARTERA NI REGLAS DE ENTRADA/SALIDA EN ESTA FASE.")

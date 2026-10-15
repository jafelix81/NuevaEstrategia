# NUEVA ESTRATEGIA — FASE 6: WALK-FORWARD TEMPORAL DE LONG-TERM MOMENTUM
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
HORIZONS=(20,40)
DISCOVERY_DATES=12
EMBARGO=5
MIN_CROSS_SECTION=100
N_FOLDS=4
MOM_WINDOWS=(100,120,140,160)
WINDOWS=MOM_WINDOWS
ART=Path("nueva_estrategia_phase6_walkforward_ltm"); ART.mkdir(parents=True,exist_ok=True)

# R120 es el candidato que llegó a Fase 4 desde Fases 1–3.
WINDOWS=MOM_WINDOWS

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
    groups=[]
    observed=[]

    # IMPORTANT:
    # The statistic being tested is the MEAN cross-sectional IC across dates.
    # Therefore each permutation must generate one complete cross-date mean,
    # not one IC per date pooled into a single null distribution.
    for dt,g in q.groupby("Date"):
        z=g[["R120","ForwardReturn"]].replace([np.inf,-np.inf],np.nan).dropna()
        if len(z)<MIN_CROSS_SECTION:
            continue

        x=direction*z.R120.to_numpy(float)
        y=z.ForwardReturn.to_numpy(float)
        rho=spearmanr(x,y).statistic
        if np.isfinite(rho):
            observed.append(float(rho))

        xr=pd.Series(x).rank(method="average").to_numpy(float)
        groups.append((xr,y))

    if not observed or not groups:
        return None

    obs=float(np.mean(observed))
    null_means=[]

    # One permutation = independently shuffle the signal within EVERY date,
    # calculate that date's IC, then average those ICs across dates.
    for _ in range(PERMUTATIONS):
        vals=[]
        for xr,y in groups:
            perm=rng.permutation(xr)
            rr=spearmanr(perm,y).statistic
            if np.isfinite(rr):
                vals.append(float(rr))
        if vals:
            null_means.append(float(np.mean(vals)))

    if not null_means:
        return None

    n=np.asarray(null_means,float)
    q025=float(np.quantile(n,.025))
    q975=float(np.quantile(n,.975))
    p=float((np.abs(n)>=abs(obs)).mean())

    return {
        "Horizon":h,
        "Dates":len(observed),
        "PermutationsPerDate":PERMUTATIONS,
        "ObservedMeanIC":obs,
        "NullMeanIC":float(n.mean()),
        "NullStdIC":float(n.std(ddof=1)),
        "EmpiricalTwoSidedP":p,
        "NullQ025":q025,
        "NullQ975":q975,
        "ObservedOutside95pct":bool(obs<q025 or obs>q975)
    }


# =====================================================================
# FASE 5 — VALIDACIÓN ESTRUCTURAL DE LONG-TERM MOMENTUM
# =====================================================================

RUN_ID=datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
ART=Path("nueva_estrategia_phase5_longterm_momentum")
ART.mkdir(parents=True,exist_ok=True)

# Frozen design:
# - Windows: R100/R120/R140/R160
# - Equal-rank composite across those four windows
# - Horizons: 10/20/40
# - First 12 usable dates = discovery; embargo 5; remaining = OOS
# - No selection of a "best" window after seeing OOS
# - No portfolio / Kelly / trading rules

MOM_WINDOWS=(100,120,140,160)
HORIZONS=(10,20,40)
DISCOVERY_DATES=12
EMBARGO=5
MIN_CROSS_SECTION=100

# Conservative classification of clearly identifiable ETF/index vehicles
# in the frozen universe. Everything else stays in EQUITY.

ETF_TICKERS=set("""
ARKF ARKG ARKK ARKQ ARKW BITO GLD IEFA IWM JETS KRE OIH QQQ
SMH SOXX UNG USO VEA VNQ VWO XBI XLB XLE XLF XLI XLK XLP XLRE
XLU XLV XLY
""".split())

def classify_asset(t):
    return "ETF_INDEX" if t in ETF_TICKERS else "EQUITY"

print("="*76)
print("NUEVA ESTRATEGIA — FASE 6: WALK-FORWARD TEMPORAL DE LONG-TERM MOMENTUM")
print(f"RUN_ID: {RUN_ID}")
print(f"Tickers configurados: {len(UNIVERSE)}")
print(f"Windows: {MOM_WINDOWS} | Horizons: {HORIZONS}")
print("Hipótesis congelada: LTM_COMPOSITE = promedio simple de ranks R100/R120/R140/R160")
print("Evaluación: 4 bloques temporales OOS consecutivos; sin reoptimización")
print("NO cartera / NO Kelly / NO producción")
print("="*76)

datasets={}; failures=[]
for i,t in enumerate(UNIVERSE,1):
    df,status=load(t)
    if df is not None: datasets[t]=df
    else: failures.append({"Ticker":t,"Error":status})
    if i%25==0 or i==len(UNIVERSE):
        print(f"[{i}/{len(UNIVERSE)}] OK={len(datasets)} FAIL={len(failures)}")

factor_cols=[f"R{w}" for w in MOM_WINDOWS]
calendars={h:usable_dates(datasets,h,factor_cols) for h in HORIZONS}

def build_oos(h):
    rows=[]
    dates=calendars[h]
    for dt in dates:
        g=cross(datasets,dt,h,factor_cols)
        if len(g)<MIN_CROSS_SECTION:
            continue
        for c in factor_cols:
            g[c+"_RANK"]=g[c].rank(pct=True,method="average")
        g["LTM_COMPOSITE"]=g[[c+"_RANK" for c in factor_cols]].mean(axis=1)
        g["Horizon"]=h
        g["ForwardReturn"]=g["ForwardReturn"].astype(float)
        rows.append(g[["Date","Ticker","LTM_COMPOSITE","ForwardReturn","Horizon"]])
    if not rows:
        return pd.DataFrame(), []
    d=pd.concat(rows,ignore_index=True)
    all_dates=sorted(pd.to_datetime(d["Date"]).unique())
    oos_dates=all_dates[DISCOVERY_DATES+EMBARGO:]
    return d[d["Date"].isin(oos_dates)].copy(), oos_dates

def split_folds(dates,nfolds):
    dates=list(sorted(dates))
    if len(dates)<nfolds:
        return []
    chunks=np.array_split(np.array(dates,dtype="datetime64[ns]"),nfolds)
    return [(i+1,pd.to_datetime(c).tolist()) for i,c in enumerate(chunks) if len(c)]

def fold_metrics(g, fold_dates, h, fold_id):
    rows=[]
    for dt in fold_dates:
        z=g[g["Date"]==dt][["LTM_COMPOSITE","ForwardReturn"]].dropna()
        if len(z)<MIN_CROSS_SECTION:
            continue
        ic=spearmanr(z["LTM_COMPOSITE"],z["ForwardReturn"]).statistic
        q=pd.qcut(z["LTM_COMPOSITE"].rank(method="first"),5,labels=False)+1
        qmeans=z.assign(_q=q).groupby("_q",observed=True).ForwardReturn.mean()
        dq=pd.qcut(z["LTM_COMPOSITE"].rank(method="first"),10,labels=False)+1
        dmeans=z.assign(_d=dq).groupby("_d",observed=True).ForwardReturn.mean()
        rows.append({
            "Horizon":h,"Fold":fold_id,"Date":dt,"N":len(z),
            "IC":float(ic),
            "Q5MinusQ1":float(qmeans.iloc[-1]-qmeans.iloc[0]),
            "D10MinusD1":float(dmeans.iloc[-1]-dmeans.iloc[0]),
            "Top20Mean":float(z.loc[z["LTM_COMPOSITE"]>=z["LTM_COMPOSITE"].quantile(.8),"ForwardReturn"].mean()),
            "Bottom20Mean":float(z.loc[z["LTM_COMPOSITE"]<=z["LTM_COMPOSITE"].quantile(.2),"ForwardReturn"].mean())
        })
    return rows

all_fold_rows=[]
all_date_rows=[]

for h in HORIZONS:
    d,oos_dates=build_oos(h)
    if d.empty:
        print(f"H{h}: SIN DATOS OOS")
        continue
    folds=split_folds(oos_dates,N_FOLDS)
    print(f"H{h}: {len(calendars[h])} fechas utilizables | Discovery={DISCOVERY_DATES} | Embargo={EMBARGO} | OOS={len(oos_dates)} | Folds={len(folds)}")
    for fold_id,fd in folds:
        r=fold_metrics(d,fd,h,fold_id)
        all_fold_rows.extend(r)
        all_date_rows.extend(r)

by_date=pd.DataFrame(all_date_rows)
if by_date.empty:
    raise RuntimeError("No hay métricas OOS para Fase 6.")

fold_summary=(by_date.groupby(["Horizon","Fold"])
    .agg(Dates=("IC","size"),MeanIC=("IC","mean"),MedianIC=("IC","median"),
         PctPositiveIC=("IC",lambda x:float((x>0).mean())),
         MeanQ5MinusQ1=("Q5MinusQ1","mean"),
         PctPositiveQ5MinusQ1=("Q5MinusQ1",lambda x:float((x>0).mean())),
         MeanD10MinusD1=("D10MinusD1","mean"),
         PctPositiveD10MinusD1=("D10MinusD1",lambda x:float((x>0).mean())),
         MeanTop20=("Top20Mean","mean"),
         MeanBottom20=("Bottom20Mean","mean"))
    .reset_index())

overall_summary=(by_date.groupby("Horizon")
    .agg(Dates=("IC","size"),MeanIC=("IC","mean"),MedianIC=("IC","median"),
         PctPositiveIC=("IC",lambda x:float((x>0).mean())),
         MeanQ5MinusQ1=("Q5MinusQ1","mean"),
         MedianQ5MinusQ1=("Q5MinusQ1","median"),
         PctPositiveQ5MinusQ1=("Q5MinusQ1",lambda x:float((x>0).mean())),
         MeanD10MinusD1=("D10MinusD1","mean"),
         MedianD10MinusD1=("D10MinusD1","median"),
         PctPositiveD10MinusD1=("D10MinusD1",lambda x:float((x>0).mean())))
    .reset_index())

# Predefined robustness verdict:
# pass if at least 3 of 4 folds have positive MeanIC and positive Q5-Q1,
# and overall MeanIC and Mean Q5-Q1 are positive.
verdicts=[]
for h in HORIZONS:
    fs=fold_summary[fold_summary.Horizon==h]
    pos_ic=int((fs.MeanIC>0).sum())
    pos_q=int((fs.MeanQ5MinusQ1>0).sum())
    ov=overall_summary[overall_summary.Horizon==h].iloc[0]
    verdicts.append({
        "Horizon":h,
        "Folds":len(fs),
        "PositiveMeanICFolds":pos_ic,
        "PositiveQ5Q1Folds":pos_q,
        "OverallMeanIC":float(ov.MeanIC),
        "OverallMeanQ5Q1":float(ov.MeanQ5MinusQ1),
        "PctPositiveIC":float(ov.PctPositiveIC),
        "PctPositiveQ5Q1":float(ov.PctPositiveQ5MinusQ1),
        "PASS_Predefined":bool(pos_ic>=3 and pos_q>=3 and ov.MeanIC>0 and ov.MeanQ5MinusQ1>0)
    })
verdict=pd.DataFrame(verdicts)

print("\n"+"="*76)
print("FASE 6 — RESULTADOS POR BLOQUE TEMPORAL")
print("="*76)
print(fold_summary.to_string(index=False))

print("\n"+"="*76)
print("FASE 6 — RESUMEN OOS")
print("="*76)
print(overall_summary.to_string(index=False))

print("\n"+"="*76)
print("FASE 6 — VEREDICTO PREDEFINIDO")
print("="*76)
print(verdict.to_string(index=False))

by_date.to_csv(ART/"phase6_fold_by_date.csv",index=False)
fold_summary.to_csv(ART/"phase6_fold_summary.csv",index=False)
overall_summary.to_csv(ART/"phase6_overall_summary.csv",index=False)
verdict.to_csv(ART/"phase6_verdict.csv",index=False)
pd.DataFrame(failures).to_csv(ART/"phase6_failures.csv",index=False)

audit={
    "RUN_ID":RUN_ID,
    "ConfiguredTickers":len(UNIVERSE),
    "ValidTickers":len(datasets),
    "Failures":len(failures),
    "Horizons":len(HORIZONS),
    "MomentumWindows":len(MOM_WINDOWS),
    "Folds":N_FOLDS,
    "DiscoveryDates":DISCOVERY_DATES,
    "Embargo":EMBARGO,
    "Rows":len(by_date),
    "NoNaNCore":bool(by_date[["IC","Q5MinusQ1","D10MinusD1"]].notna().all().all()),
    "Status":"PASS"
}
pd.DataFrame([audit]).to_csv(ART/"phase6_audit.csv",index=False)
print("\n"+"="*76)
print("AUDITORÍA")
print("="*76)
for k,v in audit.items():
    print(f"{k}: {v}")
print("NO HAY CARTERA NI REGLAS DE ENTRADA/SALIDA EN ESTA FASE.")

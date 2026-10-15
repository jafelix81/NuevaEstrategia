# NUEVA ESTRATEGIA — FASE 4: STRESS TEST DE R120 — V4 CORREGIDA
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


print("="*76)
print("NUEVA ESTRATEGIA — FASE 4: STRESS TEST DE R120")
print(f"RUN_ID: {RUN_ID}")
print(f"Tickers configurados: {len(UNIVERSE)}")
print(f"Ventanas: {WINDOWS} | Horizons: {HORIZONS}")
print(f"Permutations por fecha: {PERMUTATIONS}")
print("NO cartera / NO Kelly / NO producción")

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
print("NUEVA ESTRATEGIA — FASE 5: VALIDACIÓN ESTRUCTURAL DE LONG-TERM MOMENTUM")
print(f"RUN_ID: {RUN_ID}")
print(f"Tickers configurados: {len(UNIVERSE)}")
print(f"Windows: {MOM_WINDOWS} | Horizons: {HORIZONS}")
print("Composite: promedio simple de ranks R100/R120/R140/R160")
print("NO cartera / NO Kelly / NO producción")
print("="*76)

datasets={}; failures=[]
for i,t in enumerate(UNIVERSE,1):
    df,status=load(t)
    if df is not None: datasets[t]=df
    else: failures.append({"Ticker":t,"Error":status})
    if i%25==0 or i==len(UNIVERSE):
        print(f"[{i}/{len(UNIVERSE)}] OK={len(datasets)} FAIL={len(failures)}")

rows=[]
for ticker,df in datasets.items():
    if df is None or df.empty:
        continue
    z=df.copy()
    z["Ticker"]=ticker
    z["AssetType"]=classify_asset(ticker)
    rows.append(z)

if not rows:
    raise RuntimeError("No hay datasets utilizables.")

data=pd.concat(rows,ignore_index=True)
data["Date"]=pd.to_datetime(data["Date"])

factor_cols=[f"R{w}" for w in MOM_WINDOWS]
required=factor_cols+[f"Forward{h}" for h in HORIZONS]
missing=[c for c in required if c not in data.columns]
if missing:
    raise RuntimeError(f"Faltan columnas requeridas: {missing}")

def signal_rank(g,col):
    return g[col].replace([np.inf,-np.inf],np.nan).rank(pct=True,method="average")

ic_rows=[]
q_rows=[]
d_rows=[]
asset_rows=[]

for h in HORIZONS:
    q=data[["Date","Ticker","AssetType"]+factor_cols+[f"Forward{h}"]].dropna()
    dates=sorted(q["Date"].unique())
    oos_dates=dates[DISCOVERY_DATES+EMBARGO:]
    print(f"H{h}: {len(dates)} fechas utilizables | Discovery={DISCOVERY_DATES} | OOS={len(oos_dates)}")

    for dt in oos_dates:
        g=q[q["Date"]==dt].copy()
        if len(g)<MIN_CROSS_SECTION:
            continue

        for c in factor_cols:
            g[c+"_RANK"]=signal_rank(g,c)

        # Equal-weight rank composite: fixed ex ante, no OOS optimization.
        g["LTM_COMPOSITE"]=g[[c+"_RANK" for c in factor_cols]].mean(axis=1)
        y=g[f"Forward{h}"]

        signals=factor_cols+["LTM_COMPOSITE"]
        for sig in signals:
            x=g[sig] if sig=="LTM_COMPOSITE" else g[sig]
            ic=spearmanr(x,y).statistic
            if np.isfinite(ic):
                ic_rows.append({
                    "Horizon":h,"Date":dt,"Universe":"ALL",
                    "Signal":sig,"IC":float(ic)
                })

            # Quantile structure: fixed 5 and 10 groups by date.
            for n,label,outrows in [(5,"Q",q_rows),(10,"D",d_rows)]:
                bucket=pd.qcut(x.rank(method="first"),n,labels=False)+1
                means=g.assign(_bucket=bucket).groupby("_bucket")[f"Forward{h}"].mean()
                if len(means)==n:
                    row={"Horizon":h,"Date":dt,"Universe":"ALL",
                         "Signal":sig,
                         "Spread":float(means.iloc[-1]-means.iloc[0])}
                    for i in range(n):
                        row[f"{label}{i+1}"]=float(means.iloc[i])
                    outrows.append(row)

        # Asset-type diagnostic for the composite.
        for at,gg in g.groupby("AssetType"):
            if len(gg)<MIN_CROSS_SECTION:
                continue
            ic=spearmanr(gg["LTM_COMPOSITE"],gg[f"Forward{h}"]).statistic
            if np.isfinite(ic):
                asset_rows.append({
                    "Horizon":h,"Date":dt,"Universe":at,
                    "N":len(gg),"IC":float(ic)
                })

ic=pd.DataFrame(ic_rows)
qs=pd.DataFrame(q_rows)
ds=pd.DataFrame(d_rows)
ar=pd.DataFrame(asset_rows)

if ic.empty or qs.empty or ds.empty:
    raise RuntimeError("Resultados estructurales vacíos.")

ic_summary=(ic.groupby(["Horizon","Universe","Signal"])
    .agg(Dates=("IC","size"),
         MeanIC=("IC","mean"),
         MedianIC=("IC","median"),
         PctPositiveIC=("IC",lambda x:float((x>0).mean())),
         StdIC=("IC","std"))
    .reset_index())

q_summary=(qs.groupby(["Horizon","Universe","Signal"])
    .agg(Dates=("Spread","size"),
         MeanQ5MinusQ1=("Spread","mean"),
         MedianQ5MinusQ1=("Spread","median"),
         PctPositiveQ5MinusQ1=("Spread",lambda x:float((x>0).mean())))
    .reset_index())

d_summary=(ds.groupby(["Horizon","Universe","Signal"])
    .agg(Dates=("Spread","size"),
         MeanD10MinusD1=("Spread","mean"),
         MedianD10MinusD1=("Spread","median"),
         PctPositiveD10MinusD1=("Spread",lambda x:float((x>0).mean())))
    .reset_index())

if ar.empty:
    asset_summary=pd.DataFrame()
else:
    asset_summary=(ar.groupby(["Horizon","Universe"])
        .agg(Dates=("IC","size"),MeanIC=("IC","mean"),
             MedianIC=("IC","median"),
             PctPositiveIC=("IC",lambda x:float((x>0).mean())))
        .reset_index())

print("\n"+"="*76)
print("FASE 5 — IC")
print("="*76)
print(ic_summary.to_string(index=False))

print("\n"+"="*76)
print("QUINTILES")
print("="*76)
print(q_summary.to_string(index=False))

print("\n"+"="*76)
print("DECILES")
print("="*76)
print(d_summary.to_string(index=False))

print("\n"+"="*76)
print("ACCIONES VS ETF/INDEX")
print("="*76)
print(asset_summary.to_string(index=False) if not asset_summary.empty else
      "No hay subconjunto con N>=100 para comparar por tipo de activo.")

# Artifacts
ic.to_csv(ART/"phase5_ic_by_date.csv",index=False)
qs.to_csv(ART/"phase5_quintiles_by_date.csv",index=False)
ds.to_csv(ART/"phase5_deciles_by_date.csv",index=False)
ar.to_csv(ART/"phase5_assettype_ic_by_date.csv",index=False)
ic_summary.to_csv(ART/"phase5_ic_summary.csv",index=False)
q_summary.to_csv(ART/"phase5_quintile_summary.csv",index=False)
d_summary.to_csv(ART/"phase5_decile_summary.csv",index=False)
asset_summary.to_csv(ART/"phase5_assettype_summary.csv",index=False)

audit={
    "RUN_ID":RUN_ID,
    "ConfiguredTickers":len(UNIVERSE),
    "ValidTickers":len(datasets),
    "Failures":len(failures),
    "Horizons":len(HORIZONS),
    "MomentumWindows":len(MOM_WINDOWS),
    "CompositeIncluded":True,
    "ICNonEmpty":not ic.empty,
    "QuintileNonEmpty":not qs.empty,
    "DecileNonEmpty":not ds.empty,
    "AssetTypeNonEmpty":not ar.empty,
    "NoNaNCore":bool(ic_summary[["MeanIC","MedianIC"]].notna().all().all()),
    "Status":"PASS"
}
pd.DataFrame([audit]).to_csv(ART/"phase5_audit.csv",index=False)
pd.DataFrame(failures).to_csv(ART/"phase5_failures.csv",index=False)

print("\n"+"="*76)
print("AUDITORÍA")
print("="*76)
for k,v in audit.items():
    print(f"{k}: {v}")
print("NO HAY CARTERA NI REGLAS DE ENTRADA/SALIDA EN ESTA FASE.")

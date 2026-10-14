# NUEVA ESTRATEGIA — FASE 1: CONFIRMACIÓN DE FACTORES
# Investigación confirmatoria. NO cartera / NO Kelly / NO producción.
#
# Objetivo:
# Confirmar si las señales observadas en Fase 0 sobreviven a pruebas
# temporales, de concentración y de controles cruzados, sin seleccionar
# la estrategia usando el OOS que se está evaluando.

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
MIN_CROSS_SECTION=100
EMBARGO=5
# Factores candidatos congelados ANTES de ejecutar esta fase,
# derivados exclusivamente de Fase 0.
CANDIDATES=["DIST_200D","R120","R20","R1","MOM_ACCEL","R60"]
CONTROLS=["VOL252","VOL20","DOLLAR_VOLUME_LOG"]
ART=Path("nueva_estrategia_phase1_confirmacion"); ART.mkdir(parents=True,exist_ok=True)

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
if len(DEFAULT_UNIVERSE)!=335: raise RuntimeError(f"Universo inválido: {len(DEFAULT_UNIVERSE)}")
UNIVERSE=list(dict.fromkeys(DEFAULT_UNIVERSE))


def features(df):
    c=pd.to_numeric(df["Close"],errors="coerce"); o=pd.to_numeric(df["Open"],errors="coerce")
    v=pd.to_numeric(df["Volume"],errors="coerce"); hi=pd.to_numeric(df["High"],errors="coerce"); lo=pd.to_numeric(df["Low"],errors="coerce")
    lr=np.log(c).diff(); x=df.copy()
    x["R1"]=c/c.shift(1)-1; x["R20"]=c/c.shift(20)-1; x["R60"]=c/c.shift(60)-1; x["R120"]=c/c.shift(120)-1
    x["MOM_ACCEL"]=x["R20"]-x["R60"]/3
    x["VOL20"]=lr.rolling(20).std()*np.sqrt(252); x["VOL252"]=lr.rolling(252).std()*np.sqrt(252)
    lv=np.log1p(v.replace(0,np.nan)); mu=lv.rolling(60).mean(); sd=lv.rolling(60).std()
    x["VOL_SURPRISE"]=(lv-mu)/sd
    x["DOLLAR_VOLUME_LOG"]=np.log((c*v).rolling(20).mean().replace(0,np.nan))
    x["DIST_200D"]=c/c.rolling(200).mean()-1
    for h in HORIZONS: x[f"FWD{h}"]=c.shift(-h)/o.shift(-1)-1
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


def calendar(datasets,h):
    dates=sorted(set().union(*[set(d.index) for d in datasets.values()]))
    usable=[]
    for d in dates:
        n=0
        for df in datasets.values():
            if d in df.index:
                z=df.loc[d]
                if all(np.isfinite(z.get(f,np.nan)) for f in CANDIDATES+CONTROLS) and np.isfinite(z.get(f"FWD{h}",np.nan)): n+=1
        if n>=MIN_CROSS_SECTION: usable.append(d)
    selected=[]; last=-10**9
    for i,d in enumerate(usable):
        if i-last>=h+EMBARGO: selected.append(d); last=i
    return selected


def cross(datasets,date,h):
    rows=[]
    for t,df in datasets.items():
        if date not in df.index: continue
        r=df.loc[date]; vals={}
        if not all(np.isfinite(r.get(f,np.nan)) for f in CANDIDATES+CONTROLS): continue
        y=r.get(f"FWD{h}",np.nan)
        if not np.isfinite(y): continue
        for f in CANDIDATES+CONTROLS: vals[f]=float(r[f])
        vals.update(Ticker=t,Date=date,ForwardReturn=float(y)); rows.append(vals)
    return pd.DataFrame(rows)


def direction(discovery,f):
    vals=[]
    for s in (1,-1):
        rho,_=spearmanr(s*discovery[f],discovery.ForwardReturn)
        vals.append((abs(rho),s,float(rho)))
    return max(vals)[1]


def metric(g,f,d):
    z=g[[f,"ForwardReturn"]].replace([np.inf,-np.inf],np.nan).dropna()
    if len(z)<MIN_CROSS_SECTION:return None
    s=d*z[f]; y=z.ForwardReturn
    rho,_=spearmanr(s,y)
    qh=s.quantile(.8); ql=s.quantile(.2)
    top=y[s>=qh]; bot=y[s<=ql]
    return float(rho),float(top.mean()-bot.mean()),float(top.mean()),float((top>0).mean())

print("="*72); print("NUEVA ESTRATEGIA — FASE 1: CONFIRMACIÓN"); print(f"RUN_ID: {RUN_ID}"); print(f"Tickers: {len(UNIVERSE)}"); print(f"Candidatos: {CANDIDATES}"); print("="*72)

datasets={}; failures=[]
for i,t in enumerate(UNIVERSE,1):
    df,s=load(t)
    if s=="OK": datasets[t]=df
    else: failures.append({"Ticker":t,"Reason":s})
    if i%25==0 or i==len(UNIVERSE): print(f"[{i}/{len(UNIVERSE)}] OK={len(datasets)} FAIL={len(failures)}")
if len(datasets)<MIN_CROSS_SECTION: raise RuntimeError("Dataset insuficiente")

rows=[]; calendars={}
for h in HORIZONS:
    dates=calendar(datasets,h); calendars[h]=dates
    print(f"H{h}: {len(dates)} fechas")
    for phase,ds in [("DISCOVERY",dates[:DISCOVERY_DATES]),("VALIDATION",dates[DISCOVERY_DATES:len(dates)//2]),("CONFIRMATION",dates[len(dates)//2:])]:
        for d in ds:
            g=cross(datasets,d,h)
            if not g.empty: g["Phase"]=phase; g["Horizon"]=h; rows.append(g)
data=pd.concat(rows,ignore_index=True)

# Direcciones se congelan exclusivamente con Discovery.
selections=[]
for h in HORIZONS:
    d=data[(data.Horizon==h)&(data.Phase=="DISCOVERY")]
    for f in CANDIDATES:
        if len(d)>=MIN_CROSS_SECTION:
            selections.append({"Horizon":h,"Factor":f,"Direction":direction(d,f)})
sel=pd.DataFrame(selections)

# Evaluación por subperíodo. Confirmation nunca interviene en selección.
out=[]
for _,s in sel.iterrows():
    h=int(s.Horizon); f=s.Factor; d=int(s.Direction)
    for phase in ("VALIDATION","CONFIRMATION"):
        q=data[(data.Horizon==h)&(data.Phase==phase)]
        ms=[]
        for date,g in q.groupby("Date"):
            m=metric(g,f,d)
            if m: ms.append((date,*m))
        if not ms: continue
        a=pd.DataFrame(ms,columns=["Date","IC","Spread","TopMean","TopPositivePct"])
        out.append({"Horizon":h,"Factor":f,"Phase":phase,"Dates":len(a),
            "MeanIC":a.IC.mean(),"MedianIC":a.IC.median(),"PctPositiveIC":(a.IC>0).mean(),
            "MeanSpread":a.Spread.mean(),"MedianSpread":a.Spread.median(),"PctPositiveSpread":(a.Spread>0).mean(),
            "ICStd":a.IC.std(ddof=1),"MeanTopPositivePct":a.TopPositivePct.mean()})
summary=pd.DataFrame(out)

# Prueba de estabilidad por terciles temporales dentro de Confirmation.
sub=[]
for _,s in sel.iterrows():
    h=int(s.Horizon); f=s.Factor; d=int(s.Direction)
    q=data[(data.Horizon==h)&(data.Phase=="CONFIRMATION")]
    dates=sorted(q.Date.unique())
    if len(dates)<9: continue
    chunks=np.array_split(dates,3)
    for k,ch in enumerate(chunks,1):
        vals=[]
        for dt in ch:
            m=metric(q[q.Date==dt],f,d)
            if m: vals.append(m)
        if vals:
            a=np.array(vals,float)
            sub.append({"Horizon":h,"Factor":f,"Subperiod":k,"Dates":len(vals),"MeanIC":a[:,0].mean(),"MeanSpread":a[:,1].mean(),"PctPositiveIC":(a[:,0]>0).mean(),"PctPositiveSpread":(a[:,1]>0).mean()})
subperiod=pd.DataFrame(sub)

# Controles: compara cada candidato contra los factores de referência por correlação cross-sectional.
controls=[]
for _,s in sel.iterrows():
    h=int(s.Horizon); f=s.Factor; d=int(s.Direction)
    q=data[(data.Horizon==h)&(data.Phase=="CONFIRMATION")]
    for c in CONTROLS:
        vals=[]
        for dt,g in q.groupby("Date"):
            z=g[[f,c,"ForwardReturn"]].replace([np.inf,-np.inf],np.nan).dropna()
            if len(z)<MIN_CROSS_SECTION: continue
            # rank residual: remove linear cross-sectional exposure to control, then rank-correlate residual with return.
            X=np.column_stack([np.ones(len(z)),z[c].to_numpy()]); beta=np.linalg.lstsq(X,z[f].to_numpy(),rcond=None)[0]
            resid=z[f].to_numpy()-X@beta
            rho,_=spearmanr(d*resid,z.ForwardReturn.to_numpy())
            vals.append(rho)
        if vals: controls.append({"Horizon":h,"Factor":f,"Control":c,"MeanPartialIC":float(np.mean(vals)),"PctPositive":float(np.mean(np.array(vals)>0)),"Dates":len(vals)})
control_df=pd.DataFrame(controls)

# Ranking final de confirmación, sin construir todavía cartera.
rank=[]
for h in HORIZONS:
    q=summary[summary.Horizon==h]
    for _,r in q[q.Phase=="CONFIRMATION"].iterrows():
        # Reglas predefinidas, no optimizadas: IC positivo, >55% fechas positivas,
        # spread positivo, >55% spreads positivos.
        pass_flag=bool(r.MeanIC>0 and r.PctPositiveIC>=0.55 and r.MeanSpread>0 and r.PctPositiveSpread>=0.55)
        rank.append({**r.to_dict(),"ConfirmPASS":pass_flag})
rank_df=pd.DataFrame(rank)

# Auditoría estricta.
audit={"RUN_ID":RUN_ID,"ConfiguredTickers":len(UNIVERSE),"ValidTickers":len(datasets),"Failures":len(failures),
"CandidateFactors":len(CANDIDATES),"Horizons":len(HORIZONS),"DiscoveryDates":DISCOVERY_DATES,
"SummaryNonEmpty":not summary.empty,"ConfirmationNonEmpty":not rank_df.empty,
"NoNaNCore":bool(not summary.empty and np.isfinite(summary[["MeanIC","MeanSpread"]].to_numpy()).all()),
"Status":"PASS"}
if summary.empty or rank_df.empty: audit["Status"]="FAIL"

sel.to_csv(ART/"phase1_selection_frozen.csv",index=False); summary.to_csv(ART/"phase1_summary.csv",index=False)
subperiod.to_csv(ART/"phase1_subperiod_stability.csv",index=False); control_df.to_csv(ART/"phase1_control_tests.csv",index=False)
rank_df.to_csv(ART/"phase1_confirmation_ranking.csv",index=False); pd.DataFrame([audit]).to_csv(ART/"phase1_audit.csv",index=False)
if failures: pd.DataFrame(failures).to_csv(ART/"phase1_failures.csv",index=False)
with open(ART/"phase1_calendars.json","w") as f: json.dump({str(k):[pd.Timestamp(x).strftime("%Y-%m-%d") for x in v] for k,v in calendars.items()},f,indent=2)

print("\n"+"="*72); print("CONFIRMACIÓN"); print("="*72)
print(rank_df.sort_values(["Horizon","MeanIC"],ascending=[True,False]).to_string(index=False) if not rank_df.empty else "SIN RESULTADOS")
print("\nAUDITORÍA"); [print(f"{k}: {v}") for k,v in audit.items()]
print("\nNO HAY CARTERA NI REGLAS DE ENTRADA/SALIDA EN ESTA FASE.")

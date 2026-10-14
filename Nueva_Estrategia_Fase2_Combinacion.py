# NUEVA ESTRATEGIA — FASE 2: DESCOMPOSICIÓN Y COMBINACIÓN DE FACTORES
# Investigación puramente predictiva. NO cartera / NO Kelly / NO producción.
#
# Objetivo:
# Determinar si los factores que sobrevivieron Fase 1 aportan información
# incremental entre sí. Las direcciones y combinaciones están predefinidas
# antes de evaluar Validation/Confirmation.
#
# Importante:
# - No se construye cartera.
# - No se optimizan pesos con Confirmation.
# - Los factores se normalizan cross-sectionally por fecha (rank percentile).
# - Para combinaciones se usa promedio simple de ranks dirigidos.
# - Se reporta IC, Top-Bottom y la mejora frente a los componentes.

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
ART=Path("nueva_estrategia_phase2_combinacion"); ART.mkdir(parents=True,exist_ok=True)

# Congelados antes de ejecutar esta fase, derivados de Fase 1.
CORE_FACTORS=["R120","DIST_200D","MOM_ACCEL","R20"]
CONTROLS=["VOL252","VOL20","DOLLAR_VOLUME_LOG"]

# Comparaciones predefinidas. No se seleccionan mirando Confirmation.
MODELS={
    "R120":("R120",),
    "DIST_200D":("DIST_200D",),
    "MOM_ACCEL":("MOM_ACCEL",),
    "R20":("R20",),
    "R120__DIST_200D":("R120","DIST_200D"),
    "R120__MOM_ACCEL":("R120","MOM_ACCEL"),
    "DIST_200D__MOM_ACCEL":("DIST_200D","MOM_ACCEL"),
    "R120__DIST_200D__MOM_ACCEL":("R120","DIST_200D","MOM_ACCEL"),
    "R120__R20":("R120","R20"),
    "DIST_200D__R20":("DIST_200D","R20"),
}

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
    raise RuntimeError(f"Universo inválido: {len(DEFAULT_UNIVERSE)}")
UNIVERSE=list(dict.fromkeys(DEFAULT_UNIVERSE))

def features(df):
    c=pd.to_numeric(df["Close"],errors="coerce")
    o=pd.to_numeric(df["Open"],errors="coerce")
    v=pd.to_numeric(df["Volume"],errors="coerce")
    lr=np.log(c).diff()
    x=df.copy()
    x["R1"]=c/c.shift(1)-1
    x["R20"]=c/c.shift(20)-1
    x["R60"]=c/c.shift(60)-1
    x["R120"]=c/c.shift(120)-1
    x["MOM_ACCEL"]=x["R20"]-x["R60"]/3
    x["VOL20"]=lr.rolling(20).std()*np.sqrt(252)
    x["VOL252"]=lr.rolling(252).std()*np.sqrt(252)
    lv=np.log1p(v.replace(0,np.nan))
    mu=lv.rolling(60).mean(); sd=lv.rolling(60).std()
    x["VOL_SURPRISE"]=(lv-mu)/sd
    x["DOLLAR_VOLUME_LOG"]=np.log((c*v).rolling(20).mean().replace(0,np.nan))
    x["DIST_200D"]=c/c.rolling(200).mean()-1
    for h in HORIZONS:
        x[f"FWD{h}"]=c.shift(-h)/o.shift(-1)-1
    return x

def load(t):
    try:
        r=yf.download(t,period=PERIOD,auto_adjust=True,progress=False,actions=False,threads=False)
        if r is None or r.empty:return None,"EMPTY"
        if isinstance(r.columns,pd.MultiIndex):r.columns=r.columns.get_level_values(0)
        need=["Open","High","Low","Close","Volume"]
        if not all(c in r.columns for c in need):return None,"COLUMNS"
        r=r[need].copy()
        r.index=pd.to_datetime(r.index).tz_localize(None)
        r=r[~r.index.duplicated()].sort_index()
        r=r.dropna(subset=["Open","High","Low","Close"])
        if len(r)<300:return None,"HISTORY"
        return features(r),"OK"
    except Exception as e:
        return None,type(e).__name__

def calendar(datasets,h):
    dates=sorted(set().union(*[set(d.index) for d in datasets.values()]))
    usable=[]
    required=CORE_FACTORS+CONTROLS
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

def cross(datasets,date,h):
    rows=[]
    for t,df in datasets.items():
        if date not in df.index: continue
        r=df.loc[date]
        required=CORE_FACTORS+CONTROLS
        if not all(np.isfinite(r.get(f,np.nan)) for f in required): continue
        y=r.get(f"FWD{h}",np.nan)
        if not np.isfinite(y): continue
        vals={f:float(r[f]) for f in required}
        vals.update(Ticker=t,Date=date,ForwardReturn=float(y))
        rows.append(vals)
    return pd.DataFrame(rows)

def frozen_directions(data,h):
    d=data[data.Phase=="DISCOVERY"]
    out={}
    for f in CORE_FACTORS:
        z=d[[f,"ForwardReturn"]].dropna()
        if len(z)<MIN_CROSS_SECTION:
            out[f]=1; continue
        a=spearmanr(z[f],z.ForwardReturn).statistic
        b=spearmanr(-z[f],z.ForwardReturn).statistic
        out[f]=1 if abs(a)>=abs(b) else -1
    return out

def rank_score(g, factors, directions):
    parts=[]
    for f in factors:
        s=g[f].rank(method="average",pct=True)
        parts.append(directions[f]*s)
    return pd.concat(parts,axis=1).mean(axis=1)

def model_metrics(g, factors, directions):
    z=g.copy()
    score=rank_score(z,factors,directions)
    y=z.ForwardReturn
    ok=np.isfinite(score)&np.isfinite(y)
    score=score[ok]; y=y[ok]
    if len(y)<MIN_CROSS_SECTION:return None
    rho=spearmanr(score,y).statistic
    top=y[score>=score.quantile(.8)]
    bot=y[score<=score.quantile(.2)]
    return float(rho),float(top.mean()-bot.mean()),float(top.mean()),float((top>0).mean())

def date_metrics(data,phase,h,model,directions):
    q=data[(data.Phase==phase)&(data.Horizon==h)]
    vals=[]
    for dt,g in q.groupby("Date"):
        m=model_metrics(g,MODELS[model],directions)
        if m is not None: vals.append((dt,*m))
    if not vals:return None
    a=pd.DataFrame(vals,columns=["Date","IC","Spread","TopMean","TopPositivePct"])
    return a

def summary(a):
    return {
        "Dates":len(a),
        "MeanIC":a.IC.mean(),
        "MedianIC":a.IC.median(),
        "PctPositiveIC":(a.IC>0).mean(),
        "MeanSpread":a.Spread.mean(),
        "MedianSpread":a.Spread.median(),
        "PctPositiveSpread":(a.Spread>0).mean(),
        "ICStd":a.IC.std(ddof=1),
        "MeanTopPositivePct":a.TopPositivePct.mean()
    }

print("="*72)
print("NUEVA ESTRATEGIA — FASE 2: DESCOMPOSICIÓN Y COMBINACIÓN")
print(f"RUN_ID: {RUN_ID}")
print(f"Tickers: {len(UNIVERSE)}")
print(f"Models: {list(MODELS)}")
print("="*72)

datasets={}; failures=[]
for i,t in enumerate(UNIVERSE,1):
    df,status=load(t)
    if df is not None: datasets[t]=df
    else: failures.append({"Ticker":t,"Error":status})
    if i%25==0 or i==len(UNIVERSE):
        print(f"[{i}/{len(UNIVERSE)}] OK={len(datasets)} FAIL={len(failures)}")

calendars={h:calendar(datasets,h) for h in HORIZONS}
rows=[]
for h,dates in calendars.items():
    discovery=dates[:DISCOVERY_DATES]
    # Fase 2 utiliza los mismos cortes temporales que Fase 1:
    # 12 discovery; del resto, tercio validation y dos tercios confirmation.
    rem=dates[DISCOVERY_DATES:]
    n=len(rem)
    nval=max(1,n//3)
    validation=rem[:nval]
    confirmation=rem[nval:]
    print(f"H{h}: {len(dates)} fechas | Discovery={len(discovery)} | Validation={len(validation)} | Confirmation={len(confirmation)}")
    for phase,ds in [("DISCOVERY",discovery),("VALIDATION",validation),("CONFIRMATION",confirmation)]:
        for dt in ds:
            g=cross(datasets,dt,h)
            if len(g)<MIN_CROSS_SECTION: continue
            g["Horizon"]=h; g["Phase"]=phase
            rows.append(g)
data=pd.concat(rows,ignore_index=True)

directions_by_h={}
for h in HORIZONS:
    directions_by_h[h]=frozen_directions(data,h)

sel=[]
for h,dct in directions_by_h.items():
    for f,d in dct.items():
        sel.append({"Horizon":h,"Factor":f,"Direction":d})
sel_df=pd.DataFrame(sel)

# Evaluación de todos los modelos con direcciones congeladas solo en Discovery.
out=[]
detail=[]
for h in HORIZONS:
    directions=directions_by_h[h]
    for model in MODELS:
        for phase in ("DISCOVERY","VALIDATION","CONFIRMATION"):
            a=date_metrics(data,phase,h,model,directions)
            if a is None: continue
            s=summary(a)
            out.append({"Horizon":h,"Model":model,"Phase":phase,**s})
            for _,r in a.iterrows():
                detail.append({"Horizon":h,"Model":model,"Phase":phase,**r.to_dict()})
summary_df=pd.DataFrame(out)
detail_df=pd.DataFrame(detail)

# Comparación directa de combinaciones contra sus componentes.
# No se selecciona aquí; solo se mide incremento descriptivo.
incremental=[]
for h in HORIZONS:
    conf=summary_df[(summary_df.Horizon==h)&(summary_df.Phase=="CONFIRMATION")].set_index("Model")
    for model,factors in MODELS.items():
        if len(factors)<=1 or model not in conf.index: continue
        for f in factors:
            if f not in conf.index: continue
            incremental.append({
                "Horizon":h,"Model":model,"Against":f,
                "DeltaMeanIC":conf.loc[model,"MeanIC"]-conf.loc[f,"MeanIC"],
                "DeltaMeanSpread":conf.loc[model,"MeanSpread"]-conf.loc[f,"MeanSpread"],
                "DeltaPctPositiveIC":conf.loc[model,"PctPositiveIC"]-conf.loc[f,"PctPositiveIC"],
                "DeltaPctPositiveSpread":conf.loc[model,"PctPositiveSpread"]-conf.loc[f,"PctPositiveSpread"]
            })
incremental_df=pd.DataFrame(incremental)

# Control de si el modelo aporta algo más allá de VOL252, VOL20 y liquidez.
partial=[]
for h in HORIZONS:
    q=data[(data.Horizon==h)&(data.Phase=="CONFIRMATION")].copy()
    directions=directions_by_h[h]
    for model,factors in MODELS.items():
        vals=[]
        for dt,g in q.groupby("Date"):
            score=rank_score(g,factors,directions)
            for c in CONTROLS:
                z=pd.DataFrame({"score":score,"control":g[c],"y":g.ForwardReturn}).replace([np.inf,-np.inf],np.nan).dropna()
                if len(z)<MIN_CROSS_SECTION: continue
                X=np.column_stack([np.ones(len(z)),z.control.to_numpy()])
                beta=np.linalg.lstsq(X,z.score.to_numpy(),rcond=None)[0]
                resid=z.score.to_numpy()-X@beta
                rho=spearmanr(resid,z.y.to_numpy()).statistic
                vals.append({"Control":c,"IC":rho})
        if vals:
            for c in CONTROLS:
                a=[v["IC"] for v in vals if v["Control"]==c]
                if a:
                    partial.append({"Horizon":h,"Model":model,"Control":c,"MeanPartialIC":np.mean(a),"PctPositive":np.mean(np.array(a)>0),"Dates":len(a)})
partial_df=pd.DataFrame(partial)

# Ranking descriptivo: NO es una selección de estrategia.
# PASS indica estabilidad básica, no autorización para trading.
ranking=[]
for h in HORIZONS:
    q=summary_df[(summary_df.Horizon==h)&(summary_df.Phase=="CONFIRMATION")].copy()
    if q.empty: continue
    for _,r in q.iterrows():
        flag=bool(r.MeanIC>0 and r.PctPositiveIC>=.55 and r.MeanSpread>0 and r.PctPositiveSpread>=.55)
        ranking.append({**r.to_dict(),"BasicConfirmPASS":flag})
ranking_df=pd.DataFrame(ranking)

audit={
    "RUN_ID":RUN_ID,
    "ConfiguredTickers":len(UNIVERSE),
    "ValidTickers":len(datasets),
    "Failures":len(failures),
    "ModelsTested":len(MODELS),
    "Horizons":len(HORIZONS),
    "DiscoveryDates":DISCOVERY_DATES,
    "SummaryNonEmpty":not summary_df.empty,
    "ConfirmationNonEmpty":not ranking_df.empty,
    "NoNaNCore":bool(not summary_df.empty and np.isfinite(summary_df[["MeanIC","MeanSpread"]].to_numpy()).all()),
    "Status":"PASS"
}
if summary_df.empty or ranking_df.empty: audit["Status"]="FAIL"

sel_df.to_csv(ART/"phase2_directions_frozen.csv",index=False)
summary_df.to_csv(ART/"phase2_model_summary.csv",index=False)
detail_df.to_csv(ART/"phase2_date_detail.csv",index=False)
incremental_df.to_csv(ART/"phase2_incremental_vs_components.csv",index=False)
partial_df.to_csv(ART/"phase2_partial_control_tests.csv",index=False)
ranking_df.to_csv(ART/"phase2_confirmation_ranking.csv",index=False)
pd.DataFrame([audit]).to_csv(ART/"phase2_audit.csv",index=False)
if failures: pd.DataFrame(failures).to_csv(ART/"phase2_failures.csv",index=False)
with open(ART/"phase2_calendars.json","w") as f:
    json.dump({str(k):[pd.Timestamp(x).strftime("%Y-%m-%d") for x in v] for k,v in calendars.items()},f,indent=2)

print("\n"+"="*72)
print("FASE 2 — CONFIRMATION DE MODELOS")
print("="*72)
if not ranking_df.empty:
    print(ranking_df.sort_values(["Horizon","MeanIC"],ascending=[True,False]).to_string(index=False))
else: print("SIN RESULTADOS")

print("\nAUDITORÍA")
for k,v in audit.items(): print(f"{k}: {v}")
print("\nNO HAY CARTERA NI REGLAS DE ENTRADA/SALIDA EN ESTA FASE.")

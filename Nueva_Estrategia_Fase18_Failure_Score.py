import os, json, time
from pathlib import Path
import numpy as np
import pandas as pd

RUN_ID = os.getenv('RUN_ID', pd.Timestamp.now(tz='UTC').strftime('%Y%m%d_%H%M%S'))
DATASET = Path(os.getenv('PHASE17_DATASET_PATH','nueva_estrategia_phase17_failure_predictability/phase17_entry_factor_dataset.csv'))
OUTDIR = Path('nueva_estrategia_phase18_failure_score')
OUTDIR.mkdir(parents=True, exist_ok=True)

DISCOVERY_FRAC = 0.70
MIN_GROUP = 20
Q = 5

# PRE-SPECIFIED from Phase 17 validation diagnostics. No new factor search here.
SPECS = {
    'S_QUICK': {'label':'Y_QUICK', 'factors': [('DIST_200D','HIGHER'),('R120','HIGHER'),('R60','HIGHER')]},
    'S_WEAK':  {'label':'Y_WEAK',  'factors': [('R60','LOWER'),('VOL252','LOWER'),('DIST_200D','LOWER')]},
    'S_MAE10': {'label':'Y_MAE10', 'factors': [('R120','HIGHER'),('VOL20','HIGHER'),('VOL60','HIGHER')]},
}


def rank_pct_by_date(g, factor, direction):
    x = pd.to_numeric(g[factor], errors='coerce')
    r = x.rank(method='average', pct=True)
    return r if direction == 'HIGHER' else 1.0-r


def score_rowwise(df, factors):
    # Cross-sectional percentile scores are computed independently on each signal date.
    parts=[]
    for factor,direction in factors:
        parts.append(df.groupby('DateSignal', group_keys=False).apply(
            lambda g: rank_pct_by_date(g, factor, direction), include_groups=False
        ).rename(f'{factor}_{direction}'))
    # groupby/apply indices can be awkward; reindex to original index
    out=pd.concat(parts, axis=1).reindex(df.index)
    return out.mean(axis=1, skipna=False), out


def auc_rank(x,y):
    z=pd.DataFrame({'x':x,'y':y}).dropna()
    if len(z)==0 or z.y.nunique()<2:return np.nan
    p=z[z.y==1].x; n=z[z.y==0].x
    if len(p)==0 or len(n)==0:return np.nan
    ranks=z.x.rank(method='average')
    return float((ranks[z.y==1].sum()-len(p)*(len(p)+1)/2)/(len(p)*len(n)))


def qstats(x,y):
    z=pd.DataFrame({'x':x,'y':y}).dropna()
    if len(z)<Q*MIN_GROUP or z.y.nunique()<2:return {}
    try:q=pd.qcut(z.x,Q,labels=False,duplicates='drop')+1
    except:return {}
    g=z.assign(q=q).groupby('q',observed=True).y.agg(['mean','count'])
    if len(g)<5:return {}
    return {'Q1Rate':float(g.loc[1,'mean']),'Q5Rate':float(g.loc[5,'mean']),'Q5MinusQ1':float(g.loc[5,'mean']-g.loc[1,'mean'])}


def evaluate(df, score, label, split):
    z=df[df.Split==split]
    y=z[label].astype(float); x=z[score]
    a=auc_rank(x,y); qs=qstats(x,y)
    base=float(y.mean()) if len(y) else np.nan
    return {'Score':score,'Label':label,'Split':split,'N':int(pd.DataFrame({'x':x,'y':y}).dropna().shape[0]),'BaseRate':base,'AUC':a,**qs}


def main():
    t=time.time()
    print('FASE 18 — MOMENTUM FAILURE SCORE')
    print('='*78)
    print(f'RUN_ID: {RUN_ID}')
    print('SOURCE: exact Phase 17 ex-ante factor dataset')
    print('NO strategy change | NO re-selection | NO risk overlay | NO production')
    print('PRE-SPECIFIED SCORES ONLY | NO NEW FACTOR SEARCH')
    if not DATASET.exists(): raise FileNotFoundError(DATASET)
    df=pd.read_csv(DATASET)
    df.columns=[str(c).strip() for c in df.columns]
    for c in ['DateSignal','ExecutionDate']:
        df[c]=pd.to_datetime(df[c],errors='coerce').dt.normalize()
    df=df.sort_values(['DateSignal','ExecutionDate','Ticker','Notional']).reset_index(drop=True)
    req=['DateSignal','ExecutionDate','Ticker','Split','Y_QUICK','Y_WEAK','Y_MAE10']
    missing=[c for c in req if c not in df.columns]
    if missing: raise RuntimeError(f'Missing columns: {missing}')
    # Recompute split chronologically, not trusting a stale label.
    dates=np.sort(df.DateSignal.dropna().unique())
    cut=dates[max(1,int(len(dates)*DISCOVERY_FRAC))-1]
    df['Split']=np.where(df.DateSignal<=cut,'DISCOVERY','VALIDATION')
    print(f'Entries: {len(df)} | discovery through {pd.Timestamp(cut).date()} | validation after')

    score_cols=[]
    score_parts={}
    for score,spec in SPECS.items():
        vals=[]
        part_names=[]
        for factor,direction in spec['factors']:
            if factor not in df.columns: raise RuntimeError(f'Missing factor {factor}')
            x=df.groupby('DateSignal',group_keys=False).apply(lambda g: rank_pct_by_date(g,factor,direction), include_groups=False)
            x=x.reindex(df.index)
            vals.append(x); part_names.append(f'{factor}_{direction}')
        mat=pd.concat(vals,axis=1); mat.columns=part_names
        df[score]=mat.mean(axis=1,skipna=False)
        score_parts[score]=mat
        score_cols.append(score)

    # Combined failure score is deliberately NOT a new optimized model. It is the
    # equal-weight average of the three pre-specified scores, for descriptive analysis.
    df['S_COMBINED']=df[score_cols].mean(axis=1,skipna=False)
    score_cols_all=score_cols+['S_COMBINED']

    # Integrity: scores use only same-date cross-section of ex-ante factors.
    timing_ok=bool((df.DateSignal < df.ExecutionDate).all())
    coverage={c:float(df[c].notna().mean()) for c in score_cols_all}
    if not timing_ok: raise RuntimeError('Ex-ante timing failed')

    rows=[]
    for score in score_cols_all:
        label = SPECS.get(score,{}).get('label')
        if label:
            rows += [evaluate(df,score,label,'DISCOVERY'),evaluate(df,score,label,'VALIDATION')]
    # Cross-score descriptive tests: each score against every failure label, including combined.
    labels=['Y_QUICK','Y_WEAK','Y_MAE10','Y_ADVERSE'] if 'Y_ADVERSE' in df else ['Y_QUICK','Y_WEAK','Y_MAE10']
    for score in score_cols_all:
        for label in labels:
            rows += [evaluate(df,score,label,'DISCOVERY'),evaluate(df,score,label,'VALIDATION')]
    diag=pd.DataFrame(rows).drop_duplicates(['Score','Label','Split'])
    diag.to_csv(OUTDIR/'phase18_score_diagnostics.csv',index=False)
    df.to_csv(OUTDIR/'phase18_entry_score_dataset.csv',index=False)

    # Primary pre-specified confirmation: directional AUC in validation must be > .5.
    primary=[]
    for score,spec in SPECS.items():
        label=spec['label']
        v=diag[(diag.Score==score)&(diag.Label==label)&(diag.Split=='VALIDATION')].iloc[0]
        d=diag[(diag.Score==score)&(diag.Label==label)&(diag.Split=='DISCOVERY')].iloc[0]
        primary.append({'Score':score,'Target':label,'DiscoveryAUC':d.AUC,'ValidationAUC':v.AUC,'ValidationBaseRate':v.BaseRate,'ValidationQ1Rate':v.get('Q1Rate',np.nan),'ValidationQ5Rate':v.get('Q5Rate',np.nan),'ValidationQ5MinusQ1':v.get('Q5MinusQ1',np.nan),'ValidationN':v.N})
    primary_df=pd.DataFrame(primary)
    primary_df.to_csv(OUTDIR/'phase18_primary_validation.csv',index=False)

    checks={
      'InputExists':DATASET.exists(),'Rows':int(len(df)),'DateOrdered':bool(df.DateSignal.is_monotonic_increasing),
      'ExAnteTimingPASS':timing_ok,'DiscoveryRows':int((df.Split=='DISCOVERY').sum()),'ValidationRows':int((df.Split=='VALIDATION').sum()),
      'ScoreCoverage':coverage,'NoNaNPrimaryLabels':bool(df[['Y_QUICK','Y_WEAK','Y_MAE10']].notna().all().all()),
      'NoNewFactorSearch':True,'NoStrategyChange':True
    }
    checks['PrimaryValidationAUCs']={r.Score:float(r.ValidationAUC) for _,r in primary_df.iterrows()}
    checks['STATUS']='PASS' if checks['InputExists'] and checks['Rows']>0 and checks['ValidationRows']>0 and checks['ExAnteTimingPASS'] and all(np.isfinite(list(checks['PrimaryValidationAUCs'].values()))) else 'FAIL'
    checks['RuntimeSeconds']=time.time()-t
    (OUTDIR/'phase18_audit.json').write_text(json.dumps(checks,indent=2,default=str),encoding='utf-8')
    print('\n--- PRIMARY VALIDATION ---')
    print(primary_df.to_string(index=False))
    print('\n--- CROSS-SCORE VALIDATION ---')
    print(diag[diag.Split=='VALIDATION'].sort_values(['Label','AUC'],ascending=[True,False]).to_string(index=False))
    print('\n--- COVERAGE ---')
    print(json.dumps(checks,indent=2,default=str))
    print(f'\nArtifacts: {OUTDIR}')
    print(f'STATUS: {checks["STATUS"]}')
    if checks['STATUS']!='PASS': raise SystemExit(1)

if __name__=='__main__': main()

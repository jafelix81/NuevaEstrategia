#!/usr/bin/env python3
"""Global Holm correction for recorded Form 144/Form 4 linkage placebos."""
from __future__ import annotations
import argparse, hashlib, json, math
from pathlib import Path

F144 = "7a54ee09e8d4520e1ec14cf22f2c0d1c62d077798b14d3db596826e3360a3659"
F4 = "a4e6a681cfcfa43a3d9e4ca9cfec1fd26a59d0a01eac7e9f7b5a0122092c90f3"
SAMPLE = {"eligible_notices":1451,"eligible_tranches":1460,"form4_sale_blocks":10525,"exact_date_share_links":521,"fallback_links":49}
SPECS = {
 256: {"json":"6b535194458ac29ea50ea9969480174d5256d66e355d806ee6551d988c299cac","zip":"f7fe3191ce54c22d2c35014aba7b65cc78457569fb27b0433ea5bbb77b7b9765","run":42767357624,"artifact":13739833787,"name":"phase256-form144-form4-lag-preserving-placebo-audit","path":("permutation_audit","placebos"),"names":{"owner_identity_within_issuer","filing_lag_within_issuer_owner","shares_within_issuer_owner","filing_lag_and_shares_within_issuer_owner"}},
 257: {"json":"968cee6bbd2ef8bb59af716252ce95c945c594987eb5ed648aa9f130ba3762ec","zip":"b2ec9653ab66da858bf3e7f42376176a67011413de4d543d8ff93fd74dba7c2f","run":42775383915,"artifact":13743028950,"name":"phase257-form144-form4-temporal-stratified-placebo-audit","path":("placebos",),"names":{"issuer_owner","issuer_owner_month","issuer_owner_iso_week"}},
 258: {"json":"99b265528819523ae078d1294d08099dd66a67b977a84d704b186957a0d41c87","zip":"e5f51d3d123f653275934f2cdfcc6e9fc491eeb09391a11dfa4533be3877602f","run":42787526319,"artifact":13749584173,"name":"phase258-form144-form4-accession-cluster-placebo","path":("placebos",),"names":{"issuer_owner_cik","issuer_owner_cik_month","issuer_owner_cik_iso_week"}},
 260: {"json":"22b646e0afb09a8e56929bde5a606b4efd4cfd0b9022f0cddc93db37e5f488a9","zip":"0962fa7dd62ecaba0992f0c2537b11ac79147e2466ddb23d5915909ee4daf565","run":42790753569,"artifact":13750319077,"name":"phase260-form144-form4-xnys-session-placebo","path":("placebos",),"names":{"issuer_owner_cik_weekday","issuer_owner_cik_month_weekday","issuer_owner_cik_iso_week_weekday"}},
}

def holm_adjust(pvals):
    if not pvals: raise ValueError("empty family")
    if any(not math.isfinite(p) or p < 0 or p > 1 for p in pvals.values()): raise ValueError("invalid p-value")
    ordered=sorted(pvals.items(),key=lambda x:(x[1],x[0])); out={}; running=0.0; m=len(ordered)
    for i,(key,p) in enumerate(ordered):
        running=max(running,min(1.0,(m-i)*p)); out[key]=running
    return out

def _sample(data, phase):
    s=data["sample"]
    keys=("eligible_notices","eligible_tranches","form4_unique_owner_sale_blocks","exact_date_share_links","fallback_links")
    if phase==260: keys=("eligible_original_notices","eligible_proposed_sale_tranches","form4_sale_blocks","exact_date_share_links","fallback_links_separate")
    vals=dict(zip(SAMPLE.keys(),(int(s[k]) for k in keys)))
    if vals != SAMPLE: raise ValueError(f"Phase {phase}: sample drift {vals}")

def _hashes(data, phase):
    x=data["inputs"]; k="form144_csv_sha256" if phase==256 else "form144_sha256"
    if x.get(k)!=F144 or x.get("form4_inner_zip_sha256")!=F4: raise ValueError(f"Phase {phase}: source hash mismatch")

def extract_tests(data, phase):
    if data.get("phase")!=phase: raise ValueError("phase mismatch")
    dec=data.get("decision",{})
    if dec.get("alpha_test_authorized") is not False or dec.get("holdout_used") is not False or dec.get("f80_frozen") is not True: raise ValueError("no-alpha/F80 control failed")
    _hashes(data,phase); _sample(data,phase)
    obj=data
    for key in SPECS[phase]["path"]: obj=obj[key]
    if set(obj)!=SPECS[phase]["names"]: raise ValueError(f"Phase {phase}: placebo family drift")
    out=[]
    for name,r in sorted(obj.items()):
        if r.get("status","COMPLETED")!="COMPLETED": raise ValueError("incomplete stratum in family")
        n=int(r["replicates"]); e=int(r["null_replicates_at_or_above_observed"]); p=float(r["empirical_tail_plus_one"])
        if n!=1000 or not 0<=e<=n or not math.isclose(p,(e+1)/(n+1),rel_tol=0,abs_tol=1e-12): raise ValueError("invalid Monte Carlo tail")
        out.append({"phase":phase,"stratum":name,"test_id":f"phase{phase}:{name}","observed":int(r["observed_mutable_exact_links"]),"null_mean":float(r["null_mean"]),"null_max":int(r["null_max"]),"exceedances":e,"replicates":n,"raw_p":p,"within_phase_holm_p":r.get("holm_adjusted_tail")})
    return out

def audit(paths):
    tests=[]; manifest=[]
    if set(paths)!=set(SPECS): raise ValueError("all four immutable phase artifacts are required")
    for phase in sorted(SPECS):
        raw=Path(paths[phase]).read_bytes(); digest=hashlib.sha256(raw).hexdigest(); spec=SPECS[phase]
        if digest!=spec["json"]: raise ValueError(f"Phase {phase}: result JSON SHA-256 mismatch")
        data=json.loads(raw.decode("utf-8")); tests.extend(extract_tests(data,phase))
        manifest.append({"phase":phase,"run_id":spec["run"],"artifact_id":spec["artifact"],"artifact_name":spec["name"],"artifact_zip_sha256":spec["zip"],"result_json_sha256":digest})
    if len(tests)!=13: raise ValueError("expected 13 tests")
    adj=holm_adjust({x["test_id"]:x["raw_p"] for x in tests})
    for x in tests: x["global_holm_p"]=adj[x["test_id"]]; x["significant_05"]=adj[x["test_id"]]<0.05
    tests.sort(key=lambda x:(x["phase"],x["stratum"]))
    return {"phase":261,"status":"GLOBAL_MULTIPLICITY_AUDIT_COMPLETED_EXPLORATORY_LINKAGE_ONLY","family":{"size":13,"phases":{"256":4,"257":3,"258":3,"260":3},"method":"Holm step-down FWER correction","caveat":"Post-hoc family of nested sensitivities on one selected one-quarter sample; dependence is allowed by Holm, but sample selection and exchangeability assumptions remain."},"inputs":{"form144_sha256":F144,"form4_sha256":F4,"sample":SAMPLE,"form4_snapshot_end":"2026-09-30","artifacts":manifest},"monte_carlo":{"replicates_per_test":1000,"plus_one":"(exceedances+1)/(replicates+1)","zero_exceedance_one_sided_95pct_upper":1-0.05**(1/1000)},"summary":{"tests":13,"zero_exceedance_tests":sum(x["exceedances"]==0 for x in tests),"global_holm_significant_05":sum(x["significant_05"] for x in tests),"minimum_global_holm_p":min(adj.values()),"maximum_global_holm_p":max(adj.values()),"phase260_iso_week_global_holm_p":adj["phase260:issuer_owner_cik_iso_week_weekday"]},"tests":tests,"decision":{"document_linkage_only":True,"independent_replication":False,"causal_evidence":False,"informed_trading_evidence":False,"strict_pit_admitted":False,"feature_admitted":False,"alpha_test_authorized":False,"return_test_run":False,"bootstrap_loo_oos_run":False,"holdout_used":False,"legacy_holdout":"CONSUMED_NOT_PRISTINE","f80_frozen":True,"production_changed":False,"universe_changed":False,"capital_changed":False}}

def main():
    p=argparse.ArgumentParser(); p.add_argument("--phase256",required=True); p.add_argument("--phase257",required=True); p.add_argument("--phase258",required=True); p.add_argument("--phase260",required=True); p.add_argument("--output",required=True); a=p.parse_args()
    result=audit({256:a.phase256,257:a.phase257,258:a.phase258,260:a.phase260}); out=Path(a.output); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8"); print(json.dumps(result,indent=2,sort_keys=True))

if __name__=="__main__": main()

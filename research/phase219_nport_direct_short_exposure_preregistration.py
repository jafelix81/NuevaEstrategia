#!/usr/bin/env python3
"""Phase 219 preregistration integrity validator; no network or return calculations."""
from __future__ import annotations
import argparse, json
from pathlib import Path

EVIDENCE = Path(__file__).with_name("phase219_nport_direct_short_exposure_preregistration.json")

def build_audit(e: dict) -> dict:
    if e.get("phase") != 219:
        raise ValueError("unexpected_phase")
    prior = e["prior_phase_adjudication"]
    if "LONG" not in prior["phase27n_filter"] or "negative CURRENCY_VALUE excluded" not in prior["phase27n_filter"]:
        raise ValueError("prior_long_only_scope_not_proven")
    if prior["phase27o_disposition"] != "KILLED; top-minus-bottom sign unstable; no rescue permitted":
        raise ValueError("phase27o_kill_disposition_changed")
    if prior["short_side_tested_before"]:
        raise ValueError("short_side_not_distinct")
    h = e["hypothesis"]
    if h["primary_feature"] != "delta_short_pct_nav" or h["sign_is_fixed"] is not True:
        raise ValueError("primary_hypothesis_changed")
    if "lower subsequent residual equity returns" not in h["direction"]:
        raise ValueError("direction_not_preregistered")
    if h["absent_row_interpretation"] != "unknown; never impute zero before complete-holdings and omission semantics pass":
        raise ValueError("missing_row_zero_imputation")
    row = e["row_filter"]
    required = {
        "payoff_profile":"Short", "asset_cat":"EC", "issuer_cat":"CORP",
        "inv_country":"US", "unit":"NS", "title":"Common Stock where present and consistent"
    }
    if any(row.get(k) != v for k,v in required.items()):
        raise ValueError("row_filter_changed")
    if row["fuzzy_ticker_fallback"] is not False:
        raise ValueError("fuzzy_identity_fallback")
    if e["knowledge_time"]["use_report_date_as_knowledge_time"] is not False or e["knowledge_time"]["fixed_report_lag"] is not False:
        raise ValueError("lookahead_knowledge_rule")
    if e["knowledge_time"]["trading_boundary"] != "first full regular U.S. equity session whose open is strictly after SEC acceptance":
        raise ValueError("trading_boundary_changed")
    g = e["admission_gates"]
    if g["alpha_test_authorized"] is not False:
        raise ValueError("premature_alpha_authorization")
    if g["five_accession_raw_hashes"] != "NOT_VERIFIED" or g["broad_pit_universe_coverage"] != "NOT_ESTIMATED":
        raise ValueError("unverified_gate_promoted")
    c = e["controls"]
    required_false = ("return_test_run","alpha_test_run","bootstrap_loo_run","holdout_used",
                      "production_changed","universe_changed","data_purchase","vendor_contact",
                      "sec_requests_sent","placeholder_contact_email_used")
    if any(c[k] is not False for k in required_false):
        raise ValueError("control_violation")
    if c["f80_frozen"] is not True or e["test_protocol"]["legacy_holdout"] != "CONSUMED_NOT_PRISTINE":
        raise ValueError("frozen_control_or_holdout_changed")
    return {
        "phase":219,
        "status":e["status"],
        "distinct_from_phase27n_27o_long_signal":True,
        "fixed_direction":h["direction"],
        "raw_five_accession_files_verified":False,
        "broad_pit_universe_coverage_estimated":False,
        "alpha_test_authorized":False,
        "holdout_used":False,
        "f80_frozen":True,
        "decision":"PREREGISTERED_ONLY_WAIT_FOR_RAW_PIT_AND_UNIVERSE_GATES"
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--evidence",type=Path,default=EVIDENCE)
    p.add_argument("--output",type=Path)
    a=p.parse_args()
    result=build_audit(json.loads(a.evidence.read_text(encoding="utf-8")))
    payload=json.dumps(result,indent=2,sort_keys=True)
    if a.output:
        a.output.parent.mkdir(parents=True,exist_ok=True)
        a.output.write_text(payload+"\n",encoding="utf-8")
    print(payload)

if __name__=="__main__":
    main()

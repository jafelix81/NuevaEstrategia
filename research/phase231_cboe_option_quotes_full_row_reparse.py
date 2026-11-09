#!/usr/bin/env python3
"""Phase 231: rerun the full Cboe Option Quotes row gate with unique-only dates.

Uses the hash-pinned Phase 174 source parser and Phase 175 all-row date diagnostic
from the base research branch. Raw rows/contract keys remain in memory only.
"""
from __future__ import annotations
import argparse, hashlib, json, re
from datetime import date, datetime
from pathlib import Path
from research import phase174_cboe_option_quotes_sample_audit as p174
from research import phase175_cboe_option_quotes_date_locale_audit as p175

EXPECTED_ARCHIVE_SHA256 = "7645a6cc94f1a984e98264a4b494f748e373c30ecde85de25ceadb83a5c56782"
EXP_FORMATS = (("%Y-%m-%d","iso_extended"),("%Y%m%d","iso_basic"),
               ("%m/%d/%Y","us_slash"),("%d/%m/%Y","dmy_slash"),
               ("%Y/%m/%d","year_slash"),("%m-%d-%Y","us_dash"))
QDT_FORMATS = (("%Y-%m-%d %H:%M","iso_minute"),("%Y-%m-%d %H:%M:%S","iso_second"),
               ("%Y-%m-%d %H:%M:%S.%f","iso_fraction"),("%m/%d/%Y %H:%M","us_slash_minute"),
               ("%m/%d/%Y %H:%M:%S","us_slash_second"),("%m/%d/%Y %H:%M:%S.%f","us_slash_fraction"),
               ("%d/%m/%Y %H:%M","dmy_slash_minute"),("%d/%m/%Y %H:%M:%S","dmy_slash_second"),
               ("%d/%m/%Y %H:%M:%S.%f","dmy_slash_fraction"))

def _candidates(raw, formats):
    found={}
    for fmt,label in formats:
        try: found[label]=datetime.strptime(str(raw).strip(),fmt)
        except (TypeError,ValueError): pass
    return found

def parse_unique_expiration(raw):
    raw=str(raw or "").strip()
    if not raw: raise ValueError("missing_expiration")
    found=_candidates(raw,EXP_FORMATS); distinct={x.date() for x in found.values()}
    if not found: raise ValueError("invalid_expiration_format")
    if len(distinct)>1: raise ValueError("ambiguous_expiration_format")
    return next(iter(distinct))

def parse_unique_quote_datetime(raw):
    raw=str(raw or "").strip()
    if not raw: raise ValueError("missing_quote_datetime")
    if raw.endswith("Z") or re.search(r"[+-]\d{2}:?\d{2}$",raw):
        raise ValueError("unexpected_timezone_in_et_wall_clock")
    found=_candidates(raw,QDT_FORMATS); distinct=set(found.values())
    if not found: raise ValueError("invalid_quote_datetime_format")
    if len(distinct)>1: raise ValueError("ambiguous_quote_datetime_format")
    return next(iter(distinct))

def audit_archive(payload: bytes) -> dict:
    if hashlib.sha256(payload).hexdigest()!=EXPECTED_ARCHIVE_SHA256:
        raise ValueError("phase174_archive_hash_mismatch")
    original_exp=p174.parse_expiration
    original_qdt=p174.parse_quote_datetime
    original_csv=p174.audit_csv_bytes
    current={}
    member_stats=[]
    def exp_wrapper(raw):
        try: return parse_unique_expiration(raw)
        except ValueError as exc:
            if str(exc)=="ambiguous_expiration_format": current["ambiguous_expiration"]+=1
            raise
    def qdt_wrapper(raw):
        try: return parse_unique_quote_datetime(raw)
        except ValueError as exc:
            if str(exc)=="ambiguous_quote_datetime_format": current["ambiguous_quote_datetime"]+=1
            raise
    def csv_wrapper(data,member_index=0):
        current.clear(); current.update(ambiguous_expiration=0,ambiguous_quote_datetime=0)
        # Independently diagnose every date field, including rows skipped by
        # Phase 174's contract-first validation order.
        diag=p175.diagnose_csv_bytes(data)
        result=original_csv(data,member_index)
        ae=current["ambiguous_expiration"]
        aq=current["ambiguous_quote_datetime"]
        diag_exp=diag.get("expiration_interpretation_counts",{})
        diag_qdt=diag.get("quote_datetime_interpretation_counts",{})
        exp_diag_amb=int(diag_exp.get("ambiguous_multiple_interpretations",0))
        qdt_diag_bad=(int(diag_qdt.get("ambiguous_multiple_interpretations",0))
                      +int(diag_qdt.get("no_parse",0))+int(diag_qdt.get("missing",0)))
        counts_reconcile=(ae==exp_diag_amb and qdt_diag_bad==0)
        invalid_contract=int(result.get("invalid_contract_rows",0))
        invalid_timestamp=int(result.get("invalid_timestamp_rows",0))
        nonq_contract=max(0,invalid_contract-ae)
        nonq_timestamp=max(0,invalid_timestamp-aq)
        oi_present=bool(result.get("open_interest_present"))
        oi_bad=int(result.get("contract_days_with_inconsistent_sod_oi",0))
        unambiguous_valid_rows=max(0,int(result.get("populated_rows",0))
            -int(result.get("short_rows",0))-int(result.get("long_rows",0))
            -invalid_contract-invalid_timestamp-int(result.get("numeric_error_rows",0))
            -int(result.get("duplicate_contract_interval_keys",0)))
        clean_subset=(
            unambiguous_valid_rows>0
            and result.get("short_rows",0)==0 and result.get("long_rows",0)==0
            and nonq_contract==0 and nonq_timestamp==0
            and result.get("numeric_error_rows",0)==0
            and result.get("duplicate_contract_interval_keys",0)==0
            and (not oi_present or oi_bad==0)
            and int(diag.get("expiry_before_quote_date_rows",0))==0
            and counts_reconcile
        )
        result.update({
            "ambiguous_expiration_rows":ae,
            "ambiguous_quote_datetime_rows":aq,
            "quarantined_ambiguous_date_rows":ae+aq,
            "phase175_all_row_expiration_interpretations":diag_exp,
            "phase175_all_row_quote_datetime_interpretations":diag_qdt,
            "date_counter_reconciliation_pass":counts_reconcile,
            "nonquarantined_invalid_contract_rows":nonq_contract,
            "nonquarantined_invalid_timestamp_rows":nonq_timestamp,
            "unambiguous_valid_rows":unambiguous_valid_rows,
            "unambiguous_subset_gate_pass":clean_subset,
            "sod_oi_semantic_gate_pass":(not oi_present or oi_bad==0),
            "raw_rows_persisted":False,"raw_symbols_persisted":False,
            "contract_keys_persisted":False
        })
        member_stats.append({
            "member_index":member_index,
            "populated_rows":result.get("populated_rows",0),
            "unambiguous_valid_rows":unambiguous_valid_rows,
            "ambiguous_expiration_rows":ae,
            "ambiguous_quote_datetime_rows":aq,
            "unambiguous_subset_gate_pass":clean_subset,
            "row_gate_pass":result.get("row_gate_pass",False),
            "schema_gate_pass":result.get("schema_gate_pass",False)
        })
        return result
    p174.parse_expiration=exp_wrapper
    p174.parse_quote_datetime=qdt_wrapper
    p174.audit_csv_bytes=csv_wrapper
    try:
        result=p174.audit_archive(payload)
    finally:
        p174.parse_expiration=original_exp
        p174.parse_quote_datetime=original_qdt
        p174.audit_csv_bytes=original_csv
    members=result.get("members",[])
    clean=bool(members) and all(x.get("unambiguous_subset_gate_pass",False) for x in members)
    result["phase"]=231
    result["phase174_source_archive_sha256"]=EXPECTED_ARCHIVE_SHA256
    result["full_row_reparse_completed"]=bool(members) and len(members)==5
    result["clean_unambiguous_subset_gate_pass"]=clean
    result["total_ambiguous_expiration_rows"]=sum(x.get("ambiguous_expiration_rows",0) for x in members)
    result["total_ambiguous_quote_datetime_rows"]=sum(x.get("ambiguous_quote_datetime_rows",0) for x in members)
    result["total_quarantined_ambiguous_date_rows"]=sum(x.get("quarantined_ambiguous_date_rows",0) for x in members)
    result["total_unambiguous_valid_rows"]=sum(x.get("unambiguous_valid_rows",0) for x in members)
    result["all_member_date_counter_reconciliation_pass"]=bool(members) and all(
        x.get("date_counter_reconciliation_pass",False) for x in members)
    result["sample_schema_gate_pass"]=bool(result.get("sample_schema_gate_pass"))
    result["sample_admission"]=False
    result["pit_admission"]=False
    result["alpha_admission"]=False
    result["forward_returns_tested"]=False
    result["bootstrap_loo_tested"]=False
    result["chronological_oos_tested"]=False
    result["final_holdout_used"]=False
    result["production_changed"]=False
    result["f80_changed"]=False
    result["f80_status"]="FROZEN"
    result["legacy_holdout_status"]="CONSUMED_NOT_PRISTINE"
    result["raw_rows_persisted"]=False
    result["raw_symbols_persisted"]=False
    result["contract_keys_persisted"]=False
    result["phase231_member_summary"]=member_stats
    if result["sample_schema_gate_pass"]:
        result["overall_status"]="FULL_SAMPLE_ROW_SCHEMA_PASS_PIT_BLOCKED"
    elif clean:
        result["overall_status"]="CLEAN_UNAMBIGUOUS_SUBSET_PASS_WITH_AMBIGUOUS_ROWS_QUARANTINED"
    else:
        result["overall_status"]="FULL_ROW_REPARSE_COMPLETE_GATE_FAIL"
    return result

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",default="phase231_output/phase231_cboe_option_quotes_full_row_reparse.json")
    args=ap.parse_args()
    try:
        payload=p174.download_sample()
        result=audit_archive(payload)
        result["download_status"]="PASS"
    except Exception as exc:
        result={"phase":231,"download_status":"BLOCKED","download_error_class":type(exc).__name__,
                "download_error_code":str(exc).split(":")[0][:100],
                "sample_schema_gate_pass":False,"clean_unambiguous_subset_gate_pass":False,
                "pit_admission":False,"alpha_admission":False,"final_holdout_used":False,
                "production_changed":False,"f80_changed":False,"overall_status":"DIAGNOSTIC_INCOMPLETE"}
    out=Path(args.output); out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2,sort_keys=True),flush=True)
    return 0 if result.get("download_status")=="PASS" else 1

if __name__=="__main__": raise SystemExit(main())

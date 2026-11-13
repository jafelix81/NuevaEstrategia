#!/usr/bin/env python3
"""Phase 378: audit CFTC TFF Russell contract eras and historical classification regimes.

Read-only source feasibility. No raw rows, IDs, positions or trader identifiers
are retained. No feature, forward return, alpha or holdout calculation occurs.
"""
from __future__ import annotations
import argparse, json, time
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
import requests

DATASET_ID = "gpe5-46if"
RESOURCE_URL = f"https://publicreporting.cftc.gov/resource/{DATASET_ID}.json"
META_URL = f"https://publicreporting.cftc.gov/api/views/{DATASET_ID}.json"
RUSSELL_CODES = ("239742", "239741", "23977A")
FIELDS = ("report_date_as_yyyy_mm_dd","cftc_contract_market_code","market_and_exchange_names","contract_market_name","cftc_market_code","open_interest_all")
TFF_PUBLIC_LAUNCH_DATE = date(2010, 7, 22)
MAX_ROWS = 5000
SERIES_BREAK_DAYS = 365

def norm(value):
    return str(value or "").strip().upper()

def parse_date(value):
    if value is None or str(value).strip() == "":
        raise ValueError("missing report date")
    return date.fromisoformat(str(value).strip()[:10])

def parse_int(value):
    if value is None or str(value).strip() in ("", ".", "NULL", "null"):
        return None
    try:
        return int(Decimal(str(value).replace(",", "").strip()))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"invalid integer-like value: {value!r}") from exc

def split_episodes(rows, break_days=SERIES_BREAK_DAYS):
    ordered = sorted(rows, key=lambda r: parse_date(r["report_date_as_yyyy_mm_dd"]))
    if not ordered:
        return []
    episodes, breaks, current = [], [], [ordered[0]]
    for row in ordered[1:]:
        previous_date = parse_date(current[-1]["report_date_as_yyyy_mm_dd"])
        current_date = parse_date(row["report_date_as_yyyy_mm_dd"])
        gap = (current_date - previous_date).days
        if gap > break_days:
            episodes.append(current)
            breaks.append({"previous_report_date":previous_date.isoformat(),"next_report_date":current_date.isoformat(),"gap_days":gap})
            current = [row]
        else:
            current.append(row)
    episodes.append(current)
    return list(zip(episodes, breaks + [None]))

def weekly_interval_summary(rows):
    dates = sorted({parse_date(r["report_date_as_yyyy_mm_dd"]) for r in rows})
    gaps = [(b-a).days for a,b in zip(dates,dates[1:])]
    unexplained = [g for g in gaps if g > 8]
    inferred_missing = sum(max(0, round(g/7)-1) for g in unexplained)
    intervals = max(0,len(dates)-1)
    denominator = intervals + inferred_missing
    return {
        "observed_report_dates":len(dates),
        "non_tuesday_report_dates":sum(d.weekday()!=1 for d in dates),
        "max_inter_report_gap_days":max(gaps) if gaps else 0,
        "intervals_over_8_days":len(unexplained),
        "inferred_missing_week_count_within_episode":inferred_missing,
        "weekly_interval_coverage_pct":round(100*intervals/denominator,6) if denominator else None,
        "missing_weeks_are_not_zero_or_forward_filled":True,
    }

def episode_summary(code,index,rows,break_after):
    dates=sorted(parse_date(r["report_date_as_yyyy_mm_dd"]) for r in rows)
    oi=[parse_int(r.get("open_interest_all")) for r in rows]
    oi=[x for x in oi if x is not None]
    names=sorted({str(r.get("contract_market_name") or "").strip() for r in rows})
    market_names=sorted({str(r.get("market_and_exchange_names") or "").strip() for r in rows})
    exchanges=sorted({norm(r.get("cftc_market_code")) for r in rows if norm(r.get("cftc_market_code"))})
    pre_launch=sum(d<TFF_PUBLIC_LAUNCH_DATE for d in dates)
    return {
        "series_code":code,"episode_number":index,"row_count":len(rows),
        "first_report_date":dates[0].isoformat(),"last_report_date":dates[-1].isoformat(),
        "contract_name_variants":names,"market_exchange_name_variants":market_names,
        "exchange_code_variants":exchanges,"open_interest_rows":len(oi),
        "median_open_interest_contracts":str(Decimal(sorted(oi)[len(oi)//2])) if oi else None,
        "weekly_intervals":weekly_interval_summary(rows),
        "pre_tff_public_launch_backcast_rows":pre_launch,
        "post_tff_public_launch_rows":len(dates)-pre_launch,"break_after":break_after,
    }

def build_summary(rows,count_before,count_after,metadata_updated_before,metadata_updated_after):
    grouped=defaultdict(list); natural_keys=Counter(); invalid_dates=0
    for row in rows:
        code=norm(row.get("cftc_contract_market_code"))
        if code not in RUSSELL_CODES: continue
        try: report_date=parse_date(row.get("report_date_as_yyyy_mm_dd"))
        except ValueError:
            invalid_dates+=1; continue
        natural_keys[(report_date.isoformat(),code)]+=1
        grouped[code].append(row)
    duplicate_groups=sum(1 for n in natural_keys.values() if n>1)
    code_summaries={}; all_episodes=[]
    for code in RUSSELL_CODES:
        episodes=split_episodes(grouped.get(code,[]))
        summaries=[episode_summary(code,i+1,episode_rows,break_after) for i,(episode_rows,break_after) in enumerate(episodes)]
        code_summaries[code]={"row_count":len(grouped.get(code,[])),"episode_count":len(summaries),"episodes":summaries}
        all_episodes.extend(summaries)
    code_239742=code_summaries["239742"]
    long_breaks=[ep["break_after"] for ep in code_239742["episodes"] if ep["break_after"]]
    era_split_gate=len(code_239742["episodes"])>=2 and any(x["gap_days"]>SERIES_BREAK_DAYS for x in long_breaks)
    snapshot_stable=(count_before==len(rows)==count_after and metadata_updated_before is not None and metadata_updated_before==metadata_updated_after)
    all_codes_present=all(code_summaries[c]["row_count"]>0 for c in RUSSELL_CODES)
    return {
        "phase":378,"source":"CFTC TFF Futures Only Socrata dataset","dataset_id":DATASET_ID,
        "audit_timestamp_utc":datetime.now(timezone.utc).isoformat(),
        "selected_codes":list(RUSSELL_CODES),"selected_fields":list(FIELDS),
        "reported_count_before":count_before,"retrieved_row_count":len(rows),"reported_count_after":count_after,
        "row_count_reconciled":count_before==len(rows)==count_after,
        "metadata_rows_updated_before":metadata_updated_before,"metadata_rows_updated_after":metadata_updated_after,
        "snapshot_stable_during_retrieval":snapshot_stable,"invalid_report_dates":invalid_dates,
        "natural_key":"(report_date_as_yyyy_mm_dd, cftc_contract_market_code)",
        "duplicate_natural_key_groups":duplicate_groups,"all_russell_codes_present_gate":all_codes_present,
        "series_by_code":code_summaries,"episodes":all_episodes,
        "russell_239742_contract_era_split_gate":era_split_gate,
        "tff_public_launch_date":TFF_PUBLIC_LAUNCH_DATE.isoformat(),
        "pre_launch_classification_status":"BACKCAST_USING_RECENT_CLASSIFICATIONS_PER_CFTC_EXPLANATORY_NOTES",
        "pre_launch_rows_eligible_for_primary_tff_feature":False,
        "strict_historical_pit_status":"NOT_ESTABLISHED_BEYOND_CFTC_VERIFIED_RELEASE_DATE_WINDOW",
        "interpretation":"TFF categories are aggregate functional classifications, not beneficial-owner identities or verified informed-trader labels.",
        "separate_contracts_must_not_be_spliced":True,"missing_weeks_are_not_zero_or_forward_filled":True,
        "raw_rows_retained":False,"raw_ids_retained":False,"forward_returns_used":False,
        "alpha_test_authorized":False,"holdout_used":False,"f80_changed":False,"production_changed":False,
        "research_disposition":"RUSSELL_CONTRACT_ERA_SPLIT_CONFIRMED_REVIEW_PIT_AND_CLASSIFICATION_REGIME"
        if snapshot_stable and invalid_dates==0 and duplicate_groups==0 and all_codes_present and era_split_gate
        else "RUSSELL_CONTRACT_ERA_AUDIT_INCOMPLETE",
    }

def request_json(session,url,params=None):
    last_error=None
    for attempt in range(4):
        try:
            response=session.get(url,params=params,timeout=90)
            if response.status_code in (429,500,502,503,504):
                raise requests.HTTPError(f"transient HTTP {response.status_code}")
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            last_error=exc
            if attempt==3: break
            time.sleep(2**attempt)
    raise RuntimeError(f"CFTC request failed: {type(last_error).__name__}: {last_error}")

def fetch_audit_data(session):
    where="cftc_contract_market_code in ('239742','239741','23977A')"
    metadata_before=request_json(session,META_URL)
    count_before_rows=request_json(session,RESOURCE_URL,{"$select":"count(*) as n","$where":where})
    count_before=int(count_before_rows[0]["n"])
    params={"$select":",".join(FIELDS),"$where":where,"$order":"report_date_as_yyyy_mm_dd ASC","$limit":MAX_ROWS}
    rows=request_json(session,RESOURCE_URL,params)
    count_after_rows=request_json(session,RESOURCE_URL,{"$select":"count(*) as n","$where":where})
    count_after=int(count_after_rows[0]["n"])
    metadata_after=request_json(session,META_URL)
    return build_summary(rows,count_before,count_after,metadata_before.get("rowsUpdatedAt"),metadata_after.get("rowsUpdatedAt"))

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",default="phase378_cftc_russell_contract_era_audit")
    args=parser.parse_args()
    output=Path(args.output); output.mkdir(parents=True,exist_ok=True)
    session=requests.Session(); session.headers.update({"User-Agent":"NuevaEstrategia-Phase378/1.0 research"})
    summary=fetch_audit_data(session)
    (output/"summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True),encoding="utf-8")
    print("PHASE378_CFTC_RUSSELL_ERA_AUDIT=",summary["research_disposition"])
    print("ROWS=",summary["retrieved_row_count"])
    print("DUPLICATE_KEYS=",summary["duplicate_natural_key_groups"])
    print("239742_EPISODES=",summary["series_by_code"]["239742"]["episode_count"])
    print("STRICT_PIT=",summary["strict_historical_pit_status"])
    print("ALPHA_TEST=NOT_AUTHORIZED")
    if summary["research_disposition"]!="RUSSELL_CONTRACT_ERA_SPLIT_CONFIRMED_REVIEW_PIT_AND_CLASSIFICATION_REGIME":
        raise SystemExit("Phase 378 contract-era/source gate failed")

if __name__=="__main__":
    main()

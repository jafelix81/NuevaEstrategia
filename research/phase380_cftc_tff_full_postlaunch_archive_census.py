#!/usr/bin/env python3
"""Phase 380: full post-launch CFTC TFF archive Updated-date census.

Fetches the distinct TFF report dates from the public CFTC dataset, then checks
the corresponding static Futures Only archive page. Only report/update dates,
URLs, status and aggregate coverage are retained. No positions or raw HTML.
"""
from __future__ import annotations
import argparse, json, re, threading, time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timezone
from pathlib import Path
import requests

DATASET_ID="gpe5-46if"
RESOURCE_URL=f"https://publicreporting.cftc.gov/resource/{DATASET_ID}.json"
META_URL=f"https://publicreporting.cftc.gov/api/views/{DATASET_ID}.json"
ARCHIVE_BASE="https://www.cftc.gov/sites/default/files/files/dea/cotarchives"
FIRST_TFF_REPORT_DATE=date(2010,7,20)
MAX_DATE_ROWS=2000
MAX_WORKERS=4
THREAD_LOCAL=threading.local()
DATE_RE=r"([A-Z][a-z]+\s+\d{1,2},\s+\d{4})"
OFFICIAL_SCHEDULE_SAMPLES={
 "2025-09-30":"2025-11-19","2025-10-07":"2025-11-21","2025-10-14":"2025-11-25",
 "2025-10-21":"2025-12-02","2025-10-28":"2025-12-05","2025-11-04":"2025-12-09",
 "2025-11-10":"2025-12-10","2025-11-18":"2025-12-12","2025-11-25":"2025-12-15",
 "2025-12-02":"2025-12-17","2025-12-09":"2025-12-19","2025-12-16":"2025-12-23",
 "2025-12-23":"2025-12-29",
 "2026-08-25":"2026-08-28","2026-09-01":"2026-09-04","2026-09-08":"2026-09-11",
 "2026-09-15":"2026-09-18","2026-09-22":"2026-09-25","2026-09-29":"2026-10-02",
 "2026-10-06":"2026-10-09","2026-10-13":"2026-10-16","2026-10-20":"2026-10-23",
 "2026-10-27":"2026-10-30",
}

def parse_month_date(value):
    return datetime.strptime(value,"%B %d, %Y").date()

def parse_report_date(value):
    return date.fromisoformat(str(value).strip()[:10])

def report_filename(report_date):
    d=date.fromisoformat(report_date)
    return f"financial_lf{d:%m%d%y}.htm"

def parse_archive_dates(html):
    report_match=re.search(r"Positions\s+as\s+of\s+"+DATE_RE,html,re.I)
    updated_matches=re.findall(r"Updated\s+"+DATE_RE,html,re.I)
    if not report_match:
        raise ValueError("report-date heading not found")
    if not updated_matches:
        raise ValueError("archive Updated date not found")
    return parse_month_date(report_match.group(1)),parse_month_date(updated_matches[-1])

def get_session():
    if not hasattr(THREAD_LOCAL,"session"):
        s=requests.Session()
        s.headers.update({"User-Agent":"NuevaEstrategia-Phase380/1.0 CFTC archive availability census"})
        THREAD_LOCAL.session=s
    return THREAD_LOCAL.session

def fetch_dates_from_cftc(session,where=None):
    params={"$select":"report_date_as_yyyy_mm_dd","$group":"report_date_as_yyyy_mm_dd",
            "$order":"report_date_as_yyyy_mm_dd ASC","$limit":MAX_DATE_ROWS}
    if where: params["$where"]=where
    response=session.get(RESOURCE_URL,params=params,timeout=90)
    response.raise_for_status()
    rows=response.json()
    return sorted({parse_report_date(r["report_date_as_yyyy_mm_dd"]) for r in rows})

def fetch_archive_page(report_day,expected_release=None):
    report_iso=report_day.isoformat()
    url=f"{ARCHIVE_BASE}/{report_day.year}/futures/{report_filename(report_iso)}"
    last_error=None
    for attempt in range(4):
        try:
            response=get_session().get(url,timeout=60)
            if response.status_code in (429,500,502,503,504):
                raise requests.HTTPError(f"transient HTTP {response.status_code}")
            response.raise_for_status()
            heading,updated=parse_archive_dates(response.text)
            expected=date.fromisoformat(expected_release) if expected_release else None
            schedule_lag=(updated-expected).days if expected else None
            return {
                "report_date":report_iso,"url":url,"http_status":response.status_code,
                "heading_matches":heading==report_day,
                "archive_updated_date":updated.isoformat(),
                "archive_lag_days":(updated-heading).days,
                "updated_not_before_report":updated>=heading,
                "expected_official_release_date":expected.isoformat() if expected else None,
                "official_release_lag_days":schedule_lag,
                "official_release_not_earlier":(schedule_lag>=0) if expected else None,
                "official_release_exact_match":(schedule_lag==0) if expected else None,
                "retrieval_status":"ok",
            }
        except Exception as exc:
            last_error=f"{type(exc).__name__}: {exc}"
            if attempt<3: time.sleep(2**attempt)
    return {"report_date":report_iso,"url":url,"retrieval_status":"failed","error_type":last_error.split(":")[0]}

def summarize(pages,all_dates,primary_dates,prelaunch_dates,metadata_before,metadata_after):
    ok=[p for p in pages if p["retrieval_status"]=="ok"]
    failed=[p for p in pages if p["retrieval_status"]!="ok"]
    heading_bad=[p for p in ok if not p["heading_matches"]]
    updated_early=[p for p in ok if not p["updated_not_before_report"]]
    lags=[p["archive_lag_days"] for p in ok]
    schedule=[p for p in ok if p["expected_official_release_date"]]
    schedule_early=[p for p in schedule if not p["official_release_not_earlier"]]
    schedule_exact=[p for p in schedule if p["official_release_exact_match"]]
    schedule_later=[p for p in schedule if p["official_release_lag_days"]>0]
    by_year=defaultdict(list)
    for p in pages: by_year[p["report_date"][:4]].append(p)
    annual={}
    for year,items in sorted(by_year.items()):
        good=[p for p in items if p["retrieval_status"]=="ok"]
        annual[year]={
            "report_dates":len(items),"retrieved":len(good),"failed":len(items)-len(good),
            "heading_mismatches":sum(not p["heading_matches"] for p in good),
            "updated_before_report":sum(not p["updated_not_before_report"] for p in good),
            "median_archive_lag_days":sorted(p["archive_lag_days"] for p in good)[len(good)//2] if good else None,
        }
    first=next((p for p in ok if p["report_date"]=="2010-07-20"),None)
    snapshot_stable=(metadata_before.get("rowsUpdatedAt") is not None and metadata_before.get("rowsUpdatedAt")==metadata_after.get("rowsUpdatedAt"))
    full_census=(len(ok)==len(primary_dates) and not failed and not heading_bad and not updated_early)
    schedule_gate=(len(schedule)==len(OFFICIAL_SCHEDULE_SAMPLES) and not schedule_early)
    first_gate=bool(first and first["archive_updated_date"]=="2010-07-23")
    return {
        "phase":380,"source":"CFTC TFF Futures Only public dataset + static HTML archive",
        "audit_timestamp_utc":datetime.now(timezone.utc).isoformat(),
        "dataset_id":DATASET_ID,"first_tff_report_date":FIRST_TFF_REPORT_DATE.isoformat(),
        "tff_launch_announcement_date":"2010-07-22",
        "report_date_population_count_all":len(all_dates),
        "backcast_report_date_count_before_first_tff_report":len(prelaunch_dates),
        "backcast_first_report_date":prelaunch_dates[0].isoformat() if prelaunch_dates else None,
        "backcast_last_report_date":prelaunch_dates[-1].isoformat() if prelaunch_dates else None,
        "primary_postlaunch_report_date_count":len(primary_dates),
        "primary_first_report_date":primary_dates[0].isoformat() if primary_dates else None,
        "primary_last_report_date":primary_dates[-1].isoformat() if primary_dates else None,
        "archive_pages_retrieved":len(ok),"archive_pages_failed":len(failed),
        "archive_page_coverage_pct":round(100*len(ok)/len(primary_dates),6) if primary_dates else 0,
        "heading_mismatch_count":len(heading_bad),"updated_before_report_count":len(updated_early),
        "archive_lag_days_median":sorted(lags)[len(lags)//2] if lags else None,
        "archive_lag_days_p90":sorted(lags)[int(.90*(len(lags)-1))] if lags else None,
        "archive_lag_days_max":max(lags) if lags else None,
        "official_schedule_sample_count":len(schedule),
        "official_schedule_not_earlier_count":len(schedule)-len(schedule_early),
        "official_schedule_exact_count":len(schedule_exact),
        "official_schedule_later_count":len(schedule_later),
        "official_schedule_earlier_samples":schedule_early,
        "official_schedule_later_samples":schedule_later,
        "first_report_page":first,
        "first_report_page_gate":first_gate,
        "metadata_rows_updated_before":metadata_before.get("rowsUpdatedAt"),
        "metadata_rows_updated_after":metadata_after.get("rowsUpdatedAt"),
        "dataset_metadata_stable":snapshot_stable,
        "annual_coverage":annual,
        "archive_pages":pages,
        "archive_updated_is_formally_defined_as_first_publication":False,
        "availability_rule_candidate":"first regular market session after archive Updated date; never same-day close",
        "strict_historical_pit_authorized":False,
        "raw_html_retained":False,"raw_positions_retained":False,"raw_trader_ids_retained":False,
        "forward_returns_used":False,"alpha_test_authorized":False,"holdout_used":False,
        "f80_changed":False,"production_changed":False,
        "full_postlaunch_archive_census_gate":full_census,
        "official_schedule_not_earlier_gate":schedule_gate,
        "first_tff_report_date_gate":first_gate,
        "research_disposition":(
            "FULL_POSTLAUNCH_ARCHIVE_CENSUS_COMPLETE_UPDATED_DATE_CANDIDATE"
            if full_census and schedule_gate and first_gate and snapshot_stable
            else "FULL_POSTLAUNCH_ARCHIVE_CENSUS_INCOMPLETE_OR_TIMESTAMP_ANOMALY"
        ),
    }

def run_audit():
    control=requests.Session()
    control.headers.update({"User-Agent":"NuevaEstrategia-Phase380/1.0 metadata"})
    metadata_before=control.get(META_URL,timeout=90); metadata_before.raise_for_status()
    metadata_before=metadata_before.json()
    all_dates=fetch_dates_from_cftc(control)
    if not all_dates: raise RuntimeError("No CFTC report dates returned")
    prelaunch=[d for d in all_dates if d<FIRST_TFF_REPORT_DATE]
    primary=[d for d in all_dates if d>=FIRST_TFF_REPORT_DATE]
    if not primary or primary[0]!=FIRST_TFF_REPORT_DATE:
        raise RuntimeError("First TFF report date 2010-07-20 missing from CFTC dataset")
    pages=[]
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures={pool.submit(fetch_archive_page,d,OFFICIAL_SCHEDULE_SAMPLES.get(d.isoformat())):d for d in primary}
        for future in as_completed(futures):
            pages.append(future.result())
    pages.sort(key=lambda p:p["report_date"])
    metadata_after_response=control.get(META_URL,timeout=90); metadata_after_response.raise_for_status()
    metadata_after=metadata_after_response.json()
    return summarize(pages,all_dates,primary,prelaunch,metadata_before,metadata_after)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",default="phase380_cftc_tff_full_postlaunch_archive_census")
    args=parser.parse_args()
    out=Path(args.output); out.mkdir(parents=True,exist_ok=True)
    summary=run_audit()
    (out/"summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True),encoding="utf-8")
    print("PHASE380_CFTC_ARCHIVE_CENSUS=",summary["research_disposition"])
    print("BACKCAST_DATES=",summary["backcast_report_date_count_before_first_tff_report"])
    print("POSTLAUNCH_DATES=",summary["primary_postlaunch_report_date_count"])
    print("ARCHIVE_COVERAGE=",summary["archive_pages_retrieved"],"/",summary["primary_postlaunch_report_date_count"])
    print("OFFICIAL_SCHEDULE_NOT_EARLIER=",summary["official_schedule_not_earlier_count"],"/",summary["official_schedule_sample_count"])
    print("FIRST_REPORT_UPDATED=",summary["first_report_page"].get("archive_updated_date") if summary["first_report_page"] else None)
    print("STRICT_PIT=NOT_AUTHORIZED")
    print("ALPHA_TEST=NOT_AUTHORIZED")
    if summary["research_disposition"]!="FULL_POSTLAUNCH_ARCHIVE_CENSUS_COMPLETE_UPDATED_DATE_CANDIDATE":
        raise SystemExit("Phase 380 full archive census gate failed")

if __name__=="__main__":
    main()

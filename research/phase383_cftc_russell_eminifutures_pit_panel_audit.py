#!/usr/bin/env python3
"""Phase 383: build a date-only archive availability panel for Russell E-mini TFF.

Only CFTC code 239742's post-2017 E-mini era is included. Two known archive
exceptions are expected to be excluded; no raw positions or HTML are retained.
"""
from __future__ import annotations
import argparse,json,re,threading,time
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import date,datetime,timezone
from pathlib import Path
import requests

DATASET_ID="gpe5-46if"
RESOURCE_URL=f"https://publicreporting.cftc.gov/resource/{DATASET_ID}.json"
META_URL=f"https://publicreporting.cftc.gov/api/views/{DATASET_ID}.json"
ARCHIVE_BASE="https://www.cftc.gov/sites/default/files/files/dea/cotarchives"
CODE="239742"
SERIES_START=date(2017,8,15)
MAX_ROWS=1000
MAX_WORKERS=4
LOCAL=threading.local()
DATE_RE=r"([A-Z][a-z]+\s+\d{1,2},\s+\d{4})"
OFFICIAL_SCHEDULE={
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

def parse_date(value):
    return date.fromisoformat(str(value).strip()[:10])

def parse_month_date(value):
    return datetime.strptime(value,"%B %d, %Y").date()

def filename(day):
    return f"financial_lf{day:%m%d%y}.htm"

def parse_archive_dates(html):
    m=re.search(r"Positions\s+as\s+of\s+"+DATE_RE,html,re.I)
    u=re.findall(r"Updated\s+"+DATE_RE,html,re.I)
    if not m: raise ValueError("report heading missing")
    if not u: raise ValueError("Updated field missing")
    return parse_month_date(m.group(1)),parse_month_date(u[-1])

def session():
    if not hasattr(LOCAL,"session"):
        s=requests.Session()
        s.headers.update({"User-Agent":"NuevaEstrategia-Phase383/1.0 CFTC Russell TFF PIT panel"})
        LOCAL.session=s
    return LOCAL.session

def fetch_api_rows():
    where=f"cftc_contract_market_code = '{CODE}' AND report_date_as_yyyy_mm_dd >= '{SERIES_START.isoformat()}T00:00:00.000'"
    params={"$select":"report_date_as_yyyy_mm_dd,cftc_contract_market_code,contract_market_name,market_and_exchange_names",
            "$where":where,"$order":"report_date_as_yyyy_mm_dd ASC","$limit":MAX_ROWS}
    before=requests.get(META_URL,timeout=90);before.raise_for_status();meta_before=before.json()
    count1=requests.get(RESOURCE_URL,params={"$select":"count(*) as n","$where":where},timeout=90)
    count1.raise_for_status();reported_before=int(count1.json()[0]["n"])
    data=requests.get(RESOURCE_URL,params=params,timeout=90);data.raise_for_status();rows=data.json()
    count2=requests.get(RESOURCE_URL,params={"$select":"count(*) as n","$where":where},timeout=90)
    count2.raise_for_status();reported_after=int(count2.json()[0]["n"])
    after=requests.get(META_URL,timeout=90);after.raise_for_status();meta_after=after.json()
    return rows,reported_before,reported_after,meta_before,meta_after

def fetch_page(row):
    day=parse_date(row["report_date_as_yyyy_mm_dd"])
    url=f"{ARCHIVE_BASE}/{day.year}/futures/{filename(day)}"
    last=None
    for attempt in range(3):
        try:
            r=session().get(url,timeout=60)
            if r.status_code in (429,500,502,503,504): raise requests.HTTPError(f"transient HTTP {r.status_code}")
            if r.status_code!=200:
                return {"report_date":day.isoformat(),"url":url,"http_status":r.status_code,"status":"missing"}
            heading,updated=parse_archive_dates(r.text)
            expected=OFFICIAL_SCHEDULE.get(day.isoformat())
            expected_day=date.fromisoformat(expected) if expected else None
            return {
                "report_date":day.isoformat(),"url":url,"http_status":200,
                "heading_date":heading.isoformat(),"archive_updated_date":updated.isoformat(),
                "heading_matches":heading==day,"updated_not_before_report":updated>=day,
                "archive_lag_days":(updated-heading).days,
                "expected_official_release_date":expected,
                "official_release_not_earlier":(updated>=expected_day) if expected_day else None,
                "official_release_lag_days":(updated-expected_day).days if expected_day else None,
                "status":"ok" if heading==day and updated>=day else "invalid",
            }
        except Exception as exc:
            last=type(exc).__name__
            if attempt<2: time.sleep(2**attempt)
    return {"report_date":day.isoformat(),"url":url,"status":"parse_or_request_error","error_class":last}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",default="phase383_cftc_russell_eminifutures_pit_panel")
    args=parser.parse_args()
    rows,before,after,meta_before,meta_after=fetch_api_rows()
    dates=[parse_date(r["report_date_as_yyyy_mm_dd"]) for r in rows]
    keys=[(d.isoformat(),r["cftc_contract_market_code"]) for d,r in zip(dates,rows)]
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures=[pool.submit(fetch_page,r) for r in rows]
        pages=[f.result() for f in as_completed(futures)]
    pages.sort(key=lambda p:p["report_date"])
    valid=[p for p in pages if p["status"]=="ok"]
    invalid=[p for p in pages if p["status"]!="ok"]
    scheduled=[p for p in pages if p.get("expected_official_release_date") and p["status"]=="ok"]
    schedule_early=[p for p in scheduled if not p.get("official_release_not_earlier")]
    lags=[p["archive_lag_days"] for p in valid]
    names=sorted({str(r.get("contract_market_name") or "").strip() for r in rows})
    markets=sorted({str(r.get("market_and_exchange_names") or "").strip() for r in rows})
    metadata_stable=meta_before.get("rowsUpdatedAt")==meta_after.get("rowsUpdatedAt")
    row_reconciled=before==len(rows)==after
    unique=len(set(keys))==len(keys)
    coverage=100*len(valid)/len(rows) if rows else 0
    expected_anomalies={"2018-09-25","2019-12-24"}
    actual_invalid={p["report_date"] for p in invalid}
    anomaly_match=actual_invalid==expected_anomalies
    disposition=("RUSSELL_EMINI_ARCHIVE_PIT_PROXY_480_OF_482_WITH_TWO_EXCLUSIONS"
                 if row_reconciled and metadata_stable and unique and anomaly_match and not schedule_early and coverage>=99.0
                 else "RUSSELL_EMINI_ARCHIVE_PIT_PANEL_INCOMPLETE_OR_NEW_ANOMALY")
    summary={
      "phase":383,"source":"CFTC TFF Futures Only code 239742 + static archive",
      "audit_timestamp_utc":datetime.now(timezone.utc).isoformat(),
      "contract_code":CODE,"series_start":SERIES_START.isoformat(),
      "reported_count_before":before,"retrieved_row_count":len(rows),"reported_count_after":after,
      "row_count_reconciled":row_reconciled,"metadata_rows_updated_before":meta_before.get("rowsUpdatedAt"),
      "metadata_rows_updated_after":meta_after.get("rowsUpdatedAt"),"metadata_stable":metadata_stable,
      "natural_key_duplicate_count":len(keys)-len(set(keys)),"natural_key_unique":unique,
      "first_report_date":min(dates).isoformat() if dates else None,
      "last_report_date":max(dates).isoformat() if dates else None,
      "contract_market_name_variants":names,"market_exchange_name_variants":markets,
      "archive_pages_valid":len(valid),"archive_pages_excluded":len(invalid),
      "archive_page_coverage_pct":round(coverage,6),"excluded_report_dates":sorted(actual_invalid),
      "expected_anomaly_dates_match_gate":anomaly_match,
      "archive_lag_days_median":sorted(lags)[len(lags)//2] if lags else None,
      "archive_lag_days_p90":sorted(lags)[int(.9*(len(lags)-1))] if lags else None,
      "archive_lag_days_max":max(lags) if lags else None,
      "official_schedule_sample_count":len(scheduled),
      "official_schedule_not_earlier_count":len(scheduled)-len(schedule_early),
      "official_schedule_earlier_samples":schedule_early,
      "archive_pages":pages,
      "availability_rule_candidate":"first regular market session after archive Updated date; never same-day close",
      "strict_historical_pit_authorized":False,"raw_html_retained":False,"raw_positions_retained":False,
      "forward_returns_used":False,"alpha_test_authorized":False,"holdout_used":False,
      "f80_changed":False,"production_changed":False,
      "research_disposition":disposition,
    }
    out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
    (out/"summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True),encoding="utf-8")
    print("PHASE383_RUSSELL_EMINI_PIT_PANEL=",disposition)
    print("VALID_ARCHIVE_PAGES=",len(valid),"/",len(rows),"coverage",round(coverage,4))
    print("EXCLUDED_DATES=",sorted(actual_invalid))
    print("STRICT_PIT=NOT_FORMALLY_CERTIFIED")
    print("ALPHA_TEST=NOT_AUTHORIZED")
    if disposition!="RUSSELL_EMINI_ARCHIVE_PIT_PROXY_480_OF_482_WITH_TWO_EXCLUSIONS":
        raise SystemExit("Russell E-mini PIT panel gate failed")

if __name__=="__main__":
    main()

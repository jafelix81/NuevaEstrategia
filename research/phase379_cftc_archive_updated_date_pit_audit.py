#!/usr/bin/env python3
"""Phase 379: test CFTC TFF archive Updated dates against official release schedules.

This is a source timestamp feasibility audit only. HTML is held in memory and
discarded; only report/update dates and retrieval status are retained.
"""
from __future__ import annotations
import argparse, json, re, time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import requests

BASE="https://www.cftc.gov/sites/default/files/files/dea/cotarchives"
TFF_PATH="futures"
OFFICIAL_SCHEDULE_SAMPLES={
    # CFTC 2025 catch-up schedule, Release 9147-25 / Historical Special Announcements.
    "2025-09-30":"2025-11-19",
    "2025-10-07":"2025-11-21",
    "2025-10-14":"2025-11-25",
    "2025-10-21":"2025-12-02",
    "2025-10-28":"2025-12-05",
    "2025-11-04":"2025-12-09",
    "2025-11-10":"2025-12-10",
    "2025-11-18":"2025-12-12",
    "2025-11-25":"2025-12-15",
    "2025-12-02":"2025-12-17",
    "2025-12-09":"2025-12-19",
    "2025-12-16":"2025-12-23",
    "2025-12-23":"2025-12-29",
    # CFTC 2026 Release Schedule.
    "2026-08-25":"2026-08-28",
    "2026-09-01":"2026-09-04",
    "2026-09-08":"2026-09-11",
    "2026-09-15":"2026-09-18",
    "2026-09-22":"2026-09-25",
    "2026-09-29":"2026-10-02",
    "2026-10-06":"2026-10-09",
    "2026-10-13":"2026-10-16",
    "2026-10-20":"2026-10-23",
    "2026-10-27":"2026-10-30",
}
ARCHIVE_ONLY_SAMPLES=[
    "2017-10-03",
    "2020-03-17",
    "2022-07-05",
    "2023-12-26",
    "2024-01-02",
    "2024-11-05",
]
MONTHS={m.lower():i for i,m in enumerate(
    ["January","February","March","April","May","June","July","August","September","October","November","December"],1)}
DATE_RE=r"([A-Z][a-z]+\s+\d{1,2},\s+\d{4})"

def parse_month_date(value):
    month,day,year=re.match(DATE_RE,value).group(1).split()[0],None,None
    parsed=datetime.strptime(value,"%B %d, %Y").date()
    return parsed

def report_filename(report_date):
    d=date.fromisoformat(report_date)
    return f"financial_lf{d:%m%d%y}.htm"

def parse_archive_dates(html):
    # CFTC TFF archive pages contain repeated report-date headings and a final Updated date.
    report_match=re.search(r"Positions\s+as\s+of\s+"+DATE_RE,html,re.I)
    updated_matches=re.findall(r"Updated\s+"+DATE_RE,html,re.I)
    if not report_match:
        raise ValueError("report-date heading not found")
    if not updated_matches:
        raise ValueError("archive Updated date not found")
    report_date=parse_month_date(report_match.group(1))
    updated_date=parse_month_date(updated_matches[-1])
    return report_date,updated_date

def schedule_relation(updated_day, expected_day):
    lag=(updated_day-expected_day).days
    return {"exact":lag==0,"not_earlier":lag>=0,"lag_days":lag}

def fetch_one(session,report_date,expected_release=None,required=False):
    url=f"{BASE}/{report_date[:4]}/{TFF_PATH}/{report_filename(report_date)}"
    error=None
    for attempt in range(4):
        try:
            response=session.get(url,timeout=60)
            if response.status_code in (429,500,502,503,504):
                raise requests.HTTPError(f"transient HTTP {response.status_code}")
            response.raise_for_status()
            report_day,updated_day=parse_archive_dates(response.text)
            requested=date.fromisoformat(report_date)
            expected=date.fromisoformat(expected_release) if expected_release else None
            relation=schedule_relation(updated_day,expected) if expected else None
            return {
                "report_date":report_date,"url":url,"http_status":response.status_code,
                "archive_heading_matches_requested":report_day==requested,
                "archive_updated_date":updated_day.isoformat(),
                "archive_lag_days":(updated_day-report_day).days,
                "expected_official_release_date":expected.isoformat() if expected else None,
                "official_schedule_exact_match":relation["exact"] if relation else None,
                "official_schedule_not_earlier":relation["not_earlier"] if relation else None,
                "official_schedule_lag_days":relation["lag_days"] if relation else None,
                "updated_date_not_before_report_date":updated_day>=report_day,
                "evidence_class":"official_schedule_crosscheck" if expected else "historical_archive_only",
                "retrieval_status":"ok",
            }
        except Exception as exc:
            error=f"{type(exc).__name__}: {exc}"
            if attempt<3:
                time.sleep(2**attempt)
    result={"report_date":report_date,"url":url,"retrieval_status":"failed","error_type":error.split(":")[0]}
    if required:
        result["required_sample"]=True
    return result

def run_audit():
    session=requests.Session()
    session.headers.update({"User-Agent":"NuevaEstrategia-Phase379/1.0 CFTC archive timestamp feasibility research"})
    results=[]
    for report_date,expected in OFFICIAL_SCHEDULE_SAMPLES.items():
        results.append(fetch_one(session,report_date,expected,required=True))
        time.sleep(0.2)
    for report_date in ARCHIVE_ONLY_SAMPLES:
        results.append(fetch_one(session,report_date,required=False))
        time.sleep(0.2)
    scheduled=[r for r in results if r["evidence_class"]=="official_schedule_crosscheck"]
    archive_only=[r for r in results if r["evidence_class"]=="historical_archive_only"]
    successful=[r for r in results if r["retrieval_status"]=="ok"]
    exact_matches=[r for r in scheduled if r.get("official_schedule_exact_match")]
    not_earlier=[r for r in scheduled if r.get("official_schedule_not_earlier")]
    required_failures=[r for r in scheduled if r["retrieval_status"]!="ok"]
    earlier_than_schedule=[r for r in scheduled if r["retrieval_status"]=="ok" and not r.get("official_schedule_not_earlier")]
    later_than_schedule=[r for r in scheduled if r["retrieval_status"]=="ok" and r.get("official_schedule_lag_days",0)>0]
    malformed=[r for r in successful if not r["archive_heading_matches_requested"] or not r["updated_date_not_before_report_date"]]
    return {
        "phase":379,"source":"CFTC TFF Futures Only static HTML archive",
        "audit_timestamp_utc":datetime.now(timezone.utc).isoformat(),
        "official_schedule_source_2025":"https://www.cftc.gov/PressRoom/PressReleases/9147-25",
        "official_schedule_source_2026":"https://www.cftc.gov/MarketReports/CommitmentsofTraders/ReleaseSchedule/index.htm",
        "historical_special_announcements":"https://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalSpecialAnnouncements/index.htm",
        "official_schedule_sample_count":len(scheduled),
        "official_schedule_samples_retrieved":len(scheduled)-len(required_failures),
        "official_schedule_exact_matches":len(exact_matches),
        "official_schedule_not_earlier_matches":len(not_earlier),
        "official_schedule_earlier_count":len(earlier_than_schedule),
        "official_schedule_later_count":len(later_than_schedule),
        "official_schedule_earlier_samples":earlier_than_schedule,
        "official_schedule_later_samples":later_than_schedule,
        "archive_only_sample_count":len(archive_only),
        "archive_only_retrieved":sum(r["retrieval_status"]=="ok" for r in archive_only),
        "archive_only_samples":archive_only,
        "all_successful_headings_match":not malformed,
        "all_official_schedule_samples_not_earlier_gate":len(not_earlier)==len(scheduled) and not required_failures,
        "required_sample_failures":required_failures,
        "successful_samples":successful,
        "raw_html_retained":False,
        "raw_positions_retained":False,
        "archive_updated_field_formally_defined_as_first_publication":False,
        "strict_historical_pit_authorized":False,
        "candidate_rule":"If wider validation confirms archive Updated is never earlier than actual release, use the first regular market session after the archive Updated date; do not use same-day close.",
        "research_disposition":(
            "ARCHIVE_UPDATED_NOT_EARLIER_THAN_ALL_OFFICIAL_RELEASES_CANDIDATE_ONLY"
            if len(not_earlier)==len(scheduled) and not required_failures and not malformed
            else "ARCHIVE_UPDATED_TIMESTAMP_AUDIT_INCOMPLETE_OR_EARLIER_THAN_RELEASE"
        ),
        "alpha_test_authorized":False,"holdout_used":False,"f80_changed":False,"production_changed":False,
    }

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",default="phase379_cftc_archive_updated_date_pit_audit")
    args=parser.parse_args()
    out=Path(args.output); out.mkdir(parents=True,exist_ok=True)
    summary=run_audit()
    (out/"summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True),encoding="utf-8")
    print("PHASE379_CFTC_ARCHIVE_UPDATED_AUDIT=",summary["research_disposition"])
    print("OFFICIAL_SCHEDULE_NOT_EARLIER=",summary["official_schedule_not_earlier_matches"],"/",summary["official_schedule_sample_count"])
    print("OFFICIAL_SCHEDULE_EXACT_MATCHES=",summary["official_schedule_exact_matches"],"/",summary["official_schedule_sample_count"])
    print("LATER_ARCHIVE_UPDATES=",summary["official_schedule_later_count"])
    print("ARCHIVE_ONLY_RETRIEVED=",summary["archive_only_retrieved"],"/",summary["archive_only_sample_count"])
    print("STRICT_PIT=NOT_AUTHORIZED")
    print("ALPHA_TEST=NOT_AUTHORIZED")
    if summary["research_disposition"]!="ARCHIVE_UPDATED_NOT_EARLIER_THAN_ALL_OFFICIAL_RELEASES_CANDIDATE_ONLY":
        raise SystemExit("Phase 379 archive timestamp candidate gate failed")

if __name__=="__main__":
    main()

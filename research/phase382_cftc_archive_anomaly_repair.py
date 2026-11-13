#!/usr/bin/env python3
"""Phase 382: targeted repair audit for CFTC TFF archive timestamp anomalies.

Probes neighboring static archive filenames and HTTP metadata for the eight
Phase 380 exceptions. Stores only dates, status, headers and row counts.
"""
from __future__ import annotations
import argparse,json,re,time
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import date,datetime,timezone,timedelta
from pathlib import Path
import requests

BASE="https://www.cftc.gov/sites/default/files/files/dea/cotarchives"
DATASET="https://publicreporting.cftc.gov/resource/gpe5-46if.json"
TARGETS=("2011-06-14","2013-12-31","2014-11-25","2014-12-02","2018-09-25","2019-12-24","2011-05-10","2012-10-16")
OFFSETS=(-14,-7,0,7,14)
RUSSELL_CODES=("239742","23977A")
DATE_RE=r"([A-Z][a-z]+\s+\d{1,2},\s+\d{4})"

def parse_date(value):
    return date.fromisoformat(str(value)[:10])

def parse_month_date(value):
    return datetime.strptime(value,"%B %d, %Y").date()

def filename(day):
    return f"financial_lf{day:%m%d%y}.htm"

def candidate_dates(target):
    d=parse_date(target)
    return sorted({d+timedelta(days=x) for x in OFFSETS})

def parse_dates(html):
    m=re.search(r"Positions\s+as\s+of\s+"+DATE_RE,html,re.I)
    u=re.findall(r"Updated\s+"+DATE_RE,html,re.I)
    return (parse_month_date(m.group(1)) if m else None,
            parse_month_date(u[-1]) if u else None)

def get_page(day):
    url=f"{BASE}/{day.year}/futures/{filename(day)}"
    s=requests.Session()
    s.headers.update({"User-Agent":"NuevaEstrategia-Phase382/1.0 CFTC archive anomaly audit"})
    last_error=None
    for attempt in range(3):
        try:
            r=s.get(url,timeout=45)
            headers={k.lower():v for k,v in r.headers.items()}
            if r.status_code!=200:
                return {"file_date":day.isoformat(),"url":url,"http_status":r.status_code,
                        "last_modified":headers.get("last-modified"),"etag":headers.get("etag"),
                        "retrieval_status":"http_error"}
            report_day,updated_day=parse_dates(r.text)
            lm=headers.get("last-modified")
            try:
                lm_day=email.utils.parsedate_to_datetime(lm).date().isoformat() if lm else None
            except Exception:
                lm_day=None
            return {
                "file_date":day.isoformat(),"url":url,"http_status":r.status_code,
                "report_heading_date":report_day.isoformat() if report_day else None,
                "archive_updated_date":updated_day.isoformat() if updated_day else None,
                "updated_lag_vs_heading_days":(updated_day-report_day).days if report_day and updated_day else None,
                "last_modified_header":lm,"last_modified_date":lm_day,
                "last_modified_lag_vs_heading_days":(date.fromisoformat(lm_day)-report_day).days if lm_day and report_day else None,
                "etag":headers.get("etag"),"content_length":headers.get("content-length"),
                "retrieval_status":"ok" if report_day and updated_day else "missing_date_field",
            }
        except Exception as exc:
            last_error=type(exc).__name__
            if attempt<2: time.sleep(2**attempt)
    return {"file_date":day.isoformat(),"url":url,"retrieval_status":"failed","error_class":last_error}

def api_counts(target):
    s=requests.Session()
    s.headers.update({"User-Agent":"NuevaEstrategia-Phase382/1.0 CFTC API"})
    where=f"report_date_as_yyyy_mm_dd = '{target}T00:00:00.000'"
    def count(extra=""):
        w=where+(f" AND {extra}" if extra else "")
        r=s.get(DATASET,params={"$select":"count(*) as n","$where":w},timeout=45)
        r.raise_for_status()
        return int(r.json()[0]["n"])
    out={"report_date":target,"all_tff_rows":count()}
    for code in RUSSELL_CODES:
        out[f"rows_{code}"]=count(f"cftc_contract_market_code = '{code}'")
    return out

def audit_target(target):
    days=candidate_dates(target)
    with ThreadPoolExecutor(max_workers=5) as pool:
        pages=list(pool.map(get_page,days))
    exact=[p for p in pages if p.get("report_heading_date")==target]
    try:
        counts=api_counts(target)
    except Exception as exc:
        counts={"report_date":target,"api_count_error":type(exc).__name__}
    return {"target_report_date":target,"api_counts":counts,
            "exact_heading_matches":exact,"candidate_pages":pages,
            "resolution_status":"exact_page_found" if exact else "no_exact_neighbor_page_found"}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",default="phase382_cftc_archive_anomaly_repair")
    args=parser.parse_args()
    with ThreadPoolExecutor(max_workers=4) as pool:
        targets=list(pool.map(audit_target,TARGETS))
    summary={
        "phase":382,"audit_timestamp_utc":datetime.now(timezone.utc).isoformat(),
        "target_count":len(TARGETS),"targets":targets,
        "targets_with_exact_heading_page":sum(t["resolution_status"]=="exact_page_found" for t in targets),
        "targets_without_exact_heading_page":sum(t["resolution_status"]!="exact_page_found" for t in targets),
        "raw_html_retained":False,"raw_positions_retained":False,
        "strict_pit_authorized":False,"alpha_test_authorized":False,"holdout_used":False,
        "f80_changed":False,"production_changed":False,
        "research_disposition":"TARGETED_ARCHIVE_ANOMALY_DIAGNOSTIC_COMPLETE_NO_PIT_PROMOTION",
    }
    out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
    (out/"summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True),encoding="utf-8")
    print("PHASE382_ARCHIVE_ANOMALY_DIAGNOSTIC=PASS")
    print("TARGETS_WITH_EXACT_PAGE=",summary["targets_with_exact_heading_page"],"/",summary["target_count"])
    print("STRICT_PIT=NOT_AUTHORIZED")
    print("ALPHA_TEST=NOT_AUTHORIZED")

if __name__=="__main__":
    import email.utils
    main()

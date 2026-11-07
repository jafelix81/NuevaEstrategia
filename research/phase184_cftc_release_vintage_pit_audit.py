#!/usr/bin/env python3
"""Offline, fail-closed CFTC TFF/COT release-vintage and PIT gate audit."""
from __future__ import annotations
import argparse
import json
from datetime import date, timedelta
from pathlib import Path

PHASE = 184
REPORT_DATE_RULE = "Tuesday position snapshot; ordinary release generally Friday 15:30 ET"
HISTORICAL_RELEASE_CALENDAR_LIMIT_MONTHS = 13
SOURCES = {
    "cftc_faq": "https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm",
    "release_schedule": "https://www.cftc.gov/MarketReports/CommitmentsofTraders/ReleaseSchedule/index.htm",
    "special_announcements": "https://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalSpecialAnnouncements/index.htm",
    "shutdown_2019": "https://www.cftc.gov/PressRoom/PressReleases/7864-19",
}
EXCEPTIONS = [
    # 2023 ION reporting disruption: report date, original scheduled publication, documented publication date.
    ("2023-01-31","2023-02-03","2023-02-24","ION_2023"),
    ("2023-02-07","2023-02-10","2023-03-03","ION_2023"),
    ("2023-02-14","2023-02-17","2023-03-08","ION_2023"),
    ("2023-02-21","2023-02-24","2023-03-10","ION_2023"),
    ("2023-02-28","2023-03-03","2023-03-14","ION_2023"),
    ("2023-03-07","2023-03-10","2023-03-16","ION_2023"),
    ("2023-03-14","2023-03-17","2023-03-21","ION_2023"),
    # 2025 lapse in appropriations: final CFTC update dated 2025-12-09.
    ("2025-09-30","2025-10-03","2025-11-19","SHUTDOWN_2025_FINAL"),
    ("2025-10-07","2025-10-10","2025-11-21","SHUTDOWN_2025_FINAL"),
    ("2025-10-14","2025-10-17","2025-11-25","SHUTDOWN_2025_FINAL"),
    ("2025-10-21","2025-10-24","2025-12-02","SHUTDOWN_2025_FINAL"),
    ("2025-10-28","2025-10-31","2025-12-05","SHUTDOWN_2025_FINAL"),
    ("2025-11-04","2025-11-07","2025-12-09","SHUTDOWN_2025_FINAL"),
    ("2025-11-10","2025-11-14","2025-12-10","SHUTDOWN_2025_FINAL"),
    ("2025-11-18","2025-11-21","2025-12-12","SHUTDOWN_2025_FINAL"),
    ("2025-11-25","2025-12-01","2025-12-15","SHUTDOWN_2025_FINAL"),
    ("2025-12-02","2025-12-05","2025-12-17","SHUTDOWN_2025_FINAL"),
    ("2025-12-09","2025-12-12","2025-12-19","SHUTDOWN_2025_FINAL"),
    ("2025-12-16","2025-12-19","2025-12-23","SHUTDOWN_2025_FINAL"),
    ("2025-12-23","2025-12-29","2025-12-29","SHUTDOWN_2025_FINAL"),
    # 2021 federal holiday: release moved from Friday to Monday.
    ("2021-06-15","2021-06-18","2021-06-21","HOLIDAY_2021"),
]

def iso(s: str) -> date:
    return date.fromisoformat(s)

def build_rows():
    rows = []
    for report_date, scheduled, actual, event in EXCEPTIONS:
        synthetic = iso(report_date) + timedelta(days=6)
        actual_d = iso(actual)
        if synthetic < actual_d:
            relation = "SYNTHETIC_RULE_EARLY"
        elif synthetic == actual_d:
            relation = "SAME_DATE_EXACT_TIME_UNKNOWN"
        else:
            relation = "SYNTHETIC_RULE_LATE"
        rows.append({
            "report_date": report_date,
            "scheduled_release_date": scheduled,
            "documented_actual_release_date": actual,
            "release_time_et": None,
            "first_receipt_utc": None,
            "next_eligible_exchange_session": None,
            "event": event,
            "synthetic_report_date_plus_6": synthetic.isoformat(),
            "synthetic_rule_relation": relation,
            "date_precision_only": True,
            "strict_pit_admitted": False,
        })
    return rows

def pit_admissible(*, actual_release_date, first_receipt_utc,
                   next_eligible_exchange_session, identity_resolved,
                   methodology_versioned):
    required = [actual_release_date, first_receipt_utc,
                next_eligible_exchange_session]
    if not all(required) or not identity_resolved or not methodology_versioned:
        return False
    try:
        release = iso(actual_release_date)
        eligible = iso(next_eligible_exchange_session)
    except (TypeError, ValueError):
        return False
    return eligible > release

def label_mature(label_end_session, test_entry_session):
    """Strict maturity: the label must end before the test entry session."""
    if not label_end_session or not test_entry_session:
        return False
    try:
        return iso(label_end_session) < iso(test_entry_session)
    except (TypeError, ValueError):
        return False

def build_audit():
    rows = build_rows()
    early = sum(r["synthetic_rule_relation"] == "SYNTHETIC_RULE_EARLY" for r in rows)
    same = sum(r["synthetic_rule_relation"] == "SAME_DATE_EXACT_TIME_UNKNOWN" for r in rows)
    return {
        "phase": PHASE,
        "date": "2026-11-07",
        "status": "HISTORICAL_PIT_GATE_FAIL_PHASE23C_QUARANTINED",
        "source": "CFTC TFF/COT official publication notices",
        "source_urls": SOURCES,
        "ordinary_schedule": REPORT_DATE_RULE,
        "official_historical_release_date_limit_months": HISTORICAL_RELEASE_CALENDAR_LIMIT_MONTHS,
        "complete_official_release_date_ledger_available_for_2016_2024": False,
        "documented_exception_rows": len(rows),
        "exception_counts": {
            "ION_2023": sum(r["event"] == "ION_2023" for r in rows),
            "SHUTDOWN_2025_FINAL": sum(r["event"] == "SHUTDOWN_2025_FINAL" for r in rows),
            "HOLIDAY_2021": sum(r["event"] == "HOLIDAY_2021" for r in rows),
        },
        "report_date_plus_6_comparison": {
            "synthetic_earlier_than_documented_release": early,
            "synthetic_same_date_time_unknown": same,
            "synthetic_later_than_documented_release": len(rows) - early - same,
        },
        "exceptions": rows,
        "unresolved_outage_windows": [{
            "event": "SHUTDOWN_2018_2019",
            "last_published_report_date": "2018-12-21",
            "next_report_date": "2018-12-24",
            "original_scheduled_release_date": "2018-12-28",
            "expected_catchup_release_date": "2019-02-01",
            "exact_first_publication_vintage_for_all_missed_reports": False,
            "disposition": "OUTAGE_WINDOW_ONLY_NOT_A_ROW_LEVEL_RELEASE_LEDGER",
        }],
        "phase23c_static_findings": {
            "synthetic_knowledge_rule": "ReportDate + 6 calendar days",
            "label_maturity_embargo_present": False,
            "phase182_immature_h5_test_dates": 6,
            "phase182_total_h5_test_dates": 12,
            "phase182_immature_h20_test_dates": 12,
            "phase182_total_h20_test_dates": 12,
            "affected_2023_walkforward_test_date": "2023-03-27",
            "disposition": "QUARANTINED_NO_REUSE",
        },
        "admission": {
            "historical_cftc_tff_pit_admitted": False,
            "phase23c_results_confirmatory": False,
            "prospective_shadow_capture_permitted_after_first_receipt_logger": True,
            "alpha_test_authorized": False,
            "holdout_used": False,
            "production_changed": False,
            "f80_baseline": "FROZEN",
        },
        "required_controls": [
            "actual_publication_date_and_time_or_explicit_unknown",
            "immutable_first_receipt_utc_and_raw_hash",
            "append_only_correction_vintages",
            "effective_dated_contract_identity",
            "next_actual_exchange_session_execution",
            "exchange_calendar_label_maturity_embargo_by_horizon",
        ],
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="phase184_output/phase184_cftc_release_vintage_pit_audit.json")
    args = parser.parse_args()
    result = build_audit()
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "phase": PHASE,
        "status": result["status"],
        "documented_exception_rows": result["documented_exception_rows"],
        "synthetic_early": result["report_date_plus_6_comparison"]["synthetic_earlier_than_documented_release"],
        "synthetic_same_date_unknown_time": result["report_date_plus_6_comparison"]["synthetic_same_date_time_unknown"],
        "pit_admitted": result["admission"]["historical_cftc_tff_pit_admitted"],
        "output": str(out),
    }, indent=2))

if __name__ == "__main__":
    main()

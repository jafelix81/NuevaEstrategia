"""Phase 263: adjudicate whether the CFTC semiweekly COT plan applies to TFF.

This is an official-source scope gate, not a positioning signal or a live
capture. It deliberately fails closed: TFF cadence changes only after
TFF-specific scope, an official TFF schedule, and two distinct TFF report
dates in the same publication week are all observed.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

AUDIT_DATE = "2026-11-10"
CURRENT_TFF_REPORT_DATE = "2026-11-03"
EXPECTED_STREAMS = ("futures_only", "futures_options_combined")


def adjudicate_tff_cadence(evidence: dict) -> dict:
    required = (
        "cot_semiweekly_plan_announced",
        "announcement_scope_is_agricultural_markets",
        "announcement_explicitly_includes_tff",
        "official_tff_wednesday_friday_schedule",
        "distinct_tff_report_dates_in_same_week",
        "current_cot_page_says_weekly",
        "current_faq_says_once_weekly",
        "current_tff_streams",
        "current_tff_report_date",
    )
    missing = [key for key in required if key not in evidence]
    if missing:
        raise ValueError(f"missing cadence evidence: {missing}")
    streams = evidence["current_tff_streams"]
    if set(streams) != set(EXPECTED_STREAMS):
        raise ValueError("both distinct TFF streams must be present")
    if any(not streams[name] for name in EXPECTED_STREAMS):
        raise ValueError("TFF stream URL cannot be blank")
    report_date = evidence["current_tff_report_date"]
    if report_date != CURRENT_TFF_REPORT_DATE:
        raise ValueError("current TFF report date differs from pinned audit evidence")
    semiweekly_confirmed = all((
        bool(evidence["announcement_explicitly_includes_tff"]),
        bool(evidence["official_tff_wednesday_friday_schedule"]),
        int(evidence["distinct_tff_report_dates_in_same_week"]) >= 2,
    ))
    reasons = []
    if evidence["cot_semiweekly_plan_announced"]:
        reasons.append("COT_SEMIWEEKLY_PLAN_ANNOUNCED_BY_END_2026")
    if evidence["announcement_scope_is_agricultural_markets"] and not evidence["announcement_explicitly_includes_tff"]:
        reasons.append("ANNOUNCEMENT_CONTEXT_IS_AGRICULTURAL_AND_TFF_SCOPE_NOT_EXPLICIT")
    if evidence["current_cot_page_says_weekly"]:
        reasons.append("CURRENT_COT_INDEX_STILL_DESCRIBES_WEEKLY_REPORTS")
    if evidence["current_faq_says_once_weekly"]:
        reasons.append("CURRENT_COT_FAQ_STILL_SAYS_ONCE_WEEKLY")
    if not evidence["official_tff_wednesday_friday_schedule"]:
        reasons.append("NO_OFFICIAL_TFF_WEDNESDAY_FRIDAY_SCHEDULE_OBSERVED")
    if int(evidence["distinct_tff_report_dates_in_same_week"]) < 2:
        reasons.append("FEWER_THAN_TWO_DISTINCT_TFF_REPORT_DATES_OBSERVED_IN_WEEK")
    return {
        "audit_date": AUDIT_DATE,
        "semiweekly_cot_plan_announced": bool(evidence["cot_semiweekly_plan_announced"]),
        "tff_semiweekly_confirmed": semiweekly_confirmed,
        "tff_cadence_disposition": (
            "SEMIWEEKLY_CONFIRMED" if semiweekly_confirmed
            else "RETAIN_WEEKLY_ASSUMPTION_PENDING_TFF_SPECIFIC_CONFIRMATION"
        ),
        "current_tff_report_date": report_date,
        "current_tff_streams": dict(streams),
        "reasons": reasons,
        "capture_protocol": {
            "retain_existing_weekday_polling": True,
            "create_duplicate_workflow": False,
            "scheduled_capture_is_first_observed_known_by_not_exact_first_publication": True,
            "report_date_is_not_knowledge_time": True,
        },
        "research_disposition": {
            "tff_is_stock_level_smart_money_feed": False,
            "category_is_beneficial_owner_identity": False,
            "historical_release_dates_fully_reconstructed": False,
            "strict_historical_pit_admitted": False,
            "alpha_admitted": False,
            "f80_frozen": True,
            "holdout_used": False,
        },
    }


def build_evidence() -> dict:
    return {
        "cot_semiweekly_plan_announced": True,
        "announcement_scope_is_agricultural_markets": True,
        "announcement_explicitly_includes_tff": False,
        "official_tff_wednesday_friday_schedule": False,
        "distinct_tff_report_dates_in_same_week": 1,
        "current_cot_page_says_weekly": True,
        "current_faq_says_once_weekly": True,
        "current_tff_report_date": CURRENT_TFF_REPORT_DATE,
        "current_tff_streams": {
            "futures_only": "https://www.cftc.gov/dea/newcot/FinFutWk.txt",
            "futures_options_combined": "https://www.cftc.gov/dea/newcot/FinComWk.txt",
        },
    }


def build_result() -> dict:
    evidence = build_evidence()
    decision = adjudicate_tff_cadence(evidence)
    return {
        "phase": 263,
        "date": AUDIT_DATE,
        "source": "CFTC Commitments of Traders / Traders in Financial Futures",
        "status": decision["tff_cadence_disposition"],
        "evidence": evidence,
        "decision": decision,
        "official_sources": {
            "semiweekly_announcement": "https://www.cftc.gov/PressRoom/PressReleases/9316-26",
            "cot_index": "https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm",
            "release_schedule": "https://www.cftc.gov/MarketReports/CommitmentsofTraders/ReleaseSchedule/index.htm",
            "tff_futures_only": evidence["current_tff_streams"]["futures_only"],
            "tff_futures_options_combined": evidence["current_tff_streams"]["futures_options_combined"],
        },
        "data_scope": {
            "current_tff_report_date": CURRENT_TFF_REPORT_DATE,
            "full_raw_files_persisted": False,
            "prospective_capture_executed": False,
            "new_workflow_created": False,
        },
        "controls": {
            "strict_pit_admitted": False,
            "alpha_admitted": False,
            "returns_tested": False,
            "bootstrap_loo_oos_tested": False,
            "holdout_used": False,
            "production_changed": False,
            "universe_changed": False,
            "capital_changed": False,
            "f80_baseline": "F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = build_result()
    Path(args.output).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("PHASE263_STATUS=" + result["status"])
    print("TFF_SEMIWEEKLY_CONFIRMED=" + str(result["decision"]["tff_semiweekly_confirmed"]).lower())


if __name__ == "__main__":
    main()

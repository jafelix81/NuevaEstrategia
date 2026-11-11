"""Static source-feasibility gate for SEC Rule 13f-2 / Form SHO.

No SEC data are downloaded. The module records the rule's current compliance
calendar, public aggregation semantics, thresholds, and PIT limitations as of
2026-11-10. It deliberately does not admit historical alpha.
"""
from __future__ import annotations

import argparse
import json
from datetime import date, timedelta
from pathlib import Path

AS_OF = date(2026, 11, 10)
COMPLIANCE_DATE = date(2028, 1, 2)
FIRST_REPORT_MONTH_END = date(2028, 1, 31)
FIRST_FILING_DEADLINE = FIRST_REPORT_MONTH_END + timedelta(days=14)


def build_result() -> dict:
    return {
        "phase": 268,
        "as_of_date": AS_OF.isoformat(),
        "source": "SEC Exchange Act Rule 13f-2 / Form SHO",
        "current_status": "TEMPORARY_EXEMPTION_THROUGH_2028-01-02",
        "compliance_date": COMPLIANCE_DATE.isoformat(),
        "first_reporting_period": "2028-01",
        "first_filing_deadline": FIRST_FILING_DEADLINE.isoformat(),
        "initial_publication": {
            "rule": "SEC planned to begin aggregated publication three months after the compliance date.",
            "approximate_start": "2028-04",
            "exact_first_publication_date_verified": False,
            "regular_cadence": "Aggregated data expected within one calendar month after each reporting month-end.",
        },
        "public_data": {
            "aggregation_unit": "equity security",
            "manager_identity_disclosed": False,
            "gross_end_of_month_short_position": True,
            "daily_net_position_activity_by_settlement_date": True,
            "individual_manager_positions_public": False,
            "manager_count_public": False,
            "single_manager_inference_risk": "SEC notes rare cases may permit inference where only one manager contributes.",
        },
        "reporting_thresholds": {
            "reporting_company": {
                "monthly_average_gross_short_usd_min": 10000000,
                "or_monthly_average_gross_short_pct_shares_min": 2.5,
            },
            "non_reporting_company": {
                "gross_short_usd_min_on_any_settlement_date": 500000,
            },
            "coverage_status": "THRESHOLD_CENSORED_NOT_UNIVERSE_COMPLETE",
        },
        "timeliness_and_quality": {
            "manager_filing_deadline": "14 calendar days after each month-end",
            "publication_lag": "approximately one month after reporting month-end",
            "positions_may_be_closed_before_publication": True,
            "sec_historical_form_sh_analysis_average_threshold_duration_days_after_month_end": 9.85,
            "duration_statistic_is_historical_form_sh_context_not_a_form_sho_observation": True,
            "edgar_validation_checks_technical_completeness_not_economic_accuracy": True,
            "amendments_and_restated_filings_possible": True,
            "rolling_publication_includes_prior_12_months_updated_for_amendments": True,
        },
        "historical_pit": {
            "public_data_available_as_of_audit": False,
            "pre_2028_public_backfill": False,
            "strict_historical_pit_admitted": False,
            "prospective_first_receipt_capture_required": True,
        },
        "related_rule_10c_1a": {
            "reporting_compliance_date": "2028-09-28",
            "public_dissemination_compliance_date": "2029-03-29",
            "status": "SEPARATE_FUTURE_SECURITIES_LENDING_SOURCE",
        },
        "research_decision": {
            "classification": "FUTURE_AGGREGATE_SHORT_SIDE_CANDIDATE_NOT_YET_AVAILABLE",
            "smart_money_identity_claim": False,
            "historical_alpha_admitted": False,
            "backtest_performed": False,
            "production_change": False,
            "f80_frozen": True,
            "holdout_used": False,
        },
        "future_hypotheses": [
            "Aggregate gross short crowding may add information about downside risk or squeeze vulnerability.",
            "Daily net short-position activity may add information about subsequent volatility or returns after public receipt.",
            "Incremental value must be tested against FINRA short interest, FINRA short volume, options features, and frozen LTM/F80.",
        ],
        "source_urls": [
            "https://www.sec.gov/files/rules/exorders/2025/34-104303.pdf",
            "https://www.sec.gov/files/rules/final/2023/34-98738.pdf",
        ],
    }


def validate_result(result: dict) -> None:
    assert result["phase"] == 268
    assert result["compliance_date"] == "2028-01-02"
    assert result["first_reporting_period"] == "2028-01"
    assert result["first_filing_deadline"] == "2028-02-14"
    assert result["initial_publication"]["approximate_start"] == "2028-04"
    assert result["initial_publication"]["exact_first_publication_date_verified"] is False
    assert result["public_data"]["aggregation_unit"] == "equity security"
    assert result["public_data"]["manager_identity_disclosed"] is False
    assert result["reporting_thresholds"]["reporting_company"]["monthly_average_gross_short_usd_min"] == 10000000
    assert result["reporting_thresholds"]["reporting_company"]["or_monthly_average_gross_short_pct_shares_min"] == 2.5
    assert result["reporting_thresholds"]["non_reporting_company"]["gross_short_usd_min_on_any_settlement_date"] == 500000
    assert result["reporting_thresholds"]["coverage_status"] == "THRESHOLD_CENSORED_NOT_UNIVERSE_COMPLETE"
    assert result["historical_pit"]["public_data_available_as_of_audit"] is False
    assert result["historical_pit"]["strict_historical_pit_admitted"] is False
    assert result["research_decision"]["historical_alpha_admitted"] is False
    assert result["research_decision"]["f80_frozen"] is True
    assert result["research_decision"]["holdout_used"] is False
    assert result["related_rule_10c_1a"]["reporting_compliance_date"] == "2028-09-28"
    assert result["related_rule_10c_1a"]["public_dissemination_compliance_date"] == "2029-03-29"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = build_result()
    validate_result(result)
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    main()

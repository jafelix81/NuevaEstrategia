#!/usr/bin/env python3
"""Phase 189: future SEC Form SHO and FINRA SLATE availability/PIT gate.

Metadata-only. No SEC/FINRA requests, raw data, account, vendor contact,
purchase, returns, holdout, or production change.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

AS_OF = "2026-11-07"
FORM_SHO_FIRST_PERIOD = "2028-01"
FORM_SHO_FIRST_DUE = "2028-02-14"
FORM_SHO_COMPLIANCE = "2028-01-02"
SLATE_REPORTING = "2028-09-28"
SLATE_PUBLIC = "2029-03-29"

SOURCES = {
    "sec_order_34_104303": "https://www.sec.gov/files/rules/exorders/2025/34-104303.pdf",
    "sec_2026_rule_10c1a_status": "https://www.govinfo.gov/content/pkg/FR-2026-09-30/html/2026-20056.htm",
    "form_sho_final_rule": "https://public-inspection.federalregister.gov/2023-23050.pdf",
    "rule_10c1a_final_rule": "https://www.sec.gov/files/rules/final/2023/34-98737.pdf",
    "sec_rule_10c1a_press_release": "https://www.sec.gov/newsroom/press-releases/2023-220",
    "finra_slate_rules": "https://www.finra.org/rules-guidance/rulebooks/finra-rules/6500-series",
}


def build_audit() -> dict:
    return {
        "phase": 189,
        "audit_as_of": AS_OF,
        "status": "FUTURE_PROSPECTIVE_CANDIDATES_ONLY",
        "sources": SOURCES,
        "form_sho": {
            "rule": "Exchange Act Rule 13f-2 / Form SHO",
            "compliance_restart_date": FORM_SHO_COMPLIANCE,
            "first_reporting_period": FORM_SHO_FIRST_PERIOD,
            "first_filing_due_date": FORM_SHO_FIRST_DUE,
            "filing_frequency": "monthly",
            "thresholds": {
                "reporting_company": {
                    "monthly_average_gross_short_position_usd_min": 10_000_000,
                    "monthly_average_gross_short_position_percent_shares_outstanding_min": 2.5,
                },
                "non_reporting_company": {
                    "gross_short_position_usd_min": 500_000,
                    "trigger": "at_close_of_regular_trading_hours_on_any_settlement_date_in_month",
                },
            },
            "reported_objects": [
                "month_end_gross_short_position",
                "manager_reported_daily_net_change_in_gross_short_position_by_settlement_date",
            ],
            "gross_short_position_netted_against_longs_or_derivatives": False,
            "manager_filing_confidential": True,
            "public_manager_identity": False,
            "public_output": "security_level_aggregates_across_reporting_managers",
            "original_expected_ongoing_publication": "within_one_calendar_month_after_reporting_month; initial dissemination timing requires verification",
            "first_publication_date_verified": False,
            "threshold_censored": True,
            "daily_net_activity_is_raw_short_sale_volume": False,
            "amendment_rule": "amendment_and_restatement; errors amended within 10 calendar days of discovery; public aggregates may update rolling 12 months",
            "possible_sparse_aggregate_reidentification": True,
            "pre_compliance_historical_backfill_verified": False,
        },
        "rule_10c1a_slate": {
            "rule": "Exchange Act Rule 10c-1a / FINRA SLATE",
            "covered_person_reporting_date": SLATE_REPORTING,
            "required_public_dissemination_date": SLATE_PUBLIC,
            "first_public_receipt_verified": False,
            "public_loan_fields": [
                "issuer_and_security_identifiers",
                "loan_effected_date_and_time",
                "platform_or_venue",
                "lending_fee_or_rate_and_rebate_terms",
                "collateral_terms_and_collateral_to_value",
                "scheduled_termination_date",
                "borrower_category",
                "unique_loan_identifier",
            ],
            "most_public_loan_fields_lag": "no_later_than_morning_of_next_business_day_after_effect_or_modification",
            "loan_amount_public_lag_business_days": 20,
            "lender_borrower_intermediary_legal_identity_public": False,
            "party_regulatory_identifiers_public": False,
            "daily_aggregate_activity_is_directional_net_change": False,
            "available_to_lend_field_in_final_rule": False,
            "pre_existing_loans": "only reportable after a qualifying post-implementation modification; no blanket day-one backfill",
            "public_retention_years_min": 5,
            "fees_and_bulk_terms_verified": False,
            "pre_compliance_historical_backfill_verified": False,
        },
        "source_roles": {
            "form_sho": "future threshold-qualified aggregate institutional short-position state and daily net-change context",
            "slate": "future anonymized securities-loan terms, rate and activity context",
            "not_interchangeable_with": [
                "FINRA daily short-sale volume",
                "FINRA settlement short interest",
                "beneficial-owner identity",
                "raw order/trade flow",
            ],
        },
        "pit_and_research_gates": {
            "form_sho_pit_admitted": False,
            "slate_pit_admitted": False,
            "alpha_test_authorized": False,
            "prospective_first_receipt_capture_required": True,
            "immutable_vintages_required": True,
            "historical_universe_and_security_identity_required": True,
            "holdout_used": False,
        },
        "controls": {
            "raw_data_downloaded": False,
            "sec_finra_requests_made": False,
            "account_used": False,
            "vendor_contact": False,
            "data_purchase": False,
            "terms_accepted": False,
            "production_changed": False,
            "f80_frozen": True,
            "phase20c_reopened": False,
        },
        "decision": "Retain Form SHO and SLATE as future prospective research candidates only. Do not claim current data availability, do not assume historical backfill, and do not start alpha tests until actual first-publication/vintage, coverage, identity and licensing gates pass.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("phase189_output/phase189_short_lending_availability_audit.json"),
    )
    args = parser.parse_args()
    result = build_audit()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "phase": result["phase"],
        "status": result["status"],
        "form_sho_first_reporting_period": result["form_sho"]["first_reporting_period"],
        "form_sho_first_filing_due_date": result["form_sho"]["first_filing_due_date"],
        "slate_reporting_date": result["rule_10c1a_slate"]["covered_person_reporting_date"],
        "slate_public_date": result["rule_10c1a_slate"]["required_public_dissemination_date"],
        "form_sho_pit_admitted": result["pit_and_research_gates"]["form_sho_pit_admitted"],
        "slate_pit_admitted": result["pit_and_research_gates"]["slate_pit_admitted"],
        "alpha_test_authorized": result["pit_and_research_gates"]["alpha_test_authorized"],
        "f80_frozen": result["controls"]["f80_frozen"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

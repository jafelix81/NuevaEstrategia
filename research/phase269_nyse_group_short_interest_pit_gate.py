"""Static source-feasibility gate for NYSE Group Short Interest.

No subscription, vendor contact, historical download, or market-data test is
performed. The module records public specifications and PIT limitations as of
2026-11-10.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def build_result() -> dict:
    return {
        "phase": 269,
        "as_of_date": "2026-11-10",
        "source": "NYSE Group Short Interest",
        "product_page": {
            "historical_start": "1988-01",
            "delivery_frequency": "semi-monthly",
            "product_page_venues": ["NYSE", "NYSE Arca", "NYSE American"],
            "subscription_required": True,
            "price_publicly_verified": False,
            "public_sample_settlement_dates": ["2026-07-15", "2026-07-31"],
        },
        "technical_specification": {
            "version": "1.7",
            "version_date": "2025-04-10",
            "delivery_time_et": "14:00",
            "delivery_timing": "on NYSE Group Release Date",
            "delivery_channels": ["SFTP", "AWS S3"],
            "specification_venues": ["NYSE", "NYSE American", "NYSE Arca", "NYSE Texas"],
            "market_codes": {"N": "NYSE", "A": "NYSE American", "P": "NYSE Arca", "M": "NYSE Texas"},
            "file_fields": [
                "Stock_Symbol", "Standard_Suffix", "CUSIP", "Legal_Issuer_Name",
                "Issue_Name", "Primary_Market", "Revision_Indicator", "Split_Indicator",
                "Free_Float", "Current_Short_Interest_Position",
                "Previous_Short_Interest_Position", "Change_In_Short_Interest_Position",
                "Average_Daily_Volume", "Change_In_Average_Daily_Volume",
                "Current_Days_To_Cover", "Change_In_Days_To_Cover",
            ],
            "revision_indicator_R": "previous reporting period revised",
            "split_indicator_S": "stock split during current reporting period",
            "free_float_zero_means_unavailable": True,
            "free_float_quality": "best-effort; may differ from other sources",
            "cusip_present": True,
            "permanent_security_id": False,
        },
        "timing_comparison": {
            "nyse_group_release_time_et": "14:00",
            "finra_api_available_by_et": "16:40",
            "same_release_date_examples": [
                {"settlement_date": "2026-07-15", "release_date": "2026-07-24"},
                {"settlement_date": "2026-07-31", "release_date": "2026-08-11"},
            ],
            "difference_minutes": 160,
            "same_day_close_potential_if_actual_receipt_before_actual_xnys_session_close": True,
            "execution_rule": "Use the actual XNYS close on the release date; on early-close sessions where the market closes before 14:00 ET, the file is post-close and entry must move to the next session.",
            "actual_first_receipt_timestamp_required": True,
        },
        "source_relationship": {
            "same_underlying_finra_rule_4560_reporting_pipeline": True,
            "independent_signal_source": False,
            "role": "earlier listing-exchange distribution of FINRA-aggregated short-interest data",
            "beneficial_owner_or_account_identity": False,
            "naked_short_inference_valid": False,
        },
        "historical_pit_and_coverage": {
            "historical_coverage_advertised": "1988-01 to present",
            "full_history_in_free_sample": False,
            "original_as_published_vintages_verified": False,
            "historical_revision_chain_verified": False,
            "delisted_security_coverage_verified": False,
            "prospective_first_receipt_capture_possible": True,
            "coverage_scope": "NYSE Group listings; not full U.S. listed/OTC universe",
            "nyse_texas_scope_discrepancy": "product page lists three venues while v1.7 specification adds NYSE Texas code M",
            "repository_universe_snapshot_present": False,
            "universe_overlap_calculated": False,
        },
        "commercial_and_operational": {
            "subscription_required": True,
            "price_publicly_verified": False,
            "license_terms_verified": False,
            "sftp_requires_dedicated_source_ip_and_ssh_key": True,
            "purchase_authorized": False,
            "vendor_contact_authorized": False,
        },
        "research_decision": {
            "classification": "CONDITIONAL_PAID_EARLY_RELEASE_DISTRIBUTION_OF_FINRA_SHORT_INTEREST",
            "historical_pit_admitted": False,
            "alpha_admitted": False,
            "backtest_performed": False,
            "production_change": False,
            "f80_frozen": True,
            "holdout_used": False,
        },
        "future_tests_if_license_and_vintages_are_verified": [
            "Compare 14:00 ET same-day-close execution with 16:40 ET next-session execution using identical report values, exposure, and costs.",
            "Test short-interest level, change, and days-to-cover as risk/crowding features, not as named institutional flow.",
            "Measure incremental information versus frozen LTM/F80 and the same FINRA data distributed through other channels.",
            "Use CUSIP plus effective-dated security identity; preserve revisions and splits; never use free-float zero as numeric zero.",
        ],
        "source_urls": [
            "https://www.nyse.com/data-products/catalog/nyse-group-short-interest",
            "https://www.nyse.com/publicdocs/nyse/data/NYSE_Group_Short_Interest_Client_Specification_v1.7.pdf",
            "https://www.nyse.com/publicdocs/nyse/data/NYSE_Group_Short_Interest_Calendar.pdf",
            "https://developer.finra.org/docs",
            "https://www.finra.org/filing-reporting/regulatory-filing-systems/short-interest",
            "https://public-inspection.federalregister.gov/2022-04670.pdf",
            "https://www.finra.org/filing-reporting/regulatory-filing-systems/short-interest/faq",
        ],
    }


def validate_result(result: dict) -> None:
    assert result["phase"] == 269
    assert result["product_page"]["historical_start"] == "1988-01"
    assert result["product_page"]["subscription_required"] is True
    assert result["technical_specification"]["delivery_time_et"] == "14:00"
    assert result["technical_specification"]["version"] == "1.7"
    assert result["technical_specification"]["cusip_present"] is True
    assert result["technical_specification"]["free_float_zero_means_unavailable"] is True
    assert result["technical_specification"]["market_codes"]["M"] == "NYSE Texas"
    assert result["timing_comparison"]["finra_api_available_by_et"] == "16:40"
    assert result["timing_comparison"]["difference_minutes"] == 160
    assert len(result["timing_comparison"]["same_release_date_examples"]) == 2
    assert result["timing_comparison"]["actual_first_receipt_timestamp_required"] is True
    assert "actual XNYS close" in result["timing_comparison"]["execution_rule"]
    assert "early-close" in result["timing_comparison"]["execution_rule"]
    assert result["source_relationship"]["same_underlying_finra_rule_4560_reporting_pipeline"] is True
    assert result["source_relationship"]["independent_signal_source"] is False
    assert result["historical_pit_and_coverage"]["original_as_published_vintages_verified"] is False
    assert result["historical_pit_and_coverage"]["universe_overlap_calculated"] is False
    assert result["commercial_and_operational"]["purchase_authorized"] is False
    assert result["commercial_and_operational"]["vendor_contact_authorized"] is False
    assert result["research_decision"]["historical_pit_admitted"] is False
    assert result["research_decision"]["alpha_admitted"] is False
    assert result["research_decision"]["f80_frozen"] is True
    assert result["research_decision"]["holdout_used"] is False


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

"""Phase 270: adjudicate the official NYSE Group Short Interest public sample scope.

Metadata/specification audit only. It deliberately does not download, parse,
persist, or redistribute NYSE sample rows because current ICE terms exclude
automated data mining/extraction without prior written permission.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path


def build_result() -> dict:
    return {
        "phase": 270,
        "as_of_date": "2026-11-10",
        "source": "NYSE Group Short Interest",
        "scope_correction": {
            "official_product_page_links_to_reference_data_samples": True,
            "sample_directory": "https://ftp.nyse.com/Reference%20Data%20Samples/NYSE%20GROUP%20SHORT%20INTEREST/",
            "sample_is_security_level": True,
            "sample_is_exchange_level_aggregate_only": False,
            "basis": [
                "official product page Sample Data link resolves to the Reference Data Samples directory",
                "indexed sample text preview shows one security issue per pipe-delimited row",
                "official specification defines 16 security-level fields including ticker, suffix, CUSIP and current short position",
            ],
            "separate_aggregate_report_directory": "https://ftp.nyse.com/NYSEGroupConsolidatedShortInterest/",
            "separate_aggregate_report_must_not_be_conflated_with_product_sample": True,
            "third_party_aggregate_only_description_applies_to_separate_report_path": True,
            "full_sample_downloaded_or_parsed": False,
        },
        "official_product": {
            "historical_start_advertised": "1988-01",
            "frequency": "semi-monthly",
            "venues_product_page": ["NYSE", "NYSE Arca", "NYSE American"],
            "venues_specification_v1_7": ["NYSE", "NYSE American", "NYSE Arca", "NYSE Texas"],
            "subscription_required_for_full_history": True,
            "technical_specification_version": "1.7",
            "technical_specification_date": "2025-04-10",
            "release_delivery_time_et": "14:00",
            "field_count": 16,
            "fields": [
                "Stock_Symbol", "Standard_Suffix", "CUSIP", "Legal_Issuer_Name",
                "Issue_Name", "Primary_Market", "Revision_Indicator", "Split_Indicator",
                "Free_Float", "Current_Short_Interest_Position",
                "Previous_Short_Interest_Position", "Change_In_Short_Interest_Position",
                "Average_Daily_Volume", "Change_In_Average_Daily_Volume",
                "Current_Days_To_Cover", "Change_In_Days_To_Cover",
            ],
            "primary_market_codes": {
                "N": "NYSE", "A": "NYSE American", "P": "NYSE Arca", "M": "NYSE Texas"
            },
        },
        "public_sample_directory": {
            "listing_modified_date": "2026-09-30",
            "files": [
                {
                    "settlement_date": "2026-07-15",
                    "txt_bytes": 750412,
                    "xls_bytes": 2130432,
                    "xml_bytes": 4300106,
                    "indexed_text_lines": 5877,
                    "line_count_is_not_claimed_as_fully_parsed_record_count": True,
                },
                {
                    "settlement_date": "2026-07-31",
                    "txt_bytes": 751053,
                    "xls_bytes": 2132480,
                    "xml_bytes": 4308024,
                    "indexed_text_lines": 5889,
                    "line_count_is_not_claimed_as_fully_parsed_record_count": True,
                },
            ],
            "number_of_sample_settlement_dates": 2,
            "historical_1988_to_present_archive_in_sample_directory": False,
            "full_history_requires_subscription": True,
        },
        "schema_and_identity": {
            "delimiter": "pipe",
            "trailing_delimiter_present_in_indexed_preview": True,
            "field_count_from_specification": 16,
            "ticker_is_not_a_unique_issue_key": True,
            "multiple_issue_rows_per_ticker_observed_in_indexed_preview": True,
            "cusip_and_suffix_required_for_issue_level_matching": True,
            "cusip_is_not_a_permanent_effective_dated_security_identifier": True,
            "free_float_zero_means_unavailable": True,
            "revision_flag_R_means_previous_period_revised": True,
            "split_flag_S_means_split_during_current_period": True,
            "full_file_schema_validation_performed": False,
            "exact_unique_issue_count_calculated": False,
            "universe_overlap_calculated": False,
        },
        "availability_and_pit": {
            "scheduled_release_time_et": "14:00",
            "finra_api_available_by_et": "16:40",
            "scheduled_distribution_difference_minutes": 160,
            "same_underlying_finra_rule_4560_reporting_pipeline": True,
            "independent_underlying_smart_money_source": False,
            "sample_directory_modified_timestamp_is_first_receipt": False,
            "original_as_published_vintages_verified": False,
            "revision_chain_verified": False,
            "delisted_security_coverage_verified": False,
            "prospective_first_receipt_capture_would_be_required": True,
            "early_close_execution_rule_required": True,
        },
        "license_and_use": {
            "ice_terms_last_reviewed": "2026-11-10",
            "website_license_limited_to_personal_noncommercial_use": True,
            "terms_exclude_data_mining_robots_or_similar_extraction": True,
            "systematic_retrieval_or_electronic_extraction_requires_prior_written_permission": True,
            "automated_download_authorized": False,
            "automated_parsing_or_feature_extraction_authorized": False,
            "vendor_contact_authorized": False,
            "purchase_authorized": False,
            "decision": "DO_NOT_AUTOMATE_DOWNLOAD_PARSE_OR_FEATURE_EXTRACTION_WITHOUT_WRITTEN_PERMISSION",
        },
        "research_decision": {
            "classification": "CONDITIONAL_SECURITY_LEVEL_SOURCE_SAMPLE_CONFIRMED_BUT_LICENSE_AND_HISTORICAL_PIT_BLOCKED",
            "sample_scope_admitted": True,
            "historical_pit_admitted": False,
            "alpha_admitted": False,
            "backtest_performed": False,
            "purchase_or_vendor_contact": False,
            "production_change": False,
            "f80_frozen": True,
            "holdout_used": False,
        },
        "future_gates_if_written_permission_or_license_is_obtained": [
            "Obtain explicit permission/license covering automated download, storage, parsing, derived features and intended use.",
            "Acquire a representative multi-year historical sample including inactive/delisted issues and original release vintages.",
            "Capture immutable first receipt timestamps, raw hashes, corrections, revision chains and split states.",
            "Build an effective-dated CUSIP-to-security/listing crosswalk and measure overlap with an immutable F80 universe snapshot.",
            "Compare NYSE 14:00 ET receipt with FINRA 16:40 ET receipt using the same report values and next eligible execution prices.",
            "Test short-interest level, change and days-to-cover as crowding/risk features versus frozen LTM/F80 with identical exposure and costs.",
        ],
        "source_urls": [
            "https://www.nyse.com/data-products/catalog/nyse-group-short-interest",
            "https://www.nyse.com/publicdocs/nyse/data/NYSE_Group_Short_Interest_Client_Specification_v1.7.pdf",
            "https://ftp.nyse.com/Reference%20DataSamples/NYSE%20GROUP%20SHORT%20INTEREST/",
            "https://ftp.nyse.com/NYSEGroupConsolidatedShortInterest/",
            "https://www.ice.com/privacy-security-center/terms-of-use",
            "https://developer.finra.org/docs",
        ],
    }


def validate_result(result: dict) -> None:
    assert result["phase"] == 270
    correction = result["scope_correction"]
    assert correction["sample_is_security_level"] is True
    assert correction["sample_is_exchange_level_aggregate_only"] is False
    assert correction["separate_aggregate_report_must_not_be_conflated_with_product_sample"] is True
    assert correction["full_sample_downloaded_or_parsed"] is False

    product = result["official_product"]
    assert product["historical_start_advertised"] == "1988-01"
    assert product["subscription_required_for_full_history"] is True
    assert product["field_count"] == 16
    assert product["release_delivery_time_et"] == "14:00"
    assert product["primary_market_codes"]["M"] == "NYSE Texas"

    files = result["public_sample_directory"]["files"]
    assert [x["settlement_date"] for x in files] == ["2026-07-15", "2026-07-31"]
    assert [x["indexed_text_lines"] for x in files] == [5877, 5889]
    assert all(x["line_count_is_not_claimed_as_fully_parsed_record_count"] for x in files)

    schema = result["schema_and_identity"]
    assert schema["field_count_from_specification"] == 16
    assert schema["ticker_is_not_a_unique_issue_key"] is True
    assert schema["cusip_and_suffix_required_for_issue_level_matching"] is True
    assert schema["free_float_zero_means_unavailable"] is True
    assert schema["full_file_schema_validation_performed"] is False
    assert schema["universe_overlap_calculated"] is False

    pit = result["availability_and_pit"]
    assert pit["scheduled_distribution_difference_minutes"] == 160
    assert pit["same_underlying_finra_rule_4560_reporting_pipeline"] is True
    assert pit["independent_underlying_smart_money_source"] is False
    assert pit["original_as_published_vintages_verified"] is False
    assert pit["prospective_first_receipt_capture_would_be_required"] is True

    terms = result["license_and_use"]
    assert terms["terms_exclude_data_mining_robots_or_similar_extraction"] is True
    assert terms["systematic_retrieval_or_electronic_extraction_requires_prior_written_permission"] is True
    assert terms["automated_download_authorized"] is False
    assert terms["automated_parsing_or_feature_extraction_authorized"] is False

    decision = result["research_decision"]
    assert decision["sample_scope_admitted"] is True
    assert decision["historical_pit_admitted"] is False
    assert decision["alpha_admitted"] is False
    assert decision["backtest_performed"] is False
    assert decision["f80_frozen"] is True
    assert decision["holdout_used"] is False


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = build_result()
    validate_result(result)
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    main()

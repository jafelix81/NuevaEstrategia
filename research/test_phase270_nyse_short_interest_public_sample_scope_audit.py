import unittest

from research.phase270_nyse_short_interest_public_sample_scope_audit import build_result, validate_result


class Phase270NYSEPublicSampleScopeTests(unittest.TestCase):
    def setUp(self):
        self.result = build_result()

    def test_official_sample_is_security_level_not_aggregate_only(self):
        scope = self.result["scope_correction"]
        self.assertTrue(scope["official_product_page_links_to_reference_data_samples"])
        self.assertTrue(scope["sample_is_security_level"])
        self.assertFalse(scope["sample_is_exchange_level_aggregate_only"])
        self.assertFalse(scope["full_sample_downloaded_or_parsed"])

    def test_aggregate_press_release_path_is_separate(self):
        scope = self.result["scope_correction"]
        self.assertNotEqual(scope["sample_directory"], scope["separate_aggregate_report_directory"])
        self.assertTrue(scope["separate_aggregate_report_must_not_be_conflated_with_product_sample"])

    def test_two_public_sample_dates_and_directory_metadata(self):
        files = self.result["public_sample_directory"]["files"]
        self.assertEqual([x["settlement_date"] for x in files], ["2026-07-15", "2026-07-31"])
        self.assertEqual([x["indexed_text_lines"] for x in files], [5877, 5889])
        self.assertEqual([x["txt_bytes"] for x in files], [750412, 751053])

    def test_line_counts_are_not_misrepresented_as_parsed_record_counts(self):
        self.assertTrue(all(x["line_count_is_not_claimed_as_fully_parsed_record_count"] for x in self.result["public_sample_directory"]["files"]))
        self.assertFalse(self.result["schema_and_identity"]["full_file_schema_validation_performed"])

    def test_official_specification_has_sixteen_security_level_fields(self):
        product = self.result["official_product"]
        self.assertEqual(product["field_count"], 16)
        self.assertIn("CUSIP", product["fields"])
        self.assertIn("Current_Short_Interest_Position", product["fields"])

    def test_ticker_is_not_unique_issue_identity(self):
        schema = self.result["schema_and_identity"]
        self.assertTrue(schema["ticker_is_not_a_unique_issue_key"])
        self.assertTrue(schema["multiple_issue_rows_per_ticker_observed_in_indexed_preview"])
        self.assertTrue(schema["cusip_and_suffix_required_for_issue_level_matching"])

    def test_market_scope_discrepancy_is_preserved(self):
        product = self.result["official_product"]
        self.assertIn("NYSE Texas", product["venues_specification_v1_7"])
        self.assertNotIn("NYSE Texas", product["venues_product_page"])

    def test_zero_float_revision_and_split_semantics_are_fail_closed(self):
        schema = self.result["schema_and_identity"]
        self.assertTrue(schema["free_float_zero_means_unavailable"])
        self.assertTrue(schema["revision_flag_R_means_previous_period_revised"])
        self.assertTrue(schema["split_flag_S_means_split_during_current_period"])

    def test_early_release_is_not_independent_underlying_information(self):
        pit = self.result["availability_and_pit"]
        self.assertEqual(pit["scheduled_release_time_et"], "14:00")
        self.assertEqual(pit["finra_api_available_by_et"], "16:40")
        self.assertEqual(pit["scheduled_distribution_difference_minutes"], 160)
        self.assertTrue(pit["same_underlying_finra_rule_4560_reporting_pipeline"])
        self.assertFalse(pit["independent_underlying_smart_money_source"])

    def test_historical_pit_still_requires_vintages_and_first_receipt(self):
        pit = self.result["availability_and_pit"]
        self.assertFalse(pit["sample_directory_modified_timestamp_is_first_receipt"])
        self.assertFalse(pit["original_as_published_vintages_verified"])
        self.assertFalse(pit["revision_chain_verified"])
        self.assertFalse(pit["delisted_security_coverage_verified"])
        self.assertTrue(pit["prospective_first_receipt_capture_would_be_required"])

    def test_ice_terms_block_automated_extraction_without_permission(self):
        terms = self.result["license_and_use"]
        self.assertTrue(terms["website_license_limited_to_personal_noncommercial_use"])
        self.assertTrue(terms["terms_exclude_data_mining_robots_or_similar_extraction"])
        self.assertTrue(terms["systematic_retrieval_or_electronic_extraction_requires_prior_written_permission"])
        self.assertFalse(terms["automated_download_authorized"])
        self.assertFalse(terms["automated_parsing_or_feature_extraction_authorized"])

    def test_no_purchase_contact_or_alpha(self):
        decision = self.result["research_decision"]
        self.assertFalse(decision["alpha_admitted"])
        self.assertFalse(decision["backtest_performed"])
        self.assertFalse(decision["purchase_or_vendor_contact"])

    def test_f80_and_holdout_controls(self):
        decision = self.result["research_decision"]
        self.assertTrue(decision["f80_frozen"])
        self.assertFalse(decision["holdout_used"])
        self.assertFalse(decision["production_change"])

    def test_full_contract(self):
        validate_result(self.result)

    def test_ice_terms_scope_over_ftp_host_is_not_assumed(self):
        terms = self.result["license_and_use"]
        self.assertFalse(terms["ftp_host_explicitly_named_in_ice_terms"])
        self.assertFalse(terms["terms_scope_over_ftp_sample_path_confirmed"])
        self.assertFalse(terms["automated_download_authorized"])
        self.assertFalse(terms["automated_parsing_or_feature_extraction_authorized"])


if __name__ == "__main__":
    unittest.main()

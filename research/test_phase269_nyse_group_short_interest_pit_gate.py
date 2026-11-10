import unittest

from research.phase269_nyse_group_short_interest_pit_gate import build_result, validate_result


class Phase269NYSEGroupShortInterestGateTests(unittest.TestCase):
    def setUp(self):
        self.result = build_result()

    def test_long_history_is_advertised_but_requires_subscription(self):
        product = self.result["product_page"]
        self.assertEqual(product["historical_start"], "1988-01")
        self.assertTrue(product["subscription_required"])
        self.assertFalse(product["price_publicly_verified"])

    def test_release_time_is_two_pm_eastern(self):
        self.assertEqual(self.result["technical_specification"]["delivery_time_et"], "14:00")

    def test_finra_api_publication_time_is_four_forty(self):
        self.assertEqual(self.result["timing_comparison"]["finra_api_available_by_et"], "16:40")

    def test_earlier_distribution_window_is_160_minutes(self):
        timing = self.result["timing_comparison"]
        self.assertEqual(timing["difference_minutes"], 160)
        self.assertTrue(timing["same_day_close_potential_if_actual_receipt_before_actual_xnys_session_close"])
        self.assertIn("actual XNYS close", timing["execution_rule"])
        self.assertIn("early-close", timing["execution_rule"])
        self.assertTrue(timing["actual_first_receipt_timestamp_required"])

    def test_release_dates_match_finra_calendar_examples(self):
        examples = self.result["timing_comparison"]["same_release_date_examples"]
        self.assertEqual(examples[0], {"settlement_date": "2026-07-15", "release_date": "2026-07-24"})
        self.assertEqual(examples[1], {"settlement_date": "2026-07-31", "release_date": "2026-08-11"})

    def test_source_is_not_independent_of_finra(self):
        relation = self.result["source_relationship"]
        self.assertTrue(relation["same_underlying_finra_rule_4560_reporting_pipeline"])
        self.assertFalse(relation["independent_signal_source"])
        self.assertFalse(relation["beneficial_owner_or_account_identity"])

    def test_file_layout_contains_cusip_and_revision_flags(self):
        spec = self.result["technical_specification"]
        self.assertTrue(spec["cusip_present"])
        self.assertIn("CUSIP", spec["file_fields"])
        self.assertEqual(spec["revision_indicator_R"], "previous reporting period revised")
        self.assertEqual(spec["split_indicator_S"], "stock split during current reporting period")

    def test_free_float_zero_is_missing_not_zero(self):
        spec = self.result["technical_specification"]
        self.assertTrue(spec["free_float_zero_means_unavailable"])
        self.assertIn("best-effort", spec["free_float_quality"])

    def test_market_scope_includes_documented_nyse_texas_code(self):
        spec = self.result["technical_specification"]
        self.assertEqual(spec["market_codes"]["M"], "NYSE Texas")
        self.assertIn("NYSE Texas", spec["specification_venues"])

    def test_product_page_and_spec_scope_discrepancy_is_preserved(self):
        pit = self.result["historical_pit_and_coverage"]
        self.assertIn("NYSE Texas", pit["nyse_texas_scope_discrepancy"])

    def test_historical_vintages_and_delisted_coverage_are_unverified(self):
        pit = self.result["historical_pit_and_coverage"]
        self.assertFalse(pit["original_as_published_vintages_verified"])
        self.assertFalse(pit["historical_revision_chain_verified"])
        self.assertFalse(pit["delisted_security_coverage_verified"])

    def test_universe_overlap_is_not_claimed(self):
        pit = self.result["historical_pit_and_coverage"]
        self.assertFalse(pit["repository_universe_snapshot_present"])
        self.assertFalse(pit["universe_overlap_calculated"])

    def test_purchase_and_vendor_contact_are_not_authorized(self):
        commercial = self.result["commercial_and_operational"]
        self.assertFalse(commercial["purchase_authorized"])
        self.assertFalse(commercial["vendor_contact_authorized"])
        self.assertTrue(commercial["sftp_requires_dedicated_source_ip_and_ssh_key"])

    def test_no_historical_pit_or_alpha_is_admitted(self):
        decision = self.result["research_decision"]
        self.assertFalse(decision["historical_pit_admitted"])
        self.assertFalse(decision["alpha_admitted"])
        self.assertFalse(decision["backtest_performed"])

    def test_f80_and_holdout_controls_remain_unchanged(self):
        decision = self.result["research_decision"]
        self.assertTrue(decision["f80_frozen"])
        self.assertFalse(decision["holdout_used"])
        self.assertFalse(decision["production_change"])

    def test_full_contract(self):
        validate_result(self.result)


if __name__ == "__main__":
    unittest.main()

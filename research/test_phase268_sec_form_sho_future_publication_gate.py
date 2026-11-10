import unittest

from research.phase268_sec_form_sho_future_publication_gate import build_result, validate_result


class Phase268FormShoGateTests(unittest.TestCase):
    def setUp(self):
        self.result = build_result()

    def test_compliance_is_deferred_until_2028(self):
        self.assertEqual(self.result["compliance_date"], "2028-01-02")
        self.assertEqual(self.result["current_status"], "TEMPORARY_EXEMPTION_THROUGH_2028-01-02")

    def test_first_reporting_month_and_filing_deadline(self):
        self.assertEqual(self.result["first_reporting_period"], "2028-01")
        self.assertEqual(self.result["first_filing_deadline"], "2028-02-14")

    def test_initial_publication_has_additional_startup_delay(self):
        publication = self.result["initial_publication"]
        self.assertEqual(publication["approximate_start"], "2028-04")
        self.assertFalse(publication["exact_first_publication_date_verified"])
        self.assertIn("three months", publication["rule"])

    def test_public_data_are_security_aggregates_not_manager_positions(self):
        public = self.result["public_data"]
        self.assertEqual(public["aggregation_unit"], "equity security")
        self.assertFalse(public["manager_identity_disclosed"])
        self.assertFalse(public["individual_manager_positions_public"])
        self.assertTrue(public["daily_net_position_activity_by_settlement_date"])

    def test_thresholds_are_not_universe_complete(self):
        thresholds = self.result["reporting_thresholds"]
        self.assertEqual(thresholds["reporting_company"]["monthly_average_gross_short_usd_min"], 10000000)
        self.assertEqual(thresholds["reporting_company"]["or_monthly_average_gross_short_pct_shares_min"], 2.5)
        self.assertEqual(thresholds["non_reporting_company"]["gross_short_usd_min_on_any_settlement_date"], 500000)
        self.assertEqual(thresholds["coverage_status"], "THRESHOLD_CENSORED_NOT_UNIVERSE_COMPLETE")

    def test_publication_lag_and_staleness_are_explicit(self):
        quality = self.result["timeliness_and_quality"]
        self.assertEqual(quality["manager_filing_deadline"], "14 calendar days after each month-end")
        self.assertIn("one calendar month", quality["publication_lag"])
        self.assertTrue(quality["positions_may_be_closed_before_publication"])
        self.assertEqual(quality["sec_historical_form_sh_analysis_average_threshold_duration_days_after_month_end"], 9.85)

    def test_edgar_does_not_verify_economic_accuracy(self):
        quality = self.result["timeliness_and_quality"]
        self.assertTrue(quality["edgar_validation_checks_technical_completeness_not_economic_accuracy"])
        self.assertTrue(quality["amendments_and_restated_filings_possible"])

    def test_no_historical_pit_or_alpha_is_admitted(self):
        pit = self.result["historical_pit"]
        decision = self.result["research_decision"]
        self.assertFalse(pit["public_data_available_as_of_audit"])
        self.assertFalse(pit["strict_historical_pit_admitted"])
        self.assertFalse(decision["historical_alpha_admitted"])
        self.assertFalse(decision["backtest_performed"])

    def test_f80_and_holdout_controls_remain_unchanged(self):
        decision = self.result["research_decision"]
        self.assertTrue(decision["f80_frozen"])
        self.assertFalse(decision["holdout_used"])
        self.assertFalse(decision["production_change"])

    def test_related_securities_lending_rule_is_a_separate_future_gate(self):
        related = self.result["related_rule_10c_1a"]
        self.assertEqual(related["reporting_compliance_date"], "2028-09-28")
        self.assertEqual(related["public_dissemination_compliance_date"], "2029-03-29")

    def test_result_fails_closed_on_inconsistent_state(self):
        altered = dict(self.result)
        altered["research_decision"] = dict(self.result["research_decision"])
        altered["research_decision"]["historical_alpha_admitted"] = True
        with self.assertRaises(AssertionError):
            validate_result(altered)

    def test_full_contract(self):
        validate_result(self.result)


if __name__ == "__main__":
    unittest.main()

import unittest
from research.phase191_nport_short_exposure_pit_feasibility import build_audit, load_evidence


class Phase191NportShortExposureTests(unittest.TestCase):
    def setUp(self):
        self.evidence = load_evidence()
        self.audit = build_audit(self.evidence)

    def test_phase_identity_and_candidate_classification(self):
        self.assertEqual(self.audit["phase"], 191)
        self.assertEqual(self.audit["status"], "CONDITIONAL_REGISTERED_FUND_SHORT_EXPOSURE_CANDIDATE")
        self.assertEqual(self.audit["classification"], "registered_fund_short_exposure_not_universal_institutional_short_interest")

    def test_documented_history_starts_october_2019(self):
        self.assertEqual(self.audit["coverage"]["start"], "2019-10-01")
        self.assertEqual(self.audit["coverage"]["end"], "2026-09-30")

    def test_quarterly_archive_count_is_28(self):
        self.assertEqual(self.audit["coverage"]["quarterly_archives"], 28)

    def test_archive_size_is_arithmetic_only(self):
        self.assertAlmostEqual(self.audit["coverage"]["compressed_archive_total_gb_decimal"], 11.38243)
        self.assertEqual(self.evidence["coverage"]["archive_min_mb"], 228.89)
        self.assertEqual(self.evidence["coverage"]["archive_max_mb"], 690.83)

    def test_public_dataset_is_quarterly(self):
        self.assertEqual(self.audit["coverage"]["publication_frequency"], "quarterly")

    def test_public_dataset_contains_only_disseminated_filings(self):
        self.assertTrue(self.audit["coverage"]["publicly_disseminated_filings_only"])

    def test_as_filed_and_amendment_scope_is_preserved(self):
        self.assertTrue(self.audit["coverage"]["as_filed"])
        self.assertTrue(self.audit["coverage"]["includes_amendments"])
        self.assertIn("NPORT-P/A", self.evidence["coverage"]["filing_types"])

    def test_bulk_submission_table_does_not_supply_acceptance_timestamp(self):
        self.assertFalse(self.audit["pit_gate"]["bulk_submission_table_has_acceptance_timestamp"])
        self.assertIn("FILING_DATE", self.evidence["bulk_dataset_schema"]["submission_table_fields"])
        self.assertNotIn("ACCEPTANCE_DATETIME", self.evidence["bulk_dataset_schema"]["submission_table_fields"])

    def test_report_date_is_not_knowledge_date(self):
        self.assertFalse(self.audit["pit_gate"]["report_date_is_knowledge_date"])

    def test_first_public_receipt_is_not_verified(self):
        self.assertFalse(self.audit["pit_gate"]["first_public_receipt_capture_verified"])

    def test_amendments_must_be_append_only(self):
        self.assertIn("Append every NPORT-P/A", self.audit["pit_gate"]["amendment_rule"])

    def test_non_derivative_short_field_is_explicit(self):
        self.assertEqual(self.evidence["short_position_semantics"]["non_derivative_payoff_profile_field"], "PAYOFF_PROFILE")
        self.assertEqual(self.evidence["short_position_semantics"]["current_values"], ["long", "short", "N/A"])

    def test_value_sign_is_only_a_crosscheck(self):
        self.assertIn("negative", self.evidence["short_position_semantics"]["short_value_sign_crosscheck"])
        self.assertIn("QUARANTINE", self.evidence["short_position_semantics"]["discordant_profile_value_rows"])

    def test_derivatives_are_separate_from_first_direct_short_hypothesis(self):
        self.assertTrue(self.evidence["bulk_dataset_schema"]["derivative_positions_have_separate_item_c11_tables"])
        self.assertFalse(self.audit["short_position_gate"]["derivatives_in_first_hypothesis"])

    def test_series_is_portfolio_unit_not_share_class(self):
        identity = self.evidence["identity_and_universe"]
        self.assertTrue(identity["series_id_is_portfolio_unit"])
        self.assertTrue(identity["multiple_share_classes_can_share_one_series"])
        self.assertTrue(self.evidence["bulk_dataset_schema"]["class_identity_is_not_portfolio_identity"])

    def test_security_identifiers_are_optional(self):
        self.assertTrue(self.evidence["identity_and_universe"]["security_identifiers_are_optional"])
        self.assertIn("ISSUER_CUSIP", self.evidence["bulk_dataset_schema"]["holding_table_fields"])
        self.assertIn("IDENTIFIER_TICKER", self.evidence["bulk_dataset_schema"]["identifiers_table_fields"])

    def test_current_public_regime_is_not_monthly_public(self):
        regime = self.evidence["current_reporting_regime"]
        self.assertEqual(regime["public_frequency"], "quarterly")
        self.assertIn("third month", regime["public_period_rule"])
        self.assertIn("60 days", regime["filing_deadline"])

    def test_2024_monthly_amendments_are_delayed(self):
        regime = self.evidence["current_reporting_regime"]
        self.assertEqual(regime["2024_monthly_amendments_large_funds_compliance"], "2027-11-17")
        self.assertEqual(regime["2024_monthly_amendments_small_funds_compliance"], "2028-05-18")

    def test_2026_proposal_is_not_current_law(self):
        self.assertEqual(self.evidence["current_reporting_regime"]["2026_proposal_status_as_of_audit"], "PROPOSED_NOT_ADOPTED")

    def test_no_short_equity_sample_is_claimed(self):
        self.assertFalse(self.evidence["short_position_semantics"]["sample_short_equity_row_verified"])
        self.assertEqual(self.audit["short_position_gate"]["short_equity_sample"], "NOT_VERIFIED")

    def test_phase27o_long_accumulation_result_is_not_reused(self):
        prior = self.evidence["prior_work"]
        self.assertFalse(prior["phase27o_is_evidence_against_short_position_hypothesis"])
        self.assertFalse(prior["phase27o_oos_results_reused"])

    def test_no_universe_admission_or_alpha_test(self):
        self.assertFalse(self.audit["identity_gate"]["historical_security_crosswalk_admitted"])
        self.assertFalse(self.audit["identity_gate"]["broad_pit_equity_universe_admitted"])
        self.assertEqual(self.audit["admission_gates"]["alpha_test"], "NOT_AUTHORIZED")

    def test_f80_holdout_and_production_controls(self):
        controls = self.audit["controls"]
        self.assertTrue(controls["f80_frozen"])
        self.assertFalse(controls["holdout_used"])
        self.assertFalse(controls["production_changed"])
        self.assertFalse(controls["return_test_run"])
        self.assertFalse(controls["data_purchase"])
        self.assertFalse(controls["vendor_contact"])


if __name__ == "__main__":
    unittest.main()

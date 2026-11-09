import unittest

from research.phase189_sec_short_and_securities_lending_availability import build_audit


class Phase189ShortAndLendingTests(unittest.TestCase):
    def setUp(self):
        self.audit = build_audit()

    def test_as_of_and_status_are_explicit(self):
        self.assertEqual(self.audit["audit_as_of"], "2026-11-07")
        self.assertEqual(self.audit["status"], "FUTURE_PROSPECTIVE_CANDIDATES_ONLY")

    def test_form_sho_first_reporting_period_and_due_date(self):
        sho = self.audit["form_sho"]
        self.assertEqual(sho["compliance_restart_date"], "2028-01-02")
        self.assertEqual(sho["first_reporting_period"], "2028-01")
        self.assertEqual(sho["first_filing_due_date"], "2028-02-14")

    def test_form_sho_thresholds_are_not_conflated(self):
        thresholds = self.audit["form_sho"]["thresholds"]
        self.assertEqual(thresholds["reporting_company"]["monthly_average_gross_short_position_usd_min"], 10_000_000)
        self.assertEqual(thresholds["reporting_company"]["monthly_average_gross_short_position_percent_shares_outstanding_min"], 2.5)
        self.assertEqual(thresholds["non_reporting_company"]["gross_short_position_usd_min"], 500_000)

    def test_form_sho_is_confidential_at_manager_level(self):
        sho = self.audit["form_sho"]
        self.assertTrue(sho["manager_filing_confidential"])
        self.assertFalse(sho["public_manager_identity"])
        self.assertEqual(sho["public_output"], "security_level_aggregates_across_reporting_managers")

    def test_form_sho_is_threshold_censored_and_not_raw_volume(self):
        sho = self.audit["form_sho"]
        self.assertTrue(sho["threshold_censored"])
        self.assertFalse(sho["daily_net_activity_is_raw_short_sale_volume"])
        self.assertFalse(sho["gross_short_position_netted_against_longs_or_derivatives"])

    def test_form_sho_amendment_and_first_publication_uncertainty(self):
        sho = self.audit["form_sho"]
        self.assertIn("amendment_and_restatement", sho["amendment_rule"])
        self.assertFalse(sho["first_publication_date_verified"])
        self.assertFalse(sho["pre_compliance_historical_backfill_verified"])

    def test_slate_reporting_and_public_dates_are_distinct(self):
        slate = self.audit["rule_10c1a_slate"]
        self.assertEqual(slate["covered_person_reporting_date"], "2028-09-28")
        self.assertEqual(slate["required_public_dissemination_date"], "2029-03-29")
        self.assertFalse(slate["first_public_receipt_verified"])

    def test_slate_has_t1_fields_but_t20_loan_size(self):
        slate = self.audit["rule_10c1a_slate"]
        self.assertIn("no_later_than_morning_of_next_business_day", slate["most_public_loan_fields_lag"])
        self.assertEqual(slate["loan_amount_public_lag_business_days"], 20)

    def test_slate_does_not_reveal_counterparty_identity(self):
        slate = self.audit["rule_10c1a_slate"]
        self.assertFalse(slate["lender_borrower_intermediary_legal_identity_public"])
        self.assertFalse(slate["party_regulatory_identifiers_public"])

    def test_slate_aggregate_is_not_directional_and_no_available_to_lend(self):
        slate = self.audit["rule_10c1a_slate"]
        self.assertFalse(slate["daily_aggregate_activity_is_directional_net_change"])
        self.assertFalse(slate["available_to_lend_field_in_final_rule"])

    def test_slate_preexisting_loan_treatment_and_retention(self):
        slate = self.audit["rule_10c1a_slate"]
        self.assertIn("no blanket day-one backfill", slate["pre_existing_loans"])
        self.assertEqual(slate["public_retention_years_min"], 5)
        self.assertFalse(slate["pre_compliance_historical_backfill_verified"])

    def test_sources_remain_separate_from_finra_short_volume_and_interest(self):
        not_interchangeable = self.audit["source_roles"]["not_interchangeable_with"]
        self.assertIn("FINRA daily short-sale volume", not_interchangeable)
        self.assertIn("FINRA settlement short interest", not_interchangeable)

    def test_no_pit_admission_or_alpha_test(self):
        gates = self.audit["pit_and_research_gates"]
        self.assertFalse(gates["form_sho_pit_admitted"])
        self.assertFalse(gates["slate_pit_admitted"])
        self.assertFalse(gates["alpha_test_authorized"])
        self.assertTrue(gates["prospective_first_receipt_capture_required"])
        self.assertFalse(gates["holdout_used"])

    def test_no_purchase_or_production_change_and_f80_stays_frozen(self):
        controls = self.audit["controls"]
        self.assertFalse(controls["raw_data_downloaded"])
        self.assertFalse(controls["sec_finra_requests_made"])
        self.assertFalse(controls["vendor_contact"])
        self.assertFalse(controls["data_purchase"])
        self.assertFalse(controls["terms_accepted"])
        self.assertFalse(controls["production_changed"])
        self.assertTrue(controls["f80_frozen"])
        self.assertFalse(controls["phase20c_reopened"])


if __name__ == "__main__":
    unittest.main()

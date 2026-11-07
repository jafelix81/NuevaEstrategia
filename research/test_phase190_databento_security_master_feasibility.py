import unittest

from research.phase190_databento_security_master_feasibility import build_audit, load_evidence


class Phase190DatabentoSecurityMasterTests(unittest.TestCase):
    def setUp(self):
        self.evidence = load_evidence()
        self.audit = build_audit(self.evidence)

    def test_phase_and_candidate_classification(self):
        self.assertEqual(self.audit["phase"], 190)
        self.assertEqual(self.audit["status"], "CONDITIONAL_TOP_PRIORITY_REFERENCE_DATA_CANDIDATE")
        self.assertEqual(self.evidence["classification"], "foundational_reference_data_not_alpha_signal")

    def test_history_start_is_documented_but_not_independently_validated(self):
        self.assertEqual(self.evidence["history"]["start_date"], "2005-01-01")
        self.assertEqual(self.evidence["research_gates"]["documented_history_2005"], "PASS_DOCUMENTATION_ONLY")

    def test_record_effective_and_created_timestamps_are_distinct(self):
        pit = self.evidence["point_in_time"]
        self.assertIn("last changed", pit["ts_record"])
        self.assertIn("effective", pit["ts_effective"])
        self.assertIn("added", pit["ts_created"])
        self.assertNotEqual(pit["ts_record"], pit["ts_effective"])

    def test_get_range_has_record_and_effective_time_axes(self):
        self.assertEqual(self.evidence["point_in_time"]["get_range_supported_index"], ["ts_effective", "ts_record"])
        self.assertTrue(self.evidence["point_in_time"]["get_last_is_current_state_only"])

    def test_vendor_record_time_is_not_first_customer_receipt(self):
        pit = self.evidence["point_in_time"]
        self.assertFalse(pit["first_customer_receipt_timestamp_provided"])
        self.assertTrue(pit["vendor_record_time_is_not_exchange_publication_time"])
        self.assertTrue(pit["ts_created_is_not_customer_receipt_time"])
        self.assertTrue(pit["prospective_immutable_capture_required"])

    def test_listing_security_and_issuer_keys_are_not_collapsed(self):
        ids = self.evidence["identity_fields"]
        self.assertEqual(ids["listing_id"], "listing-level identity")
        self.assertEqual(ids["security_id"], "security-level identity across listings")
        self.assertEqual(ids["issuer_id"], "issuer-level identity")

    def test_crosswalk_fields_include_cusip_figi_isin_and_cik(self):
        ids = self.evidence["identity_fields"]
        for field in ("us_code", "figi", "isin", "cik"):
            self.assertIn(field, ids)

    def test_us_equity_venue_scope_is_explicit_and_trace_is_not_equity(self):
        venues = self.evidence["us_venues_documented"]
        for venue in ("Nasdaq", "New York Stock Exchange", "NYSE American", "NYSE Arca", "Cboe BZX", "Investors Exchange (IEX)"):
            self.assertIn(venue, venues)
        self.assertTrue(self.evidence["venue_caveats"]["FINRA_TRACE_is_not_equity_listing_venue"])

    def test_instrument_count_scope_conflict_is_preserved(self):
        history = self.evidence["history"]
        self.assertEqual(history["headline_instrument_count"], 860000)
        self.assertEqual(history["body_global_instrument_count"], 310000)
        self.assertFalse(history["instrument_count_scope_reconciled"])

    def test_update_frequency_conflict_is_preserved(self):
        history = self.evidence["history"]
        self.assertEqual(history["dataset_guide_update_frequency"], "weekly")
        self.assertEqual(history["faq_update_frequency"], "four_times_daily")
        self.assertFalse(history["update_frequency_reconciled"])

    def test_pricing_conflict_is_preserved(self):
        pricing = self.evidence["pricing"]
        self.assertEqual(pricing["included_symbols"], 1000) if "included_symbols" in pricing else self.assertEqual(pricing["included_symbols_claimed"], 1000)
        self.assertEqual(pricing["sample_section_extra_usd_per_symbol_month"], 0.5)
        self.assertEqual(pricing["faq_extra_usd_per_symbol_month"], 1.75)
        self.assertFalse(pricing["pricing_reconciled"])

    def test_api_request_limit_is_separate_from_plan_allocation(self):
        self.assertEqual(self.evidence["api"]["max_symbols_per_request"], 2000)
        self.assertEqual(self.evidence["pricing"]["included_symbols_claimed"], 1000)
        self.assertTrue(self.evidence["api"]["plan_symbol_allocation_is_separate_from_request_limit"])

    def test_cost_scenarios_are_arithmetic_only(self):
        scenarios = {x["requested_symbols"]: x for x in self.audit["cost_scenarios"]}
        self.assertEqual(scenarios[5000]["extra_symbols"], 4000)
        self.assertEqual(scenarios[5000]["low_extra_usd_per_month"], 2000.0)
        self.assertEqual(scenarios[5000]["high_extra_usd_per_month"], 7000.0)
        self.assertEqual(scenarios[10000]["extra_symbols"], 9000)
        self.assertEqual(scenarios[10000]["low_extra_usd_per_month"], 4500.0)
        self.assertEqual(scenarios[10000]["high_extra_usd_per_month"], 15750.0)
        self.assertTrue(scenarios[10000]["base_plan_excluded"])
        self.assertFalse(scenarios[10000]["vendor_quote"])

    def test_advertised_sample_is_not_treated_as_downloaded(self):
        sample = self.evidence["sample_advertised"]
        self.assertEqual(sample["us_sample_securities"], 500)
        self.assertEqual(sample["us_sample_records"], 9100)
        self.assertFalse(sample["direct_static_sample_url_resolved"])
        self.assertFalse(sample["sample_downloaded"])

    def test_norgate_is_comparator_not_equivalent_record_time_pit(self):
        norgate = self.evidence["alternatives"]["norgate"]
        self.assertTrue(norgate["delisted_securities_included"])
        self.assertTrue(norgate["historical_index_constituents_included"])
        self.assertTrue(norgate["stable_assetid_claimed"])
        self.assertFalse(norgate["prior_symbol_and_change_date_provided"])
        self.assertFalse(norgate["record_time_pit_archive_equivalent"])

    def test_reference_data_is_not_return_data(self):
        self.assertEqual(self.evidence["research_gates"]["return_series_and_delisting_returns"], "NOT_INCLUDED")
        self.assertFalse(self.audit["admission"]["return_series_included"])

    def test_no_account_request_purchase_or_vendor_contact(self):
        controls = self.evidence["controls"]
        for field in ("account_created", "api_key_used", "api_request_made", "sample_downloaded",
                      "vendor_contact", "data_purchase", "free_credits_used", "terms_accepted"):
            self.assertFalse(controls[field])

    def test_no_alpha_holdout_or_production_change_and_f80_stays_frozen(self):
        controls = self.evidence["controls"]
        self.assertFalse(controls["return_test_run"])
        self.assertFalse(controls["alpha_test_run"])
        self.assertFalse(controls["holdout_used"])
        self.assertFalse(controls["production_changed"])
        self.assertFalse(controls["phase20c_reopened"])
        self.assertTrue(controls["f80_frozen"])
        self.assertFalse(self.audit["admission"]["broad_universe_admitted"])
        self.assertFalse(self.audit["admission"]["alpha_test_authorized"])

    def test_legacy_335_remains_diagnostic_only(self):
        legacy = self.evidence["legacy_universe"]
        self.assertEqual(legacy["ticker_count"], 335)
        self.assertEqual(legacy["status"], "diagnostic_only_not_universe_anchor")


if __name__ == "__main__":
    unittest.main()

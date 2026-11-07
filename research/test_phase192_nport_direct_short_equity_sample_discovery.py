import unittest
from research.phase192_nport_direct_short_equity_sample_discovery import build_audit, load_evidence


class Phase192NportDirectShortDiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.evidence = load_evidence()
        self.audit = build_audit(self.evidence)

    def test_phase_identity_and_status(self):
        self.assertEqual(self.audit["phase"], 192)
        self.assertEqual(self.audit["status"], "DISCOVERY_PASS_RAW_RETRIEVAL_PENDING")

    def test_complete_rows_are_purposive_not_representative(self):
        self.assertGreaterEqual(self.audit["complete_short_row_excerpts"], 8)
        self.assertFalse(self.evidence["controls"]["representative_random_sample"])
        self.assertFalse(self.audit["prevalence_estimated"])

    def test_sample_spans_multiple_historical_years(self):
        self.assertEqual(self.audit["complete_sample_filing_years"], [2020, 2022, 2024, 2025])
        self.assertEqual(self.audit["distinct_complete_accessions"], 4)

    def test_partial_2023_evidence_is_not_counted_as_complete_row(self):
        self.assertEqual(self.audit["partial_filing_discoveries"], 1)
        self.assertTrue(self.evidence["partial_filing_discoveries"][0]["security_name_cusip_value_not_captured"])

    def test_all_complete_rows_match_narrow_direct_short_filter(self):
        for row in self.evidence["complete_short_rows"]:
            self.assertEqual(row["payoff_profile"], "Short")
            self.assertEqual(row["asset_category"], "EC")
            self.assertEqual(row["issuer_category"], "CORP")
            self.assertEqual(row["investment_country"], "US")
            self.assertEqual(row["units"], "NS")
            self.assertLess(row["balance"], 0)
            self.assertLess(row["currency_value_usd"], 0)
            self.assertLess(row["pct_net_assets"], 0)

    def test_all_primary_documents_are_sec_archive_urls(self):
        for row in self.evidence["complete_short_rows"]:
            self.assertTrue(row["source_url"].startswith("https://www.sec.gov/Archives/edgar/data/"))

    def test_directory_times_are_not_promoted_to_acceptance_times(self):
        self.assertGreaterEqual(len(self.evidence["timestamp_observations"]), 3)
        self.assertTrue(all(not x["timezone_and_acceptance_semantics_verified"] for x in self.evidence["timestamp_observations"]))

    def test_raw_xml_retrieval_and_hashes_remain_pending(self):
        c = self.evidence["controls"]
        self.assertFalse(c["raw_xml_files_downloaded"])
        self.assertFalse(c["raw_xml_sha256_verified"])
        self.assertEqual(self.evidence["admission_gates"]["raw_xml_retrieval_and_sha256"], "NOT_VERIFIED")

    def test_no_acceptance_or_first_receipt_claim(self):
        self.assertEqual(self.evidence["admission_gates"]["filing_index_acceptance_timestamp_reconciliation"], "NOT_VERIFIED")
        self.assertEqual(self.evidence["admission_gates"]["amendment_append_only_version_ledger"], "NOT_VERIFIED")

    def test_no_universe_or_alpha_admission(self):
        g = self.evidence["admission_gates"]
        self.assertEqual(g["historical_cusip_to_listing_crosswalk"], "NOT_ESTABLISHED")
        self.assertEqual(g["broad_pit_universe"], "NOT_ADMITTED")
        self.assertEqual(g["alpha_test"], "NOT_AUTHORIZED")
        self.assertFalse(self.audit["alpha_test_authorized"])

    def test_phase27o_long_accumulation_is_not_reused(self):
        self.assertFalse(self.evidence["controls"]["phase27o_long_accumulation_results_reused"])

    def test_f80_holdout_and_production_controls(self):
        c = self.evidence["controls"]
        self.assertTrue(c["f80_frozen"])
        self.assertFalse(c["holdout_used"])
        self.assertFalse(c["production_changed"])
        self.assertFalse(c["return_test_run"])
        self.assertFalse(c["bootstrap_or_loo_run"])
        self.assertFalse(c["data_purchase"])
        self.assertFalse(c["vendor_contact"])

    def test_invalid_positive_short_value_is_rejected(self):
        bad = dict(self.evidence)
        bad["complete_short_rows"] = [dict(self.evidence["complete_short_rows"][0], currency_value_usd=100.0)]
        with self.assertRaises(ValueError):
            build_audit(bad)

    def test_derivative_or_non_us_row_is_rejected(self):
        bad = dict(self.evidence)
        bad["complete_short_rows"] = [dict(self.evidence["complete_short_rows"][0], asset_category="DE")]
        with self.assertRaises(ValueError):
            build_audit(bad)


if __name__ == "__main__":
    unittest.main()

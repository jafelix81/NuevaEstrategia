import unittest

from research.phase464_form144_first_production_capture_audit import audit


class Phase464ProductionCaptureAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = audit()

    def test_migrated_ledger_shape_and_committed_rows(self):
        self.assertEqual(self.result["event_header_fields"], 43)
        # Ledgers are append-only and have continued to grow since Phase 464.
        # Assert the audited first-production snapshot is still present rather
        # than freezing the mutable repository-wide row totals.
        self.assertGreaterEqual(self.result["event_rows_total"], 106)
        self.assertGreaterEqual(self.result["feed_observation_rows_total"], 388)
        self.assertGreaterEqual(self.result["acceptance_reconciliation_rows_total"], 106)
        self.assertGreaterEqual(self.result["event_rows_total"], self.result["new_event_rows"])
        self.assertGreaterEqual(
            self.result["acceptance_reconciliation_rows_total"],
            self.result["acceptance_reconciliations_added"],
        )

    def test_first_production_poll_persisted_54_new_filing_versions(self):
        self.assertEqual(self.result["new_event_rows"], 54)
        self.assertEqual(self.result["new_event_rows_by_feed"], {"144": 50, "144A": 4})
        self.assertEqual(self.result["new_event_xml_resolved"], 54)
        self.assertTrue(self.result["all_new_rows_cross_feed_provenance_complete"])

    def test_feed_observation_ledger_preserves_all_58_endpoint_observations(self):
        self.assertEqual(self.result["feed_observation_rows_appended"], 58)
        self.assertEqual(self.result["feed_observation_rows_by_feed"], {"144": 50, "144A": 8})

    def test_capped_144_feed_is_quarantined(self):
        self.assertTrue(self.result["feed_144_rows_all_gap_quarantined"])
        self.assertEqual(self.result["candidate_matches_on_gap_contaminated_144_feed"], 14)

    def test_only_four_bounded_144a_versions_are_raw_research_observations(self):
        self.assertEqual(self.result["research_observation_eligible_rows"], 4)
        self.assertTrue(self.result["eligible_rows_all_from_144a_feed"])
        self.assertTrue(self.result["feed_144a_rows_all_bounded"])
        self.assertTrue(self.result["feed_144a_rows_all_amendment_linked"])
        self.assertTrue(self.result["eligible_rows_all_parent_linked"])

    def test_bounded_amendments_have_no_candidate_universe_match(self):
        self.assertEqual(self.result["eligible_candidate_matches"], 0)
        self.assertEqual(self.result["new_event_candidate_matches"], 14)

    def test_all_54_new_versions_have_acceptance_reconciliation(self):
        self.assertEqual(self.result["acceptance_reconciliations_added"], 54)
        self.assertEqual(self.result["acceptance_reconciliation_unresolved"], 0)
        self.assertTrue(self.result["feed_updated_equals_acceptance_all_rows"])
        self.assertEqual(self.result["receipt_lag_seconds_min"], 98)
        self.assertEqual(self.result["receipt_lag_seconds_max"], 101348)
        self.assertEqual(self.result["eligible_receipt_lag_seconds_min"], 83338)
        self.assertEqual(self.result["eligible_receipt_lag_seconds_max"], 101348)

    def test_no_signal_or_public_availability_promotion(self):
        self.assertTrue(self.result["all_new_rows_signal_ineligible"])
        self.assertTrue(self.result["all_new_rows_public_availability_uncertified"])
        self.assertTrue(self.result["all_new_rows_historical_f80_membership_unverified"])
        self.assertTrue(self.result["all_new_rows_intraday_unauthorized"])
        self.assertEqual(self.result["eligible_rows_signal_eligible"], 0)
        self.assertEqual(self.result["eligible_rows_public_availability_certified"], 0)

    def test_current_state_preserves_successful_anchor_without_freezing_latest_attempt(self):
        self.assertIn(self.result["state_poll_status"], {"complete", "partial", "failed"})
        self.assertGreaterEqual(self.result["state_complete_poll_count"], 10)
        self.assertTrue(self.result["state_last_poll_attempt_run_id"])
        self.assertTrue(self.result["state_last_successful_poll_run_id"])
        self.assertTrue(self.result["state_last_successful_poll_utc"])
        self.assertEqual(set(self.result["state_gap_by_feed"]), {"144", "144A"})
        self.assertTrue(all(isinstance(value, bool) for value in self.result["state_gap_by_feed"].values()))


if __name__ == "__main__":
    unittest.main()

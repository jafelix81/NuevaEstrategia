import json
import unittest
from pathlib import Path

from research.phase267_finra_short_interest_pit_pagination_audit import build_result

INPUT = Path(__file__).resolve().with_name("phase267_finra_short_interest_audit_input.json")


class Phase267FinraShortInterestAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(INPUT.read_text(encoding="utf-8"))
        cls.result = build_result(cls.data)

    def test_finra_sync_cap_exposes_unverified_first_page_only_retrieval(self):
        audit = self.result["retrieval_audit"]
        self.assertEqual(audit["successful_queries"], 55)
        self.assertEqual(audit["documented_sync_max"], 5000)
        self.assertEqual(audit["requested_limit"], 10000)
        self.assertTrue(audit["all_successful_responses_at_sync_cap"])
        self.assertTrue(audit["old_loop_breaks_after_first_capped_page"])
        self.assertEqual(audit["coverage_status"], "UNVERIFIED_FIRST_PAGE_ONLY")
        self.assertIn("NOT_PROVEN", audit["truncation_claim"])

    def test_weekend_only_settlement_schedule_misses_xnys_holidays(self):
        audit = self.result["settlement_calendar_audit"]
        self.assertEqual(audit["wrong_settlement_queries"], 2)
        self.assertEqual(
            audit["mismatches"],
            [
                {"queried_date": "2024-01-15", "expected_xnys_settlement": "2024-01-12"},
                {"queried_date": "2024-03-29", "expected_xnys_settlement": "2024-03-28"},
            ],
        )

    def test_bday_knowledge_date_is_early_on_holiday_cycles(self):
        audit = self.result["publication_and_execution_audit"]
        self.assertEqual(audit["successful_cycles"], 55)
        self.assertEqual(audit["old_knowledge_date_early_cycles"], 19)
        self.assertEqual(audit["old_knowledge_date_equal_cycles"], 36)
        self.assertEqual(audit["old_knowledge_date_late_cycles"], 0)

    def test_every_training_price_anchor_precedes_safe_post_publication_entry(self):
        audit = self.result["publication_and_execution_audit"]
        self.assertEqual(audit["training_price_anchor_lookahead_cycles"], 55)
        self.assertEqual(audit["old_entry_early_by_xnys_sessions_distribution"], {"1": 38, "2": 17})
        self.assertEqual(audit["publication_time_et"], "16:40")
        self.assertEqual(audit["regular_session_close_et"], "16:00")

    def test_phase25c_november_25_signal_uses_not_yet_published_settlement(self):
        entries = self.result["signal_date_availability"]["phase25c"]
        affected = [x for x in entries if x["direct_oos_availability_mismatch"]]
        self.assertEqual(len(affected), 1)
        self.assertEqual(affected[0]["signal_date"], "2022-11-25")
        self.assertEqual(affected[0]["old_latest_settlement"], "2022-11-15")
        self.assertEqual(affected[0]["official_latest_settlement"], "2022-10-31")
        impact = self.result["phase25c_november_2022_direct_oos_issue"]
        self.assertEqual(impact["old_available_snapshot_dates"], 11)
        self.assertEqual(impact["corrected_available_snapshot_dates"], 10)
        self.assertEqual(impact["latest_ticker_rows_changed"], 89)

    def test_phase25b_and_25c_are_not_independent_replications(self):
        audit = self.result["original_diagnostics_not_admissible"]
        self.assertFalse(audit["independent_replication"])
        self.assertEqual(
            audit["shared_feature_file_sha256"],
            self.data["source"]["shared_feature_file_sha256"],
        )

    def test_revision_flags_confirm_historical_vintage_risk(self):
        audit = self.result["revision_vintage_audit"]
        self.assertEqual(audit["revision_flag_rows"], 102)
        self.assertEqual(audit["unique_tickers_with_revision_flag"], 63)
        self.assertEqual(audit["settlement_dates_with_revision_flag"], 9)
        self.assertFalse(audit["historical_original_vintage_available"])

    def test_no_alpha_or_f80_promotion(self):
        decision = self.result["decision"]
        self.assertFalse(decision["phase25b_valid_for_pit_inference"])
        self.assertFalse(decision["phase25c_valid_for_pit_inference"])
        self.assertFalse(decision["historical_alpha_admitted"])
        self.assertFalse(decision["historical_coverage_admitted"])
        self.assertTrue(decision["prospective_capture_candidate"])
        self.assertTrue(decision["f80_frozen"])
        self.assertFalse(decision["holdout_used"])


if __name__ == "__main__":
    unittest.main()

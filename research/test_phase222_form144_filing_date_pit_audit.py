import json
import unittest
from research.phase222_form144_filing_date_pit_audit import (
    EVIDENCE, build_audit, next_session_after
)


class Phase222Form144DailyPitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        cls.audit = build_audit(cls.evidence)

    def test_phase_admits_daily_clock_only(self):
        self.assertTrue(self.audit["daily_pit_clock_admitted"])
        self.assertFalse(self.audit["full_signal_panel_admitted"])
        self.assertFalse(self.audit["alpha_test_authorized"])

    def test_same_day_is_never_eligible(self):
        sessions = ["2026-07-01", "2026-07-02", "2026-07-06"]
        self.assertEqual(next_session_after("2026-07-01", sessions), "2026-07-02")

    def test_weekend_gap_uses_next_regular_session(self):
        sessions = ["2026-07-02", "2026-07-06", "2026-07-07"]
        self.assertEqual(next_session_after("2026-07-03", sessions), "2026-07-06")

    def test_market_holiday_gap_uses_next_session(self):
        sessions = ["2026-12-24", "2026-12-28", "2026-12-29"]
        self.assertEqual(next_session_after("2026-12-24", sessions), "2026-12-28")

    def test_early_close_is_still_a_scheduled_regular_session(self):
        sessions = ["2026-07-02", "2026-07-03", "2026-07-06"]
        self.assertEqual(next_session_after("2026-07-02", sessions), "2026-07-03")

    def test_out_of_range_calendar_fails_closed(self):
        with self.assertRaises(ValueError):
            next_session_after("2027-01-01", ["2026-12-29", "2026-12-30"])

    def test_acceptance_pilot_is_five_of_five(self):
        p = self.evidence["acceptance_pilot"]
        self.assertEqual(p["filing_date_matches_acceptance_date"], 5)
        self.assertEqual(p["next_session_matches"], 5)

    def test_notice_date_is_not_knowledge_clock(self):
        p = self.evidence["panel"]
        self.assertEqual(p["notice_date_differs_from_filing_date_rows"], 168)
        self.assertNotEqual(p["notice_date_differs_from_filing_date_rows"], 0)

    def test_amendments_are_separate_vintages(self):
        p = self.evidence["panel"]
        self.assertEqual(p["forms"]["144/A"], 196)
        self.assertEqual(p["amendments_with_previous_accession"], 196)

    def test_historical_universe_gate_remains_closed(self):
        self.assertEqual(self.evidence["panel"]["current_ticker_mapping_denominator"], 335)
        self.assertFalse(self.evidence["decision"]["full_signal_panel_admitted"])

    def test_f80_and_holdout_controls(self):
        self.assertTrue(self.audit["f80_frozen"])
        self.assertFalse(self.audit["holdout_used"])
        self.assertEqual(self.evidence["decision"]["legacy_holdout"], "CONSUMED_NOT_PRISTINE")


if __name__ == "__main__":
    unittest.main()

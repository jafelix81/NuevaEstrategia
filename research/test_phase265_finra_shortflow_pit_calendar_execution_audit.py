import unittest

from research.phase265_finra_shortflow_pit_calendar_execution_audit import (
    build_result,
    label_is_mature,
    next_xnys_session_after,
    session_coverage,
    strict_pit_gate,
)

class Phase265FinraShortflowPITCalendarTests(unittest.TestCase):
    def test_explicit_session_calendar_excludes_weekend_and_holiday_dates(self):
        result = session_coverage(
            ["2026-06-12", "2026-06-15", "2026-06-16"],
            ["2026-06-12", "2026-06-13", "2026-06-15", "2026-06-16"],
        )
        self.assertEqual(result["expected_sessions"], 3)
        self.assertEqual(result["observed_expected_sessions"], 3)
        self.assertEqual(result["unexpected_observed_dates"], ["2026-06-13"])
        self.assertEqual(result["coverage_rate"], 1.0)

    def test_missing_expected_session_is_counted_as_missing(self):
        result = session_coverage(
            ["2026-06-12", "2026-06-15", "2026-06-16"],
            ["2026-06-12", "2026-06-16"],
        )
        self.assertEqual(result["missing_expected_sessions"], ["2026-06-15"])
        self.assertAlmostEqual(result["coverage_rate"], 2 / 3)

    def test_empty_calendar_has_unknown_coverage(self):
        result = session_coverage([], [])
        self.assertIsNone(result["coverage_rate"])

    def test_duplicate_expected_sessions_fail_closed(self):
        with self.assertRaises(ValueError):
            session_coverage(["2026-06-12", "2026-06-12"], [])

    def test_duplicate_observed_dates_fail_closed(self):
        with self.assertRaises(ValueError):
            session_coverage(["2026-06-12"], ["2026-06-12", "2026-06-12"])

    def test_calendar_date_success_ratio_is_not_market_session_coverage(self):
        result = build_result()
        sample = result["sample"]
        self.assertAlmostEqual(sample["calendar_date_success_ratio"], 1382 / 2020, places=6)
        self.assertFalse(sample["calendar_date_success_ratio_is_market_session_coverage"])
        self.assertIsNone(sample["xnys_session_coverage"])

    def test_next_session_is_strictly_after_trade_date(self):
        self.assertEqual(
            next_xnys_session_after("2026-06-12", ["2026-06-12", "2026-06-15", "2026-06-16"]),
            "2026-06-15",
        )

    def test_next_session_returns_none_when_calendar_has_no_later_session(self):
        self.assertIsNone(next_xnys_session_after("2026-06-16", ["2026-06-12", "2026-06-15", "2026-06-16"]))

    def test_duplicate_sessions_in_execution_calendar_fail_closed(self):
        with self.assertRaises(ValueError):
            next_xnys_session_after("2026-06-12", ["2026-06-15", "2026-06-15"])

    def test_training_label_must_end_before_test_entry(self):
        self.assertTrue(label_is_mature("2026-06-12", "2026-06-15"))

    def test_label_ending_on_test_entry_is_not_mature(self):
        self.assertFalse(label_is_mature("2026-06-15", "2026-06-15"))

    def test_label_ending_after_test_entry_is_not_mature(self):
        self.assertFalse(label_is_mature("2026-06-16", "2026-06-15"))

    def test_missing_first_receipt_blocks_pit(self):
        gate = strict_pit_gate(None, "2026-06-15T20:00:00Z", "a" * 64, True)
        self.assertFalse(gate["admitted"])
        self.assertIn("MISSING_FIRST_RECEIPT_TIMESTAMP", gate["reasons"])

    def test_receipt_at_or_after_entry_blocks_pit(self):
        gate = strict_pit_gate(
            "2026-06-15T20:00:00Z",
            "2026-06-15T20:00:00Z",
            "a" * 64,
            True,
        )
        self.assertFalse(gate["admitted"])
        self.assertIn("RECEIPT_NOT_STRICTLY_BEFORE_ENTRY", gate["reasons"])

    def test_receipt_after_entry_blocks_pit(self):
        gate = strict_pit_gate(
            "2026-06-15T20:01:00Z",
            "2026-06-15T20:00:00Z",
            "a" * 64,
            True,
        )
        self.assertFalse(gate["admitted"])

    def test_raw_hash_is_required(self):
        gate = strict_pit_gate(
            "2026-06-15T19:00:00Z",
            "2026-06-15T20:00:00Z",
            None,
            True,
        )
        self.assertFalse(gate["admitted"])
        self.assertIn("MISSING_OR_INVALID_RAW_SHA256", gate["reasons"])

    def test_immutable_vintage_is_required(self):
        gate = strict_pit_gate(
            "2026-06-15T19:00:00Z",
            "2026-06-15T20:00:00Z",
            "a" * 64,
            False,
        )
        self.assertFalse(gate["admitted"])
        self.assertIn("IMMUTABLE_VINTAGE_NOT_PRESERVED", gate["reasons"])

    def test_complete_timestamp_hash_and_vintage_can_pass(self):
        gate = strict_pit_gate(
            "2026-06-15T19:00:00Z",
            "2026-06-15T20:00:00Z",
            "a" * 64,
            True,
        )
        self.assertTrue(gate["admitted"])
        self.assertEqual(gate["reasons"], [])

    def test_timezone_naive_timestamp_is_rejected(self):
        gate = strict_pit_gate(
            "2026-06-15T19:00:00",
            "2026-06-15T20:00:00Z",
            "a" * 64,
            True,
        )
        self.assertFalse(gate["admitted"])
        self.assertIn("INVALID_FIRST_RECEIPT_TIMESTAMP", gate["reasons"])

    def test_legacy_phase20c_is_not_strict_pit(self):
        result = build_result()
        self.assertFalse(result["timing_and_vintages"]["strict_pit_admitted"])
        self.assertTrue(result["timing_and_vintages"]["feature_uses_signal_date_finra_row"])
        self.assertTrue(result["timing_and_vintages"]["entry_return_denominator_uses_same_signal_date_close"])

    def test_no_holdout_or_f80_change(self):
        result = build_result()
        self.assertFalse(result["decision"]["holdout_used"])
        self.assertTrue(result["decision"]["f80_frozen"])
        self.assertFalse(result["decision"]["production_changed"])
        self.assertFalse(result["decision"]["universe_changed"])
        self.assertFalse(result["decision"]["capital_changed"])

if __name__ == "__main__":
    unittest.main()

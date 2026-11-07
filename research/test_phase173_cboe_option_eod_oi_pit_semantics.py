import unittest

from research.phase173_cboe_option_eod_oi_pit_semantics import (
    OI_SEMANTICS,
    build_audit,
    conservative_history_floor,
    feature_knowledge_time,
)

class Phase173Tests(unittest.TestCase):
    def test_conservative_history_floor_uses_later_conflicting_start(self):
        self.assertEqual(conservative_history_floor("2012-01", "2010-01"), "2012-01")
        self.assertEqual(conservative_history_floor("2011-01", "2012-01"), "2012-01")

    def test_invalid_history_month_is_rejected(self):
        with self.assertRaises(ValueError):
            conservative_history_floor("2012-13", "2010-01")

    def test_oi_is_prior_night_occ_eod_at_start_of_quote_date(self):
        audit = build_audit()
        self.assertEqual(OI_SEMANTICS, "PREVIOUS_NIGHT_OCC_EOD_AT_START_OF_QUOTE_DATE")
        self.assertTrue(audit["oi_static_during_session"])
        self.assertFalse(audit["oi_is_same_day_close_measure"])

    def test_knowledge_time_is_latest_of_all_required_sources(self):
        result = feature_knowledge_time(
            "2026-11-06T20:00:00-05:00",
            "2026-11-07T01:30:00Z",
            "2026-11-06T22:00:00Z",
        )
        self.assertTrue(result["eligible"])
        self.assertEqual(result["knowledge_time_utc"], "2026-11-07T01:30:00+00:00")

    def test_missing_file_receipt_blocks_pit(self):
        result = feature_knowledge_time(
            "2026-11-06T20:00:00Z", None, "2026-11-06T21:00:00Z"
        )
        self.assertFalse(result["eligible"])
        self.assertEqual(result["reason"], "MISSING_REQUIRED_AVAILABILITY_TIMESTAMP")

    def test_naive_timestamp_is_rejected(self):
        with self.assertRaises(ValueError):
            feature_knowledge_time(
                "2026-11-06T20:00:00", "2026-11-07T01:30:00Z",
                "2026-11-06T22:00:00Z"
            )

    def test_four_symbol_sample_does_not_claim_broad_universe_coverage(self):
        audit = build_audit()
        self.assertEqual(len(audit["sample"]["underlyings"]), 4)
        self.assertEqual(audit["sample"]["legacy_335_overlap"], 1)
        self.assertFalse(audit["sample"]["representative_universe_sample"])
        self.assertEqual(audit["broad_pit_universe_coverage"], "NOT_TESTED")

    def test_phase_is_not_alpha_or_pit_admitted(self):
        audit = build_audit()
        self.assertFalse(audit["pit_admission"])
        self.assertFalse(audit["alpha_admission"])
        self.assertFalse(audit["forward_returns_tested"])
        self.assertFalse(audit["final_holdout_used"])
        self.assertFalse(audit["f80_changed"])

if __name__ == "__main__":
    unittest.main()

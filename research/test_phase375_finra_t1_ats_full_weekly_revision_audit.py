import unittest

from research.phase375_finra_t1_ats_full_weekly_revision_audit import (
    validate_weekly_anchors, hash_key, summarize_partitions,
)


class Phase375Tests(unittest.TestCase):
    def test_full_historical_inventory_is_209_consecutive_weeks(self):
        weeks = []
        from datetime import date, timedelta
        current = date(2021, 11, 15)
        for _ in range(209):
            weeks.append(current.isoformat())
            current += timedelta(days=7)
        result = validate_weekly_anchors(weeks)
        self.assertTrue(result["consecutive"])
        self.assertEqual(result["count"], 209)
        self.assertEqual(result["first"], "2021-11-15")
        self.assertEqual(result["last"], "2025-11-10")

    def test_missing_week_fails_closed(self):
        result = validate_weekly_anchors(["2021-11-15", "2021-11-29", "2021-12-06"])
        self.assertFalse(result["consecutive"])
        self.assertEqual(result["nonweekly_gaps"][0]["gap_days"], 14)

    def test_duplicate_week_fails_closed(self):
        result = validate_weekly_anchors(["2021-11-15", "2021-11-15"])
        self.assertFalse(result["consecutive"])
        self.assertEqual(result["duplicates"], 1)

    def test_hash_is_deterministic_and_case_normalized(self):
        self.assertEqual(hash_key("mpid-1"), hash_key("MPID-1"))
        self.assertEqual(len(hash_key("MPID-1")), 64)

    def test_summary_uses_correct_unique_union_counts(self):
        partitions = [
            {
                "rows": 1000,
                "pages": 2,
                "bridge_mapped_symbols": 100,
                "revision_stable_concentration_symbols": 90,
                "total_aggregate_shares_mapped": 1000,
                "revision_stable_concentration_shares": 900,
                "union_symbols": 100,
                "revision_stable_symbols": 90,
                "revised_symbols": 10,
                "symbol_bridge_gate": "PASS",
                "stable_concentration_gate": "PASS",
                "publication_schedule_review_symbols": 0,
            },
            {
                "rows": 2000,
                "pages": 4,
                "bridge_mapped_symbols": 200,
                "revision_stable_concentration_symbols": 180,
                "total_aggregate_shares_mapped": 4000,
                "revision_stable_concentration_shares": 3600,
                "union_symbols": 200,
                "revision_stable_symbols": 180,
                "revised_symbols": 20,
                "symbol_bridge_gate": "PASS",
                "stable_concentration_gate": "PASS",
                "publication_schedule_review_symbols": 0,
            },
        ]
        result = summarize_partitions(partitions, {"a", "b"}, {"x", "y", "z"})
        self.assertEqual(result["symbol_week_bridge_mapped"], 300)
        self.assertEqual(result["revision_stable_concentration_symbol_week_groups"], 270)
        self.assertEqual(result["revision_stable_concentration_symbol_coverage_pct"], 90.0)
        self.assertEqual(result["revision_stable_share_volume_coverage_pct"], 90.0)
        self.assertEqual(result["unique_symbols_union_count"], 2)
        self.assertEqual(result["unique_participant_keys_union_count"], 3)


if __name__ == "__main__":
    unittest.main()

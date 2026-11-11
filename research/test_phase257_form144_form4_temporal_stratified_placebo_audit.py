import random
import unittest
from datetime import date, timedelta
from decimal import Decimal

from research.phase257_form144_form4_temporal_stratified_placebo_audit import (
    STRATA, build_temporal_groups, holm_adjust, mutable_indices,
    permute_lags_in_groups, run_stratified_placebo, temporal_group_key,
)


def block(issuer, owner, filing, lag, accession):
    return {"issuer": issuer, "owner": owner, "filing": filing,
            "date": filing - timedelta(days=lag), "lag": lag,
            "accession": accession, "shares": Decimal("100")}


class Phase257TemporalStratificationTests(unittest.TestCase):
    def setUp(self):
        self.blocks = [
            block("1", "ALICE", date(2025, 1, 10), 1, "A1"),
            block("1", "ALICE", date(2025, 1, 15), 2, "A2"),
            block("1", "ALICE", date(2025, 2, 10), 0, "A3"),
            block("1", "BOB", date(2025, 1, 10), 1, "B1"),
            block("1", "BOB", date(2025, 1, 15), 1, "B2"),
            block("2", "ALICE", date(2025, 1, 10), 3, "C1"),
        ]

    def test_supported_strata_are_explicit(self):
        self.assertEqual(STRATA, ("issuer_owner", "issuer_owner_month", "issuer_owner_iso_week"))

    def test_issuer_owner_key_ignores_time(self):
        self.assertEqual(
            temporal_group_key(self.blocks[0], "issuer_owner"),
            temporal_group_key(self.blocks[2], "issuer_owner"),
        )

    def test_month_stratum_splits_months(self):
        self.assertNotEqual(
            temporal_group_key(self.blocks[0], "issuer_owner_month"),
            temporal_group_key(self.blocks[2], "issuer_owner_month"),
        )
        self.assertGreater(len(build_temporal_groups(self.blocks, "issuer_owner_month")), 0)

    def test_iso_week_uses_iso_year_and_week(self):
        x = block("1", "ALICE", date(2021, 1, 1), 1, "X")
        y = block("1", "ALICE", date(2021, 1, 4), 1, "Y")
        self.assertNotEqual(
            temporal_group_key(x, "issuer_owner_iso_week"),
            temporal_group_key(y, "issuer_owner_iso_week"),
        )

    def test_only_groups_with_distinct_lags_are_mutable(self):
        groups = build_temporal_groups(self.blocks, "issuer_owner")
        mutable, count = mutable_indices(groups, self.blocks)
        self.assertNotIn(3, mutable)
        self.assertNotIn(4, mutable)
        self.assertIn(0, mutable)
        self.assertIn(1, mutable)
        self.assertIn(2, mutable)
        self.assertEqual(count, 1)

    def test_permutation_preserves_lag_multiset_and_filing_dates(self):
        groups = build_temporal_groups(self.blocks, "issuer_owner")
        dates, lags = permute_lags_in_groups(self.blocks, groups, random.Random(11))
        self.assertEqual(sorted(lags[:3]), sorted(b["lag"] for b in self.blocks[:3]))
        for i, lag in enumerate(lags):
            self.assertEqual(dates[i], self.blocks[i]["filing"] - timedelta(days=lag))
            self.assertGreaterEqual(lag, 0)
            self.assertLessEqual(lag, 4)

    def test_same_lag_group_is_unchanged(self):
        groups = build_temporal_groups(self.blocks, "issuer_owner")
        dates, lags = permute_lags_in_groups(self.blocks, groups, random.Random(99))
        self.assertEqual(lags[3:5], [1, 1])
        self.assertEqual(dates[3:5], [self.blocks[3]["date"], self.blocks[4]["date"]])

    def test_permutation_is_deterministic(self):
        groups = build_temporal_groups(self.blocks, "issuer_owner_month")
        a = permute_lags_in_groups(self.blocks, groups, random.Random(257))
        b = permute_lags_in_groups(self.blocks, groups, random.Random(257))
        self.assertEqual(a, b)

    def test_invalid_lag_fails_closed(self):
        bad = [dict(self.blocks[0], lag=5), self.blocks[1]]
        groups = build_temporal_groups(bad, "issuer_owner")
        with self.assertRaises(ValueError):
            permute_lags_in_groups(bad, groups, random.Random(1))

    def test_filing_date_must_be_valid(self):
        bad = [dict(self.blocks[0], filing=None)]
        with self.assertRaises(ValueError):
            build_temporal_groups(bad, "issuer_owner")

    def test_unknown_stratum_fails_closed(self):
        with self.assertRaises(ValueError):
            temporal_group_key(self.blocks[0], "issuer_owner_quarter")

    def test_no_genuinely_permutable_groups_is_reported_not_forced(self):
        same_lag = [
            block("1", "ALICE", date(2025, 1, 10), 1, "S1"),
            block("1", "ALICE", date(2025, 1, 15), 1, "S2"),
        ]
        result = run_stratified_placebo([], same_lag, [], "issuer_owner", reps=100, seed=1)
        self.assertEqual(result["status"], "INSUFFICIENT_PERMUTABLE_GROUPS")
        self.assertEqual(result["replicates"], 0)
        self.assertIsNone(result["empirical_tail_plus_one"])

    def test_holm_adjustment_is_monotone_and_bounded(self):
        adjusted = holm_adjust({"a": 0.001, "b": 0.01, "c": 0.04})
        self.assertEqual(adjusted["a"], 0.003)
        self.assertEqual(adjusted["b"], 0.02)
        self.assertEqual(adjusted["c"], 0.04)
        self.assertTrue(all(0 <= x <= 1 for x in adjusted.values()))

    def test_holm_adjustment_preserves_ties(self):
        adjusted = holm_adjust({"a": 0.001, "b": 0.001, "c": 0.001})
        self.assertEqual(adjusted, {"a": 0.003, "b": 0.003, "c": 0.003})


if __name__ == "__main__":
    unittest.main()

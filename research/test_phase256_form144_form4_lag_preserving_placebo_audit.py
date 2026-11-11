import random
import unittest
from datetime import date, timedelta
from decimal import Decimal

from research.phase256_form144_form4_lag_preserving_placebo_audit import (
    build_groups,
    count_unique_mutable_matches_fast,
    count_unique_mutable_matches_slow,
    measure_raw_date_shuffle_invalidity,
    permute_lags_within_owner_groups,
    summarize_counts,
)


class Phase256LagPreservingPlaceboTests(unittest.TestCase):
    def setUp(self):
        self.blocks = [
            {"issuer": "1", "owner": "ALICE", "accession": "A1", "date": date(2025, 1, 8),
             "filing": date(2025, 1, 10), "lag": 2, "shares": Decimal("10")},
            {"issuer": "1", "owner": "ALICE", "accession": "A2", "date": date(2025, 1, 9),
             "filing": date(2025, 1, 10), "lag": 1, "shares": Decimal("20")},
            {"issuer": "1", "owner": "BOB", "accession": "B1", "date": date(2025, 1, 7),
             "filing": date(2025, 1, 10), "lag": 3, "shares": Decimal("30")},
        ]
        self.tranches = [
            {"accession": "T1", "idx": "1", "issuer": "1", "seller": "ALICE",
             "date": date(2025, 1, 8), "units": Decimal("10")},
            {"accession": "T2", "idx": "1", "issuer": "1", "seller": "ALICE",
             "date": date(2025, 1, 9), "units": Decimal("20")},
        ]

    def test_lag_permutation_preserves_group_multiset_and_eligibility(self):
        groups = build_groups(self.blocks)
        dates, lags = permute_lags_within_owner_groups(self.blocks, groups, random.Random(11))
        self.assertEqual(sorted(lags[:2]), [1, 2])
        self.assertEqual(lags[2], 3)
        for i, lag in enumerate(lags):
            self.assertEqual(dates[i], self.blocks[i]["filing"] - timedelta(days=lag))
            self.assertGreaterEqual(lag, 0)
            self.assertLessEqual(lag, 4)
            self.assertLessEqual(dates[i], self.blocks[i]["filing"])

    def test_lag_permutation_is_deterministic(self):
        groups = build_groups(self.blocks)
        a = permute_lags_within_owner_groups(self.blocks, groups, random.Random(99))
        b = permute_lags_within_owner_groups(self.blocks, groups, random.Random(99))
        self.assertEqual(a, b)

    def test_fast_match_count_equals_reference(self):
        owners = [b["owner"] for b in self.blocks]
        dates = [b["date"] for b in self.blocks]
        shares = [b["shares"] for b in self.blocks]
        mutable = {0, 1}
        fast = count_unique_mutable_matches_fast(self.tranches, self.blocks, owners, dates, shares, mutable)
        slow = count_unique_mutable_matches_slow(self.tranches, self.blocks, owners, dates, shares, mutable)
        self.assertEqual(fast, slow)
        self.assertEqual(fast, 2)

    def test_duplicate_block_key_is_not_counted_as_unique(self):
        blocks = self.blocks + [dict(self.blocks[0], accession="A3")]
        owners = [b["owner"] for b in blocks]
        dates = [b["date"] for b in blocks]
        shares = [b["shares"] for b in blocks]
        self.assertEqual(count_unique_mutable_matches_fast(self.tranches, blocks, owners, dates, shares, {0, 1, 3}), 1)

    def test_duplicate_tranche_id_is_not_counted_as_unique(self):
        tranches = self.tranches + [dict(self.tranches[0])]
        owners = [b["owner"] for b in self.blocks]
        dates = [b["date"] for b in self.blocks]
        shares = [b["shares"] for b in self.blocks]
        self.assertEqual(count_unique_mutable_matches_fast(tranches, self.blocks, owners, dates, shares, {0, 1}), 1)

    def test_summary_reports_plus_one_tail_and_zero_exceedance_bound(self):
        summary = summarize_counts([1, 2, 2, 3, 2], observed=4, mutable_blocks=10)
        self.assertEqual(summary["null_replicates_at_or_above_observed"], 0)
        self.assertEqual(summary["empirical_tail_plus_one"], 1 / 6)
        self.assertGreater(summary["zero_exceedance_one_sided_95pct_upper"], 0)

    def test_raw_date_shuffle_detects_selection_envelope_violations(self):
        blocks = [
            {"issuer": "1", "owner": "ALICE", "accession": "X1", "date": date(2025, 1, 8),
             "filing": date(2025, 1, 10), "lag": 2, "shares": Decimal("10")},
            {"issuer": "1", "owner": "ALICE", "accession": "X2", "date": date(2025, 1, 19),
             "filing": date(2025, 1, 20), "lag": 1, "shares": Decimal("20")},
        ]
        result = measure_raw_date_shuffle_invalidity(blocks, reps=20, seed=211)
        self.assertGreater(result["mean_invalid_blocks"], 0)
        self.assertEqual(result["blocks_per_replicate"], 2)
        self.assertGreater(result["mean_invalid_fraction"], 0)

    def test_invalid_lag_fails_closed(self):
        bad = [dict(self.blocks[0], lag=5), self.blocks[1], self.blocks[2]]
        with self.assertRaises(ValueError):
            permute_lags_within_owner_groups(bad, build_groups(bad), random.Random(1))


if __name__ == "__main__":
    unittest.main()

import random
import unittest
from datetime import date, timedelta
from decimal import Decimal

import exchange_calendars as xc
import pandas as pd

from research.phase260_form144_form4_xnys_session_placebo import (
    STRATA, build_accession_clusters, build_session_groups, mutable_indices,
    permute_session_lags, session_group_key, valid_xnys_lags,
)


def block(issuer, owner, owner_cik, filing, lag, accession, shares="100"):
    return {
        "issuer": issuer, "owner": owner, "owner_cik": owner_cik,
        "filing": filing, "date": filing - timedelta(days=lag),
        "lag": lag, "accession": accession, "shares": Decimal(shares),
    }


class Phase260XNYSPlaceboTests(unittest.TestCase):
    def setUp(self):
        self.cal = xc.get_calendar("XNYS")

    def test_strata_are_explicit(self):
        self.assertEqual(STRATA, (
            "issuer_owner_cik_weekday",
            "issuer_owner_cik_month_weekday",
            "issuer_owner_cik_iso_week_weekday",
        ))

    def test_mlk_holiday_candidate_lags_are_session_valid(self):
        self.assertEqual(valid_xnys_lags(date(2026, 1, 20), self.cal), (0, 4))

    def test_regular_tuesday_candidate_signature(self):
        self.assertEqual(valid_xnys_lags(date(2026, 1, 27), self.cal), (0, 1, 4))

    def test_every_candidate_reconstructs_an_xnys_session(self):
        filing = date(2026, 1, 20)
        for lag in valid_xnys_lags(filing, self.cal):
            self.assertTrue(self.cal.is_session(pd.Timestamp(filing - timedelta(days=lag))))

    def test_weekday_and_candidate_signature_are_in_group_key(self):
        a = block("1", "ALICE", "101", date(2026, 1, 20), 4, "A1")
        b = block("1", "ALICE", "101", date(2026, 1, 27), 4, "A2")
        self.assertNotEqual(
            session_group_key(a, STRATA[0], valid_xnys_lags(a["filing"], self.cal)),
            session_group_key(b, STRATA[0], valid_xnys_lags(b["filing"], self.cal)),
        )

    def test_month_stratum_splits_months(self):
        a = block("1", "ALICE", "101", date(2026, 1, 27), 1, "A1")
        b = block("1", "ALICE", "101", date(2026, 2, 3), 1, "A2")
        ka = session_group_key(a, "issuer_owner_cik_month_weekday", valid_xnys_lags(a["filing"], self.cal))
        kb = session_group_key(b, "issuer_owner_cik_month_weekday", valid_xnys_lags(b["filing"], self.cal))
        self.assertNotEqual(ka, kb)

    def test_iso_week_uses_iso_year(self):
        a = block("1", "ALICE", "101", date(2021, 1, 1), 0, "A1")
        b = block("1", "ALICE", "101", date(2021, 1, 8), 0, "A2")
        ka = session_group_key(a, "issuer_owner_cik_iso_week_weekday", (0,))
        kb = session_group_key(b, "issuer_owner_cik_iso_week_weekday", (0,))
        self.assertNotEqual(ka, kb)

    def test_non_session_transaction_is_frozen(self):
        blocks = [block("1", "ALICE", "101", date(2026, 1, 20), 2, "A1")]
        groups, eligible, frozen, _ = build_session_groups(blocks, {0}, STRATA[0], self.cal)
        self.assertEqual(groups, {})
        self.assertEqual(eligible, set())
        self.assertEqual(frozen, {0})

    def test_same_candidate_signature_group_can_be_permuted(self):
        blocks = [
            block("1", "ALICE", "101", date(2026, 1, 27), 0, "A1"),
            block("1", "ALICE", "101", date(2026, 2, 3), 1, "A2"),
            block("1", "ALICE", "101", date(2026, 2, 10), 4, "A3"),
        ]
        groups, eligible, frozen, valid = build_session_groups(blocks, {0, 1, 2}, STRATA[0], self.cal)
        self.assertEqual(len(groups), 1)
        self.assertEqual(eligible, {0, 1, 2})
        self.assertEqual(frozen, set())
        dates, lags = permute_session_lags(blocks, groups, eligible, valid, self.cal, random.Random(260))
        self.assertEqual(sorted(lags), [0, 1, 4])
        for i, lag in enumerate(lags):
            self.assertEqual(dates[i], blocks[i]["filing"] - timedelta(days=lag))
            self.assertTrue(self.cal.is_session(pd.Timestamp(dates[i])))

    def test_multi_block_accession_is_not_in_single_block_partition(self):
        blocks = [
            block("1", "ALICE", "101", date(2026, 1, 27), 0, "A1"),
            block("1", "ALICE", "101", date(2026, 1, 27), 1, "A1", "200"),
            block("1", "ALICE", "101", date(2026, 2, 3), 4, "A2"),
        ]
        _, single, multi = build_accession_clusters(blocks)
        self.assertEqual(single, {2})
        self.assertEqual(multi, {0, 1})

    def test_same_lag_groups_are_not_mutable(self):
        blocks = [
            block("1", "ALICE", "101", date(2026, 1, 27), 1, "A1"),
            block("1", "ALICE", "101", date(2026, 2, 3), 1, "A2"),
        ]
        groups, _, _, _ = build_session_groups(blocks, {0, 1}, STRATA[0], self.cal)
        mutable, count = mutable_indices(groups, blocks)
        self.assertEqual(mutable, set())
        self.assertEqual(count, 0)

    def test_permutation_is_deterministic(self):
        blocks = [
            block("1", "ALICE", "101", date(2026, 1, 27), 0, "A1"),
            block("1", "ALICE", "101", date(2026, 2, 3), 1, "A2"),
            block("1", "ALICE", "101", date(2026, 2, 10), 4, "A3"),
        ]
        groups, eligible, _, valid = build_session_groups(blocks, {0, 1, 2}, STRATA[0], self.cal)
        a = permute_session_lags(blocks, groups, eligible, valid, self.cal, random.Random(7))
        b = permute_session_lags(blocks, groups, eligible, valid, self.cal, random.Random(7))
        self.assertEqual(a, b)

    def test_invalid_lag_fails_closed(self):
        blocks = [block("1", "ALICE", "101", date(2026, 1, 27), 5, "A1")]
        with self.assertRaises(ValueError):
            build_session_groups(blocks, {0}, STRATA[0], self.cal)

    def test_unknown_stratum_fails_closed(self):
        b = block("1", "ALICE", "101", date(2026, 1, 27), 1, "A1")
        with self.assertRaises(ValueError):
            session_group_key(b, "unknown", (0, 1, 4))

    def test_mutability_requires_distinct_observed_lags(self):
        blocks = [
            block("1", "ALICE", "101", date(2026, 1, 27), 1, "A1"),
            block("1", "ALICE", "101", date(2026, 2, 3), 1, "A2"),
        ]
        groups, _, _, _ = build_session_groups(blocks, {0, 1}, STRATA[0], self.cal)
        mutable, count = mutable_indices(groups, blocks)
        self.assertEqual(mutable, set())
        self.assertEqual(count, 0)


if __name__ == "__main__":
    unittest.main()

import random
import tempfile
import unittest
import zipfile
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

from research.phase258_form144_form4_accession_cluster_preserving_placebo import (
    STRATA, build_accession_clusters, build_single_accession_groups, holm_adjust,
    mutable_indices, owner_cik_by_accession, permute_single_accession_lags, temporal_group_key,
)


def block(issuer, owner, owner_cik, filing, lag, accession, shares="100"):
    return {"issuer": issuer, "owner": owner, "owner_cik": owner_cik, "filing": filing,
            "date": filing - timedelta(days=lag), "lag": lag, "accession": accession,
            "shares": Decimal(shares)}


class Phase258AccessionClusterTests(unittest.TestCase):
    def setUp(self):
        self.blocks = [
            block("1", "ALICE", "101", date(2025, 1, 10), 1, "A1"),
            block("1", "ALICE", "101", date(2025, 1, 15), 2, "A2"),
            block("1", "ALICE", "101", date(2025, 1, 20), 0, "A3"),
            block("1", "ALICE", "101", date(2025, 1, 20), 3, "A3", "200"),
            block("1", "ALICE", "202", date(2025, 1, 12), 1, "B1"),
            block("1", "ALICE", "202", date(2025, 1, 18), 4, "B2"),
        ]

    def test_strata_are_explicit(self):
        self.assertEqual(STRATA, ("issuer_owner_cik", "issuer_owner_cik_month", "issuer_owner_cik_iso_week"))

    def test_accession_partition_preserves_multi_block_cluster(self):
        by_acc, single, multi = build_accession_clusters(self.blocks)
        self.assertEqual(len(by_acc), 5)
        self.assertEqual(len(single), 4)
        self.assertEqual(multi, {2, 3})

    def test_accession_cannot_span_multiple_owner_identities(self):
        bad = [self.blocks[0], dict(self.blocks[0], owner_cik="999")]
        with self.assertRaises(ValueError):
            build_accession_clusters(bad)

    def test_owner_cik_is_required(self):
        with self.assertRaises(ValueError):
            temporal_group_key(dict(self.blocks[0], owner_cik=""), "issuer_owner_cik")

    def test_cik_not_name_defines_permutation_group(self):
        a = dict(self.blocks[0], owner="SAME NAME", owner_cik="101")
        b = dict(self.blocks[4], owner="SAME NAME", owner_cik="202")
        self.assertNotEqual(temporal_group_key(a, "issuer_owner_cik"), temporal_group_key(b, "issuer_owner_cik"))

    def test_month_stratum_splits_months(self):
        a = dict(self.blocks[0], filing=date(2025, 1, 31))
        b = dict(self.blocks[1], filing=date(2025, 2, 1))
        self.assertNotEqual(temporal_group_key(a, "issuer_owner_cik_month"), temporal_group_key(b, "issuer_owner_cik_month"))

    def test_iso_week_uses_iso_year(self):
        a = dict(self.blocks[0], filing=date(2021, 1, 1))
        b = dict(self.blocks[1], filing=date(2021, 1, 4))
        self.assertNotEqual(temporal_group_key(a, "issuer_owner_cik_iso_week"), temporal_group_key(b, "issuer_owner_cik_iso_week"))

    def test_unknown_stratum_fails_closed(self):
        with self.assertRaises(ValueError):
            temporal_group_key(self.blocks[0], "issuer_owner_quarter")

    def test_only_single_accessions_enter_groups(self):
        _, single, multi = build_accession_clusters(self.blocks)
        groups = build_single_accession_groups(self.blocks, single, "issuer_owner_cik")
        included = {i for ids in groups.values() for i in ids}
        self.assertEqual(included, single)
        self.assertTrue(included.isdisjoint(multi))

    def test_same_lag_groups_are_not_mutable(self):
        same = [block("1", "ALICE", "101", date(2025, 1, 10), 1, "S1"),
                block("1", "ALICE", "101", date(2025, 1, 15), 1, "S2")]
        groups = build_single_accession_groups(same, {0, 1}, "issuer_owner_cik")
        mutable, count = mutable_indices(groups, same)
        self.assertEqual(mutable, set())
        self.assertEqual(count, 0)

    def test_permutation_preserves_lag_multiset_and_filing_dates(self):
        _, single, multi = build_accession_clusters(self.blocks)
        groups = build_single_accession_groups(self.blocks, single, "issuer_owner_cik")
        dates, lags = permute_single_accession_lags(self.blocks, groups, single, random.Random(258))
        for ids in groups.values():
            self.assertEqual(sorted(lags[i] for i in ids), sorted(self.blocks[i]["lag"] for i in ids))
            for i in ids:
                self.assertEqual(dates[i], self.blocks[i]["filing"] - timedelta(days=lags[i]))
        for i in multi:
            self.assertEqual(dates[i], self.blocks[i]["date"])
            self.assertEqual(lags[i], self.blocks[i]["lag"])

    def test_permutation_is_deterministic(self):
        _, single, _ = build_accession_clusters(self.blocks)
        groups = build_single_accession_groups(self.blocks, single, "issuer_owner_cik_month")
        self.assertEqual(
            permute_single_accession_lags(self.blocks, groups, single, random.Random(7)),
            permute_single_accession_lags(self.blocks, groups, single, random.Random(7)),
        )

    def test_invalid_lag_rejected(self):
        bad = [dict(self.blocks[0], lag=5)]
        with self.assertRaises(ValueError):
            permute_single_accession_lags(bad, {("1", "101"): [0]}, {0}, random.Random(1))

    def test_holm_adjustment(self):
        self.assertEqual(holm_adjust({"a": 0.001, "b": 0.01, "c": 0.04}), {"a": 0.003, "b": 0.02, "c": 0.04})

    def test_owner_cik_parser_uses_unique_accession_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "form4.zip"
            with zipfile.ZipFile(path, "w") as z:
                z.writestr("REPORTINGOWNER.tsv",
                    "ACCESSION_NUMBER\tRPTOWNERCIK\tRPTOWNERNAME\n"
                    "A1\t00000101\tAlice\nA2\t00000202\tBob\nA2\t00000303\tBob LLC\n")
            unique, ambiguous = owner_cik_by_accession(path)
            self.assertEqual(unique, {"A1": "101"})
            self.assertEqual(ambiguous, {"A2": ["202", "303"]})


if __name__ == "__main__":
    unittest.main()

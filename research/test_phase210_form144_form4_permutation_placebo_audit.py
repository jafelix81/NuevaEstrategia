import unittest
from datetime import date
from decimal import Decimal
import json

from research.phase210_form144_form4_permutation_placebo_audit import (
    count_unique_mutable_matches, quantile_linear, run_permutations,
)


def tranche(day="2026-07-01", units=100):
    return {"issuer": "1", "seller": "A", "date": date.fromisoformat(day),
            "units": Decimal(str(units)), "accession": "144", "idx": "1"}


def block(day="2026-07-01", shares=100, owner="A", accession="4"):
    return {"issuer": "1", "owner": owner, "date": date.fromisoformat(day),
            "shares": Decimal(str(shares)), "accession": accession}


class Phase210Tests(unittest.TestCase):
    def test_linear_quantile(self):
        self.assertEqual(quantile_linear([0, 10], 0.5), 5)

    def test_exact_unique_mutable_match_count(self):
        self.assertEqual(count_unique_mutable_matches(
            [tranche()], [block()], ["A"], [date(2026, 7, 1)], [Decimal("100")], {0}
        ), 1)

    def test_ambiguous_block_is_not_counted(self):
        self.assertEqual(count_unique_mutable_matches(
            [tranche()], [block(), block(accession="4b")], ["A", "A"],
            [date(2026, 7, 1)] * 2, [Decimal("100")] * 2, {0, 1}
        ), 0)

    def test_immutable_block_is_excluded(self):
        self.assertEqual(count_unique_mutable_matches(
            [tranche()], [block()], ["A"], [date(2026, 7, 1)], [Decimal("100")], set()
        ), 0)

    def test_permutation_audit_is_deterministic_and_metadata_only(self):
        ts = [tranche(), tranche(day="2026-07-02", units=200)]
        bs = [block(), block(day="2026-07-02", shares=200, accession="4b")]
        a = run_permutations(ts, bs, reps=100, seed=210)
        b = run_permutations(ts, bs, reps=100, seed=210)
        self.assertEqual(a, b)
        self.assertNotIn("owner", json.dumps(a, sort_keys=True))


if __name__ == "__main__":
    unittest.main()

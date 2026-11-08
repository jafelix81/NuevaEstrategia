import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path
import json

from research.phase210_form144_form4_permutation_placebo_audit import (
    count_unique_mutable_matches, quantile_linear, run_permutations,
    summarize_price_matches, plan_flag_concordance,
)


def tranche(day="2026-07-01", units=100, accession="144", idx="1", plan=False):
    return {"issuer": "1", "seller": "A", "date": date.fromisoformat(day),
            "units": Decimal(str(units)), "accession": accession, "idx": idx, "plan": plan,
            "class_family": "COMMON", "class_norm": "COMMON"}


def block(day="2026-07-01", shares=100, owner="A", accession="4", flag_value="0"):
    return {"issuer": "1", "owner": owner, "date": date.fromisoformat(day),
            "shares": Decimal(str(shares)), "accession": accession, "flag": flag_value,
            "class_family": "COMMON", "class_norm": "COMMON"}


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

    def test_duplicate_tranche_identity_is_not_counted_twice(self):
        ts = [tranche(day="2026-07-01"), tranche(day="2026-07-02")]
        bs = [block(day="2026-07-01"), block(day="2026-07-02", accession="4b")]
        self.assertEqual(count_unique_mutable_matches(
            ts, bs, ["A", "A"], [date(2026, 7, 1), date(2026, 7, 2)],
            [Decimal("100"), Decimal("100")], {0, 1}
        ), 0)

    def test_immutable_block_is_excluded(self):
        self.assertEqual(count_unique_mutable_matches(
            [tranche()], [block()], ["A"], [date(2026, 7, 1)], [Decimal("100")], set()
        ), 0)

    def test_price_summary(self):
        matches = [(tranche(), block(), 0)]
        p144 = {("144", "1"): Decimal("10")}
        p4 = {("4", date(2026, 7, 1)): {
            "weighted_avg_price": Decimal("10.2"), "priced_share_fraction": Decimal("1")
        }}
        result = summarize_price_matches(matches, p144, p4)
        self.assertEqual(result["within_5pct"], 1)
        self.assertEqual(result["all_form4_shares_priced"], 1)

    def test_plan_flag_concordance(self):
        matches = [
            (tranche(plan=True), block(flag_value="1"), 0),
            (tranche(accession="145", plan=False), block(accession="5", flag_value="0"), 0),
            (tranche(accession="146", plan=True), block(accession="6", flag_value="0"), 0),
        ]
        result = plan_flag_concordance(matches)
        self.assertEqual(result["concordant"], 2)
        self.assertEqual(result["discordant"], 1)

    def test_permutation_audit_is_deterministic_and_metadata_only(self):
        ts = [tranche(), tranche(day="2026-07-02", units=200, accession="145")]
        bs = [block(), block(day="2026-07-02", shares=200, accession="4b")]
        a = run_permutations(ts, bs, [], {}, {}, reps=100, seed=210)
        b = run_permutations(ts, bs, [], {}, {}, reps=100, seed=210)
        self.assertEqual(a, b)
        self.assertNotIn("accession", json.dumps(a, sort_keys=True))

    def test_workflow_has_two_valid_cross_run_auth_pairs(self):
        workflow = Path(".github/workflows/phase210_form144_form4_permutation_placebo_audit.yml").read_text()
        dollar = chr(36)
        self.assertEqual(workflow.count("repository: " + dollar + "{{ github.repository }}"), 2)
        self.assertEqual(workflow.count("github-token: " + dollar + "{{ secrets.GITHUB_TOKEN }}"), 2)
        self.assertNotIn("REPO_EXPR", workflow)
        self.assertNotIn("TOKEN_EXPR", workflow)
        self.assertIn("python -m research.phase210_form144_form4_permutation_placebo_audit", workflow)


if __name__ == "__main__":
    unittest.main()

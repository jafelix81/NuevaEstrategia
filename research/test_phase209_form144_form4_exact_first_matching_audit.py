import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

from research.phase209_form144_form4_exact_first_matching_audit import (
    candidate_edges, exact_first_match, mutually_unique,
)


def tranche(accession, idx, day, units=100):
    return {"accession": accession, "idx": str(idx), "issuer": "123",
            "seller": "JANEDOE", "date": date.fromisoformat(day),
            "units": Decimal(str(units)), "class_family": "COMMON"}


def block(accession, day, shares=100):
    return {"accession": accession, "issuer": "123", "owner": "JANEDOE",
            "date": date.fromisoformat(day), "shares": Decimal(str(shares)),
            "class_family": "COMMON", "lag": 1}


class Phase209Tests(unittest.TestCase):
    def test_exact_link_survives_weaker_near_date_collision(self):
        t = tranche("144a", 1, "2026-07-01", 100)
        exact = block("4exact", "2026-07-01", 100)
        near = block("4near", "2026-07-02", 101)
        broad = candidate_edges([t], [exact, near], 0, 2)
        self.assertEqual(len(broad), 2)
        self.assertEqual(len(mutually_unique(broad)), 0)
        result = exact_first_match([t], [exact, near])
        self.assertEqual(len(result["exact_unique"]), 1)
        self.assertEqual(len(result["fallback_unique"]), 0)

    def test_fallback_uses_only_unreserved_nodes(self):
        t1 = tranche("144a", 1, "2026-07-01", 100)
        t2 = tranche("144b", 1, "2026-07-01", 200)
        b1 = block("4exact", "2026-07-01", 100)
        b2 = block("4fallback", "2026-07-02", 201)
        result = exact_first_match([t1, t2], [b1, b2])
        self.assertEqual(len(result["exact_unique"]), 1)
        self.assertEqual(len(result["fallback_unique"]), 1)
        self.assertEqual(result["fallback_unique"][0][0]["accession"], "144b")

    def test_ambiguous_exact_nodes_are_quarantined(self):
        t1 = tranche("144a", 1, "2026-07-01", 100)
        t2 = tranche("144b", 1, "2026-07-01", 100)
        b1 = block("4exact", "2026-07-01", 100)
        b2 = block("4near", "2026-07-02", 101)
        result = exact_first_match([t1, t2], [b1, b2])
        self.assertEqual(len(result["exact_edges"]), 2)
        self.assertEqual(len(result["exact_unique"]), 0)
        self.assertEqual(result["exact_ambiguous_blocks"], 1)
        self.assertEqual(len(result["fallback_unique"]), 0)

    def test_exact_edges_are_one_to_one(self):
        ts = [tranche("144a", 1, "2026-07-01", 100), tranche("144b", 1, "2026-07-01", 200)]
        bs = [block("4a", "2026-07-01", 100), block("4b", "2026-07-01", 200)]
        result = exact_first_match(ts, bs)
        self.assertEqual(len(result["exact_unique"]), 2)

    def test_same_date_quantity_mismatch_is_fallback(self):
        result = exact_first_match([tranche("144a", 1, "2026-07-01", 100)],
                                   [block("4a", "2026-07-01", 99)])
        self.assertEqual(len(result["exact_edges"]), 0)
        self.assertEqual(len(result["fallback_unique"]), 1)

    def test_pre_notice_candidate_is_not_post_notice_fallback(self):
        result = exact_first_match([tranche("144a", 1, "2026-07-02", 100)],
                                   [block("4a", "2026-07-01", 100)])
        self.assertEqual(len(result["exact_unique"]), 0)
        self.assertEqual(len(result["fallback_unique"]), 0)

    def test_gap_boundary_is_inclusive(self):
        t = tranche("144a", 1, "2026-07-01", 100)
        b2 = block("4a", "2026-07-03", 100)
        b3 = block("4b", "2026-07-04", 100)
        self.assertEqual(len(candidate_edges([t], [b2, b3], 0, 2)), 1)

    def test_workflow_auth_and_module_invocation_are_valid(self):
        workflow = Path(".github/workflows/phase209_form144_form4_exact_first_matching_audit.yml").read_text()
        dollar = chr(36)
        self.assertIn("repository: " + dollar + "{{ github.repository }}", workflow)
        self.assertIn("github-token: " + dollar + "{{ secrets.GITHUB_TOKEN }}", workflow)
        self.assertNotIn(chr(92) + dollar + "{{", workflow)
        self.assertIn("python -m research.phase209_form144_form4_exact_first_matching_audit", workflow)
        self.assertNotIn("python research/phase209_form144_form4_exact_first_matching_audit.py", workflow)


if __name__ == "__main__":
    unittest.main()

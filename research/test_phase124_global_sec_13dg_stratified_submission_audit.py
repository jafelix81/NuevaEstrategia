import csv
import tempfile
import unittest
from pathlib import Path

from research.phase124_global_sec_13dg_stratified_submission_audit import (
    allocate_strata, exclusion_set, parse_json_list, parse_rule_designations,
    sample_hash, weighted_rate,
)

class Phase124Tests(unittest.TestCase):
    def test_allocation_hits_exact_target_with_minimum_per_stratum(self):
        counts = {"a": 100, "b": 200, "c": 300, "d": 400}
        allocation = allocate_strata(counts, target=20, minimum=2)
        self.assertEqual(sum(allocation.values()), 20)
        self.assertTrue(all(allocation[k] >= 2 for k in counts))
        self.assertTrue(all(allocation[k] <= counts[k] for k in counts))

    def test_allocation_is_deterministic(self):
        counts = {"2016Q1|13D|false": 100, "2016Q1|13G|true": 500, "2026Q3|13D|true": 40}
        self.assertEqual(
            allocate_strata(counts, target=12, minimum=2),
            allocate_strata(counts, target=12, minimum=2),
        )

    def test_allocation_rejects_impossible_minimum(self):
        with self.assertRaises(ValueError):
            allocate_strata({"a": 1, "b": 1, "c": 1}, target=2, minimum=1)

    def test_sample_hash_is_stable_and_accession_specific(self):
        self.assertEqual(sample_hash("0000000000-26-000001"), sample_hash("0000000000-26-000001"))
        self.assertNotEqual(sample_hash("0000000000-26-000001"), sample_hash("0000000000-26-000002"))
        self.assertEqual(len(sample_hash("0000000000-26-000001")), 64)

    def test_parse_json_list_is_safe(self):
        self.assertEqual(parse_json_list('["0000000001","0000000002"]'), ["0000000001","0000000002"])
        self.assertEqual(parse_json_list("not-json"), [])

    def test_exclusion_set_removes_all_prior_pilot_accessions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            p82, p84, p120 = (root / x for x in ("p82","p84","p120"))
            for d in (p82,p84,p120):
                d.mkdir()
            for path, header, row in [
                (p82/"pilot_manifest.csv","accession","A"),
                (p84/"pilot_header_validation.csv","accession","B"),
                (p120/"phase120_predecessor_audit.csv","current_accession,previous_accession","C,D"),
            ]:
                with path.open("w",newline="",encoding="utf-8") as f:
                    w=csv.writer(f); w.writerow(header.split(",")); w.writerow(row.split(","))
            self.assertEqual(exclusion_set(p82,p84,p120), {"A","B","C","D"})

    def test_13g_rule_designations_are_extracted_only_from_xml(self):
        raw = """<XML><edgarSubmission><formData><designateRulesPursuantThisScheduleFiled>
        <designateRulePursuantThisScheduleFiled>Rule 13d-1(b)</designateRulePursuantThisScheduleFiled>
        </designateRulesPursuantThisScheduleFiled></formData></edgarSubmission></XML>"""
        self.assertEqual(parse_rule_designations(raw,"13G"), ["Rule 13d-1(b)"])
        self.assertEqual(parse_rule_designations(raw,"13D"), [])

    def test_weighted_rate_uses_post_stratification_weights(self):
        rows = [
            {"sample_weight": 10, "flag": True},
            {"sample_weight": 30, "flag": False},
        ]
        self.assertAlmostEqual(weighted_rate(rows,"flag"), 0.25)

    def test_weighted_rate_ignores_missing_values(self):
        rows = [
            {"sample_weight": 10, "flag": True},
            {"sample_weight": 100, "flag": None},
        ]
        self.assertAlmostEqual(weighted_rate(rows,"flag"), 1.0)

if __name__ == "__main__":
    unittest.main()

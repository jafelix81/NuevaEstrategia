import base64
import gzip
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from research.phase179_sec13dg_legacy_497_predecessor_audit import (
    INPUT_CSV_SHA256,
    INPUT_GZIP_SHA256,
    audit_rows,
    cusip_is_valid,
    parse_rows,
    prior_candidates,
    run_audit,
)

class Phase179Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = run_audit()
        cls.input_path = Path(__file__).with_name("phase179_sec13dg_legacy_497_parent_input.csv.gz.b64")
        payload = cls.input_path.read_bytes().strip()
        cls.rows = parse_rows(gzip.decompress(base64.b64decode(payload, validate=True)))

    def test_input_hashes_are_pinned(self):
        payload = self.input_path.read_bytes().strip()
        gzip_bytes = base64.b64decode(payload, validate=True)
        self.assertEqual(hashlib.sha256(gzip_bytes).hexdigest(), INPUT_GZIP_SHA256)
        self.assertEqual(hashlib.sha256(gzip.decompress(gzip_bytes)).hexdigest(), INPUT_CSV_SHA256)

    def test_full_legacy_sample_has_497_unique_accessions(self):
        self.assertEqual(self.result["input_rows"], 497)
        self.assertEqual(self.result["unique_accessions"], 497)
        self.assertEqual(self.result["family_counts"], {"13D": 180, "13G": 317})

    def test_role_counts_reconcile_by_family(self):
        self.assertEqual(self.result["family_role_counts"]["13D"], {"A": 108, "N": 68, "C": 4})
        self.assertEqual(self.result["family_role_counts"]["13G"], {"A": 204, "N": 113, "C": 0})
        self.assertEqual(self.result["amendment_candidates"], 316)
        self.assertEqual(self.result["nonamendment_status_unconfirmed"], 181)

    def test_13d_item4_cohort_remains_unconfirmed(self):
        self.assertEqual(self.result["13d_item4_nonamendment_unconfirmed"], 55)
        self.assertEqual(self.result["13d_item4_complete_strict_key"], 46)
        self.assertEqual(self.result["strict_13d_item4_nonamendment_candidates"]["with_candidate"], 0)

    def test_strict_amendment_screen_finds_only_two_candidates(self):
        x = self.result["strict_amendment_candidates_same_family"]
        self.assertEqual(x["eligible"], 276)
        self.assertEqual(x["with_candidate"], 2)
        self.assertEqual(x["unique_candidate"], 2)
        self.assertEqual(x["ambiguous_candidate"], 0)
        self.assertEqual(x["candidate_edges"], 2)

    def test_strict_matches_are_same_family_and_match_phase178_pairs(self):
        pairs = {(p["parent_accession"], p["child_accession"]) for p in self.result["strict_candidate_pairs"]}
        self.assertEqual(pairs, {
            ("0000921895-18-001641", "0001011438-19-000110"),
            ("0000807249-18-000020", "0000807249-20-000135"),
        })
        self.assertTrue(all(p["parent_family"] == p["child_family"] == "13D" for p in self.result["strict_candidate_pairs"]))
        self.assertTrue(all(p["same_filer"] and p["same_first_owner_hash"] for p in self.result["strict_candidate_pairs"]))

    def test_both_strict_candidate_parents_are_unanchored_amendments(self):
        self.assertEqual(self.result["strict_candidate_parent_anchor_counts"], [0, 0])
        self.assertTrue(self.result["strict_candidate_parents_are_amendments"])
        self.assertTrue(self.result["strict_candidate_parents_have_no_earlier_strict_anchor"])

    def test_relaxing_to_issuer_cusip_creates_false_collisions(self):
        same = self.result["issuer_cusip_amendment_candidates_same_family"]
        all_families = self.result["issuer_cusip_amendment_candidates_all_families"]
        self.assertEqual(same["with_candidate"], 5)
        self.assertEqual(all_families["with_candidate"], 8)
        self.assertEqual(self.result["weak_same_family_collision_count"], 3)
        self.assertEqual(self.result["cross_family_collision_count"], 3)
        self.assertTrue(self.result["all_relaxed_collisions_fail_filer_and_owner"])

    def test_three_key_screens_do_not_add_candidates(self):
        self.assertEqual(self.result["three_key_without_owner_same_family"]["with_candidate"], 2)
        self.assertEqual(self.result["three_key_without_filer_same_family"]["with_candidate"], 2)

    def test_nonamendment_forms_have_no_in_sample_predecessor(self):
        x = self.result["strict_nonamendment_candidates_same_family"]
        self.assertEqual(x["with_candidate"], 0)
        relaxed = self.result["issuer_cusip_nonamendment_candidates_same_family"]
        self.assertEqual(relaxed["with_candidate"], 0)

    def test_cusip_check_digit(self):
        self.assertTrue(cusip_is_valid("81752R100"))
        self.assertTrue(cusip_is_valid("903002103"))
        self.assertFalse(cusip_is_valid("81752R101"))
        self.assertFalse(cusip_is_valid(""))

    def test_missing_keys_and_same_date_never_match(self):
        child = next(r for r in self.rows if r["acc"] == "0001011438-19-000110")
        matches = prior_candidates(self.rows, child)
        self.assertEqual([r["acc"] for r in matches], ["0000921895-18-001641"])
        self.assertTrue(all(r["dt"] < child["dt"] for r in matches))
        missing = dict(child)
        missing["owner_h96"] = ""
        self.assertEqual(prior_candidates(self.rows, missing), [])
        same_date = dict(child)
        same_date["dt"] = "2018-05-11"
        self.assertEqual(prior_candidates(self.rows, same_date), [])

    def test_no_parent_or_alpha_admission(self):
        self.assertEqual(self.result["verified_parent_edges"], 0)
        self.assertEqual(self.result["initial_status_confirmed"], 0)
        self.assertFalse(self.result["feature_admission"])
        self.assertFalse(self.result["alpha_admission"])
        self.assertFalse(self.result["final_holdout_used"])
        self.assertFalse(self.result["f80_modified"])

    def test_metadata_output_is_deterministic_and_privacy_limited(self):
        with tempfile.TemporaryDirectory() as temp:
            result = run_audit(Path(temp))
            output = Path(temp) / "phase179_sec13dg_legacy_497_parent_summary.json"
            loaded = json.loads(output.read_text())
            self.assertEqual(loaded, result)
            self.assertFalse(loaded["input"]["raw_names_persisted"])
            self.assertFalse(loaded["input"]["item4_text_persisted"])

if __name__ == "__main__":
    unittest.main()

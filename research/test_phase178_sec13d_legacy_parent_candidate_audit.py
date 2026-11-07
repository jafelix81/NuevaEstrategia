import gzip, hashlib, json, tempfile, unittest
from pathlib import Path
from research.phase178_sec13d_legacy_parent_candidate_audit import (
    INPUT_CSV_SHA256, INPUT_GZIP_SHA256, audit_rows, cusip_is_valid,
    parse_rows, prior_candidates, run_audit,
)

class Phase178Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = run_audit()
        cls.input_path = Path(__file__).with_name("phase178_sec13d_legacy_parent_input.csv.gz")
        cls.rows = parse_rows(gzip.decompress(cls.input_path.read_bytes()))

    def test_input_gzip_hash_is_pinned(self):
        self.assertEqual(hashlib.sha256(self.input_path.read_bytes()).hexdigest(), INPUT_GZIP_SHA256)

    def test_input_csv_hash_is_pinned(self):
        self.assertEqual(hashlib.sha256(gzip.decompress(self.input_path.read_bytes())).hexdigest(), INPUT_CSV_SHA256)

    def test_sample_has_180_unique_accessions(self):
        self.assertEqual(self.result["input_rows"], 180)
        self.assertEqual(self.result["unique_accessions"], 180)

    def test_role_counts_reconcile(self):
        self.assertEqual(self.result["role_counts"]["index_coded_amendment"], 108)
        self.assertEqual(self.result["role_counts"]["non_amendment_form_initial_status_unconfirmed"], 68)
        self.assertEqual(self.result["role_counts"]["cover_numbered_amendment_candidate"], 4)
        self.assertEqual(self.result["role_counts"]["total_amendment_candidates"], 112)

    def test_item4_candidate_count_and_key_coverage(self):
        self.assertEqual(self.result["item4_non_amendment_unconfirmed_candidates"], 55)
        self.assertEqual(self.result["item4_candidates_with_valid_cusip"], 46)
        self.assertEqual(self.result["item4_candidates_with_body_issuer_hash"], 53)
        self.assertEqual(self.result["item4_candidates_with_first_owner_hash"], 55)
        self.assertEqual(self.result["item4_candidates_with_complete_match_key"], 46)
        self.assertEqual(self.result["legacy_previous_accession_populated_rows"], 0)

    def test_no_item4_candidate_has_in_sample_predecessor(self):
        self.assertEqual(self.result["item4_candidates_with_any_in_sample_predecessor"], 0)
        self.assertEqual(self.result["item4_candidates_without_in_sample_predecessor"], 55)

    def test_only_two_amendment_candidates_have_unique_predecessor_candidates(self):
        self.assertEqual(self.result["amendment_candidates_with_any_in_sample_candidate"], 2)
        self.assertEqual(self.result["amendment_candidates_with_unique_candidate"], 2)
        self.assertEqual(self.result["amendment_candidates_with_ambiguous_candidates"], 0)
        self.assertEqual(self.result["amendment_candidates_without_candidate"], 110)

    def test_candidate_pairs_are_exact_and_not_verified_edges(self):
        pairs = {(p["candidate_predecessor_accession"], p["later_amendment_accession"]) for p in self.result["candidate_pairs"]}
        self.assertEqual(pairs, {
            ("0000921895-18-001641", "0001011438-19-000110"),
            ("0000807249-18-000020", "0000807249-20-000135"),
        })
        self.assertTrue(all(not p["verified_parent_edge"] for p in self.result["candidate_pairs"]))
        self.assertTrue(self.result["candidate_parent_documents_are_amendments"])
        self.assertTrue(self.result["candidate_parent_documents_have_no_earlier_in_sample_anchor"])

    def test_missing_keys_never_act_as_wildcards(self):
        child = next(r for r in self.rows if r["acc"] == "0001504304-24-000004")
        self.assertEqual(prior_candidates(self.rows, child, require_owner=True), [])

    def test_same_date_is_not_a_prior_filing(self):
        child = next(r for r in self.rows if r["acc"] == "0001011438-19-000110")
        matches = prior_candidates(self.rows, child, require_owner=True)
        self.assertTrue(all(r["dt"] < child["dt"] for r in matches))

    def test_cusip_check_digit(self):
        self.assertTrue(cusip_is_valid("452521107"))
        self.assertTrue(cusip_is_valid("074014101"))
        self.assertFalse(cusip_is_valid("452521108"))
        self.assertFalse(cusip_is_valid(""))

    def test_no_parent_or_alpha_admission(self):
        self.assertEqual(self.result["parent_edges_verified"], 0)
        self.assertEqual(self.result["initial_status_confirmed"], 0)
        self.assertFalse(self.result["feature_admission"])
        self.assertFalse(self.result["alpha_admission"])
        self.assertFalse(self.result["final_holdout_used"])
        self.assertFalse(self.result["f80_modified"])

    def test_metadata_only_output(self):
        with tempfile.TemporaryDirectory() as temp:
            result = run_audit(Path(temp))
            output = Path(temp) / "phase178_sec13d_legacy_parent_candidate_summary.json"
            loaded = json.loads(output.read_text())
            self.assertEqual(loaded, result)
            self.assertFalse(loaded["input"]["raw_names_persisted"])
            self.assertFalse(loaded["input"]["item4_text_persisted"])

if __name__ == "__main__":
    unittest.main()

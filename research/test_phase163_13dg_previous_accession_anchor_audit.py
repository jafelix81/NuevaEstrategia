import json
import tempfile
import unittest
from pathlib import Path

from phase163_13dg_previous_accession_anchor_audit import (
    PARENT_CASES, audit, normalize_accession, write_outputs
)


class Phase163PreviousAccessionAnchorTests(unittest.TestCase):
    def test_accession_normalization(self):
        self.assertEqual(normalize_accession("315066-12-2323"), "0000315066-12-002323")
        self.assertIsNone(normalize_accession("not-an-accession"))

    def test_six_parent_documents_are_inspected(self):
        rows, summary = audit()
        self.assertEqual(summary["parent_documents_inspected"], 6)
        self.assertEqual(summary["unique_inspected_parent_accessions"], 6)

    def test_thirteen_child_rows_are_examined(self):
        rows, summary = audit()
        self.assertEqual(summary["child_rows_examined"], 13)
        self.assertEqual(len(rows), 13)

    def test_amdocs_fourteenth_amendment_points_to_initial_anchor(self):
        rows, summary = audit()
        row = next(r for r in rows if r["child_accession"] == "0000315066-26-000372")
        self.assertEqual(row["parent_form"], "SC 13G")
        self.assertEqual(row["child_amendment_no"], 14)
        self.assertTrue(row["long_chain_anchor_evidence"])
        self.assertTrue(row["same_issuer_cik"])
        self.assertTrue(row["same_cusip"])

    def test_89bio_fifth_amendment_points_to_initial_anchor(self):
        rows, _ = audit()
        row = next(r for r in rows if r["child_accession"] == "0001274173-25-000015")
        self.assertEqual(row["child_amendment_no"], 5)
        self.assertTrue(row["long_chain_anchor_evidence"])
        self.assertTrue(row["same_issuer_cik"])
        self.assertTrue(row["same_cusip"])

    def test_montrose_same_issuer_and_cusip_is_candidate_not_edge(self):
        rows, _ = audit()
        row = next(r for r in rows if r["child_accession"] == "0001644956-25-000034")
        self.assertEqual(row["status"], "ISSUER_SECURITY_CONTINUITY_CANDIDATE_NOT_EDGE")
        self.assertFalse(row["immediate_predecessor_verified"])

    def test_endeavor_security_identity_remains_unverified(self):
        rows, _ = audit()
        row = next(r for r in rows if r["child_accession"] == "0001140361-25-017757")
        self.assertTrue(row["same_issuer_cik"])
        self.assertIsNone(row["same_cusip"])
        self.assertEqual(row["status"], "ISSUER_MATCH_SECURITY_UNVERIFIED")

    def test_mobiquity_security_identity_remains_unverified(self):
        rows, _ = audit()
        row = next(r for r in rows if r["child_accession"] == "0001535610-25-000004")
        self.assertTrue(row["same_issuer_cik"])
        self.assertIsNone(row["same_cusip"])
        self.assertEqual(row["status"], "ISSUER_MATCH_SECURITY_UNVERIFIED")

    def test_first_trust_reused_reference_has_eight_children(self):
        rows, summary = audit()
        group = [r for r in rows if r["previous_accession"] == "0001445546-21-002430"]
        self.assertEqual(len(group), 8)
        self.assertEqual(summary["first_trust_reused_reference_children"], 8)

    def test_first_trust_has_four_cross_issuer_children(self):
        rows, summary = audit()
        group = [r for r in rows if r["previous_accession"] == "0001445546-21-002430"]
        self.assertEqual(sum(r["status"] == "CROSS_ISSUER_QUARANTINE" for r in group), 4)

    def test_first_trust_has_four_same_issuer_different_cusip_children(self):
        rows, _ = audit()
        group = [r for r in rows if r["previous_accession"] == "0001445546-21-002430"]
        self.assertEqual(sum(r["status"] == "SAME_ISSUER_DIFFERENT_CUSIP_QUARANTINE" for r in group), 4)

    def test_no_first_trust_child_has_exact_issuer_cusip_match(self):
        rows, summary = audit()
        group = [r for r in rows if r["previous_accession"] == "0001445546-21-002430"]
        self.assertEqual(sum(r["status"] == "ISSUER_SECURITY_CONTINUITY_CANDIDATE_NOT_EDGE" for r in group), 0)
        self.assertEqual(summary["first_trust_exact_issuer_cusip_matches"], 0)

    def test_no_immediate_predecessor_edge_is_promoted(self):
        rows, summary = audit()
        self.assertEqual(summary["immediate_predecessor_edges_verified"], 0)
        self.assertTrue(all(not r["immediate_predecessor_verified"] for r in rows))

    def test_remaining_phase160_references_are_not_claimed_as_audited(self):
        _, summary = audit()
        self.assertEqual(summary["uninspected_phase160_references"], 26)

    def test_output_files_are_reproducible(self):
        rows, summary = audit()
        with tempfile.TemporaryDirectory() as tmp:
            write_outputs(rows, summary, Path(tmp))
            saved = json.loads((Path(tmp) / "phase163_13dg_previous_accession_anchor_summary.json").read_text())
            self.assertEqual(saved["child_rows_examined"], 13)
            self.assertTrue((Path(tmp) / "phase163_13dg_previous_accession_anchor_rows.csv").exists())

    def test_no_returns_holdout_or_production_change(self):
        _, summary = audit()
        self.assertFalse(summary["forward_returns_used"])
        self.assertFalse(summary["final_holdout_used"])
        self.assertFalse(summary["production_changed"])
        self.assertFalse(summary["f80_changed"])


if __name__ == "__main__":
    unittest.main()

import unittest

from phase162_13dg_parent_accession_validation import (
    CHILD_ROWS, PARENT_DOCUMENT, audit, normalize_accession
)


class Phase162ParentAccessionValidationTests(unittest.TestCase):
    def test_accession_is_canonical(self):
        self.assertEqual(normalize_accession("1445546-21-2430"), "0001445546-21-002430")

    def test_parent_is_real_initial_13g_filing(self):
        self.assertEqual(PARENT_DOCUMENT["form"], "SC 13G")
        self.assertFalse(PARENT_DOCUMENT["form"].endswith("/A"))
        self.assertEqual(PARENT_DOCUMENT["filing_date"], "2021-05-10")

    def test_parent_security_identity_is_explicit(self):
        self.assertEqual(PARENT_DOCUMENT["issuer_cik"], "0001667919")
        self.assertEqual(PARENT_DOCUMENT["cusip"], "33740F854")
        self.assertIn("Deep Buffer ETF - August", PARENT_DOCUMENT["security_class"])

    def test_eight_child_rows_are_preserved(self):
        _, summary = audit()
        self.assertEqual(len(CHILD_ROWS), 8)
        self.assertEqual(summary["valid_child_rows"], 8)
        self.assertEqual(summary["unique_child_accessions"], 8)

    def test_all_children_reuse_inspected_reference(self):
        _, summary = audit()
        self.assertEqual(summary["unique_previous_accessions"], 1)
        self.assertEqual(summary["children_matching_parent_reference"], 8)

    def test_all_children_have_same_filer_cik_as_parent(self):
        _, summary = audit()
        self.assertEqual(summary["children_matching_parent_filer_cik"], 8)

    def test_four_children_match_parent_issuer_cik(self):
        _, summary = audit()
        self.assertEqual(summary["children_matching_parent_issuer_cik"], 4)

    def test_four_children_have_different_issuer_cik(self):
        _, summary = audit()
        self.assertEqual(summary["children_with_parent_issuer_cik_mismatch"], 4)

    def test_no_child_matches_parent_cusip(self):
        _, summary = audit()
        self.assertEqual(summary["children_matching_parent_cusip"], 0)

    def test_same_issuer_children_all_have_different_cusip(self):
        _, summary = audit()
        self.assertEqual(summary["children_same_issuer_different_cusip"], 4)

    def test_no_child_has_exact_issuer_and_cusip_continuity(self):
        _, summary = audit()
        self.assertEqual(summary["children_with_exact_issuer_and_cusip_match"], 0)

    def test_parent_form_family_matches_but_does_not_prove_parentage(self):
        _, summary = audit()
        self.assertTrue(summary["parent_13g_family_matches_children"])
        self.assertEqual(summary["status"], "PREVIOUS_ACCESSION_NOT_PARENT_FOR_TARGETED_CHILD_SET")

    def test_parent_precedes_all_children_by_accession_year(self):
        rows, summary = audit()
        self.assertTrue(summary["all_children_later_than_parent_by_accession_year"])
        self.assertTrue(all(r["parent_precedes_child_by_accession_year"] for r in rows))

    def test_row_statuses_distinguish_cross_issuer_and_security_mismatch(self):
        rows, _ = audit()
        cross = [r for r in rows if r["status"] == "ISSUER_CIK_MISMATCH"]
        same_issuer = [r for r in rows if r["status"] == "SAME_ISSUER_CIK_DIFFERENT_CUSIP_UNRESOLVED"]
        self.assertEqual(len(cross), 4)
        self.assertEqual(len(same_issuer), 4)

    def test_raw_previous_accession_is_retained(self):
        rows, _ = audit()
        self.assertTrue(all(r["previous_accession"] == PARENT_DOCUMENT["accession"] for r in rows))

    def test_source_provenance_discloses_manual_fixture_limit(self):
        _, summary = audit()
        self.assertIn("manually transcribed", summary["source_provenance"])
        self.assertIn("not included", summary["source_provenance"])

    def test_no_returns_holdout_or_production_change(self):
        _, summary = audit()
        self.assertFalse(summary["forward_returns_used"])
        self.assertFalse(summary["final_holdout_used"])
        self.assertFalse(summary["production_changed"])
        self.assertFalse(summary["f80_changed"])


if __name__ == "__main__":
    unittest.main()

import unittest
from phase35_13dg_lineage_feasibility_audit import norm_name, classify_candidate_count, family, pointer_is_latest

class LineageAuditTests(unittest.TestCase):
    def test_conservative_name_normalization(self):
        self.assertEqual(norm_name("The Vanguard Group, Inc."), "VANGUARD GROUP")
        self.assertEqual(norm_name("JPMORGAN CHASE & CO."), "JPMORGAN CHASE")
    def test_missing_pointer_candidates_are_not_assigned(self):
        self.assertEqual(classify_candidate_count(0), "zero_in_panel_candidates")
        self.assertEqual(classify_candidate_count(1), "one_in_panel_candidate_unassigned")
        self.assertEqual(classify_candidate_count(2), "multiple_in_panel_candidates_ambiguous")
    def test_previous_accession_may_reference_an_older_filing(self):
        self.assertFalse(pointer_is_latest("original-accession", "later-amendment"))
        self.assertTrue(pointer_is_latest("latest-accession", "latest-accession"))
        self.assertFalse(pointer_is_latest("original-accession", None))
    def test_form_family(self):
        self.assertEqual(family("SC 13G/A"), "13G")
        self.assertEqual(family("SC 13D"), "13D")

if __name__ == "__main__": unittest.main()

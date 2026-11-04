import unittest

from research.phase67_form144_full_candidate_role_resolution import (
    classify_candidate_identity, classify_control, index_row_invalid,
)


class CandidateRoleTests(unittest.TestCase):
    def setUp(self):
        self.identity = {
            "xml_issuer_cik": "0000000001",
            "xml_filer_cik": "0000000002",
            "both_xml_ciks_in_pair": True,
            "xml_ciks_distinct": True,
            "xml_form_matches_index": True,
        }

    def test_unique_candidate_issuer_is_event(self):
        result = classify_candidate_identity(
            "unique_candidate", ["0000000001"], self.identity
        )
        self.assertEqual(result["candidate_role_status"], "issuer_match")
        self.assertTrue(result["role_resolved"])
        self.assertTrue(result["include_as_issuer_event"])

    def test_unique_candidate_filer_is_excluded(self):
        result = classify_candidate_identity(
            "unique_candidate", ["0000000002"], self.identity
        )
        self.assertEqual(result["candidate_role_status"], "filer_only_false_positive")
        self.assertTrue(result["role_resolved"])
        self.assertFalse(result["include_as_issuer_event"])

    def test_unique_candidate_not_in_either_xml_role_is_unresolved(self):
        result = classify_candidate_identity(
            "unique_candidate", ["0000000003"], self.identity
        )
        self.assertFalse(result["role_resolved"])
        self.assertFalse(result["include_as_issuer_event"])

    def test_ambiguous_pair_includes_only_when_issuer_is_candidate(self):
        result = classify_candidate_identity(
            "ambiguous", ["0000000001", "0000000002"], self.identity
        )
        self.assertEqual(result["candidate_role_status"], "ambiguous_pair_issuer_match")
        self.assertTrue(result["include_as_issuer_event"])

    def test_ambiguous_filer_only_candidate_is_excluded(self):
        result = classify_candidate_identity(
            "ambiguous", ["0000000002", "0000000003"], self.identity
        )
        self.assertEqual(
            result["candidate_role_status"],
            "ambiguous_pair_filer_only_false_positive",
        )
        self.assertTrue(result["role_resolved"])
        self.assertFalse(result["include_as_issuer_event"])

    def test_pair_or_form_mismatch_is_unresolved(self):
        bad_pair = dict(self.identity, both_xml_ciks_in_pair=False)
        result = classify_candidate_identity(
            "unique_candidate", ["0000000001"], bad_pair
        )
        self.assertEqual(
            result["candidate_role_status"],
            "unresolved_identity_or_index_mismatch",
        )
        self.assertFalse(result["role_resolved"])
        bad_form = dict(self.identity, xml_form_matches_index=False)
        result = classify_candidate_identity(
            "unique_candidate", ["0000000001"], bad_form
        )
        self.assertFalse(result["include_as_issuer_event"])

    def test_expected_archive_path_multiplicity_is_not_a_form_or_date_conflict(self):
        row = {
            "form": "144", "filing_date": "2025-01-02",
            "metadata_conflict": True, "archive_path_cik_conflict": True,
        }
        self.assertFalse(index_row_invalid(row))
        self.assertTrue(index_row_invalid(dict(row, form=None)))
        self.assertTrue(index_row_invalid(dict(row, filing_date=None)))

    def test_control_pair_requires_both_distinct_ciks_and_form_match(self):
        self.assertEqual(classify_control(self.identity), "control_pair_concordant")
        self.assertEqual(
            classify_control(dict(self.identity, xml_ciks_distinct=False)),
            "control_pair_mismatch",
        )


if __name__ == "__main__":
    unittest.main()

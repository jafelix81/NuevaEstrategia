import unittest

from research.phase606_sec_13f_manager_table_live_audit import (
    audit_infotable_references,
    audit_othermanager,
    audit_othermanager2,
    audit_summarypage,
    normalize_file_number,
    resolve_manager_identity,
)


class Phase606Tests(unittest.TestCase):
    def test_file_number_formatting_is_normalized(self):
        self.assertEqual(normalize_file_number("28-4545"), "028-04545")
        self.assertEqual(normalize_file_number("028 - 04545"), "028-04545")

    def test_explicit_cik_conflict_is_not_silently_resolved(self):
        mapping = {"028-04545": {"0000000001"}}
        self.assertEqual(
            resolve_manager_identity("0000000002", "028-04545", mapping),
            "IDENTITY_CONFLICT",
        )

    def test_no_name_based_identity_fallback(self):
        self.assertEqual(resolve_manager_identity("", "", {}), "UNRESOLVED_NO_IDENTIFIER")

    def test_othermanager_uses_accession_and_surrogate_key(self):
        header = ["ACCESSION_NUMBER", "OTHERMANAGER_SK", "CIK", "FORM13FFILENUMBER", "NAME"]
        rows = [
            ["A1", "1", "0000000002", "", "Manager B"],
            ["A1", "2", "0000000003", "", "Manager C"],
            ["A1", "2", "0000000003", "", "Duplicate"],
        ]
        out = audit_othermanager(header, rows, {"A1": {}}, {})
        self.assertEqual(out["rows"], 3)
        self.assertEqual(out["duplicate_accession_sk_keys"], 1)
        self.assertEqual(out["accessions_with_multiple_rows"], 1)

    def test_othermanager2_accession_key_cardinality_and_sequence_pair(self):
        header = ["ACCESSION_NUMBER", "SEQUENCENUMBER", "CIK", "FORM13FFILENUMBER", "NAME"]
        rows = [
            ["A1", "1", "0000000002", "", "Manager B"],
            ["A1", "2", "0000000003", "", "Manager C"],
            ["A2", "1", "0000000004", "", "Manager D"],
        ]
        out = audit_othermanager2(header, rows, {"A1": {}, "A2": {}}, {})
        self.assertEqual(out["accession_only_key_collisions"], 1)
        self.assertEqual(out["duplicate_accession_sequence_pairs"], 0)
        self.assertEqual(out["accessions_with_multiple_rows"], 1)
        self.assertEqual(out["sequences_by_accession"]["A1"], ["1", "2"])

    def test_duplicate_othermanager2_sequence_pair_is_detected(self):
        header = ["ACCESSION_NUMBER", "SEQUENCENUMBER", "CIK", "FORM13FFILENUMBER", "NAME"]
        rows = [
            ["A1", "1", "0000000002", "", "Manager B"],
            ["A1", "1", "0000000002", "", "Duplicate"],
        ]
        out = audit_othermanager2(header, rows, {"A1": {}}, {})
        self.assertEqual(out["duplicate_accession_sequence_pairs"], 1)

    def test_infotable_references_resolve_by_accession_and_sequence(self):
        header = ["ACCESSION_NUMBER", "INFOTABLE_SK", "OTHERMANAGER"]
        rows = [
            ["A1", "1", "1,2"],
            ["A1", "2", "3"],
            ["A1", "3", "bad"],
            ["A2", "1", "1"],
        ]
        filers = {"A1": {"submission_type": "13F-HR", "report_type": "13F HOLDINGS REPORT"},
                  "A2": {"submission_type": "13F-HR", "report_type": "13F HOLDINGS REPORT"}}
        out = audit_infotable_references(header, rows, filers, {"A1": {"1", "2"}})
        self.assertEqual(out["manager_reference_tokens"], 4)
        self.assertEqual(out["resolved_sequence_tokens"], 2)
        self.assertEqual(out["dangling_sequence_tokens"], 2)
        self.assertEqual(out["malformed_sequence_tokens"], 1)

    def test_summary_page_count_is_reconciled_to_manager2_rows(self):
        header = ["ACCESSION_NUMBER", "OTHERINCLUDEDMANAGERSCOUNT"]
        rows = [["A1", "2"], ["A2", "0"]]
        out = audit_summarypage(header, rows, {"A1": 2})
        self.assertEqual(out["compared_rows"], 2)
        self.assertEqual(out["count_mismatches"], 0)


if __name__ == "__main__":
    unittest.main()

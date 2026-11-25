import unittest

from research.phase608_sec_13f_sequence_group_graph import build_sequence_groups
from research.phase609_sec_13f_full_quarter_group_audit import audit_infotable_rows

OM_HEADER = ["ACCESSION_NUMBER","SEQUENCENUMBER","CIK","FORM13FFILENUMBER","CRDNUMBER","SEC_FILENUMBER","NAME"]
INFO_HEADER = ["ACCESSION_NUMBER","INFOTABLE_SK","OTHERMANAGER"]


class Phase609Tests(unittest.TestCase):
    def group_graph(self):
        rows = [
            ["A","1","0001327354","028-11406","","","Manager A"],
            ["A","1","","","","","Manager A on behalf of Manager B"],
            ["A","2","0001075869","028-04413","","","Manager C"],
        ]
        return build_sequence_groups(OM_HEADER, rows)["groups"]

    def test_streaming_counts_group_only_and_single_member_refs(self):
        filers = {"A":{"submission_type":"13F-HR","report_type":"13F HOLDINGS REPORT"}}
        rows = iter([["A","1","1"],["A","2","2"],["A","3","1"]])
        out = audit_infotable_rows(INFO_HEADER, rows, filers, self.group_graph())
        self.assertEqual(out["audit"]["rows"], 3)
        self.assertEqual(out["audit"]["numeric_reference_tokens"], 3)
        self.assertEqual(out["audit"]["matched_group_tokens"], 3)
        self.assertEqual(out["audit"]["group_only_reference_tokens"], 2)
        self.assertEqual(out["audit"]["single_member_group_tokens"], 1)
        self.assertEqual(out["audit"]["unmatched_sequence_tokens"], 0)

    def test_nonnumeric_comma_name_is_one_raw_value(self):
        filers = {"A":{"submission_type":"13F-HR","report_type":"13F HOLDINGS REPORT"}}
        out = audit_infotable_rows(INFO_HEADER, iter([["A","1","XXEC, INC."]]), filers, self.group_graph())
        self.assertEqual(out["audit"]["nonnumeric_as_filed_rows"], 1)
        self.assertEqual(out["top_nonnumeric_as_filed_values"], {"XXEC, INC.":1})
        self.assertEqual(out["audit"]["numeric_reference_tokens"], 0)

    def test_zero_sentinel_is_not_a_group_reference(self):
        filers = {"A":{"submission_type":"13F-HR","report_type":"13F HOLDINGS REPORT"}}
        out = audit_infotable_rows(INFO_HEADER, iter([["A","1","0"]]), filers, self.group_graph())
        self.assertEqual(out["audit"]["zero_only_rows"], 1)
        self.assertEqual(out["audit"]["zero_sentinel_tokens"], 1)
        self.assertEqual(out["audit"]["matched_group_tokens"], 0)

    def test_unmatched_numeric_sequence_is_preserved(self):
        filers = {"A":{"submission_type":"13F-HR","report_type":"13F HOLDINGS REPORT"}}
        out = audit_infotable_rows(INFO_HEADER, iter([["A","1","4"]]), filers, self.group_graph())
        self.assertEqual(out["audit"]["unmatched_sequence_tokens"], 1)
        self.assertEqual(out["unmatched_examples"][0]["sequence"], 4)

    def test_notice_accessions_are_not_zero_holdings_inferred(self):
        filers = {"N":{"submission_type":"13F-NT","report_type":"13F NOTICE"}}
        out = audit_infotable_rows(INFO_HEADER, iter([["N","1","0"]]), filers, {})
        self.assertEqual(out["audit"]["notice_info_rows"], 1)
        self.assertEqual(out["audit"]["zero_only_rows"], 1)


if __name__ == "__main__":
    unittest.main()

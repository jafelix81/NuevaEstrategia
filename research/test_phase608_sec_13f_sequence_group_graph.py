import unittest

from research.phase608_sec_13f_sequence_group_graph import (
    attach_infotable_rows,
    build_group_aware_graph,
    build_sequence_groups,
    parse_manager_field,
    reconcile_summary_page,
)


OM_HEADER = ["ACCESSION_NUMBER","SEQUENCENUMBER","CIK","FORM13FFILENUMBER","CRDNUMBER","SEC_FILENUMBER","NAME"]
INFO_HEADER = ["ACCESSION_NUMBER","INFOTABLE_SK","OTHERMANAGER"]
SUMMARY_HEADER = ["ACCESSION_NUMBER","OTHERINCLUDEDMANAGERSCOUNT"]


class Phase608Tests(unittest.TestCase):
    def allspring_members(self):
        return [
            ["A","1","0001327354","028-11406","000110841","801-58237","Allspring Funds Management, LLC"],
            ["A","1","","","","","Allspring Funds Management, LLC reporting on behalf of Morgan Stanley Smith Barney, LLC"],
            ["A","2","0001075869","028-04413","000104973","801-21122","Allspring Global Investments, LLC"],
            ["A","2","","","","","Allspring Global Investments, LLC reporting on behalf of SEI INVESTMENTS CO"],
            ["A","2","","","","","Allspring Global Investments, LLC reporting on behalf of UBS ASSET MANAGEMENT AMERICAS INC"],
        ]

    def test_numeric_sequence_list_is_parsed(self):
        out = parse_manager_field("1, 2 3")
        self.assertEqual(out["status"], "NUMERIC_GROUP_REFS")
        self.assertEqual(out["sequence_refs"], [1,2,3])

    def test_zero_is_a_no_group_sentinel(self):
        out = parse_manager_field("0")
        self.assertEqual(out["status"], "ZERO_ONLY")
        self.assertEqual(out["zero_count"], 1)
        self.assertEqual(out["sequence_refs"], [])

    def test_nonnumeric_comma_name_is_preserved_whole(self):
        out = parse_manager_field("XXEC, INC.")
        self.assertEqual(out["status"], "NONNUMERIC_AS_FILED")
        self.assertEqual(out["raw_value"], "XXEC, INC.")
        self.assertEqual(out["sequence_refs"], [])

    def test_mixed_numeric_and_text_is_not_partially_parsed(self):
        out = parse_manager_field("1, XXEC")
        self.assertEqual(out["status"], "NONNUMERIC_AS_FILED")
        self.assertEqual(out["sequence_refs"], [])

    def test_all_spring_sequence_numbers_define_groups_not_unique_members(self):
        out = build_sequence_groups(OM_HEADER, self.allspring_members())
        groups = out["groups"]
        self.assertEqual(out["audit"]["member_rows"], 5)
        self.assertEqual(out["audit"]["group_count"], 2)
        self.assertEqual(out["audit"]["multi_member_groups"], 2)
        self.assertEqual(groups[("A",1)]["member_count"], 2)
        self.assertEqual(groups[("A",2)]["member_count"], 3)
        self.assertEqual(groups[("A",1)]["member_attribution"], "GROUP_ONLY")
        self.assertEqual(len({m["member_key"] for g in groups.values() for m in g["members"]}), 5)

    def test_names_alone_do_not_become_stable_identity(self):
        rows = [["A","1","","","","","Manager Name"]]
        out = build_sequence_groups(OM_HEADER, rows)
        self.assertEqual(out["groups"][("A",1)]["members"][0]["identity_status"], "NO_STABLE_IDENTIFIER")

    def test_identical_member_rows_are_preserved_and_flagged(self):
        row = ["A","1","0000000001","028-00001","","","Manager"]
        out = build_sequence_groups(OM_HEADER, [row,row])
        self.assertEqual(out["audit"]["member_rows"], 2)
        self.assertEqual(out["audit"]["exact_duplicate_member_rows"], 1)
        self.assertEqual(out["groups"][("A",1)]["member_count"], 2)

    def test_group_references_attach_to_group_not_individual_members(self):
        group_graph = build_sequence_groups(OM_HEADER, self.allspring_members())
        rows = [["A","1","1"],["A","2","2"],["A","3","1,2"]]
        out = attach_infotable_rows(group_graph, INFO_HEADER, rows)
        self.assertEqual(out["audit"]["numeric_reference_tokens"], 4)
        self.assertEqual(out["audit"]["matched_group_tokens"], 4)
        self.assertEqual(out["audit"]["group_only_reference_tokens"], 4)
        self.assertEqual(out["audit"]["single_member_group_tokens"], 0)
        self.assertTrue(all(x["member_attribution"] == "GROUP_ONLY" for x in out["links"]))

    def test_unmatched_numeric_reference_is_not_repaired(self):
        group_graph = build_sequence_groups(OM_HEADER, [
            ["D","1","","","","","A"],["D","2","","","","","B"],
            ["D","3","","","","","C"],["D","8","","","","","D"],
        ])
        out = attach_infotable_rows(group_graph, INFO_HEADER, [["D","1","4"]])
        self.assertEqual(out["audit"]["unmatched_sequence_tokens"], 1)
        self.assertEqual(out["links"][0]["status"], "UNMATCHED_SEQUENCE")

    def test_nonnumeric_label_and_zero_do_not_create_group_links(self):
        group_graph = build_sequence_groups(OM_HEADER, self.allspring_members())
        rows = [["A","1","XXEC, INC."],["A","2","0"]]
        out = attach_infotable_rows(group_graph, INFO_HEADER, rows)
        self.assertEqual(out["audit"]["nonnumeric_as_filed_rows"], 1)
        self.assertEqual(out["nonnumeric_as_filed_values"], {"XXEC, INC.":1})
        self.assertEqual(out["audit"]["zero_only_rows"], 1)
        self.assertEqual(out["links"], [])

    def test_summary_page_counts_member_rows_not_distinct_groups(self):
        graph = build_sequence_groups(OM_HEADER, self.allspring_members())
        out = reconcile_summary_page(graph, SUMMARY_HEADER, [["A","5"]])
        self.assertEqual(out["compared"], 1)
        self.assertEqual(out["mismatches"], 0)


if __name__ == "__main__":
    unittest.main()

import unittest

from research.phase337_sec_xbrl_common_role_standard_taxonomy_audit import (
    classify_alias,
    compare_common_role_labels,
    compare_documentation,
    parse_linkbase,
)


class Phase337Tests(unittest.TestCase):
    def test_one_sided_default_label_is_not_a_common_role_conflict(self):
        members = [
            {"labels": [
                {"role": "role/label", "language": "en", "text": "Preferred stock member"},
                {"role": "role/terseLabel", "language": "en", "text": "5.50% preferred"},
            ]},
            {"labels": [
                {"role": "role/terseLabel", "language": "en", "text": "5.50% preferred"},
            ]},
        ]
        result = compare_common_role_labels(members)
        self.assertTrue(result["common_role_labels_match"])
        self.assertEqual(result["matching_common_role_keys"], [
            {"role": "role/terseLabel", "language": "en"}
        ])
        self.assertEqual(result["one_sided_role_keys"], [
            {"role": "role/label", "language": "en"}
        ])

    def test_same_role_different_text_is_a_conflict(self):
        members = [
            {"labels": [{"role": "role/label", "language": "en", "text": "Class A common stock"}]},
            {"labels": [{"role": "role/label", "language": "en", "text": "Common stock"}]},
        ]
        result = compare_common_role_labels(members)
        self.assertFalse(result["common_role_labels_match"])
        self.assertEqual(len(result["conflicting_common_role_keys"]), 1)
        self.assertEqual(classify_alias(result, "INCOMPLETE"), "COMMON_ROLE_LABEL_CONFLICT_NOT_MERGED")

    def test_no_common_role_is_not_treated_as_a_match(self):
        members = [
            {"labels": [{"role": "role/label", "language": "en", "text": "A"}]},
            {"labels": [{"role": "role/terseLabel", "language": "en", "text": "A"}]},
        ]
        result = compare_common_role_labels(members)
        self.assertFalse(result["common_role_labels_match"])
        self.assertEqual(result["common_role_keys"], [])

    def test_documentation_match_is_candidate_only_not_merge(self):
        common = {
            "common_role_keys": [{"role": "role/label", "language": "en"}],
            "matching_common_role_keys": [{"role": "role/label", "language": "en"}],
            "conflicting_common_role_keys": [],
            "one_sided_role_keys": [],
            "common_role_labels_match": True,
        }
        members = [{"documentation": ["Class A common stock member"]},
                   {"documentation": ["Class A common stock member"]}]
        self.assertEqual(compare_documentation(members), "MATCH")
        self.assertEqual(
            classify_alias(common, compare_documentation(members)),
            "CANDIDATE_COMMON_ROLE_LABEL_AND_DOCUMENTATION_MATCH_NOT_MERGED",
        )

    def test_documentation_conflict_blocks_candidate(self):
        self.assertEqual(
            compare_documentation([
                {"documentation": ["Class A common stock member"]},
                {"documentation": ["Common stock member"]},
            ]),
            "CONFLICT",
        )

    def test_linkbase_parser_extracts_standard_label_and_documentation_roles(self):
        raw = b'''<?xml version="1.0"?>
        <link:linkbase xmlns:link="http://www.xbrl.org/2003/linkbase"
                       xmlns:xlink="http://www.w3.org/1999/xlink"
                       xmlns:xml="http://www.w3.org/XML/1998/namespace">
          <link:labelLink xlink:type="extended">
            <link:loc xlink:type="locator" xlink:label="loc1"
                      xlink:href="us-gaap.xsd#us-gaap_CommonClassAMember"/>
            <link:label xlink:type="resource" xlink:label="lab1"
                        xlink:role="http://www.xbrl.org/2003/role/label" xml:lang="en">
              Class A common stock member
            </link:label>
            <link:labelArc xlink:type="arc" xlink:from="loc1" xlink:to="lab1"/>
          </link:labelLink>
          <link:labelLink xlink:type="extended">
            <link:loc xlink:type="locator" xlink:label="loc2"
                      xlink:href="us-gaap.xsd#us-gaap_CommonClassAMember"/>
            <link:label xlink:type="resource" xlink:label="doc1"
                        xlink:role="http://www.xbrl.org/2003/role/documentation" xml:lang="en">
              A class of common stock designated as Class A.
            </link:label>
            <link:labelArc xlink:type="arc" xlink:from="loc2" xlink:to="doc1"/>
          </link:labelLink>
        </link:linkbase>'''
        got = parse_linkbase(raw, {"CommonClassAMember", "CommonStockMember"})
        self.assertEqual(got["CommonClassAMember"][0]["text"], "Class A common stock member")
        self.assertEqual(got["CommonClassAMember"][1]["role"],
                         "http://www.xbrl.org/2003/role/documentation")


if __name__ == "__main__":
    unittest.main()

import unittest

from research.phase336_sec_xbrl_taxonomy_linkbase_audit import (
    classify_alias_evidence,
    parse_instance_metadata,
    parse_label_linkbase,
    parse_schema,
)


class Phase336Tests(unittest.TestCase):
    def test_instance_schema_refs_and_namespace_prefixes(self):
        raw = b'''<?xml version="1.0"?>
        <xbrl xmlns="http://www.xbrl.org/2003/instance"
              xmlns:link="http://www.xbrl.org/2003/linkbase"
              xmlns:xlink="http://www.w3.org/1999/xlink"
              xmlns:pcg="https://example.test/pcg">
          <link:schemaRef xlink:type="simple" xlink:href="pcg-2022.xsd"/>
        </xbrl>'''
        got = parse_instance_metadata(raw)
        self.assertEqual(got["namespaces"]["pcg"], "https://example.test/pcg")
        self.assertEqual(got["schema_refs"], ["pcg-2022.xsd"])

    def test_schema_extracts_target_namespace_member_and_linkbase_refs(self):
        raw = b'''<?xml version="1.0"?>
        <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
                   xmlns:link="http://www.xbrl.org/2003/linkbase"
                   xmlns:xlink="http://www.w3.org/1999/xlink"
                   targetNamespace="https://example.test/pcg">
          <xs:import namespace="https://example.test/us-gaap" schemaLocation="us-gaap.xsd"/>
          <xs:element name="SeriesMember" type="xs:string">
            <xs:annotation><xs:documentation>Series A preferred</xs:documentation></xs:annotation>
          </xs:element>
          <xs:annotation><xs:appinfo>
            <link:linkbaseRef xlink:type="simple" xlink:href="pcg_lab.xml"/>
          </xs:appinfo></xs:annotation>
        </xs:schema>'''
        got = parse_schema(raw)
        self.assertEqual(got["target_namespace"], "https://example.test/pcg")
        self.assertEqual(got["elements"]["SeriesMember"]["documentation"], ["Series A preferred"])
        self.assertEqual(got["imports"][0]["schema_location"], "us-gaap.xsd")
        self.assertEqual(got["linkbase_refs"], ["pcg_lab.xml"])

    def test_label_linkbase_resolves_locator_arc_and_resource(self):
        raw = b'''<?xml version="1.0"?>
        <link:linkbase xmlns:link="http://www.xbrl.org/2003/linkbase"
                       xmlns:xlink="http://www.w3.org/1999/xlink"
                       xmlns:xml="http://www.w3.org/XML/1998/namespace">
          <link:labelLink xlink:type="extended" xlink:role="http://www.xbrl.org/2003/role/link">
            <link:loc xlink:type="locator" xlink:label="loc1" xlink:href="pcg.xsd#pcg_SeriesMember"/>
            <link:label xlink:type="resource" xlink:label="lab1"
                        xlink:role="http://www.xbrl.org/2003/role/label" xml:lang="en-US">
              Series A preferred
            </link:label>
            <link:labelArc xlink:type="arc" xlink:from="loc1" xlink:to="lab1"
                           xlink:arcrole="http://www.xbrl.org/2003/arcrole/concept-label"/>
          </link:labelLink>
        </link:linkbase>'''
        got = parse_label_linkbase(raw, {"SeriesMember"})
        self.assertEqual(got["SeriesMember"][0]["text"], "Series A preferred")
        self.assertEqual(
            got["SeriesMember"][0]["role"],
            "http://www.xbrl.org/2003/role/label",
        )

    def test_identical_labels_and_definitions_remain_candidate_not_merged(self):
        members = [
            {"preferred_label_texts": ["5.50% preferred"], "schema_documentation": ["same definition"]},
            {"preferred_label_texts": ["5.50% preferred"], "schema_documentation": ["same definition"]},
        ]
        self.assertEqual(
            classify_alias_evidence(members),
            "CANDIDATE_LABEL_AND_SCHEMA_DOC_MATCH_NOT_MERGED",
        )

    def test_identical_labels_without_definitions_do_not_authorize_merge(self):
        members = [
            {"preferred_label_texts": ["5.50% preferred"], "schema_documentation": []},
            {"preferred_label_texts": ["5.50% preferred"], "schema_documentation": []},
        ]
        self.assertEqual(
            classify_alias_evidence(members),
            "CANDIDATE_LABEL_MATCH_DEFINITION_NOT_CONFIRMED_NOT_MERGED",
        )

    def test_different_labels_are_not_merged(self):
        members = [
            {"preferred_label_texts": ["Common Class A"], "schema_documentation": []},
            {"preferred_label_texts": ["Common Stock"], "schema_documentation": []},
        ]
        self.assertEqual(
            classify_alias_evidence(members),
            "LABELS_DIFFER_OR_AMBIGUOUS_NOT_MERGED",
        )

    def test_missing_label_quarantines_alias_group(self):
        members = [
            {"preferred_label_texts": ["5.50% preferred"], "schema_documentation": []},
            {"preferred_label_texts": [], "schema_documentation": []},
        ]
        self.assertEqual(
            classify_alias_evidence(members),
            "LINKBASE_LABEL_INCOMPLETE_NOT_MERGED",
        )

    def test_empty_member_group_is_not_admitted(self):
        self.assertEqual(classify_alias_evidence([]), "NO_MEMBER_EVIDENCE")


if __name__ == "__main__":
    unittest.main()

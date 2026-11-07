import unittest

from research.phase122_sec_13dg_xml_ownership_continuity_audit import (
    group_overlap_pairs, norm_name, number, parse_people, unique_name_map,
)

class Phase122Tests(unittest.TestCase):
    def test_name_normalization(self):
        self.assertEqual(norm_name("Franklin Resources, Inc."), "FRANKLIN RESOURCES INC")

    def test_numeric_parsing(self):
        self.assertEqual(number("1,234,567.00"), 1234567.0)
        self.assertIsNone(number("not reported"))

    def test_13d_schema_extracts_person_cik_group_and_ownership(self):
        raw = """<XML><edgarSubmission><formData><reportingPersons>
        <reportingPersonInfo>
          <reportingPersonCIK>0000123456</reportingPersonCIK>
          <reportingPersonName>Example Adviser, Inc.</reportingPersonName>
          <memberOfGroup>b</memberOfGroup>
          <soleVotingPower>1000</soleVotingPower>
          <soleDispositivePower>1000</soleDispositivePower>
          <aggregateAmountOwned>1000</aggregateAmountOwned>
          <percentOfClass>5.1</percentOfClass>
        </reportingPersonInfo>
        </reportingPersons></formData></edgarSubmission></XML>"""
        people = parse_people(raw, "13D")
        self.assertEqual(len(people), 1)
        self.assertEqual(people[0]["cik"], "0000123456")
        self.assertEqual(people[0]["group"], "b")
        self.assertEqual(people[0]["amount"], 1000.0)
        self.assertEqual(people[0]["percent"], 5.1)

    def test_13g_schema_is_not_parsed_as_13d(self):
        raw = """<XML><edgarSubmission><formData><coverPageHeaderReportingPersonDetails>
        <reportingPersonName>Example Bank</reportingPersonName>
        <reportingPersonBeneficiallyOwnedAggregateNumberOfShares>2,500</reportingPersonBeneficiallyOwnedAggregateNumberOfShares>
        <classPercent>6.2</classPercent>
        </coverPageHeaderReportingPersonDetails></formData></edgarSubmission></XML>"""
        people = parse_people(raw, "13G")
        self.assertEqual(people[0]["amount"], 2500.0)
        self.assertEqual(people[0]["percent"], 6.2)
        self.assertIsNone(people[0]["cik"])

    def test_group_overlap_is_diagnostic_not_aggregation(self):
        people = [
            {"name":"Parent", "group":"b", "amount":100.0, "percent":5.0},
            {"name":"Subsidiary", "group":"b", "amount":100.0, "percent":5.0},
            {"name":"Other", "group":"b", "amount":40.0, "percent":2.0},
        ]
        overlaps = group_overlap_pairs(people, "13D")
        self.assertEqual(len(overlaps), 1)
        self.assertEqual(overlaps[0]["amount"], 100.0)
        self.assertEqual(group_overlap_pairs(people, "13G"), [])

    def test_duplicate_names_are_ambiguous_not_silently_overwritten(self):
        people = [
            {"name":"Same Name", "name_key":"SAME NAME"},
            {"name":"Same Name", "name_key":"SAME NAME"},
        ]
        self.assertIsNone(unique_name_map(people))

    def test_missing_xml_is_not_an_empty_ownership_position(self):
        self.assertIsNone(parse_people("<DOCUMENT><TEXT>legacy HTML</TEXT></DOCUMENT>", "13D"))

if __name__ == "__main__":
    unittest.main()

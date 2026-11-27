import unittest

from research.phase313_nport_sgml_header_reconciliation import (
    extract_primary_xml,
    identity_state,
    parse_header_identity,
    ticker_overlap_state,
    local_name,
    xml_values,
)
import xml.etree.ElementTree as ET

HEADER = """<SEC-HEADER>
ACCESSION NUMBER: 0001145549-22-060851
<SERIES-AND-CLASSES-CONTRACTS-DATA>
<EXISTING-SERIES-AND-CLASSES>
<SERIES>
<OWNER-CIK>0000811030
<SERIES-ID>S000043717
<SERIES-NAME>Otter Creek Long/Short Opportunity Fund
<CLASS-CONTRACT>
<CLASS-CONTRACT-ID>C000135565
<CLASS-CONTRACT-NAME>Institutional Class
</CLASS-CONTRACT>
<CLASS-CONTRACT>
<CLASS-CONTRACT-ID>C000135566
<CLASS-CONTRACT-NAME>Investor Class
</CLASS-CONTRACT>
</SERIES>
</EXISTING-SERIES-AND-CLASSES>
</SERIES-AND-CLASSES-CONTRACTS-DATA>
</SEC-HEADER>
"""

XML = """<?xml version="1.0" encoding="UTF-8"?>
<edgarSubmission xmlns="http://www.sec.gov/edgar/nport">
  <headerData><submissionType>NPORT-P/A</submissionType></headerData>
  <formData><genInfo>
    <seriesId>S000043717</seriesId>
    <seriesName>Otter Creek Long/Short Opportunity Fund</seriesName>
    <classId>C000135565</classId>
    <classId>C000135566</classId>
  </genInfo></formData>
</edgarSubmission>
"""


class Phase313SgmlHeaderTests(unittest.TestCase):
    def test_unclosed_sgml_series_and_class_tags_match_xml(self):
        parsed = parse_header_identity(HEADER + "<DOCUMENT>")
        self.assertEqual(parsed["series_ids"], ["S000043717"])
        self.assertEqual(parsed["class_ids"], ["C000135565", "C000135566"])
        self.assertEqual(parsed["series_names"], ["Otter Creek Long/Short Opportunity Fund"])
        root = ET.fromstring(XML)
        self.assertEqual(identity_state(parsed["series_ids"], xml_values(root, "seriesId")), "MATCH")
        self.assertEqual(identity_state(parsed["class_ids"], xml_values(root, "classId")), "MATCH")

    def test_header_parser_does_not_read_document_xml(self):
        parsed = parse_header_identity("<SEC-HEADER>only header</SEC-HEADER><DOCUMENT>" + XML + "</DOCUMENT>")
        self.assertEqual(parsed["series_ids"], [])
        self.assertEqual(parsed["class_ids"], [])

    def test_header_only_is_explicit(self):
        self.assertEqual(identity_state(["S1"], []), "HEADER_ONLY")
        self.assertEqual(identity_state(["C1"], []), "HEADER_ONLY")

    def test_xml_only_is_explicit(self):
        self.assertEqual(identity_state([], ["S1"]), "XML_ONLY")

    def test_missing_both_is_explicit(self):
        self.assertEqual(identity_state([], []), "MISSING_BOTH")

    def test_mismatch_is_not_forced_to_match(self):
        self.assertEqual(identity_state(["S1"], ["S2"]), "MISMATCH")
        self.assertEqual(identity_state(["S1", "S2"], ["S1"]), "MISMATCH")

    def test_primary_xml_uses_exact_form(self):
        submission = (
            "<DOCUMENT><TYPE>EX-99</TYPE><TEXT>not xml</TEXT></DOCUMENT>"
            "<DOCUMENT><TYPE>NPORT-P/A</TYPE><TEXT><XML>" + XML + "</XML></TEXT></DOCUMENT>"
        )
        self.assertIn("<edgarSubmission", extract_primary_xml(submission, "NPORT-P/A"))
        with self.assertRaisesRegex(ValueError, "primary_nport_xml_document_not_found"):
            extract_primary_xml(submission, "NPORT-P")

    def test_ticker_string_overlap_keeps_missing_as_unknown(self):
        universe = {"AAPL", "NVDA", "TSLA"}
        self.assertEqual(ticker_overlap_state("NVDA", universe), "MATCH")
        self.assertEqual(ticker_overlap_state("MSFT", universe), "NO_STRING_MATCH")
        self.assertEqual(ticker_overlap_state("", universe), "UNKNOWN_NOT_REPORTED")
        self.assertEqual(ticker_overlap_state("N/A", universe), "UNKNOWN_NOT_REPORTED")


if __name__ == "__main__":
    unittest.main()

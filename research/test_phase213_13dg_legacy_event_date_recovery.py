import unittest
from datetime import date

from phase213_13dg_legacy_event_date_recovery import (
    extract_event, extract_amendment_marker, family, parse_date,
    primary_document, summarize, validate_header,
)


class Phase213Tests(unittest.TestCase):
    def test_13d_xml_event_tag(self):
        value, method = extract_event("<edgarSubmission><dateOfEvent>03/14/2025</dateOfEvent></edgarSubmission>")
        self.assertEqual(value, date(2025, 3, 14))
        self.assertEqual(method, "XML_dateOfEvent")

    def test_13g_xml_event_tag(self):
        value, method = extract_event("<edgarSubmission><eventDateRequiresFilingThisStatement>09/30/2024</eventDateRequiresFilingThisStatement></edgarSubmission>")
        self.assertEqual(value, date(2024, 9, 30))
        self.assertEqual(method, "XML_eventDateRequiresFilingThisStatement")

    def test_html_date_before_label(self):
        value, method = extract_event("<html><body>December 31, 2022 (Date of Event Which Requires Filing of this Statement)</body></html>")
        self.assertEqual(value, date(2022, 12, 31))
        self.assertEqual(method, "HTML_LABEL_NEAREST_DATE")

    def test_html_date_after_label(self):
        value, method = extract_event("<html><body>Date of Event Which Requires Filing of this Statement: November 30, 2017</body></html>")
        self.assertEqual(value, date(2017, 11, 30))
        self.assertEqual(method, "HTML_LABEL_NEAREST_DATE")

    def test_html_label_variant_without_of(self):
        value, _ = extract_event("<html><body>January 22, 2016 (Date of Event Which Requires Filing this Statement)</body></html>")
        self.assertEqual(value, date(2016, 1, 22))

    def test_html_no_label_is_not_imputed(self):
        value, method = extract_event("<html><body>CUSIP 123456789 December 31, 2022</body></html>")
        self.assertIsNone(value)
        self.assertEqual(method, "NO_LABEL")

    def test_label_without_unambiguous_date(self):
        value, method = extract_event("<html><body>(Date of Event Which Requires Filing of this Statement) N/A</body></html>")
        self.assertIsNone(value)
        self.assertEqual(method, "LABEL_NO_DATE")

    def test_two_digit_year_is_not_inferred(self):
        self.assertIsNone(parse_date("7/03/17"))

    def test_html_amendment_underscore(self):
        value, method = extract_amendment_marker("<html><body>(AMENDMENT NO. _6_)*</body></html>", False)
        self.assertEqual(value, 6)
        self.assertEqual(method, "HTML_COVER_AMENDMENT_NUMBER")

    def test_html_amendment_hash(self):
        value, _ = extract_amendment_marker("<html><body>Amendment # 1</body></html>", False)
        self.assertEqual(value, 1)

    def test_xml_amendment_number(self):
        value, method = extract_amendment_marker("<edgarSubmission><amendmentNo>10</amendmentNo></edgarSubmission>", True)
        self.assertEqual(value, 10)
        self.assertEqual(method, "XML_AMENDMENT_NO_TAG")

    def test_xml_amendment_absence_is_unknown(self):
        value, method = extract_amendment_marker("<edgarSubmission><submissionType>SCHEDULE 13G</submissionType></edgarSubmission>", True)
        self.assertIsNone(value)
        self.assertEqual(method, "XML_AMENDMENT_NO_ABSENT")

    def test_form_family(self):
        self.assertEqual(family("SC 13D/A"), "13D")
        self.assertEqual(family("SCHEDULE 13G"), "13G")
        self.assertIsNone(family("SC TO-T/A"))

    def test_weighted_summary(self):
        rows = [
            {"event_date": "2024-09-30", "sample_weight": 3.0, "event_date_is_quarter_end": True,
             "filing_minus_event_days": 45, "index_form_suffix_is_amendment": False},
            {"event_date": "", "sample_weight": 1.0, "event_date_is_quarter_end": "",
             "filing_minus_event_days": "", "index_form_suffix_is_amendment": False},
        ]
        result = summarize(rows)
        self.assertEqual(result["event_date_n"], 1)
        self.assertEqual(result["event_date_coverage_sample_weighted_pct"], 75.0)
        self.assertEqual(result["quarter_end_event_date"]["sample_weighted_pct_within_parsed"], 100.0)

    def test_header_validation(self):
        raw = (
            "<SEC-HEADER>\n<ACCEPTANCE-DATETIME>20241114121400\n"
            "ACCESSION NUMBER: 0001412741-24-000004\n"
            "CONFORMED SUBMISSION TYPE: SCHEDULE 13G\n"
            "FILED AS OF DATE: 20241114\n</SEC-HEADER>"
        )
        row = {"accession": "0001412741-24-000004", "acceptance_datetime": "20241114121400",
               "filing_date_header": "2024-11-14", "form": "SC 13G"}
        validate_header(raw, row)

    def test_primary_document(self):
        raw = (
            "<DOCUMENT><TYPE>EX-99.1\n<TEXT>Exhibit</TEXT></DOCUMENT>"
            "<DOCUMENT><TYPE>SC 13G/A\n<TEXT>Primary</TEXT></DOCUMENT>"
        )
        self.assertEqual(primary_document(raw), ("SC 13G/A", "Primary"))


if __name__ == "__main__":
    unittest.main()

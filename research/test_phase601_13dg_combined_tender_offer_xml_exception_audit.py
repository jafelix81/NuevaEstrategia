from __future__ import annotations

import unittest

from research.phase601_13dg_combined_tender_offer_xml_exception_audit import (
    is_documented_combined_13d_exception,
    normalize_form,
    parse_sec_header,
)


GENCO_COMBINED_HEADER = """<SEC-HEADER>
<ACCEPTANCE-DATETIME>20260507172214</ACCEPTANCE-DATETIME>
CONFORMED SUBMISSION TYPE: SC TO-T/A
SUBJECT COMPANY:
  COMPANY DATA:
    COMPANY CONFORMED NAME: GENCO SHIPPING & TRADING LTD
    CENTRAL INDEX KEY: 0001326200
  FILING VALUES:
    FORM TYPE: SC 13D/A
SUBJECT COMPANY:
  COMPANY DATA:
    COMPANY CONFORMED NAME: GENCO SHIPPING & TRADING LTD
    CENTRAL INDEX KEY: 0001326200
  FILING VALUES:
    FORM TYPE: SC TO-T/A
FILED BY:
  COMPANY DATA:
    COMPANY CONFORMED NAME: DIANA SHIPPING INC.
    CENTRAL INDEX KEY: 0001318885
  FILING VALUES:
    FORM TYPE: SC TO-T/A
</SEC-HEADER>"""


class Phase601CombinedTenderOfferExceptionTests(unittest.TestCase):
    def test_genco_combination_header_is_parsed_by_role(self):
        parsed = parse_sec_header(GENCO_COMBINED_HEADER)
        self.assertEqual(parsed["conformed_submission_type"], "SC TO-T/A")
        self.assertEqual(parsed["subject_form_types"], ["SC 13D/A", "SC TO-T/A"])
        self.assertEqual(parsed["subject_ciks"], ["0001326200"])

    def test_sec_documented_combined_13d_a_exception_applies(self):
        parsed = parse_sec_header(GENCO_COMBINED_HEADER)
        self.assertTrue(is_documented_combined_13d_exception("SC 13D/A", parsed, False))

    def test_schedule_alias_normalizes(self):
        self.assertEqual(normalize_form("SCHEDULE 13D/A"), "SC 13D/A")

    def test_standalone_13d_a_missing_xml_is_not_exempt(self):
        parsed = {
            "conformed_submission_type": "SCHEDULE 13D/A",
            "subject_form_types": ["SC 13D/A"],
        }
        self.assertFalse(is_documented_combined_13d_exception("SC 13D/A", parsed, False))

    def test_combined_tender_with_13g_a_is_not_exempt(self):
        parsed = {
            "conformed_submission_type": "SC TO-T/A",
            "subject_form_types": ["SC 13G/A", "SC TO-T/A"],
        }
        self.assertFalse(is_documented_combined_13d_exception("SC 13G/A", parsed, False))

    def test_combined_tender_without_13d_a_subject_form_is_not_exempt(self):
        parsed = {
            "conformed_submission_type": "SC TO-T/A",
            "subject_form_types": ["SC TO-T/A"],
        }
        self.assertFalse(is_documented_combined_13d_exception("SC 13D/A", parsed, False))

    def test_xml_present_needs_no_exception(self):
        parsed = parse_sec_header(GENCO_COMBINED_HEADER)
        self.assertFalse(is_documented_combined_13d_exception("SC 13D/A", parsed, True))

    def test_missing_sec_header_fails_closed(self):
        with self.assertRaises(ValueError):
            parse_sec_header("ACCESSION NUMBER: 0000000000-26-000001")


if __name__ == "__main__":
    unittest.main()

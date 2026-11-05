import unittest
from research.phase125_sec_13dg_exact_cusip_audit import (
    classify_submission, cusip_check_digit, cusip_status,
    classify_xml_cusip, extract_legacy_cusips, normalize_cusip, weighted_rate,
)

class Phase125Tests(unittest.TestCase):
    def test_known_cusip_checksums(self):
        self.assertTrue(cusip_check_digit("037833100"))
        self.assertTrue(cusip_check_digit("594918104"))
        self.assertFalse(cusip_check_digit("584680106"))

    def test_exact_cusip_after_label(self):
        raw = "<DOCUMENT><TYPE>SC 13D/A</TYPE><TEXT><p>CUSIP No. 037833100</p></TEXT></DOCUMENT>"
        self.assertEqual(extract_legacy_cusips(raw), ["037833100"])

    def test_exact_cusip_before_parenthesized_label(self):
        raw = "<DOCUMENT><TYPE>SC 13D</TYPE><TEXT><p>037833100</p><p>(CUSIP Number)</p></TEXT></DOCUMENT>"
        self.assertEqual(extract_legacy_cusips(raw), ["037833100"])

    def test_does_not_truncate_isin_or_ten_digit_cik(self):
        raw = """<DOCUMENT><TYPE>SC 13D</TYPE><TEXT>
        <p>CUSIP No. US12021A1079</p><p>CUSIP No. 0001875609</p>
        </TEXT></DOCUMENT>"""
        self.assertEqual(extract_legacy_cusips(raw), [])

    def test_rejects_placeholder(self):
        raw = "<DOCUMENT><TYPE>SC 13D</TYPE><TEXT><p>CUSIP No. 000000000</p></TEXT></DOCUMENT>"
        self.assertEqual(extract_legacy_cusips(raw), [])

    def test_xml_placeholder_is_distinguished_from_invalid_format(self):
        self.assertEqual(classify_xml_cusip("000000000")[0], "XML_PLACEHOLDER")
        self.assertEqual(classify_xml_cusip(None)[0], "MISSING")
        self.assertEqual(classify_xml_cusip("US12021A1079")[0], "INVALID_XML_CUSIP_FORMAT")

    def test_ambiguous_candidates_are_not_collapsed(self):
        self.assertEqual(cusip_status(["42234Q102", "376536603"])[0], "AMBIGUOUS")

    def test_invalid_checksum_is_flagged(self):
        status, value, valid = cusip_status(["584680106"])
        self.assertEqual(status, "UNIQUE_CHECKSUM_INVALID")
        self.assertEqual(value, "584680106")
        self.assertFalse(valid)

    def test_normalize_requires_exact_nine_characters(self):
        self.assertIsNone(normalize_cusip("US12021A1079"))
        self.assertIsNone(normalize_cusip("0001875609"))
        self.assertEqual(normalize_cusip("037833100"), "037833100")

    def test_index_alias_requires_non_13dg_header_and_documents(self):
        accession = "0001104659-25-001464"
        raw = """<SEC-HEADER>
ACCESSION NUMBER: 0001104659-25-001464
CONFORMED SUBMISSION TYPE: SC TO-T/A
FILED AS OF DATE: 20250107
</SEC-HEADER>
<DOCUMENT><TYPE>SC TO-T/A</TYPE></DOCUMENT>
<DOCUMENT><TYPE>EX-99.(A)(5)(B)</TYPE></DOCUMENT>"""
        status, header, _ = classify_submission("SC 13D/A", raw, accession, "2025-01-07")
        self.assertEqual(status, "INDEX_ALIAS_NON_13DG")
        self.assertEqual(header["form"], "SC TO-T/A")

    def test_mixed_form_submission_remains_unresolved(self):
        accession = "0000000000-26-000001"
        raw = """<SEC-HEADER>
ACCESSION NUMBER: 0000000000-26-000001
CONFORMED SUBMISSION TYPE: SC TO-T/A
FILED AS OF DATE: 20260105
</SEC-HEADER>
<DOCUMENT><TYPE>SC TO-T/A</TYPE></DOCUMENT>
<DOCUMENT><TYPE>SC 13D/A</TYPE></DOCUMENT>"""
        self.assertEqual(classify_submission("SC 13D/A", raw, accession, "2026-01-05")[0], "UNRESOLVED_FORM_CONFLICT")

    def test_weighted_rate(self):
        rows = [{"sample_weight": 10, "flag": True}, {"sample_weight": 30, "flag": False}]
        self.assertAlmostEqual(weighted_rate(rows, lambda r: r["flag"]), 0.25)

if __name__ == "__main__":
    unittest.main()

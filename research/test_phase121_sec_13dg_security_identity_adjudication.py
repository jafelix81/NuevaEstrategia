import unittest

from research.phase121_sec_13dg_security_identity_adjudication import (
    ADJUDICATIONS, cusips_from_text, family_of, legacy_persons, norm_cusip,
    parse_xml, parse_legacy, valid_cusip,
)

class Phase121Tests(unittest.TestCase):
    def test_cusip_check_digit_and_placeholder(self):
        self.assertTrue(valid_cusip("86887Q109"))
        self.assertTrue(valid_cusip("46131T507"))
        self.assertIsNone(norm_cusip("000000000"))

    def test_form_family(self):
        self.assertEqual(family_of("SC 13D/A"),"13D")
        self.assertEqual(family_of("SCHEDULE 13G"),"13G")
        self.assertIsNone(family_of("SC 13F"))

    def test_legacy_cusip_split_across_tokens(self):
        self.assertEqual(cusips_from_text("CUSIP No. 46131T 507"),["46131T507"])

    def test_legacy_cusip_precedes_label(self):
        self.assertEqual(cusips_from_text("78137L105 (CUSIP Number)"),["78137L105"])

    def test_legacy_cusip_parser_avoids_month_date_false_positive(self):
        self.assertEqual(cusips_from_text("CUSIP Number April 26, 2021 Date of Event"),[])

    def test_xml_issuer_cusip_number_list_is_supported(self):
        raw="""<XML><edgarSubmission><formData><coverPageHeader>
        <issuerInfo><issuerCIK>0001808898</issuerCIK><issuerCusips>
        <issuerCusipNumber>86887Q109</issuerCusipNumber></issuerCusips></issuerInfo>
        <securitiesClassTitle>Common Stock</securitiesClassTitle></coverPageHeader>
        <coverPageHeaderReportingPersonDetails><reportingPersonName>David Goldman</reportingPersonName></coverPageHeaderReportingPersonDetails>
        </formData></edgarSubmission></XML>"""
        d=parse_xml(raw,"13G")
        self.assertEqual(d["cusip"],"86887Q109")
        self.assertEqual(d["class_title"],"Common Stock")
        self.assertEqual(d["persons"][0]["name"],"David Goldman")

    def test_legacy_class_title_and_no_cusip(self):
        raw="""<DOCUMENT><TYPE>SC 13D</TYPE><TEXT>
        Jefferies Credit Partners BDC Inc.
        Common Stock, par value $0.001 per share
        (Title and Class of Securities)
        None
        (CUSIP Number)
        </TEXT></DOCUMENT>"""
        d=parse_legacy(raw)
        self.assertIsNone(d["cusip"])
        self.assertEqual(d["class_title"],"Common Stock, par value $0.001 per share")

    def test_legacy_person_names_are_deduplicated(self):
        text="""1. NAMES OF REPORTING PERSONS
        Franklin Resources, Inc.
        2. CHECK THE APPROPRIATE BOX
        1. NAMES OF REPORTING PERSONS
        Franklin Resources, Inc."""
        names=legacy_persons(text)
        self.assertEqual(len(names),1)
        self.assertEqual(names[0]["name"],"Franklin Resources, Inc.")

    def test_all_five_mismatch_cases_have_explicit_adjudications(self):
        self.assertEqual(len(ADJUDICATIONS),5)
        self.assertEqual(ADJUDICATIONS["0001445546-26-005159"]["category"],"CROSS_SERIES_LINK_WITHIN_TRUST")
        self.assertEqual(ADJUDICATIONS["0001398344-25-002939"]["category"],"PREDECESSOR_CUSIP_MISKEY_SUSPECTED")

if __name__=="__main__":
    unittest.main()

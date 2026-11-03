import unittest
from phase35_13dg_parser_v2 import parse_xml, parse_legacy, parse_index, group_fingerprint


class ParserTests(unittest.TestCase):
    def test_13d_xml(self):
        x = """<edgarSubmission xmlns="urn:13d"><previousAccessionNumber>0001193125-23-304047</previousAccessionNumber>
        <issuerCIK>0000031005</issuerCIK><issuerCUSIP>123456789</issuerCUSIP>
        <reportingPersonInfo><reportingPersonCIK>0000310051</reportingPersonCIK><reportingPersonName>Alpha Fund LLC</reportingPersonName></reportingPersonInfo>
        <reportingPersonInfo><reportingPersonName>Jane Doe</reportingPersonName></reportingPersonInfo>
        <transactionPurpose>Seeking board representation.</transactionPurpose></edgarSubmission>"""
        r = parse_xml(x)
        self.assertEqual(r["subject_issuer_cik"], "0000031005")
        self.assertEqual(r["previous_accession"], "0001193125-23-304047")
        self.assertEqual(len(r["reporting_persons"]), 2)
        self.assertEqual(r["purpose_text"], "Seeking board representation.")
        self.assertTrue(group_fingerprint(r["reporting_persons"]))

    def test_13g_xml_distinct_schema(self):
        x = """<edgarSubmission xmlns="urn:13g"><previousAccessionNumber>0000092230-25-000001</previousAccessionNumber>
        <issuerCik>0001849998</issuerCik><issuerName>Federated Hermes ETF Trust</issuerName><issuerCusip>31423L503</issuerCusip>
        <eventDateRequiresFilingThisStatement>01/31/2025</eventDateRequiresFilingThisStatement>
        <coverPageHeaderReportingPersonDetails><reportingPersonName>TRUIST FINANCIAL CORP</reportingPersonName>
        <reportingPersonBeneficiallyOwnedAggregateNumberOfShares>153847</reportingPersonBeneficiallyOwnedAggregateNumberOfShares>
        <classPercent>38.0</classPercent><typeOfReportingPerson>IA</typeOfReportingPerson><typeOfReportingPerson>HC</typeOfReportingPerson>
        </coverPageHeaderReportingPersonDetails><filingPersonName>Truist Financial Corporation</filingPersonName></edgarSubmission>"""
        r = parse_xml(x)
        self.assertEqual(r["subject_issuer_cik"], "0001849998")
        self.assertEqual(r["subject_issuer_name"], "Federated Hermes ETF Trust")
        self.assertEqual(r["subject_issuer_cusips"], ["31423L503"])
        self.assertEqual(r["previous_accession"], "0000092230-25-000001")
        self.assertEqual(r["reporting_persons"][0]["name"], "TRUIST FINANCIAL CORP")
        self.assertEqual(r["reporting_persons"][0]["percent"], "38.0")
        self.assertEqual(r["reporting_persons"][0]["types"], "IA|HC")

    def test_legacy_multiple_people(self):
        t = """Item 1: Reporting Person - FMR LLC
        Item 1: Reporting Person - Abigail P. Johnson
        CUSIP #253393102
        JOINT FILING AGREEMENT"""
        r = parse_legacy(t)
        self.assertEqual(r["reporting_person_names"], ["FMR LLC", "Abigail P. Johnson"])
        self.assertEqual(r["cusip"], "253393102")
        self.assertTrue(r["joint_filing_agreement"])

    def test_legacy_cover_page(self):
        t = """CUSIP No. 02390A101
        1 | Name of reporting person
        HELU CARLOS SLIM
        Item 4. Purpose of Transaction
        The reporting persons may seek to influence management.
        Item 5. Interest in Securities"""
        r = parse_legacy(t)
        self.assertIn("HELU CARLOS SLIM", r["reporting_person_names"])
        self.assertIn("influence", r["purpose_text"])

    def test_index_separates_filer_and_subject(self):
        page = """<div>Accepted</div><div>2024-12-27 16:15:12</div>
        <div>HELU CARLOS SLIM (Filed by) CIK: 0001080910</div>
        <div>AMERICA MOVIL SAB DE CV (Subject) CIK: 0001129137</div>"""
        r = parse_index(page)
        self.assertEqual(r["filed_by_cik"], "0001080910")
        self.assertEqual(r["subject_cik"], "0001129137")
        self.assertEqual(r["accepted_at"], "2024-12-27 16:15:12")


if __name__ == "__main__":
    unittest.main()

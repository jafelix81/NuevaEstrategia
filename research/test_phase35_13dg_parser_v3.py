import unittest
from phase35_13dg_parser_v3 import parse_xml, parse_legacy, parse_index, parse_master_index, reporting_person_set_fingerprint

class ParserV3Tests(unittest.TestCase):
    def test_13d_official_hierarchy(self):
        x = """<edgarSubmission xmlns="http://www.sec.gov/edgar/schedule13d">
        <headerData><submissionType>SCHEDULE 13D/A</submissionType><previousAccessionNumber>0001193125-23-304047</previousAccessionNumber>
        <filerInfo><filer><filerCredentials><cik>0000310051</cik></filerCredentials></filer></filerInfo></headerData>
        <formData><coverPageHeader><issuerInfo><issuerCIK>0000031005</issuerCIK><issuerName>Acme Corp</issuerName><issuerCUSIP>123456789</issuerCUSIP></issuerInfo><dateOfEvent>2023-12-01</dateOfEvent></coverPageHeader>
        <reportingPersons><reportingPersonInfo><reportingPersonCIK>0000310051</reportingPersonCIK><reportingPersonName>Alpha Fund LLC</reportingPersonName><memberOfGroup>a</memberOfGroup><aggregateAmountOwned>1000000</aggregateAmountOwned><percentOfClass>6.2</percentOfClass><soleVotingPower>1000000</soleVotingPower><typeOfReportingPerson>IA</typeOfReportingPerson></reportingPersonInfo></reportingPersons>
        <items1To7><item2><filingPersonName>Alpha Fund LLC</filingPersonName></item2><item4><transactionPurpose>Seeking board representation.</transactionPurpose></item4><item5><transactionDesc>Acquired shares.</transactionDesc></item5></items1To7></formData></edgarSubmission>"""
        r = parse_xml(x)
        self.assertEqual(r["subject_issuer_cik"], "0000031005")
        self.assertEqual(r["filer_cik"], "0000310051")
        self.assertEqual(r["previous_accession"], "0001193125-23-304047")
        self.assertEqual(r["reporting_persons"][0]["cik"], "0000310051")
        self.assertEqual(r["reporting_persons"][0]["group_marker"], "a")
        self.assertEqual(r["reporting_persons"][0]["percent"], "6.2")
        self.assertEqual(r["purpose_text"], "Seeking board representation.")

    def test_13g_exact_schema_names_and_nested_cusips(self):
        x = """<edgarSubmission xmlns="http://www.sec.gov/edgar/schedule13g">
        <headerData><submissionType>SCHEDULE 13G/A</submissionType><previousAccessionNumber>0000092230-25-000001</previousAccessionNumber></headerData>
        <formData><coverPageHeader><eventDateRequiresFilingThisStatement>01/31/2025</eventDateRequiresFilingThisStatement>
        <issuerInfo><issuerCik>0001849998</issuerCik><issuerName>Federated Hermes ETF Trust</issuerName><issuerCusips><issuerCusipNumber>31423L503</issuerCusipNumber></issuerCusips></issuerInfo>
        </coverPageHeader><coverPageHeaderReportingPersonDetails><reportingCik>0000092230</reportingCik><reportingPersonName>TRUIST FINANCIAL CORP</reportingPersonName><memberGroup>b</memberGroup>
        <reportingPersonBeneficiallyOwnedNumberOfShares><soleVotingPower>153847</soleVotingPower><sharedVotingPower>0</sharedVotingPower></reportingPersonBeneficiallyOwnedNumberOfShares>
        <reportingPersonBeneficiallyOwnedAggregateNumberOfShares>153847</reportingPersonBeneficiallyOwnedAggregateNumberOfShares><classPercent>38.0</classPercent>
        <typeOfReportingPerson>IA</typeOfReportingPerson><typeOfReportingPerson>HC</typeOfReportingPerson></coverPageHeaderReportingPersonDetails></formData></edgarSubmission>"""
        r = parse_xml(x)
        self.assertEqual(r["subject_issuer_cik"], "0001849998")
        self.assertEqual(r["subject_issuer_name"], "Federated Hermes ETF Trust")
        self.assertEqual(r["subject_issuer_cusips"], ["31423L503"])
        self.assertEqual(r["previous_accession"], "0000092230-25-000001")
        p = r["reporting_persons"][0]
        self.assertEqual(p["cik"], "0000092230")
        self.assertEqual(p["name"], "TRUIST FINANCIAL CORP")
        self.assertEqual(p["group_marker"], "b")
        self.assertEqual(p["percent"], "38.0")
        self.assertEqual(p["sole_voting"], "153847")
        self.assertEqual(p["types"], ["IA", "HC"])
        self.assertTrue(reporting_person_set_fingerprint(r["reporting_persons"]))

    def test_person_set_fingerprint_requires_all_ciks(self):
        self.assertIsNone(reporting_person_set_fingerprint([{"cik": "1"}, {"name": "No CIK"}]))
        self.assertTrue(reporting_person_set_fingerprint([{"cik": "1"}, {"cik": "2"}]))

    def test_index_page_filed_by_and_subject(self):
        page = """<div>SEC Accession No. 0000315066-25-000987</div><div>Form SCHEDULE 13G</div>
        <div>Filing Date 2025-03-07</div><div>Accepted 2025-03-07 09:59:15</div>
        <div>Mailing Address 245 SUMMER STREET BOSTON MA 02210</div>
        <div>Business Address 245 SUMMER STREET BOSTON MA 02210 6175706339</div>
        <div>FMR LLC (Filed by) CIK: 0000315066 (see all company filings)</div>
        <div>Mailing Address 951 SANDISK DRIVE MILPITAS CA 95035</div>
        <div>Business Address 951 SANDISK DRIVE MILPITAS CA 95035 408-801-1000</div>
        <div>Sandisk Corp (Subject) CIK: 0002023554 (see all company filings)</div>"""
        r = parse_index(page)
        self.assertEqual(r["filed_by_cik"], "0000315066")
        self.assertEqual(r["filed_by_name"], "FMR LLC")
        self.assertEqual(r["subject_cik"], "0002023554")
        self.assertEqual(r["subject_name"], "Sandisk Corp")
        self.assertEqual(r["filing_date"], "2025-03-07")
        self.assertEqual(r["accepted_at"], "2025-03-07 09:59:15")
        self.assertEqual(r["accession"], "0000315066-25-000987")

    def test_master_index_filters_forms_and_preserves_filer(self):
        idx = """Description: SEC master file
CIK|Company Name|Form Type|Date Filed|Filename
--------------------------------------------------------------------------------
315066|FMR LLC|SC 13G|2025-03-07|edgar/data/315066/000031506625000987/0000315066-25-000987.txt
2023554|SANDISK CORP|10-K|2025-03-07|edgar/data/2023554/000202355425000001/0002023554-25-000001.txt
"""
        rows = parse_master_index(idx)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["filer_cik"], "0000315066")
        self.assertEqual(rows[0]["accession"], "0000315066-25-000987")
        self.assertTrue(rows[0]["index_url"].endswith("0000315066-25-000987-index.htm"))

    def test_legacy_parser(self):
        t = """Item 1: Reporting Person - FMR LLC
Item 1: Reporting Person - Abigail P. Johnson
CUSIP #253393102
JOINT FILING AGREEMENT"""
        r = parse_legacy(t)
        self.assertEqual(r["reporting_person_names"], ["FMR LLC", "Abigail P. Johnson"])
        self.assertEqual(r["cusip"], "253393102")
        self.assertTrue(r["joint_filing_agreement"])

if __name__ == "__main__":
    unittest.main()

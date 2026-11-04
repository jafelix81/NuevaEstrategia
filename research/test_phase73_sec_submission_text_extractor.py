import unittest

from research.phase72_13dg_structured_xml_parser import parse_schedule13_xml
from research.phase73_sec_submission_text_extractor import (
    extract_primary_doc_xml,
    normalize_acceptance_datetime,
)


class Phase73SubmissionTextExtractorTests(unittest.TestCase):
    def test_13g_submission_separates_subject_filer_and_xml(self):
        raw = """<SEC-DOCUMENT>0000019617-25-000296.txt : 20250306
<SEC-HEADER>
<ACCEPTANCE-DATETIME>20250306105250
CONFORMED SUBMISSION TYPE: SCHEDULE 13G/A
FILED AS OF DATE: 20250306
SUBJECT COMPANY:
    COMPANY CONFORMED NAME: Revance Therapeutics, Inc.
    CENTRAL INDEX KEY: 0001479290
FILED BY:
    COMPANY CONFORMED NAME: JPMORGAN CHASE & CO.
    CENTRAL INDEX KEY: 0000019617
</SEC-HEADER>
<DOCUMENT>
<TYPE>SCHEDULE 13G/A
<SEQUENCE>1
<FILENAME>primary_doc.xml
<TEXT>
<XML>
<?xml version="1.0" encoding="UTF-8"?>
<edgarSubmission xmlns="http://www.sec.gov/edgar/schedule13g">
  <headerData><submissionType>SCHEDULE 13G/A</submissionType><filerInfo><filer><filerCredentials><cik>0000019617</cik></filerCredentials></filer></filerInfo></headerData>
  <formData><coverPageHeader><issuerInfo><issuerCik>0001479290</issuerCik><issuerName>Revance &amp; Therapeutics</issuerName></issuerInfo></coverPageHeader>
  <coverPageHeaderReportingPersonDetails><reportingPersonName>JPMORGAN CHASE &amp; CO.</reportingPersonName><reportingCikNotPresentInEdgarFlag>Y</reportingCikNotPresentInEdgarFlag><classPercent>0</classPercent></coverPageHeaderReportingPersonDetails>
</formData></edgarSubmission>
</XML>
</TEXT>
</DOCUMENT>
</SEC-DOCUMENT>"""
        extracted = extract_primary_doc_xml(raw)
        parsed = parse_schedule13_xml(extracted["xml_bytes"])
        self.assertEqual(extracted["subject_cik"], "0001479290")
        self.assertEqual(extracted["filer_cik"], "0000019617")
        self.assertEqual(extracted["form"], "SCHEDULE 13G/A")
        self.assertEqual(extracted["filing_date"], "2025-03-06")
        self.assertEqual(extracted["acceptance_datetime"], "20250306105250")
        self.assertEqual(parsed["issuer_cik"], extracted["subject_cik"])
        self.assertEqual(parsed["filer_cik_xml"], extracted["filer_cik"])
        self.assertEqual(parsed["issuer_name"], "Revance & Therapeutics")
        self.assertEqual(extracted["extraction_method"], "complete_submission_txt_primary_doc_xml")

    def test_13d_submission_extracts_primary_xml_not_exhibit_html(self):
        raw = """<SEC-DOCUMENT>0001062993-25-015044.txt : 20250828
<SEC-HEADER>
<ACCEPTANCE-DATETIME>20250828162333
CONFORMED SUBMISSION TYPE: SCHEDULE 13D
FILED AS OF DATE: 20250828
SUBJECT COMPANY:
    COMPANY CONFORMED NAME: Osisko Development Corp.
    CENTRAL INDEX KEY: 0001431852
FILED BY:
    COMPANY CONFORMED NAME: Double Zero Capital, LP
    CENTRAL INDEX KEY: 0002083861
</SEC-HEADER>
<DOCUMENT>
<TYPE>EX-99.1
<FILENAME>exhibit99-1.htm
<TEXT><html><body>Not the primary document</body></html></TEXT>
</DOCUMENT>
<DOCUMENT>
<TYPE>SCHEDULE 13D
<FILENAME>primary_doc.xml
<TEXT>
<XML>
<?xml version="1.0" encoding="UTF-8"?>
<edgarSubmission xmlns="http://www.sec.gov/edgar/schedule13d">
  <headerData><submissionType>SCHEDULE 13D</submissionType><filerInfo><filer><filerCredentials><cik>0002083861</cik></filerCredentials></filer></filerInfo></headerData>
  <formData><coverPageHeader><issuerInfo><issuerCIK>0001431852</issuerCIK><issuerName>Osisko Development Corp.</issuerName></issuerInfo></coverPageHeader>
  <reportingPersons><reportingPersonInfo><reportingPersonCIK>0002083861</reportingPersonCIK><reportingPersonNoCIK>N</reportingPersonNoCIK><reportingPersonName>Double Zero Capital, LP</reportingPersonName><aggregateAmountOwned>47476245</aggregateAmountOwned><percentOfClass>19.9</percentOfClass><typeOfReportingPerson>PN</typeOfReportingPerson></reportingPersonInfo></reportingPersons>
</formData></edgarSubmission>
</XML>
</TEXT>
</DOCUMENT>
</SEC-DOCUMENT>"""
        extracted = extract_primary_doc_xml(raw)
        parsed = parse_schedule13_xml(extracted["xml_bytes"])
        self.assertEqual(extracted["subject_cik"], "0001431852")
        self.assertEqual(extracted["filer_cik"], "0002083861")
        self.assertEqual(parsed["issuer_cik"], "0001431852")
        self.assertEqual(parsed["filer_cik_xml"], "0002083861")
        self.assertEqual(parsed["reporting_person_count"], 1)

    def test_acceptance_datetime_normalizes_header_and_submissions_formats(self):
        self.assertEqual(normalize_acceptance_datetime("20250306105250"), "20250306105250")
        self.assertEqual(normalize_acceptance_datetime("2025-03-06T10:52:50.000Z"), "20250306105250")
        self.assertEqual(normalize_acceptance_datetime(""), "")

    def test_missing_primary_xml_fails_closed(self):
        raw = """<SEC-HEADER>CONFORMED SUBMISSION TYPE: SCHEDULE 13G</SEC-HEADER>
<DOCUMENT><TYPE>EX-99.1</TYPE><FILENAME>exhibit99-1.xml</FILENAME><TEXT><XML><x/></XML></TEXT></DOCUMENT>"""
        with self.assertRaisesRegex(ValueError, "no primary_doc.xml"):
            extract_primary_doc_xml(raw)

    def test_missing_subject_or_filer_identity_is_preserved_not_inferred(self):
        raw = """<SEC-HEADER>CONFORMED SUBMISSION TYPE: SCHEDULE 13G</SEC-HEADER>
<DOCUMENT><TYPE>SCHEDULE 13G</TYPE><FILENAME>primary_doc.xml</FILENAME><TEXT><XML><edgarSubmission xmlns="http://www.sec.gov/edgar/schedule13g"><headerData><submissionType>SCHEDULE 13G</submissionType></headerData><formData><coverPageHeader><issuerInfo><issuerCik>0000001234</issuerCik></issuerInfo></coverPageHeader></formData></edgarSubmission></XML></TEXT></DOCUMENT>"""
        extracted = extract_primary_doc_xml(raw)
        self.assertEqual(extracted["subject_cik"], "")
        self.assertEqual(extracted["filer_cik"], "")
        parsed = parse_schedule13_xml(extracted["xml_bytes"])
        self.assertEqual(parsed["issuer_cik"], "0000001234")
        self.assertEqual(parsed["filer_cik_xml"], "")


if __name__ == "__main__":
    unittest.main()

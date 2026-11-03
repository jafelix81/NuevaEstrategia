import unittest

from phase35_13dg_parser_v3 import parse_xml
from phase35_global_subject_census_pilot_xml import identity_row, primary_xml_urls


class GlobalSubjectCensusXMLPilotTests(unittest.TestCase):
    def setUp(self):
        self.group = {
            "accession": "0000092230-25-000015",
            "form": "SC 13G/A",
            "filing_date": "2025-02-06",
            "master_index_ciks": ["0000092230", "0001849998"],
            "master_index_names": {
                "0000092230": "TRUIST FINANCIAL CORP",
                "0001849998": "Federated Hermes ETF Trust",
            },
            "master_index_row_count": 2,
            "metadata_conflict": False,
            "target_relevant": True,
            "validation_sample": False,
        }

    def test_primary_xml_urls_use_each_archive_cik(self):
        urls = primary_xml_urls(self.group)
        self.assertEqual(urls[0], "https://www.sec.gov/Archives/edgar/data/92230/000009223025000015/primary_doc.xml")
        self.assertEqual(urls[1], "https://www.sec.gov/Archives/edgar/data/1849998/000009223025000015/primary_doc.xml")

    def test_xml_subject_and_submission_filer_are_separate(self):
        xml = """<edgarSubmission xmlns="http://www.sec.gov/edgar/schedule13g">
          <headerData>
            <submissionType>SCHEDULE 13G/A</submissionType>
            <filerInfo><filer><filerCredentials><cik>0000092230</cik></filerCredentials></filer></filerInfo>
            <previousAccessionNumber>0000092230-25-000001</previousAccessionNumber>
          </headerData>
          <formData>
            <coverPageHeader>
              <eventDateRequiresFilingThisStatement>01/31/2025</eventDateRequiresFilingThisStatement>
              <issuerInfo>
                <issuerCik>0001849998</issuerCik>
                <issuerName>Federated Hermes ETF Trust</issuerName>
                <issuerCusip>31423L503</issuerCusip>
              </issuerInfo>
            </coverPageHeader>
            <coverPageHeaderReportingPersonDetails>
              <reportingCik>0000092230</reportingCik>
              <reportingPersonName>TRUIST FINANCIAL CORP</reportingPersonName>
              <memberGroup>b</memberGroup>
              <reportingPersonBeneficiallyOwnedAggregateNumberOfShares>153847</reportingPersonBeneficiallyOwnedAggregateNumberOfShares>
              <classPercent>38.0</classPercent>
              <typeOfReportingPerson>IA</typeOfReportingPerson>
            </coverPageHeaderReportingPersonDetails>
          </formData>
        </edgarSubmission>"""
        parsed = parse_xml(xml)
        row = identity_row(
            self.group, parsed,
            "https://www.sec.gov/Archives/edgar/data/92230/000009223025000015/primary_doc.xml",
            {"0001849998"},
        )
        self.assertEqual(row["subject_issuer_cik"], "0001849998")
        self.assertEqual(row["submission_filer_cik"], "0000092230")
        self.assertNotEqual(row["subject_issuer_cik"], row["submission_filer_cik"])
        self.assertEqual(row["previous_accession"], "0000092230-25-000001")
        self.assertTrue(row["both_subject_and_filer_in_master_pair"])
        self.assertTrue(row["subject_is_target_candidate"])
        self.assertFalse(row["submission_filer_is_target_candidate"])
        self.assertEqual(row["reporting_person_count"], 1)
        self.assertEqual(row["reporting_person_ciks"], "0000092230")

    def test_missing_reporting_person_cik_does_not_invent_group(self):
        xml = """<edgarSubmission xmlns="http://www.sec.gov/edgar/schedule13g">
          <headerData><submissionType>SCHEDULE 13G</submissionType></headerData>
          <formData><coverPageHeader><issuerInfo>
            <issuerCik>0001849998</issuerCik><issuerName>Federated Hermes ETF Trust</issuerName>
          </issuerInfo></coverPageHeader>
          <coverPageHeaderReportingPersonDetails>
            <reportingPersonName>Unknown Filer</reportingPersonName>
          </coverPageHeaderReportingPersonDetails></formData>
        </edgarSubmission>"""
        parsed = parse_xml(xml)
        row = identity_row(self.group, parsed, "https://example.invalid/primary_doc.xml", set())
        self.assertIsNone(row["reporting_person_set_fingerprint"])
        self.assertEqual(row["reporting_person_cik_coverage"], 0.0)


if __name__ == "__main__":
    unittest.main()

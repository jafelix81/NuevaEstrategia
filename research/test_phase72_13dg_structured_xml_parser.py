import unittest

from research.phase72_13dg_structured_xml_parser import parse_schedule13_xml


class Phase72StructuredXmlParserTests(unittest.TestCase):
    def test_13d_amendment_multiple_reporting_persons_and_direct_lineage(self):
        xml = b'''<?xml version="1.0"?>
        <edgarSubmission xmlns="http://www.sec.gov/edgar/schedule13d">
          <headerData>
            <submissionType>SCHEDULE 13D/A</submissionType>
            <previousAccessionNumber>0001683168-24-001211</previousAccessionNumber>
            <filerInfo><filer><filerCredentials><cik>1510865</cik></filerCredentials></filer></filerInfo>
          </headerData>
          <formData>
            <coverPageHeader>
              <amendmentNo>1</amendmentNo><dateOfEvent>12/19/2024</dateOfEvent>
              <issuerInfo><issuerCIK>0001289850</issuerCIK><issuerName>NEUROMETRIX, INC.</issuerName><issuerCUSIP>641255880</issuerCUSIP></issuerInfo>
            </coverPageHeader>
            <reportingPersons>
              <reportingPersonInfo>
                <reportingPersonCIK>0001510865</reportingPersonCIK><reportingPersonNoCIK>N</reportingPersonNoCIK>
                <reportingPersonName>Ephraim Fields</reportingPersonName><memberOfGroup>Y</memberOfGroup>
                <soleVotingPower>74301.00</soleVotingPower><sharedVotingPower>0.00</sharedVotingPower>
                <soleDispositivePower>74301.00</soleDispositivePower><sharedDispositivePower>0.00</sharedDispositivePower>
                <aggregateAmountOwned>74301.00</aggregateAmountOwned><percentOfClass>3.6</percentOfClass>
                <typeOfReportingPerson>IN</typeOfReportingPerson><typeOfReportingPerson>IA</typeOfReportingPerson>
              </reportingPersonInfo>
              <reportingPersonInfo>
                <reportingPersonNoCIK>Y</reportingPersonNoCIK><reportingPersonName>Co-investment LLC</reportingPersonName>
                <memberOfGroup>N</memberOfGroup><aggregateAmountOwned>1000.00</aggregateAmountOwned>
              </reportingPersonInfo>
            </reportingPersons>
            <items1To7><item2><filingPersonName>Ephraim Fields and Co-investment LLC</filingPersonName></item2>
              <item4><transactionPurpose>Investment and governance purposes.</transactionPurpose></item4></items1To7>
          </formData>
        </edgarSubmission>'''
        parsed = parse_schedule13_xml(xml)
        self.assertEqual(parsed["form_family"], "13D")
        self.assertTrue(parsed["is_amendment"])
        self.assertEqual(parsed["previous_accession_number"], "0001683168-24-001211")
        self.assertEqual(parsed["lineage_status"], "direct_predecessor_present")
        self.assertEqual(parsed["issuer_cik"], "0001289850")
        self.assertEqual(parsed["filer_cik_xml"], "0001510865")
        self.assertEqual(parsed["reporting_person_count"], 2)
        self.assertEqual(parsed["reporting_persons"][0]["person_cik"], "0001510865")
        self.assertEqual(parsed["reporting_persons"][0]["type_codes"], ["IN", "IA"])
        self.assertEqual(parsed["reporting_persons"][0]["member_of_group"], "Y")
        self.assertEqual(parsed["reporting_persons"][1]["person_cik_status"], "declared_no_cik")
        self.assertEqual(parsed["purpose_text"], "Investment and governance purposes.")
        self.assertEqual(parsed["knowledge_date"], "")

    def test_13g_amendment_uses_distinct_schema_and_preserves_group_flags(self):
        xml = b'''<?xml version="1.0"?>
        <edgarSubmission xmlns="http://www.sec.gov/edgar/schedule13g">
          <headerData><submissionType>SCHEDULE 13G/A</submissionType>
            <previousAccessionNumber>0001493152-25-012122</previousAccessionNumber>
            <filerInfo><filer><filerCredentials><cik>0002081473</cik></filerCredentials></filer></filerInfo>
          </headerData>
          <formData>
            <coverPageHeader>
              <amendmentNo>1</amendmentNo><eventDateRequiresFilingThisStatement>09/01/2025</eventDateRequiresFilingThisStatement>
              <issuerInfo><issuerCik>0001130166</issuerCik><issuerName>Cyclacel Pharmaceuticals, Inc.</issuerName>
                <issuerCusips><issuerCusipNumber>23254L876</issuerCusipNumber></issuerCusips>
              </issuerInfo>
              <designateRulesPursuantThisScheduleFiled><designateRulePursuantThisScheduleFiled>Rule 13d-1(c)</designateRulePursuantThisScheduleFiled></designateRulesPursuantThisScheduleFiled>
            </coverPageHeader>
            <coverPageHeaderReportingPersonDetails>
              <reportingCik>0002081473</reportingCik><reportingCikNotPresentInEdgarFlag>N</reportingCikNotPresentInEdgarFlag>
              <reportingPersonName>Ong Yee Lung</reportingPersonName><memberGroup>b</memberGroup>
              <citizenshipOrOrganization>MY</citizenshipOrOrganization>
              <reportingPersonBeneficiallyOwnedNumberOfShares><soleVotingPower>218000.00</soleVotingPower>
                <sharedVotingPower>0.00</sharedVotingPower><soleDispositivePower>218000.00</soleDispositivePower>
                <sharedDispositivePower>0.00</sharedDispositivePower></reportingPersonBeneficiallyOwnedNumberOfShares>
              <reportingPersonBeneficiallyOwnedAggregateNumberOfShares>218000.00</reportingPersonBeneficiallyOwnedAggregateNumberOfShares>
              <classPercent>9.8</classPercent><typeOfReportingPerson>IN</typeOfReportingPerson>
            </coverPageHeaderReportingPersonDetails>
            <coverPageHeaderReportingPersonDetails>
              <reportingCikNotPresentInEdgarFlag>Y</reportingCikNotPresentInEdgarFlag>
              <reportingPersonName>Other Person</reportingPersonName><memberGroup>a</memberGroup>
              <classPercent>2.0</classPercent><typeOfReportingPerson>CO</typeOfReportingPerson>
            </coverPageHeaderReportingPersonDetails>
            <items><item2><filingPersonName>Ong Yee Lung</filingPersonName></item2>
              <item8><identificationAndClassificationOfGroupMembers>Group member details.</identificationAndClassificationOfGroupMembers></item8></items>
          </formData>
        </edgarSubmission>'''
        parsed = parse_schedule13_xml(xml)
        self.assertEqual(parsed["form_family"], "13G")
        self.assertEqual(parsed["previous_accession_number"], "0001493152-25-012122")
        self.assertEqual(parsed["issuer_cik"], "0001130166")
        self.assertEqual(parsed["cusips"], ["23254L876"])
        self.assertEqual(parsed["rule_designations"], ["Rule 13d-1(c)"])
        self.assertEqual(parsed["reporting_person_count"], 2)
        self.assertEqual(parsed["reporting_persons"][0]["person_cik"], "0002081473")
        self.assertEqual(parsed["reporting_persons"][0]["member_of_group"], "b")
        self.assertEqual(parsed["reporting_persons"][0]["percent_of_class"], "9.8")
        self.assertEqual(parsed["reporting_persons"][1]["person_cik"], "")
        self.assertEqual(parsed["reporting_persons"][1]["person_cik_status"], "declared_no_cik")
        self.assertEqual(parsed["group_members_narrative"], "Group member details.")

    def test_original_13g_without_predecessor_is_not_misclassified(self):
        xml = b'''<edgarSubmission xmlns="http://www.sec.gov/edgar/schedule13g">
          <headerData><submissionType>SCHEDULE 13G</submissionType></headerData>
          <formData><coverPageHeader><issuerInfo><issuerCik>1130166</issuerCik></issuerInfo></coverPageHeader>
            <coverPageHeaderReportingPersonDetails><reportingPersonName>Investor</reportingPersonName>
              <reportingCikNotPresentInEdgarFlag>Y</reportingCikNotPresentInEdgarFlag></coverPageHeaderReportingPersonDetails>
          </formData></edgarSubmission>'''
        parsed = parse_schedule13_xml(xml)
        self.assertFalse(parsed["is_amendment"])
        self.assertEqual(parsed["lineage_status"], "original_no_predecessor")
        self.assertEqual(parsed["reporting_persons"][0]["person_cik_status"], "declared_no_cik")
        self.assertNotEqual(parsed["reporting_persons"][0]["person_cik"], parsed["filer_cik_xml"])

    def test_amendment_without_previous_accession_is_flagged(self):
        xml = b'''<edgarSubmission xmlns="http://www.sec.gov/edgar/schedule13d">
          <headerData><submissionType>SCHEDULE 13D/A</submissionType></headerData>
          <formData><coverPageHeader><issuerInfo><issuerCIK>0001289850</issuerCIK></issuerInfo></coverPageHeader>
            <reportingPersons><reportingPersonInfo><reportingPersonName>Person</reportingPersonName></reportingPersonInfo></reportingPersons>
          </formData></edgarSubmission>'''
        parsed = parse_schedule13_xml(xml)
        self.assertEqual(parsed["lineage_status"], "amendment_missing_predecessor")

    def test_invalid_xml_fails_closed(self):
        with self.assertRaises(ValueError):
            parse_schedule13_xml(b"<edgarSubmission>")


if __name__ == "__main__":
    unittest.main()

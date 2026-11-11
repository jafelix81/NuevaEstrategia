import unittest
from phase299_form4a_edgar_validation import (
    parse_submission, xml_transaction_rows, norm_date, norm_cik,
    diff_rows, ND_EXACT, ND_COARSE, metadata_check, parse_acceptance,
)

SAMPLE = b"""<SEC-DOCUMENT>0000000001-26-000001.txt : 20261101
<SEC-HEADER>0000000001-26-000001.hdr.sgml : 20261101
<ACCEPTANCE-DATETIME>20261101153000
ACCESSION NUMBER:        0000000001-26-000001
CONFORMED SUBMISSION TYPE:        4/A
FILED AS OF DATE:        20261101
</SEC-HEADER>
<DOCUMENT>
<TYPE>4/A
<TEXT>
<XML>
<?xml version="1.0"?>
<ownershipDocument>
  <documentType>4/A</documentType>
  <periodOfReport>2026-10-30</periodOfReport>
  <dateOfOriginalSubmission>2026-10-30</dateOfOriginalSubmission>
  <issuer><issuerCik>0000000002</issuerCik><issuerTradingSymbol>TEST</issuerTradingSymbol></issuer>
  <reportingOwner><reportingOwnerId><rptOwnerCik>0000000003</rptOwnerCik></reportingOwnerId></reportingOwner>
  <nonDerivativeTable>
    <nonDerivativeTransaction>
      <securityTitle><value>Common Stock</value></securityTitle>
      <transactionDate><value>2026-10-30</value></transactionDate>
      <transactionCoding><transactionFormType>4</transactionFormType><transactionCode>P</transactionCode><equitySwapInvolved>0</equitySwapInvolved></transactionCoding>
      <transactionAmounts>
        <transactionShares><value>100</value></transactionShares>
        <transactionPricePerShare><value>10.00</value></transactionPricePerShare>
        <transactionAcquiredDisposedCode><value>A</value></transactionAcquiredDisposedCode>
      </transactionAmounts>
      <postTransactionAmounts><sharesOwnedFollowingTransaction><value>1100</value></sharesOwnedFollowingTransaction></postTransactionAmounts>
      <ownershipNature><directOrIndirectOwnership><value>D</value></directOrIndirectOwnership></ownershipNature>
    </nonDerivativeTransaction>
  </nonDerivativeTable>
</ownershipDocument>
</XML>
</TEXT>
</DOCUMENT>
</SEC-DOCUMENT>
"""


class Phase299Tests(unittest.TestCase):
    def test_normalizers(self):
        self.assertEqual(norm_date("31-MAR-2012"), "2012-03-31")
        self.assertEqual(norm_cik("123"), "0000000123")

    def test_parse_complete_submission_header_and_xml(self):
        parsed = parse_submission(SAMPLE)
        self.assertTrue(parsed["xml_parse_ok"])
        self.assertEqual(parsed["accession"], "0000000001-26-000001")
        self.assertEqual(parsed["header_form_type"], "4/A")
        self.assertEqual(parsed["xml_document_type"], "4/A")
        self.assertEqual(parsed["xml_issuer_cik"], "0000000002")
        self.assertEqual(parsed["xml_owner_ciks"], ["0000000003"])
        self.assertEqual(parsed["xml_date_of_original_submission"], "2026-10-30")
        self.assertEqual(parsed["acceptance_datetime"], "20261101153000")

    def test_xml_table_mapping(self):
        parsed = parse_submission(SAMPLE)
        from xml.etree import ElementTree as ET
        root = ET.fromstring(SAMPLE.split(b"<XML>", 1)[1].split(b"</XML>", 1)[0])
        rows = xml_transaction_rows(root, "nd")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["TRANS_CODE"], "P")
        self.assertEqual(rows[0]["TRANS_SHARES"], "100")
        self.assertEqual(rows[0]["TRANS_PRICEPERSHARE"], "10.00")
        self.assertEqual(parsed["xml_nd_rows"], rows)

    def test_metadata_check_fails_closed_on_owner_mismatch(self):
        parsed = parse_submission(SAMPLE)
        expected = {
            "accession": "0000000001-26-000001", "document_type": "4/A",
            "filing_date": "2026-11-01", "issuer_cik": "0000000002",
            "owner_ciks": ["0000000004"],
        }
        rows = {
            "all_transaction_rows_exact_match": True,
            "nd_exact_multiset_match": True, "dv_exact_multiset_match": True,
        }
        checks = metadata_check(expected, parsed, rows)
        self.assertFalse(checks["reporting_owner_set_matches"])
        self.assertFalse(checks["all_header_xml_identity_checks"])

    def test_diff_does_not_promote_same_coarse_change_to_new_trade(self):
        parent = [{
            "SECURITY_TITLE": "Common Stock", "TRANS_DATE": "2026-10-30",
            "TRANS_FORM_TYPE": "4", "TRANS_CODE": "P",
            "TRANS_SHARES": "100", "TRANS_PRICEPERSHARE": "10",
        }]
        child = [{
            "SECURITY_TITLE": "Common Stock", "TRANS_DATE": "2026-10-30",
            "TRANS_FORM_TYPE": "4", "TRANS_CODE": "P",
            "TRANS_SHARES": "120", "TRANS_PRICEPERSHARE": "9",
        }]
        result = diff_rows(parent, child, ND_EXACT, ND_COARSE)
        self.assertEqual(result["same_coarse_unmatched"], 1)
        self.assertEqual(result["distinct_coarse_added"], 0)

    def test_acceptance_clock_parser(self):
        self.assertEqual(parse_acceptance("20261101153000").strftime("%Y-%m-%d %H:%M:%S"), "2026-11-01 15:30:00")
        self.assertIsNone(parse_acceptance("bad"))


if __name__ == "__main__":
    unittest.main()

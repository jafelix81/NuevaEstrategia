import unittest
import xml.etree.ElementTree as ET
from research.phase326_form4_collision_security_title_audit import (
    classify_symbol, normalize_accession, normalize_cik, parse_filing_header,
    parse_ownership_xml, value_of, load_plan
)

class Phase326Tests(unittest.TestCase):
    def test_exchange_prefix_is_not_identity(self):
        self.assertEqual(classify_symbol("NYSE: DLR"), "DLR")
    def test_multisymbol_is_not_split(self):
        self.assertIsNone(classify_symbol("DLR, DLR.PRB"))
    def test_placeholder_is_not_candidate(self):
        self.assertIsNone(classify_symbol("N/A"))
    def test_accession_normalization(self):
        self.assertEqual(normalize_accession("000141588923000349"), "0001415889-23-000349")
    def test_cik_normalization(self):
        self.assertEqual(normalize_cik("00001297996"), "1297996")
    def test_header_parser(self):
        raw=b"ACCESSION NUMBER: 0001415889-23-000349\nCONFORMED SUBMISSION TYPE: 4\nCENTRAL INDEX KEY: 0001297996\nFILED AS OF DATE: 20230104\n<ACCEPTANCE-DATETIME>20230104120000"
        h=parse_filing_header(raw)
        self.assertEqual((h["accession"],h["form_type"],h["cik"],h["filed_date"]),("0001415889-23-000349","4","1297996","2023-01-04"))
    def test_xml_parser_extracts_issuer_owner_title_and_code(self):
        raw=b"""<SEC-DOCUMENT><DOCUMENT><TYPE>4</TYPE><FILENAME>doc4.xml</FILENAME><TEXT><XML>
        <ownershipDocument><issuer><issuerCik>0001297996</issuerCik><issuerName>Digital Realty Trust</issuerName><issuerTradingSymbol>DLR</issuerTradingSymbol></issuer>
        <reportingOwner><reportingOwnerId><rptOwnerCik>0001741270</rptOwnerCik></reportingOwnerId></reportingOwner>
        <nonDerivativeTable><nonDerivativeTransaction><securityTitle><value>Common Stock</value></securityTitle><transactionCoding><transactionCode><value>P</value></transactionCode></transactionCoding></nonDerivativeTransaction></nonDerivativeTable>
        </ownershipDocument></XML></TEXT></DOCUMENT></SEC-DOCUMENT>"""
        x=parse_ownership_xml(raw)
        self.assertEqual(x["xml_status"],"PARSED")
        self.assertEqual(x["xml_issuer_cik"],"1297996")
        self.assertEqual(x["xml_issuer_symbol"],"DLR")
        self.assertEqual(x["xml_owner_ciks"],["1741270"])
        self.assertEqual(x["non_derivative_titles"],["Common Stock"])
        self.assertEqual(x["transaction_codes"],["P"])
    def test_xml_missing_is_quarantined(self):
        x=parse_ownership_xml(b"<SEC-DOCUMENT><DOCUMENT><TYPE>4</TYPE><TEXT>not xml</TEXT></DOCUMENT></SEC-DOCUMENT>")
        self.assertNotEqual(x["xml_status"],"PARSED")
        self.assertFalse(x["xml_issuer_cik"])
    def test_plan_reconstructs_exact_collision_population(self):
        import os
        if os.path.exists("/mnt/data/phase321.zip") and os.path.exists("/mnt/data/phase325.zip"):
            p=load_plan(__import__("pathlib").Path("/mnt/data/phase321.zip"),__import__("pathlib").Path("/mnt/data/phase325.zip"))
            self.assertEqual((p["census_rows"],p["pair_count"],p["shared_dates"],len(p["selected"])),(317267,28,42,283))
            self.assertEqual(len({r["issuer_cik"] for r in p["selected"].values()}),56)

if __name__ == "__main__":
    unittest.main()

import unittest
import xml.etree.ElementTree as ET
from research.phase326_form4_collision_security_title_audit import (
    classify_symbol, normalize_accession, normalize_cik, parse_filing_header,
    parse_ownership_xml, value_of, load_plan, submission_urls_for, pair_summary
)

class Phase326Tests(unittest.TestCase):
    def test_submission_urls_cover_flat_and_accession_directory_layouts(self):
        urls = submission_urls_for("0000939057-26-000239", "1041368")
        self.assertEqual(urls[0], (
            "flat",
            "https://www.sec.gov/Archives/edgar/data/1041368/0000939057-26-000239.txt"
        ))
        self.assertEqual(urls[1], (
            "accession_directory",
            "https://www.sec.gov/Archives/edgar/data/1041368/000093905726000239/0000939057-26-000239.txt"
        ))
    def test_accession_prefix_is_a_retrieval_path_not_issuer_identity(self):
        from research.phase326_form4_collision_security_title_audit import path_ciks_for
        self.assertEqual(path_ciks_for("0000939057-26-000239", "1041368", ["1972440"]), ["939057", "1041368", "1972440"])
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


    def test_equal_transaction_titles_do_not_prove_same_security(self):
        pair = {
            "pair_id": "P01_DLR_1297996_1494877",
            "ticker_candidate": "DLR",
            "issuer_cik_a": "1297996",
            "issuer_name_a": "Digital Realty Trust, Inc.",
            "issuer_cik_b": "1494877",
            "issuer_name_b": "Digital Realty Trust, L.P.",
            "shared_filing_dates": ["2023-01-04"],
        }
        filings = [
            {"issuer_cik": "1297996", "pair_memberships": [{"pair_id": pair["pair_id"], "side": "A"}],
             "retrieval_status": "RETRIEVED", "non_derivative_titles": ["Common Stock"], "derivative_titles": []},
            {"issuer_cik": "1494877", "pair_memberships": [{"pair_id": pair["pair_id"], "side": "B"}],
             "retrieval_status": "RETRIEVED", "non_derivative_titles": ["Common Stock"], "derivative_titles": []},
        ]
        result = pair_summary([pair], filings)[0]
        self.assertEqual(result["title_relation"], "OVERLAPPING_LABELS_NOT_SECURITY_IDENTITY")
        self.assertFalse(result["title_is_security_id"])

    def test_different_transaction_titles_do_not_prove_different_share_classes(self):
        pair = {
            "pair_id": "P02_X_100_200", "ticker_candidate": "X",
            "issuer_cik_a": "100", "issuer_name_a": "Issuer A",
            "issuer_cik_b": "200", "issuer_name_b": "Issuer B",
            "shared_filing_dates": ["2023-01-04"],
        }
        filings = [
            {"issuer_cik": "100", "pair_memberships": [{"pair_id": pair["pair_id"], "side": "A"}],
             "retrieval_status": "RETRIEVED", "non_derivative_titles": ["Common Stock"], "derivative_titles": []},
            {"issuer_cik": "200", "pair_memberships": [{"pair_id": pair["pair_id"], "side": "B"}],
             "retrieval_status": "RETRIEVED", "non_derivative_titles": ["Class A Common Stock"], "derivative_titles": []},
        ]
        result = pair_summary([pair], filings)[0]
        self.assertEqual(result["title_relation"], "DISJOINT_LABELS_NOT_SHARE_CLASS_PROOF")
        self.assertFalse(result["title_is_security_id"])

    def test_xml_parser_keeps_underlying_security_title_separate(self):
        raw = b"""<SEC-DOCUMENT><DOCUMENT><TYPE>4</TYPE><TEXT><XML>
        <ownershipDocument>
          <issuer><issuerCik>00001297996</issuerCik><issuerName>Issuer</issuerName><issuerTradingSymbol>DLR</issuerTradingSymbol></issuer>
          <reportingOwner><reportingOwnerId><rptOwnerCik>00001741270</rptOwnerCik></reportingOwnerId></reportingOwner>
          <derivativeTable><derivativeTransaction>
            <securityTitle><value>Employee Stock Option</value></securityTitle>
            <underlyingSecurity><underlyingSecurityTitle><value>Class A Common Stock</value></underlyingSecurityTitle></underlyingSecurity>
            <transactionCoding><transactionCode><value>M</value></transactionCode></transactionCoding>
          </derivativeTransaction></derivativeTable>
        </ownershipDocument></XML></TEXT></DOCUMENT></SEC-DOCUMENT>"""
        result = parse_ownership_xml(raw)
        self.assertEqual(result["derivative_titles"], ["Employee Stock Option"])
        self.assertEqual(result["underlying_titles"], ["Class A Common Stock"])
        self.assertEqual(result["transaction_codes"], ["M"])

if __name__ == "__main__":
    unittest.main()

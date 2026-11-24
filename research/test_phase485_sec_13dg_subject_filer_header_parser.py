import unittest

from research.phase485_sec_13dg_subject_filer_header_parser import parse_subject_filer_identity


SEC_HEADER_FIXTURE = """
<SEC-HEADER>0000895421-24-000178.hdr.sgml : 20240212
<ACCEPTANCE-DATETIME>20240212095001
ACCESSION NUMBER: 0000895421-24-000178
CONFORMED SUBMISSION TYPE: SC 13G

SUBJECT COMPANY:

    COMPANY DATA:
        COMPANY CONFORMED NAME: abrdn Global Infrastructure Income Fund
        CENTRAL INDEX KEY: 0001793855
        ORGANIZATION NAME:
        IRS NUMBER: 000000000

    FILING VALUES:
        FORM TYPE: SC 13G

FILED BY:

    COMPANY DATA:
        COMPANY CONFORMED NAME: MORGAN STANLEY
        CENTRAL INDEX KEY: 0000895421
        STANDARD INDUSTRIAL CLASSIFICATION: SECURITY BROKERS, DEALERS & FLOTATION COMPANIES [6211]

    FILING VALUES:
        FORM TYPE: SC 13G
</SEC-HEADER>
"""


class Sec13DGHeaderIdentityTests(unittest.TestCase):
    def test_subject_and_filer_are_separated(self):
        result = parse_subject_filer_identity(SEC_HEADER_FIXTURE, "0000895421-24-000178")
        self.assertEqual(result["subject_issuer_cik"], "0001793855")
        self.assertEqual(result["subject_issuer_name"], "abrdn Global Infrastructure Income Fund")
        self.assertEqual(result["filing_cik"], "0000895421")
        self.assertEqual(result["filing_entity_name"], "MORGAN STANLEY")
        self.assertTrue(result["subject_issuer_identity_verified"])
        self.assertFalse(result["signal_eligible"])

    def test_accession_filer_mismatch_fails_closed(self):
        result = parse_subject_filer_identity(SEC_HEADER_FIXTURE, "0000000001-24-000178")
        self.assertEqual(result["identity_status"], "ACCESSION_HEADER_FILER_MISMATCH")
        self.assertFalse(result["subject_issuer_identity_verified"])

    def test_missing_subject_block_fails_closed(self):
        text = "<SEC-HEADER>FILED BY:\n CENTRAL INDEX KEY: 0000895421\n</SEC-HEADER>"
        result = parse_subject_filer_identity(text, "0000895421-24-000178")
        self.assertEqual(result["identity_status"], "NO_SUBJECT_COMPANY_BLOCK")
        self.assertIsNone(result["subject_issuer_cik"])

    def test_missing_filed_by_block_fails_closed(self):
        text = "<SEC-HEADER>SUBJECT COMPANY:\n CENTRAL INDEX KEY: 0001793855\n</SEC-HEADER>"
        result = parse_subject_filer_identity(text, "0000895421-24-000178")
        self.assertEqual(result["identity_status"], "NO_FILED_BY_BLOCK")
        self.assertFalse(result["subject_issuer_identity_verified"])

    def test_missing_subject_cik_fails_closed(self):
        text = """<SEC-HEADER>
SUBJECT COMPANY:
 COMPANY CONFORMED NAME: Example Issuer
FILED BY:
 COMPANY CONFORMED NAME: MORGAN STANLEY
 CENTRAL INDEX KEY: 0000895421
</SEC-HEADER>"""
        result = parse_subject_filer_identity(text, "0000895421-24-000178")
        self.assertEqual(result["identity_status"], "MISSING_OR_INVALID_SUBJECT_CIK")
        self.assertIsNone(result["subject_issuer_cik"])

    def test_empty_subject_name_does_not_consume_next_field(self):
        text = SEC_HEADER_FIXTURE.replace(
            "COMPANY CONFORMED NAME: abrdn Global Infrastructure Income Fund",
            "COMPANY CONFORMED NAME:",
        )
        result = parse_subject_filer_identity(text, "0000895421-24-000178")
        self.assertIsNone(result["subject_issuer_name"])
        self.assertEqual(result["subject_issuer_cik"], "0001793855")

    def test_empty_filer_name_does_not_consume_next_field(self):
        text = SEC_HEADER_FIXTURE.replace(
            "COMPANY CONFORMED NAME: MORGAN STANLEY",
            "COMPANY CONFORMED NAME:",
        )
        result = parse_subject_filer_identity(text, "0000895421-24-000178")
        self.assertIsNone(result["filing_entity_name"])
        self.assertEqual(result["filing_cik"], "0000895421")

    def test_empty_subject_cik_does_not_consume_following_metadata(self):
        text = SEC_HEADER_FIXTURE.replace(
            "CENTRAL INDEX KEY: 0001793855",
            "CENTRAL INDEX KEY:",
        )
        result = parse_subject_filer_identity(text, "0000895421-24-000178")
        self.assertIsNone(result["subject_issuer_cik"])
        self.assertEqual(result["identity_status"], "MISSING_OR_INVALID_SUBJECT_CIK")

    def test_invalid_accession_fails_closed(self):
        result = parse_subject_filer_identity(SEC_HEADER_FIXTURE, "000089542124000178")
        self.assertEqual(result["identity_status"], "INVALID_OR_MISSING_ACCESSION")
        self.assertFalse(result["subject_issuer_identity_verified"])

    def test_ticker_is_never_inferred_from_cik(self):
        result = parse_subject_filer_identity(SEC_HEADER_FIXTURE, "0000895421-24-000178")
        self.assertIsNone(result["ticker"])
        self.assertEqual(result["ticker_mapping_status"], "NOT_ATTEMPTED")

    def test_duplicate_subject_block_is_ambiguous(self):
        text = SEC_HEADER_FIXTURE.replace(
            "FILED BY:",
            "SUBJECT COMPANY:\n COMPANY CONFORMED NAME: Duplicate\n CENTRAL INDEX KEY: 0000000002\n\nFILED BY:",
        )
        result = parse_subject_filer_identity(text, "0000895421-24-000178")
        self.assertEqual(result["identity_status"], "MISSING_OR_INVALID_SUBJECT_CIK")


if __name__ == "__main__":
    unittest.main()

import unittest

from research.phase347_13dg_cusip_integrity_audit import (
    audit_rows, cusip_checksum_valid, is_valid_security_cusip,
)

class Phase347CusipTests(unittest.TestCase):
    def base(self, accession, subject="0000000001", cusip="037833100", family="13D", amendment=False):
        return {
            "accession": accession, "family": family,
            "is_amendment": str(amendment).lower(), "subject_cik": subject,
            "cusips": f'["{cusip}"]', "event_mechanism_tags": "[]",
        }

    def test_known_cusip_checksum(self):
        self.assertTrue(cusip_checksum_valid("037833100"))
        self.assertFalse(cusip_checksum_valid("037833101"))

    def test_zero_sentinel_is_not_valid_security(self):
        self.assertTrue(cusip_checksum_valid("000000000"))
        self.assertFalse(is_valid_security_cusip("000000000"))

    def test_invalid_checksum_is_not_valid_security(self):
        self.assertFalse(cusip_checksum_valid("80512Q302"))
        self.assertFalse(is_valid_security_cusip("80512Q302"))

    def test_multiple_cusips_fail_one_per_filing_count(self):
        row = self.base("0000000001-24-000001")
        row["cusips"] = '["037833100", "594918104"]'
        summary, details = audit_rows([row])
        self.assertEqual(summary["exactly_one_cusip_rows"], 0)
        self.assertEqual(details[0]["cusip_count"], 2)

    def test_nonzero_cusip_cross_subject_collision_is_reported(self):
        rows = [
            self.base("0000000001-24-000001", subject="0000000001"),
            self.base("0000000002-24-000001", subject="0000000002"),
        ]
        summary, _ = audit_rows(rows)
        self.assertEqual(summary["nonzero_cusips_with_multiple_subject_ciks"], 1)

    def test_multiple_cusips_for_one_subject_are_not_collapsed(self):
        rows = [
            self.base("0000000001-24-000001", cusip="037833100"),
            self.base("0000000001-24-000002", cusip="594918104", amendment=True),
        ]
        summary, _ = audit_rows(rows)
        self.assertEqual(summary["subject_ciks_with_multiple_nonzero_cusips"], 1)
        self.assertEqual(summary["maximum_nonzero_cusips_for_one_subject_cik"], 2)

    def test_duplicate_accessions_rejected(self):
        row = self.base("0000000001-24-000001")
        with self.assertRaises(ValueError):
            audit_rows([row, dict(row)])

if __name__ == "__main__":
    unittest.main()

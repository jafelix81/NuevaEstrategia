import unittest

from research.phase484_13dg_subject_issuer_identity_audit import (
    accession_filer_cik,
    classify_identity_row,
    normalize_cik,
    summarize_rows,
)


class SubjectIssuerIdentityTests(unittest.TestCase):
    def test_accession_prefix_is_filing_cik(self):
        self.assertEqual(accession_filer_cik("0000895421-24-000178"), "0000895421")

    def test_invalid_accession_fails_closed(self):
        self.assertIsNone(accession_filer_cik("000089542124000178"))

    def test_normalize_cik(self):
        self.assertEqual(normalize_cik("1282850"), "0001282850")
        self.assertIsNone(normalize_cik("MS"))

    def test_filer_subject_collision_is_review_not_verified(self):
        row = {"ticker": "MS", "issuer_cik": "0000895421", "accession": "0000895421-24-000178"}
        result = classify_identity_row(row)
        self.assertEqual(result["identity_status"], "FILER_CIK_COLLISION_REVIEW")
        self.assertFalse(result["subject_issuer_identity_verified"])
        self.assertFalse(result["signal_eligible"])

    def test_nonmatching_cik_is_still_unverified(self):
        row = {"ticker": "OXY", "issuer_cik": "0000797468", "accession": "0000928464-20-000057"}
        result = classify_identity_row(row)
        self.assertEqual(result["identity_status"], "SUBJECT_IDENTITY_UNVERIFIED")
        self.assertFalse(result["subject_issuer_identity_verified"])

    def test_missing_stored_cik_is_not_promoted(self):
        row = {"ticker": "MS", "issuer_cik": "", "accession": "0000895421-24-000178"}
        result = classify_identity_row(row)
        self.assertEqual(result["identity_status"], "MISSING_STORED_CIK")

    def test_summary_counts_collisions_and_keeps_duplicate_accessions(self):
        rows = [
            {"ticker": "MS", "issuer_cik": "0000895421", "accession": "0000895421-24-000178", "reporting_person": "", "reporting_person_type": "HC"},
            {"ticker": "OXY", "issuer_cik": "0000797468", "accession": "0000928464-20-000057", "reporting_person": "Example", "reporting_person_type": "PN"},
            {"ticker": "MS", "issuer_cik": "0000895421", "accession": "0000895421-24-000178", "reporting_person": "", "reporting_person_type": "HC"},
        ]
        result = summarize_rows(rows)
        self.assertEqual(result["rows"], 3)
        self.assertEqual(result["unique_accessions"], 2)
        self.assertEqual(result["duplicate_accession_rows"], 1)
        self.assertEqual(result["filer_cik_equals_stored_issuer_cik_rows"], 2)
        self.assertEqual(result["subject_issuer_identity_verified_rows"], 0)
        self.assertFalse(result["signal_eligible"])

    def test_institutional_review_cohort_is_not_automatically_valid(self):
        rows = [
            {"ticker": "BLK", "issuer_cik": "0002012383", "accession": "0002012383-24-000091", "reporting_person": "", "reporting_person_type": "HC"}
        ]
        result = summarize_rows(rows)
        self.assertEqual(result["review_ticker_cohort_rows"], 1)
        self.assertEqual(result["review_ticker_cohort_filer_cik_collisions"], 1)
        self.assertEqual(result["subject_issuer_identity_verified_rows"], 0)

    def test_empty_input_is_rejected_by_summary(self):
        result = summarize_rows([])
        self.assertEqual(result["rows"], 0)
        self.assertFalse(result["signal_eligible"])


if __name__ == "__main__":
    unittest.main()

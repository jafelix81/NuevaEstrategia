import unittest
from research.phase327_form4_single_accession_recovery import (
    FAILED_ACCESSION, padded_submission_urls_for
)

class Phase327RecoveryTests(unittest.TestCase):
    def test_known_quarantine_accession_is_fixed(self):
        self.assertEqual(FAILED_ACCESSION, "0000939057-26-000239")

    def test_zero_padded_cik_flat_and_directory_urls(self):
        urls = padded_submission_urls_for(FAILED_ACCESSION, "1972440")
        self.assertEqual(urls, [
            ("flat_zero_padded",
             "https://www.sec.gov/Archives/edgar/data/0001972440/0000939057-26-000239.txt"),
            ("accession_directory_zero_padded",
             "https://www.sec.gov/Archives/edgar/data/0001972440/000093905726000239/0000939057-26-000239.txt"),
        ])

    def test_zero_padded_cik_variants_are_not_repeated_for_ten_digit_cik(self):
        self.assertEqual(padded_submission_urls_for(FAILED_ACCESSION, "1234567890"), [])

    def test_invalid_accession_is_rejected(self):
        with self.assertRaises(ValueError):
            padded_submission_urls_for("bad-accession", "1972440")

if __name__ == "__main__":
    unittest.main()

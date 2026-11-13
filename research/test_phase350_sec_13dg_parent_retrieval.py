import unittest
from datetime import datetime
from research.phase350_sec_13dg_parent_retrieval import (
    build_archive_url, family_from_form, normalize_accession, parse_acceptance_utc,
    parse_sec_header, validate_parent_metadata,
)

class Phase350ParentRetrievalTests(unittest.TestCase):
    def header(self, acceptance="20230102150000", form="SC 13D/A", subject="0000000001", accession="0000000002-23-000001"):
        return f"""<SEC-HEADER>
ACCESSION NUMBER: {accession}
CONFORMED SUBMISSION TYPE: {form}
FILED AS OF DATE: 20230102
<ACCEPTANCE-DATETIME>{acceptance}
SUBJECT COMPANY:
  COMPANY DATA:
    CENTRAL INDEX KEY: {subject}
FILED BY:
  COMPANY DATA:
    CENTRAL INDEX KEY: 0000000003
</SEC-HEADER>"""

    def expected(self):
        return {
            "explicit_parent_accession": "0000000002-23-000001",
            "subject_issuer_cik": "0000000001",
            "form_family": "13D",
            "child_acceptance_utc": "2024-01-02T15:00:00+00:00",
        }

    def test_accession_normalization(self):
        self.assertEqual(normalize_accession("0000000002-23-000001"), "0000000002-23-000001")
        self.assertEqual(normalize_accession("bad"), "")

    def test_archive_url_uses_accession_prefix_only_as_path_cik(self):
        url = build_archive_url("0001011438-23-000658", "0001011438")
        self.assertEqual(
            url,
            "https://www.sec.gov/Archives/edgar/data/1011438/000101143823000658/0001011438-23-000658.txt",
        )

    def test_form_family(self):
        self.assertEqual(family_from_form("SC 13D/A"), "13D")
        self.assertEqual(family_from_form("SC 13G"), "13G")
        self.assertEqual(family_from_form("10-K"), "")

    def test_acceptance_is_converted_from_eastern_to_utc(self):
        parsed = parse_acceptance_utc("<ACCEPTANCE-DATETIME>20230102150000")
        self.assertEqual(parsed, "2023-01-02T20:00:00+00:00")

    def test_subject_cik_is_read_from_subject_block_not_filed_by(self):
        parsed = parse_sec_header(self.header())
        self.assertEqual(parsed["parent_subject_cik"], "0000000001")
        self.assertNotEqual(parsed["parent_subject_cik"], "0000000003")
        self.assertEqual(parsed["parent_form_family"], "13D")

    def test_exact_parent_metadata_passes(self):
        parsed = parse_sec_header(self.header())
        self.assertEqual(validate_parent_metadata(parsed, self.expected()), [])

    def test_subject_mismatch_is_quarantined(self):
        parsed = parse_sec_header(self.header(subject="0000000009"))
        self.assertIn("parent_subject_cik_mismatch", validate_parent_metadata(parsed, self.expected()))

    def test_family_mismatch_is_quarantined(self):
        parsed = parse_sec_header(self.header(form="SC 13G/A"))
        self.assertIn("parent_form_family_mismatch", validate_parent_metadata(parsed, self.expected()))

    def test_parent_not_strictly_earlier_is_quarantined(self):
        parsed = parse_sec_header(self.header(acceptance="20240102100000"))
        self.assertIn("parent_acceptance_not_strictly_earlier", validate_parent_metadata(parsed, self.expected()))

    def test_missing_acceptance_is_quarantined(self):
        parsed = parse_sec_header(self.header(acceptance=""))
        self.assertIn("parent_acceptance_missing", validate_parent_metadata(parsed, self.expected()))

if __name__ == "__main__":
    unittest.main()

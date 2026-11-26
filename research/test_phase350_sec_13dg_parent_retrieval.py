import os
import unittest
from unittest.mock import patch
from datetime import datetime
from research.sec_user_agent import resolve_sec_user_agent
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

    def test_archive_url_uses_subject_path_when_accession_prefix_differs(self):
        url = build_archive_url("0001567619-19-013029", "0000883265")
        self.assertEqual(
            url,
            "https://www.sec.gov/Archives/edgar/data/883265/000156761919013029/0001567619-19-013029.txt",
        )

    def test_missing_archive_path_candidate_is_rejected(self):
        with self.assertRaises(ValueError):
            build_archive_url("0001567619-19-013029", "")

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


class Phase350SecUserAgentTests(unittest.TestCase):
    def test_missing_secret_uses_established_project_contact(self):
        with patch.dict(os.environ, {}, clear=True):
            value, source = resolve_sec_user_agent()
        self.assertIn("@", value)
        self.assertEqual(source, "shared_project_contact_fallback")

    def test_valid_secret_overrides_fallback(self):
        secret = "NuevaEstrategia quantitative research test@research.test"
        with patch.dict(os.environ, {"SEC_USER_AGENT": secret}, clear=True):
            value, source = resolve_sec_user_agent()
        self.assertEqual(value, secret)
        self.assertEqual(source, "repository_secret")

    def test_placeholder_secret_uses_fallback(self):
        with patch.dict(os.environ, {
            "SEC_USER_AGENT": "NuevaEstrategia contact your-email@example.com"
        }, clear=True):
            value, source = resolve_sec_user_agent()
        self.assertIn("@", value)
        self.assertEqual(source, "shared_project_contact_fallback")

    def test_invalid_fallback_fails_closed(self):
        with (
            patch.dict(os.environ, {}, clear=True),
            patch("research.sec_user_agent.SEC_USER_AGENT_FALLBACK", "placeholder"),
        ):
            with self.assertRaisesRegex(RuntimeError, "no_valid_sec_user_agent"):
                resolve_sec_user_agent()


if __name__ == "__main__":
    unittest.main()

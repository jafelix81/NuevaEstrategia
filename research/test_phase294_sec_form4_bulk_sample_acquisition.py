import io
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from research.phase294_sec_form4_bulk_sample_acquisition import (
    SAMPLE_ARCHIVES,
    inspect_archive,
    run_audit,
    _fetch,
    RetrievalError,
    normalize_filing_date,
)

ACCESSION = "0001234567-26-000001"


def build_zip(*, duplicate_transaction=False, orphan_footnote=False, omit_footnotes=False,
              duplicate_signature=False, signature_date_collision=False):
    tables = {
        "SUBMISSION": (
            ["ACCESSION_NUMBER", "DOCUMENT_TYPE", "FILING_DATE", "ISSUERCIK",
             "ISSUERTRADINGSYMBOL", "AFF10B5ONE"],
            [[ACCESSION, "4", "2026-01-15", "1234567", "TEST", "0"]],
        ),
        "REPORTINGOWNER": (
            ["ACCESSION_NUMBER", "RPTOWNERCIK"],
            [[ACCESSION, "7654321"]],
        ),
        "NONDERIV_TRANS": (
            ["ACCESSION_NUMBER", "NONDERIV_TRANS_SK", "TRANS_DATE",
             "TRANS_CODE", "TRANS_SHARES"],
            [[ACCESSION, "1", "2026-01-14", "P", "100"]],
        ),
        "NONDERIV_HOLDING": (
            ["ACCESSION_NUMBER", "NONDERIV_HOLDING_SK"],
            [[ACCESSION, "1"]],
        ),
        "DERIV_TRANS": (
            ["ACCESSION_NUMBER", "DERIV_TRANS_SK"],
            [[ACCESSION, "1"]],
        ),
        "DERIV_HOLDING": (
            ["ACCESSION_NUMBER", "DERIV_HOLDING_SK"],
            [[ACCESSION, "1"]],
        ),
        "FOOTNOTES": (
            ["ACCESSION_NUMBER", "FOOTNOTE_ID", "FOOTNOTE_TXT"],
            [[("0000000001-26-000001" if orphan_footnote else ACCESSION), "1", "Open market purchase"]],
        ),
        "OWNER_SIGNATURE": (
            ["ACCESSION_NUMBER", "OWNERSIGNATURENAME"],
            [[ACCESSION, "Example Owner"]],
        ),
    }
    if duplicate_transaction:
        tables["NONDERIV_TRANS"][1].append(tables["NONDERIV_TRANS"][1][0][:])
    if duplicate_signature:
        tables["OWNER_SIGNATURE"][1].append(tables["OWNER_SIGNATURE"][1][0][:])
    if signature_date_collision:
        tables["OWNER_SIGNATURE"][1].append([ACCESSION, "Example Owner", "2026-01-16"])
    if omit_footnotes:
        tables.pop("FOOTNOTES")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name, (header, rows) in tables.items():
            lines = ["\t".join(header)] + ["\t".join(row) for row in rows]
            zf.writestr(f"{name}.tsv", "\n".join(lines) + "\n")
    return buf.getvalue()


class Phase294Tests(unittest.TestCase):
    def test_sec_bulk_date_formats_normalize_without_locale_guessing(self):
        self.assertEqual(normalize_filing_date("31-MAR-2006"), "2006-03-31")
        self.assertEqual(normalize_filing_date("2026-01-15"), "2026-01-15")
        self.assertIsNone(normalize_filing_date("31-XYZ-2006"))
        self.assertIsNone(normalize_filing_date("2026-02-30"))

    def test_six_stratified_archives_are_configured(self):
        self.assertEqual(list(SAMPLE_ARCHIVES), [
            "2006Q1", "2012Q1", "2023Q1", "2023Q2", "2025Q3", "2026Q3"
        ])
        self.assertTrue(all(url.startswith("https://www.sec.gov/") for url in SAMPLE_ARCHIVES.values()))

    def test_archive_schema_and_form4_sample(self):
        result = inspect_archive(build_zip(), "2026Q1")
        self.assertTrue(result["schema_gate_pass"])
        self.assertEqual(result["form4_and_4a_rows"], 1)
        self.assertEqual(result["form4_accession_sample"][0]["accession"], ACCESSION)
        self.assertTrue(result["submission_aff10b5one_present"])
        self.assertEqual(result["orphan_accession_rows"], 0)
        self.assertEqual(len(result["tables_present"]), 8)

    def test_duplicate_primary_key_fails_schema_gate(self):
        result = inspect_archive(build_zip(duplicate_transaction=True), "2026Q1")
        self.assertFalse(result["schema_gate_pass"])
        self.assertEqual(
            result["table_summaries"]["NONDERIV_TRANS"]["duplicate_primary_keys"], 1
        )

    def test_owner_signature_exact_duplicate_is_reported_but_not_a_core_schema_failure(self):
        result = inspect_archive(build_zip(duplicate_signature=True), "2026Q1")
        diagnostic = result["owner_signature_key_diagnostics"]
        self.assertEqual(diagnostic["duplicate_key_rows"], 1)
        self.assertEqual(diagnostic["exact_duplicate_rows"], 1)
        self.assertEqual(diagnostic["same_key_different_row_rows"], 0)
        self.assertFalse(diagnostic["unique_key"])
        self.assertTrue(result["schema_gate_pass"])

    def test_owner_signature_same_name_different_date_is_not_unique(self):
        result = inspect_archive(build_zip(signature_date_collision=True), "2026Q1")
        diagnostic = result["owner_signature_key_diagnostics"]
        self.assertEqual(diagnostic["same_key_different_row_rows"], 1)
        self.assertFalse(diagnostic["unique_key"])

    def test_orphan_accession_fails_schema_gate(self):
        result = inspect_archive(build_zip(orphan_footnote=True), "2026Q1")
        self.assertFalse(result["schema_gate_pass"])
        self.assertEqual(result["orphan_accession_rows"], 1)

    def test_missing_required_table_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "missing_required_tables"):
            inspect_archive(build_zip(omit_footnotes=True), "2026Q1")

    def test_corrupt_zip_is_rejected(self):
        with self.assertRaises(zipfile.BadZipFile):
            inspect_archive(b"not a zip", "2026Q1")

    def test_missing_contact_blocks_without_network(self):
        with tempfile.TemporaryDirectory() as temp:
            with patch(
                "research.phase294_sec_form4_bulk_sample_acquisition._fetch",
                side_effect=AssertionError("network must not be called"),
            ):
                result = run_audit("", Path(temp))
        self.assertEqual(result["status"], "BLOCKED_MISSING_SEC_CONTACT_EMAIL")
        self.assertFalse(result["email_secret_present"])
        self.assertEqual(result["raw_sec_requests"], 0)
        self.assertFalse(result["alpha_test_authorized"])
        self.assertTrue(result["f80_frozen"])

    def test_invalid_non_sec_url_is_rejected(self):
        with self.assertRaisesRegex(RetrievalError, "non_sec_https_url_rejected"):
            _fetch("https://example.com/file.zip", "test (contact: test@example.com)")


if __name__ == "__main__":
    unittest.main()

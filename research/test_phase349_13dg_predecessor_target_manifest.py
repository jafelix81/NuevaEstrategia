import json
import tempfile
import unittest
from pathlib import Path
from research.phase349_13dg_predecessor_target_manifest import (
    build_manifest, child_cusip_status, cusip_checksum_valid, normalize_accession, write_json,
)

class Phase349ManifestTests(unittest.TestCase):
    def fixture(self, cusips='["037833100"]'):
        child = "0000000001-24-000001"
        parent = "0000000002-23-000001"
        lineage = [{
            "accession": child, "xml_previous_accession": parent,
            "lineage_status": "explicit_predecessor_outside_600_header_sample",
            "subject_cik": "0000000001", "filer_cik": "0000000003",
            "family": "13D", "filing_date": "2024-01-02",
            "acceptance_utc": "2024-01-02T15:00:00+00:00",
        }]
        events = [{
            "accession": child, "xml_previous_accession": parent,
            "subject_cik": "0000000001", "family": "13D",
            "cusips": cusips, "explicit_person_ciks": '["0000000004"]',
            "person_names": '["Jane Doe"]', "reporting_person_count": "1",
            "event_mechanism_tags": '["activist_or_control_action"]',
            "matched_event_phrases": '["board representation"]',
        }]
        phase84 = []
        summary = {
            "filings_reparsed": 1,
            "raw_sha256_and_xml_identity_errors": [],
            "amendment_lineage_status_counts": {
                "explicit_predecessor_outside_600_header_sample": 1
            },
        }
        return lineage, events, phase84, summary

    def test_accession_normalization(self):
        self.assertEqual(normalize_accession("000000000124000001"), "0000000001-24-000001")
        self.assertEqual(normalize_accession("0000000001-24-000001"), "0000000001-24-000001")
        self.assertEqual(normalize_accession("bad"), "")

    def test_known_cusip_checksum(self):
        self.assertTrue(cusip_checksum_valid("037833100"))
        self.assertFalse(cusip_checksum_valid("037833101"))

    def test_zero_sentinel_is_not_a_security(self):
        self.assertEqual(child_cusip_status(["000000000"]), ("000000000", "ZERO_SENTINEL"))

    def test_multi_cusip_is_quarantined(self):
        self.assertEqual(child_cusip_status(["037833100", "594918104"]), ("", "MISSING_OR_MULTIPLE"))

    def test_archive_path_cik_is_not_subject_or_filer_identity(self):
        args = self.fixture()
        summary, rows = build_manifest(*args, expected_target_count=1)
        row = rows[0]
        self.assertEqual(row["subject_issuer_cik"], "0000000001")
        self.assertEqual(row["child_filer_cik"], "0000000003")
        self.assertEqual(row["parent_archive_path_cik"], "0000000002")
        self.assertEqual(row["parent_path_cik_role"], "ARCHIVE_PATH_ONLY_NOT_ISSUER_IDENTITY")
        self.assertFalse(summary["strict_pit_admitted"])

    def test_summary_json_is_parseable_after_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "summary.json"
            write_json(path, {"phase": 349, "ok": True})
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), {"phase": 349, "ok": True})

    def test_parent_already_in_phase84_sample_is_rejected(self):
        lineage, events, _, summary = self.fixture()
        phase84 = [{"accession": "0000000002-23-000001"}]
        with self.assertRaises(ValueError):
            build_manifest(lineage, events, phase84, summary, expected_target_count=1)

    def test_child_subject_mismatch_is_rejected(self):
        args = self.fixture()
        args[1][0]["subject_cik"] = "0000000009"
        with self.assertRaises(ValueError):
            build_manifest(*args, expected_target_count=1)

    def test_duplicate_parent_reference_is_rejected(self):
        args = self.fixture()
        args[0].append(dict(args[0][0], accession="0000000005-24-000001"))
        args[1].append(dict(args[1][0], accession="0000000005-24-000001"))
        args[3]["filings_reparsed"] = 2
        args[3]["amendment_lineage_status_counts"]["explicit_predecessor_outside_600_header_sample"] = 2
        with self.assertRaises(ValueError):
            build_manifest(*args, expected_target_count=2)

if __name__ == "__main__":
    unittest.main()

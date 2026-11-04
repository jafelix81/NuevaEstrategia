import csv
import hashlib
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from research.phase74_13dg_global_subject_audit import run_index_audit


SAMPLE_INDEX = (
    "Description: Master Index of EDGAR Dissemination Feed\n"
    "CIK|Company Name|Form Type|Date Filed|Filename\n"
    "0001849998|FEDERATED HERMES ETF TRUST|SC 13G/A|2025-02-06|edgar/data/1849998/000009223025000015/0000092230-25-000015.txt\n"
    "0000092230|TRUIST FINANCIAL CORP|SC 13G/A|2025-02-06|edgar/data/92230/000009223025000015/0000092230-25-000015.txt\n"
).encode("latin-1")



SAMPLE_SUBMISSION = b"""<SEC-DOCUMENT>0000092230-25-000015.txt : 20250206
<SEC-HEADER>
<ACCEPTANCE-DATETIME>20250206105250
CONFORMED SUBMISSION TYPE: SCHEDULE 13G/A
FILED AS OF DATE: 20250206
SUBJECT COMPANY:
    COMPANY CONFORMED NAME: Federated Hermes ETF Trust
    CENTRAL INDEX KEY: 0001849998
FILED BY:
    COMPANY CONFORMED NAME: Truist Financial Corp.
    CENTRAL INDEX KEY: 0000092230
</SEC-HEADER>
<DOCUMENT>
<TYPE>SCHEDULE 13G/A
<SEQUENCE>1
<FILENAME>primary_doc.xml
<TEXT>
<XML>
<?xml version="1.0" encoding="UTF-8"?>
<edgarSubmission xmlns="http://www.sec.gov/edgar/schedule13g">
  <headerData><submissionType>SCHEDULE 13G/A</submissionType><filerInfo><filer><filerCredentials><cik>0000092230</cik></filerCredentials></filer></filerInfo></headerData>
  <formData><coverPageHeader><issuerInfo><issuerCik>0001849998</issuerCik><issuerName>Federated Hermes ETF Trust</issuerName></issuerInfo></coverPageHeader><coverPageHeaderReportingPersonDetails><reportingPersonName>Truist Financial Corp.</reportingPersonName><reportingCik>0000092230</reportingCik></coverPageHeaderReportingPersonDetails></formData>
</edgarSubmission>
</XML>
</TEXT>
</DOCUMENT>
</SEC-DOCUMENT>"""

class Phase82IndexSnapshotTests(unittest.TestCase):
    def test_index_only_audit_preserves_raw_index_and_retrieval_metadata(self):
        fake_response = SimpleNamespace(
            content=SAMPLE_INDEX,
            status_code=200,
            headers={"Content-Type": "text/plain; charset=ISO-8859-1"},
        )
        with tempfile.TemporaryDirectory() as tmp:
            with patch(
                "research.phase74_13dg_global_subject_audit.SecClient.get_response",
                return_value=fake_response,
            ):
                summary = run_index_audit(
                    ["2025Q1"],
                    {"0001849998"},
                    Path(tmp),
                    mode="index-only",
                    sample_limit=5,
                    sleep_seconds=0,
                )

            self.assertEqual(summary["status"], "COMPLETE")
            self.assertEqual(summary["data_gate"], "PASS")
            self.assertEqual(summary["global_13dg_accessions"], 1)
            self.assertEqual(summary["index_metadata_conflicts_quarantined"], 0)
            self.assertEqual(summary["multi_cik_accessions"], 1)
            self.assertEqual(summary["index_pair_type_counts"]["multi_cik_multiple_archive_paths"], 1)
            raw_path = Path(tmp) / "raw_master_indexes" / "master_2025Q1.idx"
            self.assertTrue(raw_path.exists())
            self.assertEqual(raw_path.read_bytes(), SAMPLE_INDEX)

            with (Path(tmp) / "quarterly_counts.csv").open(encoding="utf-8") as handle:
                row = next(csv.DictReader(handle))
            self.assertEqual(row["http_status"], "200")
            self.assertIn("text/plain", row["content_type"])
            self.assertEqual(int(row["content_length"]), len(SAMPLE_INDEX))
            self.assertTrue(row["retrieved_at_utc"])
            self.assertEqual(row["sha256"], hashlib.sha256(SAMPLE_INDEX).hexdigest())
            self.assertEqual(row["raw_file"], "raw_master_indexes/master_2025Q1.idx")


    def test_pilot_saves_raw_submission_hash_and_utc_retrieval_time(self):
        fake_index_response = SimpleNamespace(
            content=SAMPLE_INDEX,
            status_code=200,
            headers={"Content-Type": "text/plain; charset=ISO-8859-1"},
        )
        fake_submission_response = SimpleNamespace(
            content=SAMPLE_SUBMISSION,
            status_code=200,
            headers={"Content-Type": "text/plain; charset=US-ASCII"},
        )
        with tempfile.TemporaryDirectory() as tmp:
            with patch(
                "research.phase74_13dg_global_subject_audit.SecClient.get_response",
                side_effect=[fake_index_response, fake_submission_response],
            ):
                summary = run_index_audit(
                    ["2025Q1"],
                    {"0001849998"},
                    Path(tmp),
                    mode="pilot",
                    sample_limit=1,
                    sleep_seconds=0,
                )

            self.assertEqual(summary["data_gate"], "PASS")
            self.assertEqual(summary["pilot_summary"]["data_gate"], "PASS")
            self.assertEqual(summary["pilot_summary"]["raw_submission_files_saved"], 1)
            with (Path(tmp) / "pilot_header_validation.csv").open(encoding="utf-8") as handle:
                row = next(csv.DictReader(handle))
            raw_path = Path(tmp) / row["raw_file"]
            self.assertTrue(raw_path.exists())
            self.assertEqual(raw_path.read_bytes(), SAMPLE_SUBMISSION)
            self.assertEqual(row["source_sha256"], hashlib.sha256(SAMPLE_SUBMISSION).hexdigest())
            self.assertEqual(row["source_http_status"], "200")
            self.assertTrue(row["retrieved_at_utc"])
            self.assertEqual(row["candidate_role"], "subject")
            self.assertEqual(row["xml_subject_matches_header"], "True")
            self.assertEqual(row["xml_filer_matches_header"], "True")


if __name__ == "__main__":
    unittest.main()

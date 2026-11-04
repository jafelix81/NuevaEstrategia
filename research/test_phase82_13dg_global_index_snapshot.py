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


if __name__ == "__main__":
    unittest.main()

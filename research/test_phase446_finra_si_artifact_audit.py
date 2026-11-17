import csv
import tempfile
import unittest
import zipfile
from pathlib import Path

from phase446_finra_si_artifact_audit import audit_artifact


class Phase446AuditTests(unittest.TestCase):
    def make_zip(self, audit_rows, feature_rows):
        tmp = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
        tmp.close()
        path = Path(tmp.name)
        with zipfile.ZipFile(path, "w") as zf:
            for name, rows in (
                ("si_download_audit.csv", audit_rows),
                ("short_interest_features.csv", feature_rows),
            ):
                if rows:
                    import io
                    buf = io.StringIO()
                    writer = csv.DictWriter(buf, fieldnames=list(rows[0]))
                    writer.writeheader()
                    writer.writerows(rows)
                    zf.writestr(name, buf.getvalue())
                else:
                    zf.writestr(name, "")
        return path

    def test_sync_cap_hit_blocks_zero_inference(self):
        path = self.make_zip(
            [{"settlementDate": "2026-01-15", "rows": "5000", "universeRows": "2", "status": "ok", "error": ""}],
            [{"Ticker": "AAPL", "settlementDate": "2026-01-15", "currentShortPositionQuantity": "100"}],
        )
        try:
            result = audit_artifact(path)
            self.assertTrue(result["all_successful_requests_hit_sync_cap"])
            self.assertFalse(result["complete_snapshot_proven"])
            self.assertFalse(result["zero_inference_allowed"])
        finally:
            path.unlink()

    def test_failed_settlement_blocks_zero_inference(self):
        path = self.make_zip(
            [{"settlementDate": "2026-01-15", "rows": "0", "universeRows": "0", "status": "error", "error": "timeout"}],
            [],
        )
        try:
            result = audit_artifact(path)
            self.assertEqual(result["failed_settlement_requests"], 1)
            self.assertFalse(result["zero_inference_allowed"])
        finally:
            path.unlink()

    def test_alphabetical_prefix_is_reported(self):
        path = self.make_zip(
            [{"settlementDate": "2026-01-15", "rows": "5000", "universeRows": "2", "status": "ok", "error": ""}],
            [
                {"Ticker": "AAPL", "settlementDate": "2026-01-15", "currentShortPositionQuantity": "100"},
                {"Ticker": "DOW", "settlementDate": "2026-01-15", "currentShortPositionQuantity": "200"},
            ],
        )
        try:
            result = audit_artifact(path)
            self.assertTrue(result["alphabetical_prefix_through_D_likely"])
            self.assertEqual(result["observed_unique_tickers"], 2)
        finally:
            path.unlink()

    def test_complete_snapshot_requires_total_and_pagination_evidence(self):
        path = self.make_zip(
            [{
                "settlementDate": "2026-01-15",
                "rows": "2",
                "status": "ok",
                "recordTotal": "2",
                "recordOffset": "0",
                "paginationComplete": "true",
            }],
            [{"Ticker": "AAPL", "settlementDate": "2026-01-15", "currentShortPositionQuantity": "100"}],
        )
        try:
            result = audit_artifact(path)
            self.assertTrue(result["complete_snapshot_proven"])
        finally:
            path.unlink()

    def test_missing_metadata_is_not_completeness(self):
        path = self.make_zip(
            [{"settlementDate": "2026-01-15", "rows": "3", "status": "ok"}],
            [],
        )
        try:
            result = audit_artifact(path)
            self.assertFalse(result["complete_snapshot_proven"])
            self.assertEqual(result["classification"], "INCOMPLETE_OR_UNVERIFIED")
        finally:
            path.unlink()


if __name__ == "__main__":
    unittest.main()

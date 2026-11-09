import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from research.phase234_cftc_bpr_capture import (
    build_capture_metadata, capture_latest, extract_report_date,
    select_latest_futures_url,
)

INDEX_FIXTURE = """
<html><body><table>
<tr><td>November</td><td><a href="/MarketReports/BankParticipation/deanov26f">Futures</a></td>
<td><a href="/MarketReports/BankParticipation/deanov26o">Options</a></td></tr>
<tr><td>October</td><td><a href="/MarketReports/BankParticipation/deaoct26f">Futures</a></td></tr>
</table></body></html>
"""
REPORT_FIXTURE = """
<html><body><h1>November Bank Participation Report Futures IN CONTRACT</h1>
<div>REPORT DATE: 11/3/2026</div><table><tr><td>CME E-MINI S&amp;P 500</td></tr></table>
</body></html>
"""

class Phase234CaptureTests(unittest.TestCase):
    def test_latest_futures_link_selected_not_options(self):
        self.assertEqual(
            select_latest_futures_url(INDEX_FIXTURE),
            "https://www.cftc.gov/MarketReports/BankParticipation/deanov26f",
        )

    def test_missing_futures_link_fails_closed(self):
        with self.assertRaises(ValueError):
            select_latest_futures_url("<a href='/x'>Options</a>")

    def test_report_date_extracted(self):
        self.assertEqual(extract_report_date(REPORT_FIXTURE), "2026-11-03")

    def test_missing_report_date_fails_closed(self):
        with self.assertRaises(ValueError):
            extract_report_date("<html><body>no date</body></html>")

    def test_scheduled_friday_after_1530_et_is_pipeline_pit_candidate(self):
        receipt = datetime(2026, 11, 6, 20, 35, tzinfo=timezone.utc)
        m = build_capture_metadata(
            report_date="2026-11-03", report_url="https://x", report_sha256="abc",
            receipt_time=receipt, event_name="schedule"
        )
        self.assertTrue(m["pit_eligible_from_pipeline_receipt"])

    def test_delayed_weekday_publication_is_captured_after_release_time(self):
        receipt = datetime(2026, 11, 9, 20, 35, tzinfo=timezone.utc)  # Monday 15:35 EST
        m = build_capture_metadata(
            report_date="2026-11-03", report_url="https://x", report_sha256="abc",
            receipt_time=receipt, event_name="schedule"
        )
        self.assertTrue(m["pit_eligible_from_pipeline_receipt"])

    def test_manual_dispatch_never_pit(self):
        receipt = datetime(2026, 11, 6, 20, 35, tzinfo=timezone.utc)
        m = build_capture_metadata(
            report_date="2026-11-03", report_url="https://x", report_sha256="abc",
            receipt_time=receipt, event_name="workflow_dispatch"
        )
        self.assertFalse(m["pit_eligible_from_pipeline_receipt"])

    def test_before_release_time_not_pit(self):
        receipt = datetime(2026, 11, 6, 20, 20, tzinfo=timezone.utc)
        m = build_capture_metadata(
            report_date="2026-11-03", report_url="https://x", report_sha256="abc",
            receipt_time=receipt, event_name="schedule"
        )
        self.assertFalse(m["pit_eligible_from_pipeline_receipt"])

    def test_capture_appends_raw_and_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            calls = []
            def fetcher(url):
                calls.append(url)
                if url.endswith("index.htm"):
                    return INDEX_FIXTURE.encode(), {}
                return REPORT_FIXTURE.encode(), {"Date": "Fri, 06 Nov 2026 20:35:00 GMT"}
            now = datetime(2026, 11, 6, 20, 35, tzinfo=timezone.utc)
            result = capture_latest(root=root, event_name="schedule", now=now, fetcher=fetcher, env={})
            self.assertTrue(result["new_snapshot"])
            self.assertFalse(result["pit_eligible_from_pipeline_receipt"])
            self.assertTrue(result["prospective_state_usable_after_receipt"])
            self.assertTrue((root / result["raw_snapshot_path"]).exists())
            self.assertTrue((root / result["metadata_path"]).exists())
            self.assertEqual(len(calls), 2)

    def test_same_scheduled_hash_is_not_duplicated(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            def fetcher(url):
                if url.endswith("index.htm"):
                    return INDEX_FIXTURE.encode(), {}
                return REPORT_FIXTURE.encode(), {}
            now = datetime(2026, 11, 6, 20, 35, tzinfo=timezone.utc)
            first = capture_latest(root=root, event_name="schedule", now=now, fetcher=fetcher, env={})
            second = capture_latest(root=root, event_name="schedule", now=now, fetcher=fetcher, env={})
            self.assertTrue(first["new_snapshot"])
            self.assertEqual(second["status"], "UNCHANGED_ALREADY_CAPTURED")
            self.assertFalse(second["new_snapshot"])

    def test_manual_backfill_then_scheduled_receipt_is_baseline_state_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            def fetcher(url):
                if url.endswith("index.htm"):
                    return INDEX_FIXTURE.encode(), {}
                return REPORT_FIXTURE.encode(), {}
            now = datetime(2026, 11, 6, 20, 35, tzinfo=timezone.utc)
            manual = capture_latest(root=root, event_name="workflow_dispatch", now=now, fetcher=fetcher, env={})
            scheduled = capture_latest(root=root, event_name="schedule", now=now, fetcher=fetcher, env={})
            self.assertFalse(manual["pit_eligible_from_pipeline_receipt"])
            self.assertFalse(scheduled["pit_eligible_from_pipeline_receipt"])
            self.assertTrue(scheduled["prospective_state_usable_after_receipt"])
            self.assertTrue(scheduled["initial_baseline"])
            self.assertTrue(scheduled["new_snapshot"])
            metadata_files = list((root/"data/cftc_bpr/metadata").glob("*.json"))
            self.assertEqual(len(metadata_files), 2)
            stored = [json.loads(p.read_text()) for p in metadata_files]
            self.assertEqual(sum(bool(x["pit_eligible_from_pipeline_receipt"]) for x in stored), 0)
            self.assertEqual(scheduled["status"], "INITIAL_BASELINE_CAPTURED_STATE_ONLY")
            self.assertIn("INITIAL_BASELINE_STATE_ONLY", {x["receipt_kind"] for x in stored})

    def test_repeated_manual_backfill_is_not_duplicated(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            def fetcher(url):
                if url.endswith("index.htm"):
                    return INDEX_FIXTURE.encode(), {}
                return REPORT_FIXTURE.encode(), {}
            now = datetime(2026, 11, 6, 20, 35, tzinfo=timezone.utc)
            first = capture_latest(root=root, event_name="workflow_dispatch", now=now, fetcher=fetcher, env={})
            second = capture_latest(root=root, event_name="workflow_dispatch", now=now, fetcher=fetcher, env={})
            self.assertTrue(first["new_snapshot"])
            self.assertEqual(second["status"], "UNCHANGED_NON_PIT_VERSION")
            self.assertEqual(len(list((root/"data/cftc_bpr/metadata").glob("*.json"))), 1)

    def test_revision_is_append_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            versions = [REPORT_FIXTURE.encode(), REPORT_FIXTURE.replace("11/3/2026","11/3/2026 ").encode()]
            i = {"n":0}
            def fetcher(url):
                if url.endswith("index.htm"):
                    return INDEX_FIXTURE.encode(), {}
                b = versions[min(i["n"],1)]
                i["n"] += 1
                return b, {}
            now = datetime(2026, 11, 6, 20, 35, tzinfo=timezone.utc)
            first = capture_latest(root=root, event_name="schedule", now=now, fetcher=fetcher, env={})
            second = capture_latest(root=root, event_name="schedule", now=now, fetcher=fetcher, env={})
            self.assertTrue(first["new_snapshot"])
            self.assertEqual(second["status"], "NEW_REVISION")
            self.assertTrue(second["pit_eligible_from_pipeline_receipt"])
            raw_files = list((root/"data/cftc_bpr/raw").glob("*.html"))
            self.assertEqual(len(raw_files), 2)

if __name__ == "__main__":
    unittest.main()

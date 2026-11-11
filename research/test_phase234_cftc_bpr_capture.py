import hashlib
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from research.phase234_cftc_bpr_capture import (
    build_capture_metadata, capture_latest, extract_report_date,
    select_latest_futures_url,
)

OCT_URL = "https://www.cftc.gov/MarketReports/BankParticipation/deaoct26f"
NOV_URL = "https://www.cftc.gov/MarketReports/BankParticipation/deanov26f"
DEC_URL = "https://www.cftc.gov/MarketReports/BankParticipation/deadec26f"

INDEX_FIXTURE = """
<html><body><table>
<tr><td>November</td><td><a href="/MarketReports/BankParticipation/deanov26f">Futures</a></td>
<td><a href="/MarketReports/BankParticipation/deanov26o">Options</a></td></tr>
<tr><td>October</td><td><a href="/MarketReports/BankParticipation/deaoct26f">Futures</a></td></tr>
</table></body></html>
"""
INDEX_WITH_DECEMBER = """
<html><body><table>
<tr><td>December</td><td><a href="/MarketReports/BankParticipation/deadec26f">Futures</a></td></tr>
<tr><td>November</td><td><a href="/MarketReports/BankParticipation/deanov26f">Futures</a></td>
<td><a href="/MarketReports/BankParticipation/deanov26o">Options</a></td></tr>
<tr><td>October</td><td><a href="/MarketReports/BankParticipation/deaoct26f">Futures</a></td></tr>
</table></body></html>
"""
OCT_REPORT_FIXTURE = """
<html><body><h1>October Bank Participation Report Futures IN CONTRACT</h1>
<div>REPORT DATE: 10/6/2026</div><table><tr><td>CME E-MINI S&amp;P 500</td></tr></table>
</body></html>
"""
REPORT_FIXTURE = """
<html><body><h1>November Bank Participation Report Futures IN CONTRACT</h1>
<div>REPORT DATE: 11/3/2026</div><table><tr><td>CME E-MINI S&amp;P 500</td></tr></table>
</body></html>
"""
DEC_REPORT_FIXTURE = """
<html><body><h1>December Bank Participation Report Futures IN CONTRACT</h1>
<div>REPORT DATE: 12/1/2026</div><table><tr><td>CME E-MINI S&amp;P 500</td></tr></table>
</body></html>
"""


def report_for_url(url):
    if url == OCT_URL:
        return OCT_REPORT_FIXTURE.encode()
    if url == NOV_URL:
        return REPORT_FIXTURE.encode()
    if url == DEC_URL:
        return DEC_REPORT_FIXTURE.encode()
    raise AssertionError("unexpected BPR report URL: " + url)


class Phase234CaptureTests(unittest.TestCase):
    def test_latest_futures_link_selected_not_options(self):
        self.assertEqual(select_latest_futures_url(INDEX_FIXTURE), NOV_URL)

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
        m = build_capture_metadata(report_date="2026-11-03", report_url="https://x",
            report_sha256="abc", receipt_time=receipt, event_name="schedule")
        self.assertTrue(m["pit_eligible_from_pipeline_receipt"])

    def test_delayed_weekday_publication_is_captured_after_release_time(self):
        receipt = datetime(2026, 11, 9, 20, 35, tzinfo=timezone.utc)
        m = build_capture_metadata(report_date="2026-11-03", report_url="https://x",
            report_sha256="abc", receipt_time=receipt, event_name="schedule")
        self.assertTrue(m["pit_eligible_from_pipeline_receipt"])

    def test_manual_dispatch_never_pit(self):
        receipt = datetime(2026, 11, 6, 20, 35, tzinfo=timezone.utc)
        m = build_capture_metadata(report_date="2026-11-03", report_url="https://x",
            report_sha256="abc", receipt_time=receipt, event_name="workflow_dispatch")
        self.assertFalse(m["pit_eligible_from_pipeline_receipt"])

    def test_previously_observed_version_is_state_only(self):
        receipt = datetime(2026, 11, 6, 20, 35, tzinfo=timezone.utc)
        m = build_capture_metadata(report_date="2026-11-03", report_url="https://x",
            report_sha256="abc", receipt_time=receipt, event_name="schedule",
            previously_observed=True)
        self.assertFalse(m["pit_eligible_from_pipeline_receipt"])
        self.assertTrue(m["prospective_state_usable_after_receipt"])
        self.assertEqual(m["event_type"], "PREVIOUSLY_OBSERVED_VERSION_STATE_ONLY")

    def test_before_release_time_not_pit(self):
        receipt = datetime(2026, 11, 6, 20, 20, tzinfo=timezone.utc)
        m = build_capture_metadata(report_date="2026-11-03", report_url="https://x",
            report_sha256="abc", receipt_time=receipt, event_name="schedule")
        self.assertFalse(m["pit_eligible_from_pipeline_receipt"])

    def test_first_scheduled_capture_bootstraps_all_retained_reports_state_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            calls = []
            def fetcher(url):
                calls.append(url)
                if url.endswith("index.htm"):
                    return INDEX_FIXTURE.encode(), {}
                return report_for_url(url), {"Date": "Fri, 06 Nov 2026 20:35:00 GMT"}
            now = datetime(2026, 11, 6, 20, 35, tzinfo=timezone.utc)
            result = capture_latest(root=root, event_name="schedule", now=now, fetcher=fetcher, env={})
            self.assertEqual(result["status"], "INITIAL_BASELINE_CAPTURED_STATE_ONLY")
            self.assertEqual(len(result["captures"]), 2)
            self.assertEqual(len(calls), 3)
            self.assertFalse(result["pit_eligible_from_pipeline_receipt"])
            for capture in result["captures"]:
                self.assertFalse(capture["pit_eligible_from_pipeline_receipt"])
                self.assertTrue(capture["prospective_state_usable_after_receipt"])
                self.assertTrue((root / capture["raw_snapshot_path"]).exists())
                self.assertTrue((root / capture["metadata_path"]).exists())
            metadata = [json.loads(p.read_text()) for p in (root / "data/cftc_bpr/metadata").glob("*.json")]
            self.assertEqual(len(metadata), 2)
            self.assertTrue(all(x["initial_baseline"] for x in metadata))

    def test_same_scheduled_hash_is_not_duplicated(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            def fetcher(url):
                if url.endswith("index.htm"):
                    return INDEX_FIXTURE.encode(), {}
                return report_for_url(url), {}
            now = datetime(2026, 11, 6, 20, 35, tzinfo=timezone.utc)
            first = capture_latest(root=root, event_name="schedule", now=now, fetcher=fetcher, env={})
            second = capture_latest(root=root, event_name="schedule", now=now, fetcher=fetcher, env={})
            self.assertEqual(len(first["captures"]), 2)
            self.assertEqual(second["status"], "UNCHANGED_ALREADY_CAPTURED")
            self.assertFalse(second["new_snapshot"])

    def test_manual_backfill_then_scheduled_baseline_is_state_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            def fetcher(url):
                if url.endswith("index.htm"):
                    return INDEX_FIXTURE.encode(), {}
                return report_for_url(url), {}
            now = datetime(2026, 11, 6, 20, 35, tzinfo=timezone.utc)
            manual = capture_latest(root=root, event_name="workflow_dispatch", now=now, fetcher=fetcher, env={})
            scheduled = capture_latest(root=root, event_name="schedule", now=now, fetcher=fetcher, env={})
            self.assertFalse(manual["pit_eligible_from_pipeline_receipt"])
            self.assertFalse(scheduled["pit_eligible_from_pipeline_receipt"])
            self.assertTrue(scheduled["prospective_state_usable_after_receipt"])
            self.assertTrue(scheduled["initial_baseline"])
            self.assertTrue(scheduled["new_snapshot"])
            metadata_files = list((root/"data/cftc_bpr/metadata").glob("*.json"))
            self.assertEqual(len(metadata_files), 3)
            stored = [json.loads(p.read_text()) for p in metadata_files]
            self.assertEqual(sum(bool(x["pit_eligible_from_pipeline_receipt"]) for x in stored), 0)
            self.assertEqual(scheduled["status"], "INITIAL_BASELINE_CAPTURED_STATE_ONLY")

    def test_repeated_manual_backfill_is_not_duplicated(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            def fetcher(url):
                if url.endswith("index.htm"):
                    return INDEX_FIXTURE.encode(), {}
                return report_for_url(url), {}
            now = datetime(2026, 11, 6, 20, 35, tzinfo=timezone.utc)
            first = capture_latest(root=root, event_name="workflow_dispatch", now=now, fetcher=fetcher, env={})
            second = capture_latest(root=root, event_name="workflow_dispatch", now=now, fetcher=fetcher, env={})
            self.assertTrue(first["new_snapshot"])
            self.assertEqual(second["status"], "UNCHANGED_NON_PIT_VERSION")
            self.assertEqual(len(list((root/"data/cftc_bpr/metadata").glob("*.json"))), 1)

    def test_nonlatest_report_revision_is_polled_and_state_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            oct_versions = [OCT_REPORT_FIXTURE.encode(),
                OCT_REPORT_FIXTURE.replace("</body>", "<!-- revised --> </body>").encode()]
            calls = {OCT_URL: 0, NOV_URL: 0}
            def fetcher(url):
                if url.endswith("index.htm"):
                    return INDEX_FIXTURE.encode(), {}
                if url == OCT_URL:
                    version = oct_versions[min(calls[OCT_URL], 1)]
                    calls[OCT_URL] += 1
                    return version, {}
                if url == NOV_URL:
                    calls[NOV_URL] += 1
                    return REPORT_FIXTURE.encode(), {}
                raise AssertionError(url)
            now = datetime(2026, 11, 6, 20, 35, tzinfo=timezone.utc)
            first = capture_latest(root=root, event_name="schedule", now=now, fetcher=fetcher, env={})
            second = capture_latest(root=root, event_name="schedule", now=now, fetcher=fetcher, env={})
            self.assertEqual(first["status"], "INITIAL_BASELINE_CAPTURED_STATE_ONLY")
            revision = next(x for x in second["captures"] if x["report_date"] == "2026-10-06")
            self.assertEqual(revision["status"], "NEW_REVISION_STATE_ONLY")
            self.assertFalse(revision["pit_eligible_from_pipeline_receipt"])
            self.assertTrue(revision["prospective_state_usable_after_receipt"])
            stored = [json.loads(p.read_text()) for p in (root / "data/cftc_bpr/metadata").glob("*.json")]
            revision_record = next(x for x in stored if x.get("receipt_kind") == "NEW_REVISION_STATE_ONLY")
            self.assertEqual(revision_record["event_type"], "NEW_REVISION_STATE_ONLY")
            self.assertFalse(revision_record["event_signal_eligible"])
            self.assertEqual(len(list((root / "data/cftc_bpr/raw").glob("*.html"))), 3)

    def test_newly_indexed_report_is_event_eligible_from_scheduled_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            def fetcher(index):
                def inner(url):
                    if url.endswith("index.htm"):
                        return index.encode(), {}
                    return report_for_url(url), {}
                return inner
            first_time = datetime(2026, 11, 6, 20, 35, tzinfo=timezone.utc)
            capture_latest(root=root, event_name="schedule", now=first_time,
                fetcher=fetcher(INDEX_FIXTURE), env={})
            second_time = datetime(2026, 12, 4, 20, 35, tzinfo=timezone.utc)
            result = capture_latest(root=root, event_name="schedule", now=second_time,
                fetcher=fetcher(INDEX_WITH_DECEMBER), env={})
            dec = next(x for x in result["captures"] if x.get("report_date") == "2026-12-01")
            self.assertEqual(dec["status"], "NEW_REPORT_FIRST_SCHEDULED_OBSERVATION")
            self.assertTrue(dec["pit_eligible_from_pipeline_receipt"])

    def test_manual_observation_after_baseline_is_not_promoted_to_new_event(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            def fetcher(index):
                def inner(url):
                    if url.endswith("index.htm"):
                        return index.encode(), {}
                    return report_for_url(url), {}
                return inner
            baseline_time = datetime(2026, 11, 6, 20, 35, tzinfo=timezone.utc)
            capture_latest(root=root, event_name="schedule", now=baseline_time,
                fetcher=fetcher(INDEX_FIXTURE), env={})
            manual_time = datetime(2026, 12, 4, 20, 35, tzinfo=timezone.utc)
            manual = capture_latest(root=root, event_name="workflow_dispatch", now=manual_time,
                fetcher=fetcher(INDEX_WITH_DECEMBER), env={})
            self.assertFalse(manual["pit_eligible_from_pipeline_receipt"])
            scheduled = capture_latest(root=root, event_name="schedule", now=manual_time,
                fetcher=fetcher(INDEX_WITH_DECEMBER), env={})
            dec = next(x for x in scheduled["captures"] if x.get("report_date") == "2026-12-01")
            self.assertEqual(dec["status"], "PREVIOUSLY_OBSERVED_VERSION_FIRST_SCHEDULED_RECEIPT_STATE_ONLY")
            self.assertFalse(dec["pit_eligible_from_pipeline_receipt"])
            self.assertTrue(dec["prospective_state_usable_after_receipt"])



    def test_orphan_raw_snapshot_is_state_only_not_promoted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            def fetcher(index):
                def inner(url):
                    if url.endswith("index.htm"):
                        return index.encode(), {}
                    return report_for_url(url), {}
                return inner
            baseline = datetime(2026, 11, 6, 20, 35, tzinfo=timezone.utc)
            capture_latest(root=root, event_name="schedule", now=baseline,
                fetcher=fetcher(INDEX_FIXTURE), env={})

            orphan_bytes = report_for_url(DEC_URL)
            orphan_hash = hashlib.sha256(orphan_bytes).hexdigest()
            raw_path = root / "data/cftc_bpr/raw" / f"2026-12-01__{orphan_hash[:12]}.html"
            raw_path.parent.mkdir(parents=True, exist_ok=True)
            raw_path.write_bytes(orphan_bytes)  # Simulate a committed raw file after metadata-write failure.

            scheduled = capture_latest(root=root, event_name="schedule", now=baseline,
                fetcher=fetcher(INDEX_WITH_DECEMBER), env={})
            dec = next(x for x in scheduled["captures"] if x.get("report_date") == "2026-12-01")
            self.assertFalse(dec["pit_eligible_from_pipeline_receipt"])
            self.assertTrue(dec["prospective_state_usable_after_receipt"])
            self.assertTrue(dec["raw_snapshot_preexisting_without_metadata"])
            self.assertEqual(
                dec["status"],
                "PREVIOUSLY_OBSERVED_VERSION_FIRST_SCHEDULED_RECEIPT_STATE_ONLY",
            )
            meta_path = root / dec["metadata_path"]
            metadata = json.loads(meta_path.read_text())
            self.assertTrue(metadata["raw_snapshot_preexisting_without_metadata"])
            self.assertFalse(metadata["event_signal_eligible"])

    def test_corrupt_orphan_raw_snapshot_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            def fetcher(index):
                def inner(url):
                    if url.endswith("index.htm"):
                        return index.encode(), {}
                    return report_for_url(url), {}
                return inner
            baseline = datetime(2026, 11, 6, 20, 35, tzinfo=timezone.utc)
            capture_latest(root=root, event_name="schedule", now=baseline,
                fetcher=fetcher(INDEX_FIXTURE), env={})
            expected = report_for_url(DEC_URL)
            digest = hashlib.sha256(expected).hexdigest()
            raw_path = root / "data/cftc_bpr/raw" / f"2026-12-01__{digest[:12]}.html"
            raw_path.parent.mkdir(parents=True, exist_ok=True)
            raw_path.write_bytes(b"corrupt bytes")
            with self.assertRaisesRegex(ValueError, "raw snapshot hash mismatch"):
                capture_latest(root=root, event_name="schedule", now=baseline,
                    fetcher=fetcher(INDEX_WITH_DECEMBER), env={})

    def test_missing_raw_snapshot_is_repaired_from_existing_receipt_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            def fetcher(url):
                if url.endswith("index.htm"):
                    return INDEX_FIXTURE.encode(), {}
                return report_for_url(url), {}
            now = datetime(2026, 11, 6, 20, 35, tzinfo=timezone.utc)
            first = capture_latest(root=root, event_name="schedule", now=now, fetcher=fetcher, env={})
            nov = next(x for x in first["captures"] if x.get("report_date") == "2026-11-03")
            raw_path = root / nov["raw_snapshot_path"]
            raw_path.unlink()
            second = capture_latest(root=root, event_name="schedule", now=now, fetcher=fetcher, env={})
            self.assertFalse(second["new_snapshot"])
            self.assertTrue(raw_path.exists())
            self.assertEqual(hashlib.sha256(raw_path.read_bytes()).hexdigest(), nov["report_sha256"])

if __name__ == "__main__":
    unittest.main()

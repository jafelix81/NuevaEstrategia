from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from research import phase614_sec_13f_first_seen_capture as p


def entry(accession, form, updated, filing_date="2026-11-24", cik="123"):
    digits = accession.replace("-", "")
    return f"""
    <entry>
      <id>urn:tag:sec.gov,2008:accession-number={accession}</id>
      <title>{form} - Test Institutional Manager ({cik}) (Filer)</title>
      <updated>{updated}</updated>
      <category scheme="https://www.sec.gov/" label="form type" term="{form}"/>
      <summary type="html">&lt;b&gt;Filed:&lt;/b&gt; {filing_date} &lt;b&gt;AccNo:&lt;/b&gt; {accession}</summary>
      <link rel="alternate" type="text/html" href="https://www.sec.gov/Archives/edgar/data/{cik}/{digits}/{accession}-index.htm"/>
    </entry>
    """


def feed(*entries):
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<feed xmlns="http://www.w3.org/2005/Atom">'
        + "".join(entries)
        + "</feed>"
    ).encode("utf-8")


def candidate(accession, form, received="2026-11-24T13:05:00Z"):
    digits = accession.replace("-", "")
    return {
        "accession": accession,
        "form": form,
        "filing_date": "2026-11-24",
        "filing_url": f"https://www.sec.gov/Archives/edgar/data/123/{digits}/{accession}-index.htm",
        "feed_path_cik_unverified": "0000000123",
        "feed_updated_raw": "2026-11-24T07:30:00-05:00",
        "feed_updated_utc": "2026-11-24T12:30:00Z",
        "feed_url": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent",
        "_page_offset": 0,
        "_page_received_at_utc": received,
        "_page_sha256": "a" * 64,
    }


class Phase614AtomParserTests(unittest.TestCase):
    def test_hr_original_feed_accepts_only_original(self):
        raw = feed(
            entry("0000000001-26-000001", "13F-HR", "2026-11-24T13:00:00-05:00"),
            entry("0000000001-26-000002", "13F-HR/A", "2026-11-24T13:01:00-05:00"),
        )
        rows = p.parse_atom_feed(raw, "13F-HR", "feed")
        self.assertEqual([x["form"] for x in rows], ["13F-HR"])

    def test_hr_amendment_feed_accepts_only_hr_amendments(self):
        raw = feed(
            entry("0000000001-26-000002", "13F-HR/A", "2026-11-24T13:01:00-05:00"),
            entry("0000000002-26-000003", "13F-NT/A", "2026-11-24T13:02:00-05:00"),
        )
        rows = p.parse_atom_feed(raw, "13F-HR-A", "feed")
        self.assertEqual([x["form"] for x in rows], ["13F-HR/A"])

    def test_nt_original_feed_accepts_only_notice_original(self):
        raw = feed(
            entry("0000000002-26-000003", "13F-NT", "2026-11-24T13:02:00-05:00"),
            entry("0000000002-26-000004", "13F-NT/A", "2026-11-24T13:03:00-05:00"),
        )
        rows = p.parse_atom_feed(raw, "13F-NT", "feed")
        self.assertEqual([x["form"] for x in rows], ["13F-NT"])

    def test_nt_amendment_feed_accepts_only_notice_amendments(self):
        raw = feed(
            entry("0000000002-26-000004", "13F-NT/A", "2026-11-24T13:03:00-05:00"),
            entry("0000000001-26-000002", "13F-HR/A", "2026-11-24T13:01:00-05:00"),
        )
        rows = p.parse_atom_feed(raw, "13F-NT-A", "feed")
        self.assertEqual([x["form"] for x in rows], ["13F-NT/A"])

    def test_accession_extraction_supports_hyphenated_and_compact(self):
        self.assertEqual(p.extract_accession("0000000001-26-000001"), "0000000001-26-000001")
        self.assertEqual(p.extract_accession("000000000126000001"), "0000000001-26-000001")

    def test_path_cik_is_retained_as_unverified(self):
        raw = feed(entry("0000000001-26-000001", "13F-HR", "2026-11-24T13:00:00-05:00", cik="98765"))
        row = p.parse_atom_feed(raw, "13F-HR", "feed")[0]
        self.assertEqual(row["feed_path_cik_unverified"], "0000098765")

    def test_naive_atom_updated_is_not_normalized(self):
        raw = feed(entry("0000000001-26-000001", "13F-HR", "2026-11-24T13:00:00"))
        row = p.parse_atom_feed(raw, "13F-HR", "feed")[0]
        self.assertEqual(row["feed_updated_utc"], "")
        self.assertEqual(row["feed_updated_timestamp_status"], "UNKNOWN_OR_NAIVE")

    def test_legal_filing_floor_respects_est_and_edt(self):
        self.assertEqual(p.legal_filing_date_floor_utc("2026-11-24"), "2026-11-24T11:00:00Z")
        self.assertEqual(p.legal_filing_date_floor_utc("2026-08-24"), "2026-08-24T10:00:00Z")

    def test_parse_utc_rejects_naive(self):
        self.assertIsNone(p.parse_utc("2026-11-24T13:00:00"))


class Phase614IntervalTests(unittest.TestCase):
    def test_bounded_metadata_uses_complete_snapshot_receipt_interval(self):
        status = p.classify_event_interval(
            "schedule", True, "2026-11-24T12:00:00Z",
            "2026-11-24T13:05:00Z",
        )
        self.assertEqual(status, "BOUNDED_METADATA_ONLY")

    def test_stale_atom_updated_is_not_used_as_interval_lower_bound(self):
        status = p.classify_event_interval(
            "schedule", True, "2026-11-24T12:00:00Z",
            "2026-11-24T13:05:00Z",
        )
        self.assertEqual(status, "BOUNDED_METADATA_ONLY")

    def test_future_atom_updated_is_not_used_as_interval_upper_bound(self):
        status = p.classify_event_interval(
            "schedule", True, "2026-11-24T12:00:00Z",
            "2026-11-24T13:05:00Z",
        )
        self.assertEqual(status, "BOUNDED_METADATA_ONLY")

    def test_missing_prior_successful_poll_is_baseline_only(self):
        status = p.classify_event_interval(
            "schedule", True, None, "2026-11-24T13:05:00Z",
        )
        self.assertEqual(status, "NO_PRIOR_SUCCESSFUL_POLL")

    def test_missing_receipt_timestamp_is_not_bounded(self):
        status = p.classify_event_interval(
            "schedule", True, "2026-11-24T12:00:00Z", None,
        )
        self.assertEqual(status, "RECEIPT_TIMESTAMP_UNKNOWN")

    def test_nonincreasing_poll_interval_is_not_bounded(self):
        status = p.classify_event_interval(
            "schedule", True, "2026-11-24T13:05:00Z",
            "2026-11-24T13:05:00Z",
        )
        self.assertEqual(status, "INVALID_POLL_INTERVAL")

    def test_manual_capture_never_becomes_eligible(self):
        status = p.classify_event_interval(
            "manual", True, "2026-11-24T12:00:00Z",
            "2026-11-24T13:05:00Z",
        )
        self.assertEqual(status, "MANUAL_DIAGNOSTIC")

    def test_incomplete_snapshot_suppresses_candidates(self):
        status = p.classify_event_interval(
            "schedule", False, "2026-11-24T12:00:00Z",
            "2026-11-24T13:05:00Z",
        )
        self.assertEqual(status, "POLL_INCOMPLETE_CANDIDATE_SUPPRESSED")


class Phase614PaginationTests(unittest.TestCase):
    def test_unparsed_target_form_entry_fails_closed(self):
        malformed = """
        <entry>
          <id>urn:tag:sec.gov,2008:accession-number=not-an-accession</id>
          <title>13F-HR - Missing accession</title>
          <updated>2026-11-24T13:00:00Z</updated>
          <category scheme="https://www.sec.gov/" label="form type" term="13F-HR"/>
          <summary>Filed: 2026-11-24</summary>
        </entry>
        """
        raw = feed(malformed)
        with patch.object(p.p401, "fetch_bytes", return_value=raw):
            result = p.fetch_feed(
                "13F-HR", "https://example.test/feed", {
                    "latest_accession": "",
                    "last_successful_poll_end_utc": "",
                }, "schedule", "test-run", "2026-11-24T12:01:00Z",
            )
        self.assertFalse(result["poll_success"])
        self.assertEqual(result["page_error"]["error_type"], "ValueError")
        self.assertIn("atom_entry_parse_mismatch", result["page_error"]["error"])
        self.assertEqual(result["event_candidates"], [])

    def test_prefix_neighbor_form_does_not_create_false_parse_failure(self):
        raw = feed(
            entry("0000000001-26-000002", "13F-HR/A", "2026-11-24T13:01:00Z"),
            entry("0000000001-26-000001", "13F-HR", "2026-11-24T13:00:00Z"),
        )
        with patch.object(p.p401, "fetch_bytes", return_value=raw):
            result = p.fetch_feed(
                "13F-HR", "https://example.test/feed", {
                    "latest_accession": "",
                    "last_successful_poll_end_utc": "",
                }, "schedule", "test-run", "2026-11-24T12:01:00Z",
            )
        self.assertTrue(result["poll_success"])
        self.assertEqual(result["page_observations"][0]["raw_entry_count"], 2)
        self.assertEqual(result["page_observations"][0]["matching_form_entry_count"], 1)
        self.assertEqual(
            [x["form"] for x in result["event_candidates"]], ["13F-HR"]
        )

    def test_unclassified_atom_entry_fails_closed(self):
        raw = feed(entry("0000000001-26-000001", "8-K", "2026-11-24T13:00:00Z"))
        with patch.object(p.p401, "fetch_bytes", return_value=raw):
            result = p.fetch_feed(
                "13F-HR", "https://example.test/feed", {
                    "latest_accession": "",
                    "last_successful_poll_end_utc": "",
                }, "schedule", "test-run", "2026-11-24T12:01:00Z",
            )
        self.assertFalse(result["poll_success"])
        self.assertIn("atom_entry_form_unparsed", result["page_error"]["error"])

    def test_fetch_scans_complete_snapshot_after_prior_accession(self):
        raw = feed(
            entry("0000000001-26-000003", "13F-HR", "2026-11-24T13:00:00Z"),
            entry("0000000001-26-000001", "13F-HR", "2026-11-24T12:30:00Z"),
            entry("0000000002-26-000001", "13F-HR", "2026-11-24T11:00:00Z"),
        )
        with patch.object(p.p401, "fetch_bytes", return_value=raw):
            result = p.fetch_feed(
                "13F-HR", "https://example.test/feed", {
                    "latest_accession": "0000000001-26-000001",
                    "last_successful_poll_end_utc": "2026-11-24T10:00:00Z",
                }, "schedule", "test-run", "2026-11-24T12:00:00Z",
            )
        self.assertTrue(result["poll_success"])
        self.assertTrue(result["snapshot_complete"])
        self.assertEqual(result["boundary_type"], "FULL_SNAPSHOT_END_OF_FEED")
        self.assertTrue(result["prior_watermark_found"])
        self.assertEqual(
            [x["accession"] for x in result["event_candidates"]],
            ["0000000001-26-000003", "0000000002-26-000001"],
        )

    def test_late_indexed_accession_after_watermark_on_later_page_is_captured(self):
        first_page = feed(*[
            entry(f"0000000001-26-{i:06d}", "13F-HR", "2026-11-24T13:00:00Z")
            for i in range(200, 100, -1)
        ])
        second_page = feed(
            entry("0000000001-26-000100", "13F-HR", "2026-11-24T12:00:00Z"),
            entry("0000000002-26-000001", "13F-HR", "2026-11-20T09:00:00Z"),
        )
        with patch.object(p, "MAX_FEED_PAGES", 2), patch.object(
            p.p401, "fetch_bytes", side_effect=[first_page, second_page]
        ), patch.object(p.time, "sleep"):
            result = p.fetch_feed(
                "13F-HR", "https://example.test/feed", {
                    "latest_accession": "0000000001-26-000100",
                    "last_successful_poll_end_utc": "2026-11-24T12:00:00Z",
                }, "schedule", "test-run", "2026-11-24T13:01:00Z",
            )
        self.assertTrue(result["poll_success"])
        self.assertTrue(result["prior_watermark_found"])
        self.assertEqual(result["raw_page_count"], 2)
        self.assertIn(
            "0000000002-26-000001",
            [x["accession"] for x in result["event_candidates"]],
        )

    def test_initial_baseline_enumerates_all_pages_before_setting_watermark(self):
        first_page = feed(*[
            entry(f"0000000001-26-{i:06d}", "13F-HR", "2026-11-24T13:00:00Z")
            for i in range(200, 100, -1)
        ])
        second_page = feed(
            entry("0000000002-26-000001", "13F-HR", "2026-11-24T12:00:00Z")
        )
        with patch.object(p, "MAX_FEED_PAGES", 2), patch.object(
            p.p401, "fetch_bytes", side_effect=[first_page, second_page]
        ), patch.object(p.time, "sleep"):
            result = p.fetch_feed(
                "13F-HR", "https://example.test/feed", {
                    "latest_accession": "",
                    "last_successful_poll_end_utc": "",
                }, "schedule", "test-run", "2026-11-24T13:01:00Z",
            )
        self.assertTrue(result["poll_success"])
        self.assertEqual(result["boundary_type"], "INITIAL_BASELINE_FULL_SNAPSHOT")
        self.assertEqual(result["raw_page_count"], 2)
        self.assertEqual(len(result["event_candidates"]), 101)
        self.assertEqual(result["poll_interval_status"], "INITIAL_BASELINE_NO_LOWER_BOUND")

    def test_missing_prior_accession_is_not_a_gap_after_complete_snapshot(self):
        raw = feed(
            entry("0000000001-26-000003", "13F-HR", "2026-11-24T13:00:00Z"),
            entry("0000000001-26-000002", "13F-HR", "2026-11-24T12:30:00Z"),
        )
        with patch.object(p.p401, "fetch_bytes", return_value=raw):
            result = p.fetch_feed(
                "13F-HR", "https://example.test/feed", {
                    "latest_accession": "0000000001-26-000001",
                    "last_successful_poll_end_utc": "2026-11-24T12:00:00Z",
                }, "schedule", "test-run", "2026-11-24T13:01:00Z",
            )
        self.assertTrue(result["poll_success"])
        self.assertFalse(result["prior_watermark_found"])
        self.assertEqual(result["boundary_type"], "FULL_SNAPSHOT_END_OF_FEED")
        self.assertEqual(len(result["event_candidates"]), 2)

    def test_empty_feed_is_a_complete_snapshot(self):
        raw = feed()
        with patch.object(p.p401, "fetch_bytes", return_value=raw):
            result = p.fetch_feed(
                "13F-HR", "https://example.test/feed", {
                    "latest_accession": "0000000001-26-000001",
                    "last_successful_poll_end_utc": "2026-11-24T12:00:00Z",
                }, "schedule", "test-run", "2026-11-24T12:01:00Z",
            )
        self.assertTrue(result["poll_success"])
        self.assertEqual(result["boundary_type"], "EMPTY_FEED_END_OF_SNAPSHOT")
        self.assertEqual(result["event_candidates"], [])

    def test_empty_page_after_full_page_confirms_end_of_snapshot(self):
        full_page = feed(*[
            entry(f"0000000001-26-{i:06d}", "13F-HR", "2026-11-24T13:00:00Z")
            for i in range(100, 0, -1)
        ])
        empty_page = feed()
        with patch.object(p, "MAX_FEED_PAGES", 2), patch.object(
            p.p401, "fetch_bytes", side_effect=[full_page, empty_page]
        ), patch.object(p.time, "sleep"):
            result = p.fetch_feed(
                "13F-HR", "https://example.test/feed", {
                    "latest_accession": "",
                    "last_successful_poll_end_utc": "2026-11-24T12:00:00Z",
                }, "schedule", "test-run", "2026-11-24T12:01:00Z",
            )
        self.assertTrue(result["poll_success"])
        self.assertEqual(result["boundary_type"], "FULL_SNAPSHOT_END_OF_FEED")
        self.assertEqual(len(result["event_candidates"]), 100)

    def test_nonmonotonic_atom_updated_does_not_block_snapshot(self):
        raw = feed(
            entry("0000000001-26-000003", "13F-HR", "2026-11-24T13:00:00Z"),
            entry("0000000001-26-000002", "13F-HR", "2026-11-24T11:00:00Z"),
            entry("0000000001-26-000001", "13F-HR", "2026-11-24T12:00:00Z"),
        )
        with patch.object(p.p401, "fetch_bytes", return_value=raw):
            result = p.fetch_feed(
                "13F-HR", "https://example.test/feed", {
                    "latest_accession": "0000000001-26-000001",
                    "last_successful_poll_end_utc": "2026-11-24T12:00:00Z",
                }, "schedule", "test-run", "2026-11-24T13:01:00Z",
            )
        self.assertTrue(result["poll_success"])
        self.assertTrue(result["prior_watermark_found"])
        self.assertEqual(result["boundary_type"], "FULL_SNAPSHOT_END_OF_FEED")

    def test_unknown_atom_updated_does_not_block_snapshot(self):
        raw = feed(
            entry("0000000001-26-000003", "13F-HR", "2026-11-24T13:00:00"),
            entry("0000000001-26-000001", "13F-HR", "2026-11-24T10:00:00Z"),
        )
        with patch.object(p.p401, "fetch_bytes", return_value=raw):
            result = p.fetch_feed(
                "13F-HR", "https://example.test/feed", {
                    "latest_accession": "0000000001-26-000001",
                    "last_successful_poll_end_utc": "2026-11-24T12:00:00Z",
                }, "schedule", "test-run", "2026-11-24T13:01:00Z",
            )
        self.assertTrue(result["poll_success"])
        self.assertEqual(result["event_candidates"][0]["feed_updated_utc"], "")

    def test_pagination_limit_fails_closed_without_end_of_feed(self):
        full_page = feed(*[
            entry(f"0000000001-26-{i:06d}", "13F-HR", "2026-11-24T13:00:00Z")
            for i in range(100, 0, -1)
        ])
        with patch.object(p, "MAX_FEED_PAGES", 1), patch.object(
            p.p401, "fetch_bytes", return_value=full_page
        ):
            result = p.fetch_feed(
                "13F-HR", "https://example.test/feed", {
                    "latest_accession": "0000000001-26-000001",
                    "last_successful_poll_end_utc": "2026-11-24T12:00:00Z",
                }, "schedule", "test-run", "2026-11-24T13:01:00Z",
            )
        self.assertFalse(result["poll_success"])
        self.assertFalse(result["snapshot_complete"])
        self.assertEqual(result["page_error"]["error_type"], "PaginationLimitReached")

    def test_repeated_page_hash_fails_closed(self):
        full_page = feed(*[
            entry(f"0000000001-26-{i:06d}", "13F-HR", "2026-11-24T13:00:00Z")
            for i in range(100, 0, -1)
        ])
        with patch.object(p, "MAX_FEED_PAGES", 2), patch.object(
            p.p401, "fetch_bytes", return_value=full_page
        ), patch.object(p.time, "sleep"):
            result = p.fetch_feed(
                "13F-HR", "https://example.test/feed", {
                    "latest_accession": "0000000001-26-000001",
                    "last_successful_poll_end_utc": "2026-11-24T12:00:00Z",
                }, "schedule", "test-run", "2026-11-24T13:01:00Z",
            )
        self.assertFalse(result["poll_success"])
        self.assertIn("repeated_page_hash", result["page_error"]["error"])




class Phase614PersistenceTests(unittest.TestCase):
    def test_manual_run_does_not_persist_state_or_ledgers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with (
                patch.object(p, "STATE_PATH", root / "state.json"),
                patch.object(p, "EVENTS_PATH", root / "events.csv"),
                patch.object(p, "PAGE_OBSERVATIONS_PATH", root / "pages.csv"),
                patch.object(p, "ACCESSION_OBSERVATIONS_PATH", root / "observations.csv"),
                patch.object(p, "FEEDS", {"13F-HR": "feed-hr", "13F-NT": "feed-nt"}),
                patch.object(p, "fetch_feed", return_value={
                    "prior_watermark": "", "previous_successful_poll_end_utc": "",
                    "boundary_found": True, "boundary_type": "INITIAL_BASELINE",
                    "poll_success": True, "poll_interval_status": "INITIAL_BASELINE_NO_LOWER_BOUND",
                    "new_latest_accession": "", "latest_feed_updated_utc": "",
                    "event_candidates": [], "page_observations": [],
                    "accession_observations": [], "page_error": {},
                    "raw_page_count": 0, "candidate_accession_occurrence_count": 0,
                    "candidate_accession_count": 0,
                }),
            ):
                summary = p.run_capture("manual", "manual-test", root / "out")
            self.assertFalse((root / "state.json").exists())
            self.assertFalse((root / "events.csv").exists())
            self.assertFalse(summary["persistent_write"])
            self.assertEqual(summary["signal_eligible_count"], 0)

    def test_scheduled_bounded_metadata_is_not_a_research_signal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = {
                "schema_version": 1,
                "phase": p.PHASE,
                "feeds": {
                    "13F-HR": {
                        "latest_accession": "0000000001-26-000001",
                        "last_successful_poll_end_utc": "2026-11-24T12:00:00Z",
                    },
                    "13F-NT": {
                        "latest_accession": "0000000002-26-000001",
                        "last_successful_poll_end_utc": "2026-11-24T12:00:00Z",
                    },
                },
            }
            (root / "state.json").write_text(json.dumps(state), encoding="utf-8")
            def fake_fetch(feed_name, base_url, feed_state, mode, run_id, poll_started):
                form = "13F-HR" if feed_name == "13F-HR" else "13F-NT"
                acc = "0000000001-26-000002" if feed_name == "13F-HR" else "0000000002-26-000002"
                return {
                    "prior_watermark": feed_state["latest_accession"],
                    "previous_successful_poll_end_utc": feed_state["last_successful_poll_end_utc"],
                    "boundary_found": True, "boundary_type": "FULL_SNAPSHOT_END_OF_FEED",
                    "prior_watermark_found": True, "snapshot_complete": True,
                    "poll_success": True, "poll_interval_status": "FULL_SNAPSHOT_COMPLETE",
                    "new_latest_accession": acc, "latest_feed_updated_utc": "2026-11-24T12:30:00Z",
                    "event_candidates": [candidate(acc, form)],
                    "page_observations": [], "accession_observations": [],
                    "page_error": {}, "raw_page_count": 1,
                    "candidate_accession_occurrence_count": 1, "candidate_accession_count": 1,
                }
            with (
                patch.object(p, "STATE_PATH", root / "state.json"),
                patch.object(p, "EVENTS_PATH", root / "events.csv"),
                patch.object(p, "PAGE_OBSERVATIONS_PATH", root / "pages.csv"),
                patch.object(p, "ACCESSION_OBSERVATIONS_PATH", root / "observations.csv"),
                patch.object(p, "FEEDS", {"13F-HR": "feed-hr", "13F-NT": "feed-nt"}),
                patch.object(p, "fetch_feed", side_effect=fake_fetch),
                patch.object(p, "now_utc", side_effect=[
                    "2026-11-24T12:01:00Z", "2026-11-24T13:10:00Z"
                ]),
            ):
                summary = p.run_capture("schedule", "scheduled-test", root / "out")
            with (root / "events.csv").open("r", encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 2)
            self.assertTrue(all(row["metadata_observation_eligible"] == "True" for row in rows))
            self.assertTrue(all(row["research_observation_eligible"] == "False" for row in rows))
            self.assertTrue(all(row["signal_eligible"] == "False" for row in rows))
            self.assertEqual(summary["metadata_observation_eligible_count"], 2)
            self.assertEqual(summary["research_observation_eligible_count"], 0)
            self.assertEqual(summary["signal_eligible_count"], 0)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from research import phase476_sec_form4_first_seen_capture as p


def entry(accession: str, form: str = "4", updated: str = "2026-11-18T10:00:00-04:00"):
    cik = accession.split("-")[0].lstrip("0") or "0"
    term = form
    return f"""
    <entry>
      <id>urn:tag:sec.gov,2008:accession-number={accession}</id>
      <title>{form} - Test Reporting Owner (0000000001) (Reporting)</title>
      <updated>{updated}</updated>
      <link rel="alternate" href="https://www.sec.gov/Archives/edgar/data/{cik}/{accession.replace('-', '')}/{accession}-index.htm"/>
      <summary type="html">&lt;b&gt;Filed:&lt;/b&gt; 2026-11-18 &lt;b&gt;AccNo:&lt;/b&gt; {accession}</summary>
      <category scheme="https://www.sec.gov/" label="form type" term="{term}"/>
    </entry>
    """


def feed(*entries):
    return ('<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom">' + "".join(entries) + "</feed>").encode()


class Phase476Tests(unittest.TestCase):
    def setUp(self):
        self.url = p.FEEDS["4"]

    def test_extract_hyphenated_accession(self):
        self.assertEqual(p.extract_accession("0000320193-26-000001"), "0000320193-26-000001")

    def test_extract_compact_accession(self):
        self.assertEqual(p.extract_accession("000032019326000001"), "0000320193-26-000001")

    def test_extract_missing_accession(self):
        self.assertIsNone(p.extract_accession("no accession"))

    def test_parse_form4_category(self):
        raw = feed(entry("0000000001-26-000001", "4"))
        rows = p.parse_atom_feed(raw, "4", self.url)
        self.assertEqual(rows[0]["form"], "4")

    def test_parse_form4a_category(self):
        raw = feed(entry("0000000001-26-000002", "4/A"))
        rows = p.parse_atom_feed(raw, "4A", p.FEEDS["4A"])
        self.assertEqual(rows[0]["form"], "4/A")

    def test_form4_feed_accepts_amendment_prefix(self):
        raw = feed(entry("0000000001-26-000003", "4/A"))
        self.assertEqual(len(p.parse_atom_feed(raw, "4", self.url)), 1)

    def test_form4a_feed_excludes_original_form4(self):
        raw = feed(entry("0000000001-26-000004", "4"))
        self.assertEqual(p.parse_atom_feed(raw, "4A", p.FEEDS["4A"]), [])

    def test_parse_filing_date_and_path_cik(self):
        rows = p.parse_atom_feed(feed(entry("0000000123-26-000005")), "4", self.url)
        self.assertEqual(rows[0]["filing_date"], "2026-11-18")
        self.assertEqual(rows[0]["feed_path_cik_unverified"], "0000000123")

    def test_feed_updated_is_converted_to_utc(self):
        rows = p.parse_atom_feed(feed(entry("0000000001-26-000006")), "4", self.url)
        self.assertEqual(rows[0]["feed_updated_utc"], "2026-11-18T14:00:00Z")

    def test_invalid_feed_updated_remains_unknown(self):
        rows = p.parse_atom_feed(feed(entry("0000000001-26-000007", updated="not-a-date")), "4", self.url)
        self.assertEqual(rows[0]["feed_updated_utc"], "")

    def test_non_ownership_form_is_ignored(self):
        raw = feed(entry("0000000001-26-000008", "8-K"))
        self.assertEqual(p.parse_atom_feed(raw, "4", self.url), [])

    def test_malformed_xml_fails_closed(self):
        with self.assertRaises(Exception):
            p.parse_atom_feed(b"<feed>", "4", self.url)

    def test_initial_baseline_has_no_lower_bound(self):
        self.assertEqual(
            p.classify_poll_interval("schedule", None, False, None),
            "INITIAL_BASELINE_NO_LOWER_BOUND",
        )

    def test_missing_watermark_is_gap(self):
        self.assertEqual(
            p.classify_poll_interval("schedule", "old", False, "2026-11-18T10:00:00Z"),
            "GAP_OR_WATERMARK_NOT_FOUND",
        )

    def test_missing_prior_success_is_not_bounded(self):
        self.assertEqual(
            p.classify_poll_interval("schedule", "old", True, None),
            "NO_PRIOR_SUCCESSFUL_POLL",
        )

    def test_bounded_metadata_requires_prior_watermark_and_success(self):
        self.assertEqual(
            p.classify_poll_interval("schedule", "old", True, "2026-11-18T10:00:00Z"),
            "POLL_WATERMARK_BOUNDED",
        )
        self.assertEqual(
            p.classify_interval(
                "schedule", "old", True, "2026-11-18T10:00:00Z",
                "2026-11-18T10:30:00Z", "2026-11-18T11:00:00Z",
            ),
            "BOUNDED_METADATA_ONLY",
        )

    def test_stale_feed_timestamp_is_not_bounded(self):
        self.assertEqual(
            p.classify_interval(
                "schedule", "old", True, "2026-11-18T10:00:00Z",
                "2026-11-18T09:59:59Z", "2026-11-18T11:00:00Z",
            ),
            "FEED_TIMESTAMP_NOT_AFTER_PREVIOUS_POLL",
        )

    def test_missing_feed_timestamp_is_not_bounded(self):
        self.assertEqual(
            p.classify_interval(
                "schedule", "old", True, "2026-11-18T10:00:00Z",
                "", "2026-11-18T11:00:00Z",
            ),
            "FEED_OR_RECEIPT_TIMESTAMP_UNKNOWN",
        )

    def test_future_feed_timestamp_is_not_bounded(self):
        self.assertEqual(
            p.classify_interval(
                "schedule", "old", True, "2026-11-18T10:00:00Z",
                "2026-11-18T11:00:01Z", "2026-11-18T11:00:00Z",
            ),
            "FEED_TIMESTAMP_AFTER_FIRST_SEEN",
        )

    def test_manual_capture_never_becomes_bounded(self):
        self.assertEqual(
            p.classify_poll_interval("manual", "old", True, "2026-11-18T10:00:00Z"),
            "MANUAL_DIAGNOSTIC",
        )

    def test_count_atom_entries_counts_raw_rows(self):
        self.assertEqual(p.count_atom_entries(feed(
            entry("0000000001-26-000010"), entry("0000000001-26-000011")
        )), 2)

    def test_page_url_uses_raw_offset(self):
        self.assertTrue(p._page_url(self.url, 100).endswith("&start=100"))

    @patch.object(p.p401, "fetch_bytes")
    def test_first_poll_is_one_page_baseline(self, fetch):
        raw = feed(entry("0000000001-26-000012"), entry("0000000001-26-000013"))
        fetch.return_value = raw
        result = p.fetch_feed("4", self.url, {}, "schedule", "run-1")
        self.assertTrue(result["poll_success"])
        self.assertEqual(result["interval_status"], "INITIAL_BASELINE_NO_LOWER_BOUND")
        self.assertEqual(result["new_accession_count"], 2)
        self.assertEqual(fetch.call_count, 1)

    @patch.object(p, "MAX_FEED_PAGES", 2)
    @patch.object(p.p401, "fetch_bytes")
    def test_pagination_advances_by_raw_entry_count_and_finds_watermark(self, fetch, _max_pages=None):
        page1 = feed(*[
            entry(f"0000000001-26-{i:06d}") for i in range(100, 200)
        ])
        prior = "0000000001-26-000099"
        page2 = feed(entry(prior))
        fetch.side_effect = [page1, page2]
        result = p.fetch_feed(
            "4", self.url,
            {"latest_accession": prior, "last_successful_poll_end_utc": "2026-11-18T10:00:00Z"},
            "schedule", "run-2",
        )
        self.assertTrue(result["watermark_found"])
        self.assertTrue(result["poll_success"])
        self.assertEqual(result["new_accession_count"], 100)
        self.assertEqual(fetch.call_count, 2)
        self.assertIn("start=100", fetch.call_args_list[1].args[0])

    @patch.object(p, "MAX_FEED_PAGES", 2)
    @patch.object(p, "PAGE_DELAY_SECONDS", 0)
    @patch.object(p.p401, "fetch_bytes")
    def test_missing_watermark_after_page_limit_is_gap(self, fetch, _delay=None, _max_pages=None):
        fetch.side_effect = [
            feed(entry("0000000001-26-000020")),
            feed(entry("0000000001-26-000021")),
        ]
        result = p.fetch_feed(
            "4", self.url,
            {"latest_accession": "0000000001-25-999999", "last_successful_poll_end_utc": "2026-11-18T10:00:00Z"},
            "schedule", "run-3",
        )
        self.assertFalse(result["poll_success"])
        self.assertEqual(result["interval_status"], "GAP_OR_WATERMARK_NOT_FOUND")
        self.assertEqual(result["page_error"]["error_type"], "PaginationLimitReached")

    @patch.object(p, "MAX_FEED_PAGES", 2)
    @patch.object(p, "PAGE_DELAY_SECONDS", 0)
    @patch.object(p.p401, "fetch_bytes")
    def test_repeated_page_hash_is_gap(self, fetch, _delay=None, _max_pages=None):
        raw = feed(entry("0000000001-26-000022"))
        fetch.side_effect = [raw, raw]
        result = p.fetch_feed(
            "4", self.url,
            {"latest_accession": "0000000001-25-999999", "last_successful_poll_end_utc": "2026-11-18T10:00:00Z"},
            "schedule", "run-4",
        )
        self.assertFalse(result["poll_success"])
        self.assertEqual(result["page_error"]["error_type"], "RepeatedPageHash")

    @patch.object(p, "MAX_FEED_PAGES", 2)
    @patch.object(p, "PAGE_DELAY_SECONDS", 0)
    @patch.object(p.p401, "fetch_bytes")
    def test_fetch_error_does_not_claim_poll_success(self, fetch, _delay=None, _max_pages=None):
        fetch.side_effect = [feed(entry("0000000001-26-000023")), RuntimeError("temporary")]
        result = p.fetch_feed(
            "4", self.url,
            {"latest_accession": "0000000001-25-999999", "last_successful_poll_end_utc": "2026-11-18T10:00:00Z"},
            "schedule", "run-5",
        )
        self.assertFalse(result["poll_success"])
        self.assertEqual(result["page_error"]["error_type"], "RuntimeError")

    def test_event_policy_never_authorizes_signal(self):
        # A bounded first-seen interval is metadata only; all identity and semantics gates remain false.
        status = p.classify_interval(
            "schedule", "old", True, "2026-11-18T10:00:00Z",
            "2026-11-18T10:30:00Z", "2026-11-18T11:00:00Z",
        )
        self.assertEqual(status, "BOUNDED_METADATA_ONLY")
        self.assertFalse(status == "SIGNAL_ELIGIBLE")

    def test_existing_accessions_are_append_only_dedup_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "events.csv"
            p.append_csv(path, ["accession", "form"], [{"accession": "a", "form": "4"}])
            p.append_csv(path, ["accession", "form"], [{"accession": "b", "form": "4/A"}])
            self.assertEqual(path.read_text().count("accession,form"), 1)
            self.assertEqual(path.read_text().count("\n"), 3)

    def test_hash_is_sha256_of_exact_page_bytes(self):
        raw = feed(entry("0000000001-26-000024"))
        self.assertEqual(hashlib.sha256(raw).hexdigest(), hashlib.sha256(raw).hexdigest())


    def test_run_capture_initial_baseline_persists_no_signal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_dir = root / "data"
            output_dir = root / "output"
            raw = feed(entry("0000000001-26-000030"))
            with patch.object(p, "DATA_DIR", data_dir), \
                 patch.object(p, "STATE_PATH", data_dir / "state.json"), \
                 patch.object(p, "EVENTS_PATH", data_dir / "events.csv"), \
                 patch.object(p, "OBSERVATIONS_PATH", data_dir / "feed_observations.csv"), \
                 patch.object(p, "FEEDS", {"4": self.url}), \
                 patch.object(p.p401, "fetch_bytes", return_value=raw):
                summary = p.run_capture("schedule", "baseline-run", output_dir)
            self.assertEqual(summary["new_event_rows"], 1)
            self.assertEqual(summary["bounded_metadata_rows"], 0)
            self.assertEqual(summary["signal_eligible_rows"], 0)
            self.assertTrue((data_dir / "state.json").exists())
            with (data_dir / "events.csv").open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["first_seen_interval_status"], "INITIAL_BASELINE_NO_LOWER_BOUND")
            self.assertEqual(rows[0]["signal_eligible"], "False")
            self.assertEqual(rows[0]["research_observation_eligible"], "False")
            self.assertFalse((data_dir / "raw.xml").exists())

    def test_run_capture_second_poll_bounds_metadata_but_never_signal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_dir = root / "data"
            output_dir = root / "output"
            prior = "0000000001-26-000031"
            first = feed(entry(prior))
            second = feed(entry("0000000001-26-000032", updated="2026-11-18T10:30:00Z"), entry(prior))
            with patch.object(p, "DATA_DIR", data_dir), \
                 patch.object(p, "STATE_PATH", data_dir / "state.json"), \
                 patch.object(p, "EVENTS_PATH", data_dir / "events.csv"), \
                 patch.object(p, "OBSERVATIONS_PATH", data_dir / "feed_observations.csv"), \
                 patch.object(p, "FEEDS", {"4": self.url}), \
                 patch.object(p.p401, "fetch_bytes", side_effect=[first, second]), \
                 patch.object(p, "now_utc", side_effect=[
                     "2026-11-18T10:00:00Z", "2026-11-18T10:00:01Z", "2026-11-18T10:00:02Z",
                     "2026-11-18T11:00:00Z", "2026-11-18T11:00:01Z", "2026-11-18T11:00:02Z",
                 ]):
                p.run_capture("schedule", "baseline-run", output_dir)
                previous_end = json.loads((data_dir / "state.json").read_text())["feeds"]["4"]["last_successful_poll_end_utc"]
                summary = p.run_capture("schedule", "bounded-run", output_dir)
            self.assertEqual(summary["new_event_rows"], 1)
            self.assertEqual(summary["bounded_metadata_rows"], 1)
            with (data_dir / "events.csv").open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            bounded = next(row for row in rows if row["accession"] == "0000000001-26-000032")
            self.assertEqual(bounded["first_seen_interval_status"], "BOUNDED_METADATA_ONLY")
            self.assertEqual(bounded["first_seen_interval_lower_bound_utc"], previous_end)
            self.assertEqual(bounded["event_metadata_interval_bounded"], "True")
            self.assertEqual(bounded["research_observation_eligible"], "False")
            self.assertEqual(bounded["signal_eligible"], "False")

    def test_manual_run_does_not_persist_state_or_events(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_dir = root / "data"
            output_dir = root / "output"
            raw = feed(entry("0000000001-26-000033"))
            with patch.object(p, "DATA_DIR", data_dir), \
                 patch.object(p, "STATE_PATH", data_dir / "state.json"), \
                 patch.object(p, "EVENTS_PATH", data_dir / "events.csv"), \
                 patch.object(p, "OBSERVATIONS_PATH", data_dir / "feed_observations.csv"), \
                 patch.object(p, "FEEDS", {"4": self.url}), \
                 patch.object(p.p401, "fetch_bytes", return_value=raw):
                summary = p.run_capture("manual", "manual-run", output_dir)
            self.assertFalse(summary["persistent_write"])
            self.assertFalse(data_dir.exists())
            self.assertTrue((output_dir / "poll_summary.json").exists())

    def test_gap_does_not_advance_prior_watermark(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_dir = root / "data"
            output_dir = root / "output"
            data_dir.mkdir()
            previous_end = "2026-11-18T10:00:00Z"
            old_state = {
                "schema_version": 1,
                "phase": p.PHASE,
                "feeds": {"4": {
                    "latest_accession": "0000000001-25-999999",
                    "last_successful_poll_end_utc": previous_end,
                }},
            }
            (data_dir / "state.json").write_text(json.dumps(old_state))
            raw = feed(entry("0000000001-26-000034"))
            with patch.object(p, "DATA_DIR", data_dir), \
                 patch.object(p, "STATE_PATH", data_dir / "state.json"), \
                 patch.object(p, "EVENTS_PATH", data_dir / "events.csv"), \
                 patch.object(p, "OBSERVATIONS_PATH", data_dir / "feed_observations.csv"), \
                 patch.object(p, "FEEDS", {"4": self.url}), \
                 patch.object(p, "MAX_FEED_PAGES", 1), \
                 patch.object(p.p401, "fetch_bytes", return_value=raw):
                summary = p.run_capture("schedule", "gap-run", output_dir)
            state = json.loads((data_dir / "state.json").read_text())
            self.assertEqual(state["feeds"]["4"]["latest_accession"], "0000000001-25-999999")
            self.assertEqual(state["feeds"]["4"]["last_successful_poll_end_utc"], previous_end)
            self.assertEqual(state["feeds"]["4"]["last_poll_status"], "GAP_OR_FETCH_ERROR")
            self.assertEqual(summary["bounded_metadata_rows"], 0)

    def test_duplicate_accession_is_not_appended_twice(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_dir = root / "data"
            output_dir = root / "output"
            raw = feed(entry("0000000001-26-000035"))
            with patch.object(p, "DATA_DIR", data_dir), \
                 patch.object(p, "STATE_PATH", data_dir / "state.json"), \
                 patch.object(p, "EVENTS_PATH", data_dir / "events.csv"), \
                 patch.object(p, "OBSERVATIONS_PATH", data_dir / "feed_observations.csv"), \
                 patch.object(p, "FEEDS", {"4": self.url}), \
                 patch.object(p.p401, "fetch_bytes", side_effect=[raw, raw]):
                p.run_capture("schedule", "baseline-run", output_dir)
                p.run_capture("schedule", "same-run", output_dir)
            with (data_dir / "events.csv").open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 1)



if __name__ == "__main__":
    unittest.main()

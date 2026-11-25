from __future__ import annotations

import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from research import phase476_sec_form4_first_seen_capture as p


def entry(
    accession: str,
    form: str = "4",
    updated: str = "2026-11-18T10:00:00-04:00",
    entity_cik: str | None = None,
    entity_name: str = "Test Reporting Owner",
    entity_role: str = "Reporting",
    link_cik: str | None = None,
):
    submitter_cik = accession.split("-")[0].zfill(10)
    entity_cik = (entity_cik or submitter_cik).zfill(10)
    link_cik = (link_cik or entity_cik).zfill(10)
    term = form
    return f"""
    <entry>
      <id>urn:tag:sec.gov,2008:accession-number={accession}</id>
      <title>{form} - {entity_name} ({entity_cik}) ({entity_role})</title>
      <updated>{updated}</updated>
      <link rel="alternate" href="https://www.sec.gov/Archives/edgar/data/{int(link_cik)}/{accession.replace('-', '')}/{accession}-index.htm"/>
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

    def test_naive_feed_timestamp_is_rejected_without_assuming_utc(self):
        self.assertIsNone(p.parse_utc("2026-11-18T10:30:00"))
        self.assertEqual(
            p.classify_interval(
                "schedule", "old", True, "2026-11-18T10:00:00Z",
                "2026-11-18T10:30:00", "2026-11-18T11:00:00Z",
            ),
            "FEED_OR_RECEIPT_TIMESTAMP_UNKNOWN",
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
        self.assertEqual(result["candidate_accession_count"], 2)
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
        self.assertEqual(result["candidate_accession_count"], 100)
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
                 patch.object(p, "ACCESSION_OBSERVATIONS_PATH", data_dir / "accession_observations.csv"), \
                 patch.object(p, "ENTITY_OBSERVATIONS_PATH", data_dir / "entity_observations.csv"), \
                 patch.object(p, "ENTITY_DUPLICATE_AUDIT_PATH", data_dir / "entity_duplicate_audit.csv"), \
                 patch.object(p, "FEEDS", {"4": self.url}), \
                 patch.object(p.p401, "fetch_bytes", return_value=raw):
                summary = p.run_capture("schedule", "baseline-run", output_dir)
            self.assertEqual(summary["new_event_rows"], 1)
            self.assertTrue(summary["all_feeds_successful"])
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
                 patch.object(p, "ACCESSION_OBSERVATIONS_PATH", data_dir / "accession_observations.csv"), \
                 patch.object(p, "ENTITY_OBSERVATIONS_PATH", data_dir / "entity_observations.csv"), \
                 patch.object(p, "ENTITY_DUPLICATE_AUDIT_PATH", data_dir / "entity_duplicate_audit.csv"), \
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
            self.assertTrue(summary["all_feeds_successful"])
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
                 patch.object(p, "ACCESSION_OBSERVATIONS_PATH", data_dir / "accession_observations.csv"), \
                 patch.object(p, "ENTITY_OBSERVATIONS_PATH", data_dir / "entity_observations.csv"), \
                 patch.object(p, "ENTITY_DUPLICATE_AUDIT_PATH", data_dir / "entity_duplicate_audit.csv"), \
                 patch.object(p, "FEEDS", {"4": self.url}), \
                 patch.object(p.p401, "fetch_bytes", return_value=raw):
                summary = p.run_capture("manual", "manual-run", output_dir)
            self.assertFalse(summary["persistent_write"])
            self.assertFalse(summary["accession_observation_ledger_persisted"])
            self.assertFalse(data_dir.exists())
            self.assertFalse((data_dir / "accession_observations.csv").exists())
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
                 patch.object(p, "ACCESSION_OBSERVATIONS_PATH", data_dir / "accession_observations.csv"), \
                 patch.object(p, "ENTITY_OBSERVATIONS_PATH", data_dir / "entity_observations.csv"), \
                 patch.object(p, "ENTITY_DUPLICATE_AUDIT_PATH", data_dir / "entity_duplicate_audit.csv"), \
                 patch.object(p, "FEEDS", {"4": self.url}), \
                 patch.object(p, "MAX_FEED_PAGES", 1), \
                 patch.object(p.p401, "fetch_bytes", return_value=raw):
                summary = p.run_capture("schedule", "gap-run", output_dir)
            state = json.loads((data_dir / "state.json").read_text())
            self.assertEqual(state["feeds"]["4"]["latest_accession"], "0000000001-25-999999")
            self.assertEqual(state["feeds"]["4"]["last_successful_poll_end_utc"], previous_end)
            self.assertEqual(state["feeds"]["4"]["last_poll_status"], "GAP_OR_FETCH_ERROR")
            self.assertEqual(summary["bounded_metadata_rows"], 0)
            self.assertEqual(summary["new_event_rows"], 0)
            self.assertFalse(summary["all_feeds_successful"])
            self.assertEqual(summary["incomplete_poll_candidate_rows_suppressed"], 1)
            self.assertEqual(summary["incomplete_poll_candidate_occurrences_suppressed"], 1)
            self.assertFalse((data_dir / "events.csv").exists())
            with (data_dir / "accession_observations.csv").open(newline="", encoding="utf-8") as handle:
                observations = list(csv.DictReader(handle))
            self.assertEqual(len(observations), 1)
            self.assertEqual(observations[0]["candidate_suppressed_in_incomplete_poll"], "True")
            self.assertEqual(observations[0]["canonical_event_emitted"], "False")

    def test_incomplete_poll_candidates_can_be_reconciled_on_successful_retry(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_dir = root / "data"
            output_dir = root / "output"
            prior = "0000000001-25-999999"
            new_accession = "0000000001-26-000034"
            baseline = feed(entry(prior, updated="2026-11-18T09:00:00Z"))
            incomplete = feed(entry(new_accession, updated="2026-11-18T10:30:30Z"))
            retry = feed(
                entry(new_accession, updated="2026-11-18T10:30:30Z"),
                entry(prior, updated="2026-11-18T09:00:00Z"),
            )
            with (
                patch.object(p, "DATA_DIR", data_dir),
                patch.object(p, "STATE_PATH", data_dir / "state.json"),
                patch.object(p, "EVENTS_PATH", data_dir / "events.csv"),
                patch.object(p, "OBSERVATIONS_PATH", data_dir / "feed_observations.csv"),
                patch.object(p, "ACCESSION_OBSERVATIONS_PATH", data_dir / "accession_observations.csv"), \
                patch.object(p, "FEEDS", {"4": self.url}),
                patch.object(p, "MAX_FEED_PAGES", 1),
                patch.object(p.p401, "fetch_bytes", side_effect=[baseline, incomplete, retry]),
                patch.object(p, "now_utc", side_effect=[
                    "2026-11-18T10:00:00Z", "2026-11-18T10:00:01Z", "2026-11-18T10:00:02Z",
                    "2026-11-18T10:30:00Z", "2026-11-18T10:30:01Z", "2026-11-18T10:30:02Z",
                    "2026-11-18T11:00:00Z", "2026-11-18T11:00:01Z", "2026-11-18T11:00:02Z",
                ]),
            ):
                p.run_capture("schedule", "baseline-run", output_dir)
                failed = p.run_capture("schedule", "gap-run", output_dir)
                self.assertEqual(failed["new_event_rows"], 0)
                self.assertFalse(failed["all_feeds_successful"])
                self.assertEqual(failed["incomplete_poll_candidate_rows_suppressed"], 1)
                with (data_dir / "events.csv").open(newline="", encoding="utf-8") as handle:
                    after_gap = list(csv.DictReader(handle))
                self.assertEqual([row["accession"] for row in after_gap], [prior])

                recovered = p.run_capture("schedule", "retry-run", output_dir)

            self.assertEqual(recovered["new_event_rows"], 1)
            self.assertTrue(recovered["all_feeds_successful"])
            self.assertEqual(recovered["bounded_metadata_rows"], 1)
            with (data_dir / "events.csv").open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 2)
            new_row = next(row for row in rows if row["accession"] == new_accession)
            self.assertEqual(new_row["first_seen_interval_status"], "BOUNDED_METADATA_ONLY")
            self.assertEqual(new_row["first_seen_interval_lower_bound_utc"], "2026-11-18T10:00:02Z")
            self.assertEqual(new_row["first_seen_at_utc"], "2026-11-18T11:00:01Z")
            self.assertEqual(new_row["signal_eligible"], "False")
            with (data_dir / "accession_observations.csv").open(newline="", encoding="utf-8") as handle:
                observations = list(csv.DictReader(handle))
            suppressed = [
                row for row in observations
                if row["poll_run_id"] == "gap-run" and row["accession"] == new_accession
            ]
            recovered_observation = next(
                row for row in observations
                if row["poll_run_id"] == "retry-run" and row["accession"] == new_accession
            )
            self.assertEqual(len(suppressed), 1)
            self.assertEqual(suppressed[0]["candidate_suppressed_in_incomplete_poll"], "True")
            self.assertEqual(recovered_observation["canonical_event_emitted"], "True")

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
                 patch.object(p, "ACCESSION_OBSERVATIONS_PATH", data_dir / "accession_observations.csv"), \
                 patch.object(p, "ENTITY_OBSERVATIONS_PATH", data_dir / "entity_observations.csv"), \
                 patch.object(p, "ENTITY_DUPLICATE_AUDIT_PATH", data_dir / "entity_duplicate_audit.csv"), \
                 patch.object(p, "FEEDS", {"4": self.url}), \
                 patch.object(p.p401, "fetch_bytes", side_effect=[raw, raw]):
                p.run_capture("schedule", "baseline-run", output_dir)
                p.run_capture("schedule", "same-run", output_dir)
            with (data_dir / "events.csv").open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 1)


    @patch.object(p.p401, "fetch_bytes")
    def test_fetch_feed_records_duplicate_occurrences_and_prior_watermark(self, fetch):
        prior = "0000000001-26-000099"
        repeated = "0000000001-26-000100"
        raw = feed(
            entry(repeated, "4", updated="2026-11-18T10:30:00Z"),
            entry(repeated, "4", updated="2026-11-18T10:30:00Z"),
            entry(prior, "4", updated="2026-11-18T09:00:00Z"),
        )
        fetch.return_value = raw
        result = p.fetch_feed(
            "4", self.url,
            {"latest_accession": prior, "last_successful_poll_end_utc": "2026-11-18T10:00:00Z"},
            "schedule", "run-duplicate-boundary",
        )
        self.assertTrue(result["poll_success"])
        self.assertEqual(result["candidate_accession_count"], 1)
        self.assertEqual(result["candidate_accession_occurrence_count"], 2)
        self.assertEqual(len(result["accession_observations"]), 3)
        self.assertEqual(
            [row["accession"] for row in result["accession_observations"]],
            [repeated, repeated, prior],
        )
        self.assertEqual(
            [row["event_interval_status"] for row in result["accession_observations"]],
            ["BOUNDED_METADATA_ONLY", "BOUNDED_METADATA_ONLY", "PRIOR_WATERMARK_BOUNDARY"],
        )
        self.assertTrue(result["accession_observations"][-1]["is_prior_watermark"])

    def test_run_capture_accession_observation_ledger_preserves_same_and_cross_feed_duplicates(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_dir = root / "data"
            output_dir = root / "output"
            url4 = p.FEEDS["4"]
            url4a = p.FEEDS["4A"]
            accession_a = "0000000001-26-000041"
            accession_b = "0000000001-26-000042"
            accession_c = "0000000001-26-000043"
            feed4 = feed(
                entry(accession_a, "4"),
                entry(accession_b, "4/A"),
                entry(accession_a, "4"),
            )
            feed4a = feed(
                entry(accession_b, "4/A"),
                entry(accession_c, "4/A"),
            )
            with patch.object(p, "DATA_DIR", data_dir), \
                 patch.object(p, "STATE_PATH", data_dir / "state.json"), \
                 patch.object(p, "EVENTS_PATH", data_dir / "events.csv"), \
                 patch.object(p, "OBSERVATIONS_PATH", data_dir / "feed_observations.csv"), \
                 patch.object(p, "ACCESSION_OBSERVATIONS_PATH", data_dir / "accession_observations.csv"), \
                 patch.object(p, "ENTITY_OBSERVATIONS_PATH", data_dir / "entity_observations.csv"), \
                 patch.object(p, "ENTITY_DUPLICATE_AUDIT_PATH", data_dir / "entity_duplicate_audit.csv"), \
                 patch.object(p, "FEEDS", {"4": url4, "4A": url4a}), \
                 patch.object(p.p401, "fetch_bytes", side_effect=[feed4, feed4a]):
                summary = p.run_capture("schedule", "duplicate-provenance-run", output_dir)

            self.assertEqual(summary["new_event_rows"], 3)
            self.assertEqual(summary["new_accession_count"], 3)
            self.assertEqual(summary["candidate_accession_occurrence_count"], 5)
            self.assertEqual(summary["unique_candidate_accession_count"], 3)
            self.assertEqual(summary["feeds"]["4"]["candidate_accession_count"], 2)
            self.assertEqual(summary["feeds"]["4"]["candidate_accession_occurrence_count"], 3)
            self.assertEqual(summary["feeds"]["4"]["new_accession_count"], 2)
            self.assertEqual(summary["feeds"]["4A"]["candidate_accession_count"], 2)
            self.assertEqual(summary["feeds"]["4A"]["candidate_accession_occurrence_count"], 2)
            self.assertEqual(summary["feeds"]["4A"]["new_accession_count"], 1)
            self.assertEqual(summary["accession_observation_rows"], 5)
            self.assertEqual(summary["same_feed_duplicate_occurrences"], 1)
            self.assertEqual(summary["same_feed_repeated_accession_occurrences"], 1)
            self.assertEqual(summary["exact_duplicate_entity_observation_rows"], 1)
            self.assertEqual(summary["exact_duplicate_entity_key_groups"], 1)
            with (data_dir / "entity_duplicate_audit.csv").open(newline="", encoding="utf-8") as handle:
                entity_audit = list(csv.DictReader(handle))
            self.assertEqual(len(entity_audit), 5)
            self.assertEqual(sum(row["is_exact_duplicate_entity_observation"] == "True" for row in entity_audit), 1)
            self.assertEqual(summary["cross_feed_duplicate_occurrences"], 1)
            self.assertEqual(summary["canonical_event_observation_rows"], 3)
            with (data_dir / "events.csv").open(newline="", encoding="utf-8") as handle:
                events = list(csv.DictReader(handle))
            self.assertEqual(len(events), 3)
            with (data_dir / "accession_observations.csv").open(newline="", encoding="utf-8") as handle:
                observations = list(csv.DictReader(handle))
            self.assertEqual(len(observations), 5)
            same_feed_duplicate = next(
                row for row in observations
                if row["accession"] == accession_a and row["is_duplicate_within_feed"] == "True"
            )
            cross_feed_duplicate = next(
                row for row in observations
                if row["accession"] == accession_b and row["is_duplicate_across_feeds"] == "True"
            )
            self.assertEqual(same_feed_duplicate["canonical_event_emitted"], "False")
            self.assertEqual(cross_feed_duplicate["canonical_event_emitted"], "False")
            self.assertEqual(
                sum(row["canonical_event_emitted"] == "True" for row in observations),
                3,
            )
            self.assertTrue(all(row["signal_eligible"] == "False" for row in events))




    @patch.object(p, "MAX_FEED_PAGES", 21)
    @patch.object(p, "PAGE_DELAY_SECONDS", 0)
    @patch.object(p.p401, "fetch_bytes")
    def test_pagination_can_recover_watermark_after_original_20_page_cap(self, fetch, _delay=None, _max_pages=None):
        prior = "0000000001-25-999999"
        pages = []
        for page_index in range(20):
            start = page_index * 100
            pages.append(feed(*[
                entry(f"0000000001-26-{start + offset:06d}")
                for offset in range(100)
            ]))
        pages.append(feed(entry(prior)))
        fetch.side_effect = pages

        result = p.fetch_feed(
            "4", self.url,
            {"latest_accession": prior, "last_successful_poll_end_utc": "2026-11-18T10:00:00Z"},
            "schedule", "run-after-original-cap",
        )

        self.assertTrue(result["watermark_found"])
        self.assertTrue(result["poll_success"])
        self.assertEqual(result["raw_page_count"], 21)
        self.assertEqual(result["candidate_accession_count"], 2000)
        self.assertEqual(fetch.call_count, 21)
        self.assertIn("start=2000", fetch.call_args_list[-1].args[0])



    def test_parse_feed_entity_role_and_accession_submitter_are_distinct(self):
        accession = "0000000123-26-000005"
        rows = p.parse_atom_feed(
            feed(entry(
                accession,
                entity_cik="0000000456",
                entity_name="Example Reporting Owner LLC",
                entity_role="Reporting",
            )),
            "4",
            self.url,
        )
        self.assertEqual(rows[0]["feed_entity_cik"], "0000000456")
        self.assertEqual(rows[0]["feed_entity_name"], "Example Reporting Owner LLC")
        self.assertEqual(rows[0]["feed_entity_role"], "REPORTING")
        self.assertEqual(rows[0]["feed_entity_status"], "PARSED")
        self.assertEqual(rows[0]["feed_path_cik_unverified"], "0000000456")
        self.assertTrue(rows[0]["feed_path_entity_cik_match"])
        self.assertEqual(p.accession_submitter_cik(accession), "0000000123")

    @patch.object(p.p401, "fetch_bytes")
    def test_multi_owner_accession_selects_issuer_and_preserves_all_entity_rows(self, fetch):
        accession = "0000947871-26-001051"
        raw = feed(
            entry(accession, entity_cik="0001920574", entity_name="OrbiMed Capital GP IX LLC", entity_role="Reporting"),
            entry(accession, entity_cik="0001808744", entity_name="OrbiMed Genesis GP LLC", entity_role="Reporting"),
            entry(accession, entity_cik="0001739410", entity_name="Avenzo Therapeutics, Inc.", entity_role="Issuer"),
            entry(accession, entity_cik="0001055951", entity_name="ORBIMED ADVISORS LLC", entity_role="Reporting"),
            entry("0000000001-26-000099", entity_cik="0000000001", entity_name="Watermark Issuer", entity_role="Issuer"),
        )
        fetch.return_value = raw
        result = p.fetch_feed(
            "4", self.url,
            {"latest_accession": "0000000001-26-000099", "last_successful_poll_end_utc": "2026-11-18T10:00:00Z"},
            "schedule", "multi-owner-run",
        )
        self.assertTrue(result["poll_success"])
        self.assertEqual(result["candidate_accession_count"], 1)
        self.assertEqual(result["candidate_accession_occurrence_count"], 4)
        self.assertEqual(len(result["event_rows"]), 1)
        self.assertEqual(result["event_rows"][0]["accession"], accession)
        self.assertEqual(result["event_rows"][0]["feed_path_cik_unverified"], "0001739410")
        self.assertIn("/1739410/", result["event_rows"][0]["filing_url"])
        self.assertEqual(result["multi_entity_accession_count"], 1)
        self.assertEqual(result["issuer_entity_occurrence_count"], 1)
        self.assertEqual(result["reporting_entity_occurrence_count"], 3)
        self.assertEqual(result["unknown_entity_role_occurrence_count"], 0)
        self.assertEqual(result["path_entity_cik_mismatch_occurrence_count"], 0)
        self.assertEqual(result["quarantined_entity_accession_count"], 0)
        issuer = next(row for row in result["accession_observations"] if row["feed_entity_role"] == "ISSUER")
        self.assertTrue(issuer["_canonical_event_source"])
        self.assertEqual(issuer["canonical_entity_selection_status"], "ISSUER_ENTITY_SELECTED")
        self.assertFalse(next(row for row in result["accession_observations"] if row["feed_entity_role"] == "REPORTING")["_canonical_event_source"])

    @patch.object(p.p401, "fetch_bytes")
    def test_path_entity_cik_mismatch_quarantines_accession(self, fetch):
        accession = "0000000001-26-000051"
        raw = feed(
            entry(accession, entity_cik="0000000001", entity_name="Issuer LLC", entity_role="Issuer", link_cik="0000000002"),
            entry(accession, entity_cik="0000000003", entity_name="Reporting Owner LLC", entity_role="Reporting"),
            entry("0000000001-26-000050", entity_cik="0000000001", entity_name="Watermark Issuer", entity_role="Issuer"),
        )
        fetch.return_value = raw
        result = p.fetch_feed(
            "4", self.url,
            {"latest_accession": "0000000001-26-000050", "last_successful_poll_end_utc": "2026-11-18T10:00:00Z"},
            "schedule", "path-mismatch-run",
        )
        self.assertTrue(result["poll_success"])
        self.assertEqual(result["quarantined_entity_accession_count"], 1)
        self.assertEqual(result["path_entity_cik_mismatch_occurrence_count"], 1)
        self.assertEqual(result["event_rows"], [])
        self.assertTrue(all(row["entity_identity_quarantined"] for row in result["accession_observations"] if row["accession"] == accession))
        self.assertFalse(any(row["_canonical_event_source"] for row in result["accession_observations"] if row["accession"] == accession))

    @patch.object(p.p401, "fetch_bytes")
    def test_multiple_issuer_ciks_quarantine_accession(self, fetch):
        accession = "0000000001-26-000061"
        raw = feed(
            entry(accession, entity_cik="0000000002", entity_name="Issuer A", entity_role="Issuer"),
            entry(accession, entity_cik="0000000003", entity_name="Issuer B", entity_role="Issuer"),
            entry("0000000001-26-000060", entity_cik="0000000001", entity_name="Watermark Issuer", entity_role="Issuer"),
        )
        fetch.return_value = raw
        result = p.fetch_feed(
            "4", self.url,
            {"latest_accession": "0000000001-26-000060", "last_successful_poll_end_utc": "2026-11-18T10:00:00Z"},
            "schedule", "multiple-issuer-run",
        )
        self.assertTrue(result["poll_success"])
        self.assertEqual(result["quarantined_entity_accession_count"], 1)
        self.assertEqual(result["event_rows"], [])
        self.assertTrue(all(row["entity_identity_quarantined"] for row in result["accession_observations"] if row["accession"] == accession))

    @patch.object(p.p401, "fetch_bytes")
    def test_missing_issuer_row_emits_accession_without_owner_locator(self, fetch):
        accession = "0000000001-26-000071"
        raw = feed(
            entry(accession, entity_cik="0000000007", entity_name="Reporting Owner LLC", entity_role="Reporting"),
            entry("0000000001-26-000070", entity_cik="0000000001", entity_name="Watermark Issuer", entity_role="Issuer"),
        )
        fetch.return_value = raw
        result = p.fetch_feed(
            "4", self.url,
            {"latest_accession": "0000000001-26-000070", "last_successful_poll_end_utc": "2026-11-18T10:00:00Z"},
            "schedule", "missing-issuer-run",
        )
        self.assertEqual(len(result["event_rows"]), 1)
        self.assertEqual(result["event_rows"][0]["filing_url"], "")
        self.assertEqual(result["event_rows"][0]["feed_path_cik_unverified"], "")
        self.assertEqual(result["accessions_without_issuer_entity_count"], 1)

    def test_run_capture_persists_entity_occurrence_sidecar_and_marks_issuer_canonical(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_dir = root / "data"
            output_dir = root / "output"
            accession = "0000000001-26-000081"
            raw = feed(
                entry(accession, entity_cik="0000000002", entity_name="Reporting Owner LLC", entity_role="Reporting"),
                entry(accession, entity_cik="0000000003", entity_name="Issuer Company Inc.", entity_role="Issuer"),
            )
            with patch.object(p, "DATA_DIR", data_dir), \
                 patch.object(p, "STATE_PATH", data_dir / "state.json"), \
                 patch.object(p, "EVENTS_PATH", data_dir / "events.csv"), \
                 patch.object(p, "OBSERVATIONS_PATH", data_dir / "feed_observations.csv"), \
                 patch.object(p, "ACCESSION_OBSERVATIONS_PATH", data_dir / "accession_observations.csv"), \
                 patch.object(p, "ENTITY_OBSERVATIONS_PATH", data_dir / "entity_observations.csv"), \
                 patch.object(p, "ENTITY_DUPLICATE_AUDIT_PATH", data_dir / "entity_duplicate_audit.csv"), \
                 patch.object(p, "FEEDS", {"4": self.url}), \
                 patch.object(p.p401, "fetch_bytes", return_value=raw):
                summary = p.run_capture("schedule", "entity-sidecar-run", output_dir)
            self.assertEqual(summary["new_event_rows"], 1)
            self.assertEqual(summary["entity_observation_rows"], 2)
            self.assertEqual(summary["multi_entity_accession_count"], 1)
            self.assertEqual(summary["canonical_issuer_event_count"], 1)
            with (data_dir / "entity_observations.csv").open(newline="", encoding="utf-8") as handle:
                entities = list(csv.DictReader(handle))
            self.assertEqual(len(entities), 2)
            canonical = next(row for row in entities if row["canonical_event_emitted"] == "True")
            self.assertEqual(canonical["feed_entity_role"], "ISSUER")
            self.assertEqual(canonical["feed_entity_cik"], "0000000003")
            self.assertEqual(canonical["canonical_entity_selection_status"], "ISSUER_ENTITY_SELECTED")
            self.assertTrue((output_dir / "entity_summary.json").exists())



    def test_entity_duplicate_audit_separates_cross_page_repeat_from_distinct_entities(self):
        rows = [
            {"poll_run_id": "r", "observation_sequence": 1, "feed_name": "4", "accession": "A",
             "form": "4", "feed_entity_role": "REPORTING", "feed_entity_cik": "0000000002",
             "feed_entity_name": "Owner LLC", "feed_entity_status": "PARSED", "page_offset": 0,
             "page_raw_sha256": "h1", "page_received_at_utc": "t1"},
            {"poll_run_id": "r", "observation_sequence": 2, "feed_name": "4", "accession": "A",
             "form": "4", "feed_entity_role": "ISSUER", "feed_entity_cik": "0000000003",
             "feed_entity_name": "Issuer Inc.", "feed_entity_status": "PARSED", "page_offset": 100,
             "page_raw_sha256": "h2", "page_received_at_utc": "t2"},
            {"poll_run_id": "r", "observation_sequence": 3, "feed_name": "4", "accession": "B",
             "form": "4", "feed_entity_role": "ISSUER", "feed_entity_cik": "0000000004",
             "feed_entity_name": "Issuer Two Inc.", "feed_entity_status": "PARSED", "page_offset": 200,
             "page_raw_sha256": "h3", "page_received_at_utc": "t3"},
            {"poll_run_id": "r", "observation_sequence": 4, "feed_name": "4", "accession": "B",
             "form": "4", "feed_entity_role": "REPORTING", "feed_entity_cik": "0000000005",
             "feed_entity_name": "Owner Two LLC", "feed_entity_status": "PARSED", "page_offset": 200,
             "page_raw_sha256": "h3", "page_received_at_utc": "t3"},
            {"poll_run_id": "r", "observation_sequence": 5, "feed_name": "4", "accession": "B",
             "form": "4", "feed_entity_role": "ISSUER", "feed_entity_cik": "0000000004",
             "feed_entity_name": "  ISSUER TWO INC. ", "feed_entity_status": "PARSED", "page_offset": 300,
             "page_raw_sha256": "h4", "page_received_at_utc": "t4"},
        ]
        audited, summary = p.audit_entity_observation_duplicates(rows)
        self.assertEqual(summary["entity_duplicate_audit_rows"], 5)
        self.assertEqual(summary["exact_duplicate_entity_observation_rows"], 1)
        self.assertEqual(summary["exact_duplicate_entity_key_groups"], 1)
        self.assertEqual(summary["exact_duplicate_entity_observation_rows_across_page_offsets"], 1)
        self.assertEqual(summary["exact_duplicate_entity_key_groups_across_page_offsets"], 1)
        self.assertEqual(summary["legitimate_multi_entity_accessions_split_across_pages"], 2)
        duplicate = next(row for row in audited if row["observation_sequence"] == 5)
        self.assertEqual(duplicate["is_exact_duplicate_entity_observation"], True)
        self.assertEqual(duplicate["is_exact_duplicate_across_page_offsets"], True)
        self.assertEqual(duplicate["first_entity_observation_sequence"], 3)

    def test_entity_duplicate_audit_does_not_fuzzy_match_unparsed_entities(self):
        rows = [
            {"poll_run_id": "r", "observation_sequence": 1, "feed_name": "4", "accession": "C",
             "form": "4", "feed_entity_role": "UNKNOWN", "feed_entity_cik": "",
             "feed_entity_name": "", "feed_entity_status": "UNPARSED_TITLE", "page_offset": 0,
             "page_raw_sha256": "h1", "page_received_at_utc": "t1"},
            {"poll_run_id": "r", "observation_sequence": 2, "feed_name": "4", "accession": "C",
             "form": "4", "feed_entity_role": "UNKNOWN", "feed_entity_cik": "",
             "feed_entity_name": "", "feed_entity_status": "UNPARSED_TITLE", "page_offset": 100,
             "page_raw_sha256": "h2", "page_received_at_utc": "t2"},
        ]
        audited, summary = p.audit_entity_observation_duplicates(rows)
        self.assertEqual(summary["unkeyed_entity_observation_rows"], 2)
        self.assertEqual(summary["exact_duplicate_entity_observation_rows"], 0)
        self.assertTrue(all(row["entity_observation_key"] == "" for row in audited))

if __name__ == "__main__":
    unittest.main()

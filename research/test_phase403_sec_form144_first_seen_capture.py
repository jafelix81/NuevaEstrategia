import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from research import phase403_sec_form144_first_seen_capture as p403


SAMPLE_144 = """<?xml version="1.0" encoding="UTF-8"?>
<edgarSubmission>
  <submissionType>144</submissionType>
  <filerCredentials><cik>9999999999</cik></filerCredentials>
  <issuerInfo><issuerCik>0000123456</issuerCik><issuerName>Candidate Corp</issuerName></issuerInfo>
  <securitiesInformation><nameOfPersonForWhoseAccountTheSecuritiesAreToBeSold>Jane Seller</nameOfPersonForWhoseAccountTheSecuritiesAreToBeSold></securitiesInformation>
</edgarSubmission>"""

SAMPLE_ATOM = """<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>Latest Filings</title>
  <entry>
    <id>urn:tag:sec.gov,2008:accession-number=000012345624000001</id>
    <title>144 - Candidate Corp (0000123456) (Issuer)</title>
    <updated>2026-11-14T18:30:00-05:00</updated>
    <link rel="alternate" href="https://www.sec.gov/Archives/edgar/data/9999999999/000012345624000001/0000123456-24-000001-index.htm" />
    <summary type="html">Form 144 filing</summary>
  </entry>
</feed>"""

SAMPLE_ATOM_144A = """<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>urn:tag:sec.gov,2008:accession-number=000012345624000002</id>
    <title>144/A - Candidate Corp (0000123456) (Issuer)</title>
    <updated>2026-11-14T19:00:00Z</updated>
    <link rel="alternate" href="https://www.sec.gov/Archives/edgar/data/9999999999/000012345624000002/0000123456-24-000002-index.htm" />
  </entry>
</feed>"""


class Phase403Tests(unittest.TestCase):
    def test_extract_accession_hyphenated_and_compact(self):
        self.assertEqual(p403.extract_accession("https://x/0000123456-24-000001-index.htm"),
                         "0000123456-24-000001")
        self.assertEqual(p403.extract_accession("urn:tag:sec.gov,2008:accession-number=000012345624000002"),
                         "0000123456-24-000002")

    def test_parse_atom_144_and_path_cik(self):
        rows = p403.parse_atom_feed(SAMPLE_ATOM, "144", p403.FEEDS["144"])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["accession"], "0000123456-24-000001")
        self.assertEqual(rows[0]["form"], "144")
        self.assertEqual(rows[0]["feed_path_cik"], "9999999999")
        self.assertEqual(rows[0]["feed_updated_utc"], "2026-11-14T23:30:00Z")

    def test_parse_atom_144a(self):
        rows = p403.parse_atom_feed(SAMPLE_ATOM_144A, "144A", p403.FEEDS["144A"])
        self.assertEqual(rows[0]["form"], "144/A")
        self.assertEqual(rows[0]["accession"], "0000123456-24-000002")

    def test_candidate_identity_uses_xml_issuer_not_archive_path_cik(self):
        raw = (
            "ACCEPTANCE-DATETIME: 20261114183000\n"
            "<XML>" + SAMPLE_144 + "</XML>"
        ).encode("latin-1")
        item = p403.parse_atom_feed(SAMPLE_ATOM, "144", p403.FEEDS["144"])[0]
        with patch.object(p403.p401, "fetch_bytes", return_value=raw):
            metadata = p403.fetch_document_metadata(item, {"0000123456"})
        self.assertEqual(metadata["issuer_cik"], "0000123456")
        self.assertEqual(metadata["filer_cik"], "9999999999")
        self.assertTrue(metadata["candidate_issuer_match"])
        self.assertEqual(metadata["submission_type"], "144")
        self.assertEqual(metadata["xml_status"], "retrieved")

    def test_acceptance_timestamp_is_parsed_as_eastern_then_utc(self):
        accepted_et, accepted_utc = p403.parse_acceptance_submission(
            "ACCEPTANCE-DATETIME: 20261114183000"
        )
        self.assertEqual(accepted_et, "2026-11-14 18:30:00")
        self.assertEqual(accepted_utc, "2026-11-14T23:30:00Z")

    def test_acceptance_timestamp_parses_native_edgar_sgml_element(self):
        raw = (
            b"<SEC-HEADER>\\n"
            b"<ACCEPTANCE-DATETIME>20261114183000\\n"
            b"ACCESSION NUMBER: 0000123456-26-000001\\n"
        )
        accepted_et, accepted_utc = p403.parse_acceptance_submission(raw)
        self.assertEqual(accepted_et, "2026-11-14 18:30:00")
        self.assertEqual(accepted_utc, "2026-11-14T23:30:00Z")

    def test_acceptance_timestamp_conflict_fails_closed(self):
        raw = (
            "ACCEPTANCE-DATETIME: 20261114183000\\n"
            "<ACCEPTANCE-DATETIME>20261114183100\\n"
        )
        self.assertEqual(p403.parse_acceptance_submission(raw), (None, None))

    def test_duplicate_identical_acceptance_encodings_are_unambiguous(self):
        raw = (
            "ACCEPTANCE-DATETIME: 20261114183000\\n"
            "<ACCEPTANCE-DATETIME>20261114183000\\n"
        )
        self.assertEqual(
            p403.parse_acceptance_submission(raw),
            ("2026-11-14 18:30:00", "2026-11-14T23:30:00Z"),
        )

    def test_gap_is_any_missing_previous_latest_after_pagination(self):
        entries = [{"accession": f"0000000000-26-{i:06d}"} for i in range(50)]
        self.assertTrue(p403.detect_possible_gap(entries, "9999999999-26-000001"))
        self.assertTrue(p403.detect_possible_gap(entries[:49], "9999999999-26-000001"))
        self.assertFalse(p403.detect_possible_gap(entries, entries[0]["accession"]))


    def test_acceptance_timestamp_from_filing_detail_html(self):
        raw = b"<html><div>Filing Date 2026-11-13</div><div>Accepted 2026-11-13 16:24:50</div></html>"
        accepted_et, accepted_utc, filing_date = p403.parse_acceptance_html(raw)
        self.assertEqual(accepted_et, "2026-11-13 16:24:50")
        self.assertEqual(accepted_utc, "2026-11-13T21:24:50Z")
        self.assertEqual(filing_date, "2026-11-13")

    def test_acceptance_index_reconciliation_is_separate_and_non_signal(self):
        event = {
            "accession": "0000123456-24-000001",
            "feed_path_cik": "0009999999",
            "form": "144",
            "feed_updated_utc": "2026-11-13T21:24:50Z",
            "first_seen_at_utc": "2026-11-14T20:45:08Z",
        }
        html = b"<html><div>Filing Date 2026-11-13</div><div>Accepted 2026-11-13 16:24:50</div></html>"
        with patch.object(p403.p401, "fetch_bytes", return_value=html):
            row = p403.fetch_acceptance_from_index(event, "123")
        self.assertEqual(row["acceptance_utc"], "2026-11-13T21:24:50Z")
        self.assertEqual(row["feed_updated_minus_acceptance_seconds"], 0)
        self.assertFalse(row["signal_eligible"])
        self.assertFalse(row["public_availability_certified"])

    def test_sec_atom_page_size_and_fail_closed_page_limit(self):
        self.assertEqual(p403.MAX_FEED_ENTRIES, 100)
        self.assertEqual(p403.MAX_FEED_PAGES, 10)
        entries = [{"accession": f"0000000000-26-{i:06d}"} for i in range(50)]
        self.assertTrue(p403.detect_possible_gap(entries, "9999999999-26-000001"))
        self.assertTrue(p403.detect_possible_gap(entries[:49], "9999999999-26-000001"))

    def test_interval_lower_bound_is_suppressed_after_gap(self):
        prior = "2026-11-14T18:00:00Z"
        self.assertEqual(
            p403.interval_policy(prior, False, False),
            (prior, "BOUNDED_BY_SUCCESSIVE_SUCCESSFUL_POLLS")
        )
        self.assertEqual(
            p403.interval_policy(prior, True, False),
            (None, "PREVIOUS_POLL_GAP_INTERVAL_UNBOUNDED")
        )
        self.assertEqual(
            p403.interval_policy(prior, False, True),
            (None, "POSSIBLE_FEED_WINDOW_GAP")
        )

    def test_manifest_has_frozen_290_cik_candidate_set(self):
        ciks, manifest = p403.load_candidate_manifest()
        self.assertEqual(len(ciks), 290)
        self.assertEqual(manifest["source_artifact_sha256"], p403.EXPECTED_SOURCE_ARTIFACT_SHA256)

    def test_events_append_without_replacing_prior_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "events.csv"
            p403.append_events(path, [{"accession": "0000123456-24-000001", "form": "144"}])
            p403.append_events(path, [{"accession": "0000123456-24-000002", "form": "144/A"}])
            import csv
            with path.open("r", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual([x["accession"] for x in rows],
                             ["0000123456-24-000001", "0000123456-24-000002"])

    def test_phase403_never_authorizes_a_signal_or_intraday_use(self):
        candidate_ciks = {"0000123456"}
        item = p403.parse_atom_feed(SAMPLE_ATOM, "144", p403.FEEDS["144"])[0]
        metadata = {
            "submission_acceptance_utc": "2026-11-14T23:30:00Z",
            "submission_acceptance_et": "2026-11-14 18:30:00",
            "submission_type": "144",
            "issuer_cik": "0000123456",
            "issuer_name": "Candidate Corp",
            "filer_cik": "9999999999",
            "seller_name": "Jane Seller",
            "previous_accession": None,
            "remarks": "",
            "xml_status": "retrieved",
            "xml_source": "test",
            "xml_sha256": "abc",
            "submission_txt_status": "retrieved",
            "candidate_issuer_match": True,
        }
        manifest = {"candidate_ciks": list(candidate_ciks),
                    "source_artifact_sha256": p403.EXPECTED_SOURCE_ARTIFACT_SHA256}
        row = p403.build_event(
            item, metadata, "2026-11-14T23:00:00Z", "2026-11-14T23:31:00Z",
            "2026-11-14T23:00:00Z", "BOUNDED_BY_SUCCESSIVE_SUCCESSFUL_POLLS",
            "123", "schedule", manifest
        )
        self.assertFalse(row["signal_eligible"])
        self.assertFalse(row["same_day_intraday_use_authorized"])
        self.assertFalse(row["public_availability_certified"])
        self.assertTrue(row["research_observation_eligible"])
        self.assertTrue(row["first_seen_is_upper_bound_not_exact_receipt"])



    def test_cross_feed_provenance_and_observation_ledger_preserve_overlap(self):
        snapshots = {
            "144": {
                "url": "https://example.test/144",
                "raw_sha256": "hash144",
                "received_at_utc": "2026-11-14T21:17:01Z",
                "entries": [{
                    "accession": "0000123456-26-000001",
                    "form": "144/A",
                    "feed_updated_raw": "2026-11-14T16:00:00-05:00",
                    "feed_updated_utc": "2026-11-14T21:00:00Z",
                    "feed_link": "https://www.sec.gov/Archives/edgar/data/1/x",
                    "feed_path_cik": "0000000001",
                }],
            },
            "144A": {
                "url": "https://example.test/144A",
                "raw_sha256": "hash144a",
                "received_at_utc": "2026-11-14T21:17:03Z",
                "entries": [{
                    "accession": "0000123456-26-000001",
                    "form": "144/A",
                    "feed_updated_raw": "2026-11-14T16:00:00-05:00",
                    "feed_updated_utc": "2026-11-14T21:00:00Z",
                    "feed_link": "https://www.sec.gov/Archives/edgar/data/1/x",
                    "feed_path_cik": "0000000001",
                }],
            },
        }
        self.assertEqual(
            p403.feed_names_by_accession(snapshots)["0000123456-26-000001"],
            ["144", "144A"],
        )
        rows = p403.build_feed_observation_rows(snapshots, "run-404")
        self.assertEqual(len(rows), 2)
        self.assertEqual({row["feed_name"] for row in rows}, {"144", "144A"})

    def test_feed_observation_append_is_idempotent_per_run_feed_accession(self):
        snapshots = {
            "144": {
                "url": "https://example.test/144",
                "raw_sha256": "hash144",
                "received_at_utc": "2026-11-14T21:17:01Z",
                "entries": [{
                    "accession": "0000123456-26-000001",
                    "form": "144",
                    "feed_updated_raw": "2026-11-14T16:00:00-05:00",
                    "feed_updated_utc": "2026-11-14T21:00:00Z",
                    "feed_link": "https://www.sec.gov/Archives/edgar/data/1/x",
                    "feed_path_cik": "0000000001",
                }],
            },
        }
        rows = p403.build_feed_observation_rows(snapshots, "run-404")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "feed_observations.csv"
            self.assertEqual(p403.append_feed_observations(path, rows), 1)
            self.assertEqual(p403.append_feed_observations(path, rows), 0)
            import csv
            with path.open("r", encoding="utf-8") as handle:
                stored = list(csv.DictReader(handle))
            self.assertEqual(len(stored), 1)
            self.assertEqual(stored[0]["feed_name"], "144")


    def test_fetch_all_feeds_keeps_success_when_other_feed_times_out(self):
        def fake_fetch(url, **kwargs):
            if url.startswith(p403.FEEDS["144"] + "&start=0"):
                return SAMPLE_ATOM.encode("utf-8")
            raise TimeoutError("temporary SEC 144/A timeout")

        with patch.object(p403.p401, "fetch_bytes", side_effect=fake_fetch), \
             patch.object(p403, "now_utc", return_value="2026-11-16T23:00:00Z"):
            snapshots, errors = p403.fetch_all_feeds()

        self.assertEqual(set(snapshots), {"144"})
        self.assertEqual(len(snapshots["144"]["entries"]), 1)
        self.assertEqual(set(errors), {"144A"})
        self.assertEqual(errors["144A"]["error_type"], "TimeoutError")
        self.assertIn("temporary SEC 144/A timeout", errors["144A"]["error"])

    def test_partial_poll_persists_successful_feed_without_advancing_failed_feed_clock(self):
        with tempfile.TemporaryDirectory() as tmp:
            previous = {
                "schema_version": 1,
                "last_successful_poll_utc": "2026-11-16T22:00:00Z",
                "last_successful_poll_mode": "schedule",
                "last_successful_poll_run_id": "previous-run",
                "poll_count": 10,
                "last_successful_poll_utc_by_feed": {
                    "144": "2026-11-16T22:00:00Z",
                    "144A": "2026-11-16T22:00:00Z",
                },
                "last_successful_poll_started_utc_by_feed": {
                    "144": "2026-11-16T21:59:00Z",
                    "144A": "2026-11-16T21:59:00Z",
                },
                "latest_accession_by_feed": {
                    "144": "0000000000-26-000001",
                    "144A": "0000000000-26-000002",
                },
                "last_poll_possible_gap_by_feed": {"144": False, "144A": False},
                "last_feed_sha256_by_feed": {"144": "old-144", "144A": "old-144a"},
                "poll_count_by_feed": {"144": 10, "144A": 10},
            }
            p403.write_json(Path(tmp) / "state.json", previous)
            item = p403.parse_atom_feed(SAMPLE_ATOM, "144", p403.FEEDS["144"])[0]
            snapshots = {
                "144": {
                    "url": p403.FEEDS["144"],
                    "raw_sha256": "new-144-hash",
                    "response_bytes": len(SAMPLE_ATOM.encode("utf-8")),
                    "received_at_utc": "2026-11-16T23:00:00Z",
                    "entries": [item],
                    "entry_count": 1,
                    "oldest_updated_utc": item["feed_updated_utc"],
                    "newest_updated_utc": item["feed_updated_utc"],
                    "previous_latest_accession_found": True,
                    "possible_feed_window_gap": False,
                    "pagination_complete": True,
                }
            }
            errors = {
                "144A": {
                    "url": p403.FEEDS["144A"],
                    "error_type": "TimeoutError",
                    "error": "read timed out after retries",
                    "response_bytes": None,
                    "raw_sha256": None,
                }
            }
            manifest = {
                "candidate_ciks": ["0000123456"],
                "source_artifact_sha256": p403.EXPECTED_SOURCE_ARTIFACT_SHA256,
            }
            metadata = {
                "submission_acceptance_utc": "2026-11-14T23:30:00Z",
                "submission_acceptance_et": "2026-11-14 18:30:00",
                "submission_type": "144",
                "issuer_cik": "0000123456",
                "issuer_name": "Candidate Corp",
                "filer_cik": "9999999999",
                "seller_name": "Jane Seller",
                "previous_accession": None,
                "remarks": "",
                "xml_status": "retrieved",
                "xml_source": "test",
                "xml_sha256": "abc",
                "submission_txt_status": "retrieved",
                "candidate_issuer_match": True,
            }
            with patch.object(p403, "load_candidate_manifest",
                              return_value=({"0000123456"}, manifest)), \
                 patch.object(p403, "fetch_all_feeds", return_value=(snapshots, errors)), \
                 patch.object(p403, "fetch_document_metadata", return_value=metadata), \
                 patch.object(p403, "fetch_acceptance_from_index", return_value=None), \
                 patch.object(p403, "now_utc", side_effect=[
                     "2026-11-16T22:59:00Z",
                     "2026-11-16T23:00:01Z",
                     "2026-11-16T23:00:02Z",
                 ]):
                summary = p403.run("schedule", Path(tmp) / "out", "partial-run-1", data_dir=tmp)

            state = p403.read_json(Path(tmp) / "state.json")
            events = p403.read_event_rows(Path(tmp) / "events.csv")
            with (Path(tmp) / "feed_observations.csv").open("r", encoding="utf-8") as handle:
                observations = list(__import__("csv").DictReader(handle))

            self.assertEqual(summary["poll_status"], "partial")
            self.assertEqual(summary["successful_feeds"], ["144"])
            self.assertEqual(summary["failed_feeds"], ["144A"])
            self.assertFalse(summary["cross_feed_provenance_complete"])
            self.assertIsNone(summary["new_cross_feed_overlap_count"])
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0]["accession"], "0000123456-24-000001")
            self.assertEqual(events[0]["capture_poll_status"], "partial")
            self.assertEqual(events[0]["cross_feed_provenance_complete"], "False")
            self.assertEqual(events[0]["feed_names"], '["144"]')
            self.assertEqual(events[0]["research_observation_eligible"], "True")
            self.assertEqual(events[0]["first_seen_interval_lower_bound_utc"], "2026-11-16T21:59:00Z")
            self.assertEqual(len(observations), 1)
            self.assertEqual(observations[0]["feed_name"], "144")
            self.assertEqual(state["last_successful_poll_utc"], "2026-11-16T22:00:00Z")
            self.assertEqual(state["last_successful_poll_run_id"], "previous-run")
            self.assertEqual(state["last_successful_poll_utc_by_feed"]["144"], "2026-11-16T23:00:00Z")
            self.assertEqual(state["last_successful_poll_utc_by_feed"]["144A"], "2026-11-16T22:00:00Z")
            self.assertEqual(state["last_successful_poll_started_utc_by_feed"]["144"], "2026-11-16T22:59:00Z")
            self.assertEqual(state["last_successful_poll_started_utc_by_feed"]["144A"], "2026-11-16T21:59:00Z")
            self.assertEqual(state["poll_count"], 11)
            self.assertEqual(state["complete_poll_count"], 10)
            self.assertEqual(state["partial_poll_count"], 1)
            self.assertEqual(state["last_poll_status"], "partial")
            self.assertEqual(state["last_poll_failed_feeds"], ["144A"])
            self.assertEqual(state["last_poll_errors"]["144A"]["error_type"], "TimeoutError")

    def test_all_feed_failure_writes_audit_summary_and_preserves_prior_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            previous = {
                "schema_version": 1,
                "last_successful_poll_utc": "2026-11-16T22:00:00Z",
                "poll_count": 10,
                "last_successful_poll_utc_by_feed": {"144": "2026-11-16T22:00:00Z"},
            }
            p403.write_json(Path(tmp) / "state.json", previous)
            manifest = {
                "candidate_ciks": ["0000123456"],
                "source_artifact_sha256": p403.EXPECTED_SOURCE_ARTIFACT_SHA256,
            }
            errors = {
                name: {"url": url, "error_type": "TimeoutError", "error": "timeout"}
                for name, url in p403.FEEDS.items()
            }
            with patch.object(p403, "load_candidate_manifest",
                              return_value=({"0000123456"}, manifest)), \
                 patch.object(p403, "fetch_all_feeds", return_value=({}, errors)), \
                 patch.object(p403, "now_utc", return_value="2026-11-16T23:00:00Z"):
                with self.assertRaisesRegex(RuntimeError, "All SEC Atom feeds failed"):
                    p403.run("schedule", Path(tmp) / "out", "failed-run-1", data_dir=tmp)

            self.assertEqual(p403.read_json(Path(tmp) / "state.json"), previous)
            self.assertFalse((Path(tmp) / "events.csv").exists())
            failed_summary = json.loads((Path(tmp) / "out" / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(failed_summary["poll_status"], "failed")
            self.assertFalse(failed_summary["state_write"])
            self.assertEqual(failed_summary["disposition"], "POLL_FAILED_ALL_FEEDS")

if __name__ == "__main__":
    unittest.main()

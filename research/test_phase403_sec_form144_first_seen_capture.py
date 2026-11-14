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

    def test_gap_requires_full_feed_and_missing_previous_latest(self):
        entries = [{"accession": f"0000000000-26-{i:06d}"} for i in range(100)]
        self.assertTrue(p403.detect_possible_gap(entries, "9999999999-26-000001"))
        self.assertFalse(p403.detect_possible_gap(entries[:99], "9999999999-26-000001"))
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

    def test_observed_feed_window_cap_is_50(self):
        self.assertEqual(p403.MAX_FEED_ENTRIES, 50)
        entries = [{"accession": f"0000000000-26-{i:06d}"} for i in range(50)]
        self.assertTrue(p403.detect_possible_gap(entries, "9999999999-26-000001"))
        self.assertFalse(p403.detect_possible_gap(entries[:49], "9999999999-26-000001"))

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


if __name__ == "__main__":
    unittest.main()

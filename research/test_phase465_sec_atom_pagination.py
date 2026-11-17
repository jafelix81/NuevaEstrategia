import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from research import phase403_sec_form144_first_seen_capture as p403


def atom(entries):
    body = []
    for accession, role in entries:
        digits = accession.replace("-", "")
        body.append(
            "<entry>"
            f"<id>urn:tag:sec.gov,2008:accession-number={digits}</id>"
            f"<title>144 - Candidate Corp (0000123456) ({role})</title>"
            "<updated>2026-11-17T20:00:00Z</updated>"
            f'<link rel="alternate" href="https://www.sec.gov/Archives/edgar/data/9999999999/{digits}/{accession}-index.htm"/>'
            "</entry>"
        )
    return ('<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom">'
            + "".join(body) + "</feed>").encode("utf-8")


def empty_atom():
    return b'<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom"></feed>'


class Phase465PaginationTests(unittest.TestCase):
    def test_raw_atom_count_precedes_accession_deduplication(self):
        duplicate = "0000000001-26-000001"
        raw = atom([(duplicate, "Reporting"), (duplicate, "Issuer")])
        self.assertEqual(p403.count_atom_entries(raw), 2)
        parsed = p403.parse_atom_feed(raw, "144", p403.FEEDS["144"])
        self.assertEqual(len(parsed), 1)

    def test_offset_advances_by_raw_rows_and_finds_prior_watermark(self):
        prior = "0000000009-26-000999"
        first = [(f"0000000001-26-{i:06d}", "Issuer") for i in range(1, 50)]
        first.append((first[0][0], "Reporting"))  # 50 raw rows, 49 unique accessions
        page0 = atom(first)
        page50 = atom([(prior, "Issuer")])
        page_a = atom([("0000000002-26-000001", "Issuer")])
        calls = []

        def fake_fetch(url, **kwargs):
            calls.append(url)
            query = parse_qs(urlparse(url).query)
            start = int(query.get("start", ["0"])[0])
            if "type=144%2FA" in url or "type=144/A" in url:
                return page_a
            if start == 0:
                return page0
            if start == 50:
                return page50
            raise AssertionError(f"unexpected offset {start}")

        with patch.object(p403.p401, "fetch_bytes", side_effect=fake_fetch), \
             patch.object(p403.time, "sleep", return_value=None):
            snapshots, errors = p403.fetch_all_feeds(
                {"144": prior}, mode="schedule"
            )

        self.assertEqual(errors, {})
        snap = snapshots["144"]
        self.assertEqual(snap["page_count"], 2)
        self.assertEqual(snap["raw_entry_count"], 51)
        self.assertEqual(snap["entry_count"], 50)
        self.assertTrue(snap["previous_latest_accession_found"])
        self.assertFalse(snap["possible_feed_window_gap"])
        self.assertTrue(snap["pagination_complete"])
        self.assertEqual([p["start"] for p in snap["pages"]], [0, 50])
        self.assertTrue(any("start=50" in url for url in calls))

        observed = p403.build_feed_observation_rows(snapshots, "run-465")
        prior_row = next(row for row in observed if row["accession"] == prior)
        self.assertIn("start=50", prior_row["feed_url"])
        self.assertEqual(prior_row["feed_raw_sha256"], snap["pages"][1]["raw_sha256"])

    def test_empty_second_page_does_not_falsely_bound_missing_watermark(self):
        prior = "0000000009-26-000999"
        page0 = atom([(f"0000000001-26-{i:06d}", "Issuer") for i in range(1, 51)])

        def fake_fetch(url, **kwargs):
            start = int(parse_qs(urlparse(url).query).get("start", ["0"])[0])
            return page0 if start == 0 else empty_atom()

        with patch.object(p403.p401, "fetch_bytes", side_effect=fake_fetch), \
             patch.object(p403.time, "sleep", return_value=None):
            snapshots, errors = p403.fetch_all_feeds({"144": prior}, mode="schedule")

        snap = snapshots["144"]
        self.assertEqual(errors, {})
        self.assertEqual(snap["pagination_stop_reason"], "empty_page")
        self.assertTrue(snap["pagination_complete"])
        self.assertTrue(snap["possible_feed_window_gap"])
        self.assertIsNone(p403.interval_policy("2026-11-17T20:00:00Z", False, True)[0])

    def test_repeated_page_hash_fails_closed(self):
        prior = "0000000009-26-000999"
        page0 = atom([(f"0000000001-26-{i:06d}", "Issuer") for i in range(1, 51)])

        def fake_fetch(url, **kwargs):
            return page0

        with patch.object(p403.p401, "fetch_bytes", side_effect=fake_fetch), \
             patch.object(p403.time, "sleep", return_value=None):
            snapshots, errors = p403.fetch_all_feeds({"144": prior}, mode="schedule")

        self.assertIn("144", errors)
        self.assertEqual(errors["144"]["error_type"], "RepeatedPageHash")
        self.assertTrue(snapshots["144"]["possible_feed_window_gap"])
        self.assertFalse(snapshots["144"]["pagination_complete"])

    def test_bootstrap_is_one_page_and_never_claims_historical_interval(self):
        page0 = atom([("0000000001-26-000001", "Issuer")])
        calls = []

        def fake_fetch(url, **kwargs):
            calls.append(url)
            return page0

        with patch.object(p403.p401, "fetch_bytes", side_effect=fake_fetch), \
             patch.object(p403.time, "sleep", return_value=None):
            snapshots, errors = p403.fetch_all_feeds({}, mode="bootstrap")

        self.assertEqual(errors, {})
        self.assertEqual(len(calls), 2)  # one page per feed
        self.assertTrue(all("start=0" in url for url in calls))
        self.assertEqual(snapshots["144"]["pagination_stop_reason"], "bootstrap_single_page")
        self.assertFalse(snapshots["144"]["possible_feed_window_gap"])


if __name__ == "__main__":
    unittest.main()

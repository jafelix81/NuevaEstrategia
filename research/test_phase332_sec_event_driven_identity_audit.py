import json
import unittest

from research.phase332_sec_event_driven_identity_audit import (
    EVENT_FORMS,
    classify_latest_symbol_evidence,
    load_submission_rows_in_window,
    select_event_filings,
)


class FakeClient:
    def __init__(self, payloads=None):
        self.payloads = payloads or {}
        self.calls = []

    def get(self, url, max_bytes=20_000_000):
        self.calls.append(url)
        if url not in self.payloads:
            return None, 404, "HTTP_404", {}
        return json.dumps(self.payloads[url]).encode(), 200, "", {}


class Phase332Tests(unittest.TestCase):
    def test_event_form_scope_includes_corporate_action_forms_not_periodic_reports(self):
        self.assertIn("8-K", EVENT_FORMS)
        self.assertIn("8-K/A", EVENT_FORMS)
        self.assertIn("25", EVENT_FORMS)
        self.assertIn("S-4", EVENT_FORMS)
        self.assertNotIn("10-K", EVENT_FORMS)
        self.assertNotIn("10-Q", EVENT_FORMS)

    def test_event_window_is_strictly_after_anchor_and_before_collision_date(self):
        rows = [
            {"form": "8-K", "filingDate": "2023-01-09", "accessionNumber": "a1", "primaryDocument": "a.htm"},
            {"form": "8-K", "filingDate": "2023-01-10", "accessionNumber": "a2", "primaryDocument": "b.htm"},
            {"form": "8-K", "filingDate": "2023-01-11", "accessionNumber": "a3", "primaryDocument": "c.htm"},
            {"form": "8-K", "filingDate": "2023-01-12", "accessionNumber": "a4", "primaryDocument": "d.htm"},
            {"form": "10-Q", "filingDate": "2023-01-10", "accessionNumber": "a5", "primaryDocument": "e.htm"},
        ]
        got = select_event_filings(rows, "2023-01-09", "2023-01-11")
        self.assertEqual([x["accessionNumber"] for x in got], ["a2"])
        self.assertTrue(all(x["filingDate"] < "2023-01-11" for x in got))

    def test_event_filings_are_deduplicated_by_accession_and_sorted_latest_first(self):
        rows = [
            {"form": "8-K", "filingDate": "2023-01-10", "accessionNumber": "a1", "primaryDocument": "a.htm"},
            {"form": "8-K/A", "filingDate": "2023-01-12", "accessionNumber": "a2", "primaryDocument": "b.htm"},
            {"form": "8-K", "filingDate": "2023-01-10", "accessionNumber": "a1", "primaryDocument": "duplicate.htm"},
        ]
        got = select_event_filings(rows, "2023-01-01", "2023-01-20")
        self.assertEqual([x["accessionNumber"] for x in got], ["a2", "a1"])
        self.assertEqual(len(got), 2)

    def test_invalid_or_non_positive_window_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid_event_window_date"):
            select_event_filings([], "not-a-date", "2023-01-01")
        with self.assertRaisesRegex(ValueError, "non_positive_event_window"):
            select_event_filings([], "2023-01-01", "2023-01-01")

    def test_latest_symbol_fact_controls_evidence_classification(self):
        events = [
            {"filing_date": "2023-01-09", "form": "8-K", "accession": "a1", "trading_symbols": ["LNDC"]},
            {"filing_date": "2023-01-10", "form": "8-K", "accession": "a2", "trading_symbols": ["LFCR"]},
        ]
        got = classify_latest_symbol_evidence(events, "LFCR")
        self.assertEqual(got["latest_symbol_evidence_status"], "MATCH_SINGLE_SYMBOL")
        self.assertEqual(got["latest_symbol_evidence_date"], "2023-01-10")
        self.assertEqual(got["latest_symbol_evidence_accession"], "a2")

    def test_latest_mismatch_is_not_overridden_by_an_older_match(self):
        events = [
            {"filing_date": "2023-01-09", "form": "8-K", "accession": "a1", "trading_symbols": ["LFCR"]},
            {"filing_date": "2023-01-10", "form": "8-K", "accession": "a2", "trading_symbols": ["LNDC"]},
        ]
        got = classify_latest_symbol_evidence(events, "LFCR")
        self.assertEqual(got["latest_symbol_evidence_status"], "MISMATCH")
        self.assertEqual(got["latest_symbol_evidence_accession"], "a2")

    def test_no_symbol_facts_remain_unknown(self):
        got = classify_latest_symbol_evidence(
            [{"filing_date": "2023-01-10", "accession": "a1", "trading_symbols": []}],
            "LFCR",
        )
        self.assertEqual(got["latest_symbol_evidence_status"], "NO_TARGET_SYMBOL_FACT")
        self.assertEqual(got["latest_symbol_evidence_symbols"], [])

    def test_multiple_symbol_fact_is_not_a_single_security_match(self):
        got = classify_latest_symbol_evidence(
            [{"filing_date": "2023-01-10", "accession": "a1", "trading_symbols": ["LFCR", "LFCRP"]}],
            "LFCR",
        )
        self.assertEqual(got["latest_symbol_evidence_status"], "MATCH_AMONG_MULTIPLE_SYMBOLS")

    def test_historical_shards_are_loaded_only_when_window_predates_recent_rows(self):
        submissions = {
            "filings": {
                "recent": {
                    "form": ["8-K"], "filingDate": ["2023-01-10"],
                    "accessionNumber": ["recent"], "primaryDocument": ["r.htm"],
                    "reportDate": [""],
                },
                "files": [
                    {"name": "old.json", "filingFrom": "2022-01-01", "filingTo": "2022-12-31"},
                    {"name": "future.json", "filingFrom": "2024-01-01", "filingTo": "2024-12-31"},
                ],
            }
        }
        old_payload = {"filings": {"recent": {
            "form": ["8-K"], "filingDate": ["2022-06-01"],
            "accessionNumber": ["old"], "primaryDocument": ["o.htm"],
            "reportDate": [""],
        }}}
        client = FakeClient({"https://data.sec.gov/submissions/old.json": old_payload})
        rows, errors = load_submission_rows_in_window(submissions, "2022-05-01", "2023-01-11", client)
        self.assertEqual({x["accessionNumber"] for x in rows}, {"recent", "old"})
        self.assertEqual(errors, [])
        self.assertEqual(client.calls, ["https://data.sec.gov/submissions/old.json"])

    def test_recent_window_sufficient_means_no_historical_shard_request(self):
        submissions = {
            "filings": {
                "recent": {
                    "form": ["8-K"], "filingDate": ["2023-01-10"],
                    "accessionNumber": ["recent"], "primaryDocument": ["r.htm"],
                    "reportDate": [""],
                },
                "files": [{"name": "old.json", "filingFrom": "2020-01-01", "filingTo": "2020-12-31"}],
            }
        }
        client = FakeClient()
        rows, errors = load_submission_rows_in_window(submissions, "2023-01-01", "2023-01-11", client)
        self.assertEqual(len(rows), 1)
        self.assertEqual(errors, [])
        self.assertEqual(client.calls, [])


if __name__ == "__main__":
    unittest.main()

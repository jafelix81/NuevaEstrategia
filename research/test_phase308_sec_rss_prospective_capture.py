import unittest

from research.phase308_sec_rss_prospective_capture import merge_capture_into_ledger


def capture(start, end, complete=True, run_id="1"):
    return {
        "run_id": run_id,
        "capture_started_at_utc": start,
        "capture_completed_at_utc": end,
        "status": "PASS_COMPLETE_CAPTURE" if complete else "PARTIAL_CAPTURE",
        "snapshot_complete": complete,
        "form_counts": {},
        "form_scans": {},
        "raw_page_hashes": {},
    }


def event(form, accession, rows=None):
    return {
        "form_type": form,
        "accession": accession,
        "issuer_ciks": ["0000000001"],
        "reporting_owner_ciks": ["0000000002"],
        "entity_rows": rows or [{
            "entity_role": "Reporting",
            "entity_cik": "0000000002",
            "title": "4 - Example (0000000002) (Reporting)",
            "link": f"https://www.sec.gov/Archives/edgar/data/1/000000000126000001/{accession}-index.htm",
            "feed_updated_raw": "2026-11-12T01:00:00-05:00",
        }],
        "feed_updated_values": ["2026-11-12T01:00:00-05:00"],
    }


class Phase308ProspectiveLedgerTests(unittest.TestCase):
    def test_new_accession_is_left_censored_without_prior_complete_capture(self):
        ledger, summary = merge_capture_into_ledger(
            {},
            capture("2026-11-12T02:00:00+00:00", "2026-11-12T02:01:00+00:00", True),
            [event("4", "0000000001-26-000001")],
        )
        record = ledger["accessions"]["4:0000000001-26-000001"]
        self.assertIsNone(record["first_observation_interval_start_utc"])
        self.assertEqual(record["first_observation_lower_bound_quality"], "left_censored_no_prior_complete_capture")
        self.assertEqual(record["seen_count"], 1)
        self.assertEqual(summary["new_accessions_this_capture"], 1)

    def test_new_accession_interval_is_bounded_by_previous_complete_capture(self):
        ledger = {
            "last_complete_capture_end_utc": "2026-11-12T01:00:00+00:00",
            "last_complete_snapshot_accessions": ["4:old"],
            "accessions": {},
            "captures": [],
        }
        ledger, summary = merge_capture_into_ledger(
            ledger,
            capture("2026-11-12T02:00:00+00:00", "2026-11-12T02:01:00+00:00", True, "2"),
            [event("4", "new")],
        )
        record = ledger["accessions"]["4:new"]
        self.assertEqual(record["first_observation_interval_start_utc"], "2026-11-12T01:00:00+00:00")
        self.assertEqual(record["first_observation_interval_end_utc"], "2026-11-12T02:00:00+00:00")
        self.assertEqual(record["first_observation_interval_width_minutes"], 60)
        self.assertEqual(summary["missing_since_previous_complete_snapshot"], 1)

    def test_existing_accession_preserves_first_observation_and_increments_seen_count(self):
        first = capture("2026-11-12T02:00:00+00:00", "2026-11-12T02:01:00+00:00", True, "1")
        ledger, _ = merge_capture_into_ledger({}, first, [event("4", "same")])
        first_seen = ledger["accessions"]["4:same"]["first_observed_at_utc"]
        second = capture("2026-11-12T03:00:00+00:00", "2026-11-12T03:01:00+00:00", True, "2")
        ledger, summary = merge_capture_into_ledger(ledger, second, [event("4", "same")])
        record = ledger["accessions"]["4:same"]
        self.assertEqual(record["first_observed_at_utc"], first_seen)
        self.assertEqual(record["seen_count"], 2)
        self.assertEqual(record["last_seen_run_id"], "2")
        self.assertEqual(summary["new_accessions_this_capture"], 0)

    def test_incomplete_capture_does_not_advance_last_complete_boundary(self):
        ledger = {
            "last_complete_capture_end_utc": "2026-11-12T01:00:00+00:00",
            "last_complete_snapshot_accessions": ["4:old"],
            "accessions": {},
            "captures": [],
        }
        ledger, summary = merge_capture_into_ledger(
            ledger,
            capture("2026-11-12T02:00:00+00:00", "2026-11-12T02:01:00+00:00", False, "2"),
            [event("4", "partial")],
        )
        self.assertEqual(ledger["last_complete_capture_end_utc"], "2026-11-12T01:00:00+00:00")
        self.assertEqual(summary["missing_since_previous_complete_snapshot"], 0)
        self.assertFalse(ledger["accessions"]["4:partial"]["last_seen_snapshot_complete"])

    def test_gap_over_90_minutes_is_flagged(self):
        ledger = {
            "last_complete_capture_end_utc": "2026-11-12T00:00:00+00:00",
            "last_complete_snapshot_accessions": [],
            "accessions": {},
            "captures": [],
        }
        ledger, summary = merge_capture_into_ledger(
            ledger,
            capture("2026-11-12T02:00:00+00:00", "2026-11-12T02:01:00+00:00", True, "3"),
            [event("4", "new")],
        )
        self.assertTrue(summary["gap_before_capture_detected"])
        self.assertEqual(summary["gap_before_capture_minutes"], 120)

    def test_form4_and_form4a_accessions_are_separate_ledger_keys(self):
        ledger, _ = merge_capture_into_ledger(
            {},
            capture("2026-11-12T02:00:00+00:00", "2026-11-12T02:01:00+00:00", True),
            [event("4", "same"), event("4/A", "same")],
        )
        self.assertIn("4:same", ledger["accessions"])
        self.assertIn("4/A:same", ledger["accessions"])
        self.assertEqual(ledger["total_unique_accessions"], 2)

    def test_entity_rows_are_unioned_without_duplicate_identity(self):
        rows = [
            {"entity_role":"Reporting","entity_cik":"0000000002","title":"4 - Example (0000000002) (Reporting)","link":"https://example/1","feed_updated_raw":"x"},
            {"entity_role":"Reporting","entity_cik":"0000000002","title":"4 - Example (0000000002) (Reporting)","link":"https://example/1","feed_updated_raw":"x"},
        ]
        ledger, _ = merge_capture_into_ledger(
            {},
            capture("2026-11-12T02:00:00+00:00", "2026-11-12T02:01:00+00:00", True),
            [event("4", "dupe", rows)],
        )
        record = ledger["accessions"]["4:dupe"]
        self.assertEqual(len(record["entity_rows_seen"]), 1)

    def test_atom_updated_is_not_promoted_to_first_public_time(self):
        ledger, _ = merge_capture_into_ledger(
            {},
            capture("2026-11-12T02:00:00+00:00", "2026-11-12T02:01:00+00:00", True),
            [event("4", "time")],
        )
        record = ledger["accessions"]["4:time"]
        self.assertNotIn("first_public_at_utc", record)
        self.assertIn("first_observation_interval_end_utc", record)


if __name__ == "__main__":
    unittest.main()

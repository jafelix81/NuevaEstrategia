import unittest

from research.phase308_sec_rss_prospective_capture import build_accession_events, compact_ledger, merge_capture_into_ledger


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


def event(form, accession, rows=None, observed_at=None, poll_started=None, page_start=None):
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
        "first_observed_at_utc": observed_at,
        "first_observation_poll_started_at_utc": poll_started,
        "first_observation_page_start": page_start,
        "first_observation_page_label": "form4" if form == "4" else "form4a",
    }


class Phase308ProspectiveLedgerTests(unittest.TestCase):
    def test_new_accession_is_left_censored_without_prior_complete_capture(self):
        ledger, summary = merge_capture_into_ledger(
            {},
            capture("2026-11-12T02:00:00+00:00", "2026-11-12T02:01:00+00:00", True),
            [event("4", "0000000001-26-000001", observed_at="2026-11-12T02:00:45+00:00")],
        )
        record = ledger["accessions"]["4:0000000001-26-000001"]
        self.assertIsNone(record["first_observation_interval_start_utc"])
        self.assertEqual(record["first_observation_interval_end_utc"], "2026-11-12T02:00:45+00:00")
        self.assertEqual(record["first_observed_at_utc"], "2026-11-12T02:00:45+00:00")
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
            [event(
                "4", "new",
                observed_at="2026-11-12T02:00:45+00:00",
                poll_started="2026-11-12T02:00:44+00:00",
                page_start=80,
            )],
        )
        record = ledger["accessions"]["4:new"]
        self.assertEqual(record["first_observation_interval_start_utc"], "2026-11-12T01:00:00+00:00")
        self.assertEqual(record["first_observation_interval_end_utc"], "2026-11-12T02:00:45+00:00")
        self.assertEqual(record["first_observation_interval_width_minutes"], 60.75)
        self.assertEqual(record["first_observation_poll_started_at_utc"], "2026-11-12T02:00:44+00:00")
        self.assertEqual(record["first_observation_page_start"], 80)
        self.assertTrue(record["first_observation_interval_valid"])
        self.assertEqual(summary["missing_since_previous_complete_snapshot"], 1)

    def test_existing_accession_preserves_first_observation_and_increments_seen_count(self):
        first = capture("2026-11-12T02:00:00+00:00", "2026-11-12T02:01:00+00:00", True, "1")
        ledger, _ = merge_capture_into_ledger(
            {}, first, [event("4", "same", observed_at="2026-11-12T02:00:30+00:00")]
        )
        first_seen = ledger["accessions"]["4:same"]["first_observed_at_utc"]
        second = capture("2026-11-12T03:00:00+00:00", "2026-11-12T03:01:00+00:00", True, "2")
        ledger, summary = merge_capture_into_ledger(
            ledger, second, [event("4", "same", observed_at="2026-11-12T03:00:30+00:00")]
        )
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
        self.assertEqual(record["entity_row_count"], 1)
        self.assertEqual(len(record["entity_row_set_sha256"]), 64)
        self.assertNotIn("entity_rows_seen", record)
        self.assertNotIn("last_entity_rows", record)

    def test_compact_ledger_removes_verbose_rows_and_stores_hashes(self):
        prior = {
            "last_complete_capture_end_utc": "2026-11-12T01:00:00+00:00",
            "last_complete_snapshot_accessions": [],
            "accessions": {
                "4:old": {
                    "form_type": "4",
                    "accession": "old",
                    "entity_rows_seen": {
                        "row": {
                            "entity_role": "Reporting",
                            "entity_cik": "0000000002",
                            "title": "4 - Example (0000000002) (Reporting)",
                            "link": "https://example/old",
                        }
                    },
                    "last_entity_rows": [],
                    "feed_updated_values_seen": ["2026-11-12T00:00:00-05:00"],
                    "seen_count": 1,
                }
            },
            "captures": [],
        }
        ledger, _ = merge_capture_into_ledger(
            prior,
            capture("2026-11-12T02:00:00+00:00", "2026-11-12T02:01:00+00:00", True),
            [event("4", "new")],
        )
        old = ledger["accessions"]["4:old"]
        self.assertEqual(old["entity_row_count"], 1)
        self.assertEqual(len(old["entity_row_set_sha256"]), 64)
        self.assertNotIn("entity_rows_seen", old)
        self.assertNotIn("last_entity_rows", old)
        self.assertNotIn("feed_updated_values_seen", old)

    def test_repo_snapshot_due_once_per_utc_day(self):
        ledger, first = merge_capture_into_ledger(
            {},
            capture("2026-11-12T02:00:00+00:00", "2026-11-12T02:01:00+00:00", True, "1"),
            [event("4", "one")],
        )
        self.assertTrue(first["repo_snapshot_due"])
        ledger, second = merge_capture_into_ledger(
            ledger,
            capture("2026-11-12T03:00:00+00:00", "2026-11-12T03:01:00+00:00", True, "2"),
            [event("4", "one")],
        )
        self.assertFalse(second["repo_snapshot_due"])
        ledger, third = merge_capture_into_ledger(
            ledger,
            capture("2026-11-13T02:00:00+00:00", "2026-11-13T02:01:00+00:00", True, "3"),
            [event("4", "one")],
        )
        self.assertTrue(third["repo_snapshot_due"])

    def test_build_accession_events_uses_earliest_response_completion_and_unions_rows(self):
        accession = "0000000001-26-000001"
        issuer = {
            "title": "4 - Example Inc. (0000000001) (Issuer)",
            "link": f"https://www.sec.gov/Archives/edgar/data/1/000000000126000001/{accession}-index.htm",
            "accession_from_link": accession,
            "feed_updated_raw": "2026-11-12T01:00:00-05:00",
        }
        owner = {
            "title": "4 - Example Owner (0000000002) (Reporting)",
            "link": f"https://www.sec.gov/Archives/edgar/data/2/000000000126000001/{accession}-index.htm",
            "accession_from_link": accession,
            "feed_updated_raw": "2026-11-12T01:00:00-05:00",
        }
        pages = {
            "form4": [
                {
                    "label": "form4",
                    "start": 0,
                    "poll_started_at_utc": "2026-11-12T02:00:01+00:00",
                    "poll_completed_at_utc": "2026-11-12T02:00:02+00:00",
                    "entries": [issuer],
                },
                {
                    "label": "form4",
                    "start": 80,
                    "poll_started_at_utc": "2026-11-12T02:00:03+00:00",
                    "poll_completed_at_utc": "2026-11-12T02:00:04+00:00",
                    "entries": [owner],
                },
            ],
            "form4a": [],
        }
        events, counts = build_accession_events(pages)
        found = next(x for x in events if x["accession"] == accession)
        self.assertEqual(found["first_observed_at_utc"], "2026-11-12T02:00:02+00:00")
        self.assertEqual(found["first_observation_poll_started_at_utc"], "2026-11-12T02:00:01+00:00")
        self.assertEqual(found["first_observation_page_start"], 0)
        self.assertEqual(len(found["entity_rows"]), 2)
        self.assertEqual(counts["form4"]["unique_accessions"], 1)

    def test_invalid_event_time_before_prior_complete_boundary_is_not_bounded(self):
        ledger = {
            "last_complete_capture_end_utc": "2026-11-12T02:00:00+00:00",
            "last_complete_snapshot_accessions": [],
            "accessions": {},
            "captures": [],
        }
        ledger, _ = merge_capture_into_ledger(
            ledger,
            capture("2026-11-12T02:01:00+00:00", "2026-11-12T02:02:00+00:00", True, "2"),
            [event("4", "clock-error", observed_at="2026-11-12T01:59:59+00:00")],
        )
        record = ledger["accessions"]["4:clock-error"]
        self.assertFalse(record["first_observation_interval_valid"])
        self.assertIsNone(record["first_observation_interval_width_minutes"])
        self.assertEqual(
            record["first_observation_lower_bound_quality"],
            "invalid_event_timestamp_before_previous_complete_capture",
        )

    def test_legacy_capture_start_placeholder_is_quarantined(self):
        ledger = {
            "accessions": {
                "4:legacy": {
                    "form_type": "4",
                    "accession": "legacy",
                    "first_seen_run_id": "43142830440",
                    "first_observed_at_utc": "2026-11-12T02:38:45.928105+00:00",
                    "first_observation_interval_end_utc": "2026-11-12T02:38:45.928105+00:00",
                    "first_observation_interval_start_utc": None,
                    "first_observation_interval_width_minutes": None,
                    "first_observation_lower_bound_quality": "left_censored_no_prior_complete_capture",
                }
            }
        }
        compacted = compact_ledger(ledger)
        record = compacted["accessions"]["4:legacy"]
        self.assertIsNone(record["first_observed_at_utc"])
        self.assertIsNone(record["first_observation_interval_end_utc"])
        self.assertEqual(
            record["legacy_capture_started_at_utc"],
            "2026-11-12T02:38:45.928105+00:00",
        )
        self.assertFalse(record["first_observation_interval_valid"])
        self.assertEqual(
            record["first_observation_timestamp_quality"],
            "legacy_capture_start_pre_response_not_observation",
        )


    def test_legacy_timestamp_migration_forces_durable_repo_snapshot(self):
        ledger = {
            "last_repo_snapshot_date": "2026-11-12",
            "last_complete_capture_end_utc": "2026-11-12T02:57:01+00:00",
            "last_complete_snapshot_accessions": ["4:legacy"],
            "accessions": {
                "4:legacy": {
                    "form_type": "4",
                    "accession": "legacy",
                    "first_seen_run_id": "43142830440",
                    "first_observed_at_utc": None,
                    "first_observation_interval_end_utc": None,
                    "first_observation_interval_start_utc": None,
                    "first_observation_interval_width_minutes": None,
                    "first_observation_lower_bound_quality": "left_censored_no_prior_complete_capture",
                    "first_observation_timestamp_quality": "legacy_capture_start_pre_response_not_observation",
                    "legacy_capture_started_at_utc": "2026-11-12T02:38:45.928105+00:00",
                    "seen_count": 4,
                    "entity_row_set_sha256": "a" * 64,
                }
            },
            "captures": [],
        }
        ledger, first = merge_capture_into_ledger(
            ledger,
            capture("2026-11-12T03:00:00+00:00", "2026-11-12T03:00:30+00:00", True, "5"),
            [event("4", "legacy", observed_at="2026-11-12T03:00:10+00:00")],
        )
        self.assertTrue(first["repo_snapshot_due"])
        self.assertEqual(ledger["legacy_timestamp_migration_snapshot_date"], "2026-11-12")
        ledger, second = merge_capture_into_ledger(
            ledger,
            capture("2026-11-12T03:10:00+00:00", "2026-11-12T03:10:30+00:00", True, "6"),
            [event("4", "legacy", observed_at="2026-11-12T03:10:10+00:00")],
        )
        self.assertFalse(second["repo_snapshot_due"])


    def test_atom_updated_is_not_promoted_to_first_public_time(self):
        ledger, _ = merge_capture_into_ledger(
            {},
            capture("2026-11-12T02:00:00+00:00", "2026-11-12T02:01:00+00:00", True),
            [event("4", "time", observed_at="2026-11-12T02:00:15+00:00")],
        )
        record = ledger["accessions"]["4:time"]
        self.assertNotIn("first_public_at_utc", record)
        self.assertEqual(record["first_observation_interval_end_utc"], "2026-11-12T02:00:15+00:00")


if __name__ == "__main__":
    unittest.main()

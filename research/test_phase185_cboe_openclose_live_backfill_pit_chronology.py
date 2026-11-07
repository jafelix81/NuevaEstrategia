import copy
import json
import unittest

from research.phase185_cboe_openclose_live_backfill_pit_chronology import audit, DEFAULT_INPUT


class Phase185CboeOpenCloseChronologyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snapshot = json.loads(DEFAULT_INPUT.read_text(encoding="utf-8"))
        cls.result = audit(cls.snapshot)

    def test_phase_and_status(self):
        self.assertEqual(self.result["phase"], 185)
        self.assertEqual(self.result["status"], "BACKFILL_PRELAUNCH_RETROSPECTIVE_NO_HISTORICAL_STRICT_PIT_ADMITTED")

    def test_four_venues_and_two_intervals(self):
        self.assertEqual(self.result["venue_interval_rows"], 8)
        self.assertEqual({x["venue"] for x in self.result["rows"]}, {"C1", "C2", "BZX", "EDGX"})
        self.assertEqual({x["interval"] for x in self.result["rows"]}, {"1m", "10m"})

    def test_ten_minute_product_floor(self):
        self.assertEqual(self.result["product_not_before"]["10m"], "2020-08-03")

    def test_one_minute_product_floor(self):
        self.assertEqual(self.result["product_not_before"]["1m"], "2025-07-13")

    def test_all_eight_archives_predate_product_introduction(self):
        self.assertEqual(self.result["prelaunch_backfill_rows"], 8)
        self.assertTrue(all(x["prelaunch_archive_is_retrospective"] for x in self.result["rows"]))

    def test_c1_ten_minute_archive_extension_is_preserved(self):
        row = next(x for x in self.snapshot["venue_interval_rows"] if x["venue"] == "C1" and x["interval"] == "10m")
        self.assertEqual(row["archive_start_current_page"], "2011-01-03")
        self.assertEqual(row["archive_start_at_2020_launch_announcement"], "2019-10-01")

    def test_other_ten_minute_archive_extension_is_preserved(self):
        rows = [x for x in self.snapshot["venue_interval_rows"] if x["interval"] == "10m" and x["venue"] != "C1"]
        self.assertTrue(all(x["archive_start_current_page"] == "2019-03-01" for x in rows))
        self.assertTrue(all(x["archive_start_at_2020_launch_announcement"] == "2020-01-01" for x in rows))

    def test_one_minute_archives_precede_2025_introduction(self):
        rows = [x for x in self.snapshot["venue_interval_rows"] if x["interval"] == "1m"]
        self.assertTrue(all(x["archive_start_current_page"] < "2025-07-13" for x in rows))

    def test_one_minute_legal_floor_and_first_possible_session(self):
        rows = [x for x in self.snapshot["venue_interval_rows"] if x["interval"] == "1m"]
        self.assertTrue(all(x["operative_delay_days"] == 30 for x in rows))
        self.assertTrue(all(x["first_possible_regular_trading_session"] == "2025-07-14" for x in rows))
        self.assertTrue(all(x["actual_first_delivery_verified"] is False for x in rows))
        self.assertEqual(self.result["one_minute_first_possible_regular_session"], "2025-07-14")

    def test_one_minute_operability_mutation_fails_closed(self):
        broken = copy.deepcopy(self.snapshot)
        row = next(x for x in broken["venue_interval_rows"] if x["interval"] == "1m")
        row["operative_delay_days"] = 0
        with self.assertRaises(ValueError):
            audit(broken)

    def test_ten_minute_latency_envelope(self):
        rows = [x for x in self.snapshot["venue_interval_rows"] if x["interval"] == "10m"]
        self.assertTrue(all((x["latency_min_minutes"], x["latency_max_minutes"]) == (0, 5) for x in rows))

    def test_one_minute_latency_envelope(self):
        rows = [x for x in self.snapshot["venue_interval_rows"] if x["interval"] == "1m"]
        self.assertTrue(all((x["latency_min_minutes"], x["latency_max_minutes"]) == (2, 5) for x in rows))

    def test_all_intraday_snapshots_are_cumulative(self):
        self.assertTrue(all(x["cumulative_snapshot"] for x in self.snapshot["venue_interval_rows"]))
        self.assertFalse(self.snapshot["global_semantics"]["first_difference_is_trade_time_interval_volume"])

    def test_actual_receipt_logs_are_required(self):
        self.assertTrue(all(x["actual_first_receipt_log_required"] for x in self.snapshot["venue_interval_rows"]))
        self.assertTrue(self.snapshot["eod_delivery"]["actual_first_receipt_log_required"])

    def test_no_strict_pit_row_is_admitted(self):
        self.assertEqual(self.result["strict_pit_admitted_rows"], 0)
        self.assertTrue(all(not x["strict_pit_admitted"] for x in self.snapshot["venue_interval_rows"]))

    def test_eod_schedule_is_not_guaranteed(self):
        self.assertFalse(self.snapshot["eod_delivery"]["typical_window_is_guaranteed"])
        self.assertFalse(self.snapshot["eod_delivery"]["same_day_close_entry_allowed_from_eod_file"])

    def test_future_v18_sample_is_not_historical_receipt_evidence(self):
        sample = self.snapshot["schema_sample"]
        self.assertEqual(sample["public_sample_trade_date"], "2026-09-30")
        self.assertEqual(sample["v18_effective_date"], "2026-11-08")
        self.assertFalse(sample["sample_is_production_delivery_evidence"])
        self.assertFalse(sample["sample_is_historical_first_receipt_evidence"])

    def test_capacity_and_venue_scope_are_not_overstated(self):
        semantics = self.snapshot["global_semantics"]
        self.assertFalse(semantics["capacity_is_beneficial_owner_identity"])
        self.assertFalse(semantics["all_opra_coverage"])

    def test_controls_remain_closed(self):
        controls = self.result["controls"]
        self.assertTrue(controls["f80_frozen"])
        self.assertFalse(controls["holdout_used"])
        self.assertFalse(controls["vendor_contact"])
        self.assertFalse(controls["data_purchase"])
        self.assertFalse(controls["production_changed"])
        self.assertFalse(controls["alpha_test_authorized"])

    def test_deterministic_output(self):
        self.assertEqual(self.result, audit(copy.deepcopy(self.snapshot)))

    def test_mutated_launch_floor_fails_closed(self):
        broken = copy.deepcopy(self.snapshot)
        broken["venue_interval_rows"][0]["product_not_before"] = "2019-03-01"
        with self.assertRaises(ValueError):
            audit(broken)

    def test_strict_pit_cannot_be_enabled_without_receipts(self):
        broken = copy.deepcopy(self.snapshot)
        broken["venue_interval_rows"][0]["strict_pit_admitted"] = True
        with self.assertRaises(ValueError):
            audit(broken)

    def test_non_cumulative_semantics_fail_closed(self):
        broken = copy.deepcopy(self.snapshot)
        broken["venue_interval_rows"][0]["cumulative_snapshot"] = False
        with self.assertRaises(ValueError):
            audit(broken)


if __name__ == "__main__":
    unittest.main()

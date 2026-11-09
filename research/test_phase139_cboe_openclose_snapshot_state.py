import unittest

from research.phase139_cboe_openclose_snapshot_state import (
    SnapshotValidationError, compare_snapshots, validate_snapshot,
)


def snap(minute, received, values=None, *, mode="LIVE_FIRST_RECEIPT", sha="a",
         exchange="C1", interval=1, schema="1.8", contract_map="map-v1", rows=None):
    rows = rows if rows is not None else [{
        "series_key": "AAPL  261218C00200000",
        "values": values or {"customer_open_buy_vol": 100, "customer_open_sell_vol": 40},
    }]
    return {
        "market_date": "2026-11-05", "trading_dt": "2026-11-05",
        "exchange": exchange, "interval_minutes": interval,
        "trading_segment": 1 if exchange == "C1" else None,
        "snapshot_at_utc": f"2026-11-05T14:{minute:02d}:00Z",
        "first_received_at_utc": f"2026-11-05T14:{received:02d}:30Z",
        "capture_mode": mode, "schema_version": schema,
        "contract_map_version": contract_map, "source_file_id": f"file-{minute}",
        "raw_file_sha256": sha * 64, "rows": rows,
    }


class Phase139Tests(unittest.TestCase):
    def test_positive_reported_increment_is_not_interval_volume(self):
        result = compare_snapshots(snap(40, 41, {"x": 100}), snap(41, 42, {"x": 125}, sha="b"))
        self.assertTrue(result["strict_pit_pair"])
        self.assertEqual(result["deltas"][0]["reported_increment"], 25)
        self.assertIn("not_trade_time_interval_volume", result["economic_interpretation"])

    def test_negative_correction_is_preserved(self):
        result = compare_snapshots(snap(40, 41, {"x": 100}), snap(41, 42, {"x": 92}, sha="b"))
        self.assertEqual(result["deltas"][0]["reported_increment"], -8)
        self.assertTrue(result["deltas"][0]["is_correction"])

    def test_new_and_removed_series_are_not_zero_filled(self):
        a, b = "AAPL", "MSFT"
        old = snap(40, 41, rows=[{"series_key": a, "values": {"x": 100}},
                                 {"series_key": b, "values": {"x": 20}}])
        new = snap(41, 42, sha="b", rows=[{"series_key": a, "values": {"x": 110}},
                                          {"series_key": "NVDA", "values": {"x": 7}}])
        result = compare_snapshots(old, new)
        self.assertEqual(result["new_series_without_prior_baseline"], ["NVDA"])
        self.assertEqual(result["removed_series_without_zero_assumption"], [b])
        self.assertEqual(len(result["deltas"]), 1)

    def test_archive_backfill_is_not_pit(self):
        result = compare_snapshots(snap(40, 41, mode="ARCHIVE_BACKFILL"),
                                   snap(41, 42, mode="ARCHIVE_BACKFILL", sha="b"))
        self.assertFalse(result["strict_pit_pair"])
        self.assertEqual(result["status"], "ARCHIVE_BACKFILL_NOT_PIT")

    def test_mixed_live_and_archive_is_not_pit(self):
        result = compare_snapshots(snap(40, 41, mode="ARCHIVE_BACKFILL"),
                                   snap(41, 42, sha="b"))
        self.assertFalse(result["strict_pit_pair"])

    def test_snapshot_time_must_increase(self):
        with self.assertRaisesRegex(SnapshotValidationError, "snapshot_time_not_increasing"):
            compare_snapshots(snap(41, 42), snap(40, 43, sha="b"))

    def test_knowledge_time_must_be_monotonic(self):
        with self.assertRaisesRegex(SnapshotValidationError, "knowledge_time_not_monotonic"):
            compare_snapshots(snap(40, 43), snap(41, 42, sha="b"))

    def test_receipt_cannot_precede_snapshot(self):
        with self.assertRaisesRegex(SnapshotValidationError, "received_before_snapshot"):
            validate_snapshot(snap(40, 39))

    def test_naive_timestamp_is_rejected(self):
        bad = snap(40, 41)
        bad["snapshot_at_utc"] = "2026-11-05T14:40:00"
        with self.assertRaisesRegex(SnapshotValidationError, "timezone_required"):
            validate_snapshot(bad)

    def test_schema_version_must_match(self):
        with self.assertRaisesRegex(SnapshotValidationError, "snapshot_identity_mismatch:schema_version"):
            compare_snapshots(snap(40, 41), snap(41, 42, sha="b", schema="1.7"))

    def test_contract_map_must_match(self):
        with self.assertRaisesRegex(SnapshotValidationError, "snapshot_identity_mismatch:contract_map_version"):
            compare_snapshots(snap(40, 41), snap(41, 42, sha="b", contract_map="map-v2"))

    def test_interval_must_match(self):
        with self.assertRaisesRegex(SnapshotValidationError, "snapshot_identity_mismatch:interval_minutes"):
            compare_snapshots(snap(40, 41), snap(41, 42, sha="b", interval=10))

    def test_market_date_and_trading_date_must_match(self):
        later = snap(41, 42, sha="b")
        later["trading_dt"] = "2026-11-06"
        with self.assertRaisesRegex(SnapshotValidationError, "snapshot_identity_mismatch:trading_dt"):
            compare_snapshots(snap(40, 41), later)

    def test_c1_segment_is_identity(self):
        later = snap(41, 42, sha="b")
        later["trading_segment"] = 2
        with self.assertRaisesRegex(SnapshotValidationError, "snapshot_identity_mismatch:trading_segment"):
            compare_snapshots(snap(40, 41), later)

    def test_c1_segment_rejects_float(self):
        bad = snap(40, 41)
        bad["trading_segment"] = 1.0
        with self.assertRaisesRegex(SnapshotValidationError, "c1_trading_segment_must_be_1_or_2"):
            validate_snapshot(bad)

    def test_non_c1_segment_must_be_null(self):
        bad = snap(40, 41, exchange="BZX")
        bad["trading_segment"] = 1
        with self.assertRaisesRegex(SnapshotValidationError, "non_c1_trading_segment_must_be_null"):
            validate_snapshot(bad)

    def test_ten_minute_non_c1_with_null_segment_is_valid(self):
        result = validate_snapshot(snap(40, 41, exchange="BZX", interval=10, schema="1.7"))
        self.assertEqual(result["interval_minutes"], 10)
        self.assertIsNone(result["trading_segment"])

    def test_same_cutoff_new_hash_is_revision_not_increment(self):
        result = compare_snapshots(snap(40, 41), snap(40, 42, sha="b"))
        self.assertEqual(result["status"], "SAME_CUTOFF_REVISION")
        self.assertEqual(result["deltas"], [])

    def test_same_cutoff_same_hash_is_duplicate(self):
        self.assertEqual(compare_snapshots(snap(40, 41), snap(40, 42))["status"],
                         "DUPLICATE_SNAPSHOT")

    def test_duplicate_series_key_is_rejected(self):
        bad = snap(40, 41, rows=[{"series_key": "AAPL", "values": {"x": 1}},
                                {"series_key": "AAPL", "values": {"x": 2}}])
        with self.assertRaisesRegex(SnapshotValidationError, "duplicate_series_key"):
            validate_snapshot(bad)

    def test_missing_metric_is_counted_not_filled(self):
        result = compare_snapshots(
            snap(40, 41, {"x": 100, "y": 30}),
            snap(41, 42, {"x": 110}, sha="b"),
        )
        self.assertEqual(result["missing_metric_pairs"], 1)
        self.assertEqual(len(result["deltas"]), 1)

    def test_invalid_cumulative_values_are_rejected(self):
        for value in (-1, 1.5, True):
            with self.subTest(value=value), self.assertRaises(SnapshotValidationError):
                validate_snapshot(snap(40, 41, {"x": value}))

    def test_raw_hash_must_be_sha256(self):
        bad = snap(40, 41)
        bad["raw_file_sha256"] = "not-a-hash"
        with self.assertRaisesRegex(SnapshotValidationError, "raw_file_sha256_invalid"):
            validate_snapshot(bad)


if __name__ == "__main__":
    unittest.main()

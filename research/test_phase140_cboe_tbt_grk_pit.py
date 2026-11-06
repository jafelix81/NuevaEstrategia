import unittest
import pandas as pd

from research.phase140_cboe_tbt_grk_pit import (
    build_formatted_symbol, classify_tbt_row, open_close_coverage, safe_grk_join,
)


class Phase140Tests(unittest.TestCase):
    def base_frames(self):
        tbt = pd.DataFrame([
            {"trading_dt":"2025-03-28","formatted_symbol":"AAPL250328C200","price":1.0,"transact_time":"2025-03-28 09:30:00","size":1},
            {"trading_dt":"2025-03-28","formatted_symbol":"MSFT250328C300","price":2.0,"transact_time":"2025-03-28 09:30:30","size":2},
            {"trading_dt":"2025-03-28","formatted_symbol":"AAPL250328C200","price":1.0,"transact_time":"2025-03-28 09:31:00","size":3},
        ])
        grk = pd.DataFrame([
            {"trading_dt":"2025-03-28","formatted_symbol":"AAPL250328C200","price":1.0,"transact_time":"2025-03-28 09:29:59","delta":0.5},
            {"trading_dt":"2025-03-28","formatted_symbol":"AAPL250328C200","price":1.0,"transact_time":"2025-03-28 09:30:02","delta":0.55},
            {"trading_dt":"2025-03-28","formatted_symbol":"AAPL250328C200","price":1.0,"transact_time":"2025-03-28 09:31:01","delta":0.6},
            {"trading_dt":"2025-03-28","formatted_symbol":"MSFT250328C300","price":2.0,"transact_time":"2025-03-28 09:30:31","delta":0.7},
        ])
        return tbt, grk

    def test_side_t_is_not_buy_or_sell(self):
        result = classify_tbt_row({"side":"T","open_close":""})
        self.assertIsNone(result["side"])
        self.assertEqual(result["side_status"], "UNCLASSIFIED")

    def test_blank_open_close_is_not_imputed(self):
        result = classify_tbt_row({"side":"B","open_close":" "})
        self.assertIsNone(result["open_close"])
        self.assertEqual(result["open_close_status"], "UNCLASSIFIED")

    def test_valid_flags_are_preserved(self):
        result = classify_tbt_row({"side":"s","open_close":"o","capacity":"Customer"})
        self.assertEqual(result["side"], "S")
        self.assertEqual(result["open_close"], "O")
        self.assertEqual(result["capacity"], "Customer")

    def test_open_close_coverage_is_capacity_specific(self):
        rows = [
            {"capacity":"MarketMaker","open_close":""},
            {"capacity":"MarketMaker","open_close":"O"},
            {"capacity":"Customer","open_close":"C"},
        ]
        result = open_close_coverage(rows)
        self.assertAlmostEqual(result["MarketMaker"]["unclassified_rate"], 0.5)
        self.assertEqual(result["Customer"]["unclassified"], 0)

    def test_formatted_symbol_integer_strike(self):
        row = {"osi_root":"SPXW","expire_date":"2024-08-16","call_put_flag":"P","strike_price":"5405.000"}
        self.assertEqual(build_formatted_symbol(row), "SPXW240816P5405")

    def test_formatted_symbol_decimal_strike(self):
        row = {"osi_root":"SPXW","expire_date":"2024-08-16","call_put_flag":"C","strike_price":"5405.5"}
        self.assertEqual(build_formatted_symbol(row), "SPXW240816C5405.5")

    def test_vendor_group_first_sort_is_not_globally_monotonic(self):
        tbt, _ = self.base_frames()
        vendor_style = tbt.sort_values(["formatted_symbol", "price", "trading_dt", "transact_time"])
        self.assertFalse(pd.to_datetime(vendor_style["transact_time"]).is_monotonic_increasing)

    def test_backward_join_is_globally_sorted_and_never_future(self):
        tbt, grk = self.base_frames()
        joined, report = safe_grk_join(tbt, grk, direction="backward", tolerance_seconds=5)
        self.assertTrue(report["event_time_causal"])
        self.assertEqual(report["use_class"], "PRE_OR_AT_TRADE")
        matched = joined[joined["_grk_time"].notna()]
        self.assertTrue((matched["grk_lag_seconds"] <= 0).all())
        self.assertEqual(report["strict_pit_eligible"], False)

    def test_forward_join_is_explicitly_post_trade_only(self):
        tbt, grk = self.base_frames()
        joined, report = safe_grk_join(tbt, grk, direction="forward", tolerance_seconds=5)
        self.assertFalse(report["event_time_causal"])
        self.assertEqual(report["use_class"], "POST_TRADE_ATTRIBUTION_ONLY")
        matched = joined[joined["_grk_time"].notna()]
        self.assertTrue((matched["grk_lag_seconds"] >= 0).all())

    def test_join_keeps_unmatched_tbt_rows(self):
        tbt, grk = self.base_frames()
        grk = grk.iloc[:1].copy()
        joined, report = safe_grk_join(tbt, grk, direction="backward", tolerance_seconds=1)
        self.assertEqual(len(joined), len(tbt))
        self.assertGreater(report["unmatched_rows"], 0)

    def test_join_does_not_cross_contract_keys(self):
        tbt, grk = self.base_frames()
        grk = grk[grk["formatted_symbol"] == "MSFT250328C300"].copy()
        joined, report = safe_grk_join(tbt.iloc[[0]], grk, direction="backward", tolerance_seconds=5)
        self.assertTrue(joined["_grk_time"].isna().all())
        self.assertEqual(report["matched_rows"], 0)

    def test_forward_match_within_tolerance(self):
        tbt, grk = self.base_frames()
        joined, report = safe_grk_join(tbt.iloc[[0]], grk, direction="forward", tolerance_seconds=5)
        self.assertEqual(report["matched_rows"], 1)
        self.assertAlmostEqual(joined.iloc[0]["grk_lag_seconds"], 2.0)

    def test_invalid_direction_rejected(self):
        tbt, grk = self.base_frames()
        with self.assertRaisesRegex(ValueError, "direction_must_be_backward_or_forward"):
            safe_grk_join(tbt, grk, direction="nearest")

    def test_naive_timestamps_not_strict_pit(self):
        tbt, grk = self.base_frames()
        _, report = safe_grk_join(tbt, grk, direction="backward")
        self.assertFalse(report["timezone_verified"])
        self.assertFalse(report["strict_pit_eligible"])

    def test_timezone_awareness_mismatch_rejected(self):
        tbt, grk = self.base_frames()
        grk["transact_time"] = pd.to_datetime(grk["transact_time"], utc=True)
        with self.assertRaisesRegex(ValueError, "timezone_awareness_mismatch"):
            safe_grk_join(tbt, grk, direction="backward")


if __name__ == "__main__":
    unittest.main()

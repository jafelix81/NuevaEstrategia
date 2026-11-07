import json
import unittest
from pathlib import Path

from phase186_nasdaq_trade_outline_pit_feasibility_audit import audit


DATA = json.loads(Path(__file__).with_name(
    "phase186_nasdaq_trade_outline_pit_feasibility_audit.json"
).read_text(encoding="utf-8"))


class Phase186NasdaqTradeOutlineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.summary = audit(DATA)
        cls.nasdaq = DATA["nasdaq_trade_outline"]
        cls.venues = {x["venue"]: x for x in cls.nasdaq["venues"]}

    def test_phase_and_status(self):
        self.assertEqual(self.summary["phase"], 186)
        self.assertIn("NOT_PIT_ADMITTED", self.summary["status"])

    def test_six_venues(self):
        self.assertEqual(set(self.venues), {"PHLX", "ISE", "NOM", "GEMX", "MRX", "NTX"})

    def test_phlx_archive_precedes_live_floor(self):
        self.assertEqual(self.venues["PHLX"]["archive_start"]["intraday"], "2009-01")
        self.assertEqual(self.venues["PHLX"]["live_product_floor"]["intraday"], "2010-09-01")

    def test_ise_eod_and_intraday_archives_are_distinct(self):
        self.assertEqual(self.venues["ISE"]["archive_start"]["eod"], "2006-01")
        self.assertEqual(self.venues["ISE"]["archive_start"]["intraday"], "2009-10")
        self.assertEqual(self.venues["ISE"]["live_product_floor"]["intraday"], "2010-01-04")

    def test_noto_operative_lower_bound(self):
        self.assertEqual(self.venues["NOM"]["live_product_floor"]["intraday"], "2011-11-11")
        self.assertFalse(self.venues["NOM"]["first_receipt_verified"])

    def test_gemx_first_live_date_remains_unknown(self):
        self.assertIsNone(self.venues["GEMX"]["live_product_floor"]["intraday"])
        self.assertEqual(self.venues["GEMX"]["archive_start"]["intraday"], "2013-08")

    def test_mrx_archive_is_prelaunch_backfill(self):
        self.assertEqual(self.venues["MRX"]["archive_start"]["intraday"], "2017-09")
        self.assertEqual(self.venues["MRX"]["live_product_floor"]["intraday"], "2024-09-03")

    def test_ntx_archive_is_prelaunch_backfill(self):
        self.assertEqual(self.venues["NTX"]["archive_start"]["intraday"], "2014-09")
        self.assertEqual(self.venues["NTX"]["live_product_floor"]["intraday"], "2024-09-03")

    def test_no_venue_is_strict_pit_admitted(self):
        self.assertEqual(self.summary["strict_pit_admitted_venues"], 0)
        self.assertTrue(all(not x["strict_pit_admitted"] for x in self.venues.values()))

    def test_routed_away_orders_are_unflagged(self):
        sem = self.nasdaq["semantics"]
        self.assertTrue(sem["routed_orders_away_included"])
        self.assertFalse(sem["routed_away_flag_available"])

    def test_cross_venue_aggregation_is_blocked(self):
        self.assertFalse(self.summary["cross_venue_aggregation_authorized"])

    def test_missing_rows_are_not_zero(self):
        self.assertFalse(self.nasdaq["semantics"]["no_trade_row_means_zero"])

    def test_cumulative_snapshots_are_mutable(self):
        sem = self.nasdaq["semantics"]
        self.assertTrue(self.nasdaq["delivery"]["cumulative_snapshots"])
        self.assertTrue(sem["volume_can_decrease_after_corrections"])
        self.assertTrue(sem["rows_can_disappear_after_full_cancellation"])

    def test_market_maker_open_close_exception(self):
        self.assertEqual(
            set(self.nasdaq["semantics"]["market_maker_open_close_not_required_for"]),
            {"PHOTO", "NOTO", "MRX", "TEXAS"}
        )

    def test_ise_gemx_schema_cutover(self):
        sem = self.nasdaq["semantics"]
        self.assertEqual(sem["ise_gemx_schema_cutover"], "2026-03-04")
        self.assertEqual(sem["old_ise_gemx_codes_decommissioned_after"], "2026-06-02")
        self.assertTrue(sem["ise_gemx_pre_cutover_total_industry_volume_double_count"])

    def test_current_delivery_sla_is_not_backdated(self):
        delivery = self.nasdaq["delivery"]
        self.assertEqual(delivery["current_sla_minutes"], 2)
        self.assertEqual(delivery["historical_sec_examples_phlx_noto_sla_minutes"], 5)

    def test_ntx_one_minute_snapshot_threshold(self):
        ntx = DATA["ntx_one_minute_snapshots"]
        self.assertEqual(ntx["minimum_trades"], 2)
        self.assertEqual(ntx["minimum_origin_types"], 3)
        self.assertTrue(ntx["remaining_activity_reported_at_interval_end"])

    def test_ntx_one_minute_is_not_directional_trade_flow(self):
        ntx = DATA["ntx_one_minute_snapshots"]
        self.assertFalse(ntx["trade_count_disclosed"])
        self.assertFalse(ntx["buy_sell_side_disclosed"])
        self.assertFalse(ntx["real_time_feed"])

    def test_ntx_implementation_not_verified(self):
        ntx = DATA["ntx_one_minute_snapshots"]
        self.assertEqual(ntx["operative_not_before"], "2026-09-10")
        self.assertEqual(ntx["implementation_notice_deadline"], "2026-10-10")
        self.assertFalse(ntx["implementation_notice_located"])
        self.assertFalse(ntx["actual_first_delivery_verified"])

    def test_cboe_one_minute_operative_floor_corrected(self):
        cboe = DATA["cboe_one_minute_operability_correction"]
        self.assertEqual(cboe["filing_date"], "2025-06-13")
        self.assertEqual(cboe["legal_operative_not_before"], "2025-07-13")
        self.assertEqual(cboe["first_possible_regular_trading_session"], "2025-07-14")
        self.assertFalse(cboe["actual_first_delivery_verified"])

    def test_published_cost_totals(self):
        costs = self.nasdaq["costs_2026_usd"]
        self.assertEqual(costs["monthly_intraday_all_six"], 12000)
        self.assertEqual(costs["monthly_eod_all_six"], 4350)
        self.assertEqual(costs["monthly_both_all_six_using_ise_combined_subscription"], 12600)
        self.assertEqual(costs["history_36m_intraday_discount_current_subscribers"], 57000)
        self.assertEqual(costs["history_36m_intraday_ad_hoc_without_subscription"], 171000)

    def test_no_purchase_no_holdout_no_production_change(self):
        decisions = DATA["decisions"]
        self.assertFalse(decisions["data_purchase"])
        self.assertFalse(decisions["holdout_used"])
        self.assertFalse(decisions["production_changed"])
        self.assertTrue(decisions["f80_frozen"])

    def test_no_alpha_test_authorized(self):
        self.assertFalse(self.summary["alpha_test_authorized"])


if __name__ == "__main__":
    unittest.main()

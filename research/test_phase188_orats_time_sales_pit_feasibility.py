import unittest

from research.phase188_orats_time_sales_pit_feasibility import build_audit


class Phase188OratsTimeSalesTests(unittest.TestCase):
    def setUp(self):
        self.audit = build_audit()

    def test_history_start_is_documented_backfill_not_pit(self):
        self.assertEqual(self.audit["documented_history"]["start_date"], "2022-09-09")
        self.assertTrue(self.audit["documented_history"]["historical_backfill_start_is_not_proof_of_live_availability"])
        self.assertFalse(self.audit["pit_and_universe_gates"]["first_live_product_availability_date_verified"])

    def test_reference_universe_is_not_closed_universe(self):
        budget = self.audit["reference_universe_budget"]
        self.assertEqual(budget["symbols"], 335)
        self.assertIn("not_a_closed_universe", budget["status"])

    def test_daily_full_universe_request_budget(self):
        budget = self.audit["reference_universe_budget"]
        self.assertEqual(budget["requests_per_full_universe_day"], 335)
        self.assertEqual(budget["full_universe_sweep_minutes_at_rate_limit"], 33.5)

    def test_annual_and_history_request_estimates(self):
        budget = self.audit["reference_universe_budget"]
        self.assertEqual(budget["requests_per_year_estimate"], 84_420)
        self.assertEqual(budget["history_requests_estimate"], 351_324)

    def test_rate_limit_backfill_duration(self):
        budget = self.audit["reference_universe_budget"]
        self.assertAlmostEqual(budget["history_backfill_rate_limit_days_continuous"], 24.4, places=1)

    def test_monthly_quota_duration(self):
        budget = self.audit["reference_universe_budget"]
        self.assertEqual(budget["history_quota_months_by_cap"]["20000"], 17.57)
        self.assertEqual(budget["history_quota_months_by_cap"]["100000"], 3.51)
        self.assertEqual(budget["history_quota_months_by_cap"]["1000000"], 0.35)

    def test_billing_months_and_costs_are_explicit(self):
        budget = self.audit["reference_universe_budget"]
        self.assertEqual(budget["billing_months_by_plan"]["delayed_plus_timesales"], 18)
        self.assertEqual(budget["billing_months_by_plan"]["live_plus_timesales"], 4)
        self.assertEqual(budget["billing_months_by_plan"]["live_intraday_plus_timesales"], 1)
        self.assertEqual(budget["estimated_subscription_cost_usd_by_plan"]["delayed_plus_timesales"], 8_964)
        self.assertEqual(budget["estimated_subscription_cost_usd_by_plan"]["live_plus_timesales"], 2_392)
        self.assertEqual(budget["estimated_subscription_cost_usd_by_plan"]["live_intraday_plus_timesales"], 898)

    def test_full_universe_live_polling_is_too_slow_for_30_second_refresh(self):
        ops = self.audit["api_operational_limits"]
        self.assertEqual(ops["requests_per_minute_per_token"], 10)
        self.assertEqual(ops["live_refresh_bucket_seconds"], 30)
        self.assertFalse(ops["full_universe_live_polling_feasible_at_30_second_refresh"])

    def test_large_response_constraints_are_recorded(self):
        ops = self.audit["api_operational_limits"]
        self.assertEqual(ops["json_response_row_cap"], 250_000)
        self.assertIsNone(ops["csv_response_row_cap"])
        self.assertEqual(ops["example_spy_full_day_rows_approx"], 1_300_000)
        self.assertEqual(ops["example_spy_full_day_json_mb_approx"], 700)

    def test_historical_and_live_enrichment_are_not_equivalent(self):
        shape = self.audit["historical_live_shape"]
        self.assertFalse(shape["live_historical_shape_parity"])
        self.assertTrue(shape["historical_greeks_enrichment"])
        self.assertEqual(shape["live_greeks_enrichment"], [])

    def test_session_cutoff_and_share_class_coverage_breaks_are_explicit(self):
        shape = self.audit["historical_live_shape"]
        self.assertEqual(shape["historical_session_end_et"], "15:59")
        self.assertEqual(shape["live_capture_end_et"], "near 16:15")
        self.assertEqual(shape["share_class_ticker_prints_start_date"], "2026-08-26")

    def test_event_index_and_cancel_handling_are_prespecified(self):
        events = self.audit["trade_print_semantics"]
        self.assertTrue(events["event_index_must_be_preserved_as_string"])
        self.assertEqual(events["event_key"], ["symbol", "eventIndex", "type"])
        self.assertTrue(events["cancel_shares_event_index_and_sequence_with_new"])
        self.assertEqual(events["volume_aggregation_type"], "NEW")
        self.assertTrue(events["cancel_rows_must_not_be_double_counted"])

    def test_aggressor_side_is_not_participant_identity(self):
        events = self.audit["trade_print_semantics"]
        self.assertTrue(events["aggressor_side_is_inferred"])
        self.assertTrue(events["aggressor_side_can_be_blank"])
        self.assertFalse(events["participant_capacity_available"])
        self.assertFalse(events["beneficial_owner_identity_available"])
        self.assertFalse(events["open_close_classification_available"])

    def test_tradeflow_independence_is_not_assumed(self):
        independence = self.audit["source_independence"]
        self.assertFalse(independence["raw_source_independence_vs_ivydb_tradeflow_verified"])

    def test_no_purchase_or_alpha_admission(self):
        self.assertFalse(self.audit["pit_and_universe_gates"]["strict_pit_admitted"])
        self.assertFalse(self.audit["pit_and_universe_gates"]["alpha_test_authorized"])
        controls = self.audit["controls"]
        self.assertFalse(controls["api_token_used"])
        self.assertFalse(controls["raw_data_downloaded"])
        self.assertFalse(controls["data_purchase"])
        self.assertTrue(controls["f80_frozen"])


if __name__ == "__main__":
    unittest.main()

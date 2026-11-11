import unittest
from decimal import Decimal

from research.phase251_cboe_multi_exchange_convention_gate import (
    aggregate_multi_exchange_underlying_rows,
    classify_exchange_date,
)


def make_row(
    exchange="C1",
    day="2018-06-15",
    underlying="ABC",
    security_type="1",
    option_symbol="ABC",
    expiry="2018-07-20",
    strike="100",
    call_put="C",
    series_type="S",
    buy=60,
    sell=30,
    total=120,
):
    row = {
        "exchange": exchange,
        "quote_date": day,
        "underlying_symbol": underlying,
        "security_type": security_type,
        "option_symbol": option_symbol,
        "expiration_date": expiry,
        "strike_price": strike,
        "call_put_flag": call_put,
        "series_type": series_type,
        "total_exchange_vol": str(total),
        "total_industry_vol": "1000",
        "open_interest": "500",
        "previous_open_interest": "490",
        "previous_close": "99.5",
        "cust_lt_100_open_buy_vol": str(buy),
        "cust_lt_100_open_sell_vol": str(sell),
        "cust_100_199_open_buy_vol": "0",
        "cust_100_199_open_sell_vol": "0",
        "cust_gt_199_open_buy_vol": "0",
        "cust_gt_199_open_sell_vol": "0",
        "cust_lt_100_close_buy_vol": "0",
        "cust_lt_100_close_sell_vol": "0",
        "cust_100_199_close_buy_vol": "0",
        "cust_100_199_close_sell_vol": "0",
        "cust_gt_199_close_buy_vol": "0",
        "cust_gt_199_close_sell_vol": "0",
        "procust_lt_100_open_buy_vol": "0",
        "procust_lt_100_open_sell_vol": "0",
        "procust_100_199_open_buy_vol": "0",
        "procust_100_199_open_sell_vol": "0",
        "procust_gt_199_open_buy_vol": "0",
        "procust_gt_199_open_sell_vol": "0",
        "procust_lt_100_close_buy_vol": "0",
        "procust_lt_100_close_sell_vol": "0",
        "procust_100_199_close_buy_vol": "0",
        "procust_100_199_close_sell_vol": "0",
        "procust_gt_199_close_buy_vol": "0",
        "procust_gt_199_close_sell_vol": "0",
        "firm_open_buy_vol": "0",
        "firm_open_sell_vol": "0",
        "firm_close_buy_vol": "0",
        "firm_close_sell_vol": "0",
        "bd_open_buy_vol": "0",
        "bd_open_sell_vol": "0",
        "bd_close_buy_vol": "0",
        "bd_close_sell_vol": "0",
    }
    return row


class Phase251MultiExchangeGateTests(unittest.TestCase):
    def test_c1_advertised_history_starts_2005(self):
        state = classify_exchange_date("C1", "2005-01-03")
        self.assertTrue(state["history_available"])
        self.assertEqual(state["history_start"], "2005-01-03")

    def test_c1_before_advertised_history_is_unavailable(self):
        state = classify_exchange_date("C1", "2004-12-31")
        self.assertFalse(state["history_available"])

    def test_c1_pre_migration_is_separate_legacy_schema(self):
        state = classify_exchange_date("C1", "2010-12-31")
        self.assertEqual(state["schema_regime"], "C1_LEGACY_CUSTOMER_FIRM_ORDER_SIZE")
        self.assertFalse(state["post_migration_feature_eligible"])

    def test_c1_post_migration_capacity_schema_starts_2011(self):
        state = classify_exchange_date("C1", "2011-01-02")
        self.assertTrue(state["post_migration_feature_eligible"])
        self.assertEqual(state["schema_regime"], "POST_2011_CAPACITY_EXECUTION_SIZE")

    def test_bzx_c2_edgx_history_starts_2018(self):
        for venue in ("BZX", "C2", "EDGX"):
            with self.subTest(venue=venue):
                state = classify_exchange_date(venue, "2018-01-02")
                self.assertTrue(state["history_available"])
                self.assertTrue(state["post_migration_feature_eligible"])

    def test_other_venues_before_2018_are_not_advertised(self):
        for venue in ("BZX", "C2", "EDGX"):
            with self.subTest(venue=venue):
                self.assertFalse(classify_exchange_date(venue, "2017-12-29")["history_available"])

    def test_c1_old_total_exchange_volume_is_scaled_by_two(self):
        state = classify_exchange_date("C1", "2019-10-04")
        self.assertEqual(state["total_exchange_volume_multiplier"], 2)

    def test_c1_current_total_exchange_volume_has_no_scale(self):
        state = classify_exchange_date("C1", "2019-10-07")
        self.assertEqual(state["total_exchange_volume_multiplier"], 1)

    def test_c2_industry_volume_was_doubled_through_may_11(self):
        state = classify_exchange_date("C2", "2018-05-11")
        self.assertEqual(state["total_industry_volume_multiplier"], "0.5")

    def test_c2_industry_volume_current_scale_from_may_12(self):
        state = classify_exchange_date("C2", "2018-05-12")
        self.assertEqual(state["total_industry_volume_multiplier"], "1")

    def test_c1_oi_shifted_through_october_4(self):
        self.assertIn("SHIFTED", classify_exchange_date("C1", "2019-10-04")["open_interest_convention"])

    def test_c1_oi_current_convention_from_october_7(self):
        self.assertEqual(
            classify_exchange_date("C1", "2019-10-07")["open_interest_convention"],
            "CONSISTENT_START_OF_DAY_CONVENTION",
        )

    def test_c2_oi_shifted_through_may_11(self):
        self.assertIn("SHIFTED", classify_exchange_date("C2", "2018-05-11")["open_interest_convention"])

    def test_bzx_edgx_oi_consistent_start_of_day(self):
        for venue in ("BZX", "EDGX"):
            with self.subTest(venue=venue):
                self.assertEqual(
                    classify_exchange_date(venue, "2018-01-02")["open_interest_convention"],
                    "CONSISTENT_START_OF_DAY_CONVENTION",
                )

    def test_previous_close_exchange_only_breaks_are_explicit(self):
        self.assertEqual(classify_exchange_date("C1", "2019-10-04")["previous_close_scope"], "EXCHANGE_ONLY")
        self.assertEqual(classify_exchange_date("C2", "2018-05-11")["previous_close_scope"], "EXCHANGE_ONLY")

    def test_previous_close_industry_scope_is_explicit_after_breaks(self):
        self.assertEqual(classify_exchange_date("C1", "2019-10-07")["previous_close_scope"], "INDUSTRY_WIDE")
        self.assertEqual(classify_exchange_date("C2", "2018-05-12")["previous_close_scope"], "INDUSTRY_WIDE")
        self.assertEqual(classify_exchange_date("BZX", "2018-01-02")["previous_close_scope"], "INDUSTRY_WIDE")

    def test_legacy_w_capacity_boundary_is_explicit(self):
        self.assertEqual(
            classify_exchange_date("C1", "2019-09-30")["participant_code_regime"],
            "LEGACY_W_CODE_MAY_APPEAR",
        )
        self.assertEqual(
            classify_exchange_date("C1", "2019-10-01")["participant_code_regime"],
            "CURRENT_CAPACITY_CODE_MAPPING",
        )

    def test_c1_gth_boundary_is_explicit(self):
        self.assertFalse(classify_exchange_date("C1", "2023-12-10")["gth_included"])
        self.assertTrue(classify_exchange_date("C1", "2023-12-11")["gth_included"])
        self.assertFalse(classify_exchange_date("C2", "2023-12-11")["gth_included"])

    def test_flex_schema_boundary_is_explicit(self):
        self.assertFalse(classify_exchange_date("C1", "2024-10-15")["flex_schema_active"])
        self.assertTrue(classify_exchange_date("C1", "2024-10-16")["flex_schema_active"])

    def test_same_series_on_two_venues_is_allowed_and_aggregated(self):
        c1 = make_row(exchange="C1", buy=60, sell=30, total=45)
        bzx = make_row(exchange="BZX", buy=10, sell=90, total=120)
        result = aggregate_multi_exchange_underlying_rows([c1, bzx], "customer")
        self.assertEqual(result["venues_observed"], ["BZX", "C1"])
        self.assertEqual(result["unique_option_series_across_observed_venues"], 1)
        self.assertEqual(result["signed_directional_net_contracts"], -50)
        self.assertEqual(result["gross_capacity_contracts"], 190)
        self.assertEqual(result["observed_cboe_exchange_volume_adjusted"], 210)
        self.assertEqual(result["directional_imbalance_ratio_of_sums"], Decimal(-50) / Decimal(190))
        self.assertEqual(result["net_share_of_observed_cboe_exchange_volume"], Decimal(-50) / Decimal(210))

    def test_imbalance_is_ratio_of_sums_not_mean_of_venue_ratios(self):
        c1 = make_row(exchange="C1", buy=60, sell=30, total=45)
        bzx = make_row(exchange="BZX", buy=10, sell=90, total=120)
        result = aggregate_multi_exchange_underlying_rows([c1, bzx], "customer")
        self.assertNotEqual(
            result["directional_imbalance_ratio_of_sums"],
            (Decimal(30) / Decimal(90) + Decimal(-80) / Decimal(100)) / Decimal(2),
        )

    def test_duplicate_series_within_same_exchange_is_rejected(self):
        one = make_row(exchange="C1")
        two = make_row(exchange="C1")
        with self.assertRaisesRegex(ValueError, "DUPLICATE_OPTION_SERIES_WITHIN_EXCHANGE"):
            aggregate_multi_exchange_underlying_rows([one, two], "customer")

    def test_c1_legacy_rows_cannot_enter_post_migration_aggregator(self):
        row = make_row(exchange="C1", day="2010-12-31")
        with self.assertRaisesRegex(ValueError, "LEGACY_C1_REQUIRES_SEPARATE_SCHEMA"):
            aggregate_multi_exchange_underlying_rows([row], "customer")

    def test_pre_archive_exchange_row_is_rejected(self):
        row = make_row(exchange="BZX", day="2017-12-29")
        with self.assertRaisesRegex(ValueError, "EXCHANGE_HISTORY_NOT_ADVERTISED"):
            aggregate_multi_exchange_underlying_rows([row], "customer")

    def test_missing_venue_is_not_assumed_to_be_zero(self):
        result = aggregate_multi_exchange_underlying_rows([make_row(exchange="C1")], "customer")
        self.assertFalse(result["unobserved_venue_or_series_absence_is_zero"])
        self.assertFalse(result["venue_coverage_complete"])

    def test_industry_volume_and_open_interest_are_not_aggregated(self):
        result = aggregate_multi_exchange_underlying_rows(
            [make_row(exchange="C1"), make_row(exchange="BZX")], "customer"
        )
        self.assertFalse(result["total_industry_volume_aggregated"])
        self.assertFalse(result["open_interest_aggregated"])
        self.assertFalse(result["previous_close_used"])

    def test_mixed_trade_dates_are_rejected(self):
        one = make_row(exchange="C1", day="2018-06-15")
        two = make_row(exchange="BZX", day="2018-06-18")
        with self.assertRaisesRegex(ValueError, "MIXED_OR_MISSING_QUOTE_DATE"):
            aggregate_multi_exchange_underlying_rows([one, two], "customer")

    def test_mixed_underlyings_are_rejected(self):
        one = make_row(exchange="C1", underlying="ABC")
        two = make_row(exchange="BZX", underlying="XYZ", option_symbol="XYZ")
        with self.assertRaisesRegex(ValueError, "MIXED_OR_MISSING_UNDERLYING"):
            aggregate_multi_exchange_underlying_rows([one, two], "customer")

    def test_mixed_security_types_are_rejected(self):
        one = make_row(exchange="C1", security_type="1")
        two = make_row(exchange="BZX", security_type="2")
        with self.assertRaisesRegex(ValueError, "MIXED_OR_MISSING_SECURITY_TYPE"):
            aggregate_multi_exchange_underlying_rows([one, two], "customer")

    def test_index_security_type_is_excluded(self):
        row = make_row(exchange="C1", security_type="3")
        with self.assertRaisesRegex(ValueError, "UNSUPPORTED_SECURITY_TYPE"):
            aggregate_multi_exchange_underlying_rows([row], "customer")

    def test_flex_series_are_excluded_from_primary_panel(self):
        row = make_row(exchange="C1", day="2024-10-16", series_type="F")
        with self.assertRaisesRegex(ValueError, "FLEX_SERIES_EXCLUDED"):
            aggregate_multi_exchange_underlying_rows([row], "customer")

    def test_nonstandard_series_requires_deliverable_mapping(self):
        row = make_row(exchange="C1", series_type="N")
        with self.assertRaisesRegex(ValueError, "NONSTANDARD_SERIES_REQUIRES_DELIVERABLE_MAPPING"):
            aggregate_multi_exchange_underlying_rows([row], "customer")

    def test_unknown_series_type_is_rejected(self):
        row = make_row(exchange="C1", series_type="X")
        with self.assertRaisesRegex(ValueError, "UNSUPPORTED_SERIES_TYPE"):
            aggregate_multi_exchange_underlying_rows([row], "customer")

    def test_missing_exchange_is_rejected(self):
        row = make_row()
        row.pop("exchange")
        with self.assertRaisesRegex(ValueError, "MISSING_EXCHANGE"):
            aggregate_multi_exchange_underlying_rows([row], "customer")

    def test_unknown_exchange_is_rejected(self):
        row = make_row(exchange="NYSE")
        with self.assertRaisesRegex(ValueError, "UNSUPPORTED_EXCHANGE"):
            aggregate_multi_exchange_underlying_rows([row], "customer")

    def test_missing_total_exchange_volume_is_rejected(self):
        row = make_row()
        row.pop("total_exchange_vol")
        with self.assertRaisesRegex(ValueError, "MISSING_TOTAL_EXCHANGE_VOLUME"):
            aggregate_multi_exchange_underlying_rows([row], "customer")

    def test_convention_adjusted_volume_must_cover_capacity_gross(self):
        row = make_row(exchange="C1", total=20)
        with self.assertRaisesRegex(ValueError, "CAPACITY_GROSS_EXCEEDS_CONVENTION_ADJUSTED"):
            aggregate_multi_exchange_underlying_rows([row], "customer")

    def test_put_direction_reverses_buy_sell_sign(self):
        row = make_row(call_put="P", buy=60, sell=30)
        result = aggregate_multi_exchange_underlying_rows([row], "customer")
        self.assertEqual(result["signed_directional_net_contracts"], -30)

    def test_zero_gross_keeps_imbalance_undefined(self):
        row = make_row(buy=0, sell=0, total=0)
        result = aggregate_multi_exchange_underlying_rows([row], "customer")
        self.assertIsNone(result["directional_imbalance_ratio_of_sums"])
        self.assertIsNone(result["net_share_of_observed_cboe_exchange_volume"])

    def test_c1_old_volume_scale_is_applied_only_to_c1(self):
        c1 = make_row(exchange="C1", total=45)
        bzx = make_row(exchange="BZX", total=120)
        result = aggregate_multi_exchange_underlying_rows([c1, bzx], "customer")
        self.assertEqual(result["total_exchange_volume_multiplier_by_venue"], {"BZX": 1, "C1": 2})

    def test_c2_industry_volume_scale_is_metadata_not_an_aggregation_input(self):
        state = classify_exchange_date("C2", "2018-05-11")
        self.assertEqual(state["total_industry_volume_multiplier"], "0.5")
        result = aggregate_multi_exchange_underlying_rows([make_row(exchange="C2")], "customer")
        self.assertFalse(result["total_industry_volume_aggregated"])

    def test_result_never_claims_consolidated_opra_coverage_or_pit(self):
        result = aggregate_multi_exchange_underlying_rows([make_row(exchange="C1")], "customer")
        self.assertFalse(result["consolidated_opra_coverage"])
        self.assertEqual(result["series_identity_scope"], "EOD_FILE_KEY_ONLY_NOT_OCC_DELIVERABLE_IDENTITY")
        self.assertFalse(result["strict_pit_admitted"])
        self.assertFalse(result["alpha_admission"])


if __name__ == "__main__":
    unittest.main()

import unittest
from decimal import Decimal
from research.phase248_cboe_openclose_feature_contract import aggregate_underlying_rows, build_audit, compute_row_feature


def make_row(call_put="C", symbol="ABC", quote_date="2025-03-28", total=100, industry=200):
    row = {
        "call_put_flag": call_put, "underlying_symbol": symbol, "security_type": "1",
        "quote_date": quote_date, "option_symbol": f"{symbol}OPT", "expiration_date": "2025-04-18",
        "strike_price": "100", "series_type": "S", "total_exchange_vol": str(total),
        "total_industry_vol": str(industry),
    }
    for capacity in ("cust", "procust"):
        for bucket in ("lt_100", "100_199", "gt_199"):
            for action in ("open", "close"):
                for side in ("buy", "sell"):
                    row[f"{capacity}_{bucket}_{action}_{side}_vol"] = "0"
    for capacity in ("firm", "bd"):
        for action in ("open", "close"):
            for side in ("buy", "sell"):
                row[f"{capacity}_{action}_{side}_vol"] = "0"
    return row


class Phase248OpenCloseFeatureContractTests(unittest.TestCase):
    def test_call_open_buy_is_positive(self):
        row = make_row("C"); row["cust_lt_100_open_buy_vol"] = "12"; row["cust_lt_100_open_sell_vol"] = "4"
        result = compute_row_feature(row, "customer", "open")
        self.assertEqual(result["signed_directional_net_contracts"], 8)
        self.assertEqual(result["net_share_of_c1_volume"], Decimal("0.08"))

    def test_call_open_sell_is_negative(self):
        row = make_row("C"); row["cust_lt_100_open_buy_vol"] = "3"; row["cust_lt_100_open_sell_vol"] = "9"
        self.assertEqual(compute_row_feature(row, "customer")["signed_directional_net_contracts"], -6)

    def test_put_open_buy_is_negative(self):
        row = make_row("P"); row["cust_lt_100_open_buy_vol"] = "10"; row["cust_lt_100_open_sell_vol"] = "2"
        self.assertEqual(compute_row_feature(row, "customer")["signed_directional_net_contracts"], -8)

    def test_put_open_sell_is_positive(self):
        row = make_row("P"); row["cust_lt_100_open_buy_vol"] = "2"; row["cust_lt_100_open_sell_vol"] = "10"
        self.assertEqual(compute_row_feature(row, "customer")["signed_directional_net_contracts"], 8)

    def test_customer_all_size_buckets_are_aggregated(self):
        row = make_row("C")
        for bucket, buy in (("lt_100", "2"), ("100_199", "3"), ("gt_199", "5")):
            row[f"cust_{bucket}_open_buy_vol"] = buy
            row[f"cust_{bucket}_open_sell_vol"] = "1"
        result = compute_row_feature(row, "customer")
        self.assertEqual(result["buy_volume"], 10); self.assertEqual(result["sell_volume"], 3)
        self.assertEqual(result["signed_directional_net_contracts"], 7)

    def test_large_execution_bucket_is_separate(self):
        row = make_row("C"); row["procust_gt_199_open_buy_vol"] = "20"
        result = compute_row_feature(row, "pro_customer", "open", "gt_199")
        self.assertEqual(result["signed_directional_net_contracts"], 20)
        self.assertEqual(result["size_bucket"], "gt_199")

    def test_qty_counts_trades_and_is_not_used_as_contract_volume(self):
        row = make_row("C"); row["cust_lt_100_open_buy_qty"] = "999"; row["cust_lt_100_open_buy_vol"] = "7"
        self.assertEqual(compute_row_feature(row, "customer")["signed_directional_net_contracts"], 7)

    def test_close_flow_is_separate_from_open_flow(self):
        row = make_row("C"); row["cust_lt_100_close_sell_vol"] = "7"
        self.assertEqual(compute_row_feature(row, "customer", "close")["signed_directional_net_contracts"], -7)

    def test_firm_and_broker_dealer_controls_are_supported(self):
        row = make_row("P"); row["firm_open_sell_vol"] = "6"; row["bd_open_buy_vol"] = "4"
        self.assertEqual(compute_row_feature(row, "firm")["signed_directional_net_contracts"], 6)
        self.assertEqual(compute_row_feature(row, "broker_dealer")["signed_directional_net_contracts"], -4)

    def test_market_maker_open_close_is_not_invented(self):
        with self.assertRaisesRegex(ValueError, "UNSUPPORTED_CAPACITY"):
            compute_row_feature(make_row("C"), "market_maker")

    def test_blank_volume_is_unknown_not_zero(self):
        row = make_row("C"); row["cust_lt_100_open_buy_vol"] = ""
        with self.assertRaisesRegex(ValueError, "MISSING_VALUE"):
            compute_row_feature(row, "customer")

    def test_negative_and_noninteger_volumes_are_rejected(self):
        for raw, reason in (("-1", "NEGATIVE_VALUE"), ("1.5", "INVALID_INTEGER"), ("abc", "INVALID_INTEGER")):
            row = make_row("C"); row["cust_lt_100_open_buy_vol"] = raw
            with self.assertRaisesRegex(ValueError, reason):
                compute_row_feature(row, "customer")

    def test_zero_capacity_gross_has_undefined_imbalance(self):
        result = compute_row_feature(make_row("C"), "customer")
        self.assertIsNone(result["directional_imbalance"])
        self.assertEqual(result["net_share_of_c1_volume"], Decimal("0"))

    def test_zero_total_exchange_volume_with_zero_capacity_is_unknown_ratio(self):
        result = compute_row_feature(make_row("C", total=0), "customer")
        self.assertIsNone(result["net_share_of_c1_volume"])
        self.assertEqual(result["signed_directional_net_contracts"], 0)

    def test_capacity_volume_cannot_exceed_total_exchange_volume(self):
        row = make_row("C", total=5); row["cust_lt_100_open_buy_vol"] = "6"
        with self.assertRaisesRegex(ValueError, "CAPACITY_VOLUME_EXCEEDS_TOTAL_EXCHANGE_VOLUME"):
            compute_row_feature(row, "customer")

    def test_missing_industry_volume_does_not_become_zero(self):
        row = make_row("C"); del row["total_industry_vol"]
        result = compute_row_feature(row, "customer")
        self.assertIsNone(result["net_share_of_industry_volume"])
        self.assertIsNone(result["c1_to_industry_volume_ratio"])

    def test_underlying_aggregation_is_volume_weighted(self):
        a = make_row("C", total=100, industry=200); a["cust_lt_100_open_buy_vol"] = "10"
        b = make_row("P", total=300, industry=600); b["option_symbol"] = "ABCOPT2"; b["cust_lt_100_open_sell_vol"] = "20"
        result = aggregate_underlying_rows([a, b], "customer", "open")
        self.assertEqual(result["signed_directional_net_contracts"], 30)
        self.assertEqual(result["total_c1_contracts"], 400)
        self.assertEqual(result["net_share_of_c1_volume"], Decimal("0.075"))

    def test_mixed_underlyings_cannot_be_aggregated(self):
        a = make_row("C", symbol="ABC"); b = make_row("C", symbol="XYZ")
        with self.assertRaisesRegex(ValueError, "MIXED_OR_MISSING_UNDERLYING"):
            aggregate_underlying_rows([a, b], "customer")

    def test_duplicate_option_series_cannot_be_double_counted(self):
        a = make_row("C"); b = make_row("C")
        with self.assertRaisesRegex(ValueError, "DUPLICATE_OPTION_SERIES_KEY"):
            aggregate_underlying_rows([a, b], "customer")

    def test_mixed_quote_dates_cannot_be_aggregated(self):
        a = make_row("C"); b = make_row("C"); b["quote_date"] = "2025-03-31"; b["option_symbol"] = "ABCOPT2"
        with self.assertRaisesRegex(ValueError, "MIXED_OR_MISSING_QUOTE_DATE"):
            aggregate_underlying_rows([a, b], "customer")

    def test_mm_dd_yyyy_quote_date_is_normalized(self):
        row = make_row("C"); row["quote_date"] = "03/28/2025"
        self.assertEqual(aggregate_underlying_rows([row], "customer")["quote_date"], "2025-03-28")

    def test_pre_primary_history_date_is_rejected(self):
        row = make_row("C"); row["quote_date"] = "10/04/2019"
        with self.assertRaisesRegex(ValueError, "PRE_PRIMARY_HISTORY_START"):
            aggregate_underlying_rows([row], "customer")

    def test_invalid_quote_date_is_rejected(self):
        row = make_row("C"); row["quote_date"] = "2025-02-30"
        with self.assertRaisesRegex(ValueError, "INVALID_QUOTE_DATE"):
            aggregate_underlying_rows([row], "customer")

    def test_flex_series_are_excluded_from_primary_cohort(self):
        row = make_row("C"); row["series_type"] = "F"
        with self.assertRaisesRegex(ValueError, "FLEX_SERIES_EXCLUDED_FROM_PRIMARY"):
            aggregate_underlying_rows([row], "customer")

    def test_unknown_series_type_is_rejected(self):
        row = make_row("C"); row["series_type"] = "X"
        with self.assertRaisesRegex(ValueError, "UNSUPPORTED_SERIES_TYPE"):
            aggregate_underlying_rows([row], "customer")

    def test_mixed_security_types_cannot_be_aggregated(self):
        a = make_row("C"); b = make_row("C"); b["security_type"] = "2"; b["option_symbol"] = "ABCOPT2"
        with self.assertRaisesRegex(ValueError, "MIXED_OR_MISSING_SECURITY_TYPE"):
            aggregate_underlying_rows([a, b], "customer")

    def test_index_and_warrant_security_types_are_excluded(self):
        row = make_row("C"); row["security_type"] = "3"
        with self.assertRaisesRegex(ValueError, "UNSUPPORTED_SECURITY_TYPE"):
            aggregate_underlying_rows([row], "customer")

    def test_invalid_size_bucket_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "UNSUPPORTED_SIZE_BUCKET"):
            compute_row_feature(make_row("C"), "customer", "open", "huge")

    def test_feature_contract_keeps_all_research_gates_closed(self):
        audit = build_audit(); gates = audit["pit_and_economic_gates"]
        self.assertFalse(gates["strict_pit_admitted"]); self.assertFalse(gates["return_test_authorized"])
        self.assertFalse(gates["alpha_admission"]); self.assertTrue(gates["f80_frozen"])
        self.assertFalse(gates["consumed_holdout_used"])


if __name__ == "__main__":
    unittest.main()

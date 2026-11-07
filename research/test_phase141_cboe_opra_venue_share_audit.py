import unittest

from research.phase141_cboe_opra_venue_share_audit import (
    audit_option_trade_rows,
    audit_open_close_rows,
    compare_sample_populations,
)


def trade_row(exchange, size, *, date="1/7/2026", underlying="AAPL",
              clock="21:30.4", condition="18", cancelled="0"):
    return {
        "underlying_symbol": underlying,
        "market_date": date,
        "quote_datetime": clock,
        "root": underlying,
        "expiration": "1/9/2026",
        "strike": "100",
        "option_type": "C",
        "exchange_id": str(exchange),
        "trade_size": str(size),
        "trade_condition_id": str(condition),
        "canceled_trade_condition_id": str(cancelled),
    }


def open_close_row(buy, sell, exchange, industry, *, date="2025-03-28", underlying="AAPL"):
    return {
        "quote_date": date,
        "underlying_symbol": underlying,
        "option_symbol": "AAPL",
        "total_exchange_vol": str(exchange),
        "total_industry_vol": str(industry),
        "firm_open_buy_vol": str(buy),
        "firm_open_sell_vol": str(sell),
    }


class Phase141Tests(unittest.TestCase):
    def test_option_trades_uses_exchange_volume_and_ignores_blank_padding(self):
        rows = [
            trade_row(5, 10),
            trade_row(42, 20),
            trade_row(60, 5),
            trade_row(65, 5),
            trade_row(9, 10),
            {k: "" for k in trade_row(5, 1)},
        ]
        result = audit_option_trade_rows(rows)
        self.assertEqual(result["valid_trade_rows"], 5)
        self.assertEqual(result["blank_padded_rows"], 1)
        self.assertEqual(result["total_contract_volume"], 50)
        self.assertAlmostEqual(result["c1_volume_share"], 0.20)
        self.assertAlmostEqual(result["cboe_four_volume_share"], 0.80)

    def test_canceled_condition_is_counted_not_silently_dropped(self):
        result = audit_option_trade_rows([trade_row(5, 7, cancelled="123")])
        self.assertEqual(result["total_contract_volume"], 7)
        self.assertEqual(result["nonzero_cancel_condition_rows"], 1)

    def test_two_component_clock_fails_published_sample_format_gate(self):
        result = audit_option_trade_rows([trade_row(5, 7, clock="21:30.4")])
        self.assertEqual(result["quote_datetime_formats"], {"two_component_clock": 1})
        self.assertEqual(result["intraday_timestamp_conformance"], "FAIL_SAMPLE_FORMAT_CONFORMANCE")

    def test_full_datetime_does_not_prove_point_in_time_availability(self):
        result = audit_option_trade_rows([trade_row(5, 7, clock="2026-01-07 09:30:00.000")])
        self.assertEqual(result["intraday_timestamp_conformance"], "PASS_FORMAT_ONLY_NOT_PIT")

    def test_invalid_trade_size_is_not_counted(self):
        row = trade_row(5, 7)
        row["trade_size"] = "1.5"
        result = audit_option_trade_rows([row])
        self.assertEqual(result["valid_trade_rows"], 0)
        self.assertEqual(result["errors"], {"invalid_integer:trade_size": 1})

    def test_one_sided_openclose_volume_prevents_double_count(self):
        result = audit_open_close_rows([open_close_row(10, 10, 20, 100)])
        self.assertEqual(result["one_sided_buy_contract_volume"], 10)
        self.assertEqual(result["two_sided_total_exchange_volume"], 20)
        self.assertAlmostEqual(result["weighted_one_sided_c1_share_proxy"], 0.10)
        self.assertEqual(result["total_exchange_equals_buy_plus_sell_rows"], 1)

    def test_unreconciled_openclose_row_is_excluded_from_share_proxy(self):
        result = audit_open_close_rows([open_close_row(10, 8, 18, 100)])
        self.assertEqual(result["buy_equals_sell_rows"], 0)
        self.assertIsNone(result["weighted_one_sided_c1_share_proxy"])
        self.assertEqual(result["share_proxy_rows"], 0)

    def test_zero_industry_denominator_is_not_used(self):
        result = audit_open_close_rows([open_close_row(10, 10, 20, 0)])
        self.assertIsNone(result["weighted_one_sided_c1_share_proxy"])
        self.assertEqual(result["share_proxy_rows"], 0)

    def test_sample_dates_must_overlap_before_cross_source_comparison(self):
        trades = {"market_dates": ["2026-01-07"], "underlying_symbols": ["AAPL"]}
        openclose = {"quote_dates": ["2025-03-28"], "underlying_symbols": ["AAPL"]}
        result = compare_sample_populations(trades, openclose)
        self.assertFalse(result["same_date_underlying_overlap"])
        self.assertFalse(result["direct_cross_source_reconciliation_allowed"])

    def test_date_and_underlying_overlap_still_requires_contract_keys(self):
        trades = {"market_dates": ["2025-03-28"], "underlying_symbols": ["AAPL"]}
        openclose = {"quote_dates": ["2025-03-28"], "underlying_symbols": ["AAPL"]}
        result = compare_sample_populations(trades, openclose)
        self.assertTrue(result["same_date_underlying_overlap"])
        self.assertTrue(result["contract_level_key_reconciliation_still_required"])

    def test_option_trade_sample_with_one_underlying_does_not_prove_broad_coverage(self):
        result = audit_option_trade_rows([trade_row(5, 7)])
        self.assertFalse(result["broad_universe_coverage_proven"])


if __name__ == "__main__":
    unittest.main()

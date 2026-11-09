import unittest
from decimal import Decimal

from research.phase197_cboe_greek_normalized_flow_sample import aggregate_trade_rows


def row(option_type, delta, size, price, bid, ask, dte=7, vega="0.10"):
    return {
        "option_type": option_type,
        "trade_delta": delta,
        "trade_vega": vega,
        "trade_size": str(size),
        "trade_price": str(price),
        "best_bid": str(bid),
        "best_ask": str(ask),
        "dte": str(dte),
    }


class Phase197Tests(unittest.TestCase):
    def test_call_buyer_adds_positive_underlying_delta(self):
        result = aggregate_trade_rows([row("C", "0.50", 10, "1.25", "1.20", "1.25")])
        overall = result["overall"]
        self.assertEqual(overall["signed_underlying_delta_contracts_no_multiplier"], "5.00")
        self.assertEqual(overall["signed_option_demand_delta_contracts_no_multiplier"], "5.00")
        self.assertEqual(overall["delta_imbalance_ratio"], "1.00000000")

    def test_put_buyer_adds_negative_underlying_delta_but_positive_option_demand(self):
        result = aggregate_trade_rows([row("P", "-0.40", 10, "1.25", "1.20", "1.25")])
        overall = result["overall"]
        self.assertEqual(overall["signed_underlying_delta_contracts_no_multiplier"], "-4.00")
        self.assertEqual(overall["signed_option_demand_delta_contracts_no_multiplier"], "4.00")
        self.assertEqual(overall["option_demand_delta_imbalance_ratio"], "1.00000000")

    def test_put_seller_at_bid_adds_positive_underlying_delta(self):
        result = aggregate_trade_rows([row("P", "-0.40", 5, "1.20", "1.20", "1.25")])
        overall = result["overall"]
        self.assertEqual(overall["signed_underlying_delta_contracts_no_multiplier"], "2.00")
        self.assertEqual(overall["signed_option_demand_delta_contracts_no_multiplier"], "-2.00")

    def test_call_seller_at_bid_adds_negative_underlying_delta(self):
        result = aggregate_trade_rows([row("C", "0.60", 5, "1.20", "1.20", "1.25")])
        self.assertEqual(result["overall"]["signed_underlying_delta_contracts_no_multiplier"], "-3.00")

    def test_inside_spread_is_not_assigned_a_side(self):
        result = aggregate_trade_rows([row("C", "0.50", 10, "1.22", "1.20", "1.25")])
        overall = result["overall"]
        self.assertEqual(overall["classified_rows"], 0)
        self.assertEqual(overall["gross_delta_contracts_no_multiplier"], "0")
        self.assertIsNone(overall["delta_imbalance_ratio"])
        self.assertEqual(result["nbbo_class_contract_volume"]["inside_spread_unclassified"], 10)

    def test_calls_and_puts_are_separated(self):
        result = aggregate_trade_rows([
            row("C", "0.50", 10, "1.25", "1.20", "1.25"),
            row("P", "-0.40", 10, "1.25", "1.20", "1.25"),
        ])
        self.assertEqual(result["by_option_type"]["C"]["signed_underlying_delta_contracts_no_multiplier"], "5.00")
        self.assertEqual(result["by_option_type"]["P"]["signed_underlying_delta_contracts_no_multiplier"], "-4.00")

    def test_dte_buckets_are_chronological_and_separate(self):
        result = aggregate_trade_rows([
            row("C", "0.50", 1, "1.25", "1.20", "1.25", dte=3),
            row("C", "0.50", 1, "1.25", "1.20", "1.25", dte=14),
            row("P", "-0.50", 1, "1.20", "1.20", "1.25", dte=60),
            row("P", "-0.50", 1, "1.20", "1.20", "1.25", dte=120),
        ])
        self.assertEqual(set(result["by_dte_bucket"]), {"0_7_days", "8_30_days", "31_90_days", "91_plus_days"})

    def test_expired_contracts_have_separate_bucket(self):
        result = aggregate_trade_rows([row("C", "0.50", 1, "1.25", "1.20", "1.25", dte=-1)])
        self.assertIn("expired", result["by_dte_bucket"])

    def test_raw_delta_sign_mismatch_is_reported_not_silently_rewritten(self):
        result = aggregate_trade_rows([row("C", "-0.50", 10, "1.25", "1.20", "1.25")])
        diag = result["greek_sign_diagnostics"]
        self.assertEqual(diag["raw_delta_sign_mismatch_rows_vs_call_put"], 1)
        self.assertEqual(result["overall"]["signed_underlying_delta_contracts_no_multiplier"], "5.00")

    def test_vega_imbalance_is_separate_from_delta_imbalance(self):
        result = aggregate_trade_rows([
            row("C", "0.50", 10, "1.25", "1.20", "1.25", vega="0.10"),
            row("C", "0.50", 10, "1.20", "1.20", "1.25", vega="0.20"),
        ])
        overall = result["overall"]
        self.assertEqual(overall["signed_vega_contracts_no_multiplier"], "-1.00")
        self.assertEqual(overall["vega_imbalance_ratio"], "-0.33333333")

    def test_empty_sample_has_no_division_by_zero(self):
        result = aggregate_trade_rows([])
        self.assertEqual(result["overall"]["rows"], 0)
        self.assertIsNone(result["overall"]["vega_imbalance_ratio"])

    def test_option_type_validation_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "option_type_invalid"):
            aggregate_trade_rows([row("X", "0.50", 1, "1.25", "1.20", "1.25")])


if __name__ == "__main__":
    unittest.main()

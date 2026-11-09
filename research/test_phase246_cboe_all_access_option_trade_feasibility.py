import unittest

from research.phase246_cboe_all_access_option_trade_feasibility import (
    build_audit,
    classify_trade_at,
    count_as_new_trade,
)


class Phase246CboeAllAccessTests(unittest.TestCase):
    def test_trial_budget_is_conservative_integer_request_count(self):
        result = build_audit()["trial"]
        self.assertEqual(result["max_full_historical_requests_per_day"], 33)
        self.assertEqual(result["max_full_historical_requests_over_trial"], 462)
        self.assertEqual(33 * 15, 495)

    def test_advertised_history_precedes_other_current_candidates(self):
        result = build_audit()
        self.assertEqual(result["advertised_history_start_year"], 2003)
        self.assertGreater(int(result["comparators"]["orats_time_sales_history_start"][:4]), 2003)
        self.assertGreater(int(result["comparators"]["cboe_tbt_archive_history_start"][:4]), 2003)

    def test_trade_at_mapping_is_only_a_price_class_proxy(self):
        self.assertEqual(classify_trade_at("Above Ask"), "BUY_SIDE_PRICE_CLASS")
        self.assertEqual(classify_trade_at("On Ask"), "BUY_SIDE_PRICE_CLASS")
        self.assertEqual(classify_trade_at("Below Bid"), "SELL_SIDE_PRICE_CLASS")
        self.assertEqual(classify_trade_at("On Bid"), "SELL_SIDE_PRICE_CLASS")
        self.assertEqual(classify_trade_at("Mid Market"), "UNKNOWN")
        self.assertEqual(classify_trade_at("Crossed Market"), "UNKNOWN")
        self.assertEqual(classify_trade_at("No Market"), "UNKNOWN")
        self.assertEqual(classify_trade_at("unmapped"), "UNKNOWN")

    def test_only_normal_print_is_initially_countable(self):
        self.assertTrue(count_as_new_trade(0))
        self.assertFalse(count_as_new_trade(1))
        self.assertFalse(count_as_new_trade(2))
        self.assertFalse(count_as_new_trade("bad"))

    def test_trial_historical_price_access_remains_unverified(self):
        result = build_audit()
        self.assertEqual(
            result["trial"]["historical_opra_price_field_access_during_trial"],
            "UNVERIFIED",
        )
        self.assertFalse(result["trial"]["trial_sip_access"])

    def test_no_pit_or_alpha_admission(self):
        result = build_audit()
        gates = result["pit_and_coverage_gates"]
        self.assertFalse(gates["strict_pit_admitted"])
        self.assertFalse(gates["alpha_test_authorized"])
        self.assertFalse(gates["first_receipt_ledger"])
        self.assertFalse(gates["immutable_correction_vintages"])

    def test_no_external_side_effects(self):
        controls = build_audit()["controls"]
        self.assertFalse(controls["account_signup"])
        self.assertFalse(controls["card_authorization"])
        self.assertFalse(controls["api_token_used"])
        self.assertEqual(controls["api_requests_sent"], 0)
        self.assertFalse(controls["data_purchase"])
        self.assertFalse(controls["vendor_contact"])
        self.assertTrue(controls["f80_frozen"])


if __name__ == "__main__":
    unittest.main()

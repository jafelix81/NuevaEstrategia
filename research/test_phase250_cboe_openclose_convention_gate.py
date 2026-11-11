import unittest
from decimal import Decimal

from research.phase250_cboe_openclose_convention_gate import (
    classify_date,
    compute_directional_feature,
)


def row(day="2018-06-15", call_put="C", total=None):
    result = {
        "quote_date": day,
        "call_put_flag": call_put,
        "cust_lt_100_open_buy_vol": "10",
        "cust_100_199_open_buy_vol": "20",
        "cust_gt_199_open_buy_vol": "30",
        "cust_lt_100_open_sell_vol": "4",
        "cust_100_199_open_sell_vol": "8",
        "cust_gt_199_open_sell_vol": "18",
        "procust_lt_100_open_buy_vol": "3",
        "procust_100_199_open_buy_vol": "2",
        "procust_gt_199_open_buy_vol": "1",
        "procust_lt_100_open_sell_vol": "1",
        "procust_100_199_open_sell_vol": "2",
        "procust_gt_199_open_sell_vol": "3",
        "firm_open_buy_vol": "5",
        "firm_open_sell_vol": "2",
        "bd_open_buy_vol": "7",
        "bd_open_sell_vol": "3",
    }
    if total is not None:
        result["total_exchange_vol"] = str(total)
    return result


class Phase250ConventionGateTests(unittest.TestCase):
    def test_post_migration_starts_2011_01_02(self):
        state = classify_date("2011-01-02")
        self.assertTrue(state["eligible_for_post_migration_contract"])
        self.assertEqual(state["schema_regime"], "POST_2011_EXECUTION_SIZE")

    def test_pre_migration_is_separate_legacy_schema(self):
        state = classify_date("2010-12-31")
        self.assertFalse(state["eligible_for_post_migration_contract"])
        self.assertEqual(state["schema_regime"], "PRE_2011_LEGACY_ORDER_SIZE")

    def test_pre_migration_rows_fail_closed_in_post_migration_feature(self):
        with self.assertRaisesRegex(ValueError, "PRE_2011_REQUIRES_SEPARATE_LEGACY_SCHEMA"):
            compute_directional_feature(row(day="2010-12-31"), "customer")

    def test_2018_directional_imbalance_does_not_require_c1_total_volume(self):
        result = compute_directional_feature(row(), "customer")
        self.assertEqual(result["signed_directional_net_contracts"], 30)
        self.assertEqual(result["gross_capacity_contracts"], 90)
        self.assertEqual(result["directional_imbalance"], Decimal("0.3333333333333333333333333333"))
        self.assertIsNone(result["net_share_of_c1_volume"])
        self.assertEqual(result["normalization_status"], "NOT_ELIGIBLE_PRE_2019_10_07_VOLUME_CONVENTION")

    def test_2018_oi_is_not_eligible(self):
        self.assertFalse(classify_date("2018-06-15")["open_interest_eligible"])

    def test_2019_10_04_keeps_old_volume_and_oi_convention(self):
        state = classify_date("2019-10-04")
        self.assertFalse(state["open_interest_eligible"])
        self.assertEqual(state["volume_regime"], "PRE_2019_10_07_C1_VOLUME_AND_OI_CONVENTION")

    def test_2019_10_07_enables_current_volume_normalization(self):
        result = compute_directional_feature(row(day="2019-10-07", total="200"), "customer")
        self.assertEqual(result["net_share_of_c1_volume"], Decimal("0.15"))
        self.assertEqual(result["normalization_status"], "CURRENT_CONVENTION_NORMALIZATION_AVAILABLE")
        self.assertTrue(result["open_interest_eligible"])

    def test_2019_10_01_participant_code_regime_is_current_but_volume_is_not(self):
        state = classify_date("2019-10-01")
        self.assertEqual(state["participant_code_regime"], "CURRENT_PARTICIPANT_CODE_MAPPING")
        self.assertFalse(state["open_interest_eligible"])

    def test_pre_october_2019_marks_legacy_w_code(self):
        state = classify_date("2019-09-30")
        self.assertEqual(state["participant_code_regime"], "LEGACY_W_CODE_PRESENT")

    def test_put_direction_reverses_buy_sell_sign(self):
        result = compute_directional_feature(row(call_put="P"), "customer")
        self.assertEqual(result["signed_directional_net_contracts"], -30)
        self.assertLess(result["directional_imbalance"], 0)

    def test_zero_gross_has_undefined_imbalance(self):
        r = row()
        for key in list(r):
            if key.endswith("_open_buy_vol") or key.endswith("_open_sell_vol"):
                r[key] = "0"
        result = compute_directional_feature(r, "customer")
        self.assertEqual(result["gross_capacity_contracts"], 0)
        self.assertIsNone(result["directional_imbalance"])

    def test_customer_size_buckets_sum_to_all(self):
        all_sizes = compute_directional_feature(row(), "customer")
        small = compute_directional_feature(row(), "customer", size_bucket="lt_100")
        medium = compute_directional_feature(row(), "customer", size_bucket="100_199")
        large = compute_directional_feature(row(), "customer", size_bucket="gt_199")
        self.assertEqual(all_sizes["buy_volume"], small["buy_volume"] + medium["buy_volume"] + large["buy_volume"])
        self.assertEqual(all_sizes["sell_volume"], small["sell_volume"] + medium["sell_volume"] + large["sell_volume"])

    def test_pro_customer_remains_a_capacity_class_not_beneficial_owner(self):
        result = compute_directional_feature(row(), "pro_customer")
        self.assertFalse(result["beneficial_owner_identified"])

    def test_firm_and_broker_dealer_have_no_size_bucket(self):
        self.assertEqual(compute_directional_feature(row(), "firm")["buy_volume"], 5)
        with self.assertRaisesRegex(ValueError, "SIZE_BUCKET_NOT_DEFINED_FOR_CAPACITY"):
            compute_directional_feature(row(), "firm", size_bucket="lt_100")

    def test_gth_boundary_is_explicit(self):
        self.assertFalse(classify_date("2023-12-10")["gth_included"])
        self.assertTrue(classify_date("2023-12-11")["gth_included"])

    def test_invalid_negative_volume_fails_closed(self):
        r = row()
        r["cust_lt_100_open_buy_vol"] = "-1"
        with self.assertRaisesRegex(ValueError, "INVALID_NONNEGATIVE_INTEGER_VOLUME"):
            compute_directional_feature(r, "customer")

    def test_invalid_current_convention_denominator_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "CAPACITY_GROSS_EXCEEDS_CURRENT_C1_TOTAL_VOLUME"):
            compute_directional_feature(row(day="2019-10-07", total="20"), "customer")


if __name__ == "__main__":
    unittest.main()

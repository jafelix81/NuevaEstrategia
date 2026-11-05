import unittest

from research.phase94_dood import (
    compute_published_dood,
    compute_multiplier_adjusted_dood,
)


class PublishedDOODTests(unittest.TestCase):
    def test_published_formula_has_no_contract_multiplier(self):
        rows = [{"delta": 0.5, "ask_volume": 100, "bid_volume": 20, "multiplier": 100}]
        self.assertAlmostEqual(compute_published_dood(rows, 10_000), 0.004)

    def test_signed_put_delta_is_not_flipped_a_second_time(self):
        rows = [{"delta": -0.4, "ask_volume": 100, "bid_volume": 0}]
        self.assertAlmostEqual(compute_published_dood(rows, 10_000), -0.004)

    def test_seller_initiated_call_volume_reduces_dood(self):
        rows = [{"delta": 0.5, "ask_volume": 0, "bid_volume": 100}]
        self.assertAlmostEqual(compute_published_dood(rows, 10_000), -0.005)

    def test_call_and_put_demand_net_by_signed_delta(self):
        rows = [
            {"delta": 0.5, "ask_volume": 100, "bid_volume": 0},
            {"delta": -0.5, "ask_volume": 100, "bid_volume": 0},
        ]
        self.assertAlmostEqual(compute_published_dood(rows, 10_000), 0.0)

    def test_midpoint_or_unknown_volume_is_not_silently_signed(self):
        rows = [{
            "delta": 0.5, "ask_volume": 0, "bid_volume": 0,
            "midpoint_volume": 500, "unclassified_volume": 200,
        }]
        self.assertAlmostEqual(compute_published_dood(rows, 10_000), 0.0)

    def test_empty_chain_is_zero(self):
        self.assertEqual(compute_published_dood([], 10_000), 0.0)

    def test_multiplier_variant_is_separate_and_scales_standard_contract(self):
        rows = [{"delta": 0.5, "ask_volume": 100, "bid_volume": 20, "multiplier": 100}]
        published = compute_published_dood(rows, 10_000)
        adjusted = compute_multiplier_adjusted_dood(rows, 10_000)
        self.assertAlmostEqual(adjusted, 100 * published)

    def test_adjusted_contracts_change_only_the_sensitivity(self):
        rows = [
            {"delta": 0.5, "ask_volume": 100, "bid_volume": 0, "multiplier": 100},
            {"delta": 0.5, "ask_volume": 100, "bid_volume": 0, "multiplier": 50},
        ]
        self.assertAlmostEqual(compute_published_dood(rows, 10_000), 0.01)
        self.assertAlmostEqual(compute_multiplier_adjusted_dood(rows, 10_000), 0.075)

    def test_zero_or_negative_underlying_volume_is_rejected(self):
        for volume in (0, -1):
            with self.assertRaises(ValueError):
                compute_published_dood([], volume)

    def test_negative_option_volume_is_rejected(self):
        with self.assertRaises(ValueError):
            compute_published_dood(
                [{"delta": 0.5, "ask_volume": -1, "bid_volume": 0}], 100
            )

    def test_non_finite_delta_is_rejected(self):
        with self.assertRaises(ValueError):
            compute_published_dood(
                [{"delta": float("nan"), "ask_volume": 1, "bid_volume": 0}], 100
            )

    def test_missing_multiplier_is_rejected_only_for_sensitivity(self):
        rows = [{"delta": 0.5, "ask_volume": 10, "bid_volume": 0}]
        self.assertGreater(compute_published_dood(rows, 100), 0)
        with self.assertRaises(ValueError):
            compute_multiplier_adjusted_dood(rows, 100)


if __name__ == "__main__":
    unittest.main()

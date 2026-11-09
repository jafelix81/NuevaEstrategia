import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

import research.phase148_independent_alpha_lab_cost_audit as audit


class Phase148CostAuditTests(unittest.TestCase):
    def test_long_short_spread_has_four_one_way_legs(self):
        self.assertEqual(audit.SPREAD_COST_MULTIPLIER, 4)
        self.assertEqual(audit.SPREAD_COST_MULTIPLIER * 10, 40)

    def test_cost_adjustment_is_applied_to_each_spread(self):
        gross = 0.012
        net = gross - audit.SPREAD_COST_MULTIPLIER * 10 / 10_000
        self.assertAlmostEqual(net, 0.008)

    def test_cost_shift_moves_both_ci_bounds_equally(self):
        gross_ci = (-0.02, 0.05)
        spread_cost = audit.SPREAD_COST_MULTIPLIER * 25 / 10_000
        net_ci = (gross_ci[0] - spread_cost, gross_ci[1] - spread_cost)
        self.assertAlmostEqual(net_ci[0], -0.03)
        self.assertAlmostEqual(net_ci[1], 0.04)

    def test_bootstrap_is_deterministic(self):
        values = np.array([-0.02, 0.01, 0.03, -0.01, 0.02, 0.04])
        a = audit.circular_block_bootstrap(values, 3, 500, 99)
        b = audit.circular_block_bootstrap(values, 3, 500, 99)
        np.testing.assert_array_equal(a, b)

    def test_bootstrap_returns_expected_number_of_draws(self):
        values = np.array([0.01, -0.01, 0.02, 0.03])
        got = audit.circular_block_bootstrap(values, 2, 1000, 5)
        self.assertEqual(len(got), 1000)
        self.assertTrue(np.isfinite(got).all())

    def test_loo_means(self):
        values = np.array([1.0, 2.0, 3.0])
        np.testing.assert_allclose(audit.leave_one_out_means(values), [2.5, 2.0, 1.5])

    def test_loo_rejects_single_observation(self):
        with self.assertRaises(ValueError):
            audit.leave_one_out_means([1.0])

    def test_bootstrap_rejects_invalid_block(self):
        with self.assertRaises(ValueError):
            audit.circular_block_bootstrap([1.0, 2.0], 0, 100, 1)

    def test_bootstrap_rejects_single_observation(self):
        with self.assertRaises(ValueError):
            audit.circular_block_bootstrap([1.0], 1, 100, 1)

    def test_actual_20_session_validation_fails_after_five_bps(self):
        audit.BOOTSTRAP_REPS = 500
        input_path = Path("research/phase148_phase29_spread_series.json")
        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "audit.json"
            result = audit.run_audit(input_path, output_path)
        gate = result["validation_strict_screen"]["20"]["5"]
        stage = next(
            x for x in result["stage_summaries"]
            if x["horizon_sessions"] == 20 and x["stage"] == "validation"
        )
        self.assertLess(stage["cost_sensitivity"]["5"]["net_mean"], 0)
        self.assertFalse(gate["strict_validation_pass"])

    def test_actual_60_session_validation_mean_is_positive_but_ci_fails(self):
        audit.BOOTSTRAP_REPS = 500
        input_path = Path("research/phase148_phase29_spread_series.json")
        with tempfile.TemporaryDirectory() as tmp:
            result = audit.run_audit(input_path, Path(tmp) / "audit.json")
        stage = next(
            x for x in result["stage_summaries"]
            if x["horizon_sessions"] == 60 and x["stage"] == "validation"
        )
        cost = stage["cost_sensitivity"]["10"]
        self.assertGreater(cost["net_mean"], 0)
        self.assertLess(cost["net_ci95_by_block"]["3"][0], 0)
        self.assertLess(cost["net_ci95_by_block"]["6"][0], 0)
        self.assertFalse(result["validation_strict_screen"]["60"]["10"]["strict_validation_pass"])

    def test_final_slice_is_explicitly_exposed_not_holdout(self):
        audit.BOOTSTRAP_REPS = 500
        input_path = Path("research/phase148_phase29_spread_series.json")
        with tempfile.TemporaryDirectory() as tmp:
            result = audit.run_audit(input_path, Path(tmp) / "audit.json")
        self.assertEqual(
            result["interpretation"]["final_oos_status"],
            "EXPOSED_EXPLORATORY_NOT_AN_UNTOUCHED_HOLDOUT",
        )
        self.assertEqual(result["interpretation"]["f80_comparison"], "NOT_PERFORMED")


if __name__ == "__main__":
    unittest.main()

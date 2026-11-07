import copy
import json
import unittest

from research.phase182_legacy_experiment_validity_audit import audit, DEFAULT_INPUT


class Phase182LegacyExperimentValidityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snapshot = json.loads(DEFAULT_INPUT.read_text(encoding="utf-8"))
        cls.result = audit(cls.snapshot)

    def test_phase_and_overall_status(self):
        self.assertEqual(self.result["phase"], 182)
        self.assertEqual(self.result["status"], "NO_LEGACY_SMART_MONEY_SIGNAL_PROMOTED")

    def test_finra_20c_file_coverage_is_incomplete(self):
        self.assertAlmostEqual(self.result["finra_20c"]["file_coverage"], 1382 / 2020)
        self.assertLess(self.result["finra_20c"]["file_coverage"], 0.70)

    def test_finra_20c_short_horizon_is_weak_and_inconsistent(self):
        x = self.result["finra_20c"]
        self.assertTrue(x["h5_median_negative"])
        self.assertLess(x["h5_positive_date_rate"], 0.50)
        self.assertLess(abs(x["h5_mean_to_std"]), 0.05)

    def test_finra_20c_longer_horizons_are_negative(self):
        x = self.result["finra_20c"]
        self.assertTrue(x["h10_mean_negative"])
        self.assertTrue(x["h20_mean_negative"])

    def test_finra_20b_is_not_confirmatory(self):
        x = self.result["finra_20b"]
        self.assertEqual(x["final_oos_dates"], 6)
        self.assertFalse(x["costs_included"])
        self.assertFalse(x["bootstrap_ci_available"])
        self.assertTrue(x["holdout_consumed"])

    def test_cftc_training_maturity_gap_is_detected(self):
        x = self.result["cftc_23c"]
        self.assertEqual(x["test_dates"], 12)
        self.assertEqual(x["immature_5d_test_dates"], 6)
        self.assertEqual(x["immature_5d_rows"], 6)
        self.assertEqual(x["immature_20d_test_dates"], 12)
        self.assertEqual(x["immature_20d_rows"], 42)
        self.assertFalse(x["training_embargo_present"])

    def test_form4_bootstrap_intervals_all_include_zero(self):
        x = self.result["sec_form4_21c"]
        self.assertTrue(x["all_bootstrap_intervals_cross_zero"])
        self.assertEqual(set(x["bootstrap_intervals_cross_zero"].values()), {True})

    def test_form4_residual_correlations_do_not_support_incremental_signal(self):
        self.assertTrue(self.result["sec_form4_21c"]["all_mean_residual_spearman_nonpositive"])

    def test_legacy_final_holdout_is_marked_consumed(self):
        x = self.result["holdout"]
        self.assertEqual(x["status"], "CONSUMED_NOT_PRISTINE")
        self.assertFalse(x["phase182_used_final_holdout"])
        self.assertEqual(len(x["dates"]), 6)

    def test_f80_and_production_controls_remain_unchanged(self):
        x = self.result["controls"]
        self.assertTrue(x["f80_frozen"])
        self.assertFalse(x["production_changed"])
        self.assertFalse(x["vendor_contact"])
        self.assertFalse(x["data_purchase"])

    def test_output_is_deterministic(self):
        self.assertEqual(self.result, audit(copy.deepcopy(self.snapshot)))


if __name__ == "__main__":
    unittest.main()

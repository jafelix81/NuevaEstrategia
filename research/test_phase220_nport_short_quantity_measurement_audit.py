import json
import unittest
from research.phase220_nport_short_quantity_measurement_audit import EVIDENCE, build_audit, quantity_change_pct


class Phase220NportQuantityMeasurementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        cls.result = build_audit(cls.evidence)

    def test_phase_and_primary_feature(self):
        self.assertEqual(self.evidence["phase"], 220)
        self.assertEqual(self.result["primary_feature"], "delta_short_shares_pct")

    def test_quantity_change_is_fixed_direction(self):
        self.assertEqual(quantity_change_pct(-100, -110), 10.0)

    def test_price_revaluation_does_not_look_like_new_shares(self):
        row = self.evidence["synthetic_counterexamples"]["unchanged_shares_price_rises_20pct"]
        self.assertEqual(row["delta_short_pct_nav_percentage_points"], 0.2)
        self.assertEqual(quantity_change_pct(-row["prior_shares"], -row["current_shares"]), 0.0)

    def test_nav_denominator_change_does_not_look_like_new_shares(self):
        row = self.evidence["synthetic_counterexamples"]["unchanged_shares_nav_falls"]
        self.assertEqual(row["delta_short_pct_nav_percentage_points"], 0.2)
        self.assertEqual(quantity_change_pct(-row["prior_shares"], -row["current_shares"]), 0.0)

    def test_real_quantity_increase_is_detected(self):
        row = self.evidence["synthetic_counterexamples"]["short_shares_increase_10pct"]
        self.assertEqual(row["delta_short_shares_pct"], 10)
        self.assertEqual(quantity_change_pct(-row["prior_shares"], -row["current_shares"]), 10.0)

    def test_split_adjustment_is_applied(self):
        self.assertEqual(quantity_change_pct(-100, -200, 0.5), 0.0)

    def test_non_short_or_zero_prior_fails_closed(self):
        with self.assertRaises(ValueError):
            quantity_change_pct(100, -110)
        with self.assertRaises(ValueError):
            quantity_change_pct(0, -110)

    def test_nav_delta_is_not_behavior(self):
        self.assertIn("exposure-state descriptor", self.evidence["supersedes"]["disposition"])
        self.assertEqual(self.result["nav_delta_role"], "EXPOSURE_STATE_ONLY_NOT_BEHAVIOR")

    def test_missing_rows_and_corporate_actions_are_conservative(self):
        self.assertIn("no zero imputation", self.evidence["measurement"]["zero_or_missing_prior"])
        self.assertIn("otherwise exclude", self.evidence["measurement"]["corporate_actions"])

    def test_pit_and_controls_remain_closed(self):
        p = self.evidence["point_in_time"]
        self.assertFalse(p["report_date_is_knowledge_time"])
        self.assertFalse(p["fixed_filing_lag"])
        c = self.evidence["controls"]
        self.assertTrue(c["f80_frozen"])
        self.assertFalse(c["alpha_test_run"])
        self.assertFalse(c["holdout_used"])
        self.assertEqual(c["legacy_holdout"], "CONSUMED_NOT_PRISTINE")


if __name__ == "__main__":
    unittest.main()

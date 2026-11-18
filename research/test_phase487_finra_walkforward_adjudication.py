import unittest
import pandas as pd

from research.phase487_finra_walkforward_adjudication import (
    phase20a_residual_summary, phase20b_date_differences, phase20b_tie_audit,
    phase20c_summary, summarize,
)


class Phase487AdjudicationTests(unittest.TestCase):
    def test_small_sample_summary_and_familywise_adjustment(self):
        r = summarize([1, 2, 3, 4, 5, 6], family_tests=21)
        self.assertEqual(r["n"], 6)
        self.assertEqual(r["positive_n"], 6)
        self.assertAlmostEqual(r["mean"], 3.5)
        self.assertAlmostEqual(r["sign_p_two_sided"], 0.03125)
        self.assertEqual(r["family_tests"], 21)
        self.assertAlmostEqual(r["bonferroni_p"], min(1.0, r["t_p_two_sided"] * 21))

    def test_zero_variance_is_not_mistaken_for_predictive_evidence(self):
        r = summarize([0, 0, 0, 0])
        self.assertEqual(r["std"], 0.0)
        self.assertEqual(r["t_p_two_sided"], 1.0)
        self.assertEqual(r["ci95_low"], 0.0)
        self.assertEqual(r["ci95_high"], 0.0)

    def test_phase20b_equal_weight_date_level_differences(self):
        rows = []
        for date, blocked, replacement in [("D1", [0.00, 0.02], [0.04, 0.06]),
                                            ("D2", [0.10, 0.12], [0.08, 0.10])]:
            for role, values in [("BLOCKED_F80", blocked), ("REPLACEMENT_NONF80", replacement)]:
                for value in values:
                    rows.append({"DateSignal": date, "Role": role, "FwdRet_5D": value,
                                 "FwdRet_10D": float("nan"), "FwdRet_20D": float("nan")})
        r = phase20b_date_differences(pd.DataFrame(rows))["5"]
        self.assertEqual(r["n"], 2)
        self.assertAlmostEqual(r["date_differences"][0]["replacement_minus_blocked"], 0.04)
        self.assertAlmostEqual(r["date_differences"][1]["replacement_minus_blocked"], -0.02)
        self.assertAlmostEqual(r["mean"], 0.01)
        self.assertEqual(r["family_tests"], 3)

    def test_phase20b_zero_ties_fail_continuous_rank_gate(self):
        df = pd.DataFrame({"Group": ["REPLACEMENT_NONF80"] * 4,
                           "RuleScore": [0.0, -0.0, 0.0, 0.0]})
        r = phase20b_tie_audit(df)
        self.assertEqual(r["replacement_rows"], 4)
        self.assertEqual(r["zero_score_rows"], 4)
        self.assertEqual(r["unique_score_values"], 1)
        self.assertFalse(r["continuous_rank_discriminates_replacements"])

    def test_phase20a_corrects_across_all_factor_horizon_combinations(self):
        df = pd.DataFrame([
            {"Factor": "A", "Horizon": 5, "SpearmanResidual": -0.10},
            {"Factor": "A", "Horizon": 5, "SpearmanResidual": -0.08},
            {"Factor": "B", "Horizon": 10, "SpearmanResidual": 0.02},
            {"Factor": "B", "Horizon": 10, "SpearmanResidual": 0.04},
        ])
        r = phase20a_residual_summary(df)
        self.assertEqual(len(r), 2)
        self.assertTrue(all(x["family_tests"] == 2 for x in r))
        self.assertAlmostEqual(r[0]["mean"], -0.09)

    def test_phase20c_groups_horizons_and_corrects_three_tests(self):
        df = pd.DataFrame([
            {"Horizon": 5, "DateSignal": "D1", "DeltaReplacementMinusBlocked": 0.01},
            {"Horizon": 5, "DateSignal": "D2", "DeltaReplacementMinusBlocked": -0.01},
            {"Horizon": 10, "DateSignal": "D1", "DeltaReplacementMinusBlocked": -0.02},
            {"Horizon": 10, "DateSignal": "D2", "DeltaReplacementMinusBlocked": -0.04},
        ])
        r = phase20c_summary(df)
        self.assertEqual(r["5"]["n"], 2)
        self.assertEqual(r["10"]["n"], 2)
        self.assertEqual(r["5"]["family_tests"], 3)
        self.assertAlmostEqual(r["10"]["mean"], -0.03)

    def test_missing_columns_fail_closed(self):
        with self.assertRaises(ValueError):
            phase20b_tie_audit(pd.DataFrame({"Group": ["x"]}))


if __name__ == "__main__":
    unittest.main()

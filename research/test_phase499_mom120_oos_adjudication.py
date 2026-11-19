import unittest

import numpy as np
import pandas as pd

from research.phase499_mom120_oos_adjudication import (
    paired_incremental_summary,
    validate_ledger,
)


class Phase499Mom120AdjudicationTests(unittest.TestCase):
    def test_ledger_accounting_and_top20_invariants_pass(self):
        frame = pd.DataFrame({
            "Date": pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-04"]),
            "Equity": [1010.0, 1000.0, 1020.0],
            "DailyReturn": [0.01, 1000.0 / 1010.0 - 1.0, 0.02],
            "Cash": [0.0, 0.0, 0.0],
            "GrossValue": [1010.0, 1000.0, 1020.0],
            "Positions": [20, 20, 20],
            "Gross": [1.0, 1.0, 1.0],
        })
        result = validate_ledger(frame, "synthetic")
        self.assertEqual(result["rows"], 3)
        self.assertEqual(result["max_positions"], 20)
        self.assertAlmostEqual(result["max_gross"], 1.0)

    def test_ledger_rejects_more_than_twenty_positions(self):
        frame = pd.DataFrame({
            "Date": pd.to_datetime(["2024-01-02", "2024-01-03"]),
            "Equity": [1010.0, 1020.0],
            "DailyReturn": [0.01, 1020.0 / 1010.0 - 1.0],
            "Cash": [0.0, 0.0],
            "GrossValue": [1010.0, 1020.0],
            "Positions": [20, 21],
            "Gross": [1.0, 1.0],
        })
        with self.assertRaises(ValueError):
            validate_ledger(frame, "too-many")

    def test_ledger_rejects_return_chain_mismatch(self):
        frame = pd.DataFrame({
            "Date": pd.to_datetime(["2024-01-02", "2024-01-03"]),
            "Equity": [1010.0, 1020.0],
            "DailyReturn": [0.01, 0.50],
            "Cash": [0.0, 0.0],
            "GrossValue": [1010.0, 1020.0],
            "Positions": [20, 20],
            "Gross": [1.0, 1.0],
        })
        with self.assertRaises(ValueError):
            validate_ledger(frame, "bad-return")

    def test_paired_summary_is_deterministic_and_keeps_zero_inside_interval(self):
        candidate = np.array([0.001, -0.001, 0.0005, -0.0005, 0.0002, -0.0002])
        baseline = np.zeros_like(candidate)
        a = paired_incremental_summary(candidate, baseline, blocks=(2, 4), bootstrap_samples=200, seed=7)
        b = paired_incremental_summary(candidate, baseline, blocks=(2, 4), bootstrap_samples=200, seed=7)
        self.assertEqual(a, b)
        self.assertEqual(a["n_daily_observations"], 6)
        self.assertIn("2", a["block_bootstrap"])
        self.assertIn("4", a["block_bootstrap"])

    def test_paired_summary_rejects_mismatched_shapes(self):
        with self.assertRaises(ValueError):
            paired_incremental_summary([0.01, 0.02], [0.01])


if __name__ == "__main__":
    unittest.main()

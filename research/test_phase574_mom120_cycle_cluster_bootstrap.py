import unittest

from research.phase574_mom120_cycle_cluster_bootstrap import (
    exact_one_sided_sign_p,
    summarize_clusters,
)


class Phase574Tests(unittest.TestCase):
    def test_exact_sign_test(self):
        self.assertAlmostEqual(exact_one_sided_sign_p(8, 9), 10 / 512)
        self.assertAlmostEqual(exact_one_sided_sign_p(8, 10), 56 / 1024)

    def test_cluster_bootstrap_is_deterministic(self):
        records = [
            {"sessions": 80, "mean_daily_excess": 0.001, "relative_log_return": 0.08},
            {"sessions": 80, "mean_daily_excess": 0.0005, "relative_log_return": 0.04},
            {"sessions": 75, "mean_daily_excess": -0.0001, "relative_log_return": -0.01},
        ]
        a = summarize_clusters(records, draws=5000, seed=123)
        b = summarize_clusters(records, draws=5000, seed=123)
        self.assertEqual(a, b)
        self.assertEqual(a["clusters"], 3)
        self.assertEqual(a["positive_relative_cycles"], 2)

    def test_leave_one_out_is_cluster_level(self):
        records = [
            {"sessions": 80, "mean_daily_excess": 0.001, "relative_log_return": 0.08},
            {"sessions": 80, "mean_daily_excess": 0.0005, "relative_log_return": 0.04},
            {"sessions": 75, "mean_daily_excess": -0.0001, "relative_log_return": -0.01},
        ]
        result = summarize_clusters(records, draws=5000, seed=123)
        self.assertAlmostEqual(result["minimum_leave_one_cycle_out_mean_bps"], 2.0)


if __name__ == "__main__":
    unittest.main()

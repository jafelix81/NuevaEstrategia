import unittest
import numpy as np

from research.phase428_mom120_recent_segment_bootstrap_audit import (
    circular_block_bootstrap,
    hac_se,
)


class Phase428Tests(unittest.TestCase):
    def test_circular_bootstrap_is_reproducible(self):
        x = np.linspace(-0.01, 0.02, 240)
        a = circular_block_bootstrap(x, 20, 1000, 428020)
        b = circular_block_bootstrap(x, 20, 1000, 428020)
        self.assertEqual(a, b)

    def test_circular_bootstrap_preserves_sample_mean(self):
        x = np.sin(np.arange(240) / 13.0)
        result = circular_block_bootstrap(x, 20, 1000, 428021)
        self.assertAlmostEqual(result["mean"], float(x.mean()), places=14)

    def test_hac_constant_series_has_zero_standard_error(self):
        self.assertEqual(hac_se(np.ones(100), 20), 0.0)

    def test_hac_rejects_nonfinite_values(self):
        with self.assertRaises(ValueError):
            hac_se(np.array([1.0, np.nan] + [0.0] * 50), 20)


if __name__ == "__main__":
    unittest.main()

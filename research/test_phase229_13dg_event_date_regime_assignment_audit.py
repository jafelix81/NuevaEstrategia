import unittest
from datetime import date

from phase229_13dg_event_date_regime_assignment_audit import assign_regimes, weighted_quantile


class Phase229Tests(unittest.TestCase):
    def test_13d_cutoff_is_family_specific(self):
        self.assertEqual(assign_regimes("13D", date(2024, 2, 4), date(2024, 2, 4)), ("pre", "pre"))
        self.assertEqual(assign_regimes("13D", date(2024, 2, 5), date(2024, 2, 5)), ("post", "post"))

    def test_13g_cutoff_is_family_specific(self):
        self.assertEqual(assign_regimes("13G", date(2024, 9, 29), date(2024, 9, 29)), ("pre", "pre"))
        self.assertEqual(assign_regimes("13G", date(2024, 9, 30), date(2024, 9, 30)), ("post", "post"))

    def test_event_date_unknown_is_not_imputed(self):
        self.assertEqual(assign_regimes("13D", date(2024, 2, 8), None), ("post", "unknown"))

    def test_filing_after_cutoff_event_before_cutoff_is_crossing(self):
        self.assertEqual(assign_regimes("13D", date(2024, 2, 8), date(2024, 1, 31)), ("post", "pre"))

    def test_event_date_on_cutoff_is_post(self):
        self.assertEqual(assign_regimes("13G", date(2024, 10, 1), date(2024, 9, 30)), ("post", "post"))

    def test_weighted_quantile(self):
        self.assertEqual(weighted_quantile([1, 2, 3], [1, 8, 1], 0.5), 2.0)
        self.assertEqual(weighted_quantile([1, 2, 3], [1, 8, 1], 0.9), 2.0)

    def test_empty_weighted_quantile(self):
        self.assertIsNone(weighted_quantile([], [], 0.5))

    def test_unsupported_family_fails_closed(self):
        with self.assertRaises(ValueError):
            assign_regimes("13F", date(2024, 1, 1), date(2024, 1, 1))


if __name__ == "__main__":
    unittest.main()

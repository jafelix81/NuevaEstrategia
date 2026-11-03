import unittest
from phase35_13dg_crosswalk_precision_validation import normalize_cik, precision_label


class CrosswalkPrecisionTests(unittest.TestCase):
    def test_normalizes_numeric_cik(self):
        self.assertEqual(normalize_cik("19617.0"), "0000019617")

    def test_13d_explicit_cik_match(self):
        self.assertEqual(precision_label("13D", "1032666", "0001032666"), (True, True, False))

    def test_13d_explicit_cik_mismatch(self):
        self.assertEqual(precision_label("13D", "1032666", "0001106636"), (True, False, True))

    def test_13g_is_coverage_only(self):
        self.assertEqual(precision_label("13G", "19617", None), (False, False, False))

    def test_13d_without_explicit_cik_is_not_validated(self):
        self.assertEqual(precision_label("13D", "19617", None), (False, False, False))


if __name__ == "__main__":
    unittest.main()

import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("phase116_cboe_market_volume_audit.py")
spec = importlib.util.spec_from_file_location("phase116", MODULE_PATH)
phase116 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(phase116)


class Phase116Tests(unittest.TestCase):
    def test_daily_header_and_arithmetic(self):
        header = ",".join(phase116.DAILY_HEADER)
        row = "2026-01-02,FINRA / Nasdaq TRF Carteret,1,2,3,6,10,20,30,60,1,2,3,6"
        parsed = phase116.parse_csv((header + "\n" + row + "\n").encode(), "daily", 2026)
        self.assertEqual(parsed["rows"], 1)
        self.assertEqual(len(parsed["dates"]), 1)
        self.assertIn("FINRA / Nasdaq TRF Carteret", parsed["participants"])

    def test_monthly_header_and_arithmetic(self):
        header = ",".join(phase116.MONTHLY_HEADER)
        row = "2026-01,NYSE,1,2,3,6,10,20,30,60,1,2,3,6"
        parsed = phase116.parse_csv((header + "\n" + row + "\n").encode(), "monthly", 2026)
        self.assertEqual(parsed["rows"], 1)

    def test_duplicate_key_rejected(self):
        header = ",".join(phase116.DAILY_HEADER)
        row = "2026-01-02,NYSE,1,2,3,6,10,20,30,60,1,2,3,6"
        with self.assertRaisesRegex(ValueError, "duplicate"):
            phase116.parse_csv((header + "\n" + row + "\n" + row + "\n").encode(), "daily", 2026)

    def test_arithmetic_mismatch_rejected(self):
        header = ",".join(phase116.DAILY_HEADER)
        row = "2026-01-02,NYSE,1,2,3,7,10,20,30,60,1,2,3,6"
        with self.assertRaisesRegex(ValueError, "arithmetic"):
            phase116.parse_csv((header + "\n" + row + "\n").encode(), "daily", 2026)

    def test_negative_value_rejected(self):
        header = ",".join(phase116.DAILY_HEADER)
        row = "2026-01-02,NYSE,1,2,-3,0,10,20,30,60,1,2,3,6"
        with self.assertRaisesRegex(ValueError, "negative"):
            phase116.parse_csv((header + "\n" + row + "\n").encode(), "daily", 2026)

    def test_monthly_daily_reconciliation(self):
        # Exercise the reconciliation function directly with parsed fixture objects.
        dh = ",".join(phase116.DAILY_HEADER)
        mh = ",".join(phase116.MONTHLY_HEADER)
        dr = "2026-01-02,NYSE,1,2,3,6,10,20,30,60,1,2,3,6"
        mr = "2026-01,NYSE,1,2,3,6,10,20,30,60,1,2,3,6"
        daily = phase116.parse_csv((dh + "\n" + dr + "\n").encode(), "daily", 2026)
        monthly = phase116.parse_csv((mh + "\n" + mr + "\n").encode(), "monthly", 2026)
        # January is incomplete relative to current month only if current month is January.
        result = phase116.compare_monthly(daily, monthly, 2026, "2026-02")
        self.assertEqual(result["mismatch_count"], 0)
        self.assertEqual(result["participant_month_comparisons"], 1)

    def test_year_mismatch_rejected(self):
        header = ",".join(phase116.DAILY_HEADER)
        row = "2025-12-31,NYSE,1,2,3,6,10,20,30,60,1,2,3,6"
        with self.assertRaisesRegex(ValueError, "outside requested year"):
            phase116.parse_csv((header + "\n" + row + "\n").encode(), "daily", 2026)


if __name__ == "__main__":
    unittest.main()

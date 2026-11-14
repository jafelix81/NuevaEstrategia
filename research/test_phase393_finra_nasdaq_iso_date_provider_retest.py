import unittest

from research.phase393_finra_nasdaq_iso_date_provider_retest import (
    START, END_EXCLUSIVE, validate_iso_window, parse_nasdaq_payload,
    compare_daily_returns, public_record,
)


class Phase393Tests(unittest.TestCase):
    def test_fixed_window_is_iso(self):
        self.assertTrue(validate_iso_window())
        self.assertEqual(START, "2016-10-24")
        self.assertEqual(END_EXCLUSIVE, "2026-10-24")

    def test_rejects_slash_dates(self):
        self.assertFalse(validate_iso_window("10/24/2016", "10/24/2026"))

    def test_parse_nasdaq_trades_table(self):
        payload = {
            "status": {"rCode": 200, "bCodeMessage": None},
            "data": {
                "tradesTable": {
                    "headers": {"date": "Date", "close": "Close/Last"},
                    "totalRecords": 2,
                    "rows": [
                        {"date": "01/03/2024", "close": "$101.25"},
                        {"date": "01/02/2024", "close": "$100.00"},
                    ],
                }
            },
        }
        parsed = parse_nasdaq_payload(payload)
        self.assertEqual(parsed["reported_row_count"], 2)
        self.assertEqual(parsed["total_records"], 2)
        self.assertEqual(list(parsed["series"]), ["2024-01-02", "2024-01-03"])
        self.assertAlmostEqual(parsed["series"]["2024-01-03"], 101.25)

    def test_empty_or_changed_schema_is_not_silent_success(self):
        parsed = parse_nasdaq_payload({"data": {"message": "unavailable"}})
        self.assertEqual(parsed["series"], {})
        self.assertEqual(parsed["reported_row_count"], 0)
        self.assertEqual(parsed["response_message"], "unavailable")

    def test_daily_return_concordance(self):
        left = {f"2024-01-{day:02d}": 100.0 + day for day in range(1, 32)}
        right = {day: value * 2 for day, value in left.items()}
        result = compare_daily_returns(left, right)
        self.assertEqual(result["common_dates"], 31)
        self.assertEqual(result["return_pairs"], 30)
        self.assertAlmostEqual(result["median_abs_return_diff"], 0.0, places=12)
        self.assertAlmostEqual(result["return_corr"], 1.0, places=12)

    def test_no_prices_in_public_artifact_record(self):
        record = {"ticker": "AAPL", "rows": 2, "_series": {"2024-01-02": 100.0}}
        public = public_record(record)
        self.assertEqual(public, {"ticker": "AAPL", "rows": 2})
        self.assertNotIn("_series", public)


if __name__ == "__main__":
    unittest.main()

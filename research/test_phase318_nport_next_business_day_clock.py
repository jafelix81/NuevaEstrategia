import unittest
from datetime import date

from research.phase318_nport_next_business_day_clock import (
    classify_clock,
    is_edgar_business_day,
    next_edgar_business_day,
    us_federal_holidays,
)


class EdgarBusinessCalendarTests(unittest.TestCase):
    def test_friday_rolls_to_monday(self):
        self.assertEqual(next_edgar_business_day(date(2020, 1, 10)), date(2020, 1, 13))

    def test_thanksgiving_rolls_to_friday(self):
        self.assertEqual(next_edgar_business_day(date(2020, 11, 25)), date(2020, 11, 27))

    def test_juneteenth_observed_holiday_is_skipped(self):
        self.assertEqual(next_edgar_business_day(date(2022, 6, 17)), date(2022, 6, 21))

    def test_new_year_observed_on_prior_year_friday_is_skipped(self):
        self.assertEqual(next_edgar_business_day(date(2021, 12, 30)), date(2022, 1, 3))

    def test_good_friday_is_not_a_federal_holiday(self):
        self.assertNotIn(date(2021, 4, 2), us_federal_holidays(2021))
        self.assertTrue(is_edgar_business_day(date(2021, 4, 2)))


class FilingClockTests(unittest.TestCase):
    def test_after_cutoff_next_business_day_is_consistent_not_proof(self):
        result = classify_clock("20200110181828", "2020-01-13")
        self.assertEqual(
            result["classification"],
            "NEXT_EDGAR_BUSINESS_DAY_CONSISTENT_NOT_PROOF_OF_TRANSMISSION_START",
        )
        self.assertTrue(result["filed_date_matches_next_edgar_business_day"])
        self.assertFalse(result["transmission_start_time_observed"])

    def test_same_date_after_cutoff_remains_unresolved(self):
        result = classify_clock("20200730194048", "2020-07-30")
        self.assertEqual(
            result["classification"],
            "SAME_FILED_DATE_ACCEPTANCE_AFTER_1730_TRANSMISSION_START_UNOBSERVED",
        )
        self.assertFalse(result["filed_date_matches_next_edgar_business_day"])

    def test_before_cutoff_same_date(self):
        result = classify_clock("20201125143747", "2020-11-25")
        self.assertEqual(result["classification"], "SAME_CALENDAR_DATE_ACCEPTANCE_BEFORE_1730")

    def test_before_cutoff_date_shift_is_not_explained(self):
        result = classify_clock("20201125143747", "2020-11-27")
        self.assertEqual(
            result["classification"],
            "UNEXPLAINED_DATE_SHIFT_WITH_ACCEPTANCE_BEFORE_1730",
        )

    def test_filed_date_before_acceptance_is_invalid(self):
        result = classify_clock("20201125143747", "2020-11-24")
        self.assertEqual(result["classification"], "INVALID_FILED_DATE_PRECEDES_ACCEPTANCE_DATE")


if __name__ == "__main__":
    unittest.main()

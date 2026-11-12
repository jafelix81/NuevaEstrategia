import unittest

from research.phase317_nport_filing_clock_adjudication import (
    classify_filing_clock,
    lag_summary,
    percentile,
)


class FilingClockTests(unittest.TestCase):
    def test_same_day_before_cutoff(self):
        result = classify_filing_clock("20201125143747", "2020-11-25")
        self.assertEqual(result["classification"], "SAME_CALENDAR_DATE")
        self.assertEqual(result["calendar_day_shift"], 0)
        self.assertFalse(result["acceptance_at_or_after_1730_et"])

    def test_after_cutoff_with_next_filed_date(self):
        result = classify_filing_clock("20191126203100", "2019-11-27")
        self.assertEqual(
            result["classification"],
            "NEXT_FILED_DATE_AFTER_1730_CONSISTENT_WITH_SEC_RULE",
        )
        self.assertEqual(result["calendar_day_shift"], 1)
        self.assertTrue(result["acceptance_at_or_after_1730_et"])

    def test_friday_after_cutoff_with_monday_filed_date(self):
        result = classify_filing_clock("20200110181828", "2020-01-13")
        self.assertEqual(result["calendar_day_shift"], 3)
        self.assertEqual(
            result["classification"],
            "NEXT_FILED_DATE_AFTER_1730_CONSISTENT_WITH_SEC_RULE",
        )

    def test_after_cutoff_same_filed_date_is_not_assumed_public_same_evening(self):
        result = classify_filing_clock("20200730194048", "2020-07-30")
        self.assertEqual(
            result["classification"],
            "SAME_FILED_DATE_ACCEPTED_AFTER_1730_START_TIME_UNRESOLVED",
        )
        self.assertEqual(result["calendar_day_shift"], 0)

    def test_pre_cutoff_date_shift_is_unexplained(self):
        result = classify_filing_clock("20201125143747", "2020-11-27")
        self.assertEqual(
            result["classification"],
            "UNEXPLAINED_DATE_SHIFT_BEFORE_1730",
        )

    def test_filed_date_before_acceptance_is_invalid(self):
        result = classify_filing_clock("20201125143747", "2020-11-24")
        self.assertEqual(
            result["classification"],
            "INVALID_FILED_DATE_PRECEDES_ACCEPTANCE_DATE",
        )


class LagSummaryTests(unittest.TestCase):
    def test_percentile_interpolation(self):
        self.assertEqual(percentile([10, 20, 30, 40], 0.5), 25.0)

    def test_amendment_lag_summary_counts_thresholds(self):
        rows = [
            {"form_type": "NPORT-P/A", "report_date": "2020-01-01", "master_index_filing_date": "2020-03-01"},
            {"form_type": "NPORT-P/A", "report_date": "2020-01-01", "master_index_filing_date": "2020-07-01"},
            {"form_type": "NPORT-P/A", "report_date": "2020-01-01", "master_index_filing_date": "2021-02-01"},
            {"form_type": "NPORT-P", "report_date": "2020-01-01", "master_index_filing_date": "2020-02-01"},
        ]
        result = lag_summary(rows, "NPORT-P/A")
        self.assertEqual(result["n"], 3)
        self.assertEqual(result["at_least_90_days"], 2)
        self.assertEqual(result["at_least_180_days"], 2)
        self.assertEqual(result["at_least_365_days"], 1)


if __name__ == "__main__":
    unittest.main()

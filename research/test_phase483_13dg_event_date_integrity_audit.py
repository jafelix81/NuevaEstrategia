import unittest

from research.phase483_13dg_event_date_integrity_audit import classify_event_date, summarize_rows


class EventDateClassificationTests(unittest.TestCase):
    def test_prior_event_is_before_filing(self):
        self.assertEqual(classify_event_date("2024-02-09", "2024-02-08"), "BEFORE_FILING")

    def test_same_day_event_is_explicit(self):
        self.assertEqual(classify_event_date("2024-02-09", "2024-02-09"), "SAME_DAY")

    def test_future_event_is_not_hidden_as_missing_lag(self):
        self.assertEqual(classify_event_date("2024-02-09", "2024-12-31"), "AFTER_FILING_UNRESOLVED")

    def test_missing_event_date_is_distinct(self):
        self.assertEqual(classify_event_date("2024-02-09", ""), "MISSING_EVENT_DATE")

    def test_invalid_event_date_is_distinct(self):
        self.assertEqual(classify_event_date("2024-02-09", "2024-02-30"), "INVALID_EVENT_DATE")

    def test_invalid_filing_date_fails_closed(self):
        self.assertEqual(classify_event_date("not-a-date", "2024-02-08"), "INVALID_OR_MISSING_FILING_DATE")

    def test_future_event_count_survives_null_business_day_lag(self):
        rows = [
            {"form":"SC 13G","filing_date":"2024-02-09","event_date":"2024-12-31","filing_lag_business_days":"","accession":"0000895421-24-000126"},
            {"form":"SC 13G","filing_date":"2024-02-12","event_date":"2024-12-31","filing_lag_business_days":"","accession":"0000895421-24-000178"},
            {"form":"SC 13D","filing_date":"2024-02-12","event_date":"2024-02-10","filing_lag_business_days":"1","accession":"0000000000-24-000001"},
        ]
        result = summarize_rows(rows)
        self.assertEqual(result["event_date_relation_counts"]["AFTER_FILING_UNRESOLVED"], 2)
        self.assertEqual(result["filing_lag_business_days_missing_when_event_date_valid"], 2)
        self.assertEqual(result["future_event_rows_by_form"], {"SC 13G": 2})
        self.assertFalse(result["signal_eligible"])
        self.assertFalse(result["forward_returns_used"])

    def test_duplicate_accessions_are_counted_not_silently_collapsed(self):
        row = {"form":"SC 13D","filing_date":"2024-02-12","event_date":"2024-02-10","filing_lag_business_days":"1","accession":"0000000000-24-000001"}
        result = summarize_rows([row, row])
        self.assertEqual(result["rows"], 2)
        self.assertEqual(result["unique_accessions"], 1)
        self.assertEqual(result["duplicate_accession_rows"], 1)

    def test_missing_and_future_dates_reconcile(self):
        rows = [
            {"form":"SC 13D","filing_date":"2024-02-12","event_date":"2024-02-10","accession":"a"},
            {"form":"SC 13G","filing_date":"2024-02-12","event_date":"2024-12-31","accession":"b"},
            {"form":"SC 13G/A","filing_date":"2024-02-12","event_date":"","accession":"c"},
        ]
        result = summarize_rows(rows)
        counts = result["event_date_relation_counts"]
        self.assertEqual(sum(counts.values()), 3)
        self.assertEqual(result["event_date_valid_count"], 2)
        self.assertEqual(result["event_date_missing_count"], 1)
        self.assertEqual(result["event_date_coverage_pct"], 66.67)


if __name__ == "__main__":
    unittest.main()

import unittest
from datetime import date

from research.phase368_finra_revision_lag_pit_audit import (
    DateAccumulator,
    LagAccumulator,
    analyze_rows,
    build_query,
    parse_date,
    parse_rows,
)


class Phase368Tests(unittest.TestCase):
    def test_historic_query_uses_historical_week_and_tier(self):
        query = build_query("weeklySummaryHistoric", "2025-10-20", "T1", 5000, 10000)
        filters = {item["fieldName"]: item["fieldValue"] for item in query["compareFilters"]}
        self.assertEqual(filters["historicalWeek"], "2025-10-20")
        self.assertEqual(filters["tierIdentifier"], "T1")
        self.assertEqual(query["offset"], 10000)

    def test_rejects_non_historic_dataset(self):
        with self.assertRaises(ValueError):
            build_query("weeklySummary", "2025-10-20", "T1", 5000, 0)

    def test_parse_date_accepts_date_and_timestamp(self):
        self.assertEqual(parse_date("2025-10-20"), date(2025, 10, 20))
        self.assertEqual(parse_date("2025-10-20T23:59:59Z"), date(2025, 10, 20))

    def test_parse_date_rejects_invalid_and_missing(self):
        self.assertIsNone(parse_date(None))
        self.assertIsNone(parse_date(""))
        self.assertIsNone(parse_date("not-a-date"))

    def test_lag_accumulator_positive_zero_negative_and_missing(self):
        acc = LagAccumulator()
        acc.add("2025-01-01", "2025-01-31")
        acc.add("2025-01-01", "2025-01-01")
        acc.add("2025-01-02", "2025-01-01")
        acc.add(None, "2025-01-03")
        result = acc.summary()
        self.assertEqual(result["comparable_rows"], 3)
        self.assertEqual(result["positive_gap_rows"], 1)
        self.assertEqual(result["zero_gap_rows"], 1)
        self.assertEqual(result["negative_gap_rows"], 1)
        self.assertEqual(result["missing_base"], 1)
        self.assertEqual(result["maximum_days"], 30)
        self.assertEqual(result["threshold_counts"]["gte_30_days"], 1)

    def test_lag_percentiles_are_monotone(self):
        acc = LagAccumulator()
        for day in range(1, 101):
            month = 1 + (day - 1) // 28
            day_of_month = 1 + (day - 1) % 28
            acc.add("2025-01-01", f"2025-{month:02d}-{day_of_month:02d}")
        result = acc.summary()
        self.assertLessEqual(result["p50_days_nearest_rank"], result["p90_days_nearest_rank"])
        self.assertLessEqual(result["p90_days_nearest_rank"], result["p99_days_nearest_rank"])

    def test_date_accumulator_reports_missing_invalid_and_range(self):
        acc = DateAccumulator()
        acc.add("2025-01-01")
        acc.add("2025-01-02")
        acc.add(None)
        acc.add("bad")
        result = acc.summary()
        self.assertEqual(result["rows"], 4)
        self.assertEqual(result["missing"], 1)
        self.assertEqual(result["invalid"], 1)
        self.assertEqual(result["distinct_dates"], 2)
        self.assertEqual(result["maximum_date"], "2025-01-02")

    def test_analyze_rows_outputs_aggregate_counts_only(self):
        rows = [
            {
                "summaryTypeCode": "ATS_W_SMBL",
                "issueSymbolIdentifier": "SECRET_SYMBOL",
                "MPID": None,
                "firmCRDNumber": None,
                "marketParticipantName": None,
                "weekStartDate": "2025-10-20",
                "initialPublishedDate": "2025-11-03",
                "lastUpdateDate": "2026-09-30",
                "lastReportedDate": "2025-10-31",
            },
            {
                "summaryTypeCode": "ATS_W_SMBL_FIRM",
                "issueSymbolIdentifier": "OTHER_SECRET",
                "MPID": "SECRET_MPID",
                "firmCRDNumber": "12345",
                "marketParticipantName": "Firm Name",
                "weekStartDate": "2025-10-20",
                "initialPublishedDate": "2025-11-03",
                "lastUpdateDate": "2025-11-03",
                "lastReportedDate": "2025-10-31",
            },
        ]
        result = analyze_rows(rows, "2025-10-20", "T1")
        self.assertEqual(result["rows_retrieved"], 2)
        self.assertEqual(result["unique_symbols_count_only"], 2)
        self.assertEqual(result["participant_id_rows"], 1)
        self.assertEqual(result["summary_type_counts"]["ATS_W_SMBL"], 1)
        self.assertEqual(
            result["date_gap_distributions"]["lastUpdateDate_minus_initialPublishedDate"]["all_rows"]["positive_gap_rows"],
            1,
        )
        serialized = str(result)
        self.assertNotIn("SECRET_SYMBOL", serialized)
        self.assertNotIn("SECRET_MPID", serialized)
        self.assertNotIn("Firm Name", serialized)

    def test_parse_rows_supports_list_and_wrapped_payload(self):
        self.assertEqual(parse_rows([{"a": 1}]), [{"a": 1}])
        self.assertEqual(parse_rows({"data": [{"a": 1}]}), [{"a": 1}])
        self.assertEqual(parse_rows({"data": {"data": [{"a": 1}]} }), [{"a": 1}])


if __name__ == "__main__":
    unittest.main()

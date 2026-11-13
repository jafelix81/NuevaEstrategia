import unittest
from collections import Counter

from research.phase367_finra_t1_field_level_vintage_diagnostic import (
    build_query,
    canonical_row,
    compare_key_maps,
    decimal_text,
    decimal_value,
    identity_key_fingerprint,
    row_json,
)


class Phase367Tests(unittest.TestCase):
    def test_historic_query_uses_historical_week(self):
        query = build_query("weeklySummaryHistoric", "2025-10-20", "T1", 5000, 5000)
        filters = {item["fieldName"]: item["fieldValue"] for item in query["compareFilters"]}
        self.assertEqual(filters["historicalWeek"], "2025-10-20")
        self.assertEqual(query["offset"], 5000)

    def test_current_query_uses_week_start_date(self):
        query = build_query("weeklySummary", "2025-10-20", "T1", 5000, 0)
        filters = {item["fieldName"]: item["fieldValue"] for item in query["compareFilters"]}
        self.assertEqual(filters["weekStartDate"], "2025-10-20")

    def test_summary_start_date_is_compared_but_query_helper_is_not(self):
        row = {"summaryStartDate": "2025-10-20", "historicalweek": "2025-10-20"}
        result = canonical_row(row)
        self.assertIn("summaryStartDate", result)
        self.assertNotIn("historicalweek", result)

    def test_decimal_scale_normalizes(self):
        self.assertEqual(decimal_text(decimal_value("1.000000")), "1")
        self.assertEqual(decimal_text(decimal_value("1.0")), "1")
        self.assertEqual(decimal_value("1.000000"), decimal_value("1"))

    def test_row_json_is_order_independent(self):
        a = {"summaryTypeCode": "ATS_W_SMBL", "totalNotionalSum": "1.000000"}
        b = {"totalNotionalSum": "1", "summaryTypeCode": "ATS_W_SMBL"}
        self.assertEqual(row_json(a), row_json(b))

    def test_compare_reports_notional_only_difference(self):
        current = {
            "summaryTypeCode": "ATS_W_SMBL", "issueSymbolIdentifier": "ABC",
            "MPID": "M1", "summaryStartDate": "2025-10-20",
            "totalNotionalSum": "100.000001", "totalWeeklyShareQuantity": "10",
        }
        historic = dict(current, totalNotionalSum="100.000000")
        key = identity_key_fingerprint(current)
        result = compare_key_maps({key: [canonical_row(current)]}, {key: [canonical_row(historic)]})
        self.assertEqual(result["field_mismatch_counts"], {"totalNotionalSum": 1})
        self.assertEqual(result["rows_differing_only_in_totalNotionalSum"], 1)
        self.assertEqual(result["rows_with_other_field_differences"], 0)
        self.assertEqual(result["numeric_field_differences"]["totalNotionalSum"]["mismatched_rows"], 1)

    def test_compare_detects_last_reported_date_as_field(self):
        current = {
            "summaryTypeCode": "ATS_W_SMBL", "issueSymbolIdentifier": "ABC",
            "MPID": "M1", "summaryStartDate": "2025-10-20",
            "lastReportedDate": "2025-10-24",
        }
        historic = dict(current, lastReportedDate="2025-10-23")
        key = identity_key_fingerprint(current)
        result = compare_key_maps({key: [canonical_row(current)]}, {key: [canonical_row(historic)]})
        self.assertEqual(result["field_mismatch_counts"], {"lastReportedDate": 1})
        self.assertFalse(result["selected_field_exact_match"])

    def test_key_groups_do_not_retain_raw_identifiers(self):
        row = {
            "summaryTypeCode": "ATS_W_SMBL", "issueSymbolIdentifier": "SECRET_SYMBOL",
            "MPID": "SECRET_MPID", "summaryStartDate": "2025-10-20",
        }
        key = identity_key_fingerprint(row)
        result = compare_key_maps({key: [canonical_row(row)]}, {key: [canonical_row(row)]})
        self.assertNotIn("SECRET_SYMBOL", str(result))
        self.assertNotIn("SECRET_MPID", str(result))
        self.assertFalse(result["raw_keys_retained"])
        self.assertTrue(result["selected_field_exact_match"])


if __name__ == "__main__":
    unittest.main()

import unittest
from collections import Counter

from research.phase366_finra_full_row_vintage_reconciliation import (
    build_query,
    canonical_row,
    compare_vintages,
    identity_key_fingerprint,
    row_fingerprint,
    summarise_rows,
)


class Phase366Tests(unittest.TestCase):
    def test_historic_query_uses_historical_week(self):
        query = build_query("weeklySummaryHistoric", "2025-10-20", "OTCE", 5000, 10000)
        filters = {item["fieldName"]: item["fieldValue"] for item in query["compareFilters"]}
        self.assertEqual(filters["historicalWeek"], "2025-10-20")
        self.assertEqual(filters["tierIdentifier"], "OTCE")
        self.assertEqual(query["offset"], 10000)

    def test_current_query_uses_week_start_date(self):
        query = build_query("weeklySummary", "2025-10-20", "T1", 5000, 5000)
        filters = {item["fieldName"]: item["fieldValue"] for item in query["compareFilters"]}
        self.assertEqual(filters["weekStartDate"], "2025-10-20")
        self.assertEqual(filters["tierIdentifier"], "T1")
        self.assertEqual(query["limit"], 5000)

    def test_canonical_row_is_field_order_independent(self):
        left = {"summaryTypeCode": "ATS_W_SMBL", "totalWeeklyShareQuantity": "1.0"}
        right = {"totalWeeklyShareQuantity": 1, "summaryTypeCode": "ATS_W_SMBL"}
        self.assertEqual(canonical_row(left), canonical_row(right))
        self.assertEqual(row_fingerprint(left), row_fingerprint(right))

    def test_row_fingerprint_detects_numeric_difference(self):
        left = {"summaryTypeCode": "ATS_W_SMBL", "totalWeeklyShareQuantity": "10"}
        right = {"summaryTypeCode": "ATS_W_SMBL", "totalWeeklyShareQuantity": "11"}
        self.assertNotEqual(row_fingerprint(left), row_fingerprint(right))

    def test_compare_vintages_is_order_independent(self):
        rows = [
            {"summaryTypeCode": "ATS_W_SMBL", "issueSymbolIdentifier": "ABC",
             "MPID": "M1", "totalWeeklyShareQuantity": "10"},
            {"summaryTypeCode": "ATS_W_SMBL", "issueSymbolIdentifier": "XYZ",
             "MPID": "M2", "totalWeeklyShareQuantity": "20"},
        ]
        current_hashes = Counter(row_fingerprint(row) for row in rows)
        historic_hashes = Counter(row_fingerprint(row) for row in reversed(rows))
        current_keys = {}
        historic_keys = {}
        for row in rows:
            key = identity_key_fingerprint(row)
            current_keys.setdefault(key, Counter())[row_fingerprint(row)] += 1
            historic_keys.setdefault(key, Counter())[row_fingerprint(row)] += 1
        summary = {
            "record_total": 2, "rows_retrieved": 2, "returned_fields": ["MPID"],
            "numeric_totals_by_summary_type": {}, "participant_id_rows": 2,
            "de_minimis_rows": 0, "row_multiset_sha256": "same",
        }
        result = compare_vintages(
            current_hashes, historic_hashes, current_keys, historic_keys, summary, summary
        )
        self.assertTrue(result["exact_row_multiset_match"])
        self.assertEqual(result["exact_rows_matched"], 2)

    def test_compare_vintages_detects_identity_and_value_mismatch(self):
        current = {"summaryTypeCode": "ATS_W_SMBL", "issueSymbolIdentifier": "ABC",
                   "MPID": "M1", "totalWeeklyShareQuantity": "10"}
        historic = {"summaryTypeCode": "ATS_W_SMBL", "issueSymbolIdentifier": "ABC",
                    "MPID": "M1", "totalWeeklyShareQuantity": "11"}
        current_hashes = Counter([row_fingerprint(current)])
        historic_hashes = Counter([row_fingerprint(historic)])
        current_key = identity_key_fingerprint(current)
        historic_key = identity_key_fingerprint(historic)
        summary_current = {
            "record_total": 1, "rows_retrieved": 1, "returned_fields": [],
            "numeric_totals_by_summary_type": {}, "participant_id_rows": 1,
            "de_minimis_rows": 0, "row_multiset_sha256": "a",
        }
        summary_historic = dict(summary_current, row_multiset_sha256="b")
        result = compare_vintages(
            current_hashes, historic_hashes,
            {current_key: current_hashes}, {historic_key: historic_hashes},
            summary_current, summary_historic,
        )
        self.assertFalse(result["exact_row_multiset_match"])
        self.assertEqual(result["current_only_rows"], 1)
        self.assertEqual(result["historic_only_rows"], 1)
        self.assertEqual(result["mismatched_identity_key_groups"], 1)

    def test_summary_does_not_retain_raw_identifiers(self):
        rows = [{
            "summaryTypeCode": "OTC_W_SMBL_FIRM",
            "tierIdentifier": "OTCE",
            "tierDescription": "OTCE",
            "issueSymbolIdentifier": "PRIVATE_TEST_SYMBOL",
            "MPID": "PRIVATE_MPID",
            "firmCRDNumber": "123456",
            "marketParticipantName": "De Minimis Firms",
            "totalWeeklyShareQuantity": "100",
            "totalWeeklyTradeCount": "5",
            "totalNotionalSum": "2500.00",
            "initialPublishedDate": "2025-11-24",
            "lastUpdateDate": "2025-11-24",
            "lastReportedDate": "2025-10-24",
            "weekStartDate": "2025-10-20",
        }]
        summary, hashes, keys = summarise_rows(
            "weeklySummary", "2025-10-20", "OTCE", rows, 1, 1, True
        )
        encoded = str(summary)
        self.assertNotIn("PRIVATE_TEST_SYMBOL", encoded)
        self.assertNotIn("PRIVATE_MPID", encoded)
        self.assertNotIn("123456", encoded)
        self.assertFalse(summary["raw_rows_retained"])
        self.assertEqual(summary["de_minimis_rows"], 1)
        self.assertEqual(summary["participant_id_rows"], 1)
        self.assertEqual(len(hashes), 1)
        self.assertEqual(len(keys), 1)


if __name__ == "__main__":
    unittest.main()

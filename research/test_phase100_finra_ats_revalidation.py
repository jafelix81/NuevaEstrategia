import unittest
from datetime import date

from research.phase100_finra_ats_revalidation import (
    SYMBOL_AGGREGATES,
    NON_SYMBOL_TYPES,
    SYMBOL_BEARING_TYPES,
    build_async_payload,
    build_sync_payload,
    parse_response,
    parse_sync_page_metadata,
    parse_date,
    parse_nonnegative_number,
    validate_partition_rows,
    summarize_partition,
    PAGE_HASH_FIELDS,
    record_totals_reconciled,
    weekly_coverage_passes,
)


class Phase100FinraTests(unittest.TestCase):
    def test_parse_response_list(self):
        self.assertEqual(parse_response([{"a": 1}]), [{"a": 1}])

    def test_parse_response_nested(self):
        self.assertEqual(parse_response({"data": {"data": [{"a": 1}]}}), [{"a": 1}])

    def test_parse_response_rejects_error_object(self):
        with self.assertRaises(ValueError):
            parse_response({"statusCode": 400, "message": "bad request"})

    def test_date_parser(self):
        self.assertEqual(parse_date("2025-11-03"), date(2025, 11, 3))
        self.assertIsNone(parse_date("not-a-date"))

    def test_nonnegative_number(self):
        self.assertEqual(parse_nonnegative_number("1,234"), 1234.0)
        self.assertIsNone(parse_nonnegative_number("-1"))
        self.assertIsNone(parse_nonnegative_number("x"))

    def test_partition_validation(self):
        rows = [{"weekStartDate": "2025-01-06", "tierIdentifier": "T1", "issueSymbolIdentifier": "AAPL", "summaryTypeCode": "ATS_W_SMBL"}]
        self.assertEqual(validate_partition_rows(rows, "2025-01-06", "T1"), [])
        self.assertTrue(validate_partition_rows(rows, "2025-01-13", "T1"))

    def test_firm_and_volume_stat_rows_may_omit_symbol(self):
        rows = [
            {"weekStartDate": "2025-01-06", "tierIdentifier": "T1", "summaryTypeCode": "ATS_W_FIRM"},
            {"weekStartDate": "2025-01-06", "tierIdentifier": "T1", "summaryTypeCode": "OTC_W_FIRM"},
            {"weekStartDate": "2025-01-06", "tierIdentifier": "T1", "summaryTypeCode": "ATS_W_VOL_STATS"},
            {"weekStartDate": "2025-01-06", "tierIdentifier": "T1", "summaryTypeCode": "OTC_W_VOL_STATS"},
        ]
        self.assertEqual(NON_SYMBOL_TYPES, {"ATS_W_FIRM", "OTC_W_FIRM", "ATS_W_VOL_STATS", "OTC_W_VOL_STATS"})
        self.assertEqual(validate_partition_rows(rows, "2025-01-06", "T1"), [])

    def test_sync_payload_uses_historical_week_and_tier(self):
        payload = build_sync_payload("2025-01-06", "T2", 5000)
        self.assertNotIn("async", payload)
        self.assertEqual(payload["limit"], 5000)
        self.assertEqual(payload["offset"], 5000)
        self.assertEqual(
            [(x["fieldName"], x["fieldValue"]) for x in payload["compareFilters"]],
            [("historicalWeek", "2025-01-06"), ("tierIdentifier", "T2")],
        )

    def test_sync_page_metadata_falls_back_to_actual_body_length(self):
        headers = {"record-total": "9", "record-limit": "5000", "record-offset": "0"}
        rows = [{"id": 1}, {"id": 2}, {"id": 3}]
        self.assertEqual(
            parse_sync_page_metadata(headers, rows, "2025-01-06", "T1", 0),
            (9, 3, "body_length"),
        )

    def test_sync_page_metadata_uses_and_checks_header_when_available(self):
        headers = {"Record-Total": "4", "Total-Records-On-Page": "2", "Record-Offset": "2"}
        rows = [{"id": 3}, {"id": 4}]
        self.assertEqual(
            parse_sync_page_metadata(headers, rows, "2025-01-06", "T1", 2),
            (4, 2, "header"),
        )
        with self.assertRaises(RuntimeError):
            parse_sync_page_metadata(
                {**headers, "Total-Records-On-Page": "1"},
                rows, "2025-01-06", "T1", 2,
            )

    def test_sync_page_metadata_rejects_missing_total_or_wrong_offset(self):
        with self.assertRaises(RuntimeError):
            parse_sync_page_metadata({}, [{"id": 1}], "2025-01-06", "T1", 0)
        with self.assertRaises(RuntimeError):
            parse_sync_page_metadata(
                {"record-total": "3", "record-offset": "5"},
                [{"id": 1}], "2025-01-06", "T1", 0,
            )

    def test_async_payload_uses_historical_week_and_tier(self):
        payload = build_async_payload("2025-01-06", "T2", 100000)
        self.assertTrue(payload["async"])
        self.assertEqual(payload["limit"], 100000)
        self.assertEqual(payload["offset"], 100000)
        self.assertEqual(
            [(x["fieldName"], x["fieldValue"]) for x in payload["compareFilters"]],
            [("historicalWeek", "2025-01-06"), ("tierIdentifier", "T2")],
        )

    def test_symbol_level_rows_must_have_symbol(self):
        rows = [{"weekStartDate": "2025-01-06", "tierIdentifier": "T1", "summaryTypeCode": "ATS_W_SMBL"}]
        errors = validate_partition_rows(rows, "2025-01-06", "T1")
        self.assertTrue(any("missing issueSymbolIdentifier" in x for x in errors))
        self.assertIn("ATS_W_SMBL", SYMBOL_BEARING_TYPES)

    def test_unknown_summary_type_is_rejected(self):
        rows = [{"weekStartDate": "2025-01-06", "tierIdentifier": "T1", "summaryTypeCode": "NEW_CODE"}]
        errors = validate_partition_rows(rows, "2025-01-06", "T1")
        self.assertTrue(any("unknown or missing summaryTypeCode" in x for x in errors))

    def test_page_hash_csv_schema_covers_sync_metadata(self):
        sync_meta = {
            "week", "tier", "page", "offset", "rows", "record_total",
            "total_records_on_page_header", "page_count_source", "record_limit",
            "record_offset", "request_attempts", "status_polls", "request_id",
            "async_status", "request_mode", "sha256",
        }
        self.assertTrue(sync_meta.issubset(set(PAGE_HASH_FIELDS)))
        self.assertIn("result_expires", PAGE_HASH_FIELDS)

    def test_record_total_reconciliation_requires_every_partition(self):
        self.assertTrue(record_totals_reconciled([
            {"api_record_total_match": True},
            {"api_record_total_match": True},
        ]))
        self.assertFalse(record_totals_reconciled([
            {"api_record_total_match": True},
            {"api_record_total_match": False},
        ]))
        self.assertFalse(record_totals_reconciled([]))

    def test_legacy_335_overlap_is_not_a_coverage_gate(self):
        self.assertTrue(weekly_coverage_passes([{
            "tier_partition_count": 2,
            "all_tiers_have_symbol_aggregates": True,
            "legacy_335_union_coverage_pct": 1.0,
        }]))
        self.assertFalse(weekly_coverage_passes([{
            "tier_partition_count": 1,
            "all_tiers_have_symbol_aggregates": True,
            "legacy_335_union_coverage_pct": 100.0,
        }]))

    def test_duplicate_group_counts_include_all_groups(self):
        rows = [
            {"issueSymbolIdentifier":"AAPL","weekStartDate":"2025-01-06","tierIdentifier":"T1","summaryTypeCode":"ATS_W_SMBL","productTypeCode":"CTS","initialPublishedDate":"2025-01-27","lastUpdateDate":"2025-01-27","totalWeeklyShareQuantity":"100","totalWeeklyTradeCount":"10"},
            {"issueSymbolIdentifier":"AAPL","weekStartDate":"2025-01-06","tierIdentifier":"T1","summaryTypeCode":"ATS_W_SMBL","productTypeCode":"CTS","initialPublishedDate":"2025-01-27","lastUpdateDate":"2025-01-27","totalWeeklyShareQuantity":"100","totalWeeklyTradeCount":"10"},
            {"issueSymbolIdentifier":"MSFT","weekStartDate":"2025-01-06","tierIdentifier":"T1","summaryTypeCode":"OTC_W_SMBL","productTypeCode":"CTS","initialPublishedDate":"2025-01-27","lastUpdateDate":"2025-01-27","totalWeeklyShareQuantity":"200","totalWeeklyTradeCount":"20"},
            {"issueSymbolIdentifier":"MSFT","weekStartDate":"2025-01-06","tierIdentifier":"T1","summaryTypeCode":"OTC_W_SMBL","productTypeCode":"CTS","initialPublishedDate":"2025-01-27","lastUpdateDate":"2025-01-27","totalWeeklyShareQuantity":"201","totalWeeklyTradeCount":"21"},
        ]
        summary, _, _ = summarize_partition(rows, "2025-01-06", "T1", {"AAPL","MSFT"})
        self.assertEqual(summary["duplicate_aggregate_key_groups"], 2)
        self.assertEqual(summary["duplicate_aggregate_keys"], 2)
        self.assertEqual(summary["exact_duplicate_key_groups"], 1)
        self.assertEqual(summary["conflicting_duplicate_key_groups"], 1)

    def test_only_symbol_level_rows_count_as_aggregate(self):
        self.assertEqual(SYMBOL_AGGREGATES, {"ATS_W_SMBL", "OTC_W_SMBL"})
        rows = [
            {"issueSymbolIdentifier": "AAPL", "weekStartDate": "2025-01-06", "tierIdentifier": "T1",
             "summaryTypeCode": "ATS_W_SMBL", "initialPublishedDate": "2025-01-21",
             "lastUpdateDate": "2025-01-20", "totalWeeklyShareQuantity": "100", "totalWeeklyTradeCount": "10"},
            {"issueSymbolIdentifier": "AAPL", "weekStartDate": "2025-01-06", "tierIdentifier": "T1",
             "summaryTypeCode": "ATS_W_FIRM", "initialPublishedDate": "2025-01-21",
             "lastUpdateDate": "2025-01-20", "totalWeeklyShareQuantity": "100", "totalWeeklyTradeCount": "10"},
        ]
        s, ats, otc = summarize_partition(rows, "2025-01-06", "T1", {"AAPL", "MSFT"})
        self.assertEqual(s["symbol_aggregate_rows"], 1)
        self.assertEqual(s["legacy_335_union_coverage_pct"], 50.0)
        self.assertEqual(ats, {"AAPL"})
        self.assertEqual(otc, set())


if __name__ == "__main__":
    unittest.main()

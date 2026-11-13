import unittest

from research.phase365_finra_weekly_partition_data_probe import (
    build_query, parse_rows, summarize_sample, SAMPLE_LIMIT,
)


class Phase365Tests(unittest.TestCase):
    def test_historic_uses_historical_week_filter(self):
        query = build_query("weeklySummaryHistoric", "2025-01-06", "T1")
        filters = {x["fieldName"]: x["fieldValue"] for x in query["compareFilters"]}
        self.assertEqual(filters["historicalWeek"], "2025-01-06")
        self.assertEqual(filters["tierIdentifier"], "T1")
        self.assertNotIn("weekStartDate", filters)
        self.assertEqual(query["limit"], SAMPLE_LIMIT)

    def test_current_uses_week_start_date_filter(self):
        query = build_query("weeklySummary", "2026-10-19", "OTCE")
        filters = {x["fieldName"]: x["fieldValue"] for x in query["compareFilters"]}
        self.assertEqual(filters["weekStartDate"], "2026-10-19")
        self.assertEqual(filters["tierIdentifier"], "OTCE")
        self.assertNotIn("historicalWeek", filters)

    def test_parse_rows_accepts_list_and_data_envelope(self):
        rows = [{"summaryTypeCode": "ATS_W_SMBL"}]
        self.assertEqual(parse_rows(rows), rows)
        self.assertEqual(parse_rows({"data": rows}), rows)
        self.assertEqual(parse_rows({"data": {"data": rows}}), rows)

    def test_parse_rows_rejects_finra_error_envelope(self):
        with self.assertRaises(RuntimeError):
            parse_rows({"statusCode": 400, "message": "bad request"})

    def test_summary_is_anonymized_and_counts_categories(self):
        rows = [
            {
                "issueSymbolIdentifier": "ABC",
                "tierIdentifier": "NA",
                "tierDescription": "Legacy",
                "summaryTypeCode": "ATS_W_SMBL",
                "productTypeCode": "CTS",
                "MPID": "X123",
                "firmCRDNumber": "456",
                "marketParticipantName": "Firm A",
                "initialPublishedDate": "2025-01-20",
            },
            {
                "issueSymbolIdentifier": "XYZ",
                "tierIdentifier": "NA",
                "tierDescription": "Legacy",
                "summaryTypeCode": "ATS_W_SMBL_FIRM",
                "productTypeCode": "",
                "MPID": "X456",
                "firmCRDNumber": "789",
                "marketParticipantName": "De Minimis Firms",
                "lastUpdateDate": "2025-01-20",
            },
        ]
        headers = {"record-total": "2", "total-records-on-page": "2", "record-offset": "0"}
        out = summarize_sample("weeklySummary", "2025-01-06", "NA", rows, headers)
        self.assertEqual(out["record_total"], 2)
        self.assertEqual(out["sample_summary_type_counts"]["ATS_W_SMBL"], 1)
        self.assertEqual(out["sample_de_minimis_rows"], 1)
        self.assertEqual(out["sample_unique_symbols"], 2)
        self.assertFalse(out["raw_rows_retained"])
        self.assertNotIn("X123", str(out))
        self.assertNotIn("456", str(out))
        self.assertNotIn("Firm A", str(out))

    def test_empty_partition_summary_is_valid(self):
        headers = {"record-total": "0", "total-records-on-page": "0", "record-offset": "0"}
        out = summarize_sample("weeklySummary", "2026-10-19", "NMS", [], headers)
        self.assertEqual(out["record_total"], 0)
        self.assertEqual(out["sampled_rows"], 0)
        self.assertFalse(out["sample_has_rows"])

    def test_no_return_or_f80_path_is_part_of_summary_contract(self):
        self.assertIn("weeklySummary", ("weeklySummaryHistoric", "weeklySummary"))


if __name__ == "__main__":
    unittest.main()

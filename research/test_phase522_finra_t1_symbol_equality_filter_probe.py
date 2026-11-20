import unittest

from research.phase521_finra_t1_symbol_domain_filter_probe import SAMPLE_SYMBOLS, WEEK
from research.phase522_finra_t1_symbol_equality_filter_probe import (
    build_payload,
    summarize_results,
    summarize_symbol_result,
)
from research.phase521_finra_t1_symbol_domain_filter_probe import analyze_symbol


def fixture_rows(symbol="AAPL", week=WEEK, pub="2024-06-10", update="2024-06-10"):
    common = {
        "weekStartDate": week,
        "initialPublishedDate": pub,
        "lastUpdateDate": update,
        "issueSymbolIdentifier": symbol,
    }
    return [
        {**common, "summaryTypeCode": "ATS_W_SMBL", "productTypeCode": "CTS",
         "totalWeeklyShareQuantity": "100", "totalWeeklyTradeCount": "10"},
        {**common, "summaryTypeCode": "ATS_W_SMBL", "productTypeCode": "UTP",
         "totalWeeklyShareQuantity": "50", "totalWeeklyTradeCount": "5"},
        {**common, "summaryTypeCode": "ATS_W_SMBL_FIRM", "productTypeCode": "CTS",
         "MPID": "AAA", "firmCRDNumber": "1", "marketParticipantName": "Firm A",
         "totalWeeklyShareQuantity": "100", "totalWeeklyTradeCount": "10"},
        {**common, "summaryTypeCode": "ATS_W_SMBL_FIRM", "productTypeCode": "UTP",
         "MPID": "BBB", "firmCRDNumber": "2", "marketParticipantName": "Firm B",
         "totalWeeklyShareQuantity": "50", "totalWeeklyTradeCount": "5"},
    ]


class Phase522Tests(unittest.TestCase):
    def test_payload_uses_symbol_equality_compare_filter(self):
        payload = build_payload(WEEK, "AAPL")
        filters = payload["compareFilters"]
        self.assertEqual(len(filters), 3)
        self.assertEqual(filters[2], {
            "fieldName": "issueSymbolIdentifier",
            "fieldValue": "AAPL",
            "compareType": "EQUAL",
        })
        self.assertNotIn("domainFilters", payload)

    def test_single_symbol_summary_passes_exact_bridge_and_clock(self):
        rows = fixture_rows()
        result = summarize_symbol_result(rows, "AAPL", WEEK, len(rows))
        self.assertTrue(result["exact_symbol_match"])
        self.assertTrue(result["bridge_pass"])
        self.assertTrue(result["revision_stable"])
        self.assertTrue(result["concentration_valid"])
        self.assertNotIn("AAPL", str(result))

    def test_unexpected_symbol_fails_exact_match(self):
        rows = fixture_rows("OTHER")
        result = summarize_symbol_result(rows, "AAPL", WEEK, len(rows))
        self.assertFalse(result["exact_symbol_match"])
        self.assertFalse(result["concentration_valid"])

    def test_aggregate_probe_requires_all_ten_queries(self):
        good = {
            "status": "HTTP_200", "rows_returned": 4, "record_total": 4,
            "exact_symbol_match": True, "bridge_pass": True,
            "revision_stable": True, "concentration_valid": True,
        }
        result = summarize_results([good] * len(SAMPLE_SYMBOLS))
        self.assertTrue(result["probe_pass"])
        self.assertEqual(result["queries_succeeded"], 10)
        self.assertEqual(result["concentration_valid_count"], 10)

    def test_http_400_stops_probe_and_cannot_pass(self):
        result = summarize_results([{"status": "HTTP_400"}])
        self.assertFalse(result["probe_pass"])
        self.assertEqual(result["queries_rejected"], 1)
        self.assertNotIn("AAPL", str(result))


if __name__ == "__main__":
    unittest.main()

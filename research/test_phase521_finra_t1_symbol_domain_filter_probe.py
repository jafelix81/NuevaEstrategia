import unittest

from research.phase521_finra_t1_symbol_domain_filter_probe import (
    SAMPLE_SYMBOLS,
    WEEK,
    analyze_symbol,
    build_payload,
    manifest_hash,
    summarize_rows,
)


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


class Phase521Tests(unittest.TestCase):
    def test_payload_uses_domain_filters_for_symbols_and_summary_types(self):
        payload = build_payload(WEEK, ["msft", "AAPL", "AAPL"])
        self.assertEqual(payload["compareFilters"][0]["fieldValue"], WEEK)
        self.assertEqual(payload["domainFilters"][0]["fieldName"], "issueSymbolIdentifier")
        self.assertEqual(payload["domainFilters"][0]["values"], ["AAPL", "MSFT"])
        self.assertEqual(payload["domainFilters"][1]["values"], ["ATS_W_SMBL", "ATS_W_SMBL_FIRM"])
        self.assertIn("MPID", payload["fields"])

    def test_manifest_hash_is_order_independent_and_normalized(self):
        self.assertEqual(manifest_hash(["aapl", "msft"]), manifest_hash(["MSFT", "AAPL"]))

    def test_symbol_bridge_and_concentration_gate_pass(self):
        result = analyze_symbol(fixture_rows(), "AAPL", WEEK)
        self.assertTrue(result["bridge_pass"])
        self.assertTrue(result["revision_stable"])
        self.assertTrue(result["concentration_valid"])

    def test_post_publication_revision_fails_concentration_gate(self):
        result = analyze_symbol(fixture_rows(update="2024-06-11"), "AAPL", WEEK)
        self.assertTrue(result["bridge_pass"])
        self.assertFalse(result["revision_stable"])
        self.assertFalse(result["concentration_valid"])

    def test_domain_filter_summary_passes_only_exact_requested_set(self):
        symbols = ["AAPL", "MSFT"]
        rows = fixture_rows("AAPL") + fixture_rows("MSFT")
        result = summarize_rows(rows, symbols)
        self.assertTrue(result["domain_filter_applied"])
        self.assertTrue(result["all_requested_symbols_returned"])
        self.assertEqual(result["symbols_with_both_types_and_exact_aggregate_bridge"], 2)
        self.assertTrue(result["probe_pass"])
        self.assertNotIn("AAPL", str(result))
        self.assertNotIn("MSFT", str(result))

    def test_unexpected_symbol_means_filter_was_not_applied_exactly(self):
        rows = fixture_rows("AAPL") + fixture_rows("OTHER")
        result = summarize_rows(rows, ["AAPL"])
        self.assertFalse(result["domain_filter_applied"])
        self.assertEqual(result["unexpected_symbol_count"], 1)
        self.assertFalse(result["probe_pass"])

    def test_missing_requested_symbol_is_reported_without_leaking_symbol(self):
        result = summarize_rows(fixture_rows("AAPL"), ["AAPL", "MSFT"])
        self.assertEqual(result["missing_requested_symbol_count"], 1)
        self.assertFalse(result["all_requested_symbols_returned"])
        self.assertNotIn("MSFT", str(result))


if __name__ == "__main__":
    unittest.main()

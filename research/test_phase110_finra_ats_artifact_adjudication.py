import unittest
from phase110_finra_ats_artifact_adjudication import analyze_rows, knowledge_date

def row(summary_type, symbol, quantity, trades, product="", mpid="", report_date="2024-01-12", update="2024-02-12"):
    return {
        "requested_week": "2024-01-08", "requested_tier": "T2",
        "weekStartDate": "2024-01-08", "tierIdentifier": "T2",
        "summaryTypeCode": summary_type, "issueSymbolIdentifier": symbol,
        "totalWeeklyShareQuantity": str(quantity), "totalWeeklyTradeCount": str(trades),
        "productTypeCode": product, "MPID": mpid, "firmCRDNumber": "",
        "lastReportedDate": report_date, "initialPublishedDate": "2024-02-12",
        "lastUpdateDate": update,
    }

class Phase110Tests(unittest.TestCase):
    def test_total_reconciliation_across_product_feeds(self):
        result = analyze_rows([
            row("ATS_W_SMBL", "XYZ", 100, 10, product="CTS", report_date="2024-01-12"),
            row("ATS_W_SMBL", "XYZ", 50, 5, product="UTP", report_date="2024-01-10"),
            row("ATS_W_SMBL_FIRM", "XYZ", 75, 8, mpid="A", report_date="2024-01-10"),
            row("ATS_W_SMBL_FIRM", "XYZ", 75, 7, mpid="B", report_date="2024-01-12"),
        ])
        self.assertEqual(result["symbol_groups"], 1)
        self.assertEqual(result["quantity_matches"], 1)
        self.assertEqual(result["trade_matches"], 1)

    def test_NA_is_a_valid_symbol(self):
        result = analyze_rows([
            row("OTC_W_SMBL", "NA", 10, 2, product="CTS"),
            row("OTC_W_SMBL_FIRM", "NA", 10, 2, mpid="A"),
        ])
        self.assertEqual(result["missing_symbol_rows"], 0)
        self.assertEqual(result["valid_NA_ticker_rows"], 2)

    def test_missing_symbol_is_not_allocated_to_a_security(self):
        result = analyze_rows([row("OTC_W_SMBL", "", 100, 1, product="UTP")])
        self.assertEqual(result["missing_symbol_rows"], 1)
        self.assertEqual(result["symbol_groups"], 0)

    def test_last_update_controls_final_value_knowledge_date(self):
        sample = row("ATS_W_SMBL", "XYZ", 10, 1, update="2024-12-20")
        self.assertEqual(str(knowledge_date(sample)), "2024-12-20")

if __name__ == "__main__":
    unittest.main()

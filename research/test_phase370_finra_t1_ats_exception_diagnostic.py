import unittest

from research.phase370_finra_t1_ats_exception_diagnostic import (
    ambiguous_symbol_diagnostics, date_gap_diagnostics, hash_symbol,
)

class Phase370Tests(unittest.TestCase):
    def row(self, typ, symbol="ABC", **kw):
        base = {
            "summaryTypeCode": typ, "issueSymbolIdentifier": symbol,
            "productTypeCode": "CTS", "weekStartDate": "2025-11-10",
            "summaryStartDate": "2025-11-10", "initialPublishedDate": "2025-12-01",
            "lastUpdateDate": "2025-12-01", "lastReportedDate": "2025-11-14",
            "totalWeeklyShareQuantity": "100", "totalWeeklyTradeCount": "10",
            "MPID": "M001", "firmCRDNumber": "123", "marketParticipantName": "Firm A",
        }
        base.update(kw)
        return base

    def test_single_unambiguous_aggregate_is_not_reported(self):
        rows = [self.row("ATS_W_SMBL"), self.row("ATS_W_SMBL_FIRM")]
        self.assertEqual(ambiguous_symbol_diagnostics(rows), [])

    def test_duplicate_aggregate_is_reported_without_raw_symbol(self):
        rows = [
            self.row("ATS_W_SMBL", lastReportedDate="2025-11-14"),
            self.row("ATS_W_SMBL", lastReportedDate="2025-11-12"),
            self.row("ATS_W_SMBL_FIRM"),
        ]
        out = ambiguous_symbol_diagnostics(rows)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["aggregate_row_count"], 2)
        self.assertNotIn("symbol", out[0])
        self.assertEqual(out[0]["symbol_hash"], hash_symbol("ABC"))

    def test_product_type_collision_is_reported(self):
        rows = [
            self.row("ATS_W_SMBL", productTypeCode="CTS"),
            self.row("ATS_W_SMBL", productTypeCode="UTP"),
        ]
        out = ambiguous_symbol_diagnostics(rows)
        self.assertEqual(out[0]["product_type_codes"], ["CTS", "UTP"])

    def test_combined_totals_and_reporting_date_are_diagnostic_only(self):
        rows = [
            self.row("ATS_W_SMBL", totalWeeklyShareQuantity="200", totalWeeklyTradeCount="20"),
            self.row("ATS_W_SMBL", totalWeeklyShareQuantity="300", totalWeeklyTradeCount="30"),
            self.row("ATS_W_SMBL_FIRM", totalWeeklyShareQuantity="500", totalWeeklyTradeCount="50"),
        ]
        out = ambiguous_symbol_diagnostics(rows)[0]
        self.assertTrue(out["combined_totals_match"])
        self.assertTrue(out["last_reported_date_diagnostic_only_not_an_approved_join"])

    def test_date_gap_distribution(self):
        rows = [
            self.row("ATS_W_SMBL", initialPublishedDate="2021-12-13", lastUpdateDate="2022-09-23"),
            self.row("ATS_W_SMBL", initialPublishedDate="2021-12-13", lastUpdateDate="2021-12-13"),
        ]
        out = date_gap_diagnostics(rows)
        self.assertEqual(out["gap_days_counts_by_summary_type"]["ATS_W_SMBL"]["284"], 1)
        self.assertEqual(out["gap_days_counts_by_summary_type"]["ATS_W_SMBL"]["0"], 1)

if __name__ == "__main__":
    unittest.main()

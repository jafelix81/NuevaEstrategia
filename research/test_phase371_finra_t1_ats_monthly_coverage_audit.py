import unittest

from research.phase371_finra_t1_ats_monthly_coverage_audit import (
    parse_partition_payload, select_monthly_weeks, audit_bridge, concentration_stats,
)

class Phase371Tests(unittest.TestCase):
    def row(self, typ, symbol="ABC", **kw):
        base = {
            "summaryTypeCode": typ, "issueSymbolIdentifier": symbol,
            "productTypeCode": "CTS", "totalWeeklyShareQuantity": "100",
            "totalWeeklyTradeCount": "10", "MPID": "M001",
            "firmCRDNumber": "123", "marketParticipantName": "Firm A",
        }
        base.update(kw)
        return base

    def test_partition_payload_and_monthly_selection(self):
        payload = {
            "partitionFields": ["weekStartDate", "tierIdentifier"],
            "availablePartitions": [
                {"partitions": [["2022-01-03", "T1"], ["2022-01-10", "T1"], ["2022-02-14", "T1"]]},
            ],
        }
        fields, raw, unique = parse_partition_payload(payload)
        self.assertEqual(fields, ("weekStartDate", "tierIdentifier"))
        weeks, missing = select_monthly_weeks(unique, start=(2022,1), end=(2022,2))
        self.assertEqual(weeks, ["2022-01-10", "2022-02-14"])
        self.assertEqual(missing, [])

    def test_single_product_symbol_exact_bridge_and_hhi(self):
        rows = [
            self.row("ATS_W_SMBL", totalWeeklyShareQuantity="300", totalWeeklyTradeCount="30"),
            self.row("ATS_W_SMBL_FIRM", totalWeeklyShareQuantity="100", totalWeeklyTradeCount="10", MPID="M001"),
            self.row("ATS_W_SMBL_FIRM", totalWeeklyShareQuantity="200", totalWeeklyTradeCount="20", MPID="M002"),
        ]
        out = audit_bridge(rows)
        self.assertEqual(out["bridge_gate"], "PASS")
        self.assertEqual(out["concentration_gate"], "PASS")
        self.assertEqual(out["exact_both_matches"], 1)
        self.assertEqual(out["multi_product_combined_symbols"], 0)
        self.assertEqual(out["concentration_ready_symbols"], 1)
        self.assertAlmostEqual(out["broker_dealer_reporting_concentration"]["hhi"]["mean"], (1/3)**2+(2/3)**2, places=5)

    def test_distinct_products_can_only_be_combined_at_symbol_grain(self):
        rows = [
            self.row("ATS_W_SMBL", productTypeCode="CTS", totalWeeklyShareQuantity="100", totalWeeklyTradeCount="10"),
            self.row("ATS_W_SMBL", productTypeCode="UTP", totalWeeklyShareQuantity="200", totalWeeklyTradeCount="20"),
            self.row("ATS_W_SMBL_FIRM", totalWeeklyShareQuantity="300", totalWeeklyTradeCount="30"),
        ]
        out = audit_bridge(rows)
        self.assertEqual(out["bridge_gate"], "PASS")
        self.assertEqual(out["multi_product_combined_symbols"], 1)
        self.assertEqual(out["exact_both_matches"], 1)

    def test_duplicate_same_product_remains_ambiguous(self):
        rows = [
            self.row("ATS_W_SMBL", productTypeCode="CTS"),
            self.row("ATS_W_SMBL", productTypeCode="CTS"),
            self.row("ATS_W_SMBL_FIRM"),
        ]
        out = audit_bridge(rows)
        self.assertEqual(out["bridge_gate"], "FAIL_OR_REVIEW")
        self.assertEqual(out["ambiguous_symbols"], 1)

    def test_de_minimis_censors_concentration(self):
        rows = [
            self.row("ATS_W_SMBL", totalWeeklyShareQuantity="300", totalWeeklyTradeCount="30"),
            self.row("ATS_W_SMBL_FIRM", totalWeeklyShareQuantity="200", totalWeeklyTradeCount="20", MPID="M001"),
            self.row("ATS_W_SMBL_FIRM", totalWeeklyShareQuantity="100", totalWeeklyTradeCount="10", MPID="", firmCRDNumber="0", marketParticipantName="De Minimis Firms"),
        ]
        out = audit_bridge(rows)
        self.assertEqual(out["bridge_gate"], "PASS")
        self.assertEqual(out["concentration_gate"], "FAIL_OR_REVIEW")
        self.assertEqual(out["de_minimis_rows"], 1)

if __name__ == "__main__":
    unittest.main()

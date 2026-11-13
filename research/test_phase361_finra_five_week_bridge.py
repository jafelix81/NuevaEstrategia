import unittest

from research.phase359_finra_product_key_diagnostic import TIERS
from research.phase360_finra_symbol_bridge import audit_pair
from research.phase361_finra_five_week_bridge import WEEKS


def row(stype, symbol="ABC", product="", shares=100, trades=10,
        mpid="", crd="", name="Participant"):
    return {
        "summaryTypeCode": stype,
        "issueSymbolIdentifier": symbol,
        "productTypeCode": product,
        "totalWeeklyShareQuantity": shares,
        "totalWeeklyTradeCount": trades,
        "MPID": mpid,
        "firmCRDNumber": crd,
        "marketParticipantName": name,
        "weekStartDate": "2025-01-06",
        "tierIdentifier": "T2",
    }


class Phase361Tests(unittest.TestCase):
    def test_five_week_sample_matches_phase107_weeks(self):
        self.assertEqual(WEEKS, (
            "2022-01-03", "2023-01-09", "2024-01-08",
            "2025-01-06", "2025-10-20",
        ))
        self.assertEqual(TIERS, ("T1", "T2"))

    def test_lnd_like_duplicate_aggregate_key_fails_mapping(self):
        rows = [
            row("ATS_W_SMBL", symbol="LND", product="CTS", shares=28543, trades=137),
            row("ATS_W_SMBL", symbol="LND", product="CTS", shares=67210, trades=320),
            row("ATS_W_SMBL_FIRM", symbol="LND", shares=95753, trades=457, mpid="A001"),
        ]
        out = audit_pair(rows, "2025-01-06", "T2", "ATS_W_SMBL")
        self.assertEqual(out["duplicate_aggregate_symbol_rows"], 1)
        self.assertEqual(out["mapping_gate"], "FAIL_OR_REVIEW")
        self.assertEqual(out["unambiguous_symbol_bridge_count"], 0)

    def test_multi_product_symbol_is_ambiguous_but_not_duplicate_same_key(self):
        rows = [
            row("ATS_W_SMBL", symbol="VPCC", product="CTS", shares=100, trades=10),
            row("ATS_W_SMBL", symbol="VPCC", product="UTP", shares=50, trades=5),
            row("ATS_W_SMBL_FIRM", symbol="VPCC", shares=150, trades=15, mpid="A001"),
        ]
        out = audit_pair(rows, "2025-01-06", "T2", "ATS_W_SMBL")
        self.assertEqual(out["ambiguous_symbol_count"], 1)
        self.assertEqual(out["duplicate_aggregate_symbol_rows"], 0)
        self.assertEqual(out["mapping_gate"], "PASS_WITH_EXCLUSIONS")

    def test_unambiguous_symbol_reconciles_exactly(self):
        rows = [
            row("ATS_W_SMBL", symbol="ABC", product="CTS", shares=100, trades=10),
            row("ATS_W_SMBL_FIRM", symbol="ABC", shares=40, trades=4, mpid="A001"),
            row("ATS_W_SMBL_FIRM", symbol="ABC", shares=60, trades=6, mpid="A002"),
        ]
        out = audit_pair(rows, "2025-01-06", "T2", "ATS_W_SMBL")
        self.assertEqual(out["both_exact_matches"], 1)
        self.assertEqual(out["data_gate"], "PASS")

    def test_missing_firm_product_type_is_not_a_join_failure(self):
        rows = [
            row("OTC_W_SMBL", symbol="ABC", product="UTP", shares=100, trades=10),
            row("OTC_W_SMBL_FIRM", symbol="ABC", product="", shares=100, trades=10, crd="123"),
        ]
        out = audit_pair(rows, "2025-01-06", "T2", "OTC_W_SMBL")
        self.assertEqual(out["unambiguous_symbol_bridge_count"], 1)
        self.assertEqual(out["reconciliation_gate"], "PASS")

    def test_no_alpha_or_f80_path(self):
        rows = [
            row("ATS_W_SMBL", product="CTS"),
            row("ATS_W_SMBL_FIRM", shares=100, trades=10, mpid="A001"),
        ]
        out = audit_pair(rows, "2025-01-06", "T2", "ATS_W_SMBL")
        self.assertFalse(out["intermediary_concentration_ready"] is False and out["data_gate"] == "PASS")
        self.assertEqual(WEEKS[-1], "2025-10-20")


if __name__ == "__main__":
    unittest.main()

import unittest

from research.phase360_finra_symbol_bridge import audit_pair, audit_partition


def row(stype, symbol="ABC", product="", shares=100, trades=10,
        mpid="", crd="", name="Participant", week="2025-10-20", tier="T1"):
    return {
        "summaryTypeCode": stype,
        "issueSymbolIdentifier": symbol,
        "productTypeCode": product,
        "totalWeeklyShareQuantity": shares,
        "totalWeeklyTradeCount": trades,
        "MPID": mpid,
        "firmCRDNumber": crd,
        "marketParticipantName": name,
        "weekStartDate": week,
        "tierIdentifier": tier,
    }


class Phase360Tests(unittest.TestCase):
    def test_unique_symbol_bridge_and_exact_reconciliation(self):
        rows = [
            row("ATS_W_SMBL", product="CTS", shares=100, trades=10),
            row("ATS_W_SMBL_FIRM", shares=40, trades=4, mpid="A001"),
            row("ATS_W_SMBL_FIRM", shares=60, trades=6, mpid="A002"),
        ]
        out = audit_pair(rows, "2025-10-20", "T1", "ATS_W_SMBL")
        self.assertEqual(out["unambiguous_symbol_bridge_count"], 1)
        self.assertEqual(out["mapping_gate"], "PASS")
        self.assertEqual(out["reconciliation_gate"], "PASS")
        self.assertTrue(out["intermediary_concentration_ready"])

    def test_ambiguous_product_symbol_is_excluded_not_multiplied(self):
        rows = [
            row("ATS_W_SMBL", product="CTS", shares=100, trades=10),
            row("ATS_W_SMBL", product="UTP", shares=50, trades=5),
            row("ATS_W_SMBL_FIRM", shares=150, trades=15, mpid="A001"),
        ]
        out = audit_pair(rows, "2025-10-20", "T1", "ATS_W_SMBL")
        self.assertEqual(out["ambiguous_symbol_count"], 1)
        self.assertEqual(out["unambiguous_symbol_bridge_count"], 0)
        self.assertEqual(out["mapping_gate"], "PASS_WITH_EXCLUSIONS")
        self.assertEqual(out["reconciliation_gate"], "FAIL_OR_REVIEW")

    def test_non_ats_de_minimis_bucket_is_included_but_censors_concentration(self):
        rows = [
            row("OTC_W_SMBL", product="CTS", shares=100, trades=10),
            row("OTC_W_SMBL_FIRM", shares=70, trades=7, crd="123", name="Named Firm"),
            row("OTC_W_SMBL_FIRM", shares=30, trades=3, name="De Minimis Firms"),
        ]
        out = audit_pair(rows, "2025-10-20", "T1", "OTC_W_SMBL")
        self.assertEqual(out["reconciliation_gate"], "PASS")
        self.assertEqual(out["de_minimis_rows"], 1)
        self.assertEqual(out["de_minimis_pct_of_firm_shares"], 30.0)
        self.assertFalse(out["intermediary_concentration_ready"])

    def test_quantity_or_trade_mismatch_fails_reconciliation(self):
        rows = [
            row("ATS_W_SMBL", product="UTP", shares=100, trades=10),
            row("ATS_W_SMBL_FIRM", shares=99, trades=10, mpid="A001"),
        ]
        out = audit_pair(rows, "2025-10-20", "T1", "ATS_W_SMBL")
        self.assertEqual(out["share_quantity_exact_matches"], 0)
        self.assertEqual(out["trade_count_exact_matches"], 1)
        self.assertEqual(out["reconciliation_gate"], "FAIL_OR_REVIEW")

    def test_orphan_firm_symbol_is_not_silently_joined(self):
        rows = [
            row("ATS_W_SMBL", symbol="ABC", product="CTS"),
            row("ATS_W_SMBL_FIRM", symbol="XYZ", shares=100, trades=10, mpid="A001"),
        ]
        out = audit_pair(rows, "2025-10-20", "T1", "ATS_W_SMBL")
        self.assertEqual(out["firm_only_symbols"], 1)
        self.assertEqual(out["mapping_gate"], "FAIL_OR_REVIEW")

    def test_missing_aggregate_product_type_is_excluded(self):
        rows = [
            row("ATS_W_SMBL", product="", shares=100, trades=10),
            row("ATS_W_SMBL_FIRM", shares=100, trades=10, mpid="A001"),
        ]
        out = audit_pair(rows, "2025-10-20", "T1", "ATS_W_SMBL")
        self.assertEqual(out["ambiguous_symbol_count"], 1)
        self.assertEqual(out["unambiguous_symbol_bridge_count"], 0)

    def test_duplicate_aggregate_rows_are_flagged(self):
        rows = [
            row("ATS_W_SMBL", product="CTS", shares=50, trades=5),
            row("ATS_W_SMBL", product="CTS", shares=50, trades=5),
            row("ATS_W_SMBL_FIRM", shares=100, trades=10, mpid="A001"),
        ]
        out = audit_pair(rows, "2025-10-20", "T1", "ATS_W_SMBL")
        self.assertEqual(out["duplicate_aggregate_symbol_rows"], 1)
        self.assertEqual(out["mapping_gate"], "FAIL_OR_REVIEW")

    def test_duplicate_participant_symbol_key_is_flagged(self):
        rows = [
            row("ATS_W_SMBL", product="CTS", shares=100, trades=10),
            row("ATS_W_SMBL_FIRM", shares=40, trades=4, mpid="A001"),
            row("ATS_W_SMBL_FIRM", shares=60, trades=6, mpid="A001"),
        ]
        out = audit_pair(rows, "2025-10-20", "T1", "ATS_W_SMBL")
        self.assertEqual(out["duplicate_participant_symbol_keys"], 1)
        self.assertFalse(out["intermediary_concentration_ready"])

    def test_missing_numeric_is_not_treated_as_zero(self):
        rows = [
            row("ATS_W_SMBL", product="CTS", shares=100, trades=10),
            row("ATS_W_SMBL_FIRM", shares="", trades=10, mpid="A001"),
        ]
        out = audit_pair(rows, "2025-10-20", "T1", "ATS_W_SMBL")
        self.assertEqual(out["invalid_numeric_symbol_count"], 1)
        self.assertEqual(out["reconciliation_gate"], "FAIL_OR_REVIEW")

    def test_missing_symbol_firm_row_is_explicitly_excluded(self):
        rows = [
            row("ATS_W_SMBL", product="CTS", shares=100, trades=10),
            row("ATS_W_SMBL_FIRM", shares=100, trades=10, mpid="A001"),
            row("ATS_W_SMBL_FIRM", symbol="", shares=5, trades=1, mpid="A002"),
        ]
        out = audit_pair(rows, "2025-10-20", "T1", "ATS_W_SMBL")
        self.assertEqual(out["missing_firm_symbol_rows"], 1)
        self.assertEqual(out["mapping_gate"], "PASS_WITH_EXCLUSIONS")
        self.assertFalse(out["intermediary_concentration_ready"])

    def test_partition_mismatch_is_visible(self):
        rows = [
            row("ATS_W_SMBL", product="CTS", week="2025-10-27"),
            row("ATS_W_SMBL_FIRM", shares=100, trades=10, mpid="A001"),
        ]
        out = audit_pair(rows, "2025-10-20", "T1", "ATS_W_SMBL")
        self.assertEqual(out["partition_error_count"], 1)

    def test_no_alpha_or_f80_path(self):
        rows = [
            row("ATS_W_SMBL", product="CTS"),
            row("ATS_W_SMBL_FIRM", shares=100, trades=10, mpid="A001"),
        ]
        out = audit_partition(rows, "2025-10-20", "T1")
        self.assertFalse(out["forward_returns_used"])
        self.assertFalse(out["alpha_test_authorized"])
        self.assertFalse(out["f80_changed"])


if __name__ == "__main__":
    unittest.main()

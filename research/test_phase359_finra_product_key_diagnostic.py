import unittest

from research.phase359_finra_product_key_diagnostic import audit_rows


def row(stype, symbol="ABC", product="CTS", week="2025-10-20", tier="T1",
        mpid="", crd="", name="Participant"):
    return {
        "issueSymbolIdentifier": symbol,
        "weekStartDate": week,
        "tierIdentifier": tier,
        "summaryTypeCode": stype,
        "productTypeCode": product,
        "firmCRDNumber": crd,
        "MPID": mpid,
        "marketParticipantName": name,
    }


class Phase359Tests(unittest.TestCase):
    def test_exact_symbol_product_key_overlap(self):
        rows = [
            row("ATS_W_SMBL", product="CTS"),
            row("ATS_W_SMBL_FIRM", product="CTS", mpid="A001"),
        ]
        out = audit_rows(rows, "2025-10-20", "T1")
        cw = out["key_crosswalks"]["ATS_W_SMBL"]
        self.assertEqual(cw["exact_symbol_product_key_overlap"], 1)
        self.assertEqual(cw["shared_symbols_singleton_same_product"], 1)

    def test_symbol_overlap_with_product_code_disagreement(self):
        rows = [
            row("ATS_W_SMBL", product="CTS"),
            row("ATS_W_SMBL_FIRM", product="UTP", mpid="A001"),
        ]
        out = audit_rows(rows, "2025-10-20", "T1")
        cw = out["key_crosswalks"]["ATS_W_SMBL"]
        self.assertEqual(cw["exact_symbol_product_key_overlap"], 0)
        self.assertEqual(cw["shared_symbols_ignoring_product_type"], 1)
        self.assertEqual(cw["shared_symbols_singleton_different_product"], 1)

    def test_missing_product_type_is_explicit(self):
        rows = [
            row("OTC_W_SMBL", product=""),
            row("OTC_W_SMBL_FIRM", product=None, mpid="B001"),
        ]
        out = audit_rows(rows, "2025-10-20", "T1")
        self.assertEqual(
            out["key_crosswalks"]["OTC_W_SMBL"]["exact_symbol_product_key_overlap"], 1
        )
        self.assertEqual(
            out["product_type_counts_by_summary_type"]["OTC_W_SMBL"]["__MISSING__"], 1
        )

    def test_multivalue_product_type_is_flagged(self):
        rows = [
            row("ATS_W_SMBL", product="CTS"),
            row("ATS_W_SMBL", product="UTP"),
            row("ATS_W_SMBL_FIRM", product="CTS", mpid="A001"),
        ]
        out = audit_rows(rows, "2025-10-20", "T1")
        cw = out["key_crosswalks"]["ATS_W_SMBL"]
        self.assertEqual(cw["shared_symbols_with_multivalue_product_type"], 1)
        self.assertEqual(cw["shared_symbols_singleton_same_product"], 0)

    def test_missing_symbol_rows_are_not_joined(self):
        rows = [
            row("ATS_W_SMBL", symbol=""),
            row("ATS_W_SMBL_FIRM", symbol="", mpid="A001"),
        ]
        out = audit_rows(rows, "2025-10-20", "T1")
        self.assertEqual(out["missing_symbol_rows_by_summary_type"]["ATS_W_SMBL"], 1)
        self.assertEqual(out["missing_symbol_rows_by_summary_type"]["ATS_W_SMBL_FIRM"], 1)
        self.assertEqual(out["key_crosswalks"]["ATS_W_SMBL"]["exact_symbol_product_key_overlap"], 0)

    def test_unmapped_summary_type_is_visible(self):
        out = audit_rows([row("NEW_TYPE")], "2025-10-20", "T1")
        self.assertEqual(out["partition_error_count"], 1)
        self.assertIn("NEW_TYPE", out["summary_type_counts"])

    def test_partition_mismatch_is_visible(self):
        out = audit_rows([row("ATS_W_SMBL", week="2025-10-27")], "2025-10-20", "T1")
        self.assertEqual(out["partition_error_count"], 1)

    def test_no_alpha_or_return_path(self):
        out = audit_rows([row("ATS_W_SMBL")], "2025-10-20", "T1")
        self.assertFalse(out["forward_returns_used"])
        self.assertFalse(out["alpha_test_authorized"])
        self.assertFalse(out["f80_changed"])


if __name__ == "__main__":
    unittest.main()

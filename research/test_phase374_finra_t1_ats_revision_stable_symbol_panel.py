import unittest

from research.phase374_finra_t1_ats_revision_stable_symbol_panel import (
    analyze_revision_stable_symbols,
)


def make_row(
    typ, symbol="AAA", shares=300, trades=30, product="CTS",
    mpid="ABCD", crd="123", name="Firm", pub="2022-02-07",
    update="2022-02-07", week="2022-01-17",
):
    return {
        "summaryTypeCode": typ,
        "issueSymbolIdentifier": symbol,
        "productTypeCode": product if typ == "ATS_W_SMBL" else None,
        "totalWeeklyShareQuantity": str(shares),
        "totalWeeklyTradeCount": str(trades),
        "MPID": mpid,
        "firmCRDNumber": crd,
        "marketParticipantName": name,
        "weekStartDate": week,
        "initialPublishedDate": pub,
        "lastUpdateDate": update,
    }


class Phase374Tests(unittest.TestCase):
    def base_rows(self):
        return [
            make_row("ATS_W_SMBL", shares=300, trades=30),
            make_row("ATS_W_SMBL_FIRM", shares=100, trades=10, mpid="FIRM1", crd="1"),
            make_row("ATS_W_SMBL_FIRM", shares=200, trades=20, mpid="FIRM2", crd="2"),
        ]

    def test_revision_stable_symbol_is_concentration_eligible(self):
        r = analyze_revision_stable_symbols(self.base_rows(), "2022-01-17", 3, 1)
        self.assertEqual(r["revision_stable_symbols"], 1)
        self.assertEqual(r["revision_stable_concentration_symbols"], 1)
        self.assertEqual(r["stable_concentration_gate"], "PASS")
        self.assertEqual(r["revision_stable_share_volume_coverage_pct"], 100.0)

    def test_any_post_publication_revision_excludes_whole_symbol(self):
        rows = self.base_rows()
        rows[1]["lastUpdateDate"] = "2022-02-08"
        r = analyze_revision_stable_symbols(rows, "2022-01-17", 3, 1)
        self.assertEqual(r["revised_symbols"], 1)
        self.assertEqual(r["revision_stable_symbols"], 0)
        self.assertEqual(r["revision_stable_concentration_symbols"], 0)

    def test_22_day_publication_lag_is_allowed_without_backdating(self):
        rows = [
            make_row("ATS_W_SMBL", shares=300, trades=30, pub="2022-02-08", update="2022-02-08"),
            make_row("ATS_W_SMBL_FIRM", shares=100, trades=10, mpid="FIRM1", crd="1", pub="2022-02-08", update="2022-02-08"),
            make_row("ATS_W_SMBL_FIRM", shares=200, trades=20, mpid="FIRM2", crd="2", pub="2022-02-08", update="2022-02-08"),
        ]
        r = analyze_revision_stable_symbols(rows, "2022-01-17", 3, 1)
        self.assertEqual(r["revision_stable_concentration_symbols"], 1)
        self.assertEqual(r["publication_lag_days_counts"], {"22": 3})

    def test_distinct_cts_utp_aggregates_can_reconcile_at_symbol_level(self):
        rows = [
            make_row("ATS_W_SMBL", shares=100, trades=10, product="CTS"),
            make_row("ATS_W_SMBL", shares=200, trades=20, product="UTP"),
            make_row("ATS_W_SMBL_FIRM", shares=100, trades=10, mpid="FIRM1", crd="1"),
            make_row("ATS_W_SMBL_FIRM", shares=200, trades=20, mpid="FIRM2", crd="2"),
        ]
        r = analyze_revision_stable_symbols(rows, "2022-01-17", 4, 1)
        self.assertEqual(r["bridge_mapped_symbols"], 1)
        self.assertEqual(r["revision_stable_concentration_symbols"], 1)

    def test_de_minimis_prevents_firm_concentration(self):
        rows = [
            make_row("ATS_W_SMBL", shares=300, trades=30),
            make_row("ATS_W_SMBL_FIRM", shares=100, trades=10, mpid="FIRM1", crd="1"),
            make_row("ATS_W_SMBL_FIRM", shares=200, trades=20, mpid="", crd="", name="DE MINIMIS FIRMS"),
        ]
        r = analyze_revision_stable_symbols(rows, "2022-01-17", 3, 1)
        self.assertEqual(r["revision_stable_mapped_symbols"], 1)
        self.assertEqual(r["revision_stable_concentration_symbols"], 0)
        self.assertEqual(r["stable_concentration_gate"], "FAIL_OR_REVIEW")

    def test_share_mismatch_blocks_symbol_bridge(self):
        rows = self.base_rows()
        rows[2]["totalWeeklyShareQuantity"] = "199"
        r = analyze_revision_stable_symbols(rows, "2022-01-17", 3, 1)
        self.assertEqual(r["bridge_mismatched_symbols"], 1)
        self.assertEqual(r["symbol_bridge_gate"], "FAIL_OR_REVIEW")


if __name__ == "__main__":
    unittest.main()

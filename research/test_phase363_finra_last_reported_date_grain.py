import unittest

from research.phase363_finra_last_reported_date_grain import audit_family


def row(stype, symbol="LND", last="2025-01-10", product="CTS",
        shares=100, trades=10, mpid="", crd="", name="Participant"):
    return {
        "issueSymbolIdentifier": symbol,
        "summaryTypeCode": stype,
        "lastReportedDate": last,
        "productTypeCode": product,
        "totalWeeklyShareQuantity": shares,
        "totalWeeklyTradeCount": trades,
        "MPID": mpid,
        "firmCRDNumber": crd,
        "marketParticipantName": name,
    }


class Phase363Tests(unittest.TestCase):
    def test_distinct_last_reported_dates_resolve_symbol_level_multiplicity(self):
        rows = [
            row("ATS_W_SMBL", last="2025-01-10", shares=6224, trades=37),
            row("ATS_W_SMBL", last="2025-01-08", shares=5226, trades=144),
            row("ATS_W_SMBL_FIRM", last="2025-01-10", shares=6224, trades=37, mpid="A001"),
            row("ATS_W_SMBL_FIRM", last="2025-01-08", shares=5226, trades=144, mpid="A001"),
        ]
        out = audit_family(rows, "ATS_W_SMBL")
        self.assertEqual(out["aggregate_symbol_last_reported_groups"], 2)
        self.assertEqual(out["matched_groups"], 2)
        self.assertEqual(out["exact_matches"], 2)
        self.assertEqual(out["data_gate"], "PASS")
        self.assertEqual(len(out["lnd_date_groups"]), 2)

    def test_duplicate_aggregate_same_symbol_and_date_still_fails(self):
        rows = [
            row("ATS_W_SMBL", last="2025-01-10", shares=40, trades=4),
            row("ATS_W_SMBL", last="2025-01-10", shares=60, trades=6),
            row("ATS_W_SMBL_FIRM", last="2025-01-10", shares=100, trades=10, mpid="A001"),
        ]
        out = audit_family(rows, "ATS_W_SMBL")
        self.assertEqual(out["duplicate_aggregate_symbol_date_key_count"], 1)
        self.assertEqual(out["data_gate"], "FAIL_OR_REVIEW")

    def test_multiple_products_same_symbol_date_fails(self):
        rows = [
            row("ATS_W_SMBL", last="2025-01-10", product="CTS", shares=40, trades=4),
            row("ATS_W_SMBL", last="2025-01-10", product="UTP", shares=60, trades=6),
            row("ATS_W_SMBL_FIRM", last="2025-01-10", shares=100, trades=10, mpid="A001"),
        ]
        out = audit_family(rows, "ATS_W_SMBL")
        self.assertEqual(out["multi_product_symbol_date_key_count"], 1)
        self.assertEqual(out["data_gate"], "FAIL_OR_REVIEW")

    def test_missing_last_reported_date_fails(self):
        agg = row("ATS_W_SMBL")
        firm = row("ATS_W_SMBL_FIRM", mpid="A001")
        agg["lastReportedDate"] = ""
        out = audit_family([agg, firm], "ATS_W_SMBL")
        self.assertEqual(out["missing_aggregate_last_reported_rows"], 1)
        self.assertEqual(out["data_gate"], "FAIL_OR_REVIEW")

    def test_participant_duplicate_within_same_reporting_date_fails(self):
        rows = [
            row("ATS_W_SMBL", shares=100, trades=10),
            row("ATS_W_SMBL_FIRM", shares=40, trades=4, mpid="A001"),
            row("ATS_W_SMBL_FIRM", shares=60, trades=6, mpid="A001"),
        ]
        out = audit_family(rows, "ATS_W_SMBL")
        self.assertEqual(out["participant_duplicate_key_group_count"], 1)
        self.assertEqual(out["data_gate"], "FAIL_OR_REVIEW")

    def test_exact_firm_reconciliation_by_symbol_date(self):
        rows = [
            row("OTC_W_SMBL", last="2025-01-10", shares=28543, trades=137),
            row("OTC_W_SMBL_FIRM", last="2025-01-10", shares=28543, trades=137, crd="123"),
        ]
        out = audit_family(rows, "OTC_W_SMBL")
        self.assertEqual(out["exact_matches"], 1)
        self.assertEqual(out["data_gate"], "PASS")

    def test_no_firm_aggregate_join_across_reporting_dates(self):
        rows = [
            row("ATS_W_SMBL", last="2025-01-10", shares=100, trades=10),
            row("ATS_W_SMBL_FIRM", last="2025-01-08", shares=100, trades=10, mpid="A001"),
        ]
        out = audit_family(rows, "ATS_W_SMBL")
        self.assertEqual(out["aggregate_only_groups"], 1)
        self.assertEqual(out["firm_only_groups"], 1)
        self.assertEqual(out["data_gate"], "FAIL_OR_REVIEW")


if __name__ == "__main__":
    unittest.main()

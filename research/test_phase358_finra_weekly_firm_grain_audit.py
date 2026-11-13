import unittest

from research.phase358_finra_weekly_firm_grain_audit import audit_rows, participant_id


def row(stype, symbol="ABC", product="CTS", volume="100", trades="10",
        mpid="", crd="", name="Participant"):
    return {
        "issueSymbolIdentifier": symbol,
        "weekStartDate": "2025-10-20",
        "tierIdentifier": "T1",
        "summaryTypeCode": stype,
        "productTypeCode": product,
        "firmCRDNumber": crd,
        "MPID": mpid,
        "marketParticipantName": name,
        "totalWeeklyShareQuantity": volume,
        "totalWeeklyTradeCount": trades,
        "initialPublishedDate": "2025-11-10",
        "lastUpdateDate": "2025-11-10",
        "lastReportedDate": "2025-10-24",
    }


class Phase358Tests(unittest.TestCase):
    def test_firm_rows_reconcile_to_symbol_aggregate(self):
        rows = [
            row("ATS_W_SMBL", volume="100", trades="10"),
            row("ATS_W_SMBL_FIRM", volume="60", trades="6", mpid="A001"),
            row("ATS_W_SMBL_FIRM", volume="40", trades="4", mpid="A002"),
        ]
        out = audit_rows(rows, "2025-10-20", "T1")
        rec = out["firm_to_aggregate_reconciliation"]
        self.assertEqual(rec["matched_symbol_product_groups"], 1)
        self.assertEqual(rec["exact_volume_matches"], 1)
        self.assertEqual(rec["exact_trade_matches"], 1)
        self.assertEqual(out["participant_concentration_diagnostic"]["symbol_groups"], 1)

    def test_firm_sum_mismatch_is_visible_not_repaired(self):
        rows = [
            row("OTC_W_SMBL", volume="100", trades="10"),
            row("OTC_W_SMBL_FIRM", volume="70", trades="7", crd="123"),
            row("OTC_W_SMBL_FIRM", volume="25", trades="3", crd="456"),
        ]
        out = audit_rows(rows, "2025-10-20", "T1")
        rec = out["firm_to_aggregate_reconciliation"]
        self.assertEqual(rec["exact_volume_matches"], 0)
        self.assertEqual(rec["exact_trade_matches"], 1)
        self.assertEqual(len(rec["mismatch_examples"]), 1)
        self.assertEqual(rec["mismatch_examples"][0]["firm_sum_volume"], 95)

    def test_conflicting_duplicate_aggregate_is_quarantined(self):
        rows = [
            row("ATS_W_SMBL", volume="100", trades="10"),
            row("ATS_W_SMBL", volume="90", trades="9"),
            row("ATS_W_SMBL_FIRM", volume="100", trades="10", mpid="A001"),
        ]
        out = audit_rows(rows, "2025-10-20", "T1")
        self.assertEqual(len(out["duplicate_aggregate_groups"]), 1)
        self.assertEqual(out["firm_to_aggregate_reconciliation"]["matched_symbol_product_groups"], 0)

    def test_duplicate_firm_identity_is_detected_and_excluded_from_concentration(self):
        rows = [
            row("ATS_W_SMBL", volume="100", trades="10"),
            row("ATS_W_SMBL_FIRM", volume="60", trades="6", mpid="A001"),
            row("ATS_W_SMBL_FIRM", volume="40", trades="4", mpid="A001"),
        ]
        out = audit_rows(rows, "2025-10-20", "T1")
        self.assertEqual(len(out["duplicate_firm_groups"]), 1)
        self.assertEqual(out["participant_concentration_diagnostic"]["symbol_groups"], 0)
        self.assertEqual(out["participant_concentration_diagnostic"]["excluded_duplicate_symbol_groups"], 1)

    def test_missing_firm_identifier_is_counted(self):
        rows = [
            row("OTC_W_SMBL", volume="100", trades="10"),
            row("OTC_W_SMBL_FIRM", volume="100", trades="10", crd="", mpid=""),
        ]
        out = audit_rows(rows, "2025-10-20", "T1")
        self.assertEqual(out["firm_rows_missing_participant_id"], 1)
        self.assertEqual(participant_id(rows[1]), None)

    def test_partition_mismatch_is_not_hidden(self):
        rows = [row("ATS_W_SMBL", volume="100", trades="10")]
        rows[0]["weekStartDate"] = "2025-10-27"
        out = audit_rows(rows, "2025-10-20", "T1")
        self.assertEqual(out["partition_error_count"], 1)
        self.assertEqual(out["data_gate"], "FAIL_OR_REVIEW")

    def test_orphan_firm_group_is_reported(self):
        rows = [row("ATS_W_SMBL_FIRM", volume="100", trades="10", mpid="A001")]
        out = audit_rows(rows, "2025-10-20", "T1")
        self.assertEqual(out["firm_orphan_symbol_product_groups"], 1)


if __name__ == "__main__":
    unittest.main()

"""Synthetic regression tests for the Phase 579 FINRA ATS PIT gate."""
import unittest

from research.phase579_finra_ats_stable_row_pit_gate import classify_symbol_week


def sessions():
    return [
        {"session_date": "2026-01-05", "open_utc": "2026-01-05T14:30:00Z"},
        {"session_date": "2026-02-02", "open_utc": "2026-02-02T14:30:00Z"},
        {"session_date": "2026-02-03", "open_utc": "2026-02-03T14:30:00Z"},
        {"session_date": "2026-02-04", "open_utc": "2026-02-04T14:30:00Z"},
    ]


def rows():
    return [
        {
            "summaryTypeCode": "ATS_W_SMBL",
            "issueSymbolIdentifier": "ABC",
            "weekStartDate": "2026-01-05",
            "initialPublishedDate": "2026-01-26",
            "lastReportedDate": "2026-01-26",
            "lastUpdateDate": "2026-01-26",
            "productTypeCode": "CTS",
            "totalWeeklyShareQuantity": "1000",
            "totalWeeklyTradeCount": "100",
        },
        {
            "summaryTypeCode": "ATS_W_SMBL_FIRM",
            "issueSymbolIdentifier": "ABC",
            "weekStartDate": "2026-01-05",
            "initialPublishedDate": "2026-01-26",
            "lastReportedDate": "2026-01-26",
            "lastUpdateDate": "2026-01-26",
            "productTypeCode": "CTS",
            "atsMpid": "XABC",
            "marketParticipantName": "Example ATS",
            "totalWeeklyShareQuantity": "1000",
            "totalWeeklyTradeCount": "100",
        },
    ]


def identity(**overrides):
    record = {
        "symbol": "ABC",
        "effective_from": "2025-01-01",
        "effective_to": None,
        "record_known_utc": "2026-01-20T12:00:00Z",
        "record_time_semantics_certified": True,
        "listing_id": "L1",
        "security_id": "S1",
        "issuer_id": "I1",
    }
    record.update(overrides)
    return record


class Phase579StableRowGateTests(unittest.TestCase):
    def test_stable_group_uses_next_session_strictly_after_publication(self):
        result = classify_symbol_week(rows(), sessions())
        self.assertTrue(result["stable_row_pit_eligible"])
        self.assertEqual(result["first_executable_session"], "2026-02-02")
        self.assertFalse(result["economic_test_eligible"])
        self.assertFalse(result["signal_admitted"])

    def test_revised_row_is_quarantined(self):
        data = rows()
        data[1]["lastReportedDate"] = "2026-01-27"
        data[1]["lastUpdateDate"] = "2026-01-27"
        result = classify_symbol_week(data, sessions())
        self.assertFalse(result["stable_row_pit_eligible"])
        self.assertIn("row_1:revised_row_quarantined", result["rejection_reasons"])

    def test_update_date_must_equal_max_of_publication_and_last_report(self):
        data = rows()
        data[0]["lastUpdateDate"] = "2026-01-27"
        result = classify_symbol_week(data, sessions())
        self.assertFalse(result["stable_row_pit_eligible"])
        self.assertIn("row_0:last_update_semantics_mismatch", result["rejection_reasons"])

    def test_invalid_publication_lag_is_quarantined(self):
        data = rows()
        for row in data:
            row["initialPublishedDate"] = "2026-01-27"
            row["lastReportedDate"] = "2026-01-27"
            row["lastUpdateDate"] = "2026-01-27"
        result = classify_symbol_week(data, sessions())
        self.assertFalse(result["stable_row_pit_eligible"])
        self.assertIn("publication_lag_outside_21_22", " ".join(result["rejection_reasons"]))

    def test_publication_date_must_be_common_across_group(self):
        data = rows()
        data[1]["initialPublishedDate"] = "2026-01-27"
        data[1]["lastReportedDate"] = "2026-01-27"
        data[1]["lastUpdateDate"] = "2026-01-27"
        result = classify_symbol_week(data, sessions())
        self.assertFalse(result["stable_row_pit_eligible"])
        self.assertIn("publication_date_mismatch", result["rejection_reasons"])

    def test_duplicate_aggregate_product_type_is_quarantined(self):
        data = rows()
        duplicate = dict(data[0])
        duplicate["totalWeeklyShareQuantity"] = "500"
        duplicate["totalWeeklyTradeCount"] = "50"
        data.insert(1, duplicate)
        result = classify_symbol_week(data, sessions())
        self.assertFalse(result["stable_row_pit_eligible"])
        self.assertIn("duplicate_aggregate_product_type", result["rejection_reasons"])

    def test_missing_aggregate_is_quarantined(self):
        result = classify_symbol_week([rows()[1]], sessions())
        self.assertFalse(result["stable_row_pit_eligible"])
        self.assertIn("aggregate_rows_missing", result["rejection_reasons"])

    def test_identity_requires_certified_record_clock(self):
        result = classify_symbol_week(rows(), sessions(), [identity(record_time_semantics_certified=False)])
        self.assertEqual(result["security_identity"]["status"], "record_clock_uncertified")

    def test_identity_record_must_be_known_by_entry_open(self):
        result = classify_symbol_week(rows(), sessions(), [identity(record_known_utc="2026-02-02T14:31:00Z")])
        self.assertEqual(result["security_identity"]["status"], "no_effective_known_mapping")

    def test_exactly_one_permanent_identity_tuple_can_match(self):
        result = classify_symbol_week(rows(), sessions(), [identity()])
        self.assertEqual(result["security_identity"]["status"], "matched")
        self.assertEqual(result["security_identity"]["listing_id"], "L1")

    def test_multiple_identity_mappings_are_ambiguous(self):
        result = classify_symbol_week(rows(), sessions(), [identity(), identity(listing_id="L2", security_id="S2")])
        self.assertEqual(result["security_identity"]["status"], "ambiguous_mapping")

    def test_identity_must_be_effective_on_report_week(self):
        result = classify_symbol_week(rows(), sessions(), [identity(effective_from="2026-01-06")])
        self.assertEqual(result["security_identity"]["status"], "no_effective_known_mapping")

    def test_concentration_requires_reconciled_complete_unique_mpid_rows(self):
        result = classify_symbol_week(rows(), sessions())
        self.assertTrue(result["bridge_reconciled"])
        self.assertTrue(result["concentration_eligible"])

    def test_de_minimis_or_missing_mpid_blocks_concentration_not_stable_pit(self):
        data = rows()
        data[1]["atsMpid"] = ""
        data[1]["marketParticipantName"] = "De Minimis"
        result = classify_symbol_week(data, sessions())
        self.assertTrue(result["stable_row_pit_eligible"])
        self.assertFalse(result["concentration_eligible"])

    def test_non_reconciled_firm_totals_block_concentration(self):
        data = rows()
        data[1]["totalWeeklyShareQuantity"] = "999"
        result = classify_symbol_week(data, sessions())
        self.assertTrue(result["stable_row_pit_eligible"])
        self.assertFalse(result["bridge_reconciled"])
        self.assertFalse(result["concentration_eligible"])

    def test_missing_future_session_blocks_stable_candidate(self):
        result = classify_symbol_week(rows(), sessions()[:1])
        self.assertFalse(result["stable_row_pit_eligible"])
        self.assertIn("no_future_executable_session", result["rejection_reasons"])


if __name__ == "__main__":
    unittest.main()

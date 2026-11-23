"""Synthetic regression tests for the Phase 579 FINRA ATS PIT gate."""
import unittest

from research.phase579_finra_ats_stable_row_pit_gate import classify_symbol_week


def sessions():
    return [
        {"session_date": "2026-01-05", "open_utc": "2026-01-05T14:30:00Z"},
        {"session_date": "2026-01-26", "open_utc": "2026-01-26T14:30:00Z"},
        {"session_date": "2026-01-27", "open_utc": "2026-01-27T14:30:00Z"},
        {"session_date": "2026-01-28", "open_utc": "2026-01-28T14:30:00Z"},
        {"session_date": "2026-01-29", "open_utc": "2026-01-29T14:30:00Z"},
        {"session_date": "2026-01-30", "open_utc": "2026-01-30T14:30:00Z"},
        {"session_date": "2026-02-02", "open_utc": "2026-02-02T14:30:00Z"},
    ]


def rows():
    return [
        {
            "summaryTypeCode": "ATS_W_SMBL",
            "tierIdentifier": "T1",
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
            "tierIdentifier": "T1",
            "issueSymbolIdentifier": "ABC",
            "weekStartDate": "2026-01-05",
            "initialPublishedDate": "2026-01-26",
            "lastReportedDate": "2026-01-26",
            "lastUpdateDate": "2026-01-26",
            "productTypeCode": "CTS",
            "MPID": "XABC",
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
    def evaluate(self, data, calendar=None, identity_records=()):
        return classify_symbol_week(
            data,
            calendar if calendar is not None else sessions(),
            identity_records,
            session_calendar_complete=True,
        )

    def test_uncertified_session_calendar_blocks_executable_label(self):
        result = classify_symbol_week(rows(), sessions())
        self.assertFalse(result["stable_row_pit_eligible"])
        self.assertEqual(result["reason"], "session_calendar_not_certified_complete")

    def test_timestamp_is_not_accepted_as_date_only_finra_field(self):
        data = rows()
        data[0]["initialPublishedDate"] = "2026-01-26T06:00:00Z"
        result = self.evaluate(data, sessions())
        self.assertFalse(result["stable_row_pit_eligible"])
        self.assertTrue(any("must_be_date_only" in x for x in result["rejection_reasons"]))

    def test_stable_group_uses_next_session_strictly_after_publication(self):
        result = self.evaluate(rows(), sessions())
        self.assertTrue(result["stable_row_pit_eligible"])
        self.assertEqual(result["first_executable_session"], "2026-01-27")
        self.assertFalse(result["economic_test_eligible"])
        self.assertFalse(result["signal_admitted"])

    def test_revised_row_is_quarantined(self):
        data = rows()
        data[1]["lastReportedDate"] = "2026-01-28"
        data[1]["lastUpdateDate"] = "2026-01-28"
        result = self.evaluate(data, sessions())
        self.assertFalse(result["stable_row_pit_eligible"])
        self.assertIn("row_1:revised_row_quarantined", result["rejection_reasons"])

    def test_update_date_must_equal_max_of_publication_and_last_report(self):
        data = rows()
        data[0]["lastUpdateDate"] = "2026-01-28"
        result = self.evaluate(data, sessions())
        self.assertFalse(result["stable_row_pit_eligible"])
        self.assertIn("row_0:last_update_semantics_mismatch", result["rejection_reasons"])

    def test_invalid_publication_lag_is_quarantined(self):
        data = rows()
        for row in data:
            row["initialPublishedDate"] = "2026-01-28"
            row["lastReportedDate"] = "2026-01-28"
            row["lastUpdateDate"] = "2026-01-28"
        result = self.evaluate(data, sessions())
        self.assertFalse(result["stable_row_pit_eligible"])
        self.assertIn("publication_lag_outside_21_22", " ".join(result["rejection_reasons"]))

    def test_publication_date_must_be_common_across_group(self):
        data = rows()
        data[1]["initialPublishedDate"] = "2026-01-28"
        data[1]["lastReportedDate"] = "2026-01-28"
        data[1]["lastUpdateDate"] = "2026-01-28"
        result = self.evaluate(data, sessions())
        self.assertFalse(result["stable_row_pit_eligible"])
        self.assertIn("publication_date_mismatch", result["rejection_reasons"])

    def test_duplicate_aggregate_product_type_is_quarantined(self):
        data = rows()
        duplicate = dict(data[0])
        duplicate["totalWeeklyShareQuantity"] = "500"
        duplicate["totalWeeklyTradeCount"] = "50"
        data.insert(1, duplicate)
        result = self.evaluate(data, sessions())
        self.assertFalse(result["stable_row_pit_eligible"])
        self.assertIn("duplicate_aggregate_product_type", result["rejection_reasons"])

    def test_missing_aggregate_is_quarantined(self):
        result = self.evaluate([rows()[1]], sessions())
        self.assertFalse(result["stable_row_pit_eligible"])
        self.assertIn("aggregate_rows_missing", result["rejection_reasons"])

    def test_identity_requires_certified_record_clock(self):
        result = self.evaluate(rows(), sessions(), [identity(record_time_semantics_certified=False)])
        self.assertEqual(result["security_identity"]["status"], "record_clock_uncertified")

    def test_identity_record_must_be_known_by_entry_open(self):
        result = self.evaluate(rows(), sessions(), [identity(record_known_utc="2026-02-02T14:31:00Z")])
        self.assertEqual(result["security_identity"]["status"], "no_effective_known_mapping")

    def test_exactly_one_permanent_identity_tuple_can_match(self):
        result = self.evaluate(rows(), sessions(), [identity()])
        self.assertEqual(result["security_identity"]["status"], "matched")
        self.assertEqual(result["security_identity"]["listing_id"], "L1")

    def test_multiple_identity_mappings_are_ambiguous(self):
        result = self.evaluate(rows(), sessions(), [identity(), identity(listing_id="L2", security_id="S2")])
        self.assertEqual(result["security_identity"]["status"], "ambiguous_mapping")

    def test_identity_must_be_effective_on_report_week(self):
        result = self.evaluate(rows(), sessions(), [identity(effective_from="2026-01-06")])
        self.assertEqual(result["security_identity"]["status"], "no_effective_known_mapping")

    def test_non_t1_tier_is_quarantined_under_t1_publication_lag_rule(self):
        data = rows()
        for row in data:
            row["tierIdentifier"] = "T2"
        result = self.evaluate(data, sessions())
        self.assertFalse(result["stable_row_pit_eligible"])
        self.assertIn("tier_not_t1_for_21_22_day_gate", result["rejection_reasons"])

    def test_missing_tier_identifier_blocks_t1_publication_lag_rule(self):
        data = rows()
        for row in data:
            row.pop("tierIdentifier")
        result = self.evaluate(data, sessions())
        self.assertFalse(result["stable_row_pit_eligible"])
        self.assertIn("tier_identifier_missing_or_mixed", result["rejection_reasons"])

    def test_mixed_tier_group_is_quarantined(self):
        data = rows()
        data[1]["tierIdentifier"] = "T2"
        result = self.evaluate(data, sessions())
        self.assertFalse(result["stable_row_pit_eligible"])
        self.assertIn("tier_identifier_missing_or_mixed", result["rejection_reasons"])

    def test_identity_must_remain_effective_through_entry_session(self):
        result = self.evaluate(rows(), sessions(), [identity(effective_to="2026-01-26")])
        self.assertEqual(result["security_identity"]["status"], "no_effective_known_mapping")

    def test_identity_effective_through_entry_session_is_accepted(self):
        result = self.evaluate(rows(), sessions(), [identity(effective_to="2026-01-27")])
        self.assertEqual(result["security_identity"]["status"], "matched")

    def test_concentration_requires_reconciled_complete_unique_mpid_rows(self):
        result = self.evaluate(rows(), sessions())
        self.assertTrue(result["bridge_reconciled"])
        self.assertTrue(result["concentration_eligible"])

    def test_de_minimis_or_missing_mpid_blocks_concentration_not_stable_pit(self):
        data = rows()
        data[1]["MPID"] = ""
        data[1]["firmCRDNumber"] = "0"
        data[1]["marketParticipantName"] = "De Minimis"
        result = self.evaluate(data, sessions())
        self.assertTrue(result["stable_row_pit_eligible"])
        self.assertFalse(result["concentration_eligible"])

    def test_firm_crd_is_valid_fallback_when_mpid_missing(self):
        data = rows()
        data[1]["MPID"] = ""
        data[1]["firmCRDNumber"] = "12345"
        result = self.evaluate(data, sessions())
        self.assertTrue(result["stable_row_pit_eligible"])
        self.assertTrue(result["concentration_eligible"])

    def test_missing_mpid_and_zero_crd_block_concentration(self):
        data = rows()
        data[1]["MPID"] = ""
        data[1]["firmCRDNumber"] = "0"
        result = self.evaluate(data, sessions())
        self.assertTrue(result["stable_row_pit_eligible"])
        self.assertFalse(result["concentration_eligible"])

    def test_non_reconciled_firm_totals_block_concentration(self):
        data = rows()
        data[1]["totalWeeklyShareQuantity"] = "999"
        result = self.evaluate(data, sessions())
        self.assertTrue(result["stable_row_pit_eligible"])
        self.assertFalse(result["bridge_reconciled"])
        self.assertFalse(result["concentration_eligible"])

    def test_missing_future_session_blocks_stable_candidate(self):
        result = self.evaluate(rows(), sessions()[:1])
        self.assertFalse(result["stable_row_pit_eligible"])
        self.assertIn("no_future_executable_session", result["rejection_reasons"])


if __name__ == "__main__":
    unittest.main()

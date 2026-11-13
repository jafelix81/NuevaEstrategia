import unittest

from research.phase362_finra_lnd_duplicate_diagnostic import (
    SYMBOL, WEEK, TIER, as_nonnegative_int, summarize_family,
)


def row(stype, shares=100, trades=10, symbol="LND", product="CTS",
        mpid="", crd="", name="Participant", **extra):
    value = {
        "issueSymbolIdentifier": symbol,
        "issueName": "LEND",
        "weekStartDate": WEEK,
        "tierIdentifier": TIER,
        "summaryTypeCode": stype,
        "productTypeCode": product,
        "totalWeeklyShareQuantity": shares,
        "totalWeeklyTradeCount": trades,
        "totalNotionalSum": "1000",
        "initialPublishedDate": "2025-01-20",
        "lastUpdateDate": "2025-01-20",
        "lastReportedDate": "2025-01-17",
        "MPID": mpid,
        "firmCRDNumber": crd,
        "marketParticipantName": name,
    }
    value.update(extra)
    return value


class Phase362Tests(unittest.TestCase):
    def test_partition_constants_are_the_known_duplicate_case(self):
        self.assertEqual((WEEK, TIER, SYMBOL), ("2025-01-06", "T2", "LND"))

    def test_integer_parser_rejects_missing_negative_fractional_and_nonfinite(self):
        self.assertEqual(as_nonnegative_int("1,234"), 1234)
        self.assertIsNone(as_nonnegative_int(""))
        self.assertIsNone(as_nonnegative_int("-1"))
        self.assertIsNone(as_nonnegative_int("1.5"))
        self.assertIsNone(as_nonnegative_int("NaN"))

    def test_duplicate_aggregates_that_sum_to_firms_still_fail_grain_gate(self):
        rows = [
            row("ATS_W_SMBL", shares=40, trades=4),
            row("ATS_W_SMBL", shares=60, trades=6),
            row("ATS_W_SMBL_FIRM", shares=40, trades=4, mpid="A001"),
            row("ATS_W_SMBL_FIRM", shares=60, trades=6, mpid="A002"),
        ]
        out = summarize_family(rows, "ATS_W_SMBL")
        self.assertEqual(out["aggregate_row_count"], 2)
        self.assertTrue(out["combined_aggregate_matches_firm_arithmetically"])
        self.assertEqual(out["data_gate"], "FAIL_OR_REVIEW")
        self.assertEqual(out["aggregate_diagnosis"], "MULTIPLE_DISTINCT_AGGREGATE_ROWS_SAME_SYMBOL_PRODUCT")

    def test_exact_duplicate_aggregate_rows_are_not_deduplicated(self):
        rows = [
            row("ATS_W_SMBL", shares=50, trades=5),
            row("ATS_W_SMBL", shares=50, trades=5),
            row("ATS_W_SMBL_FIRM", shares=100, trades=10, mpid="A001"),
        ]
        out = summarize_family(rows, "ATS_W_SMBL")
        self.assertEqual(out["aggregate_exact_duplicate_count"], 1)
        self.assertEqual(out["aggregate_diagnosis"], "EXACT_DUPLICATE_AGGREGATE_ROWS")
        self.assertEqual(out["data_gate"], "FAIL_OR_REVIEW")

    def test_single_aggregate_and_unique_participants_pass_data_grain_gate(self):
        rows = [
            row("ATS_W_SMBL", shares=100, trades=10),
            row("ATS_W_SMBL_FIRM", shares=40, trades=4, mpid="A001"),
            row("ATS_W_SMBL_FIRM", shares=60, trades=6, mpid="A002"),
        ]
        out = summarize_family(rows, "ATS_W_SMBL")
        self.assertTrue(out["combined_aggregate_matches_firm_arithmetically"])
        self.assertEqual(out["data_gate"], "PASS")

    def test_duplicate_participant_identity_fails_gate(self):
        rows = [
            row("ATS_W_SMBL", shares=100, trades=10),
            row("ATS_W_SMBL_FIRM", shares=40, trades=4, mpid="A001"),
            row("ATS_W_SMBL_FIRM", shares=60, trades=6, mpid="A001"),
        ]
        out = summarize_family(rows, "ATS_W_SMBL")
        self.assertEqual(out["firm_duplicate_participant_key_count"], 1)
        self.assertEqual(out["data_gate"], "FAIL_OR_REVIEW")

    def test_firm_identities_are_hashed_not_emitted(self):
        rows = [
            row("ATS_W_SMBL", shares=100, trades=10),
            row("ATS_W_SMBL_FIRM", shares=100, trades=10, mpid="SECRET-MPID"),
        ]
        out = summarize_family(rows, "ATS_W_SMBL")
        self.assertNotIn("SECRET-MPID", str(out))
        self.assertIsNotNone(out["firm_rows_anonymized"][0]["identity_hash"])

    def test_family_isolation_ignores_other_symbols_and_summary_types(self):
        rows = [
            row("ATS_W_SMBL", shares=100, trades=10),
            row("ATS_W_SMBL_FIRM", shares=100, trades=10, mpid="A001"),
            row("ATS_W_SMBL", symbol="OTHER", shares=900, trades=90),
            row("OTC_W_SMBL", shares=800, trades=80),
        ]
        out = summarize_family(rows, "ATS_W_SMBL")
        self.assertEqual(out["aggregate_row_count"], 1)
        self.assertEqual(out["firm_row_count"], 1)
        self.assertEqual(out["sum_firm_shares"], 100)


if __name__ == "__main__":
    unittest.main()

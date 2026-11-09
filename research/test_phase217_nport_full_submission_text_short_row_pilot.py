import copy
import unittest

from research.phase217_nport_full_submission_text_short_row_pilot import (
    build_audit,
    load_evidence,
)


class Phase217NportFullSubmissionTextPilotTests(unittest.TestCase):
    def setUp(self):
        self.evidence = load_evidence()

    def test_filing_identity_and_period(self):
        result = build_audit(self.evidence)
        self.assertEqual(result["accession"], "0001145549-25-033457")
        self.assertEqual(result["period_of_report"], "2025-03-31")

    def test_acceptance_clock_and_lag(self):
        result = build_audit(self.evidence)
        self.assertEqual(result["accepted_et"], "2025-05-28T16:04:35")
        self.assertEqual(result["report_to_filing_lag_calendar_days"], 58)

    def test_next_session_is_candidate_not_verified_receipt(self):
        self.assertEqual(self.evidence["filing"]["next_full_session_candidate"], "2025-05-29")
        self.assertEqual(self.evidence["gates"]["first_public_receipt_capture"], "NOT_VERIFIED")

    def test_twenty_three_selected_rows_and_unique_cusips(self):
        result = build_audit(self.evidence)
        self.assertEqual(result["selected_direct_short_common_equity_examples"], 23)
        self.assertEqual(result["unique_cusips"], 23)

    def test_all_rows_are_direct_short_common_equity(self):
        for row in self.evidence["selected_rows"]:
            self.assertEqual(row["title"], "Common Stock")
            self.assertEqual(row["units"], "NS")
            self.assertEqual(row["payoff_profile"], "Short")
            self.assertEqual(row["asset_category"], "EC")
            self.assertEqual(row["issuer_category"], "CORP")
            self.assertEqual(row["investment_country"], "US")
            self.assertLess(row["balance"], 0)
            self.assertLess(row["val_usd"], 0)
            self.assertLess(row["pct_nav"], 0)

    def test_source_line_ranges_are_valid(self):
        for row in self.evidence["selected_rows"]:
            self.assertLessEqual(row["source_line_start"], row["source_line_end"])

    def test_raw_hashes_and_first_receipt_remain_unverified(self):
        result = build_audit(self.evidence)
        self.assertFalse(result["raw_submission_sha256_verified"])
        self.assertFalse(result["raw_primary_xml_sha256_verified"])
        self.assertFalse(result["first_public_receipt_verified"])

    def test_identifier_exceptions_are_preserved(self):
        exceptions = self.evidence["identifier_exceptions"]
        self.assertEqual(len(exceptions), 3)
        self.assertEqual(exceptions[0]["cusip"], "N/A")
        self.assertEqual(exceptions[1]["cusip"], "N/A")
        self.assertEqual(exceptions[2]["cusip"], "G39387108")

    def test_no_alpha_holdout_or_production_change(self):
        result = build_audit(self.evidence)
        self.assertFalse(result["alpha_test_authorized"])
        self.assertFalse(result["holdout_used"])
        self.assertTrue(result["f80_frozen"])
        self.assertFalse(self.evidence["controls"]["production_changed"])

    def test_reject_positive_balance(self):
        bad = copy.deepcopy(self.evidence)
        bad["selected_rows"][0]["balance"] = 1
        with self.assertRaises(ValueError):
            build_audit(bad)

    def test_reject_duplicate_cusip(self):
        bad = copy.deepcopy(self.evidence)
        bad["selected_rows"][1]["cusip"] = bad["selected_rows"][0]["cusip"]
        with self.assertRaises(ValueError):
            build_audit(bad)

    def test_reject_unverified_raw_hash_claim(self):
        bad = copy.deepcopy(self.evidence)
        bad["controls"]["raw_submission_sha256_verified"] = True
        with self.assertRaises(ValueError):
            build_audit(bad)

    def test_reject_holdout_use(self):
        bad = copy.deepcopy(self.evidence)
        bad["controls"]["holdout_used"] = True
        with self.assertRaises(ValueError):
            build_audit(bad)


if __name__ == "__main__":
    unittest.main()
